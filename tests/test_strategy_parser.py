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


class TestStrategyParser(TestCase):
    client: MongoClient = None
    test_db = 'test'

    def setUp(self):
        self.client = MongoClient(mongo_uri)
        self.test_db = self.client[self.test_db]

    def tearDown(self):
        self.client.drop_database(self.test_db)

    def testConditionsPass(self):
        df =