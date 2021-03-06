import json
import requests
import time
import hmac
import hashlib

from requests.exceptions import HTTPError


SDK_VERSION = '1.0.0'
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

class HostedTransactionResponse(object):
    def __init__(self, tokens, hosted_url):
        self.tokens = tokens
        self.hosted_url = hosted_url

class Tokens(object):
    def __init__(self, refresh_token, access_token, client_token, expiry, transaction_id, response):
        self.access_token = access_token
        self.client_token = client_token
        self.refresh_token = refresh_token
        self.expiry = expiry
        self.transaction_id = transaction_id
        self.response = response

    def refresh(self, access_token, client_token, expiry, transaction_id):
        self.access_token = access_token
        self.client_token = client_token
        self.expiry = expiry
        self.transaction_id = transaction_id

    def needs_refresh(self):
        return self.access_token is None or self.expiry is None or self.expiry < time.time()

    @staticmethod
    def from_refresh(refresh_token):
        return Tokens(refresh_token, None, None, None, None, None)


class Client(object):
    def __init__(self, api_secret=None, **kwargs):
        self.api_secret = api_secret
        self.api_host = kwargs.get('api_host', 'https://api.berbix.com')
        self.http_client = kwargs.get('http_client', RequestsClient())

        if self.api_secret is None:
            self.api_secret = kwargs.get('client_secret')

        if self.api_secret is None:
            raise ValueError(
                'api_secret must be provided when instantiating the Berbix client')

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
                auth=(self.api_secret, ''))
            if result.status_code < 200 or result.status_code >= 300:
                raise UnexpectedResponse.from_response(
                    json.loads(result.content))
            data = json.loads(result.content)
            return Tokens(
                data.get('refresh_token'),
                data.get('access_token'),
                data.get('client_token'),
                data.get('expires_in') + time.time(),
                data.get('transaction_id'),
                data)
        except HTTPError as err:
            raise err

    def create_transaction(self, **kwargs):
        payload = {}
        if 'email' in kwargs:
            payload['email'] = kwargs['email']
        if 'phone' in kwargs:
            payload['phone'] = kwargs['phone']
        if 'customer_uid' in kwargs:
            payload['customer_uid'] = str(kwargs['customer_uid'])
        else:
            raise ValueError(
                'customer_uid must be provided when creating a transaction')
        if 'template_key' in kwargs:
            payload['template_key'] = kwargs['template_key']
        else:
            raise ValueError(
                'template_key must be provided when creating a transaction')
        if 'hosted_options' in kwargs:
            payload['hosted_options'] = kwargs['hosted_options']
        return self.__fetch_tokens('/v0/transactions', payload)

    def create_hosted_transaction(self, **kwargs):
        if 'hosted_options' not in kwargs:
            kwargs['hosted_options'] = {}

        tokens = self.__fetch_tokens('/v0/transactions', kwargs)

        return HostedTransactionResponse(tokens, tokens.response['hosted_url'])

    def refresh_tokens(self, tokens):
        return self.__fetch_tokens('/v0/tokens', {
            'refresh_token': tokens.refresh_token,
            'grant_type': 'refresh_token',
        })

    def refresh_if_necessary(self, tokens):
        if tokens.needs_refresh():
            refreshed = self.refresh_tokens(tokens)
            tokens.refresh(refreshed.access_token, refreshed.client_token,
                           refreshed.expiry, refreshed.transaction_id)

    def __token_auth_request(self, method, tokens, path, payload=None):
        self.refresh_if_necessary(tokens)
        try:
            headers = {
                'Authorization': 'Bearer {0}'.format(tokens.access_token),
                'User-Agent': 'BerbixPython/' + SDK_VERSION,
            }

            data = None
            if payload != None:
                data = json.dumps(payload)
                headers["Content-Type"] = "application/json"

            result = self.http_client.request(
                method=method,
                url='{}{}'.format(self.api_host, path),
                headers=headers,
                data=data)
            if result.status_code < 200 or result.status_code >= 300:
                raise UnexpectedResponse.from_response(
                    json.loads(result.content))
            elif result.status_code == 204:
                return
            return json.loads(result.content)
        except HTTPError as err:
            raise err

    def fetch_transaction(self, tokens):
        return self.__token_auth_request('GET', tokens, '/v0/transactions')

    def delete_transaction(self, tokens):
        return self.__token_auth_request('DELETE', tokens, '/v0/transactions')

    def update_transaction(self, tokens, **kwargs):
        payload = {}
        if 'action' in kwargs:
            payload['action'] = kwargs['action']
        if 'note' in kwargs:
            payload['note'] = kwargs['note']
        return self.__token_auth_request('PATCH', tokens, '/v0/transactions', payload)

    def override_transaction(self, tokens, **kwargs):
        payload = {}
        if 'response_payload' in kwargs:
            payload['response_payload'] = kwargs['response_payload']
        if 'flags' in kwargs:
            payload['flags'] = kwargs['flags']
        if 'override_fields' in kwargs:
            payload['override_fields'] = kwargs['override_fields']

        return self.__token_auth_request('PATCH', tokens, '/v0/transactions/override', payload)

    def validate_signature(self, secret, body, header):
        parts = header.split(',')
        # Version (parts[0]) is currently unused
        timestamp = parts[1]
        signature = parts[2]
        if int(timestamp) < time.time() - CLOCK_DRIFT:
            return False
        message = '{},{},{}'.format(timestamp, secret, body).encode('ascii')
        digest = hmac.new(
            str.encode(secret),
            msg=message,
            digestmod=hashlib.sha256
        ).hexdigest()
        return digest == signature
