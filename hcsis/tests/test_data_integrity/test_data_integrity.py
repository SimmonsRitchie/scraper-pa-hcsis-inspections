import unittest
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from logging import StreamHandler
import re

root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
# stream handler
stream_log = StreamHandler()
root_logger.addHandler(stream_log)

def trim_and_upper(list_of_things):
    return [thing.upper().strip() for thing in list_of_things]


class TestDataIntegrity1(unittest.TestCase):
    """ These tests check whether scraped data matches data on HCSIS website """

    def setUp(self) -> None:
        pd.set_option("display.max_columns", 40)
        pd.set_option("display.width", 2000)
        pd.set_option("display.max_rows", 2000)

        data_dir = Path("../../scraped_data/")
        data_file_path = list(data_dir.glob('*.csv'))[0] # get first csv in dir
        self.df = pd.read_csv(data_file_path, dtype={'provider_id': 'object', 'service_location_id': 'object'})
        provider_names = self.df['provider_name'].unique().tolist()
        self.provider_names = trim_and_upper(provider_names)

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
            },
            {
                "provider_id": "1763",
                "service_location_id": "0002",
                "assert_count": 15
            },
            {
                "provider_id": "1440",
                "service_location_id": "0461",
                "assert_count": 3
            },
            {
                "provider_id": "1817",
                "service_location_id": "0005",
                "assert_count": 6
            },
        ]

        df = self.df
        root_logger.debug("TEST: Correct number of inspection rows for a variety of providers")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, service_location: {assert_item['service_location_id']}")
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["service_location_id"] == assert_item[
                "service_location_id"])]
            count = len(df_test.index)

            self.assertEqual(assert_item["assert_count"], count)

    def test_service_location_id_correct(self):
        """Test that service location ID matches service location name"""

        assert_data = [
            {
                "provider_id": "401491",
                "service_location_id": "0007",
                "service_location": "South Ct",

            }
        ]

        df = self.df
        root_logger.debug("TEST: correct service location ID matches name")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, service_location_id: {assert_item['service_location']}")
            correct_val = assert_item["service_location"]
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["service_location_id"] == assert_item[
                "service_location_id"])]
            df_test = df_test["service_location"].values[0]
            root_logger.debug(f"service location is {df_test}")
            self.assertEqual(df_test, correct_val)

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
            },
            # 90 Cafferty Rd Operating Company
            {
                "provider_id": "359707",
                "inspection_id": "SIN-00116668",
                "assert_count": 1
            },
            # WAKEFIELD COTTAGE ARAPAHOE
            {
                "provider_id": "1897",
                "inspection_id": "SIN-00089395",
                "assert_count": 1
            },
            {
                "provider_id": "384275",
                "inspection_id": "SIN-00117015",
                "assert_count": 1
            },
            {
                "provider_id": "1817",
                "inspection_id": "SIN-00042335",
                "assert_count": 2
            },
            {
                "provider_id": "425975",
                "inspection_id": "SIN-00107126",
                "assert_count": 4
            },
            {
                "provider_id": "425975",
                "inspection_id": "SIN-00129909",
                "assert_count": 42
            },
            {
                "provider_id": "416894",
                "inspection_id": "SIN-00161701",
                "assert_count": 4
            },
            {
                "provider_id": "3213",
                "inspection_id": "SIN-00102676",
                "assert_count": 7
            },
            {
                "provider_id": "3213",
                "inspection_id": "SIN-00066080",
                "assert_count": 2
            },
            {
                "provider_id": "2048",
                "inspection_id": "SIN-00144697",
                "assert_count": 1
            },
        ]

        df = self.df
        root_logger.debug("TEST: correct number of violations for specific inspections")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, inspection_id: {assert_item['inspection_id']}")
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["inspection_id"] == assert_item[
                "inspection_id"])]
            count = len(df_test.index)
            self.assertEqual(assert_item["assert_count"], count)


    def test_no_certified_providers(self):
        """
        Test that certain providers have no certified locations
        """

        # list of provider IDs
        assert_data = [
            "411713",
            "416911",
            "396604",
            "391308"
        ]

        df = self.df
        root_logger.debug("TEST: provider has no certified locations")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item}")
            df_test = df[df["provider_id"] == assert_item]
            test_val = df_test["service_location"].values[0]
            self.assertEqual("No certified locations", test_val)


    def test_text_matches_row(self):
        """
        Test that text in regulation column is correct.
        """
        assert_data = [
                {
                "provider_id": "3213",
                "inspection_id": "SIN-00066080",
                "assert_reg": "2390.158(b)"
            },
            {
                "provider_id": "3213",
                "inspection_id": "SIN-00080038",
                "assert_reg": "2390.151(e)(13(ii)"
            },
            {
                "provider_id": "2106",
                "inspection_id": "SIN-00051643",
                "assert_reg": "2380.186(d)"
            },
            {
                "provider_id": "2106",
                "inspection_id": "SIN-00069441",
                "assert_reg": np.NaN
            },
            {
                "provider_id": "1744",
                "inspection_id": "SIN-00108172",
                "assert_reg": "6400.186(c)(1)"
            },
            {
                "provider_id": "1744",
                "inspection_id": "SIN-00135807",
                "assert_reg": "6400.112(f)"
            },
        ]

        df = self.df
        root_logger.debug("TEST: expected violation name is included among violations in inspection")
        for assert_item in assert_data:
            root_logger.debug(f"Testing: {assert_item['provider_id']}, inspection_id: {assert_item['inspection_id']}")
            df_test = df[(df["provider_id"] == assert_item["provider_id"]) & (df["inspection_id"] == assert_item[
                "inspection_id"])]
            test_list = df_test['regulation'].tolist()
            truth_test = assert_item['assert_reg'] in test_list
            self.assertTrue(truth_test)


    def test_provider_names_present(self):
        """ Test that selected provider names are included in data """

        # load
        assert_data_path = Path('../assert_data/provider_names.csv')
        df_assert = pd.read_csv(assert_data_path)

        # clean
        assert_list = df_assert['provider_names'].to_list()
        assert_list = trim_and_upper(assert_list)
        root_logger.debug(f"TEST: {len(assert_list)} provider names are included in"
                          f" scraped data ({len(self.provider_names)})")
        root_logger.debug(self.provider_names)

        # test
        false_list = []
        for assert_item in assert_list:
            name_check = True if assert_item in self.provider_names else False
            if not name_check:
                false_list.append(assert_item)

        root_logger.debug(f"Non-matching items: {false_list}")
        full_name_check = set(assert_list).issubset(self.provider_names)
        self.assertTrue(full_name_check)


    def test_service_coordinators_not_present(self):
        """ Test that service coordination agencies have been excluded from the scraped data"""

        # load
        assert_data_path = Path('../assert_data/service_coordination_agencies.csv')
        df_assert = pd.read_csv(assert_data_path)

        # clean
        assert_list = df_assert['service_coordination_agency'].to_list()
        assert_list = trim_and_upper(assert_list)
        root_logger.debug(f"TEST: {len(assert_list)} service coordinators are NOT included in scraped "
                          f"data ({len(self.provider_names)})")
        root_logger.debug(self.provider_names)

        # test
        false_list = []
        for assert_item in assert_list:
            name_check = True if assert_item in self.provider_names else False
            if not name_check:
                false_list.append(assert_item)

        root_logger.debug(f"Non-matching items: {false_list}")
        full_name_check = set(assert_list).issubset(self.provider_names)
        self.assertFalse(full_name_check)

if __name__ == "__main__":
    unittest.main()
