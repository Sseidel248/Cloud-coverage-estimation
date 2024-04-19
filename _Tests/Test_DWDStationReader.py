import os
import unittest
import _Tests.testConsts as tc
from datetime import datetime
from Lib.DWDStationReader import DWDStations, CorruptedInitFileError
from Lib.IOConsts import *


class TestDWDStations(unittest.TestCase):
    def test__init__(self):
        dwds = DWDStations()
        self.assertEqual(0, len(dwds.df))

    def test_invalid_load_folder(self):
        dwds = DWDStations()
        # invalid or empty path
        self.assertRaises(FileNotFoundError, dwds.load_folder, f".\\Dummy")
        self.assertRaises(FileNotFoundError, dwds.load_folder, tc.TEST_DIR_EMPTY)
        # missing init file
        self.assertRaises(FileNotFoundError, dwds.load_folder, tc.TEST_DIR_DWD_WITHOUT_INIT_FILE)
        # empty init file
        self.assertRaises(CorruptedInitFileError, dwds.load_folder, tc.TEST_DIR_DWD_CORRUPTED_INIT_FILE)

    def test_load_folder(self):
        # remove extracted test file
        os.remove(f"{tc.TEST_DIR_DWD}\\produkt_n_stunde_20220804_20240204_00096.txt")
        dwds = DWDStations()
        # valid loading
        dwds.load_folder(tc.TEST_DIR_DWD)
        self.assertEqual(2, len(dwds.get_station_locations()))
        self.assertTrue(96 in dwds.df[COL_STATION_ID].values)
        self.assertTrue(91 in dwds.df[COL_STATION_ID].values)
        self.assertTrue(dwds.df.loc[dwds.df[COL_STATION_ID] == 96, COL_DWD_LOADED].iloc[0])
        self.assertFalse(dwds.df.loc[dwds.df[COL_STATION_ID] == 91, COL_DWD_LOADED].iloc[0])

    def test_get_values(self):
        dwds = DWDStations()
        dwds.load_folder(tc.TEST_DIR_DWD)
        # invalid lat lon
        empty_df = dwds.get_values(datetime(2022, 8, 4, 1),
                                   90,
                                   0,
                                   False,
                                   ["V_N"])
        self.assertEqual(0, len(empty_df))
        # parameter not exist
        empty_df = dwds.get_values(datetime(2022, 8, 4, 1),
                                   52.9437,
                                   12.8518,
                                   False,
                                   ["T0"])
        self.assertEqual(0, len(empty_df))
        # valid single Value
        value_df = dwds.get_values(datetime(2022, 8, 4, 1),
                                   52.9437,
                                   12.8518,
                                   False,
                                   ["V_N"])
        value = int(value_df["V_N"].iloc[0])
        self.assertEqual(5, value)
        # values for all params
        value_df = dwds.get_values(datetime(2022, 8, 4, 1),
                                   52.9437,
                                   12.8518,
                                   True)
        value = int(value_df["V_N"].iloc[0])
        self.assertEqual(5, value)

