from time import sleep, time
from datetime import datetime
from settings.config import kraken_secret, kraken_key, ticker_sleep_time, mongo_uri, mongo_db
from database.services import init_database, save_data
from trade.services import init_connection

SYMBOL = 'BTC/USD'
INSERT_FREQUENCY = 5

broker = init_connection(kraken_key, kraken_secret)
mongo_client = init_database(mongo_uri)

i = 0
ticks = []
while True:
    # increase counter
    i += 1
    # fetch ticker data
    ticker_data = broker.fetch_ticker(SYMBOL)
    # start counting time
    start_ts = time()

    # create record
    ticks.append({
        'last': ticker_data['last'],
        'ts': datetime.fromtimestamp(int(str(ticker_data['timestamp'])[:-3]), None)
    })

    # save to proper collection in db
    if i % INSERT_FREQUENCY == 0:
        save_data(mongo_client[mongo_db], SYMBOL, ticks)
        i = 0
        ticks = []

    # count how much we need to wait until next fetch
    period = ticker_sleep_time - (time() - start_ts)
    # wait
    if period > 0:
        sleep(period)
