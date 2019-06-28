import sys
import os
import pprint
import time

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import berbix

cl = berbix.Client(
  client_id=os.environ['BERBIX_DEMO_CLIENT_ID'],
  client_secret=os.environ['BERBIX_DEMO_CLIENT_SECRET'],
  api_host=os.environ['BERBIX_DEMO_API_HOST'])

man_tokens = cl.create_transaction(customer_uid="this_is_a_customer_uid")

pprint.pprint(man_tokens)

continuation = cl.create_continuation(man_tokens)

pprint.pprint(continuation)

tokens = cl.exchange_code(os.environ['BERBIX_DEMO_CODE'])

pprint.pprint(tokens)

to_refresh = berbix.Tokens.from_refresh(tokens.refresh_token)

time.sleep(5)

transaction = cl.fetch_transaction(to_refresh)

pprint.pprint(transaction)
