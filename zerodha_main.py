from kiteconnect import KiteConnect
from src.connection.broker import ZerodhaOptionChain




from kiteconnect import KiteConnect

api_key = "ywlpiapt7n58dhfv"
api_secret = "x8lvsr9crr8d4p4fvsp39eohs35rc8tv"

kite = KiteConnect(api_key=api_key)
#kite.access_token("7mGD1Us1J1Jw0ag460JfkvJffhKXWjgP")


data = kite.generate_session(
    request_token="7mGD1Us1J1Jw0ag460JfkvJffhKXWjgP",
    api_secret="x8lvsr9crr8d4p4fvsp39eohs35rc8tv"
)

access_token = data["access_token"]

print(access_token)
print(kite.login_url())

# 🚀 Initialize
oc = ZerodhaOptionChain(kite)

# Load instruments ONCE (important)
oc.load_instruments()

# Fetch option chain
df = oc.get_option_chain()

print(df.head())