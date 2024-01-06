"""
File name:      DWDStationReader.py
Author:         Sebastian Seidel
Date:           2024-**-**
Description:
"""
import os
import zipfile
import re

import Lib.Consts.ErrorWarningConsts as ewConst
import Lib.ColoredPrint as clPrint
import Lib.Consts.GeneralConts as gConst
import Lib.GeneralFunctions as gFunc
from datetime import datetime
from typing import List, Tuple


# local consts
_INIT_FILE_MARKER = "Stundenwerte_Beschreibung_Stationen"
_DATA_FILE_MARKER = "produkt_"


class DWDStation:
    def __init__(self, datastr: str):
        self.filename = ""
        self.loaded = False
        match = re.search(r"(\d+) (\d+) (\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            self.id = int(match.group(1))
            self.date_from = datetime.strptime(match.group(2), "%Y%m%d")
            self.date_to = datetime.strptime(match.group(3), "%Y%m%d")
            self.height = int(match.group(4))
            self.lat = float(match.group(5))
            self.lon = float(match.group(6))
        else:
            self.id = -1
            self.date_from = gConst.NONE_DATETIME
            self.date_to = gConst.NONE_DATETIME
            self.height = -1
            self.lat = -1
            self.lon = -1

    def load_data(self, filename: str):
        self.filename = filename
        if os.path.exists(filename):
            self.loaded = True
            with open(filename, 'r') as content:
                text = content.read()
                lines = text.strip().split('\n')
                # 1. Line Header
                if len(lines) > 1:
                    self.date_from = datetime.strptime(lines[1].split(";")[1], "%Y%m%d%H")
                    self.date_to = datetime.strptime(lines[-1].split(";")[1], "%Y%m%d%H")

    def get_value(self, date_time: datetime) -> float:
        rounded_datetime = gFunc.round_to_nearest_hour(date_time)
        datetime_str = rounded_datetime.strftime("%Y%m%d%H")
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as content:
                for line in content:
                    if datetime_str in line:
                        parts = line.split(';')  # Teilt die Zeile an jedem Semikolon
                        if len(parts) > 4:  # Stellen Sie sicher, dass genügend Elemente vorhanden sind
                            value = float(parts[4].strip())  # Entfernen Sie Whitespace um den Wert
                            if value == -1:
                                return -1
                            return value / 8 * 100
        return -1

    def get_info_str(self) -> str:
        return f"Id: {self.id} ,Lat: {self.lat} ,Lon: {self.lon} ,File: {self.filename} ,Loaded: {self.loaded}"

    def datetime_in_range(self, date_time: datetime) -> bool:
        return self.date_from <= date_time <= self.date_to


class InvalidStations:
    def __init__(self, warn_msg: str):
        self.stdwarn = warn_msg
        self.unloaded_dwdstations: List[DWDStation] = []

    def show_warnings(self):
        if len(self.unloaded_dwdstations) > 0:
            clPrint.show_warning(self.stdwarn)
            for a_dwdstation in self.unloaded_dwdstations:
                clPrint.show_warning(a_dwdstation.get_info_str(), True)

    def add(self, data: DWDStation):
        self.unloaded_dwdstations.append(data)

    def remove(self, a_id: int):
        for dwd_station in self.unloaded_dwdstations:
            if dwd_station.id == a_id:
                self.unloaded_dwdstations.remove(dwd_station)


class DWDStations:
    def __init__(self):
        self.stations = {}
        self.id_latlon = {}
        self.stderr = ""
        self.unloaded_files = InvalidStations("Unloaded DWD-Stations")

    def add(self, datastr: str) -> bool:
        dwd_station = DWDStation(datastr)
        if dwd_station.id == -1:
            return False
        lat = dwd_station.lat
        lon = dwd_station.lon
        # add DWD Station with lat lon as key and collect id for the "lat lon" key
        if self.stations.get(f"{lat};{lon}") is None:
            self.stations[f"{lat};{lon}"] = dwd_station
            self.id_latlon[dwd_station.id] = f"{lat};{lon}"
            self.unloaded_files.add(self.stations.get(f"{lat};{lon}"))
            return True
        else:
            return False

    def load_station(self, filename: str) -> bool:
        a_id = _read_id(filename)
        if self.id_latlon.get(a_id) is None:
            return False
        latlon_key = self.id_latlon[a_id]
        self.stations[latlon_key].load_data(filename)
        self.unloaded_files.remove(a_id)
        return True

    def get_value(self, date_time: datetime, lat: float, lon: float) -> float:
        lat = round(lat, 4)
        lon = round(lon, 4)
        if self.stations.get(f"{lat};{lon}") is None:
            return -1
        return self.stations[f"{lat};{lon}"].get_value(date_time)

    def get_unloaded_stations(self) -> List[DWDStation]:
        return self.unloaded_files.unloaded_dwdstations

    def show_unloaded_files(self):
        self.unloaded_files.show_warnings()

    def get_stations(self) -> List[DWDStation]:
        return list(self.stations.values())

    def get_station(self, lat: float, lon: float) -> DWDStation | None:
        if not (self.stations.get(f"{lat};{lon}") is None):
            return self.stations[f"{lat};{lon}"]
        return None

    def datetime_in_range(self, date_time: datetime, lat: float, lon: float) -> bool:
        if not (self.get_station(lat, lon) is None):
            return self.get_station(lat, lon).datetime_in_range(date_time)
        return False

    def get_station_locations(self) -> List[Tuple[float, float]]:
        locations_list = []
        for key in self.stations.keys():
            lat_str, lon_str = key.split(';')
            locations_list.append((float(lat_str), float(lon_str)))
        return locations_list


def _get_init_file(look_up_path: str) -> str:
    files = gFunc.get_files(look_up_path, ".txt")
    for a_file in files:
        if _INIT_FILE_MARKER.lower() in str(a_file).lower():
            return str(a_file)
    return ewConst.ERROR_INIT_FILE_NOT_EXIST


def _read_id(filename: str) -> int:
    if not os.path.exists(filename):
        return -1
    # Read the Textfile and get station id
    with open(filename, "r") as content:
        text = content.read()
        lines = text.strip().split("\n")
        # First row contain column headers
        if len(lines) <= 1:
            return -1
        line = lines[:][1]
        return gFunc.int_def(line.split(";")[0], -1)


def init_dwd_stations(path: str) -> DWDStations:
    dwds = DWDStations()
    path = os.path.abspath(path)
    if not os.path.exists(path):
        clPrint.show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        dwds.stderr = f"{ewConst.ERROR_PATH_NOT_EXIST}: Path not exist"
        return dwds

    # Load init file who contains all station ids
    init_file = _get_init_file(path)
    if init_file == ewConst.ERROR_INIT_FILE_NOT_EXIST:
        clPrint.show_error(f"No init-file could be found (Filename contains: '{_INIT_FILE_MARKER}'. "
                           f"Your <path>: '{path}'")
        dwds.stderr = f"{ewConst.ERROR_INIT_FILE_NOT_EXIST}: Init File not exist"
        return dwds

    # Read the init File -> Content: all Ids of DWD Stations
    with open(init_file, 'r') as content:
        text = content.read()
        lines = text.strip().split('\n')
        # 1. Line Header, 2. Line Splitter (----)
        for line in lines[2:]:
            # Initial add for every Station
            dwds.add(line)
    if len(dwds.stations) == 0:
        dwds.stderr = f"{ewConst.ERROR_CORRUPT_INIT_FILES}: Init File is corrupt or empty"
        return dwds

    # Collect all zip-files (dwd data-files)
    zip_files = gFunc.get_files(path, ".zip")
    for zip_file in zip_files:
        # ZIP-Datei öffnen
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            directory = os.path.dirname(zip_file)
            # Prüfe, ob die Zielfile in der ZIP-Datei existiert
            for name in a_zip.namelist():
                if _DATA_FILE_MARKER.lower() in name.lower():
                    data_filename = os.path.join(os.path.abspath(directory), name)
                    if not os.path.exists(data_filename):
                        # Extrahiere die Datei
                        a_zip.extract(name, os.path.abspath(directory))
    data_files = gFunc.get_files(path, ".txt")
    # Only 1 Init File with extension *.txt
    if len(data_files) == 1:
        clPrint.show_error(f"No *.txt files could be found. Your <path>: '{path}'")
        dwds.stderr = f"{ewConst.ERROR_NO_DWD_STATIONDATA_FOUND}: No DWD station files could be found"
        return dwds

    # load every initialized station
    for idx, a_file in enumerate(data_files):
        if idx == 0:
            continue
        dwds.load_station(str(a_file))

    # collect all unloaded stations
    all_unloaded = dwds.get_unloaded_stations()
    if len(all_unloaded) > 0:
        clPrint.show_warning(f"init_dwd_stations(...): Some stations are unloaded, these station have been ignored. "
                             f"({len(all_unloaded)}/{len(dwds.stations)} are unloaded)")
        dwds.stderr = (f"{ewConst.WARNING_SOME_STATIONS_UNLOADED}: Some stations are unloaded "
                       f", please check here: [unloaded_files]")
    return dwds
