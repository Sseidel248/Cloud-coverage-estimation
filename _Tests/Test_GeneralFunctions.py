import unittest
import numpy as np
import Lib.GeneralFunctions as gFunc
import _Tests.testConsts as tc
from datetime import datetime


class TestGeneralFunctions(unittest.TestCase):
    def test_get_files(self):
        self.assertEqual(0, len(gFunc.get_files(tc.TEST_DIR_EMPTY, ".txt")))
        self.assertEqual(1, len(gFunc.get_files(tc.TEST_DIR_DWD_WITHOUT_INIT_FILE, ".txt")))

    def test_round_to_nearest_hour(self):
        self.assertEqual(gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 10, 27)),
                         datetime(2023, 12, 27, 10))
        self.assertEqual(gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 9, 38)),
                         datetime(2023, 12, 27, 10))
        self.assertEqual(gFunc.round_to_nearest_hour(np.datetime64("2023-12-27T10:27:00")),
                         np.datetime64("2023-12-27T10", "h"))
        self.assertEqual(gFunc.round_to_nearest_hour(np.datetime64("2023-12-27T09:38:00")),
                         np.datetime64("2023-12-27T10", "h"))
        self.assertRaises(TypeError, gFunc.round_to_nearest_hour, "2023.12.27 9:38")

    def test_hours_difference(self):
        date1: datetime = datetime(2023, 12, 27, 10, 0)
        date2: datetime = datetime(2023, 12, 27, 6, 30)
        self.assertEqual(0, gFunc.hours_difference(date1, date1), )
        self.assertEqual(3.5, gFunc.hours_difference(date1, date2))

    def test_datetime_to_strf(self):
        self.assertEqual("2023122710",
                         gFunc.datetime_to_strf(datetime(2023, 12, 27, 10, 27)))
        self.assertEqual("2023122710",
                         gFunc.datetime_to_strf(np.datetime64("2023-12-27T10:27:00")))

    def test_int_def(self):
        self.assertEqual(-1, gFunc.int_def("Hallo", -1))
        self.assertEqual(200, gFunc.int_def("200", -1))

    def test_convert_in_0_360(self):
        self.assertEqual(240, gFunc.convert_in_0_360(-120))
        self.assertEqual(120, gFunc.convert_in_0_360(120))
        self.assertEqual(40, gFunc.convert_in_0_360(400))
        self.assertEqual(320, gFunc.convert_in_0_360(-400))

    def test_convert_in_180_180(self):
        self.assertEqual(-120, gFunc.convert_in_180_180(240))
        self.assertEqual(120, gFunc.convert_in_180_180(120))
        self.assertEqual(40, gFunc.convert_in_180_180(400))
        self.assertEqual(-40, gFunc.convert_in_180_180(-400))
