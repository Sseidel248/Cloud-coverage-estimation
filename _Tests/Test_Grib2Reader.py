import unittest
import _Tests.testConsts as tc
from datetime import datetime
from Lib.Grib2Reader import Grib2Datas
from Lib.IOConsts import *


class TestGrib2Reader(unittest.TestCase):
    def test__init__(self):
        g2d = Grib2Datas()
        self.assertEqual(0, len(g2d.df))
        self.assertEqual(0, len(g2d.df_models))
        self.assertEqual(0, len(g2d.df_invalid))

    def test_load_folder(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertEqual(2, len(g2d.df))
        self.assertEqual(2, len(g2d.df_models))
        self.assertEqual(1, len(g2d.df_invalid))

    def test_count(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertEqual(2, g2d.count())

    def test_get_used_datetimes(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertEqual(1, len(g2d.get_used_datetimes(MODEL_ICON_D2)))
        self.assertEqual(1, len(g2d.get_used_datetimes(MODEL_ICON_EU)))

    def test_exist_datetime(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertTrue(g2d.exist_datetime(datetime(2023, 11, 29, 13)))
        self.assertFalse(g2d.exist_datetime(datetime(2023, 11, 29, 13), MODEL_ICON_D2))
        self.assertTrue(g2d.exist_datetime(datetime(2023, 11, 29, 13), MODEL_ICON_EU))

    def test_get_value(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        self.assertEqual(100, g2d.get_value(MODEL_ICON_D2,
                                            CLOUD_COVER,
                                            datetime(2023, 11, 29, 14),
                                            53,
                                            13))

    def test_get_multiple_values(self):
        g2d = Grib2Datas()
        g2d.load_folder(tc.TEST_DIR_GRIB2)
        df = g2d.get_multiple_values(MODEL_ICON_D2,
                                     CLOUD_COVER,
                                     datetime(2023, 11, 29, 14),
                                     [(53, 13), (55, 15)])
        self.assertEqual(2, len(df))
        self.assertEqual(100, df[COL_MODEL_VALUE].iloc[0])
        self.assertEqual(100, df[COL_MODEL_VALUE].iloc[1])

# TODO: automatische Test weitermachen
