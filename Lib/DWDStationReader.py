"""
File name:      DWDStationReader.py
Author:         Sebastian Seidel
Date:           2024-**-**
Description:
"""
import os
import zipfile
import re
import Lib.GeneralFunctions as gFunc
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, List
from pandas import DataFrame
from Lib.IOConsts import *
from tqdm import tqdm
from colorama import Fore, Style


class CorruptedInitFileError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DWDStations:
    def __init__(self):
        columns = [COL_STATION_ID, COL_DATE_START, COL_DATE_END, COL_STATION_HEIGHT, COL_LAT, COL_LON,
                   COL_DWD_FILENAME, COL_PARAM, COL_DWD_LOADED]
        datatypes = {
            COL_STATION_ID: 'int',
            COL_DATE_START: 'datetime64[ns]',
            COL_DATE_END: 'datetime64[ns]',
            COL_STATION_HEIGHT: 'float',
            COL_LAT: 'float',
            COL_LON: 'float',
            COL_DWD_FILENAME: 'str',
            COL_PARAM: "str",
            COL_DWD_LOADED: 'bool',
        }
        self.df: DataFrame = DataFrame(columns=columns).astype(datatypes)

    def load_folder(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder: '{path}' not exist.")
        self._read_init_files(path)
        extract_dwd_archives(path)
        dwd_txt_files = gFunc.get_files(path, ".txt")
        # nothing or only the init file
        if len(dwd_txt_files) <= 1:
            raise FileNotFoundError(f"No DWD *.txt Files exist in '{path}'")
        for dwd_txt in tqdm(dwd_txt_files, total=len(dwd_txt_files), desc="Loading DWD-Files"):
            if INIT_FILE_MARKER not in os.path.basename(dwd_txt):
                self._load_dwd_txt(dwd_txt)
        self.df.sort_values(by=[COL_STATION_ID, COL_PARAM], inplace=True)

    def get_dwd_value(self, date_time: datetime,
                      lat: float,
                      lon: float,
                      use_all_params: bool = True,
                      params: List[str] = None) -> DataFrame:
        return self.get_dwd_multiple_values([date_time], lat, lon, use_all_params, params)

    def get_dwd_multiple_values(self, date_times: List[datetime],
                                lat: float,
                                lon: float,
                                use_all_params: bool = True,
                                params: List[str] = None) -> DataFrame:
        lat: float = round(lat, 4)
        lon: float = round(lon, 4)
        if self.df.loc[(self.df[COL_LAT] == lat)
                       & (self.df[COL_LON] == lon)
                       & (self.df[COL_DWD_LOADED] == True)].empty:
            return pd.DataFrame()

        date_times = pd.DataFrame(date_times, columns=["Datetime"])
        # Init start structure
        result_df: DataFrame = pd.DataFrame()
        result_df[COL_DATE] = date_times["Datetime"].apply(gFunc.round_to_nearest_hour)
        result_df[COL_STATION_ID] = self.df.loc[(self.df[COL_LAT] == lat)
                                                & (self.df[COL_LON] == lon), COL_STATION_ID].iloc[0]
        result_df[COL_STATION_HEIGHT] = self.df.loc[(self.df[COL_LAT] == lat)
                                                    & (self.df[COL_LON] == lon), COL_STATION_HEIGHT].iloc[0]
        result_df[COL_LAT] = lat
        result_df[COL_LON] = lon
        result_df[COL_STATION_HEIGHT] = np.nan
        # check if all params used or not. Ignore empty param
        if use_all_params or params is None:
            params = [param for param in self.df[COL_PARAM].unique().tolist() if param.strip()]
        # fill structure for each param
        for param in params:
            row: DataFrame = self.df.loc[(self.df[COL_LAT] == lat)
                                         & (self.df[COL_LON] == lon)
                                         & (self.df[COL_PARAM] == param)]
            if row.empty:
                continue
            filename: str = row[COL_DWD_FILENAME].iloc[0]
            height: float = float(row[COL_STATION_HEIGHT].iloc[0])
            if os.path.exists(filename):
                df_file = read_file_to_df(filename)
                matching_rows = df_file[df_file[COL_DATE].isin(result_df[COL_DATE])].copy()
                if not matching_rows.empty:
                    result_df = result_df.merge(matching_rows[[COL_DATE, param]], on=COL_DATE, how='left')
                    result_df[COL_STATION_HEIGHT].fillna(height, inplace=True)
        # if eor columns exist, then remove it
        if "eor" in result_df.columns:
            result_df = result_df.drop(columns=["eor"])
        return result_df.dropna()

    def get_unloaded_stations(self) -> DataFrame:
        return self.df.loc[self.df[COL_DWD_LOADED] == False]

    def get_stations(self,
                     lat_range: Tuple[float, float] = None,
                     lon_range: Tuple[float, float] = None) -> DataFrame:
        if lat_range is not None and lon_range is not None:
            filtered_df = self.df.loc[(self.df[COL_LAT] >= lat_range[0]) & (self.df[COL_LAT] <= lat_range[1])
                                      & (self.df[COL_LON] >= lon_range[0]) & (self.df[COL_LON] <= lon_range[1])]
        elif lat_range is not None:
            filtered_df = self.df.loc[(self.df[COL_LAT] >= lat_range[0]) & (self.df[COL_LAT] <= lat_range[1])]
        elif lon_range is not None:
            filtered_df = self.df.loc[(self.df[COL_LAT] >= lon_range[0]) & (self.df[COL_LAT] <= lon_range[1])]
        else:
            filtered_df = self.df.copy()
        return filtered_df

    def get_station(self, lat: float, lon: float) -> DataFrame:
        return self.df.loc[(self.df[COL_LAT] == lat) & (self.df[COL_LON] == lon)]

    def datetime_in_range(self, date_time: datetime, lat: float, lon: float) -> bool:
        df = self.get_station(lat, lon)
        return df[COL_DATE_START].iloc[0] <= date_time <= df[COL_DATE_END].iloc[0]

    def get_station_locations(self) -> DataFrame:
        return self.df[[COL_LAT, COL_LON]].drop_duplicates()

    def _add_entry(self, datastr: str) -> bool:
        match = re.search(r"(\d+) (\d+) (\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            station_id: int = int(match.group(1))
            if self.df[COL_STATION_ID].isin([station_id]).any():
                return False
            new_row = {
                COL_STATION_ID: station_id,
                COL_DATE_START: datetime.strptime(match.group(2), "%Y%m%d"),
                COL_DATE_END: datetime.strptime(match.group(3), "%Y%m%d"),
                COL_STATION_HEIGHT: int(match.group(4)),
                COL_LAT: float(match.group(5)),
                COL_LON: float(match.group(6)),
                COL_DWD_FILENAME: "",
                COL_PARAM: "",
                COL_DWD_LOADED: False,
            }
            self.df.loc[len(self.df)] = new_row
            return True
        else:
            return False

    def count(self) -> int:
        return len(self.df[COL_STATION_ID].drop_duplicates())

    def _load_dwd_txt(self, filename: str) -> bool:
        a_id: int = _read_id(filename)
        params = _read_params(filename)
        if not params:
            return False

        row_index = self.df.index[self.df[COL_STATION_ID] == a_id].tolist()
        if not row_index:
            print(Fore.YELLOW +
                  f"\nStation ID '{a_id}' does not exist. Maybe the initialization file for the file "
                  f"'{filename}' was not loaded or the station ID does not exist in the initialization file."
                  + Style.RESET_ALL)
            return False

        start_date = _read_min_date(filename)
        end_date = _read_max_date(filename)

        # Check whether a parameter is already set for this StationId
        if self.df.at[row_index[0], COL_PARAM]:
            # If yes, copy the line for each additional parameter
            for param in params:
                new_row = self.df.loc[row_index[0]].copy()
                new_row[COL_PARAM] = param
                new_row[COL_DWD_FILENAME] = filename
                self.df.loc[len(self.df)] = new_row
        else:
            # If no, insert the first parameter in the existing line
            self.df.at[row_index[0], COL_PARAM] = params[0]
            # Set general information for the existing line
            self.df.loc[self.df[COL_STATION_ID] == a_id, [COL_DWD_LOADED, COL_DWD_FILENAME,
                                                          COL_DATE_START, COL_DATE_END]] = [True, filename,
                                                                                            start_date,
                                                                                            end_date]
            # For each additional parameter, add a new line
            for param in params[1:]:
                new_row = self.df.loc[row_index[0]].copy()
                new_row[COL_PARAM] = param
                self.df.loc[len(self.df)] = new_row
        return True

    def _read_init_files(self, path: str):
        files: list[str] = gFunc.get_files(path, ".txt")
        init_files: list[str] = []
        for a_file in files:
            if INIT_FILE_MARKER.lower() in str(a_file).lower():
                init_files.append(str(os.path.abspath(a_file)))
        if not init_files:
            raise FileNotFoundError(f"DWD-Stations init file not exist in '{path}'. The file name must contain the "
                                    f"following: '{INIT_FILE_MARKER}'")
        # Read the init File -> Content: all Ids of DWD Stations
        for init_file in init_files:
            with open(init_file, 'r') as content:
                # Skip Header line
                content.readline()
                # Skip Splitter line
                content.readline()
                for line in content:
                    line = line.strip()
                    if line:
                        self._add_entry(line)
        if len(self.df) == 0:
            raise CorruptedInitFileError("Init file contains no information on DWD stations.")


def _read_min_date(filename: str) -> datetime:
    with open(filename, 'r') as content:
        # Skip Header line
        content.readline()
        first_line: str = content.readline().strip()
        date: datetime = datetime.strptime(first_line.split(";")[1], "%Y%m%d%H")
        return date


def _read_max_date(filename: str) -> datetime:
    with open(filename, 'rb') as content:
        # Go to the last byte of the file
        content.seek(0, os.SEEK_END)
        position: int = content.tell()
        line: str = ''
        while position >= 0:
            content.seek(position)
            next_char = content.read(1)
            # Search backwards until you find a line break
            if next_char == b"\n":
                # Check if line contains ";"
                if ';' in line:
                    # reverse the reversed string
                    date: datetime = datetime.strptime(line[::-1].split(";")[1], "%Y%m%d%H")
                    return date
                # reset temp var
                line = ''
            else:
                line += next_char.decode()
            position -= 1
    return datetime(1970, 1, 1)


def read_file_to_df(filename: str) -> DataFrame:
    df = pd.read_csv(filename, sep=';', header=None)
    # remove empty spaces in headers
    header = df.iloc[0].apply(lambda x: x.strip())
    df.columns = header
    df = df.drop(0)
    # parse datetime column
    df.rename(columns={"MESS_DATUM": COL_DATE, "STATIONS_ID": COL_STATION_ID}, inplace=True)
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], format="%Y%m%d%H")
    return df


