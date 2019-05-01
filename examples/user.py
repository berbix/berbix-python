import pprint

import os
import berbix

cl = berbix.Client(
  client_id=os.environ.get("BERBIX_CLIENT_ID"),
  client_secret=os.environ.get("BERBIX_CLIENT_SECRET"),
  api_host=os.environ.get("BERBIX_API_HOST"))

code = input('enter authorization code from Berbix javascript SDK: ')
tokens = cl.exchange_code(code)

user = cl.fetch_user(tokens)

pprint.pprint(user)
