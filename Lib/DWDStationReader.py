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
from datetime import datetime
from typing import Tuple
from pandas import DataFrame
from Lib.Consts.DWDReaderConsts import *


class CorruptedInitFileError(Exception):
    def __init__(self, message):
        super().__init__(message)


class DWDStations:
    def __init__(self):
        self.init_file = ""
        columns = [COL_STATION_ID, COL_DATE_START, COL_DATE_END, COL_HEIGHT, COL_LAT, COL_LON, COL_DWD_FILENAME,
                   COL_LOADED]
        datatypes = {
            COL_STATION_ID: 'int',
            COL_DATE_START: 'datetime64[ns]',
            COL_DATE_END: 'datetime64[ns]',
            COL_HEIGHT: 'float',
            COL_LAT: 'float',
            COL_LON: 'float',
            COL_DWD_FILENAME: 'str',
            COL_LOADED: 'bool',
        }
        self.df: DataFrame = DataFrame(columns=columns).astype(datatypes)

    def load_folder(self, path: str):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder: '{path}' not exist.")
        self._read_init_file(path)
        extract_dwd_archives(path)
        dwd_txt_files = gFunc.get_files(path, ".txt")
        # nothing or only the init file
        if len(dwd_txt_files) <= 1:
            raise FileNotFoundError(f"No DWD *.txt Files exist in '{path}'")
        for dwd_txt in dwd_txt_files:
            if INIT_FILE_MARKER not in os.path.basename(dwd_txt):
                self._load_dwd_txt(dwd_txt)
        self.df.sort_values(by=[COL_LOADED, COL_DATE_START, COL_DATE_END])

    # TODO: Zeile aus der Datei laden und exportieren
    def get_dwd_value(self, date_time: datetime, lat: float, lon: float) -> DataFrame:
        lat: float = round(lat, 4)
        lon: float = round(lon, 4)
        row: DataFrame = self.df.loc[(self.df[COL_LAT] == lat) & (self.df[COL_LON] == lon)]
        if row.empty:
            return DataFrame()
        rounded_datetime: datetime = gFunc.round_to_nearest_hour(date_time)
        filename: str = row[COL_DWD_FILENAME].iloc[0]
        height: float = float(row[COL_HEIGHT].iloc[0])
        if os.path.exists(filename):
            df_file = read_file_to_df(filename)
            matching_row = df_file[df_file[COL_DWD_MESS_DATUM] == rounded_datetime].copy()
            if not matching_row.empty:
                matching_row[COL_LAT] = lat
                matching_row[COL_LON] = lon
                matching_row[COL_HEIGHT] = height
                return matching_row
        return DataFrame()

    # TODO: Zeilen aus der Datei laden und exportieren
    def get_dwd_multiple_value(self, date_times: DataFrame, lat: float, lon: float) -> DataFrame:
        lat: float = round(lat, 4)
        lon: float = round(lon, 4)
        row: DataFrame = self.df.loc[(self.df[COL_LAT] == lat) & (self.df[COL_LON] == lon)]
        if row.empty:
            return DataFrame()
        date_times = date_times.copy()
        first_col_name = date_times.columns[0]
        date_times["Rounded_Datetime"] = date_times[first_col_name].apply(gFunc.round_to_nearest_hour)
        filename: str = row[COL_DWD_FILENAME].iloc[0]
        height: float = float(row[COL_HEIGHT].iloc[0])
        if os.path.exists(filename):
            df_file = read_file_to_df(filename)
            matching_rows = df_file[df_file[COL_DWD_MESS_DATUM].isin(date_times["Rounded_Datetime"])].copy()
            if not matching_rows.empty:
                matching_rows[COL_LAT] = lat
                matching_rows[COL_LON] = lon
                matching_rows[COL_HEIGHT] = height
                return matching_rows
        return DataFrame()

    def get_unloaded_stations(self) -> DataFrame:
        return self.df.loc[self.df[COL_LOADED] == False]

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
        return self.df[[COL_LAT, COL_LON]]

    def _add_entry(self, datastr: str) -> bool:
        match = re.search(r"(\d+) (\d+) (\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            new_row = {
                COL_STATION_ID: int(match.group(1)),
                COL_DATE_START: datetime.strptime(match.group(2), "%Y%m%d"),
                COL_DATE_END: datetime.strptime(match.group(3), "%Y%m%d"),
                COL_HEIGHT: int(match.group(4)),
                COL_LAT: float(match.group(5)),
                COL_LON: float(match.group(6)),
                COL_DWD_FILENAME: "",
                COL_LOADED: False,
            }
            self.df.loc[len(self.df)] = new_row
        else:
            return False

    def count(self) -> int:
        return len(self.df)

    def _load_dwd_txt(self, filename: str) -> bool:
        a_id: int = _read_id(filename)
        row: DataFrame = self.df.loc[self.df[COL_STATION_ID] == a_id]
        if row.empty:
            return False
        self._read_min_date(a_id, filename)
        self._read_max_date(a_id, filename)
        self.df.loc[self.df[COL_STATION_ID] == a_id, COL_LOADED] = True
        self.df.loc[self.df[COL_STATION_ID] == a_id, COL_DWD_FILENAME] = filename
        return True

    def _read_init_file(self, path: str):
        files: list[str] = gFunc.get_files(path, ".txt")
        for a_file in files:
            if INIT_FILE_MARKER.lower() in str(a_file).lower():
                self.init_file = str(os.path.abspath(a_file))
        if self.init_file == "":
            raise FileNotFoundError(f"DWD-Stations init file not exist in '{path}'. The file name must contain the "
                                    f"following: '{INIT_FILE_MARKER}'")
        # Read the init File -> Content: all Ids of DWD Stations
        with open(self.init_file, 'r') as content:
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

    def _read_min_date(self, a_id: int, filename: str):
        with open(filename, 'r') as content:
            # Skip Header line
            content.readline()
            first_line: str = content.readline().strip()
            date: datetime = datetime.strptime(first_line.split(";")[1], "%Y%m%d%H")
            self.df.loc[self.df[COL_STATION_ID] == a_id, COL_DATE_START] = date

    def _read_max_date(self, a_id: int, filename: str):
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
                        self.df.loc[self.df[COL_STATION_ID] == a_id, COL_DATE_END] = date
                        return
                    # reset temp var
                    line = ''
                else:
                    line += next_char.decode()
                position -= 1


