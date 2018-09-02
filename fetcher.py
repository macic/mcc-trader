import baker
from time import time, sleep
import json
import ast
import pandas as pd
from helpers.logger import log
from database.services import save_data
from datetime import datetime
from settings.config import kraken_secret, kraken_key, ticker_sleep_time, mongo_uri, mongo_db
from trade.services import init_connection
from ccxt.base.errors import ExchangeNotAvailable


@baker.command
def read_ohlc_from_kraken(symbol, interval, ts_start, ts_end=None):
    log.info("Starting reading OHLC", extra={'symbol': symbol, 'interval': interval})
    import requests
    url = 'https://api.kraken.com/0/public/OHLC'
    if ts_end is None:
        ts_end = int(time())
    since = int(ts_start)
    prev_last = 0
    while (since < ts_end and prev_last != since):
        response = requests.get(url, {'pair': symbol, 'interval': interval, 'since': since})
        if response.status_code == 200:
            try:
                parsed_response = json.loads(response.content)
            except Exception:
                log.error("Invalid format. Content: {0}".format(response.content))
                continue
            to_add_list = next(iter(parsed_response['result'].values()))
            items = [item[0:5] for item in to_add_list]
            prev_last = since

            # iterate and fix values to be pure 'floats' by poor mans hack literal eval
            for item in items:
                for index in range(1, 5):
                    item[index] = ast.literal_eval(item[index])

            df = pd.DataFrame(items, columns=['ts', 'open', 'high', 'low', 'close'])
            df['ts'] = pd.to_datetime(df.ts, unit='s')
            records = df.to_dict('records')
            if int(interval) == 60:
                grouping_range = 'H'
            else:
                grouping_range = interval + 'T'
            save_data(symbol, records, grouping_range)
            sleep(5)
            since = int(parsed_response['result']['last'])
        else:
            log.error("Invalid response", status_code=response.status_code)


@baker.command
def read_ticks(symbol='BTC/USD'):
    INSERT_FREQUENCY = 5

    broker = init_connection(kraken_key, kraken_secret)

    i = 0
    ticks = []
    while True:
        # increase counter
        i += 1
        # fetch ticker data
        try:
            ticker_data = broker.fetch_ticker(symbol)
        except ExchangeNotAvailable:
            continue
        # start counting time
        start_ts = time()

        # create record
        ticks.append({
            'last': ticker_data['last'],
            'ts': datetime.fromtimestamp(int(str(ticker_data['timestamp'])[:-3]), None)
        })

        # save to proper collection in db
        if i % INSERT_FREQUENCY == 0:
            save_data(symbol, ticks)
            i = 0
            ticks = []

        # count how much we need to wait until next fetch
        period = ticker_sleep_time - (time() - start_ts)
        # wait
        if period > 0:
            sleep(period)


if __name__ == '__main__':
    baker.run()
