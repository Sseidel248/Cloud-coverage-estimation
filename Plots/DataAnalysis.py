"""
File name:      DataAnalysis.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import numpy as np
from numpy.typing import NDArray


def _check_len(data1, data2):
    if len(data1) != len(data2):
        raise ValueError("Data and errors must have the same length.")


def mean_error(station_data, model_data) -> float:
    _check_len(station_data, model_data)
    me = np.mean(np.array(station_data) - np.array(model_data))
    return me


def mean_absolute_error(station_data, model_data) -> float:
    _check_len(station_data, model_data)
    mae = np.mean(np.abs(np.array(station_data) - np.array(model_data)))
    return mae


def mean_sqrt_error(station_data, model_data) -> float:
    _check_len(station_data, model_data)
    rmse = np.sqrt(np.mean((np.array(station_data) - np.array(model_data)) ** 2))
    return rmse


def mean_absolute_accuracy(station_data, model_data) -> float:
    return 100 - mean_absolute_error(station_data, model_data)


def mean_sqrt_accuracy(station_data, model_data) -> float:
    return 100 - mean_sqrt_error(station_data, model_data)


def get_index_filter_by_accuracy_thershold(station_data, model_data, accuracy_thershold: float) -> list[bool]:
    _check_len(station_data, model_data)
    if accuracy_thershold < 0:
        raise ValueError("error_thershold must be a positive number")

    abs_accuracy = 100 - np.abs(np.array(station_data) - np.array(model_data))
    bool_mask = abs_accuracy <= accuracy_thershold
    return bool_mask



