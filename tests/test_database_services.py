import datetime
from unittest import TestCase
from pymongo import MongoClient
from settings.config import mongo_uri
from database.services import save_ticks, build_collection_name


def get_mocked_time():
    return datetime.datetime.now().isoformat()


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

    def test_adding_simple_record_works(self):
        symbol = 'test'
        collection_name = 'test_ticks'
        counter = self.test_db[collection_name].count()
        self.assertEqual(counter, 0)

        records = [{'last': 123.0, 'ts': get_mocked_time()}]
        save_ticks(self.test_db, symbol, records)
        counter = self.test_db[collection_name].count()
        self.assertEqual(counter, len(records))
