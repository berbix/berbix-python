import json
import requests
import time
import hmac
import hashlib

from requests.exceptions import HTTPError


SDK_VERSION = '0.0.8'
CLOCK_DRIFT = 300


class HTTPClient(object):
  def request(self, method, url, headers, data=None, auth=None):
    raise NotImplementedError('subclass must implement request')


class RequestsClient(HTTPClient):
  def request(self, method, url, headers, data=None, auth=None):
    return requests.request(method, url, headers=headers, data=data, auth=auth)


class UnexpectedResponse(Exception):
  def __init__(self, status, reason, message):
    self.status = status
    self.reason = reason
    self.message = message

  @staticmethod
  def from_response(data):
    return UnexpectedResponse(data.get('status'), data.get('reason'), data.get('message'))


class Tokens(object):
  def __init__(self, refresh_token, access_token, client_token, expiry, transaction_id):
    self.access_token = access_token
    self.client_token = client_token
    self.refresh_token = refresh_token
    self.expiry = expiry
    self.transaction_id = transaction_id

  def refresh(self, access_token, client_token, expiry, transaction_id):
    self.access_token = access_token
    self.client_token = client_token
    self.expiry = expiry
    self.transaction_id = transaction_id

  def needs_refresh(self):
    return self.access_token is None or self.expiry is None or self.expiry < time.time()

  @staticmethod
  def from_refresh(refresh_token):
    return Tokens(refresh_token, None, None, None, None)


class Client(object):
  def __init__(self, client_id=None, client_secret=None, **kwargs):
    self.client_id = client_id
    self.client_secret = client_secret
    self.api_host = kwargs.get('api_host', self.__api_host(kwargs.get('environment', 'production')))
    self.http_client = kwargs.get('http_client', RequestsClient())

    if self.client_id is None:
      raise ValueError('client_id must be provided when instantiating the Berbix client')

    if self.client_secret is None:
      raise ValueError('client_secret must be provided when instantiating the Berbix client')

  def __fetch_tokens(self, path, payload):
    try:
      headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'BerbixPython/' + SDK_VERSION,
      }
      result = self.http_client.request(
        method='POST',
        url='{}{}'.format(self.api_host, path),
        headers=headers,
        data=json.dumps(payload),
        auth=(self.client_id, self.client_secret))
      if result.status_code < 200 or result.status_code >= 300:
        raise UnexpectedResponse.from_response(json.loads(result.content))
      data = json.loads(result.content)
      return Tokens(
        data.get('refresh_token'),
        data.get('access_token'),
        data.get('client_token'),
        data.get('expires_in') + time.time(),
        data.get('transaction_id'))
    except HTTPError as err:
      raise err

  def __api_host(self, env):
    return {
      'sandbox': 'https://api.sandbox.berbix.com',
      'staging': 'https://api.staging.berbix.com',
      'production': 'https://api.berbix.com',
    }[env]

  def create_transaction(self, **kwargs):
    payload = {}
    if 'email' in kwargs: payload['email'] = kwargs['email']
    if 'phone' in kwargs: payload['phone'] = kwargs['phone']
    if 'customer_uid' in kwargs: payload['customer_uid'] = str(kwargs['customer_uid'])
    if 'template_key' in kwargs: payload['template_key'] = kwargs['template_key']
    return self.__fetch_tokens('/v0/transactions', payload)

  def create_user(self, email=None, phone=None, customer_uid=None):
    payload = {}
    if email is not None: payload['email'] = email
    if phone is not None: payload['phone'] = phone
    if customer_uid is not None: payload['customer_uid'] = customer_uid
    return self.create_transaction(**payload)

  def refresh_tokens(self, tokens):
    return self.__fetch_tokens('/v0/tokens', {
      'refresh_token': tokens.refresh_token,
      'grant_type': 'refresh_token',
    })

  def exchange_code(self, code):
    return self.__fetch_tokens('/v0/tokens', {
      'code': code,
      'grant_type': 'authorization_code',
    })

  def refresh_if_necessary(self, tokens):
    if tokens.needs_refresh():
      refreshed = self.refresh_tokens(tokens)
      tokens.refresh(refreshed.access_token, refreshed.client_token, refreshed.expiry, refreshed.transaction_id)

  def __token_auth_request(self, method, tokens, path):
    self.refresh_if_necessary(tokens)
    try:
      headers = {
        'Authorization': 'Bearer {0}'.format(tokens.access_token),
        'User-Agent': 'BerbixPython/' + SDK_VERSION,
      }
      result = self.http_client.request(
        method=method,
        url='{}{}'.format(self.api_host, path),
        headers=headers)
      if result.status_code < 200 or result.status_code >= 300:
        raise UnexpectedResponse.from_response(json.loads(result.content))
      return json.loads(result.content)
    except HTTPError as err:
      raise err

  def fetch_transaction(self, tokens):
    return self.__token_auth_request('GET', tokens, '/v0/transactions')

  def fetch_user(self, tokens):
    return self.fetch_transaction(tokens)

  def create_continuation(self, tokens):
    result = self.__token_auth_request('POST', tokens, '/v0/continuations')
    return result.get('value')

  def validate_signature(self, secret, body, header):
    parts = header.split(',')
    # Version (parts[0]) is currently unused
    timestamp = parts[1]
    signature = parts[2]
    if int(timestamp) < time.time() - CLOCK_DRIFT:
      return False
    message = '{},{},{}'.format(timestamp, secret, body)
    digest = hmac.new(
      secret,
      msg=message,
      digestmod=hashlib.sha256
    ).hexdigest()
    return digest == signature
