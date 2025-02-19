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

## Step by Step
That there are twice as many DWD stations for the total degree of coverage as there are DWD stations for measuring radiation intensity.

<img src="https://github.com/user-attachments/assets/fb6e7276-5782-43b0-b441-ab7b4f2dda6e" alt="ScatPlt_Bedeckungsgrad_Strahlungsintensität" width="600" height="500" ><br>

This would allow the DWD stations that measure the total degree of coverage to be used to solve the problem. Unfortunately, the DWD stations are not evenly distributed across Germany. That's why I use the forecast data from the German Weather Service (DWD). The DWD has two relevant models, ICON-EU and ICON-D2. The following image shows the different resolutions. The resolution of the ICON-EU model is 6.5km and the resolution of the ICON-D2 model is 2.1km.

<img src="https://github.com/user-attachments/assets/e570c1f3-9286-4df0-a91f-c2535f1ab4e6" alt="ScatPlt_Cloud_Coverage_Compare_ICON-D2_ICON-EU" width="600" height="500"><img src="https://github.com/user-attachments/assets/79a1d456-5de8-473f-8636-968b9224ecd1" alt="ScatPlt_DWD_Station_Cloud_Coverage" width="350" height="250"><br>

To check the accuracy of the model, the measured values of the DWD stations were compared with the calculated values of the model. 

<img src="https://github.com/user-attachments/assets/e686d669-0857-4f14-a456-a53f1555195f" alt="VioPlt_MAE_Vergleich_ICON-D2_ICON-EU" width="600" height="500"><br>

The ICON-D2 model is used to solve my problem. This allows a very high resolution to be guaranteed. Additional parameters can also be downloaded from the DWD if required.

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
