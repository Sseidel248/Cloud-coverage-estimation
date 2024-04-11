"""
General Information:
______
- File name:      DWDStationReader.py
- Author:         Sebastian Seidel
- Date:           2024-04-10

Description:
______

"""
import os
import zipfile
import re

import Lib.GeneralFunctions as gFunc
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List
from pandas import DataFrame
from Lib.IOConsts import *
from tqdm import tqdm
from colorama import Fore, Style


class CorruptedInitFileError(Exception):
    """
    A custom exception to indicate that an initialization file is corrupted. This exception is raised when
    the initialization process encounters data that it cannot process due to errors in the file's format
    or content.
    """
    def __init__(self, message):
        super().__init__(message)


class DWDStations:
    """
    This class is used to read the txt files of the DWD stations.
    The TXT files were downloaded from the DWD FTP server. The following contents are read from the station files:
    All existing parameters, latitude, longitude, station altitude, station ID and time range (of the data recording)

    Attributes:
        df (DataFrame): contains all found and loaded txt files

    Functions:
        `get_values(...)`: is used to read out the parameter values for a specific latitude and longitude
    """
    def __init__(self):
        columns = [COL_STATION_ID, COL_DATE_START, COL_DATE_END, COL_STATION_HEIGHT, COL_LAT, COL_LON,
                   COL_DWD_FILENAME, COL_PARAM, COL_DWD_LOADED]
        datatypes = {
            COL_STATION_ID: "int",
            COL_DATE_START: "datetime64[s]",
            COL_DATE_END: "datetime64[s]",
            COL_STATION_HEIGHT: "float",
            COL_LAT: "float",
            COL_LON: "float",
            COL_DWD_FILENAME: "str",
            COL_PARAM: "str",
            COL_DWD_LOADED: "bool",
        }
        self.df: DataFrame = DataFrame(columns=columns).astype(datatypes)

    def load_folder(self, path: str):
        """
        Loads all DWD station data from text files located in a specified directory. This method performs several
        operations: it checks the existence of the directory, reads initialization files, extracts archives, and
        loads data from .txt files not marked as initialization files.

        :param path: A string representing the directory path from which to load the data.

        :raises FileNotFoundError: If the specified directory does not exist or contains no relevant .txt files.

        Note:
        The method assumes the presence of an 'init' file that must not be loaded with the regular station data.
        Each valid text file is processed to extract data, which is then sorted by station ID and parameter name.
        Progress through the files is visually tracked using a progress bar (tqdm), enhancing usability during large
        data loads.

        Example usage:

        `dwd_stations = DWDStations()`

        `dwd_stations.load_folder("/path/to/dwd/data")`
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Folder: '{path}' not exist.")
        self._read_init_files(path)
        extract_dwd_archives(path)
        dwd_txt_files = gFunc.get_files(path, ".txt")
        # nothing or only the init file
        if len(dwd_txt_files) <= 1:
            raise FileNotFoundError(f"No DWD *.txt Files exist in '{path}'")
        for dwd_txt in tqdm(dwd_txt_files, total=len(dwd_txt_files), desc="Loading DWD-Files"):
            if INIT_FILE_HOURLY_MARKER not in os.path.basename(dwd_txt):
                self._load_dwd_txt(dwd_txt)
        self.df.sort_values(by=[COL_STATION_ID, COL_PARAM], inplace=True)

    def get_values(self, date_times: datetime | List[datetime],
                   lat: float,
                   lon: float,
                   use_all_params: bool = True,
                   params: str | List[str] = None) -> DataFrame:
        """
         Retrieves weather data for specified date and time, latitude, and longitude, optionally filtered by
         weather parameters. If no specific parameters are defined, data for all available parameters can be
         retrieved based on the 'use_all_params' flag.

         :param date_times: A single datetime or a list of datetimes for which data is requested.
         :param lat: The latitude of the location.
         :param lon: The longitude of the location.
         :param use_all_params: Boolean flag to indicate whether data should be retrieved for all available parameters.
                                Defaults to True. If False, only specified 'params' are used.
         :param params: Optional single parameter or list of parameters to filter the data. If None and
                        'use_all_params' is False, no data is returned.

         :return: A pandas DataFrame containing the requested weather data, with each parameter as a column,
                  or an empty DataFrame if no data is available for the specified location or parameters.

         :raises FileNotFoundError: If data files for the specified parameters are not found.

         Note:
         This method first checks for the existence of the station at the given coordinates. It then prepares a
         DataFrame to collect results for the requested times and parameters. Data is loaded from corresponding
         files and merged into the result DataFrame. The method handles missing data gracefully, filling missing
         values where possible, and strips whitespace from parameter names to ensure accurate matching.
         """
        def conv_to_list(data):
            if not isinstance(data, list):
                data = [data]
            return data

        # perpare data
        date_times = conv_to_list(date_times)
        params = conv_to_list(params)
        lat: float = round(lat, 4)
        lon: float = round(lon, 4)
        # check if lat, lon exist and file is loaded
        if self.df.loc[(self.df[COL_LAT] == lat)
                       & (self.df[COL_LON] == lon)
                       & (self.df[COL_DWD_LOADED] == True)].empty:
            return pd.DataFrame()
        # write all used datetimes
        date_times = pd.DataFrame(date_times, columns=["Datetime"])
        # Init start structure
        result_df: DataFrame = pd.DataFrame()
        result_df[COL_DATE] = date_times["Datetime"].apply(gFunc.round_to_nearest_hour)
        result_df[COL_DATE] = date_times["Datetime"].apply(gFunc.datetime_to_strf)  # !!
        result_df[COL_STATION_ID] = self.df.loc[(self.df[COL_LAT] == lat)
                                                & (self.df[COL_LON] == lon), COL_STATION_ID].iloc[0]
        result_df[COL_STATION_HEIGHT] = self.df.loc[(self.df[COL_LAT] == lat)
                                                    & (self.df[COL_LON] == lon), COL_STATION_HEIGHT].iloc[0]
        result_df[COL_LAT] = lat
        result_df[COL_LON] = lon
        result_df[COL_STATION_HEIGHT] = np.nan
        # check if all params used or not. Ignore empty param
        if use_all_params or params is None:
            params = [param for param in self.df[COL_PARAM].unique().tolist() if param.strip()]
        # fill structure for each param
        for param in params:
            row: DataFrame = self.df.loc[(self.df[COL_LAT] == lat)
                                         & (self.df[COL_LON] == lon)
                                         & (self.df[COL_PARAM] == param)]
            if row.empty:
                continue
            filename: str = row[COL_DWD_FILENAME].iloc[0]
            height: float = float(row[COL_STATION_HEIGHT].iloc[0])
            if os.path.exists(filename):
                df_file = read_file_to_df(filename)
                matching_rows = df_file[df_file[COL_DATE].isin(result_df[COL_DATE])].copy()
                if not matching_rows.empty:
                    matching_rows[param] = matching_rows[param].str.strip()
                    result_df = result_df.merge(matching_rows[[COL_DATE, param]], on=COL_DATE, how='left')
                    result_df[COL_STATION_HEIGHT].fillna(height, inplace=True)
        # if eor columns exist, then remove it
        if "eor" in result_df.columns:
            result_df = result_df.drop(columns=["eor"])
        result_df.dropna(inplace=True)
        result_df[COL_DATE] = pd.to_datetime(result_df[COL_DATE], format="%Y%m%d%H")
        return result_df

    def get_station_locations(self) -> DataFrame:
        """
        Retrieves unique latitude and longitude coordinates for DWD (German Weather Service) stations from
        the class's DataFrame.

        :return: A pandas DataFrame containing columns for latitude (COL_LAT) and longitude (COL_LON) with
        each row representing a unique station location.

        Note:
        This method is particularly useful for plotting station locations on maps or for performing geospatial
        analyses that require knowledge of the geographical distribution of the stations. The returned DataFrame
        is filtered to ensure that each location is listed only once.
        """
        return self.df[[COL_LAT, COL_LON]].drop_duplicates()

    def _add_entry(self, datastr: str) -> bool:
        """
        Parses a data string to extract station information and either updates existing records or adds a new entry
        to the DataFrame. The data string is expected to contain station ID, start date, end date, station height,
        latitude, longitude, and additional information in a specified format.

        :param datastr: A string containing delimited data about a weather station.

        :return: A boolean indicating whether a new entry was added to the DataFrame. Returns True if a new entry
        is added, and False if an existing entry is updated.

        :raises ValueError: If the data string does not match the expected format, which could indicate a problem
                            with input data.

        Note:
        The function uses regular expressions to parse the data string. It checks for the station's presence in the
        DataFrame using the station ID. If the station exists, it updates the start and end dates if the new dates
        extend the current recording period. If the station does not exist, it adds a new row with the station's data.
        The method assumes the date format is 'YYYYMMDD' for both start and end dates.
        """
        match = re.search(r"(\d+) (\d+) (\d+)\s+(-?\d+)\s+([\d.]+)\s+([\d.]+)\s+(.*)", datastr)
        if match:
            station_id: int = int(match.group(1))
            if self.df[COL_STATION_ID].isin([station_id]).any():
                # compare start_date and end_date and apply it
                start_date = datetime.strptime(match.group(2), "%Y%m%d")
                end_date = datetime.strptime(match.group(3), "%Y%m%d")
                if start_date < self.df.loc[self.df[COL_STATION_ID] == station_id, COL_DATE_START].iloc[0]:
                    self.df.loc[self.df[COL_STATION_ID] == station_id, COL_DATE_START] = start_date
                if end_date > self.df.loc[self.df[COL_STATION_ID] == station_id, COL_DATE_END].iloc[0]:
                    self.df.loc[self.df[COL_STATION_ID] == station_id, COL_DATE_END] = end_date
                return False
            new_row = {
                COL_STATION_ID: station_id,
                COL_DATE_START: datetime.strptime(match.group(2), "%Y%m%d"),
                COL_DATE_END: datetime.strptime(match.group(3), "%Y%m%d"),
                COL_STATION_HEIGHT: int(match.group(4)),
                COL_LAT: float(match.group(5)),
                COL_LON: float(match.group(6)),
                COL_DWD_FILENAME: "",
                COL_PARAM: "",
                COL_DWD_LOADED: False,
            }
            self.df.loc[len(self.df)] = new_row
            return True
        else:
            return False

    def _load_dwd_txt(self, filename: str) -> bool:
        """
         Loads data from a DWD station text file specified by the filename into the DataFrame. This method reads
         station IDs and parameters from the file, checks if these exist in the DataFrame, and then updates or
         appends the data accordingly.

         :param filename: The path to the DWD station text file to be loaded.

         :return: A boolean indicating whether the file was successfully processed. Returns True if data from the file
                  was successfully added or updated in the DataFrame, and False if the station ID does not exist or no
                  parameters were read from the file.

         :raises FileNotFoundError: If the file does not exist or cannot be opened.
         :raises ValueError: If the file content does not match the expected format.

         Note:
         This method first reads the station ID and parameters from the file. It then checks if the station ID exists
         in the DataFrame. If it does, the method either updates the existing entry with new parameters and dates or
         adds new rows for additional parameters not previously recorded. If the station ID does not exist, it outputs
         a warning and returns False. This method ensures that all parameters and date ranges for each station are
         up-to-date according to the latest files processed.
         """
        a_id: int = _read_id(filename)
        params = _read_params(filename)
        if not params:
            return False

        row_index = self.df.index[self.df[COL_STATION_ID] == a_id].tolist()
        if not row_index:
            print(Fore.YELLOW +
                  f"\nStation ID '{a_id}' does not exist. Maybe the initialization file for the file "
                  f"'{filename}' was not loaded or the station ID does not exist in the initialization file."
                  + Style.RESET_ALL)
            return False

        start_date = _read_min_date(filename)
        end_date = _read_max_date(filename)

        # Check whether a parameter is already set for this StationId
        if self.df.at[row_index[0], COL_PARAM]:
            # If yes, copy the line for each additional parameter
            for param in params:
                new_row = self.df.loc[row_index[0]].copy()
                if self.df.loc[self.df[COL_STATION_ID] == a_id, COL_PARAM].isin([param]).any():
                    continue
                new_row[COL_PARAM] = param
                new_row[COL_DWD_FILENAME] = filename
                self.df.loc[len(self.df)] = new_row
        else:
            # If no, insert the first parameter in the existing line
            self.df.at[row_index[0], COL_PARAM] = params[0]
            # Set general information for the existing line
            self.df.loc[self.df[COL_STATION_ID] == a_id, [COL_DWD_LOADED, COL_DWD_FILENAME,
                                                          COL_DATE_START, COL_DATE_END]] = [True, filename,
                                                                                            start_date,
                                                                                            end_date]
            # For each additional parameter, add a new line
            for param in params[1:]:
                new_row = self.df.loc[row_index[0]].copy()
                new_row[COL_PARAM] = param
                self.df.loc[len(self.df)] = new_row
        return True

    def _read_init_files(self, path: str):
        """
        Reads initialization files containing station data from a specified directory. This method filters files that
        match defined markers indicating they are initialization files and then reads these files to populate the
        DataFrame with station data.

        :param path: The directory path that contains the initialization files.

        :raises FileNotFoundError: If no initialization files are found in the specified directory, or if the files do
                                  not contain the expected markers in their filenames.
        :raises CorruptedInitFileError: If the initialization files are found but contain no valid station data.

        Note:
        The function looks for files containing specific markers, 'INIT_FILE_HOURLY_MARKER' or 'INIT_FILE_10_MIN_MARKER'
        ,in their names to identify relevant initialization files. It reads through these files, ignoring headers, and
        processes each line to extract and add station data to the DataFrame using the `_add_entry` method. If after
        processing all files, the DataFrame remains empty, it indicates that the files were corrupted or improperly
        formatted.
        """
        files: list[str] = gFunc.get_files(path, ".txt")
        init_files: list[str] = []
        for a_file in files:
            if INIT_FILE_HOURLY_MARKER.lower() in str(a_file).lower():
                init_files.append(str(os.path.abspath(a_file)))
            elif INIT_FILE_10_MIN_MARKER.lower() in str(a_file).lower():
                init_files.append(str(os.path.abspath(a_file)))
        if not init_files:
            raise FileNotFoundError(f"DWD-Stations init file not exist in '{path}'. The file name must contain the "
                                    f"following: '[{INIT_FILE_HOURLY_MARKER}, {INIT_FILE_10_MIN_MARKER}]'")
        # Read the init File -> Content: all Ids of DWD Stations
        for init_file in init_files:
            with open(init_file, "r") as content:
                # Skip Header line
                content.readline()
                # Skip Splitter line
                content.readline()
                for line in content:
                    line = line.strip()
                    if line:
                        self._add_entry(line)
        if len(self.df) == 0:
            raise CorruptedInitFileError("Init file contains no information on DWD stations.")
        self.df.sort_values(by=COL_STATION_ID, inplace=True)


def _read_min_date(filename: str) -> datetime:
    """
    Reads the earliest date from a specified file. The function assumes the date is located on the second line
    of the file and is formatted in a specific way within that line.

    :param filename: The path to the file from which to read the date.

    :return: A datetime object representing the earliest date found in the file.

    :raises ValueError: If the date in the file does not conform to the expected format.
    :raises FileNotFoundError: If the file cannot be found or read.

    Note:
    This function is designed to read standard formatted DWD data files where the first line after the header
    contains date information. The date is expected to be in the format 'YYYYMMDDHH', and this function will
    handle date strings that may contain additional characters by truncating to the first 10 characters.
    """
    with open(filename, 'r') as content:
        # Skip Header line
        content.readline()
        first_line: str = content.readline().strip()
        date_str = first_line.split(";")[1]
        if len(date_str) > 10:
            date_str = date_str[:10]
        date: datetime = datetime.strptime(date_str, "%Y%m%d%H")
        return date


def _read_max_date(filename: str) -> datetime:
    """
    Reads the latest date from a specified file by searching backwards from the end of the file. It looks for the last
    line containing a date and returns it. This method is useful for files where new data is appended, ensuring the
    latest entry is found efficiently.

    :param filename: The path to the file from which to extract the latest date.

    :return: A datetime object representing the latest date found in the file. If no valid date is found,
             returns January 1, 1970, as a default value.

    :raises ValueError: If the last date in the file does not conform to the expected format.
    :raises FileNotFoundError: If the file cannot be found or read.

    Note:
    This function operates by reading the file from the end to the beginning, looking for the first occurrence
    of a newline character followed by a semicolon, indicating the presence of a date in 'YYYYMMDDHH' format.
    This method ensures efficient processing, particularly useful for large files. If no date is found, or if
    the date is improperly formatted, a default date is returned to avoid errors in the calling function.
    """
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
                    date_str = line[::-1].split(";")[1]
                    if len(date_str) > 10:
                        date_str = date_str[:10]
                    date: datetime = datetime.strptime(date_str, "%Y%m%d%H")
                    return date
                # reset temp var
                line = ''
            else:
                line += next_char.decode()
            position -= 1
    return datetime(1970, 1, 1)


def read_file_to_df(filename: str) -> DataFrame:
    """
    Reads a CSV file into a pandas DataFrame, cleans up the column headers by stripping any leading or trailing spaces,
    and sets appropriate column names for further processing.

    :param filename: The path to the CSV file to be read. The file is expected to be delimited by semicolons (';').

    :return: A pandas DataFrame containing the data from the CSV file with formatted column headers and initial
             data processing done for dates and station IDs.

    :raises FileNotFoundError: If the file specified does not exist.
    :raises pd.errors.ParserError: If there is an issue with CSV syntax during parsing.

    Note:
    The first row of the CSV file is expected to contain the headers, which are cleaned and used as DataFrame column
    names. Specific columns like 'MESS_DATUM' for date and 'STATIONS_ID' for station identifiers are renamed for
    consistency with further data handling conventions. Additionally, this function initially prepares to parse date
    columns, though the actual parsing may be commented out or handled later depending on data structure or needs.
    """
    df = pd.read_csv(filename, sep=';', header=None)
    # remove empty spaces in headers
    header = df.iloc[0].apply(lambda x: x.strip())
    df.columns = header
    df = df.drop(0)
    # parse datetime column
    df.rename(columns={"MESS_DATUM": COL_DATE, "STATIONS_ID": COL_STATION_ID}, inplace=True)
    # df[COL_DATE] = pd.to_datetime(df[COL_DATE], format="%Y%m%d%H")
    return df


def extract_dwd_archives(path: str):
    """
    Extracts specific data files from all ZIP archives found in a given directory. This function targets files that
    contain a designated marker in their names, indicating they are relevant DWD data files.

    :param path: The directory path where the ZIP files are located. The function searches for all ZIP files in this
                 directory and processes each one found.

    :raises FileNotFoundError: If the path specified does not contain any ZIP files.
    :raises zipfile.BadZipFile: If an archive cannot be opened because it is not a ZIP file or is corrupted.

    Note:
    The function iterates over all ZIP files in the specified directory, opening each one to check for data files
    marked as relevant (identified by `DATA_FILE_MARKER`). It extracts these files into the same directory as the
    ZIP file if they do not already exist there. This method helps manage data extracted from multiple sources by
    ensuring that only necessary files are unpacked, thus optimizing storage and processing time. The extraction
    process is tracked with a progress bar for better visibility and management of the operation.
    """
    # Collect all zip-files (dwd data-files)
    zip_files: list[str] = gFunc.get_files(path, ".zip")
    for zip_file in tqdm(zip_files, total=len(zip_files), desc="Extract DWD-Files"):
        # open zip file
        with zipfile.ZipFile(zip_file, 'r') as a_zip:
            directory: str = os.path.dirname(zip_file)
            # check if file to extract allready exist
            for name in a_zip.namelist():
                if DATA_FILE_MARKER.lower() in name.lower():
                    data_filename: str = os.path.join(os.path.abspath(directory), name)
                    if not os.path.exists(data_filename):
                        # extract data file and break inner loop
                        a_zip.extract(name, os.path.abspath(directory))
                        break


def _read_params(filename: str) -> List[str]:
    """
    Reads the header of a text file to extract parameter names. This function assumes the parameter names are
    located starting from the fourth column to the second last column in the header of the file.

    :param filename: The path to the file from which to read parameter names.

    :return: A list of strings where each string is a parameter name extracted from the file header. Returns an
             empty list if the file does not exist or the header is improperly formatted.

    :raises FileNotFoundError: If the file specified does not exist.

    Note:
    The function first checks if the file exists. If it does, it opens the file and reads the first line to
    parse out parameter names. The expected format is a semicolon-separated line where the first three columns
    are typically reserved for station ID, measurement date, and quality number, and the following columns up
    to the second last are parameter names. This setup is typical in data files used for meteorological or
    environmental data collection where parameters vary per file.
    """
    if not os.path.exists(filename):
        return []
    # Read the Textfile and get station id
    with open(filename, 'r') as content:
        header_line = content.readline()
        headers = header_line.split(";")
        if len(headers) < 4:
            return []
        # 1. STATIONS_ID, 2. MESS_DATUM, 3. QN_*
        # export 4. until n-1 column
        return [name.strip() for name in headers[3:-1]]


def _read_id(filename: str) -> int:
    """
    Extracts the station ID from the specified file. The station ID is expected to be located in the first column of
    the second line of the file. This function is typically used for files where the first line is a header and the
    second line begins with station data.

    :param filename: The path to the file from which to extract the station ID.

    :return: An integer representing the station ID, or -1 if the file does not exist, the second line does not
             contain data, or the first column of the second line cannot be converted to an integer.

    :raises FileNotFoundError: If the file specified does not exist.

    Note:
    This function checks the existence of the file, reads up to the second line, and attempts to parse the station ID
    from the first column. It uses a helper function `int_def` to ensure that non-integer values or parse errors do
    not cause a crash but instead return a default value of -1. This approach provides robustness against file read
    errors and formatting issues.
    """
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

# TODO: automatische Tets schreiben
# dwdv2 = DWDStations()
# dwdv2.load_folder("..\\DWD_Downloader\\WeatherStations\\")
# print(dwdv2.df[COL_DWD_PARAM].unique())
# print(dwdv2.df.head())
# print(dwdv2.df.columns)
# print(dwdv2.df .columns)
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, False, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, True, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, True))
# print(dwdv2.get_dwd_value(datetime(2023, 12, 24, 00), 52.9437, 12.8518, False))
# print(dwdv2.get_unloaded_stations())
# print(dwdv2.get_stations())
# print(dwdv2.get_stations((52.943, 53.95), (12.85, 12.86)))
# print(dwdv2.get_station(52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2022, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.datetime_in_range(datetime(2025, 6, 26, 00), 52.9437, 12.8518))
# print(dwdv2.get_station_locations())
# dates = [datetime(2022, 6, 26, 00, 15), datetime(2022, 6, 26, 00, 45)]
# print(dwdv2.get_dwd_multiple_values(dates, 52.9437, 12.8518, False, ["V_N", "abc"]))
# print(dwdv2.get_dwd_value(datetime(2022, 6, 26, 00, 45), 52.9437, 12.8518, False, ["V_N"]))
