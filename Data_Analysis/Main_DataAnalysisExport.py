"""
General Information:
______
- File name:      Main_DataAnalysisExport.py
- Author:         Sebastian Seidel
- Date:           2024.04.10

Description:
______
Used to evaluate the data read from the DWD (German Weather Service) and the weather models and then
post process the collected data. The corresponding data files are then generated.

"""
import os
import pickle
import numpy as np
import pandas as pd
from Lib.IOConsts import *
from Lib.Grib2Reader import Grib2Datas
from Lib.DWDStationReader import DWDStations
from pandas import DataFrame
from tqdm import tqdm
from datetime import datetime
from pathlib import Path


def is_file_in_use(filepath: str) -> bool:
    """
    Checks if the specified file is currently being used by another process.

    :param filepath: path of file.
    :return: True if the file is used, otherwise False.
    """
    if not os.path.exists(filepath):
        return False
    try:
        # Try to open the file in exclusive mode.
        with open(filepath, "r+", encoding='utf-8'):
            return False
    except IOError:
        return True


def get_unique_filename(filename: str) -> str:
    """
    Checks if a file name exists and increments it if it exists or is used.

    :param filename: The original file name
    :return: A unique file name
    """
    counter = 1
    name, extension = os.path.splitext(filename)
    while os.path.exists(filename) or is_file_in_use(filename):
        filename = f"{name}({counter}){extension}"
        counter += 1
    return filename


def combine_datas(dwd_datas: DWDStations,
                  model_datas: Grib2Datas,
                  model_str: str,
                  model_param: str,
                  use_all_params: bool,
                  dwd_param_list: list[str] = None) -> DataFrame:
    """
    Combines station data from DWD (Deutscher Wetterdienst) and model data, potentially filtering by specified
    parameters, and returns a merged DataFrame.

    This function first gathers location coordinates from DWD station data and model forecast dates. Depending on
    the `use_all_params` flag, it either uses a specified list of DWD parameters or all available parameters
    for data retrieval. It collects DWD data and model data for these coordinates and dates, merges the two datasets
    based on date, latitude, and longitude, and returns the merged DataFrame sorted by station ID and date.

    :param dwd_datas: An instance of DWDStations, which contains station data including locations.
    :param model_datas: An instance of Grib2Datas, which contains model forecast data.
    :param model_str: A string specifying the model to use for fetching model data.
    :param model_param: A string specifying the model parameter to fetch from the model data.
    :param use_all_params: A boolean flag indicating whether to use all parameters from DWD data for retrieval.
                           If True, `dwd_param_list` is ignored.
    :param dwd_param_list: (Optional) A list of strings specifying which parameters to retrieve from DWD data.
                           Ignored if `use_all_params` is True.

    :return: A pandas DataFrame merging DWD and model data, sorted by station ID and date, with 'eor' column removed
             if it exists.

    Note: The function assumes that `Date_UTC` and `Date_Fcst` columns in model data contain forecast datetimes
          and are identical, and it uses these along with latitude and longitude for merging datasets.
    """
    coords = dwd_datas.get_station_locations()
    coords_list = list(zip(coords[COL_LAT], coords[COL_LON]))
    model_dates = model_datas.df[COL_MODEL_FCST_DATE].tolist()

    if use_all_params:
        dwd_param_list = None

    temp_dfs = []
    for lat, lon in tqdm(coords_list, total=len(coords_list), desc="Processing DWD-Values"):
        temp_df = dwd_datas.get_values(model_dates, lat, lon, use_all_params, dwd_param_list)
        temp_dfs.append(temp_df)
    vals_dwd = pd.concat(temp_dfs, ignore_index=True)

    temp_dfs.clear()
    for date in tqdm(model_dates, total=len(model_dates), desc="Processing Model-Values"):
        temp_df = model_datas.get_values(model_str, model_param, date, coords_list)
        temp_dfs.append(temp_df)
    vals_model = pd.concat(temp_dfs, ignore_index=True)
    # vals_model Date_UTC and Date_Fcst are identical, because both contains forecast datetime
    vals_dwd.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    vals_model.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    # merge vals_model in vals_dwd
    merged_df = pd.merge(vals_dwd, vals_model, on=[COL_DATE, COL_LAT, COL_LON], how='left')
    merged_df.sort_values(by=[COL_STATION_ID, COL_DATE], inplace=True)

    # remove DWD's "eor" column if exist
    if "eor" in merged_df.columns:
        merged_df.drop(columns="eor", inplace=True)
    print("Evaluate Data - finished")
    return merged_df


