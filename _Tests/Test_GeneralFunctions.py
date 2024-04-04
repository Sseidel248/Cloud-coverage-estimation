import unittest
import Lib.GeneralFunctions as gFunc
import _Tests.testConsts as tc
from datetime import datetime


class TestGeneralFunctions(unittest.TestCase):
    def test_get_files(self):
        self.assertEqual(0, len(gFunc.get_files(tc.TEST_DIR_EMPTY, ".txt")))
        self.assertEqual(2, len(gFunc.get_files(tc.TEST_DIR_DWD, ".txt")))

    def test_round_to_nearest_hour(self):
        self.assertEqual(gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 10, 27)),
                         datetime(2023, 12, 27, 10))
        self.assertEqual(gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 9, 38)),
                         datetime(2023, 12, 27, 10))

    def test_hours_difference(self):
        date1: datetime = datetime(2023, 12, 27, 10, 0)
        date2: datetime = datetime(2023, 12, 27, 6, 30)
        self.assertEqual(0, gFunc.hours_difference(date1, date1), )
        self.assertEqual(3.5, gFunc.hours_difference(date1, date2))

    def test_int_def(self):
        self.assertEqual(-1, gFunc.int_def("Hallo", -1))
        self.assertEqual(200, gFunc.int_def("200", -1))
