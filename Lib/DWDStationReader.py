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
_INIT_FILE_MARKER: str = "Stundenwerte_Beschreibung_Stationen"
_DATA_FILE_MARKER: str = "produkt_"


class DWDValue:
    def __init__(self):
        self.value: float = -1
        self.measurement_type = ""


class DWDStation:
    def __init__(self, datastr: str):
        self.filename: str = ""
        self.loaded: bool = False
        self.id: int = -1
        self.date_from: datetime = gConst.NONE_DATETIME
        self.date_to: datetime = gConst.NONE_DATETIME
        self.height: int = -1
        self.lat: float = -1
        self.lon: float = -1
        match = re.search(r"(\d+) (\d+) (\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            self.id = int(match.group(1))
            self.date_from = datetime.strptime(match.group(2), "%Y%m%d")
            self.date_to = datetime.strptime(match.group(3), "%Y%m%d")
            self.height = int(match.group(4))
            self.lat = float(match.group(5))
            self.lon = float(match.group(6))

    def load_data(self, filename: str):
        self.filename = filename
        if os.path.exists(filename):
            self.loaded = True
            with open(filename, 'r') as content:
                # Skip Header line
                content.readline()
                first_line: str = content.readline().strip()
                self.date_from = datetime.strptime(first_line.split(";")[1], "%Y%m%d%H")
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
                            self.date_to = datetime.strptime(line[::-1].split(";")[1], "%Y%m%d%H")
                            return
                        # reset temp var
                        line = ''
                    else:
                        line += next_char.decode()
                    position -= 1

    def get_value(self, date_time: datetime) -> DWDValue:
        rounded_datetime: datetime = gFunc.round_to_nearest_hour(date_time)
        datetime_str: str = rounded_datetime.strftime("%Y%m%d%H")
        if os.path.exists(self.filename):
            with open(self.filename, 'r') as content:
                for line in content:
                    if datetime_str in line:
                        parts: list[str] = line.split(';')
                        if len(parts) > 4:
                            dwd_value:DWDValue = DWDValue()
                            dwd_value.measurement_type = parts[3].strip()
                            value: float = float(parts[4].strip())
                            if value != -1:
                                dwd_value.value = value / 8 * 100
                            return dwd_value
        return DWDValue()

    def get_info_str(self):
        return _get_info_str(self)

    def datetime_in_range(self, date_time: datetime) -> bool:
        return self.date_from <= date_time <= self.date_to


class InvalidStations:
    def __init__(self, warn_msg: str):
        self.stdwarn: str = warn_msg
        self.unloaded_dwdstations: List[DWDStation] = []

    def show_warnings(self):
        if len(self.unloaded_dwdstations) > 0:
            clPrint.show_warning(self.stdwarn)
            for a_dwdstation in self.unloaded_dwdstations:
                clPrint.show_warning(_get_info_str(a_dwdstation), True)

    def add(self, data: DWDStation):
        self.unloaded_dwdstations.append(data)

    def remove(self, a_id: int):
        for dwd_station in self.unloaded_dwdstations:
            if dwd_station.id == a_id:
                self.unloaded_dwdstations.remove(dwd_station)


class DWDStations:
    def __init__(self):
        self.stations: dict[str, DWDStation] = {}
        self.id_latlon: [int, str] = {}
        self.stderr: str = ""
        self.unloaded_files: InvalidStations = InvalidStations("Unloaded DWD-Stations")

    def add(self, datastr: str) -> bool:
        dwd_station: DWDStation = DWDStation(datastr)
        if dwd_station.id == -1:
            return False
        lat: float = dwd_station.lat
        lon: float = dwd_station.lon
        # add DWD Station with lat lon as key and collect id for the "lat lon" key
        if self.stations.get(f"{lat};{lon}") is None:
            self.stations[f"{lat};{lon}"] = dwd_station
            self.id_latlon[dwd_station.id] = f"{lat};{lon}"
            self.unloaded_files.add(self.stations.get(f"{lat};{lon}"))
            return True
        else:
            return False

    def load_station(self, filename: str) -> bool:
        a_id: int = _read_id(filename)
        if self.id_latlon.get(a_id) is None:
            return False
        latlon_key: str = self.id_latlon[a_id]
        self.stations[latlon_key].load_data(filename)
        self.unloaded_files.remove(a_id)
        return True

    def get_value(self, date_time: datetime, lat: float, lon: float) -> DWDValue:
        lat: float = round(lat, 4)
        lon: float = round(lon, 4)
        if self.stations.get(f"{lat};{lon}") is None:
            return DWDValue()
        return self.stations[f"{lat};{lon}"].get_value(date_time)

    def get_unloaded_stations(self) -> List[DWDStation]:
        return self.unloaded_files.unloaded_dwdstations

    def show_unloaded_files(self):
        self.unloaded_files.show_warnings()

    def get_stations(self,
                     lat_range: Tuple[float, float] = None,
                     lon_range: Tuple[float, float] = None) -> List[DWDStation]:
        return [station for station in self.stations.values()
                if (lat_range is None or lat_range[0] <= station.lat <= lat_range[1])
                and (lon_range is None or lon_range[0] <= station.lon <= lon_range[1])]

    def get_station(self, lat: float, lon: float) -> DWDStation | None:
        if not (self.stations.get(f"{lat};{lon}") is None):
            return self.stations[f"{lat};{lon}"]
        return None

    def datetime_in_range(self, date_time: datetime, lat: float, lon: float) -> bool:
        if not (self.get_station(lat, lon) is None):
            return self.get_station(lat, lon).datetime_in_range(date_time)
        return False

    def get_station_locations(self) -> List[Tuple[float, float]]:
        locations_list: list[tuple[float, float]] = []
        for key in self.stations:
            lat_str, lon_str = key.split(';')
            locations_list.append((float(lat_str), float(lon_str)))
        return locations_list


def _get_init_file(look_up_path: str) -> str:
    files: list[str] = gFunc.get_files(look_up_path, ".txt")
    for a_file in files:
        if _INIT_FILE_MARKER.lower() in str(a_file).lower():
            return str(a_file)
    return ewConst.ERROR_INIT_FILE_NOT_EXIST


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


def _get_info_str(dwd_station: DWDStation) -> str:
    return (f"Id: {dwd_station.id} ,Lat: {dwd_station.lat} ,Lon: {dwd_station.lon} ,Loaded: {dwd_station.loaded} "
            f",File: {dwd_station.filename}")


def init_dwd_stations(path: str) -> DWDStations:
    dwds: DWDStations = DWDStations()
    path: str = os.path.abspath(path)
    if not os.path.exists(path):
        clPrint.show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        dwds.stderr = f"{ewConst.ERROR_PATH_NOT_EXIST}: Path not exist"
        return dwds

    # Load init file who contains all station ids
    init_file: str = _get_init_file(path)
    if init_file == ewConst.ERROR_INIT_FILE_NOT_EXIST:
        clPrint.show_error(f"No init-file could be found (Filename contains: '{_INIT_FILE_MARKER}'. "
                           f"Your <path>: '{path}'")
        dwds.stderr = f"{ewConst.ERROR_INIT_FILE_NOT_EXIST}: Init File not exist"
        return dwds

    # Read the init File -> Content: all Ids of DWD Stations
    with open(init_file, 'r') as content:
        # Skip Header line
        content.readline()
        # Skip Splitter line
        content.readline()
        for line in content:
            line = line.strip()
            if line:
                dwds.add(line)
    if len(dwds.stations) == 0:
        dwds.stderr = f"{ewConst.ERROR_CORRUPT_INIT_FILES}: Init File is corrupt or empty"
        return dwds

    # Collect all zip-files (dwd data-files)
    zip_files: list[str] = gFunc.get_files(path, ".zip")
    for zip_file in zip_files:
        # ZIP-Datei öffnen
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            directory: str = os.path.dirname(zip_file)
            # Prüfe, ob die Zielfile in der ZIP-Datei existiert
            for name in a_zip.namelist():
                if _DATA_FILE_MARKER.lower() in name.lower():
                    data_filename: str = os.path.join(os.path.abspath(directory), name)
                    if not os.path.exists(data_filename):
                        # Extrahiere die Datei
                        a_zip.extract(name, os.path.abspath(directory))
    data_files: list[str] = gFunc.get_files(path, ".txt")
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
    all_unloaded: list[DWDStation] = dwds.get_unloaded_stations()
    if len(all_unloaded) > 0:
        clPrint.show_warning(f"init_dwd_stations(...): Some stations are no longer up to date, "
                             f"these station have been ignored. "
                             f"({len(all_unloaded)}/{len(dwds.stations)} are unloaded)")
        dwds.stderr = (f"{ewConst.WARNING_SOME_STATIONS_UNLOADED}: Some stations are unloaded "
                       f", please check here: [unloaded_files]")
    return dwds
