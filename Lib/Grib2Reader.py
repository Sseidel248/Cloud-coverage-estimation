import re
import os
import bz2
import subprocess

import pandas as pd

import Lib.GeneralFunctions as gFunc
import numpy as np
from typing import List, Tuple
from pandas import DataFrame, Series
from datetime import datetime, timedelta
from Lib.Consts.Grib2ReaderConsts import *

_WGRIB2_EXE: str = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2\\wgrib2.exe"


class Grib2Datas:
    def __init__(self):
        cols = [COL_MODEL, COL_PARAM, COL_DATE, COL_FCST_MIN, COL_FCST_DATE, COL_GRIB2_FILENAME]
        datatypes = {
            COL_MODEL: 'str',
            COL_PARAM: 'str',
            COL_DATE: 'datetime64[ns]',
            COL_FCST_MIN: 'int',
            COL_FCST_DATE: 'datetime64[ns]',
            COL_GRIB2_FILENAME: 'str'
        }
        self.df: DataFrame = DataFrame(columns=cols).astype(datatypes)
        self.df_invalid: DataFrame = DataFrame(columns=cols).astype(datatypes)
        cols = [COL_MODEL, COL_PARAM, COL_LAT_START, COL_LAT_END, COL_LON_START, COL_LON_END, COL_LATLON_DELTA]
        datatypes = {
            COL_MODEL: 'str',
            COL_PARAM: 'str',
            COL_LAT_START: 'float',
            COL_LAT_END: 'float',
            COL_LON_START: 'float',
            COL_LON_END: 'float',
            COL_LATLON_DELTA: 'float'
        }
        self.df_models: DataFrame = DataFrame(columns=cols).astype(datatypes)

    def load_folder(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder: '{path}' not exist.")
        bz2_archives = gFunc.get_files(path, ".bz2")
        _extract_bz2_archives(bz2_archives)
        grib2_files = gFunc.get_files(path, ".grib2")
        if len(grib2_files) == 0:
            raise FileNotFoundError(f"No *.grib2 Files exist in '{path}'")
        for grib2 in grib2_files:
            self._load_file(os.path.abspath(grib2))
        self._data_validation()
        self.df = self.df.sort_values(by=[COL_MODEL, COL_DATE])

    def count(self) -> int:
        return len(self.df)

    def get_used_datetimes(self, model: str = '') -> Series:
        if model != '':
            return self.df[self.df[COL_MODEL] == model][COL_FCST_DATE]
        else:
            return self.df[COL_FCST_DATE]

    def get_datetime_range(self, model: str = "") -> (datetime, datetime):
        return self._datetime_start(model), self._datetime_end(model)

    def exist_datetime(self, date_time: datetime, model: str = "") -> bool:
        if model == "":
            return not self.df[self.df[COL_FCST_DATE] == date_time].empty
        return not self.df[(self.df[COL_MODEL] == model) &
                           (self.df[COL_FCST_DATE] == date_time)].empty

    def get_value(self, model: str, param: str, date_time: datetime, lat: float, lon: float) -> float:
        closest_date_time: datetime = self._get_closest_date(date_time)
        if not self.exist_datetime(closest_date_time, model):
            raise ValueError(f"Datetime '{str(date_time)}' not exist in dataframe.")
        if not self._lat_in_range(lat, model):
            raise ValueError(f"Lat. '{str(lat)}' not in range.")
        if not self._lon_in_range(lon, model):
            raise ValueError(f"Lon. '{str(lon)}' not in range.")
        if not self._exist_param(param, model):
            raise ValueError(f"Parameter '{param}' not exist for this model '{model}'.")
        rounded_date_time: datetime = gFunc.round_to_nearest_hour(date_time)
        time_hour_delta: float = gFunc.hours_difference(rounded_date_time, closest_date_time)
        if time_hour_delta > 1:
            return -1
        founded_df = self.df[(self.df[COL_MODEL] == model) &
                             (self.df[COL_PARAM] == param) &
                             (self.df[COL_FCST_DATE] == closest_date_time)]
        filename = founded_df[COL_GRIB2_FILENAME].iloc[0]
        conv_lat: float = gFunc.convert_in_0_360(lat)
        conv_lon: float = gFunc.convert_in_0_360(lon)
        command: str = f"{_WGRIB2_EXE} {filename} -match {param} -lon {str(conv_lon)} {str(conv_lat)}"
        result = subprocess.run(command, capture_output=True, text=True)
        match = re.search(r"val=(\d+\.?\d+)", result.stdout)
        if match:
            return float(match.group(1))
        return -1

    def get_multiple_values(self, model: str, param: str, date_time: datetime,
                            coords: List[Tuple[float, float]]) -> DataFrame:
        cols = [COL_DATE, COL_LAT, COL_LON, COL_MODEL_VALUE]
        lat_values, lon_values, value_values, date_times = [], [], [], []
        values: DataFrame = DataFrame(columns=cols)
        closest_date_time: datetime = self._get_closest_date(date_time)
        founded_df = self.df[(self.df[COL_MODEL] == model) &
                             (self.df[COL_PARAM] == param) &
                             (self.df[COL_FCST_DATE] == closest_date_time)]
        if founded_df.empty:
            return values
        filename = founded_df[COL_GRIB2_FILENAME].iloc[0]

        command: str = f"{_WGRIB2_EXE} {filename} -match {param}"
        for lat, lon in coords:
            conv_lat = gFunc.convert_in_0_360(lat)
            conv_lon = gFunc.convert_in_0_360(lon)
            command += f" -lon {conv_lon} {conv_lat}"
        result = subprocess.run(command, capture_output=True, text=True)
        matches = re.findall(r"val=(\d+\.?\d*(e\+20)?)", result.stdout)

        for match, (lat, lon) in zip(matches, coords):
            value: float = -1
            if match[0] != "9.999e+20":
                value = float(match[0])
            date_times.append(date_time)
            lat_values.append(lat)
            lon_values.append(lon)
            value_values.append(value)
        if len(lat_values) > 0:
            values = pd.DataFrame({COL_DATE: date_times,
                                   COL_LAT: lat_values,
                                   COL_LON: lon_values,
                                   COL_MODEL_VALUE: value_values}, columns=cols)
        return values

    def _datetime_start(self, model: str = "") -> datetime:
        if model == "":
            return self.df[COL_FCST_DATE].min()
        else:
            filtered_df = self.df[self.df[COL_MODEL] == model]
            return filtered_df[COL_FCST_DATE].min()

    def _datetime_end(self, model: str = "") -> datetime:
        if model == "":
            return self.df[COL_FCST_DATE].max()
        else:
            filtered_df = self.df[self.df[COL_MODEL] == model]
            return filtered_df[COL_FCST_DATE].max()

    def _exist_model(self, model: str) -> bool:
        return not self.df_models[self.df_models[COL_MODEL] == model].empty

    def _exist_param(self, param: str, model: str) -> bool:
        if not self._exist_model(model):
            return False
        return not self.df_models[self.df_models[COL_PARAM] == param].empty

    def _lat_in_range(self, lat: float, model: str) -> bool:
        if not self._exist_model(model):
            return False
        else:
            filtered_model = self.df_models[self.df_models[COL_MODEL] == model]
            return ((filtered_model[COL_LAT_START].iloc[0] <= lat <= filtered_model[COL_LAT_END].iloc[0])
                    and not filtered_model.empty)

    def _lon_in_range(self, lon: float, model: str) -> bool:
        if not self._exist_model(model):
            return False
        else:
            filtered_model = self.df_models[self.df_models[COL_MODEL] == model]
            return ((filtered_model[COL_LON_START].iloc[0] <= lon <= filtered_model[COL_LON_END].iloc[0])
                    and not filtered_model.empty)

    def _get_closest_date(self, date_time: datetime) -> datetime:
        differences = (self.df[COL_FCST_DATE] - date_time).abs()
        closest_date_index = differences.idxmin()
        return self.df.loc[closest_date_index, COL_FCST_DATE]

    def _data_validation(self):
        self.df_invalid = self.df[self.df[COL_FCST_MIN] > 120]
        self.df = self.df[self.df[COL_FCST_MIN] <= 120]
        self.df_models = self.df_models.drop_duplicates()

    def _load_file(self, work_file: str):
        command: str = f"{_WGRIB2_EXE} {work_file} -s -grid"
        result = subprocess.run(command, capture_output=True, text=True)
        if LAT_LON in result.stdout:
            match = re.search(PATTERN, result.stdout)
            if match:
                # index 0 = full match of complete string
                date: datetime = datetime.strptime(match.group(1), "%Y%m%d%H")
                # if not found, then None
                if match.group(4) == "anl":
                    fcst_minutes = 0
                    fcst_date = date
                else:
                    fcst_minutes = int(match.group(3))
                    fcst_date = date + timedelta(minutes=fcst_minutes)
                new_row = {
                    COL_MODEL: _get_model(float(match.group(7))),
                    COL_DATE: date,
                    COL_FCST_MIN: fcst_minutes,
                    COL_FCST_DATE: fcst_date,
                    COL_PARAM: match.group(2),
                    COL_LAT_START: gFunc.convert_in_180_180(float(match.group(5))),
                    COL_LAT_END: gFunc.convert_in_180_180(float(match.group(6))),
                    COL_LATLON_DELTA: float(match.group(7)),
                    COL_LON_START: gFunc.convert_in_180_180(float(match.group(8))),
                    COL_LON_END: gFunc.convert_in_180_180(float(match.group(9))),
                    COL_GRIB2_FILENAME: work_file
                }
                self.df.loc[len(self.df)] = new_row
                self.df_models.loc[len(self.df_models)] = new_row


def _get_model(delta: float) -> str:
    model: str = MODEL_UNKNOWN
    if delta == 0.02:
        model = MODEL_ICON_D2
    elif delta == 0.0625:
        model = MODEL_ICON_EU
    return model


def _extract_bz2_archives(bz2_archives: List[str]):
    # If there are no archives, then nothing needs to be unpacked
    if len(bz2_archives) == 0:
        return
    # Loop through each *.bz2 archive and unpack it
    for archive in bz2_archives:
        directory: str = os.path.dirname(archive)
        filename_body: str = os.path.splitext(os.path.basename(archive))[0]
        extracted_path: str = os.path.join(directory, filename_body)
        if not os.path.exists(extracted_path):
            with open(extracted_path, "wb") as extracted_file, bz2.BZ2File(archive, "rb") as archiv:
                for content in archiv:
                    extracted_file.write(content)

