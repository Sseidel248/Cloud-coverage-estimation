import re
import os
import bz2
import subprocess
import pandas as pd
import numpy as np
import Lib.GeneralFunctions as gFunc
from typing import List, Tuple
from numpy.typing import NDArray
from pandas import DataFrame, Series
from datetime import datetime, timedelta
from Lib.IOConsts import *
from tqdm import tqdm

# Wgrib2 file
_WGRIB2_EXE: str = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2\\wgrib2.exe"


def split_coords(coords, n=100):
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

    def get_values(self,
                   model: str,
                   param: str,
                   date_times: datetime | List[datetime],
                   coords: Tuple[float, float] | List[Tuple[float, float]]) -> DataFrame:

        def get_width_len(arr: NDArray) -> Tuple[int, int]:
            if len(arr.shape) == 0:
                return 1, 1
            elif len(arr.shape) == 1:
                return arr.shape[0], 1
            else:
                return arr.shape[1], arr.shape[0]

        def conv_to_np(data, dtype: str):
            if not isinstance(data, list):
                data = [data]
            return np.array(data, dtype=dtype)

        np_date_times = conv_to_np(date_times, "datetime64[m]").reshape(-1, 1)
        np_coords = conv_to_np(coords, "float64")

        coords_width, coords_len = get_width_len(np_coords)
        date_times_width, date_times_len = get_width_len(np_date_times)

        if date_times_width != 1:
            raise ValueError(f"The parameter 'date_times' has an incorrect dimensioning. Shape must be (n, 1).")

        if coords_width != 2:
            raise ValueError(f"The parameter 'coords' has an incorrect dimensioning. Shape must be (n, 2).")

        if date_times_len != coords_len:
            if date_times_len == 1:
                np_date_times = np.full((coords_len, 1), np_date_times[0])
            if coords_len == 1:
                np_coords = np.full((date_times_len, 2), np_coords)

        # Prepare vectorize functions - performance by numpy
        np_date_round_func = np.vectorize(gFunc.round_to_nearest_hour)
        np_date_times = np_date_round_func(np_date_times)
        unique_date_times = np.unique(np_date_times)
        np_closest_grib2_date = np.vectorize(self._get_closest_date)
        unique_date_times = np_closest_grib2_date(unique_date_times)
        np_conv_coords_func = np.vectorize(gFunc.convert_in_0_360)
        np_coords = np_conv_coords_func(np_coords)

        # define the return DatFrame
        cols = [COL_DATE, COL_MODEL_FCST_MIN, COL_LAT, COL_LON, param]
        lat_values, lon_values, value_values, datetimes, fcst_min_values = [], [], [], [], []
        values: DataFrame = DataFrame(columns=cols)

        for date in unique_date_times:
            # Search Entry
            founded_df = self.df[(self.df[COL_MODEL] == model) &
                                 (self.df[COL_PARAM] == param) &
                                 (self.df[COL_MODEL_FCST_DATE] == date)]
            if founded_df.empty:
                continue
            filename = founded_df[COL_MODEL_FILENAME].iloc[0]
            fcst_min = founded_df[COL_MODEL_FCST_MIN].iloc[0]
            # get the index of date
            used_date_indexes = np.where(np_date_times == date)[0]
            used_coords = np_coords[used_date_indexes]

            # Divide coordinates into groups of 50 and execute commands
            res_list = []
            for coord_grp in split_coords(used_coords, 1500):
                # run cmd
                command = f"{_WGRIB2_EXE} {filename} -match {param}"
                for lat, lon in coord_grp:
                    command += f" -lon {lon} {lat}"
                result = subprocess.run(command, capture_output=True, text=True)
                res_list.append(result.stdout)
            # Evaluate result string
            matches = re.findall(r"val=(\d+\.?\d*(e\+20)?)", ''.join(res_list))

            for match, (lat, lon) in zip(matches, used_coords):
                value: float = -1
                if match[0] != "9.999e+20":
                    value = float(match[0])
                datetimes.append(date)
                lat_values.append(lat)
                lon_values.append(lon)
                value_values.append(value)
                fcst_min_values.append(fcst_min)
        # for Performance - fill DataFrame outside loop
        if len(lat_values) > 0:
            values = pd.DataFrame({COL_DATE: datetimes,
                                   COL_MODEL_FCST_MIN: fcst_min_values,
                                   COL_LAT: lat_values,
                                   COL_LON: lon_values,
                                   param: value_values
                                   }, columns=cols)
        return values

    def get_values_idw(self,
                       model: str,
                       param: str,
                       date_times: datetime | List[datetime],
                       coords: Tuple[float, float] | List[Tuple[float, float]],
                       radius: float = 0.04) -> DataFrame:

        def idw(group, dist_col, value_col, q=2):
            # Avoid division by zero
            group[dist_col] = np.where(group[dist_col] == 0, group[dist_col] + 1e-10, group[dist_col])
            d = group[dist_col]
            vals = group[value_col]
            # Calculation of weighting
            weighted_sum = np.sum(vals / d ** q)
            weights_sum = np.sum(1 / d ** q)
            # return idw values
            return weighted_sum / weights_sum

        tmp, _ = _create_coords_in_radius(1, 1, radius, 0.02)
        len_idw_dataset = len(tmp)
        if not isinstance(coords, list):
            coords = [coords]

        idw_coords = []
        idw_distances = []
        for lat, lon in coords:
            area, distances = _create_coords_in_radius(lat, lon, radius, 0.02)
            idw_coords += area
            idw_distances += distances
        # Calculate all param values
        df = self.get_values(model, param, date_times, idw_coords)
        # Calculate idw distance and idw values
        df["idw_id"] = df.index // len_idw_dataset
        df["distances"] = idw_distances
        idw_values = df.groupby("idw_id").apply(idw, dist_col="distances", value_col=param)
        # Assignment of values
        df.drop_duplicates(subset="idw_id", inplace=True)
        lats, lons = [], []
        for lat, lon in coords:
            lats.append(lat)
            lons.append(lon)
        df[COL_LAT] = lats
        df[COL_LON] = lons
        df[param] = idw_values.values
        # drop temporary cols
        df.reset_index(drop=True, inplace=True)
        df.drop(["idw_id", "distances"], axis=1, inplace=True)
        return df

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


