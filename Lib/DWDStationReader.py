import os
import zipfile
import pathlib
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List
from Lib.ErrorWarningConsts import *
from Lib.ColoredPrint import *


_NONE_DATE = datetime(1970, 1, 1, 0, 0)
_EXTRACTION_FOLDER = ".\\extracted_station_files\\"
_INIT_FILE_MARKER = "Stundenwerte_Beschreibung_Stationen"
_DATA_FILE_MARKER = "produkt_"


class DWDStation:
    def __init__(self, datastr: str):
        self.filename = ""
        self.data = {}
        self.loaded = False
        match = re.search(r"(\d+) (\d+) (\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            self.id = int(match.group(1))
            self.date_from = datetime.strptime(match.group(2), "%Y%m%d")
            self.date_to = datetime.strptime(match.group(3), "%Y%m%d")
            self.height = int(match.group(4))
            self.lat = float(match.group(5))
            self.lon = float(match.group(6))
        else:
            self.id = -1
            self.date_from = _NONE_DATE
            self.date_to = _NONE_DATE
            self.height = -1
            self.lat = -1
            self.lon = -1

    def load_data(self, filename: str):
        self.filename = filename
        if os.path.exists(filename):
            with open(filename, 'r') as content:
                text = content.read()
                lines = text.strip().split('\n')
                # 1. Line Header
                for line in lines[1:]:
                    data = line.split(";")
                    date_time = datetime.strptime(data[1].strip(), "%Y%m%d%H")
                    value = data[4].strip()
                    self.data[date_time] = value.strip()
            self.loaded = len(self.data.keys()) > 0

    def get_value(self, date_time: datetime) -> float:
        rounded_datetime = _round_to_nearest_hour(date_time)
        if not self.loaded or self.data.get(rounded_datetime) is None:
            return -1
        return float(self.data[rounded_datetime])/8*100  # [%]

    def get_info_str(self) -> str:
        return f"Id: {self.id} ,Lat: {self.lat}, Lon: {self.lon}"


def _round_to_nearest_hour(date_time: datetime) -> datetime:
    rounded_date = date_time.replace(second=0, microsecond=0, minute=0)
    if date_time.minute >= 30:
        rounded_date += timedelta(hours=1)
    return rounded_date

class StationWarning:
    def __init__(self, warn_msg: str):
        self.stdwarn = warn_msg
        self.unloaded_dwdstations: List[DWDStation] = []

    def show_warnings(self):
        if len(self.unloaded_dwdstations) > 0:
            show_warning(self.stdwarn)
            for a_dwdstation in self.unloaded_dwdstations:
                show_warning(a_dwdstation.get_info_str(), True)

    def add(self, data: DWDStation):
        self.unloaded_dwdstations.append(data)

    def remove(self, data: DWDStation):
        for dwd_station in self.unloaded_dwdstations:
            if dwd_station.id == data.id:
                self.unloaded_dwdstations.remove(dwd_station)


class DWDStationResults:
    def __init__(self):
        self.folder = ""
        self.stations = {}
        self.id_latlon = {}
        self.stderr = ""
        self.unloaded_files = StationWarning("Unloaded DWD-Stations")

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
        self.stations.get(latlon_key).load_data(filename)
        self.unloaded_files.remove(self.stations.get(latlon_key))
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


def _get_files(look_up_path: str, extension: str) -> List[Path]:
    files = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    return files


def _get_init_file(look_up_path: str) -> str:
    files = _get_files(look_up_path, ".txt")
    for a_file in files:
        if _INIT_FILE_MARKER.lower() in str(a_file).lower():
            return str(a_file)
    return ERROR_INIT_FILE_NOT_EXIST


def _read_id(filename: str) -> int:
    if not os.path.exists(filename):
        return -1
    # Read the Textfile and get station id
    with open(filename, "r") as content:
        text = content.read()
        line = text.strip().split("\n")[:][1]
        return int(line.split(";")[0])


def init_dwd_stations(path: str) -> DWDStationResults:
    dwd_res = DWDStationResults()
    path = os.path.abspath(path)
    if not os.path.exists(path):
        show_error(f"The path you have entered does not exist. Your <path>: '{path}'")
        dwd_res.stderr = f"{ERROR_PATH_NOT_EXIST}: Path not exist"
        return dwd_res

    # Load init file who contains all station ids
    init_file = _get_init_file(path)
    if init_file == ERROR_INIT_FILE_NOT_EXIST:
        show_error(f"No init-file could be found (Filename contains: '{_INIT_FILE_MARKER}'. Your <path>: '{path}'")
        dwd_res.stderr = f"{ERROR_INIT_FILE_NOT_EXIST}: Init File not exist"
        return dwd_res

    # Read the init File -> Content: all Ids of DWD Stations
    with open(init_file, 'r') as content:
        text = content.read()
        lines = text.strip().split('\n')
        # 1. Line Header, 2. Line Splitter (----)
        for line in lines[2:]:
            # Initial add for every Station
            dwd_res.add(line)
    if len(dwd_res.stations) == 0:
        dwd_res.stderr = f"{ERROR_CORRUPT_INIT_FILES}: Init File is corrupt or empty"

    # Collect all zip-files (dwd data-files)
    zip_files = _get_files(path, ".zip")
    for zip_file in zip_files:
        # ZIP-Datei öffnen
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            # Prüfe, ob die Zielfile in der ZIP-Datei existiert
            for name in a_zip.namelist():
                if _DATA_FILE_MARKER.lower() in name.lower():
                    # Extrahiere die Datei
                    a_zip.extract(name, os.path.abspath(_EXTRACTION_FOLDER))
    data_files = _get_files(_EXTRACTION_FOLDER, ".txt")
    if len(data_files) == 0:
        show_error(f"No *.txt files could be found. Your <path>: '{path}'")
        dwd_res.stderr = f"{ERROR_NO_DWD_STATIONDATA_FOUND}: No DWD station files could be found"
        return dwd_res

    # load every initialized station
    for data in data_files:
        dwd_res.load_station(str(data))

    # collect all unloaded stations
    all_unloaded = dwd_res.get_unloaded_stations()
    if len(all_unloaded) > 0:
        dwd_res.stderr = (f"{WARNING_SOME_STATIONS_UNLOADED}: Some stations are unloaded, please check here: "
                          f"[unloaded_files]")
    return dwd_res
