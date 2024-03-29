"""
File name:      DataAnalysis.py
Author:         Sebastian Seidel
Date:           2024.01.22

This Python module contains a collection of utility functions designed to process and analyze weather
station data. It includes functions to calculate error metrics, filter and describe data, and perform
various checks and descriptive statistics on weather station measurements.

Functions in this module:
- filter_dataframe_by_value: Filters the given DataFrame based on specific value.
- calc_abs_error: Calculates the absolute error.
- get_abs_error_each_station: Computes mean absolute error for each station.
- get_me_mae_rmse: Calculates ME, MAE, and RMSE for a given DataFrame.
- get_dwd_height_details: Provides descriptive statistics for the station height column.

Each function is documented with a detailed description, parameters, and return values.
"""
import numpy as np
import pandas as pd
from pandas import DataFrame, Series
from scipy.stats import normaltest, pearsonr, spearmanr  # serves as interface
from typing import Tuple
from Lib.IOConsts import *


def _check_column_name_exist(df: DataFrame, column_name: str) -> None:
    """
    Checks if the specified column name exists in the given DataFrame.
    Raises a ValueError if the column name is not found.

    :param df: DataFrame in which to check for the column name.
    :param column_name: The name of the column to be checked for existence.
    :return: None. Raises an exception if the column name does not exist.
    """
    if column_name not in df:
        raise ValueError(f"The column '{column_name}' is missing in the DataFrame df.")


def filter_dataframe_by_value(df: DataFrame, column_name: str, value: float, greater_than: bool = True) -> DataFrame:
    """
    Filters the given DataFrame based on whether the values in the specified column
    are greater than or less than a specified value.

    :param df: The DataFrame to be filtered.
    :param column_name: The name of the column on which the filter will be applied.
    :param value: The value to be compared against the column values.
    :param greater_than: A boolean flag to determine the filter type. If True, the function
                         filters out rows where the column value is greater than the specified value.
                         If False, it filters out rows where the column value is less than the specified value.
    :return: A DataFrame filtered according to the specified column, value, and filter type.
    """
    _check_column_name_exist(df, column_name)
    if greater_than:
        return df[df[column_name] > value]
    else:
        return df[df[column_name] < value]


def calc_abs_error(df: DataFrame, col_model: str, col_dwd: str) -> None:
    """
    Calculates the absolute error between two columns in a DataFrame and adds the result as a new column named
    "Absolute_Error".

    :param df: The DataFrame containing the columns to be compared.
    :param col_model: The name of the first column to be used in the calculation.
    :param col_dwd: The name of the second column to be used in the calculation.
    :return: None. The function adds a new column to the DataFrame containing the absolute error.
    """
    _check_column_name_exist(df, col_model)
    _check_column_name_exist(df, col_dwd)
    df[COL_ABS_ERROR] = abs(df[col_model] - df[col_dwd])


def get_error_metric_each_station(df: DataFrame, col_model: str, col_dwd: str) -> DataFrame:
    """
    Calculates error metrics for different stations in a DataFrame.
    The function computes the Mean Error (ME), Mean Absolute Error (MAE), and
    Root Mean Squared Error (RMSE) for each station based on the specified columns.

    :param df: The DataFrame containing the data.
    :param col_model: The name of the column representing the model values.
    :param col_dwd: The name of the column representing the observed values.
    :return: A DataFrame with the error metrics (ME, MAE, RMSE) calculated for each station.
    """
    _check_column_name_exist(df, col_model)
    _check_column_name_exist(df, col_dwd)
    _check_column_name_exist(df, COL_ABS_ERROR)
    _check_column_name_exist(df, COL_STATION_ID)
    station_error_metrics = df.groupby(COL_STATION_ID).apply(
        lambda df_tmp: pd.Series({
            COL_ME: (df_tmp[col_model] - df_tmp[col_dwd]).mean(),
            COL_MAE: df_tmp[COL_ABS_ERROR].mean(),
            COL_RMSE: np.sqrt(np.mean(df_tmp[COL_ABS_ERROR] ** 2))
        })
    ).reset_index()
    return station_error_metrics