def _calc_idw(values: NDArray, distances: Series, weighting: int):
    zero_indexes = distances[distances == 0].index
    distances.drop(zero_indexes, inplace=True)
    values = np.delete(values, zero_indexes)

    numerator = np.sum(values / distances.values)
    denominator = np.sum(distances.values ** -weighting)
    return numerator / denominator


def _create_coords_in_radius(lat: float,
                             lon: float,
                             radius: float = 0.03,
                             delta: float = 0.02) -> (List[Tuple[float, float]], List[float]):
    points = []
    distances = []
    steps = int(radius / delta)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            new_lat = lat + i * delta
            new_lon = lon + j * delta
            distance = round((new_lat - lat) ** 2 + (new_lon - lon) ** 2, 6)
            if distance <= radius ** 2:
                points.append((new_lat, new_lon))
                distances.append(distance)
    return points, distances


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


import time

grib2_datas = Grib2Datas()
grib2_datas.load_folder("..\\DWD_Downloader\\WeatherData\\icon-d2")
t0 = time.time()
tmp_df = grib2_datas.get_values_idw(MODEL_ICON_D2, CLOUD_COVER, datetime(2024, 1, 31, 14, 15), [(53, 13), (54, 14)])
print(tmp_df)
duration = time.time() - t0
print(f"Dauer: {duration} sek.")
# tmp_df = grib2_datas.get_values(MODEL_ICON_D2,
#                                 CLOUD_COVER,
#                                 [datetime(2024, 2, 5, 18, 36),
#                                  datetime(2024, 1, 31, 14, 15)],
#                                 [(54, 14)])
# print(tmp_df)
# tmp_df = grib2_datas.get_values(MODEL_ICON_D2,
#                                 CLOUD_COVER,
#                                 [datetime(2024, 2, 5, 18, 36)],
#                                 [(54, 14), (55, 15)])
# print(tmp_df)
# tmp_df = grib2_datas.get_values(MODEL_ICON_D2,
#                                 CLOUD_COVER,
#                                 [datetime(2024, 2, 5, 18, 36)],
#                                 [(54, 14)])
# print(tmp_df)

# start_lat = 55.0
# fixed_lon = 99.0
# num_elements = 1800
# step_size = 0.02
#
# # List comprehension, um die Liste von Koordinaten zu erzeugen
# coords_list = [(start_lat - i * step_size, fixed_lon) for i in range(num_elements)]
# t0 = time.time()
# tmp_df = grib2_datas.get_values(MODEL_ICON_D2,
#                                 CLOUD_COVER,
#                                 [datetime(2024, 2, 5, 18, 36)],
#                                 coords_list)
# duration = time.time() - t0
# print(f"Dauer: {duration} sek.")
# print(f"Länge: {len(tmp_df)}")
# t0 = time.time()
# tmp_df = grib2_datas.get_multiple_values(MODEL_ICON_D2,
#                                          CLOUD_COVER,
#                                          datetime(2024, 2, 5, 18, 36),
#                                          coords_list)
# duration = time.time() - t0
# print(f"Dauer: {duration} sek.")
# print(f"Länge: {len(tmp_df)}")
# print(grib2_datas.get_value(MODEL_ICON_D2, CLOUD_COVER, datetime(2023, 11, 29, 18), 53, 13))
# print(grib2_datas.get_multiple_values(MODEL_ICON_D2, CLOUD_COVER, datetime(2023, 11, 29, 18), [(53, 13), (54, 13)]))
