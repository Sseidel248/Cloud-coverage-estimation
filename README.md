# Master Thesis 
## Cloud coverage estimation
This project is part of my master's thesis in the field of "Driver behavior monitoring for energy optimization and accident prevention" at the Technical University of Berlin. It deals with identification of the percentage of cloud cover at a location at a specific point in time.

I mainly worked with data from the DWD (German Weather Service).
[OpenData DWD](https://opendata.dwd.de/weather/tree.html)

## External libraries
I use the wgrib2.exe and his library to read grib2 files.
Version: 3.1.3

[FTP-Server NOAA: wgrib2.exe + library](https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/Windows10/)

Information about wgrib2.exe:
[wgrib2: wgrib for GRIB-2](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/)

## Required Paython Packages
| Package      | Version      |
|--------------|--------------|
| basemap      | 1.4.0        |
| bs4          | 0.0.1        |
| cartopy      | 0.22.0       |
| colorama     | 0.4.6        |
| matplotlib   | 3.8.2        |
| numpy        | 1.26.2       |
| pandas       | 2.1.4        |  
| scipy        | 1.12.0       |
| statsmodels  | 0.14.1       |
| tqdm         | 4.66.1       |

## Used Paython Packages for development
| Package      | Version      | Description  |
|--------------|--------------|--------------|
| coverage     | 7.4.0        | Code coverage|
| mypy         | 1.7.1        | Static type tests|
| pyTest       | 7.4.3        | unit tests|
