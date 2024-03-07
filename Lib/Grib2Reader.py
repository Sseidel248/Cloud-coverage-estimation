import re
import os
import bz2
import subprocess
import pandas as pd
import Lib.GeneralFunctions as gFunc
from typing import List, Tuple
from pandas import DataFrame, Series
from datetime import datetime, timedelta
from Lib.IOConsts import *
from tqdm import tqdm

# Wgrib2 file
_WGRIB2_EXE: str = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2\\wgrib2.exe"


def split_coords(coords, n=50):
    """Divide the coordinate list into sublists with n coordinates each."""
    for i in range(0, len(coords), n):
        yield coords[i:i + n]


class Grib2Datas:
    def __init__(self):
        cols = [COL_MODEL, COL_PARAM, COL_DATE, COL_MODEL_FCST_MIN, COL_MODEL_FCST_DATE, COL_MODEL_FILENAME]
        datatypes = {
            COL_MODEL: 'str',
            COL_PARAM: 'str',
            COL_DATE: 'datetime64[ns]',
            COL_MODEL_FCST_MIN: 'int',
            COL_MODEL_FCST_DATE: 'datetime64[ns]',
            COL_MODEL_FILENAME: 'str'
        }
        self.df: DataFrame = DataFrame(columns=cols).astype(datatypes)
        self.df_invalid: DataFrame = DataFrame(columns=cols).astype(datatypes)
        cols = [COL_MODEL, COL_PARAM, COL_MODEL_LAT_START, COL_MODEL_LAT_END, COL_MODEL_LON_START, COL_MODEL_LON_END,
                COL_MODEL_LATLON_DELTA]
        datatypes = {
            COL_MODEL: 'str',
            COL_PARAM: 'str',
            COL_MODEL_LAT_START: 'float',
            COL_MODEL_LAT_END: 'float',
            COL_MODEL_LON_START: 'float',
            COL_MODEL_LON_END: 'float',
            COL_MODEL_LATLON_DELTA: 'float'
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
        for grib2 in tqdm(grib2_files, total=len(grib2_files), desc="Loading Grib2-Files"):
            self._load_file(os.path.abspath(grib2))
        self._data_validation()
        self.df = self.df.sort_values(by=[COL_MODEL, COL_DATE])

    def count(self) -> int:
        return len(self.df)

    def get_used_datetimes(self, model: str = '') -> Series:
        if model != '':
            return self.df[self.df[COL_MODEL] == model][COL_MODEL_FCST_DATE]
        else:
            return self.df[COL_MODEL_FCST_DATE]

    def get_datetime_range(self, model: str = "") -> (datetime, datetime):
        return self._datetime_start(model), self._datetime_end(model)

    def exist_datetime(self, date_time: datetime, model: str = "") -> bool:
        if model == "":
            return not self.df[self.df[COL_MODEL_FCST_DATE] == date_time].empty
        return not self.df[(self.df[COL_MODEL] == model) &
                           (self.df[COL_MODEL_FCST_DATE] == date_time)].empty

    def get_value(self, model: str, param: str, date_time: datetime, lat: float, lon: float) -> DataFrame:
        return self.get_multiple_values(model, param, date_time, [(lat, lon)])

    def get_multiple_values(self, model: str, param: str, date_time: datetime,
                            coords: List[Tuple[float, float]]) -> DataFrame:
        cols = [COL_DATE, COL_MODEL_FCST_MIN, COL_LAT, COL_LON, param]
        lat_values, lon_values, value_values, date_times, fcst_min_values = [], [], [], [], []
        values: DataFrame = DataFrame(columns=cols)
        closest_date_time: datetime = self._get_closest_date(date_time)
        founded_df = self.df[(self.df[COL_MODEL] == model) &
                             (self.df[COL_PARAM] == param) &
                             (self.df[COL_MODEL_FCST_DATE] == closest_date_time)]
        if founded_df.empty:
            return values
        filename = founded_df[COL_MODEL_FILENAME].iloc[0]
        fcst_min = founded_df[COL_MODEL_FCST_MIN].iloc[0]

        results = []
        # Divide coordinates into groups of 50 and execute commands
        for coord_grp in split_coords(coords, 50):
            command = f"{_WGRIB2_EXE} {filename} -match {param}"
            for lat, lon in coord_grp:
                conv_lat = gFunc.convert_in_0_360(lat)
                conv_lon = gFunc.convert_in_0_360(lon)
                command += f" -lon {conv_lon} {conv_lat}"
            result = subprocess.run(command, capture_output=True, text=True)
            results.append(result.stdout)

        matches = re.findall(r"val=(\d+\.?\d*(e\+20)?)", ''.join(results))

        for match, (lat, lon) in zip(matches, coords):
            value: float = -1
            if match[0] != "9.999e+20":
                value = float(match[0])
            date_times.append(date_time)
            lat_values.append(lat)
            lon_values.append(lon)
            value_values.append(value)
            fcst_min_values.append(fcst_min)
        # for Performance - fill DataFrame outside loop
        if len(lat_values) > 0:
            values = pd.DataFrame({COL_DATE: date_times,
                                   COL_MODEL_FCST_MIN: fcst_min_values,
                                   COL_LAT: lat_values,
                                   COL_LON: lon_values,
                                   param: value_values
                                   }, columns=cols)
        return values

    def _datetime_start(self, model: str = "") -> datetime:
        if model == "":
            return self.df[COL_MODEL_FCST_DATE].min()
        else:
            filtered_df = self.df[self.df[COL_MODEL] == model]
            return filtered_df[COL_MODEL_FCST_DATE].min()

    def _datetime_end(self, model: str = "") -> datetime:
        if model == "":
            return self.df[COL_MODEL_FCST_DATE].max()
        else:
            filtered_df = self.df[self.df[COL_MODEL] == model]
            return filtered_df[COL_MODEL_FCST_DATE].max()

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
            return ((filtered_model[COL_MODEL_LAT_START].iloc[0] <= lat <= filtered_model[COL_MODEL_LAT_END].iloc[0])
                    and not filtered_model.empty)

    def _lon_in_range(self, lon: float, model: str) -> bool:
        if not self._exist_model(model):
            return False
        else:
            filtered_model = self.df_models[self.df_models[COL_MODEL] == model]
            return ((filtered_model[COL_MODEL_LON_START].iloc[0] <= lon <= filtered_model[COL_MODEL_LON_END].iloc[0])
                    and not filtered_model.empty)

    def _get_closest_date(self, date_time: datetime) -> datetime:
        differences = (self.df[COL_MODEL_FCST_DATE] - date_time).abs()
        closest_date_index = differences.idxmin()
        return self.df.loc[closest_date_index, COL_MODEL_FCST_DATE]

    def _data_validation(self):
        self.df_invalid = self.df[self.df[COL_MODEL_FCST_MIN] > 120]
        self.df = self.df[self.df[COL_MODEL_FCST_MIN] <= 120]
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
                submatch = re.search(r":(\d+) min fcst::", result.stdout)
                if submatch:
                    fcst_minutes = int(submatch.group(1))
                    fcst_date = date + timedelta(minutes=fcst_minutes)
                else:
                    fcst_minutes = 0
                    fcst_date = date
                new_row = {
                    COL_MODEL: _get_model(float(match.group(5))),
                    COL_DATE: date,
                    COL_MODEL_FCST_MIN: fcst_minutes,
                    COL_MODEL_FCST_DATE: fcst_date,
                    COL_PARAM: match.group(2),
                    COL_MODEL_LAT_START: gFunc.convert_in_180_180(float(match.group(3))),
                    COL_MODEL_LAT_END: gFunc.convert_in_180_180(float(match.group(4))),
                    COL_MODEL_LATLON_DELTA: float(match.group(5)),
                    COL_MODEL_LON_START: gFunc.convert_in_180_180(float(match.group(6))),
                    COL_MODEL_LON_END: gFunc.convert_in_180_180(float(match.group(7))),
                    COL_MODEL_FILENAME: work_file
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


# grib2_datas = Grib2Datas()
# grib2_datas.load_folder("..\\DWD_Downloader\\WeatherData\\icon_d2")
# print(grib2_datas.get_multiple_values(MODEL_ICON_D2, CLOUD_COVER, datetime(2023, 11, 29, 18), [(53, 13)]))
# print(grib2_datas.get_value(MODEL_ICON_D2, CLOUD_COVER, datetime(2023, 11, 29, 18), 53, 13))
