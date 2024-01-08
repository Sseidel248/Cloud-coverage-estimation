"""
File name:      DataExport.py
Author:         Sebastian Seidel
Date:           2024.**.**
"""
import os
import pandas as pd
import Lib.Consts.ModelConts as mConst
import Lib.CloudCoverageReader as ccr
import Lib.DWDStationReader as dwd_sr
import DataConsts as dc
from Lib.CloudCoverageReader import CloudCoverDatas
from Lib.DWDStationReader import DWDStation, DWDStations
from typing import List, Tuple


def get_usefull_station(dwd_locations: List[Tuple[float, float]], dwd_station_reader: DWDStations,
                        cloud_cover_reader: CloudCoverDatas):
    for (lat, lon) in dwd_locations:
        station = dwd_station_reader.get_station(lat, lon)
        # Is Station loaded
        if not station.loaded:
            continue
        # Is the date range within the model values?
        if cloud_cover_reader.datetime_in_range(station.date_to):
            yield station


def export_as_csv(filename: str, dwd_stations: List[DWDStation], cloud_cover_reader: CloudCoverDatas):
    data = {
        dc.DATE: [],
        dc.LAT: [],
        dc.LON: [],
        dc.MODEL_VALUE: [],
        dc.STATION_VALUE: [],
        dc.STATION_ID: []
    }
    coords = []
    ids_station_values = []
    for idx, cc_date in enumerate(cloud_cover_reader.cloud_cover_files):
        coords.clear()
        ids_station_values.clear()

        for dwd in dwd_stations:
            station_value = dwd.get_value(cc_date)
            if station_value == -1:
                continue
            if cloud_cover_reader.lat_in_range(dwd.lat) and cloud_cover_reader.lon_in_range(dwd.lon):
                coords.append((dwd.lat, dwd.lon))
                ids_station_values.append((dwd.id, station_value))

        if coords:
            cc = cloud_cover_reader.cloud_cover_files[cc_date]
            values = cc.get_multiple_values(coords)
            for (a_id, station_value), value, (lat, lon) in zip(ids_station_values, values, coords):
                data[dc.DATE].append(cc_date)
                data[dc.LAT].append(lat)
                data[dc.LON].append(lon)
                data[dc.MODEL_VALUE].append(value)
                data[dc.STATION_VALUE].append(station_value)
                data[dc.STATION_ID].append(a_id)

        print(f"Writing process: {((idx + 1) / len(cloud_cover_reader.cloud_cover_files)) * 100:.2f}%")

    df = pd.DataFrame(data)
    df_sorted = df.sort_values(by=dc.STATION_ID)
    # German seperation, default is english sep="," and decimal="."
    df_sorted.to_csv(filename, sep=";", decimal=",", index=False)
    print("Writing process: Done")
    print(f"Data export: '{os.path.abspath(filename)}'")


cc_reader = ccr.init_cloud_cover_data("..\\DWD_Downloader\\WeatherData\\ICON_D2", mConst.MODEL_ICON_D2)
# cc_reader = ccr.init_cloud_cover_data("..\\DWD_Downloader\\WeatherData\\ICON_EU", mConst.MODEL_ICON_EU)
print(f"Number of loaded Files: {len(cc_reader.cloud_cover_files)}")
all_model_datetimes = sorted(cc_reader.get_used_datetimes())

dwd_reader = dwd_sr.init_dwd_stations("..\\DWD_Downloader\\WeatherStations\\Cloudiness\\20231228")
all_dwd_locations = dwd_reader.get_station_locations()
print(f"Number of loaded DWD Stations: {len(all_dwd_locations)}")

all_usefull_stations = list(get_usefull_station(all_dwd_locations, dwd_reader, cc_reader))
print(f"Number of DWD measuring stations that can be used: {len(all_usefull_stations)}")

if dc.DELETE_BEFORE_START and os.path.exists(dc.EXPORT_NAME):
    os.remove(dc.EXPORT_NAME)

export_as_csv(dc.EXPORT_NAME, all_usefull_stations, cc_reader)