def calculate_idw(model_datas: Grib2Datas,
                  data_df: DataFrame,
                  model_str: str,
                  model_param: str):
    """
    Calculates Inverse Distance Weighting (IDW) values for model data based on specified model parameters and
    integrates these calculations with an existing DataFrame containing station data.

    This function iterates over unique dates in the provided DataFrame, gathering model values using IDW based on
    the specified model parameters and the geographic coordinates of the stations. It then merges the IDW calculations
    with the original station data DataFrame, ensuring that the data is aligned based on date, latitude, and longitude.

    :param model_datas: An instance of Grib2Datas containing the model data to be used for IDW calculations.
    :param data_df: A pandas DataFrame containing station data, including columns for dates, station IDs, and
                    geographic coordinates (latitude and longitude).
    :param model_str: A string specifying the model to use for fetching IDW values.
    :param model_param: A string specifying the model parameter for which to calculate IDW values.

    :return: A pandas DataFrame that merges the original station data with the calculated IDW values from the
             model data. The DataFrame is sorted by date, latitude, and longitude, and includes only the relevant
             columns from the original and calculated IDW data.

    Note: This function assumes that the input DataFrame includes specific columns (e.g., station ID, latitude,
          longitude) and that it may contain additional columns that are dropped before merging with the IDW
          calculations. The function is designed to work with weather model data and geographic locations of
          weather stations.
    """
    model_dates = data_df[COL_DATE].unique().tolist()
    coords_df = data_df.drop_duplicates([COL_STATION_ID])[[COL_LAT, COL_LON]]
    coords_list = list(zip(coords_df[COL_LAT], coords_df[COL_LON]))
    temp_dfs = []
    for date in tqdm(model_dates, total=len(model_dates), desc="Processing IDW from Model-Values"):
        temp_df = model_datas.get_values_idw(model_str, model_param, date, coords_list, 0.04)
        temp_dfs.append(temp_df)
    idw_df = pd.concat(temp_dfs, ignore_index=True)
    # Create intersection set from both data frames
    data_df.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    data_df.drop([COL_STATION_HEIGHT, COL_MODEL_FCST_DATE, COL_MODEL_FCST_MIN, CLOUD_COVER],
                 axis=1,
                 inplace=True)
    idw_df.sort_values(by=[COL_DATE, COL_LAT, COL_LON], inplace=True)
    result_df = pd.merge(data_df, idw_df, on=[COL_DATE, COL_LAT, COL_LON], how="left")
    return result_df


def export_to_csv(df: DataFrame, filename: str):
    """
    Exports a given DataFrame to a CSV file, ensuring the filename is unique to avoid overwriting existing files.
    This function handles the export process with specific formatting rules: it uses a semicolon (';') as the separator,
    a comma (',') as the decimal point, and represents NaN values as the string 'nan'. These formatting choices are
    made to accommodate certain regional settings that might be in use where commas are used as decimal points, and
    semicolons are used as column separators.

    :param df: The pandas DataFrame to be exported.
    :param filename: A string representing the base name for the output file. This base name is passed to another
                     function to ensure the final output filename is unique.

    :return: None. The function writes the DataFrame to a CSV file with the specified formatting and does not return
             a value. The name of the file will be modified to ensure uniqueness if a file with the proposed name
             already exists.

    Note: The unique filename is generated by a separate function, `get_unique_filename`, which is not shown here but
          is assumed to append a unique identifier (like a timestamp or a numeric suffix) to the original filename if
          necessary.
    """
    unique_filename = get_unique_filename(filename)
    # some Nan are exported as "", that's why na_rep="nan"
    df.to_csv(unique_filename, sep=";", decimal=",", na_rep="nan", index=False)


