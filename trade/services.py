import ccxt


def init_connection(key, secret, debug=False):
    return ccxt.kraken({
        'apiKey': key,
        'secret': secret,
        'verbose': debug})
