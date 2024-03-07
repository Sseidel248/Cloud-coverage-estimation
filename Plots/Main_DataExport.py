"""
File name:      Main_DataExport.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os

import numpy as np
import pandas as pd
from Lib.IOConsts import *
from Lib.Grib2Reader import Grib2Datas
from Lib.DWDStationReader import DWDStations
from pandas import DataFrame, Series
from tqdm import tqdm
from typing import Dict
from datetime import datetime


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
                  use_all_params: bool,
                  dwd_param_list: list[str] = None) -> DataFrame:
    coords = dwd_datas.get_station_locations()
    model_dates = model_datas.df[COL_MODEL_FCST_DATE].tolist()

    if use_all_params:
        dwd_param_list = None

    temp_dfs = []
    coords_list = []
    for row in tqdm(coords.itertuples(index=False), total=len(coords), desc="Processing DWD-Values"):
        lat, lon = row.Lat, row.Lon
        temp_df = dwd_datas.get_dwd_multiple_values(model_dates, lat, lon, use_all_params, dwd_param_list)
        temp_dfs.append(temp_df)
        coords_list.append((lat, lon))
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)

    temp_dfs.clear()
    for date in tqdm(model_dates, total=len(model_dates), desc="Processing Model-Values"):
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
    for lat, lon in tqdm(coords, total=len(coords), desc="Processing DWD-Values for adding"):
        temp_df = dwd_datas.get_dwd_multiple_values(dates, lat, lon, False, dwd_params)
        temp_dfs.append(temp_df)
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)
    # change typing for better compare
    vals_dwd.to_csv(filename, sep=";", decimal=",", index=False)
    print(f"Export - Finished, Location:'{os.path.abspath(filename)}'")


def export_to_csv(df: DataFrame, filename: str):
    unique_filename = get_unique_filename(filename)
    # some Nan are exported as "", that's why na_rep="nan"
    df.to_csv(unique_filename, sep=";", decimal=",", na_rep="nan", index=False)


def data_postprocessing(df: DataFrame,
                        drop_nan: bool,
                        drop_invalid: bool,
                        invalid_nums: list[int]) -> DataFrame:
    col_type_dict = {
        "V_N": float,
        "V_N_I": str,
        "TT_TU": float,
        "RF_TU": float,
        "P": float,
        "P0": float,
        "F": float,
        "D": float
    }

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
                df = df[~df[col].isin(invalid_nums)]

    if "V_N" in df.columns:
        # convert -1 in V_N to 8/8 Cloud Coverage because it is fog
        df["V_N"].replace(-1, 8, inplace=True)
        # recalc in percentage [-] -> [%]
        df["V_N"] = df["V_N"] / 8 * 100

    # Drop NaN
    if drop_nan:
        return df.dropna()
    return df


def create_coordinates_list(start_lat, end_lat, start_lon, end_lon, delta):
    """
    Creates a list of tuples with coordinates (Lat, Lon) that are incremented from a start value to a final value
    with a defined delta for latitude (Lat) and longitude (Lon).

    :param start_lat: Start value for latitude
    :param end_lat: End value for latitude
    :param start_lon: Start value for Longitude
    :param end_lon: Final value for longitude
    :param delta: Increment for longitude
    :return: List of tuples (Lon, Lat). Lon and Lat are rounded to the 4th decimal place
    """
    # Initialize the list for the coordinates
    coord_list = []

    # Generate the values for latitude and longitude within the specified ranges
    act_lat = start_lat
    while act_lat <= end_lat:
        act_lon = start_lon
        while act_lon <= end_lon:
            # Füge das aktuelle Tupel der Liste hinzu
            coord_list.append((act_lat, act_lon))
            act_lon += delta
        act_lat += delta

    # Round to 4th decimal place
    return [(round(lon, 4), round(lat, 4)) for lon, lat in coord_list]


def export_cloud_area_csv(dwd_datas: DWDStations,
                          model_datas: Grib2Datas,
                          start_lat: float,
                          end_lat: float,
                          start_lon: float,
                          end_lon: float,
                          delta: float,
                          exportname_dwd: str,
                          exportname_model: str):
    print("Create Area Data...")
    calc_date = datetime(2024, 1, 24, 12)
    # get DWD-Locations and Values
    dwd_locs = dwd_datas.get_station_locations()
    dwd_area = dwd_locs[(dwd_locs[COL_LAT] >= start_lat) & (dwd_locs[COL_LAT] <= end_lat) &
                        (dwd_locs[COL_LON] >= start_lon) & (dwd_locs[COL_LON] <= end_lon)].copy()
    # init clou coverage values with Nan
    dwd_area["V_N"] = np.NaN
    for idx, row in dwd_area.iterrows():
        lat = row[COL_LAT]
        lon = row[COL_LON]
        tmp = dwd_datas.get_dwd_value(calc_date, lat, lon,
                                      False, ["V_N"])
        # override nan Value if cloud coverage value exist
        if "V_N" in tmp.columns:
            dwd_area.loc[idx, "V_N"] = float(tmp["V_N"].iloc[0])
    dwd_area.insert(0, COL_DATE, calc_date)
    dwd_area = data_postprocessing(dwd_area, True, True, [-999])
    export_to_csv(dwd_area, f".\\{exportname_dwd}")

    # create Modeldata for area
    view_area = create_coordinates_list(start_lat, end_lat, start_lon, end_lon, delta)
    temp_df = model_datas.get_multiple_values(model,
                                              param,
                                              calc_date,
                                              view_area)
    export_to_csv(temp_df, f".\\{exportname_model}")


model: str = MODEL_ICON_EU
param: str = CLOUD_COVER
dwd_path: str = "..\\DWD_Downloader\\WeatherStations\\"

if model == MODEL_ICON_D2:
    exportname: str = CSV_NAME_ICON_D2
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\icon-d2"
    model_delta: float = ICON_D2_LAT_LON_DELTA
elif model == MODEL_ICON_EU:
    exportname = CSV_NAME_ICON_EU
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\icon-eu"
    model_delta: float = ICON_EU_LAT_LON_DELTA
else:
    raise ValueError(f"Model: '{model}' not exist")

# init grib2 files
grib2_datas = Grib2Datas()
grib2_datas.load_folder(grib2_path)

# init dwd txt files
dwds = DWDStations()
dwds.load_folder(dwd_path)

# # combine dwd and grib2 datas
dwd_params = ["V_N", "V_N_I"]
export_df = combine_datas(dwds, grib2_datas, model, param, False, dwd_params)
#
# # contains all params
export_all_param_df = combine_datas(dwds, grib2_datas, model, param, True)
#
# # Postprocessing readed datas
export_df = data_postprocessing(export_df, False, False, [-999])
export_all_param_df = data_postprocessing(export_all_param_df, False, False, [-999])
#
# # save export
export_to_csv(export_df, exportname)
export_to_csv(export_all_param_df, f"all_param_{exportname}")
#
# # create example area for plot some clouds
export_cloud_area_csv(dwds, grib2_datas, 52.5, 54.5, 12.0, 14.0, model_delta,
                      f"DWD-Stations_in_Area_I_{model}.csv", f"Area_I_{model}.csv")
export_cloud_area_csv(dwds, grib2_datas, 47.5, 49.5, 7.5, 9.5, model_delta,
                      f"DWD-Stations_in_Area_II_{model}.csv", f"Area_II_{model}.csv")


