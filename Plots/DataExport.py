"""
File name:      DataExport.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import pandas as pd
from Lib.Consts import DataExportConsts as dc
from Lib.Consts import Grib2ReaderConsts as gc
from Lib.Grib2Reader import Grib2Datas
from Lib.DWDStationReader import DWDStations, read_file_to_df, get_measurment_type
from typing import List, Tuple
from datetime import datetime
from pandas import DataFrame, Series
from Lib.Consts.DWDReaderConsts import *
from Lib.Consts.Grib2ReaderConsts import *
from tqdm import tqdm


def get_usefull_stations(df_dwd: DataFrame, model_datetimes: Series) -> DataFrame:
    filtered_df: DataFrame = DataFrame()
    for date in model_datetimes:
        temp_df: DataFrame = df_dwd[(df_dwd[COL_DATE_START] <= date) & (df_dwd[COL_DATE_END] >= date)]
        filtered_df = pd.concat([filtered_df, temp_df])
    filtered_df = filtered_df.drop_duplicates()
    return filtered_df.reset_index()


def parse_dwd_types(df: DataFrame) -> DataFrame:
    df[COL_STATION_ID] = df[COL_STATION_ID].astype(str)
    df[COL_DWD_VALUE] = df[COL_DWD_VALUE].astype(int)
    return df


def export_as_csv(filename: str, dwd_datas: DWDStations, model_datas: Grib2Datas, model_str: str, param_str: str):
    coords = dwd_datas.get_station_locations()
    model_dates = model_datas.df[[COL_FCST_DATE]]

    temp_dfs = []
    coords_list = []
    for row in tqdm(coords.itertuples(index=False), total=len(coords), desc="Processing DWD Values"):
        lat, lon = row.Lat, row.Lon
        temp_df = dwd_datas.get_dwd_multiple_value(model_dates, lat, lon)
        temp_dfs.append(temp_df)
        coords_list.append((lat, lon))
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)
    vals_dwd = parse_dwd_types(vals_dwd)
    # remove invalid dwd values
    vals_dwd = vals_dwd[vals_dwd[COL_DWD_VALUE] > -1]

    temp_dfs.clear()
    for date in tqdm(model_dates[COL_FCST_DATE], total=len(model_dates), desc="Processing Model Values"):
        temp_df = model_datas.get_multiple_values(model_str, param_str, date, coords_list)
        temp_dfs.append(temp_df)
    vals_model = pd.concat(temp_dfs, ignore_index=True)
    # remove invalid model values
    vals_model = vals_model[vals_model[COL_MODEL_VALUE] > -1]

    print("Export - Data merging")
    # renaming cols
    vals_dwd.rename(columns={COL_DWD_MESS_DATUM: COL_DATE,
                             COL_STATION_ID: dc.STATION_ID}, inplace=True)
    vals_dwd.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    vals_model.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)

    merged_df = pd.merge(vals_dwd, vals_model, on=[COL_DATE, COL_LAT, COL_LON], how='left')
    merged_df.sort_values(by=[dc.STATION_ID, COL_DATE], inplace=True)
    merged_df[COL_DWD_VALUE] = merged_df[COL_DWD_VALUE] / 8 * 100

    # remove DWD's "eor" column if exist
    if "eor" in merged_df.columns:
        merged_df.drop(columns="eor", inplace=True)

    merged_df.to_csv(filename, sep=";", decimal=",", index=False)
    print(f"Export - Finished, Location:'{os.path.abspath(filename)}'")


model: str = MODEL_ICON_D2
param: str = CLOUD_COVER
dwd_path: str = "..\\DWD_Downloader\\WeatherStations\\Cloudiness\\20231228"

if model == MODEL_ICON_D2:
    exportname: str = dc.CSV_NAME_ICON_D2
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\ICON_D2"
elif model == MODEL_ICON_EU:
    exportname = dc.CSV_NAME_ICON_EU
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\ICON_EU"
else:
    raise ValueError(f"Model: '{model}' not exist")

grib2_datas = Grib2Datas()
grib2_datas.load_folder(grib2_path)
print(f"Number of loaded Files: {str(grib2_datas.count())}")
all_model_datetimes = grib2_datas.get_used_datetimes()
print(f"Modeldatetime range: {str(all_model_datetimes.iloc[0])} until {str(all_model_datetimes.iloc[-1])}")
print("-> Attention, there could be gaps in the date range.")

dwds = DWDStations()
dwds.load_folder(dwd_path)
print(f"Number of readed DWD Stations: {str(dwds.count())}")
all_dwd_locations = dwds.get_station_locations()

all_usefull_stations = get_usefull_stations(dwds.df, all_model_datetimes)
print(f"Number of DWD measuring stations that can be used for actual model (datetime range): "
      f"{len(all_usefull_stations)}")

if dc.DELETE_BEFORE_START and os.path.exists(exportname):
    os.remove(exportname)
export_as_csv(exportname, dwds, grib2_datas, model, param)
