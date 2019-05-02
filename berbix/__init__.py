import json
import requests
import time

from requests.exceptions import HTTPError


class HTTPClient(object):
  def request(self, method, url, headers, data=None, auth=None):
    raise NotImplementedError("subclass must implement request")


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


class UserTokens(object):
  def __init__(self, access_token, refresh_token, expiry):
    self.access_token = access_token
    self.refresh_token = refresh_token
    self.expiry = expiry

  def refresh(self, access_token, expiry):
    self.access_token = access_token
    self.expiry = expiry

  def needs_refresh(self):
    return self.access_token is None or self.expiry is None or self.expiry < time.time()

  @staticmethod
  def from_refresh(refresh_token):
    return UserTokens(None, refresh_token, None)


class Client(object):
  def __init__(self, client_id=None, client_secret=None, api_host='https://api.berbix.com', http_client=RequestsClient()):
    self.client_id = client_id
    self.client_secret = client_secret
    self.api_host = api_host
    self.http_client = http_client

    if self.client_id is None:
      raise ValueError('client_id must be provided when instantiating the Berbix client')

    if self.client_secret is None:
      raise ValueError('client_secret must be provided when instantiating the Berbix client')

  def __fetch_tokens(self, path, payload):
    try:
      headers = {
        'Content-Type': 'application/json',
      }
      result = self.http_client.request(
        method='POST',
        url="{}{}".format(self.api_host, path),
        headers=headers,
        data=json.dumps(payload),
        auth=(self.client_id, self.client_secret))
      if result.status_code < 200 or result.status_code >= 300:
        raise UnexpectedResponse.from_response(json.loads(result.content))
      data = json.loads(result.content)
      return UserTokens(
        data.get('access_token'),
        data.get('refresh_token'),
        data.get('expires_in') + time.time())
    except HTTPError as err:
      raise err

  def create_user(self, email=None, phone=None, customer_uid=None):
    payload = {}
    if email is not None: payload['email'] = email
    if phone is not None: payload['phone'] = phone
    if customer_uid is not None: payload['customer_uid'] = customer_uid
    return self.__fetch_tokens('/v0/users', payload)

  def refresh_tokens(self, user_tokens):
    return self.__fetch_tokens('/v0/tokens', {
      'refresh_token': user_tokens.refresh_token,
      'grant_type': "refresh_token",
    })

  def exchange_code(self, code):
    return self.__fetch_tokens('/v0/tokens', {
      'code': code,
      'grant_type': "authorization_code",
    })

  def refresh_if_necessary(self, user_tokens):
    if user_tokens.needs_refresh():
      refreshed = self.refresh_tokens(user_tokens)
      user_tokens.refresh(refreshed.access_token, refreshed.expiry)

  def __token_auth_request(self, method, user_tokens, path):
    self.refresh_if_necessary(user_tokens)
    try:
      headers = {'Authorization': 'Bearer {0}'.format(user_tokens.access_token)}
      result = self.http_client.request(
        method=method,
        url="{}{}".format(self.api_host, path),
        headers=headers)
      if result.status_code < 200 or result.status_code >= 300:
        raise UnexpectedResponse.from_response(json.loads(result.content))
      return json.loads(result.content)
    except HTTPError as err:
      raise err

  def fetch_user(self, user_tokens):
    return self.__token_auth_request('GET', user_tokens, '/v0/users')

  def create_continuation(self, user_tokens):
    result = self.__token_auth_request('POST', user_tokens, '/v0/continuations')
    return result.get('value')