def get_mean_abs_error_each_station(df: DataFrame) -> DataFrame:
    """
    Calculates the mean absolute error for each station in the DataFrame.

    :param df: The DataFrame containing the data with absolute errors and station IDs.
    :return: A DataFrame with two columns: station ID and the mean absolute error for each station.
    """
    _check_column_name_exist(df, COL_STATION_ID)
    _check_column_name_exist(df, COL_ABS_ERROR)
    station_errors: DataFrame = df.groupby(COL_STATION_ID)[COL_ABS_ERROR].mean().reset_index()
    station_errors.columns = [COL_STATION_ID, COL_MEAN_ABS_ERROR]
    return station_errors


def get_me_mae_rmse(df: DataFrame, col_model: str, col_dwd: str) -> Tuple[float, float, float]:
    """
    Calculates the Mean Error (ME), Mean Absolute Error (MAE), and
    Root Mean Squared Error (RMSE) for the given DataFrame based on the specified columns.

    :param df: The DataFrame containing the model and observed data.
    :param col_model: The name of the column representing the model values.
    :param col_dwd: The name of the column representing the observed values.
    :return: A tuple containing the ME, MAE, and RMSE values.
    """
    _check_column_name_exist(df, col_model)
    _check_column_name_exist(df, col_dwd)
    error = df[col_model] - df[col_dwd]
    me = error.mean()
    mae = abs(error).mean()
    rmse = np.sqrt(np.mean(error ** 2))
    return me, mae, rmse


def get_dwd_col_details(df: DataFrame, col_name: str) -> Series:
    """
    Provides descriptive statistics for the station height column in the given DataFrame.

    :param df: The DataFrame containing the height data of the stations.
    :param col_name: Specifies the column to be described.
    :return: A pandas Series containing descriptive statistics (count, mean, std, min, 25%, 50%, 75%, max)
             for a dwd-station data column.
    """
    _check_column_name_exist(df, col_name)
    tmp = df[col_name].dropna()
    return tmp.describe()


def calc_custom_z_score(df: DataFrame, col_name: str, limit: float) -> DataFrame:
    """
    Calculates a custom Z-Score for a specified column in a Pandas DataFrame and adds it as a new column named
    "Z_SCORE".

    This custom Z-Score is computed using a modified formula: (value - limit) / custom_standard_deviation, where the
    custom standard deviation is calculated based on the difference from a specified limit rather than the mean of the
    column. This function checks if the specified column name exists in the DataFrame, calculates the custom Z-Score
    for each value in the column using the specified limit, and then adds these custom Z-Scores as a new column to the
    DataFrame.

    :param df: A Pandas DataFrame containing the data.
    :param col_name: The name of the column for which to calculate the custom Z-Score.
    :param limit: A float representing the limit used to calculate the difference for the custom Z-Score instead of
    using the mean.
    :return: The original DataFrame with an additional column named "Z_SCORE" for the custom Z-Score of the specified
    column.
    """
    _check_column_name_exist(df, col_name)
    custom_std = np.sqrt(np.sum((df[col_name] - limit) ** 2) / df[col_name].count() - 1)
    df[COL_Z_SCORE] = (df[col_name] - limit) / custom_std
    return df


def calc_corr_coef(pvalue: float, df: DataFrame, col_name1: str, col_name2: str) -> Tuple[float, float]:
    _check_column_name_exist(df, col_name1)
    _check_column_name_exist(df, col_name2)
    data = df[[col_name1, col_name2]].dropna()
    # Data not normally distributed
    if pvalue > 0.05:
        coef, pvalue = pearsonr(data[col_name1], data[col_name2])
    # Data normally distributed
    else:
        coef, pvalue = spearmanr(data[col_name1], data[col_name2])
    return coef, pvalue

