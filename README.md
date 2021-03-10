# Berbix Python SDK

This Berbix Python library provides simple interfaces to interact with the Berbix API.

## Installation

    pip install berbix

## Usage

### Constructing a client

    import berbix

    client = berbix.Client(
      api_secret='your_api_secret_here')

### Create a transaction

    transaction_tokens = client.create_transaction(
      customer_uid="interal_customer_uid", # ID for the user in internal database
      template_key="your_template_key", # Template key for this transaction
    )

### Create tokens from refresh token

    refresh_token = '' # fetched from database
    transaction_tokens = Tokens.from_refresh(refresh_token)

### Fetch transaction data

    transaction_data = client.fetch_transaction(transaction_tokens)

## Reference

### `Client`

#### Methods

##### `constructor(options)`

Supported options:

- `api_secret` (required) - The API secret that can be found in your Berbix Dashboard.
- `http_client` - An optional override for the default HTTP client.

##### `create_transaction(options): Tokens`

Creates a transaction within Berbix to initialize the client SDK. Typically after creating
a transaction, you will want to store the refresh token in your database associated with the
currently active user session.

Supported options:

- `email` - Previously verified email address for a user.
- `phone` - Previously verified phone number for a user.
- `customer_uid` - An ID or identifier for the user in your system.
- `template_key` - The template key for this transaction.
- Deprecated: `hosted_options` - Optional configuration object for creating hosted transactions. The `hosted_options` object can optionally include the following fields:
  - `completion_email` - Email address to which completion alerts will be sent for this transaction.
  - `redirect_url` - URL to redirect the user to after they complete the transaction. If not specified, the URL specified in the Berbix dashboard will be used instead.

##### `create_hosted_transaction(options): HostedTransactionResponse`

Creates a hosted transaction within Berbix to initialize the client SDK. This works the same as create_transaction except `hosted_options` is a valid parameter and that it returns an explicit `hosted_url` for hosted transactions. 

Supported options:

- `email` - Previously verified email address for a user.
- `phone` - Previously verified phone number for a user.
- `customer_uid` - An ID or identifier for the user in your system.
- `template_key` - The template key for this transaction.
- `hosted_options` - Optional configuration object for creating hosted transactions. The `hosted_options` object can optionally include the following fields:
  - `completion_email` - Email address to which completion alerts will be sent for this transaction.
  - `redirect_url` - URL to redirect the user to after they complete the transaction. If not specified, the URL specified in the Berbix dashboard will be used instead.

##### `fetch_transaction(tokens: Tokens): object`

Fetches all of the information associated with the transaction. If the user has already completed the steps of the transaction, then this will include all of the elements of the transaction payload as described on the [Berbix developer docs](https://developers.berbix.com).

##### `refresh_tokens(tokens: Tokens): Tokens`

This is typically not needed to be called explicitly as it will be called by the higher-level
SDK methods, but can be used to get fresh client or access tokens.

##### `validate_signature(secret: string, body: string, header: string): boolean`

This method validates that the content of the webhook has not been forged. This should be called for every endpoint that is configured to receive a webhook from Berbix.

Parameters:

- `secret` - This is the secret associated with that webhook. NOTE: This is distinct from the API secret and can be found on the webhook configuration page of the dashboard.
- `body` - The full request body from the webhook. This should take the raw request body prior to parsing.
- `header` - The value in the 'X-Berbix-Signature' header.

##### `delete_transaction(tokens: Tokens): void`

Permanently deletes all submitted data associated with the transaction corresponding to the tokens provided.

##### `update_transaction(tokens: Tokens, ...parameters): object`

Changes a transaction's "action", for example upon review in your systems. Returns the updated transaction upon success.

Parameters:

- `action: string` - A string describing the action taken on the transaction. Typically this will either be "accept" or "reject".
- `note: string` - A string containing an optional note explaining the action taken.

##### `override_transaction(tokens: Tokens, ...parameters): void`

Completes a previously created transaction, and overrides its return payload and flags to match the provided parameters.

Parameters:

- `response_payload: string` - A string describing the payload type to return when fetching transaction metadata, e.g. "us-dl". See [our testing guide](https://docs.berbix.com/docs/testing) for possible options.
- `flags: string[]` - An optional list of flags to associate with the transaction (independent of the payload's contents), e.g. ["id_under_18", "id_under_21"]. See [our flags documentation](https://docs.berbix.com/docs/id-flags) for a list of flags.
- `override_fields: { string: string }` - An optional mapping from a [transaction field](https://docs.berbix.com/reference#gettransactionmetadata) to the desired override value, e.g. `override_fields={"date_of_birth": "2000-12-09"}}`

### `Tokens`

#### Properties

##### `access_token: string`

This is the short-lived bearer token that the backend SDK uses to identify requests associated with a given transaction. This is not typically needed when using the higher-level SDK methods.

##### `client_token: string`

This is the short-lived token that the frontend SDK uses to identify requests associated with a given transaction. After transaction creation, this will typically be sent to a frontend SDK.

##### `refresh_token: string`

This is the long-lived token that allows you to create new tokens after the short-lived tokens have expired. This is typically stored in the database associated with the given user session.

##### `transaction_id: number`

The internal Berbix ID number associated with the transaction.

##### `expiry: Date`

The time at which the access and client tokens will expire.

##### `response: object`

The raw response object. This may include some non-token related fields.

###### Deprecated: `hosted_url: string`

This is a member of the response object. Represents the hosted transaction URL. This value will only be set when creating a transaction if the `hosted_options` field is set.

#### Static methods

##### `from_refresh(refreshToken: string): Tokens`

Creates a tokens object from a refresh token, which can be passed to higher-level SDK methods. The SDK will handle refreshing the tokens for accessing relevant data.

### HostedTransactionResponse

#### Properties

##### `tokens: Tokens`

This is the tokens object for future SDK calls.

###### `hosted_url: string`

This is a member of the response object. Represents the hosted transaction URL.

## Publishing

    To release a new version of the SDK, first bump the version in `setup.py`.

    python setup.py sdist bdist_wheel
    twine upload dist/*