def data_postprocessing(df: DataFrame) -> DataFrame:
    """
    Performs post-processing on a given DataFrame to clean and standardize the data. This includes converting
    specific known invalid or missing values to NaN, adjusting data types of columns according to a predefined
    mapping, trimming whitespace from string columns, and converting DWD cloud coverage values to percentages.

    Known invalid or missing values are defined as -999 for missing DWD data and 9.999e+20 for invalid ICON model
    values. These are replaced with NaN to standardize missing data representation.

    The function also converts the cloud coverage values (V_N) from a fraction of 8 (with -1 indicating fog as
    complete cloud coverage) to a percentage value. This conversion aids in consistent data analysis and visualization.

    :param df: The pandas DataFrame to be processed. It should contain the weather data with columns that might
               include specific values representing missing or invalid data, and cloud coverage in eighths.

    :return: A pandas DataFrame after applying the post-processing steps. This includes cleaning of data types,
             conversion of specific invalid or missing values to NaN, adjustment of cloud coverage to percentages,
             and trimming of whitespace in string columns.

    Note: The function expects a DataFrame with certain columns that may not be present in every dataset. It
          safely checks for the presence of these columns before attempting to apply any transformations.
    """
    # -999 - missing value dwd
    # 9.999e+20 - invalid value icon model
    conv_to_nan = [-999, 9.999e+20]

    col_type_dict = {
        "V_N": float,
        "V_N_I": str,
        "TT_TU": float,
        "RF_TU": float,
        "P": float,
        "P0": float,
        "F": float,
        "D": float
    }

    # Parse column types
    num_cols = []
    for col, _type in col_type_dict.items():
        if col in df.columns:
            df[col] = df[col].astype(_type)
            if pd.api.types.is_numeric_dtype(df[col]):
                num_cols.append(col)
            if pd.api.types.is_string_dtype(df[col]):
                df[col] = df[col].str.strip()

    # convert invalid Values to nan
    df.replace(conv_to_nan, np.nan, inplace=True)

    # convert dwd cloud coverage to [%]
    if "V_N" in df.columns:
        # convert -1 in V_N to 8/8 Cloud Coverage because it is fog
        df["V_N"].replace(-1, 8, inplace=True)
        # recalc in percentage [-] -> [%]
        df["V_N"] = df["V_N"] / 8 * 100

    return df


def create_coordinates_list(start_lat, end_lat, start_lon, end_lon, delta):
    """
    Creates a list of tuples with coordinates (Lat, Lon) that are incremented from a start value to a final value
    with a defined delta for latitude (Lat) and longitude (Lon).

    :param start_lat: Start value for latitude
    :param end_lat: End value for latitude
    :param start_lon: Start value for Longitude
    :param end_lon: Final value for longitude
    :param delta: Increment for longitude

    :return: List of tuples (Lon, Lat). Lon and Lat are rounded to the 4th decimal place
    """
    # Initialize the list for the coordinates
    coord_list = []

    # Generate the values for latitude and longitude within the specified ranges
    act_lat = start_lat
    while act_lat <= end_lat:
        act_lon = start_lon
        while act_lon <= end_lon:
            # Füge das aktuelle Tupel der Liste hinzu
            coord_list.append((act_lat, act_lon))
            act_lon += delta
        act_lat += delta

    # Round to 4th decimal place
    return [(round(lon, 4), round(lat, 4)) for lon, lat in coord_list]


def export_cloud_area_csv(dwd_datas: DWDStations,
                          model_datas: Grib2Datas,
                          start_lat: float,
                          end_lat: float,
                          start_lon: float,
                          end_lon: float,
                          delta: float,
                          exportname_dwd: str,
                          exportname_model: str):
    """
    Exports cloud area data to CSV files for both DWD station data and model data within specified geographical
    coordinates and for a specific calculation date. This function filters the station and model data based on
    the provided latitude and longitude boundaries, calculates cloud coverage values where applicable, and
    exports the processed data to CSV files.

    :param dwd_datas: An instance of DWDStations, containing DWD station data.
    :param model_datas: An instance of Grib2Datas, containing weather model data.
    :param start_lat: The starting latitude of the area for which to export data.
    :param end_lat: The ending latitude of the area for which to export data.
    :param start_lon: The starting longitude of the area for which to export data.
    :param end_lon: The ending longitude of the area for which to export data.
    :param delta: The step size for creating a grid of coordinates within the specified area for model data extraction.
    :param exportname_dwd: The filename for the exported CSV file containing DWD station data.
    :param exportname_model: The filename for the exported CSV file containing model data.

    Note: The function performs data post-processing on the DWD station data before exporting it, including
          converting cloud coverage values to percentages and handling missing values. It calculates cloud coverage for
          a fixed date (24th January 2024, 12:00 pm) and exports the results to the specified filenames.
    """
    print("Create Area Data...")
    calc_date = datetime(2024, 1, 24, 12)
    # get DWD-Locations and Values
    dwd_locs = dwd_datas.get_station_locations()
    dwd_area = dwd_locs[(dwd_locs[COL_LAT] >= start_lat) & (dwd_locs[COL_LAT] <= end_lat) &
                        (dwd_locs[COL_LON] >= start_lon) & (dwd_locs[COL_LON] <= end_lon)].copy()
    # init clou coverage values with Nan
    dwd_area["V_N"] = np.NaN
    for idx, row in dwd_area.iterrows():
        lat = row[COL_LAT]
        lon = row[COL_LON]
        tmp = dwd_datas.get_values(calc_date, lat, lon, False, "V_N")
        # override nan Value if cloud coverage value exist
        if "V_N" in tmp.columns:
            dwd_area.loc[idx, "V_N"] = float(tmp["V_N"].iloc[0])
    dwd_area.insert(0, COL_DATE, calc_date)
    dwd_area = data_postprocessing(dwd_area)
    export_to_csv(dwd_area, exportname_dwd)

    # create Modeldata for area
    view_area = create_coordinates_list(start_lat, end_lat, start_lon, end_lon, delta)
    temp_df = model_datas.get_values(model,
                                     param,
                                     calc_date,
                                     view_area)
    export_to_csv(temp_df, exportname_model)


