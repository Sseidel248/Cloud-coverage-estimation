import csv
import os
import Lib.Consts.ModelConts as mConst
import Lib.CloudCoverageReader as ccr
import Lib.DWDStationReader as dwd_sr
from Lib.CloudCoverageReader import CloudCoverDatas
from Lib.DWDStationReader import DWDStation, DWDStations
from typing import List, Tuple


export_name = "data.csv"
delete_before_start = True


def get_usefull_station(dwd_locations: List[Tuple[float, float]], dwd_station_reader: DWDStations, cloud_cover_reader: CloudCoverDatas):
    for (lat, lon) in dwd_locations:
        station = dwd_station_reader.get_station(lat, lon)
        # Is Station loaded
        if not station.loaded:
            continue
        # Is the date range within the model values?
        if cloud_cover_reader.datetime_in_range(station.date_to):
            yield station


def export_as_csv(filename: str, dwd_stations: List[DWDStation], cloud_cover_reader: CloudCoverDatas):
    with (open(filename, 'w', newline='') as csv_file):
        writer = csv.writer(csv_file)

        # Write header line
        writer.writerow(['Date', 'Lat', 'Lon', 'Model-Value', 'Station-Value', 'Station-ID'])

        rows_to_write = []
        coords = []
        ids_station_values = []
        for idx, cc_date in enumerate(cloud_cover_reader.cloud_cover_files.keys()):
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
                    rows_to_write.append([cc_date, lat, lon, value, station_value, a_id])

            if len(rows_to_write) >= 1000:
                writer.writerows(rows_to_write)
                rows_to_write.clear()
            print(f"Writing process: {((idx + 1) / len(cloud_cover_reader.cloud_cover_files.keys())) * 100:.2f}%")

        if rows_to_write:
            writer.writerows(rows_to_write)

        print("Writing process: Done")


cc_reader = ccr.init_cloud_cover_data("..\\DWD_Downloader\\WeatherData\\ICON_D2", mConst.MODEL_ICON_D2)
print(f"Number of loaded Files: {len(cc_reader.cloud_cover_files)}")
all_model_datetimes = sorted(cc_reader.get_used_datetimes())

dwd_reader = dwd_sr.init_dwd_stations("..\\DWD_Downloader\\WeatherStations\\Cloudiness\\20231228")
all_dwd_locations = dwd_reader.get_station_locations()
print(f"Number of loaded DWD Stations: {len(all_dwd_locations)}")

all_usefull_stations = list(get_usefull_station(all_dwd_locations, dwd_reader, cc_reader))
print(f"Number of DWD measuring stations that can be used: {len(all_usefull_stations)}")

if delete_before_start and os.path.exists(export_name):
    os.remove(export_name)

export_as_csv(export_name, all_usefull_stations, cc_reader)
