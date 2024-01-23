"""
File name:      DataExport.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import pandas as pd
from Lib.IOConsts import *
from Lib.Grib2Reader import Grib2Datas
from Lib.DWDStationReader import DWDStations
from pandas import DataFrame, Series
from tqdm import tqdm
from typing import Dict


def is_file_in_use(filepath: str) -> bool:
    """
    Checks if the specified file is currently being used by another process.

    :param filepath: path of file.
    :return: True if the file is used, otherwise False.
    """
    if not os.path.exists(filepath):
        return False
    try:
        # Try to open the file in exclusive mode.
        with open(filepath, "r+", encoding='utf-8'):
            return False
    except IOError:
        return True


def get_unique_filename(filename: str) -> str:
    """
    Checks if a file name exists and increments it if it exists or is used.

    :param filename: The original file name
    :return: A unique file name
    """
    counter = 1
    name, extension = os.path.splitext(filename)
    while os.path.exists(filename) or is_file_in_use(filename):
        filename = f"{name}({counter}){extension}"
        counter += 1
    return filename


def get_usefull_stations(df_dwd: DataFrame, model_datetimes: Series) -> DataFrame:
    filtered_df: DataFrame = DataFrame()
    for date in model_datetimes:
        temp_df: DataFrame = df_dwd[(df_dwd[COL_DATE_START] <= date) & (df_dwd[COL_DATE_END] >= date)]
        filtered_df = pd.concat([filtered_df, temp_df])
    filtered_df = filtered_df.drop_duplicates()
    return filtered_df.reset_index()


def combine_datas(dwd_datas: DWDStations,
                  model_datas: Grib2Datas,
                  model_str: str,
                  model_param: str,
                  dwd_param_list: list[str]) -> DataFrame:
    coords = dwd_datas.get_station_locations()
    model_dates = model_datas.df[COL_MODEL_FCST_DATE].tolist()

    temp_dfs = []
    coords_list = []
    for row in tqdm(coords.itertuples(index=False), total=len(coords), desc="Processing dwd values"):
        lat, lon = row.Lat, row.Lon
        temp_df = dwd_datas.get_dwd_multiple_values(model_dates, lat, lon, False, dwd_param_list)
        temp_dfs.append(temp_df)
        coords_list.append((lat, lon))
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)

    temp_dfs.clear()
    for date in tqdm(model_dates, total=len(model_dates), desc="Processing model values"):
        temp_df = model_datas.get_multiple_values(model_str, model_param, date, coords_list)
        temp_dfs.append(temp_df)
    vals_model = pd.concat(temp_dfs, ignore_index=True)

    print("Export - Data merging")
    vals_dwd.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    vals_model.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)

    merged_df = pd.merge(vals_dwd, vals_model, on=[COL_DATE, COL_LAT, COL_LON], how='left')
    merged_df.sort_values(by=[COL_STATION_ID, COL_DATE], inplace=True)

    # remove DWD's "eor" column if exist
    if "eor" in merged_df.columns:
        merged_df.drop(columns="eor", inplace=True)

    return merged_df


def add_to_csv(filename: str, dwd_datas: DWDStations, dwd_params: list[str]):
    df = pd.read_csv(filename, sep=';', parse_dates=[COL_DATE])
    df[COL_LAT] = df[COL_LAT].astype(float)
    df[COL_LON] = df[COL_LON].astype(float)
    coords = [(lat, lon) for lat, lon in zip(df[COL_LAT], df[COL_LON])]
    dates = [date for date in df[COL_DATE]]

    temp_dfs = []
    for lat, lon in tqdm(coords, total=len(coords), desc="Processing dwd values for adding"):
        temp_df = dwd_datas.get_dwd_multiple_values(dates, lat, lon, False, dwd_params)
        temp_dfs.append(temp_df)
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)
    # change typing for better compare
    vals_dwd.to_csv(filename, sep=";", decimal=",", index=False)
    print(f"Export - Finished, Location:'{os.path.abspath(filename)}'")


def export_to_csv(df: DataFrame, filename: str):
    unique_filename = get_unique_filename(filename)
    df.to_csv(unique_filename, sep=";", decimal=",", index=False)


def data_postprocessing(df: DataFrame,
                        drop_nan: bool,
                        drop_invalid: bool,
                        invalid_num: int,
                        col_type_dict: Dict[str, type]) -> DataFrame:
    # Parse column types
    num_cols = []
    for col, _type in col_type_dict.items():
        if col in df.columns:
            df[col] = df[col].astype(_type)
            if pd.api.types.is_numeric_dtype(df[col]):
                num_cols.append(col)
            if pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].str.strip()
    # Drop invalid values
    if drop_invalid:
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df = df[df[col] != invalid_num]
    # Drop NaN
    if drop_nan:
        return df.dropna()
    return df


model: str = MODEL_ICON_EU
param: str = CLOUD_COVER
dwd_path: str = "..\\DWD_Downloader\\WeatherStations\\cloudiness"

if model == MODEL_ICON_D2:
    exportname: str = CSV_NAME_ICON_D2
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\ICON_D2"
elif model == MODEL_ICON_EU:
    exportname = CSV_NAME_ICON_EU
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\ICON_EU"
else:
    raise ValueError(f"Model: '{model}' not exist")

# init grib2 files
grib2_datas = Grib2Datas()
grib2_datas.load_folder(grib2_path)

# init dwd txt files
dwds = DWDStations()
dwds.load_folder(dwd_path)

# combine dwd ad grib2 datas
dwd_params = ["V_N", "V_N_I"]
export_df = combine_datas(dwds, grib2_datas, model, param, dwd_params)

# post processing export data
parse_types = {"V_N": float,
               "V_N_I": str}
export_df = data_postprocessing(export_df, True, True, -1, parse_types)
export_df["V_N"] = export_df["V_N"] / 8 * 100

# save export
export_to_csv(export_df, exportname)


