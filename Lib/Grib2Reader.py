"""
General Information:
______
- File name:      Grib2Reader.py
- Author:         Sebastian Seidel
- Date:           2024-04-10

Description:
______
Used to read certain parameters for a desired position (latitude and longitude) from grib2 files of
the DWD (German Weather Service).
"""

import re
import os
import bz2
import subprocess
import pandas as pd
import numpy as np
import Lib.GeneralFunctions as gFunc
from typing import List, Tuple
from numpy.typing import NDArray
from pandas import DataFrame
from datetime import datetime, timedelta
from Lib.IOConsts import *
from tqdm import tqdm

# wgrib2 file
_WGRIB2_EXE: str = f"{os.path.dirname(os.path.abspath(__file__))}\\wgrib2\\wgrib2.exe"


def split_coords(coords, n=1000):
    """Divide the coordinate list into sublists with n coordinates each."""
    for i in range(0, len(coords), n):
        yield coords[i:i + n]


class Grib2Datas:
    """
    This class is used to read Grib2 files.
    The Grib2 files come from the DWD. The values of the parameters can then be read out for loaded times
    and coordinates.

    Attributes:
        df (DataFrame): contains all successfully loaded Grib2 files
        df_models (DataFrame): contains all information on the corresponding models that were recognized during loading
        (currently only ICON-D2 and ICON-EU)
        df_invalid (DataFrame): contains all loaded files that have a forecast greater than 120 minutes

    Functions:
        `get_values(...)`: is used to read out the parameter values

        `get_values_idw(...)`: reads out surrounding values in addition to the desired value and calculates an inverse
        distance weighting
    """

    def __init__(self):
        cols = [COL_MODEL, COL_PARAM, COL_DATE, COL_MODEL_FCST_MIN, COL_MODEL_FCST_DATE, COL_MODEL_FILENAME]
        datatypes = {
            COL_MODEL: "str",
            COL_PARAM: "str",
            COL_DATE: "datetime64[s]",
            COL_MODEL_FCST_MIN: "int",
            COL_MODEL_FCST_DATE: "datetime64[s]",
            COL_MODEL_FILENAME: "str"
        }
        self.df: DataFrame = DataFrame(columns=cols).astype(datatypes)
        self.df_invalid: DataFrame = DataFrame(columns=cols).astype(datatypes)
        cols = [COL_MODEL, COL_PARAM, COL_MODEL_LAT_START, COL_MODEL_LAT_END, COL_MODEL_LON_START, COL_MODEL_LON_END,
                COL_MODEL_LATLON_DELTA]
        datatypes = {
            COL_MODEL: "str",
            COL_PARAM: "str",
            COL_MODEL_LAT_START: "float",
            COL_MODEL_LAT_END: "float",
            COL_MODEL_LON_START: "float",
            COL_MODEL_LON_END: "float",
            COL_MODEL_LATLON_DELTA: "float"
        }
        self.df_models: DataFrame = DataFrame(columns=cols).astype(datatypes)

    def load_folder(self, path: str):
        """
        Loads .grib2 files from a specified folder after extracting .bz2 archives within that folder. This method first
        checks if the folder exists and raises a FileNotFoundError if not. It then finds and extracts all .bz2 archives
        in the folder and subsequently loads all .grib2 files found. The method raises a FileNotFoundError if no .grib2
        files are found in the folder. Finally, it performs data validation and sorts the DataFrame by model and date.

        :param path: The path to the folder containing .bz2 archives and .grib2 files. It's checked for existence, and
        operations are performed within it.

        - The attributes `df` and `df_invalid` have the following columns at the end of the function

            - `COL_MODEL` (string): Contains the name for the loaded model
            - `COL_PARAM` (string): Contains the name for the parameter found in the Grib2 file
            - `COL_DATE` (datetime): Contains the start date of the Grib2 file
            - `COL_MODEL_FCST_MIN` (int): Contains the Forecast minutes
            - `COL_MODEL_FCST_DATE` (datetime): Contains the start date + forecast minutes
            - `COL_MODEL_FILENAME` (string): Contains the Path to the Grib2 file

        - The attributes `df_models` has the following columns at the end of the function

            - `COL_MODEL` (string): Contains the name for the loaded model
            - `COL_PARAM` (string): Contains the name for the parameter found in the Grib2 file
            - `COL_MODEL_LAT_START` (float): Contains the latitude at which the model starts [°]
            - `COL_MODEL_LAT_END` (float): Contains the latitude at which the model ends [°]
            - `COL_MODEL_LON_START` (float): Contains the longitude at which the model starts [°]
            - `COL_MODEL_LON_END` (float): Contains the longitude at which the model ends [°]
            - `COL_MODEL_LATLON_DELTA` (float): Contains the increment of the model [°]

        - The constants are located in `IOConst.py`

        Example usage:

        `grib2datas = Grib2Datas()`

        `grib2datas.load_folder("/path/to/grib2_files")`
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder: '{path}' not exist.")
        bz2_archives = gFunc.get_files(path, ".bz2")
        _extract_bz2_archives(bz2_archives)
        grib2_files = gFunc.get_files(path, ".grib2")
        if len(grib2_files) == 0:
            raise FileNotFoundError(f"No *.grib2 Files exist in '{path}'")
        for grib2 in tqdm(grib2_files, total=len(grib2_files), desc="Loading Grib2-Files"):
            self._load_file(os.path.abspath(grib2))
        self._date_validation()
        self.df = self.df.sort_values(by=[COL_MODEL, COL_DATE])

    def get_values(self,
                   model: str,
                   param: str,
                   date_times: datetime | List[datetime],
                   coords: Tuple[float, float] | List[Tuple[float, float]]) -> DataFrame:
        """
        Retrieves values for a specified model and parameter across given date-times and coordinates, handling both
        singular and multiple inputs for date-times and coordinates. It processes input arrays to ensure compatibility
        with the expected dimensions, performs validations, and executes a series of operations to fetch and compile
        the relevant data into a DataFrame.

        :param model: The model name as a string to filter the data.
        :param param: The parameter name as a string for which values are retrieved.
        :param date_times: A datetime object or a list of datetime objects specifying the date-times for which values
        are requested.
        :param coords: A tuple of floats representing a single coordinate pair (latitude, longitude) or a list of such
        tuples for multiple coordinates.

        :returns: A pandas DataFrame containing the fetched data, structured with columns for dates, forecast dates,
        forecast minutes, latitudes, longitudes, and the specified parameter values.

        :raise ValueError: if the dimensions of the input arrays are incompatible or if both date_times and coords have
        more than one dimension but not matching lengths.

        Note:

        The valid output DataFrame has the following columns:
            - `COL_DATE` (datetime): Contains the date searched for
            - `COL_MODEL_FCST_DATE` (datetime): Contains the date used, for the search the date of receipt was rounded to the full hour
            - `COL_MODEL_FCST_MIN` (Int): Contains the forecast minutes
            - `COL_LAT` (Float): Contains the latitude searched for
            - `COL_LON` (Float): Contains the longitude searched for
            - `<Param>` (Float): Contains the value of the parameter for the date and position searched for

        If there are datetimes that do not exist in the model data or incorrect coordinates are used, the entry is invalid.

        The invalid entry has the following values:
            - `COL_DATE` (datetime): Contains the date searched for
            - `COL_MODEL_FCST_DATE` (datetime): NaT (Not a Time)
            - `COL_MODEL_FCST_MIN` (float): NaN (Not a Number)
            - `COL_LAT` (Float): NaN (Not a Number)
            - `COL_LON` (Float): NaN (Not a Number)
            - `<Param>` (Float): NaN (Not a Number)

        The parameter `<Param>` changes depending on which parameter the grib2 file contains.
        """

        def get_width_len(arr: NDArray) -> Tuple[int, int]:
            # len(arr) == 1 then there is no second value
            if len(arr.shape) == 1:
                return arr.shape[0], 1
            else:
                return arr.shape[1], arr.shape[0]

        def conv_to_np(data, dtype: str):
            if not isinstance(data, list):
                data = [data]
            return np.array(data, dtype=dtype)

        np_date_times = conv_to_np(date_times, "datetime64[s]").reshape(-1, 1)
        np_coords = conv_to_np(coords, "float64")

        coords_width, coords_len = get_width_len(np_coords)
        date_times_width, date_times_len = get_width_len(np_date_times)

        if coords_width != 2:
            raise ValueError(f"The parameter 'coords' has an incorrect dimensioning. Shape must be (n, 2).")

        if date_times_len != coords_len:
            if date_times_len == 1:
                np_date_times = np.full((coords_len, 1), np_date_times[0])
            if coords_len == 1:
                np_coords = np.full((date_times_len, 2), np_coords)
            if date_times_len > 1 and coords_len > 1:
                raise ValueError(f"Only one parameter may have a length of 1. "
                                 f"Coords must be (n, 2) and 'date_times' must be (n, 1)")

        # Prepare vectorize functions - performance by numpy
        np_date_round_func = np.vectorize(gFunc.round_to_nearest_hour)
        np_date_times_series = pd.Series(np_date_times.flatten())
        # round Datetimes to nearst hour
        np_date_times = np_date_round_func(np_date_times)
        np_unique_datetimes = np.unique(np_date_times)
        # drop duplicates
        unique_date_times = np.unique(np_date_times)
        np_closest_grib2_date = np.vectorize(self._get_closest_date)
        # compare grib2 dates und date_times and collect closest dates to load the right file
        unique_date_times = np_closest_grib2_date(unique_date_times)
        np_conv_coords_func = np.vectorize(gFunc.convert_in_0_360)
        # convert the coordinate in range 0 to 360 degree
        np_coords = np_conv_coords_func(np_coords)
        # round to 8 decimals
        np_coords = np.round(np_coords, 8)

        # define the return DataFrame
        cols = [COL_DATE, COL_MODEL_FCST_DATE, COL_MODEL_FCST_MIN, COL_LAT, COL_LON, param]
        lat_values, lon_values, model_values, fcst_datetimes, fcst_min_values = [], [], [], [], []
        values: DataFrame = DataFrame(columns=cols)

        # define invalid index array - used to insert invalid values at the end
        invalid_indexes = []

        for used_date, input_date in zip(unique_date_times, np_unique_datetimes):
            # Search Entry
            founded_df = self.df[(self.df[COL_MODEL] == model) &
                                 (self.df[COL_PARAM] == param) &
                                 (self.df[COL_MODEL_FCST_DATE] == input_date)]
            if founded_df.empty:
                invalid_indexes += list(np.where(np_date_times == input_date)[0])
                continue
            filename = founded_df[COL_MODEL_FILENAME].iloc[0]
            fcst_min = founded_df[COL_MODEL_FCST_MIN].iloc[0]
            # get the index of date
            used_date_indexes = np.where(np_date_times == used_date)[0]
            used_coords = np_coords[used_date_indexes]

            # Divide coordinates into groups of 50 and execute commands
            res_list = []
            for coord_grp in split_coords(used_coords, 1000):
                # run cmd
                command = f"{_WGRIB2_EXE} {filename} -match {param}"
                for lat, lon in coord_grp:
                    command += f" -lon {lon} {lat}"
                result = subprocess.run(command, capture_output=True, text=True)
                res_list.append(result.stdout)
            # Evaluate result string
            matches = re.findall(r"val=(\d+\.?\d*(e\+20)?)", ''.join(res_list))

            for match, (lat, lon) in zip(matches, used_coords):
                value: float = -1
                if match[0] != "9.999e+20":
                    value = float(match[0])
                fcst_datetimes.append(used_date)
                lat_values.append(lat)
                lon_values.append(lon)
                model_values.append(value)
                fcst_min_values.append(fcst_min)

        # Add invalid values
        invalid_indexes.sort()
        for idx in invalid_indexes:
            fcst_datetimes.insert(idx, pd.NaT)
            fcst_min_values.insert(idx, np.nan)
            lat_values.insert(idx, np.nan)
            lon_values.insert(idx, np.nan)
            model_values.insert(idx, np.nan)

        # for Performance - fill DataFrame outside loop
        if len(lat_values) > 0:
            values = pd.DataFrame({COL_MODEL_FCST_DATE: fcst_datetimes,
                                   COL_DATE: np_date_times_series,
                                   COL_MODEL_FCST_MIN: fcst_min_values,
                                   COL_LAT: lat_values,
                                   COL_LON: lon_values,
                                   param: model_values
                                   }, columns=cols)
        return values

    def get_values_idw(self,
                       model: str,
                       param: str,
                       date_times: datetime | List[datetime],
                       coords: Tuple[float, float] | List[Tuple[float, float]],
                       radius: float = 0.04) -> DataFrame:
        """
        Retrieves interpolated values for a specified model and parameter at given date-times and coordinates using
        Inverse Distance Weighting (IDW). This method supports both single and multiple date-times and coordinates. It
        calculates interpolated values within a specified radius [°] around each coordinate, adjusting for the influence
        of nearby data points based on their distance.

        :param model: The model name as a string, used to filter the dataset.
        :param param: The parameter name as a string, indicating which values to retrieve and interpolate.
        :param date_times: A single datetime object or a list of datetime objects specifying the date-times for the
        interpolation.
        :param coords: A single tuple of (latitude, longitude) or a list of tuples for multiple coordinates where
        interpolation is desired.
        :param radius: A float specifying the radius around each coordinate to consider for the interpolation, with a
        default value of 0.04°.

        :returns: A pandas DataFrame with the interpolated values for the specified parameter at each provided
        coordinate and date-time. The DataFrame includes columns for dates, latitudes, longitudes, and the specified
        parameter.

        This method first expands the given coordinates to include nearby points within the specified radius and then
        retrieves the values for these points. It calculates the IDW interpolated value for each original coordinate
        based on the retrieved values and their distances. The resulting DataFrame contains the original date-times,
        coordinates, and interpolated parameter values.

        Note:

        The output DataFrame has the following columns:
            - `COL_DATE` (datetime): Contains the date searched for
            - `COL_MODEL_FCST_DATE` (datetime): Contains the date used, for the search the date of receipt was rounded
              to the full hour
            - `COL_MODEL_FCST_MIN` (Int): Contains the forecast minutes
            - `COL_LAT` (Float): Contains the latitude searched for
            - `COL_LON` (Float): Contains the longitude searched for
            - `<Param>` (Float): Contains the value of the parameter calculated with the inverse distance weighting (IDW)
              for the date searched for and the specified position within a certain radius.

        :raises ValueError: If input dimensions or types are not as expected, or if any other input validations fail.
        """

        def idw(group, dist_col, value_col, q=1):
            # Avoid division by zero
            group[dist_col] = np.where(group[dist_col] == 0, group[dist_col] + 1e-10, group[dist_col])
            d = group[dist_col]
            vals = group[value_col]
            # Calculation of weighting
            weighted_sum = np.sum(vals / d ** q)
            weights_sum = np.sum(1 / d ** q)
            # return idw values
            return weighted_sum / weights_sum

        if model == MODEL_ICON_D2:
            delta = 0.02
        elif model == MODEL_ICON_EU:
            delta = 0.0625
        else:
            delta = 0.02

        if not isinstance(coords, list):
            coords = [coords]

        idw_coords = []
        idw_distances = []
        for lat, lon in coords:
            area, distances = _create_coords_in_radius(lat, lon, radius, delta)
            idw_coords += area
            idw_distances += distances
        # Calculate all param values
        values = self.get_values(model, param, date_times, idw_coords)
        column_to_check = [COL_MODEL_FCST_DATE, COL_MODEL_FCST_MIN, COL_LAT, COL_LON, param]
        # first all() check all column, second all() check this for all rows
        if values[column_to_check].isna().all().all():
            return values
        # get number of each idw points
        num_same_idw_calc = len(_create_coords_in_radius(1, 1, radius, delta)[0])
        # Calculate idw distance and idw values
        values["idw_id"] = values.index // num_same_idw_calc
        values["distances"] = idw_distances
        idw_values = values.groupby("idw_id").apply(idw, dist_col="distances", value_col=param)
        # Assignment of values
        values.drop_duplicates(subset="idw_id", inplace=True)
        lats, lons = [], []
        for lat, lon in coords:
            lats.append(lat)
            lons.append(lon)
        values[COL_LAT] = lats
        values[COL_LON] = lons
        if len(idw_values.values) == 0:
            values[param] = -1
        else:
            values[param] = idw_values.values
        # drop temporary cols
        values.reset_index(drop=True, inplace=True)
        values.drop(["idw_id", "distances"], axis=1, inplace=True)
        return values

    def _get_closest_date(self, date_time: datetime) -> datetime:
        """
        Finds and returns the date-time in the dataframe closest to the specified date-time.

        This internal method calculates the absolute difference between each forecast date-time in the dataframe and
        the specified date-time. It then identifies the index of the minimum difference, which corresponds to the
        closest forecast date-time, and returns this date-time.

        :param date_time: The reference datetime object for which the closest date-time in the dataframe is to be found.

        :return: A datetime object representing the closest forecast date-time to the specified date_time in the
        dataframe.

        Note:
        This method assumes that the dataframe has a column named as per the global variable
        'COL_MODEL_FCST_DATE' that contains datetime objects.
        """
        differences = (self.df[COL_MODEL_FCST_DATE] - date_time).abs()
        # Find the index of the nearest date
        closest_date_index = differences.idxmin()
        # Return the Entry in Column COL_MODEL_FCST_DATE at Rowindex = closest_date_index
        return self.df.loc[closest_date_index, COL_MODEL_FCST_DATE]

    def _date_validation(self):
        """
        Performs validation checks on the dataframe by filtering out entries with forecast minutes greater than 120.

        This internal method separates invalid entries from the main dataframe into a separate dataframe (`df_invalid`)
        based on the condition that the forecast minutes (`COL_MODEL_FCST_MIN`) exceed 120 minutes. It then updates the
        main dataframe to only include valid entries. Additionally, it removes duplicate entries from the `df_models`
        dataframe.

        Effects:
        - Populates `self.df_invalid` with entries from `self.df` where forecast minutes are greater than 120.
        - Updates `self.df` to only include entries where forecast minutes are 120 or less.
        - Removes duplicate entries from `self.df_models`.

        Note:
        This method directly modifies the class attributes `self.df`, `self.df_invalid`, and `self.df_models`
        based on the specified validation criteria.
        """
        self.df_invalid = self.df[self.df[COL_MODEL_FCST_MIN] > 120]
        self.df = self.df[self.df[COL_MODEL_FCST_MIN] <= 120]
        self.df_models = self.df_models.drop_duplicates()

    def _load_file(self, filename: str):
        """
        Processes a single weather forecast file, extracting and storing relevant forecast data.

        This internal method executes a command using the wgrib2 tool to read data from a given weather forecast file
        (typically .grib2 format). It parses the command's output to extract forecast data, including dates, forecast
        minutes, model parameters, and coordinates. The extracted data is then added as a new row to the class's main
        dataframe and the model-specific dataframe.

        :param filename: The path to the .grib2 file to be processed.

        - Extracts forecast information from the file, including the forecast model, date, forecast minutes,
          and geographic coordinates
        - Adds a new row with the extracted data to both `self.df` and `self.df_models` dataframes

        Note:
        This method assumes the presence of a predefined pattern (PATTERN) to parse the command output and relies
        on the wgrib2 command-line tool. The method updates class dataframes directly, adding new entries for each
        processed file.
        """

        command: str = f"{_WGRIB2_EXE} {filename} -s -grid"
        result = subprocess.run(command, capture_output=True, text=True)
        if LAT_LON in result.stdout:
            match = re.search(MODEL_PATTERN, result.stdout)
            if match:
                # index 0 = full match of complete string
                date: datetime = datetime.strptime(match.group(1), "%Y%m%d%H")
                # if not found, then None
                submatch = re.search(r":(\d+) min fcst::", result.stdout)
                if submatch:
                    fcst_minutes = int(submatch.group(1))
                    fcst_date = date + timedelta(minutes=fcst_minutes)
                else:
                    fcst_minutes = 0
                    fcst_date = date
                new_row = {
                    COL_MODEL: _get_model(float(match.group(5))),
                    COL_DATE: date,
                    COL_MODEL_FCST_MIN: fcst_minutes,
                    COL_MODEL_FCST_DATE: fcst_date,
                    COL_PARAM: match.group(2),
                    COL_MODEL_LAT_START: gFunc.convert_in_180_180(float(match.group(3))),
                    COL_MODEL_LAT_END: gFunc.convert_in_180_180(float(match.group(4))),
                    COL_MODEL_LATLON_DELTA: float(match.group(5)),
                    COL_MODEL_LON_START: gFunc.convert_in_180_180(float(match.group(6))),
                    COL_MODEL_LON_END: gFunc.convert_in_180_180(float(match.group(7))),
                    COL_MODEL_FILENAME: filename
                }
                # Fill the DataFrames according to the column definition of the init function.
                self.df.loc[len(self.df)] = new_row
                self.df_models.loc[len(self.df_models)] = new_row


def _create_coords_in_radius(lat: float,
                             lon: float,
                             radius: float = 0.04,
                             delta: float = 0.02) -> (List[Tuple[float, float]], List[float]):
    """
    Generates a list of coordinate points and their distances from a central point, all within a specified radius.

    This internal method calculates a grid of coordinates around a given central point (latitude and longitude). The
    grid is defined within a circle of a specified radius around the central point. Each point in the grid is spaced
    at a specified delta distance apart, both in latitude and longitude directions. The method returns two lists: one
    containing the coordinates of the points within the radius, and another containing the squared distances of these
    points from the central point.

    :param lat: The latitude of the central point.
    :param lon: The longitude of the central point.
    :param radius: The radius around the central point within which to generate points. Defaults to 0.04°.
    :param delta: The distance between adjacent points in the grid. Defaults to 0.02°.

    :return: A tuple containing two elements:
             - A list of tuples, each representing the latitude and longitude of a point within the specified radius.
             - A list of floats, each representing the squared distance of the corresponding point from the central
               point.

    Note:
    The distances are distances, calculated as sqrt((Δlat)^2 + (Δlon)^2), and are rounded to 6 decimal places.
    """
    points = []
    distances = []
    steps = int(radius / delta)
    for i in range(-steps, steps + 1):
        for j in range(-steps, steps + 1):
            new_lat = lat + i * delta
            new_lon = lon + j * delta
            distance = round(np.sqrt((new_lat - lat) ** 2 + (new_lon - lon) ** 2), 6)
            if distance <= radius:
                points.append((new_lat, new_lon))
                distances.append(distance)
    return points, distances


def _get_model(delta: float) -> str:
    """
    Determines the weather forecast model based on the specified delta value.

    This internal method maps a given delta (grid spacing) to a specific weather forecast model. The delta is a
    floating-point number representing the spatial resolution of the model's data. Depending on the delta value, the
    method assigns a corresponding model name or defaults to a predefined unknown model.

    :param delta: The delta value representing the grid spacing of the weather model.
    :return: A string representing the model name based on the delta value.

    Note:
    The method currently supports specific delta values for predefined models. Other delta values will default
    to a known 'unknown' model identifier.
    """
    if delta == 0.02:
        return MODEL_ICON_D2
    elif delta == 0.0625:
        return MODEL_ICON_EU
    else:
        return MODEL_UNKNOWN


def _extract_bz2_archives(bz2_archives: List[str]):
    """
    Extracts files from a list of .bz2 archives.

    This method iterates over a list of .bz2 archive paths, extracting the contents of each archive to the same
    directory as the archive itself. If the extracted file already exists, the method skips the extraction for that
    archive. This process is used for preparing the data for further processing.

    :param bz2_archives: A list of strings, where each string is a file path to a .bz2 archive that needs to be
    extracted.

    :return: None. The method performs file extraction side effects but does not return any value.

    Note:
    This method checks for the existence of the extracted file before attempting extraction to avoid redundant
    operations.
    """
    # If there are no archives, then nothing needs to be unpacked
    if len(bz2_archives) == 0:
        return
    # Loop through each *.bz2 archive and unpack it
    for archive in tqdm(bz2_archives, total=len(bz2_archives), desc="Extract Bz2-Files"):
        directory: str = os.path.dirname(archive)
        filename_body: str = os.path.splitext(os.path.basename(archive))[0]
        extracted_path: str = os.path.join(directory, filename_body)
        if not os.path.exists(extracted_path):
            with open(extracted_path, "wb") as extracted_file, bz2.BZ2File(archive, "rb") as archiv:
                for content in archiv:
                    extracted_file.write(content)
