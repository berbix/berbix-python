import sys
import os
import pprint
import time

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import berbix

cl = berbix.Client(api_secret=os.environ['BERBIX_DEMO_API_SECRET'])

tokens = cl.create_transaction(
    customer_uid="this_is_a_customer_uid", template_key=os.environ["BERBIX_DEMO_TEMPLATE_KEY"])

pprint.pprint(tokens)

time.sleep(5)

# Mimics the refreshing of expired tokens
refreshed = berbix.Tokens.from_refresh(tokens.refresh_token)

transaction = cl.fetch_transaction(tokens)

pprint.pprint(transaction)

completed_transaction = cl.override_transaction(
    tokens, response_payload="us-dl", flags=["id_under_18", "id_under_21"], override_fields={"date_of_birth": "2000-12-09"})

pprint.pprint(completed_transaction)

updated_transaction = cl.update_transaction(
    tokens, action="accept", note="making an exception for this person")

pprint.pprint(updated_transaction)

# Uncomment the lines below to delete the newly-created transaction
#deleted_transaction = cl.delete_transaction(tokens)
# pprint.pprint(deleted_transaction)
