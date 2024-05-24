"""
General Information:
______
- File name:      Demo_evaluate_driving_profile.py
- Author:         Sebastian Seidel
- Date:           2024-04-10

Description:
______
Serves as an example for reading out the degree of cloud cover for a driving profile.
"""
from Lib.Grib2Reader import Grib2Datas
import pandas as pd
import Lib.IOConsts as ioc

g2r = Grib2Datas()
# choose the folde with the grib2 files of DWD forecast model
g2r.load_folder(".\\Data_Downloader\\WeatherData\\icon-d2")
# Csv-file must contain following columns: datetime_UTC, lat, lon
car_profile = pd.read_csv("example_driving_profile.csv")
# Specify formatting of the date string
datetimes = pd.to_datetime(car_profile["datetime_UTC"], format="%Y.%m.%d %H:%M:%S")
lats = car_profile["lat"]
lons = car_profile["lon"]
# Create an list with coordinates list[tuple(float, float)]
coords = []
for lat, lon in zip(lats, lons):
    coords += [(lat, lon)]
# Calculate model values
df_car_profile = g2r.get_values(ioc.MODEL_ICON_D2, ioc.CLOUD_COVER, datetimes, coords)
print(df_car_profile)
print(df_car_profile.dtypes)

