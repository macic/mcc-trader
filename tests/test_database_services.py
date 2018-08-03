import datetime
from time import time
from unittest import TestCase
from pymongo import MongoClient
from settings.config import mongo_uri
from database.services import save_data, build_collection_name, resample_and_save_ticks, get_dataframe_from_timerange
from helpers.common import convert_docs_to_df

def get_mocked_time(ts=None):
    if not ts:
        return datetime.datetime.now().isoformat()
    else:
        return datetime.datetime.fromtimestamp(ts, None)


class TestDatabaseServices(TestCase):
    client: MongoClient = None
    test_db = 'test'

    def setUp(self):
        self.client = MongoClient(mongo_uri)
        self.test_db = self.client[self.test_db]

    def tearDown(self):
        self.client.drop_database(self.test_db)

    def test_build_collection_name(self):
        collection_name = build_collection_name('sym/bol', 'grouping')
        self.assertEqual('sym_bol_grouping', collection_name)

    def test_save_ticks(self):
        symbol = 'test'
        collection_name = 'test_ticks'
        counter = self.test_db[collection_name].count()
        self.assertEqual(counter, 0)

        records = [{'last': 123.0, 'ts': get_mocked_time()}]
        save_data(self.test_db, symbol, records)
        counter = self.test_db[collection_name].count()
        self.assertEqual(counter, len(records))

    def test_get_data_from_timerange(self):
        ts_now = time()
        ts_5min_from_now = ts_now + 5 * 60 + 1

        symbol = 'btcusd'
        ticks_collection_name = 'btcusd_ticks'

        records = [
            {'last': 100.0, 'ts': get_mocked_time(ts_now)},
            {'last': 103.0, 'ts': get_mocked_time(ts_5min_from_now)},
        ]
        save_data(self.test_db, symbol, records)

        counter = self.test_db[ticks_collection_name].count()
        self.assertEqual(counter, len(records))

        df = get_dataframe_from_timerange(self.test_db, symbol, 'ticks', ts_now - 1, ts_now + 50)
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]['last'], 100.0)

    def test_resample_and_save_ticks(self):
        ts_now = time()
        ts_5min_from_now = ts_now + 5 * 60 + 1
        ts_10min_from_now = ts_5min_from_now + 5 * 60 + 1

        symbol = 'btcusd'
        ticks_collection_name = 'btcusd_ticks'

        grouping_range = '5T'
        converted_collection_name = 'btcusd_5T'

        counter = self.test_db[ticks_collection_name].count()
        self.assertEqual(counter, 0)

        records = [
            {'last': 100.0, 'ts': get_mocked_time(ts_now)},
            {'last': 101.0, 'ts': get_mocked_time(ts_now + 3)},
            {'last': 102.0, 'ts': get_mocked_time(ts_now + 6)},
            {'last': 103.0, 'ts': get_mocked_time(ts_5min_from_now)},
            {'last': 104.0, 'ts': get_mocked_time(ts_5min_from_now + 3)},
            {'last': 105.0, 'ts': get_mocked_time(ts_5min_from_now + 6)},
            {'last': 106.0, 'ts': get_mocked_time(ts_10min_from_now)},
            {'last': 107.0, 'ts': get_mocked_time(ts_10min_from_now + 3)},
            {'last': 108.0, 'ts': get_mocked_time(ts_10min_from_now + 6)},
        ]
        save_data(self.test_db, symbol, records)

        counter = self.test_db[ticks_collection_name].count()
        self.assertEqual(counter, len(records))

        # testing resampling here
        resample_and_save_ticks(self.test_db, symbol, grouping_range, ts_now -1)

        results = convert_docs_to_df(self.test_db[converted_collection_name].find())
        self.assertEqual(len(results), 3)
        self.assertEqual(results.iloc[0]['open'], 100.0)
        self.assertEqual(results.iloc[0]['low'], 100.0)
        self.assertEqual(results.iloc[0]['high'], 102.0)
        self.assertEqual(results.iloc[0]['close'], 102.0)
        self.assertEqual(results.iloc[1]['open'], 103.0)
        self.assertEqual(results.iloc[1]['low'], 103.0)
        self.assertEqual(results.iloc[1]['high'], 105.0)
        self.assertEqual(results.iloc[1]['close'], 105.0)
        self.assertEqual(results.iloc[2]['open'], 106.0)
        self.assertEqual(results.iloc[2]['low'], 106.0)
        self.assertEqual(results.iloc[2]['high'], 108.0)
        self.assertEqual(results.iloc[2]['close'], 108.0)