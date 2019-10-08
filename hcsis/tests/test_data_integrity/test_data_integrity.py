import unittest
import pandas as pd
from pathlib import Path
import logging
from logging import StreamHandler

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# stream handler
stream_log = StreamHandler()
root_logger.addHandler(stream_log)

class TestDataIntegrity1(unittest.TestCase):
    def setUp(self) -> None:
        pd.set_option("display.max_columns", 40)
        pd.set_option("display.width", 2000)
        pd.set_option("display.max_rows", 2000)

        data_dir = Path("../../scraped_data/")
        data_file_path = list(data_dir.glob('*.csv'))[0] # get first csv in dir
        self.df = pd.read_csv(data_file_path, dtype={'provider_id': 'object', 'service_location_id': 'object'})

    def tearDown(self) -> None:
        pass

    def test_inspection_rows(self):
        """
        Test that we have correct number of inspection rows for a variety of providers
        """
        assert_data = [
                {
                "provider_id": "421754",
                "service_location_id": "0001",
                "assert_count": 4
            },  {
                "provider_id": "1763",
                "service_location_id": "0002",
                "assert_count": 15
            },  {
                "provider_id": "1440",
                "service_location_id": "0461",
                "assert_count": 3
            }
        ]

        df = self.df
        root_logger.debug("TEST: Correct number of inspection rows for a variety of providers")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, service_location: {assert_item['service_location_id']}")
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["service_location_id"] == assert_item[
                "service_location_id"])]
            count = len(df_test.index)

            self.assertEqual(assert_item["assert_count"], count)


    def test_number_of_violations_for_inspection(self):
        """
        Test that we have correct number of violations for specific inspections
        """
        assert_data = [
                {
                "provider_id": "356221",
                "inspection_id": "SIN-00157971",
                "assert_count": 32
            },  {
                "provider_id": "1513",
                "inspection_id": "SIN-00062675",
                "assert_count": 3
            },  {
                "provider_id": "1642",
                "inspection_id": "SIN-00106471",
                "assert_count": 1
            },  {
                "provider_id": "359707",
                "inspection_id": "SIN-00116668",
                "assert_count": 1
            }
        ]

        df = self.df
        root_logger.debug("TEST: correct number of violations for specific inspections")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, inspection_id: {assert_item['inspection_id']}")
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["inspection_id"] == assert_item[
                "inspection_id"])]
            count = len(df_test.index)
            self.assertEqual(assert_item["assert_count"], count)




if __name__ == "__main__":
    unittest.main()
