import os
import unittest
import _Tests.testConsts as tc
import numpy as np
from datetime import datetime
from Lib.Grib2Reader import Grib2Datas
from Lib.IOConsts import *


# To run tests use commandline terminal:
# 1. python -m coverage run -m unittest -v
# 2. python -m coverage html
# 3. visit htmlcov\index.html

class TestGrib2Reader(unittest.TestCase):

    def test__init__(self):
        g2d = Grib2Datas()
        self.assertEqual(0, len(g2d.df))
        self.assertEqual(0, len(g2d.df_models))
        self.assertEqual(0, len(g2d.df_invalid))

    def test_load_folder(self):
        g2d = Grib2Datas()
        self.assertRaises(FileNotFoundError, g2d.load_folder, ".\\Dummy")
        self.assertRaises(FileNotFoundError, g2d.load_folder, tc.TEST_DIR_EMPTY)
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertNotEqual(0, len(g2d.df))
        self.assertNotEqual(0, len(g2d.df_models))
        self.assertNotEqual(0, len(g2d.df_invalid))

    def test_loaded_files(self):
        # prepare the archive extraction in load_folder(...)
        if os.path.exists(f"{tc.TEST_DIR_GRIB2}\\icon-d2_clct.grib2"):
            os.remove(f"{tc.TEST_DIR_GRIB2}\\icon-d2_clct.grib2")

        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        # check df
        self.assertEqual(2, len(g2d.df[COL_MODEL]))
        self.assertTrue(g2d.df[COL_PARAM].isin(["TCDC"]).all())
        self.assertTrue(g2d.df[COL_MODEL].isin(["ICON-D2", "ICON-EU"]).all())
        self.assertTrue(g2d.df[COL_DATE].isin([datetime(2023, 11, 29, 18),
                                               datetime(2023, 11, 29, 12)]).all())
        self.assertTrue(g2d.df[COL_MODEL_FCST_DATE].isin([datetime(2023, 11, 29, 18),
                                                          datetime(2023, 11, 29, 13)]).all())
        self.assertTrue(g2d.df[COL_MODEL_FCST_MIN].isin([0, 60]).all())

        # check df_model
        self.assertEqual(2, len(g2d.df_models[COL_MODEL]))
        self.assertTrue(g2d.df_models[COL_PARAM].isin(["TCDC"]).all())
        self.assertTrue(g2d.df_models[COL_MODEL].isin(["ICON-D2", "ICON-EU"]).all())
        # round() for float comma arithmetic
        self.assertTrue(g2d.df_models[COL_MODEL_LAT_START].round(2).isin([43.18, 29.5]).all())
        self.assertTrue(g2d.df_models[COL_MODEL_LAT_END].round(2).isin([58.08, 70.5]).all())
        self.assertTrue(g2d.df_models[COL_MODEL_LON_START].round(2).isin([-3.94, -23.5]).all())
        self.assertTrue(g2d.df_models[COL_MODEL_LON_END].round(2).isin([20.34, 62.5]).all())
        self.assertTrue(g2d.df_models[COL_MODEL_LATLON_DELTA].round(4).isin([0.0200, 0.0625]).all())

        # check df_invalid
        self.assertEqual(1, len(g2d.df_invalid))
        self.assertEquals("ICON-D2", g2d.df_invalid[COL_MODEL].iloc[0])
        self.assertEquals("TCDC", g2d.df_invalid[COL_PARAM].iloc[0])
        self.assertEquals(datetime(2023, 12, 11, 6), g2d.df_invalid[COL_DATE].iloc[0])
        self.assertEquals(1200, g2d.df_invalid[COL_MODEL_FCST_MIN].iloc[0])
        self.assertEquals(datetime(2023, 12, 12, 2), g2d.df_invalid[COL_MODEL_FCST_DATE].iloc[0])

    def test_get_values(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        # invalid shape of date_times and coords
        self.assertRaises(ValueError, g2d.get_values, "ICON-D2", "TCDC",
                          datetime(2023, 11, 29, 18),
                          (54.4, 11.2, 54))
        self.assertRaises(ValueError, g2d.get_values, "ICON-D2", "TCDC",
                          [datetime(2023, 11, 29, 18), datetime(2023, 11, 29, 18)],
                          [(54.4, 11.2), (54, 14), (55, 15)])
        self.assertRaises(ValueError, g2d.get_values, "ICON-D2", "TCDC",
                          [datetime(2023, 11, 29, 18)],
                          [54])
        # invalid param
        df0 = g2d.get_values("ICON-D2",
                             "Dummy",
                             datetime(2023, 11, 29, 18),
                             (54.4, 11.2))
        self.assertEqual(1, len(df0))
        self.assertTrue(df0["Dummy"].isna().all())

        # one datetime one coordinate - Model ICON-D2
        df1 = g2d.get_values("ICON-D2",
                             "TCDC",
                             datetime(2023, 11, 29, 18),
                             (54.4, 11.2))
        self.assertEqual(98.9746, df1["TCDC"].iloc[0])

        # one datetime more than one coordinates
        df2 = g2d.get_values("ICON-D2",
                             "TCDC",
                             datetime(2023, 11, 29, 18),
                             [(54.4, 11.2), (54, 14)])
        self.assertEqual(98.9746, df2["TCDC"].iloc[0])
        self.assertEqual(100, df2["TCDC"].iloc[1])

        # more than one datetimes and more than one coordinates
        df3 = g2d.get_values("ICON-D2",
                             "TCDC",
                             [datetime(2023, 11, 29, 17, 45),
                              datetime(2023, 11, 29, 18, 15)],
                             [(54.4, 11.2), (54, 14)])
        self.assertEqual(98.9746, df3["TCDC"].iloc[0])
        self.assertEqual(100, df3["TCDC"].iloc[1])

        # more than one datetimes and one coordinates
        df4 = g2d.get_values("ICON-D2",
                             "TCDC",
                             [datetime(2023, 11, 29, 17, 45),
                              datetime(2023, 11, 29, 18, 15)],
                             [(54.4, 11.2)])
        self.assertEqual(98.9746, df4["TCDC"].iloc[0])
        self.assertEqual(98.9746, df4["TCDC"].iloc[1])

    def test_get_values_idw(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        # Model ICON-D2
        df1 = g2d.get_values_idw("ICON-D2",
                                 "TCDC",
                                 datetime(2023, 11, 29, 17, 45),
                                 [(54.4, 11.2)],
                                 0.04)
        self.assertEqual(98.97459998987652, df1["TCDC"].iloc[0])

        # Model ICON-EU
        df2 = g2d.get_values_idw("ICON-EU",
                                 "TCDC",
                                 datetime(2023, 11, 29, 17, 45),
                                 [(54.4, 11.2)],
                                 0.04)
        self.assertTrue(df2["TCDC"].isna().all())  # no matching ICON-EU file found

        # Model unknown
        df3 = g2d.get_values_idw("ICON",
                                 "TCDC",
                                 datetime(2023, 11, 29, 17, 45),
                                 [(54.4, 11.2)],
                                 0.04)
        self.assertTrue(df3["TCDC"].isna().all())  # no ICON Files found

        # coords as one tuple
        df4 = g2d.get_values_idw("ICON-D2",
                                 "TCDC",
                                 datetime(2023, 11, 29, 17, 45),
                                 (54.4, 11.2),
                                 0.04)
        self.assertEqual(98.97459998987652, df4["TCDC"].iloc[0])

        # one datetime and twi coords
        df5 = g2d.get_values_idw("ICON-D2",
                                 "TCDC",
                                 datetime(2023, 11, 29, 17, 45),
                                 [(54.4, 11.2), (53.4, 12.2)],
                                 0.04)
        self.assertEqual(98.97459998987652, df5["TCDC"].iloc[0])