def extract_dwd_archives(path: str):
    # Collect all zip-files (dwd data-files)
    zip_files: list[str] = gFunc.get_files(path, ".zip")
    for zip_file in tqdm(zip_files, total=len(zip_files), desc="Extract DWD-Files"):
        # open zip file
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            directory: str = os.path.dirname(zip_file)
            # check if file to extract allready exist
            for name in a_zip.namelist():
                if DATA_FILE_MARKER.lower() in name.lower():
                    data_filename: str = os.path.join(os.path.abspath(directory), name)
                    if not os.path.exists(data_filename):
                        # extract data file and break inner loop
                        a_zip.extract(name, os.path.abspath(directory))
                        break


def _read_id(filename: str) -> int:
    if not os.path.exists(filename):
        return -1
    # Read the Textfile and get station id
    with open(filename, 'r') as content:
        content.readline()
        second_line = content.readline().strip()
        # check if second line exist
        if not second_line:
            return -1
        return gFunc.int_def(second_line.split(";")[0], -1)


def _read_params(filename: str) -> List[str]:
    if not os.path.exists(filename):
        return []
    # Read the Textfile and get station id
    with open(filename, 'r') as content:
        header_line = content.readline()
        headers = header_line.split(";")
        if len(headers) < 4:
            return []
        # 1. STATIONS_ID, 2. MESS_DATUM, 3. QN_*
        # export 4. until n-1 column
        return [name.strip() for name in headers[3:-1]]

# TODO: automatische Tets schreiben
# dwdv2 = DWDStations()
# dwdv2.load_folder("..\\DWD_Downloader\\WeatherStations\\")
# print(dwdv2.df[COL_DWD_PARAM].unique())
# print(dwdv2.df.head())
# print(dwdv2.df.columns)
# print(dwdv2.df .columns)
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, False, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, True, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, True))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, False))
# print(dwdv2.get_unloaded_stations())
# print(dwdv2.get_stations())
# print(dwdv2.get_stations((52.943, 53.95), (12.85, 12.86)))
# print(dwdv2.get_station(52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2022, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2025, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.get_station_locations())
# dates = [datetime(2022, 6, 26, 00, 15), datetime(2022, 6, 26, 00, 45)]
# print(dwdv2.get_dwd_multiple_values(dates, 52.9437, 12.8518, False, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2022, 6, 26, 00, 45), 52.9437, 12.8518, False, ["V_N"]))
