import datetime
import pandas as pd
from pymongo import MongoClient, operations
from pymongo.errors import BulkWriteError
from helpers.console_colors import red, dump, yellow, green

def init_database(uri):
    return MongoClient(uri)


def get_data_from_timerange(db_instance, symbol, grouping_range, ts_start, ts_end):
    collection_name = build_collection_name(symbol, grouping_range)
    collection = db_instance[collection_name]
    iso_start = datetime.datetime.fromtimestamp(ts_start, None)
    iso_end = datetime.datetime.fromtimestamp(ts_end, None)
    print(yellow("Fetching data for %s in timeframe %s - %s" % (symbol, iso_start, iso_end)))
    docs = collection.find({"ts": {'$gte': iso_start, '$lt': iso_end}})
    df = pd.DataFrame(list(docs))
    print(df.tail())
    df.index = pd.to_datetime(df.ts, unit='s')
    del df['_id']
    return df


def read_csv():
    df = pd.read_csv(filename, names=['ts', 'price', 'volume'])
    df.index = pd.to_datetime(df.ts, unit='s')
    df = df.loc[start_date:end_date]
    df = df['price'].resample(time_range).ohlc()
    return df


def save_to_db(symbol, grouping_range, df):
    collection, collection_name = get_collection(grouping_range, symbol)
    df['ts'] = pd.to_datetime(df.index)
    records = df.to_dict('records')
    ops = [operations.ReplaceOne(
        filter={"ts": record["ts"]},
        replacement=record,
        upsert=True
    ) for record in records]

    result = collection.bulk_write(ops)


def save_ticks(db_instance, symbol, records):
    collection_name = build_collection_name(symbol, 'ticks')
    collection = db_instance[collection_name]
    ops = [operations.ReplaceOne(
        filter={"ts": record["ts"]},
        replacement=record,
        upsert=True
    ) for record in records]

    try:
        collection.bulk_write(ops)
    except BulkWriteError as bwe:
        print(red("Errors when writing ticks:"))
        dump(bwe.details)
    print(green("Saved %i ticks to %s. Last from %s." % (len(records), collection_name, records[-1]['ts'])))


def build_collection_name(symbol, grouping_range):
    return str.join('_', (symbol.replace('/', '_').replace('-', '_'), grouping_range))
