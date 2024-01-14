"""
File name:      DataAnalysis.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import numpy as np
import pandas as pd
from Lib.Consts import DataExportConsts as dc
from pandas import DataFrame, Series
from typing import Tuple


def _check_column_name_exist(df: DataFrame, column_name: str) -> None:
    if column_name not in df:
        raise ValueError(f"The column '{column_name}' is missing in the DataFrame df.")


def filter_dataframe_by_value(df: DataFrame, column_name: str, value: float, greater_than: bool = True) -> DataFrame:
    """
    Filter a DataFrame based on whether the values in a specified column
    are greater than or less than a given value.

    Parameters:
    df (pandas.DataFrame): The DataFrame to filter.
    column_name (str): The name of the column to apply the filter on.
    value (float): The value to compare against.
    greater_than (bool): If True, return rows where the column value is greater than the given value.
                         If False, return rows where the column value is less than the given value.

    Returns:
    pandas.DataFrame: A DataFrame filtered based on the specified criteria.
    """
    _check_column_name_exist(df, column_name)
    if greater_than:
        return df[df[column_name] > value]
    else:
        return df[df[column_name] < value]


def calc_abs_error(df: DataFrame) -> None:
    _check_column_name_exist(df, dc.MODEL_VALUE)
    _check_column_name_exist(df, dc.STATION_VALUE)
    df[dc.ABS_ERROR] = abs(df[dc.MODEL_VALUE] - df[dc.STATION_VALUE])


def get_error_metric_each_station(df: DataFrame) -> DataFrame:
    _check_column_name_exist(df, dc.STATION_ID)
    _check_column_name_exist(df, dc.ABS_ERROR)
    station_error_metrics = df.groupby(dc.STATION_ID).apply(
        lambda df_tmp: pd.Series({
            dc.ME: (df_tmp[dc.MODEL_VALUE] - df_tmp[dc.STATION_VALUE]).mean(),
            dc.MAE: df_tmp[dc.ABS_ERROR].mean(),
            dc.RMSE: np.sqrt(np.mean(df_tmp[dc.ABS_ERROR] ** 2))
        })
    ).reset_index()
    return station_error_metrics


def get_abs_error_each_station(df: DataFrame) -> DataFrame:
    _check_column_name_exist(df, dc.STATION_ID)
    _check_column_name_exist(df, dc.ABS_ERROR)
    station_errors: DataFrame = df.groupby(dc.STATION_ID)[dc.ABS_ERROR].mean().reset_index()
    station_errors.columns = ['Station_ID', 'Mean_Absolute_Error']
    return station_errors


def get_me_mae_rmse(df: DataFrame) -> Tuple[float, float, float]:
    _check_column_name_exist(df, dc.MODEL_VALUE)
    _check_column_name_exist(df, dc.STATION_VALUE)
    error = df[dc.MODEL_VALUE] - df[dc.STATION_VALUE]
    me = error.mean()
    mae = abs(error).mean()
    rmse = np.sqrt(np.mean(error ** 2))
    return me, mae, rmse


def get_dwd_height_details(df: DataFrame) -> Series:
    _check_column_name_exist(df, dc.STATION_HEIGHT)
    return df[dc.STATION_HEIGHT].describe()
