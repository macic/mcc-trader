import datetime
import pandas as pd
from pymongo import MongoClient, operations
from pymongo.errors import BulkWriteError
from helpers.console_colors import red, dump, yellow, green
from helpers.common import convert_docs_to_df, resample_df, add_ts_based_on_index


def init_database(uri):
    return MongoClient(uri)


def get_dataframe_from_timerange(db_instance, symbol, grouping_range, ts_start, ts_end=None) -> pd.DataFrame:
    collection_name = build_collection_name(symbol, grouping_range)
    collection = db_instance[collection_name]
    iso_start = datetime.datetime.fromtimestamp(ts_start, None)

    find_query = {'$gte': iso_start}
    if ts_end:
        iso_end = datetime.datetime.fromtimestamp(ts_end, None)
        find_query['$lt'] = iso_end
    else:
        iso_end = '' #done only for printing/logging below
    print(yellow("Fetching data for %s in timeframe %s - %s" % (symbol, iso_start, iso_end)))
    docs = collection.find({"ts": find_query})
    return convert_docs_to_df(docs)

#
# def read_csv():
#     df = pd.read_csv(filename, names=['ts', 'price', 'volume'])
#     df.index = pd.to_datetime(df.ts, unit='s')
#     df = df.loc[start_date:end_date]
#     df = df['price'].resample(time_range).ohlc()
#     return df


def save_data(db_instance, symbol, records, grouping_range='ticks'):
    collection_name = build_collection_name(symbol, grouping_range)
    collection = db_instance[collection_name]
    for record in records:
        print(record)
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


def resample_and_save_ticks(db_instance, symbol, grouping_range, ts_start):
    ticks = get_dataframe_from_timerange(db_instance, symbol, 'ticks', ts_start)
    df = resample_df(ticks, 'last', grouping_range)
    df = add_ts_based_on_index(df)
    records = df.to_dict('records')
    save_data(db_instance, symbol, records, grouping_range)

def build_collection_name(symbol, grouping_range):
    return str.join('_', (symbol.replace('/', '_').replace('-', '_'), grouping_range))
