import datetime
import pandas as pd
from pymongo import MongoClient, operations, ASCENDING
from pymongo.errors import BulkWriteError
from helpers.common import convert_docs_to_df, resample_df, add_ts_based_on_index, convert_orders_to_df, resample_ohlc
from helpers.logger import log
from settings.config import mongo_db, mongo_uri


def init_database(uri):
    return MongoClient(uri)


# @todo make db_instance optional in methods, and use this if not set
client = init_database(mongo_uri)
db_instance = client[mongo_db]


def get_dataframe_from_timerange(db_instance, symbol, grouping_range, ts_start, ts_end=None) -> pd.DataFrame:
    collection_name = build_collection_name(symbol, grouping_range)
    collection = db_instance[collection_name]
    iso_start = datetime.datetime.fromtimestamp(ts_start, None)

    find_query = {'$gte': iso_start}
    if ts_end:
        iso_end = datetime.datetime.fromtimestamp(ts_end, None)
        find_query['$lt'] = iso_end
    else:
        iso_end = ''  # done only for printing/logging below
    log.debug("Fetching data for timeframe", extra={'symbol': symbol, 'grouping_range': grouping_range,
                                                    'ts_start': ts_start, 'ts_end':ts_end})
    docs = collection.find({"ts": find_query}).sort([("ts", ASCENDING)])
    return convert_docs_to_df(docs)


def save_data(symbol, records, grouping_range='ticks'):
    collection_name = build_collection_name(symbol, grouping_range)
    collection = db_instance[collection_name]
    ops = [operations.ReplaceOne(
        filter={"ts": record["ts"]},
        replacement=record,
        upsert=True
    ) for record in records]

    try:
        collection.bulk_write(ops)
    except BulkWriteError as bwe:
        log.error("Errors when writing records:", extra={'details': bwe.details})
    log.info("Saved records.", extra={'last_ts':records[-1]['ts'], 'symbol': symbol, 'grouping_range': grouping_range})


def resample_and_save_ticks(ticks, symbol, grouping_range, price_field='last'):
    df = resample_df(ticks, price_field, grouping_range)
    df = add_ts_based_on_index(df)
    records = df.to_dict('records')
    save_data(symbol, records, grouping_range)


def resample_and_save(ohlc, symbol, to_grouping):
    df = resample_ohlc(ohlc, to_grouping)
    df = add_ts_based_on_index(df)
    records = df.to_dict('records')
    save_data(symbol, records, to_grouping)


def build_collection_name(symbol, grouping_range):
    return str.join('_', (symbol.replace('/', '_').replace('-', '_'), grouping_range))


def get_last_order(symbol, status="open"):
    from trade.order import Order
    docs = db_instance['orders'].find_one({"symbol": symbol, "status": status})
    if docs:
        del docs['_id']
        return Order(**docs)  # todo doesnt belong here!
    return False


def get_orders(symbol, ts_start, ts_end=None) -> pd.DataFrame:
    iso_start = datetime.datetime.fromtimestamp(ts_start, None)

    find_query = {'$gte': iso_start}
    if ts_end:
        iso_end = datetime.datetime.fromtimestamp(ts_end, None)
        find_query['$lt'] = iso_end
    else:
        iso_end = ''  # done only for printing/logging below
    log.debug("Fetching orders.", extra={'symbol': symbol, 'iso_start': iso_start, 'iso_end': iso_end})
    docs = db_instance['orders'].find({'symbol': symbol, "open_ts": find_query}).sort([("open_ts", ASCENDING)])
    return convert_orders_to_df(docs)


def save_order(data):
    db_instance['orders'].replace_one({'id': data['id']}, replacement=data, upsert=True)


def save_balance(data):
    data['currency'] = 'USD'
    db_instance['balance'].replace_one({'currency': 'USD'}, replacement=data, upsert=True)


def clear_collection(collection_name):
    db_instance[collection_name].remove({})
