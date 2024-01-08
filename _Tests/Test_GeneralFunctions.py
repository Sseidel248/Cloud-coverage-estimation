import unittest
import Lib.GeneralFunctions as gFunc
import _Tests.testConsts as tc
from datetime import datetime


class TestGeneralFunctions(unittest.TestCase):
    def test_get_files(self):
        self.assertEqual(len(gFunc.get_files(tc.EMPTY_TEST_DIR, ".txt")), 0)
        self.assertEqual(len(gFunc.get_files(tc.TEST_DIR_DWD_ONLY_INIT, ".txt")), 1)

    def test_round_to_nearest_hour(self):
        self.assertEqual(datetime(2023, 12, 27, 10),
                         gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 10, 27)))
        self.assertEqual(datetime(2023, 12, 27, 10),
                         gFunc.round_to_nearest_hour(datetime(2023, 12, 27, 9, 38)))

    def test_hours_difference(self):
        date1:datetime = datetime(2023, 12, 27, 10, 0)
        date2:datetime = datetime(2023, 12, 27, 6, 30)
        self.assertEqual(gFunc.hours_difference(date1, date1), 0)
        self.assertEqual(gFunc.hours_difference(date1, date2), 3.5)

    def test_int_def(self):
        self.assertEqual(gFunc.int_def("Hallo", -1), -1)
        self.assertEqual(gFunc.int_def("200", -1), 200)
