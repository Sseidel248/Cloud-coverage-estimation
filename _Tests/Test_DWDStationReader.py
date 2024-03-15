import unittest
import _Tests.testConsts as tc
from datetime import datetime
from Lib.DWDStationReader import DWDStations
from Lib.IOConsts import *


class TestDWDStations(unittest.TestCase):
    def test__init__(self):
        dwds = DWDStations()
        self.assertEqual(0, len(dwds.df))

    def test_load_folder(self):
        dwds = DWDStations()
        dwds.load_folder(f".\\DWD_Testfiles")
        self.assertEqual(2, len(dwds.df[COL_STATION_ID].unique()))
        self.assertTrue(96 in dwds.df[COL_STATION_ID].values)
        self.assertTrue(91 in dwds.df[COL_STATION_ID].values)
        self.assertTrue(dwds.df.loc[dwds.df[COL_STATION_ID] == 96, COL_DWD_LOADED].iloc[0])
        self.assertFalse(dwds.df.loc[dwds.df[COL_STATION_ID] == 91, COL_DWD_LOADED].iloc[0])

    def test_get_value(self):
        dwds = DWDStations()
        dwds.load_folder(f".\\DWD_Testfiles")
        value_df = dwds.get_dwd_value(datetime(2022, 8, 4, 1), 52.9437, 12.8518, False, ["V_N"])
        value = int(value_df["V_N"].iloc[0])
        self.assertEqual(5, value)
