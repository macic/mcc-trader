from settings.config import kraken_key, kraken_secret
import ccxt
import logging
#logging.basicConfig(level=logging.DEBUG)

def test():
    kraken = ccxt.kraken({
    'apiKey': kraken_key,
    'secret': kraken_secret,
    'verbose': False,  # switch it to False if you don't want the HTTP log
    })
    print(kraken.fetch_balance())
    print(kraken.fetch_my_trades())


test()