def load_pkl(filename: str) -> DataFrame:
    """
    Loads a pandas DataFrame from a pickle file (*.pkl) located at the specified filename.

    This function checks the file extension to ensure it is a pickle file before attempting to load it. If the file
    is not a pickle file, a ValueError is raised with an informative message.

    :param filename: The path to the pickle file as a string. The file must have a .pkl extension.

    :return: A pandas DataFrame loaded from the pickle file.

    :raises ValueError: If the file extension is not .pkl, indicating the file format is not supported for loading
                        by this function.
    """
    filepath = Path(filename)
    if filepath.suffix == ".pkl":
        with open(filename, "rb") as file:
            return pickle.load(file)
    else:
        raise ValueError("Unsupported file extension. Only *.pkl are supported.")


model: str = MODEL_ICON_D2
param: str = CLOUD_COVER
dwd_path: str = "..\\DWD_Downloader\\WeatherStations\\"

if model == MODEL_ICON_D2:
    exportname: str = CSV_NAME_ICON_D2
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\icon-d2"
    model_delta: float = ICON_D2_LAT_LON_DELTA
elif model == MODEL_ICON_EU:
    exportname = CSV_NAME_ICON_EU
    grib2_path: str = "..\\DWD_Downloader\\WeatherData\\icon-eu"
    model_delta: float = ICON_EU_LAT_LON_DELTA
else:
    raise ValueError(f"Model: '{model}' not exist")

# init grib2 files
grib2_datas = Grib2Datas()
grib2_datas.load_folder(grib2_path)

# init dwd txt files
dwds = DWDStations()
dwds.load_folder(dwd_path)

# Export Solar-Stationlocations with filterfile
dwd_solar = DWDStations()
dwd_solar.load_folder(os.path.join(dwd_path, "solar"))
export_solar_dwd = dwd_solar.df[[COL_STATION_ID, COL_LAT, COL_LON]].drop_duplicates(COL_STATION_ID)
useful_solar_station = load_pkl(f".\\datas\\radiationStations.pkl")
filter_mask = export_solar_dwd[COL_STATION_ID].isin(useful_solar_station.iloc[:, 0])
export_solar_dwd = export_solar_dwd[filter_mask]
export_to_csv(export_solar_dwd, f".\\datas\\solar_DWD_Stationlocations.csv")

# combine dwd and grib2 datas
dwd_params = ["V_N", "V_N_I"]
export_df = combine_datas(dwds, grib2_datas, model, param, False, dwd_params)

# contains all params
export_all_param_df = combine_datas(dwds, grib2_datas, model, param, True)

# Postprocessing readed datas
export_df = data_postprocessing(export_df)
export_all_param_df = data_postprocessing(export_all_param_df)

# save export
export_to_csv(export_df, f".\\datas\\{exportname}")
export_to_csv(export_all_param_df, f".\\datas\\all_param_{exportname}")

# calculate IDW Values
if model == MODEL_ICON_D2:
    export_idw_df = calculate_idw(grib2_datas, export_df, model, param)
    export_to_csv(export_idw_df, f".\\datas\\idw_{exportname}")

# create example area for plot some clouds
export_cloud_area_csv(dwds, grib2_datas, 52.5, 54.5, 12.0, 14.0, model_delta,
                      f".\\datas\\DWD-Stations_in_Area_I_{model}.csv",
                      f".\\datas\\Area_I_{model}.csv")
export_cloud_area_csv(dwds, grib2_datas, 47.5, 49.5, 7.5, 9.5, model_delta,
                      f".\\datas\\DWD-Stations_in_Area_II_{model}.csv",
                      f".\\datas\\Area_II_{model}.csv")
