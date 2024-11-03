# Master Thesis 
## Cloud coverage estimation
This project is part of my master's thesis in the field of "Driver behavior monitoring for energy optimization and accident prevention" at the Technical University of Berlin. It deals with identification of the percentage of cloud cover at a location at a specific point in time.

I mainly worked with data from the DWD (German Weather Service).
[OpenData DWD](https://opendata.dwd.de/weather/tree.html)

## Abstract
The purpose of this master's thesis is to select an existing data source for determining cloud cover that has a high level of accuracy. The weather station data of the German Weather Service (DWD) serve as reference data. 
The various data sources are compared with each other in order to select the best data source. This choosen data source is concerning to its accuracy. The existing outliers in the data are then analyzed in more detail. It is checked whether there is a correlation between the outliers and other meteorological parameters in order to identify the cause of the outliers. 
Finally, an attempt is made to further increase the accuracy using a spatial interpolation method. The result is then compared with the data from the selected data source and evaluated. 

## Data sources
- DWD - weather station data
- ICON-D2 model data
- ICON-EU model data

## External libraries
I use the wgrib2.exe and his library to read grib2 files.
Version: 3.1.3

[FTP-Server NOAA: wgrib2.exe + library](https://ftp.cpc.ncep.noaa.gov/wd51we/wgrib2/Windows10/)

Information about wgrib2.exe:
[wgrib2: wgrib for GRIB-2](https://www.cpc.ncep.noaa.gov/products/wesley/wgrib2/)

## Required Paython Packages
| Package      | Version      | Description  
|--------------|--------------|--------------
| basemap      | 1.4.0        | Displaying the topography in the graphics
| bs4          | 0.0.1        | HTML parser
| cartopy      | 0.22.0       | Geographic visualization for graphics
| colorama     | 0.4.6        | Colored print() outputs
| matplotlib   | 3.8.2        | Graphic and diagram generation
| numpy        | 1.26.2       | Vector and matrix calculations
| pandas       | 2.1.4        | Importing, editing and saving tables as CSV files (high-performance data storage)
| requests     | 2.31.0       | Data request to Internet pages
| scipy        | 1.12.0       | Data analysis functions
| statsmodels  | 0.14.1       | QQ-Plot
| tqdm         | 4.66.1       | Progress bar for for-loops

## Used Paython Packages for development
| Package      | Version      | Description  
|--------------|--------------|--------------
| coverage     | 7.4.0        | Code coverage
| mypy         | 1.7.1        | Static type tests
| pyTest       | 7.4.3        | unit tests
