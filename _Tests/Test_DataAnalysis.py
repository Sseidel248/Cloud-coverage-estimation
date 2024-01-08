import unittest
import numpy as np
import Plots.DataAnalysis as da
from numpy.typing import NDArray


class TestDataAnalysis(unittest.TestCase):
    def setUp(self):
        self.actual: NDArray = np.array([1, 2, 3, 4, 5, 6])
        self.predicted: NDArray = np.array([1, 5, 3, 2, 5, 5])
        self.error: NDArray = self.actual - self.predicted

    def test_mean_error(self):
        excepted: float = 0.00
        calculated: float = round(da.mean_error(self.actual, self.predicted), 2)
        self.assertEqual(calculated, excepted)

    def test_mean_abs_error(self):
        excepted: float = 1.00
        calculated: float = round(da.mean_absolute_error(self.actual, self.predicted), 2)
        self.assertEqual(calculated, excepted)

    def test_mean_sqrt_error(self):
        excepted: float = 1.53
        calculated: float = round(da.mean_sqrt_error(self.actual, self.predicted), 2)
        self.assertEqual(calculated, excepted)

    def test_mean_abs_accuracy(self):
        excepted: float = 99.00
        calculated: float = round(da.mean_absolute_accuracy(self.actual, self.predicted), 2)
        self.assertEqual(calculated, excepted)

    def test_mean_sqrt_accuracy(self):
        excepted: float = 98.47
        calculated: float = round(da.mean_sqrt_accuracy(self.actual, self.predicted), 2)
        self.assertEqual(calculated, excepted)

    def test_get_index_filter_by_accuracy_thershold(self):
        excepted: list[bool] = [False, True, False, False, False, False]
        actual: list[bool] = da.get_index_filter_by_accuracy_thershold(self.actual, self.predicted, 97)
        self.assertTrue(np.array_equal(actual, excepted))
