# Berbix Python SDK

This Berbix Python library provides simple interfaces to interact with the Berbix API.

## Usage

### Constructing the client

    import berbix

    client = berbix.Client(
      client_id='your_client_id_here',
      client_secret='your_client_secret_here')

### Fetching user tokens

    user_tokens = client.exchange_code(code)

### Fetching user data

    client.fetch_user(user_tokens)

### User tokens from storage

    refresh_token = '' # fetched from database
    user_tokens = UserTokens.from_refresh(refresh_token)

## Release

To release a new version of the SDK, first bump the version in `setup.py`.

    python setup.py sdist bdist_wheel
    twine upload dist/*