def read_file_to_df(filename: str) -> DataFrame:
    df = pd.read_csv(filename, sep=';', header=None)
    # remove empty spaces in headers
    header = df.iloc[0].apply(lambda x: x.strip())
    df.columns = header
    df = df.drop(0)
    # parse datetime column
    df[COL_DWD_MESS_DATUM] = pd.to_datetime(df[COL_DWD_MESS_DATUM], format="%Y%m%d%H")
    return df


def extract_dwd_archives(path: str):
    # Collect all zip-files (dwd data-files)
    zip_files: list[str] = gFunc.get_files(path, ".zip")
    for zip_file in zip_files:
        # open zip file
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            directory: str = os.path.dirname(zip_file)
            # check if file to extract allready exist
            for name in a_zip.namelist():
                if DATA_FILE_MARKER.lower() in name.lower():
                    data_filename: str = os.path.join(os.path.abspath(directory), name)
                    if not os.path.exists(data_filename):
                        # extract data file
                        a_zip.extract(name, os.path.abspath(directory))


def get_measurment_type(data: str) -> str:
    data = data.strip()
    if data == "I":
        return MARKER_I
    elif data == "P":
        return MARKER_P
    else:
        return Marker_999


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


# TODO: automatische Tets schreiben
# dwdv2 = DWDStations()
# dwdv2.load_folder("..\\DWD_Downloader\\WeatherStations\\Cloudiness\\20231228")
# print(dwdv2.get_dwd_value(datetime(2022, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.get_unloaded_stations())
# print(dwdv2.get_stations())
# print(dwdv2.get_stations((52.943, 53.95), (12.85, 12.86)))
# print(dwdv2.get_station(52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2022, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2025, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.get_station_locations())
# dates = pd.DataFrame({COL_DATE_VALUE: [datetime(2022, 6, 26, 00, 15), datetime(2022, 6, 26, 00, 45)]})
# print(dwdv2.get_dwd_multiple_value(dates, 52.9437, 12.8518))
