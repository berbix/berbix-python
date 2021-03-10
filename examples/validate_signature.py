import sys
import os
import pprint

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import berbix

cl = berbix.Client(api_secret=os.environ['BERBIX_DEMO_API_SECRET'])

secret = 'secret'
body = """body""" # might have a new line at the end here
signature = 'x-berbix-signature header'

is_valid = cl.validate_signature(secret, body, signature)

pprint.pprint(is_valid)