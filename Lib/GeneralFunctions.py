"""
General Information:
______
- File name:      GeneralFunctions.py
- Author:         Sebastian Seidel
- Date:           2024-04-10

Description:
______
Contains some helpful functions.

Functions in this module:
______
- `get_files`: Searches recursively for files with a specific extension
- `round_to_nearest_hour`: Rounds a given datetime object to the nearest hour
- `datetime_to_strf`: Converts a datetime object or a numpy.datetime64 object to a string
- `hours_difference`: Calculates the absolute difference in hours between two datetime objects.
- `int_def: Attempts` to convert a string to an integer. If the conversion fails it returns a default integer value.
- `convert_in_0_360`: Converts an angle in degrees to a value within the range [0, 360).
- `convert_in_180_180`: Normalizes an angle in degrees to fall within the range [-180, 180]
"""
import pathlib
import numpy as np
from typing import List
from pathlib import Path
from datetime import datetime, timedelta


def get_files(look_up_path: str, extension: str) -> List[str]:
    """
    Searches recursively for files with a specific extension in a given directory and returns a list of full file paths.

    :param look_up_path: The directory path where the search will begin. The search is recursive, so it will include all
           subdirectories.
    :param extension: The file extension to search for. Include the dot (e.g., '.txt') if it's part of the extension.

    :return: A list of strings, where each string is the full path to a file that matches the specified extension.

    Note:
    This function utilizes the `glob` method from the `pathlib` library to find files. It constructs a search
    pattern from the given extension and retrieves all matching files in the specified directory and its
    subdirectories.
    """
    pathes: list[Path] = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    files: list[str] = [str(path) for path in pathes]
    return files


def round_to_nearest_hour(date_time):
    """
    Rounds a given datetime object to the nearest hour. The function supports both Python's datetime.datetime and
    numpy.datetime64 types.

    :param date_time: The datetime object to round. Can be an instance of datetime.datetime or numpy.datetime64.

    :return: The rounded datetime, in the same type as the input. For datetime.datetime, it returns a datetime object
             with minutes, seconds, and microseconds set to zero, adjusted to the nearest hour. For numpy.datetime64,
             it returns a datetime64 object rounded to the nearest hour.

    :raises TypeError: If the input is neither a datetime.datetime nor a numpy.datetime64 object.

    Note:
    The rounding logic adjusts the datetime to the next hour if the minutes are 30 or more, otherwise it rounds
    down. This approach provides a standard method for rounding times across different types of datetime
    representations.
    """
    if isinstance(date_time, datetime):
        rounded_date = date_time.replace(second=0, microsecond=0, minute=0)
        if date_time.minute >= 30:
            rounded_date += timedelta(hours=1)
        return rounded_date
    elif isinstance(date_time, np.datetime64):
        date_time_in_minutes = date_time.astype("datetime64[m]")
        minutes = date_time_in_minutes.astype(int) % 60
        if minutes >= 30:
            date_time_in_minutes += np.timedelta64(60 - minutes, "m")
        else:
            date_time_in_minutes -= np.timedelta64(minutes, "m")
        # rounded_date = date_time_in_minutes - np.timedelta64(minutes, "m")
        return date_time_in_minutes.astype("datetime64[h]")
    else:
        raise TypeError("Unsupported type. Only datetime.datetime and numpy.datetime64 are supported.")


def datetime_to_strf(date_time) -> str:
    """
    Converts a datetime object or a numpy.datetime64 object to a string formatted as 'YYYYMMDDHH'. This function
    ensures compatibility across different datetime representations by converting numpy.datetime64 to datetime
    if necessary before formatting.

    :param date_time: The datetime to convert, which can be either a datetime.datetime or numpy.datetime64 object.

    :return: A string representing the formatted datetime.

    Note:
    The format '%Y%m%d%H' represents the year, month, day, and hour without any separators, which is useful
    for generating concise time labels or filenames. If the input is a numpy.datetime64 object, it is
    converted to datetime.datetime to utilize the strftime method for formatting.
    """
    if isinstance(date_time, np.datetime64):
        date_time = date_time.astype(datetime)
    return date_time.strftime("%Y%m%d%H")


def hours_difference(datetime1: datetime, datetime2: datetime) -> float:
    """
    Calculates the absolute difference in hours between two datetime objects.

    :param datetime1: The first datetime object.
    :param datetime2: The second datetime object.

    :return: The absolute difference between the two datetime objects measured in hours as a floating point number.

    Note:
    The function computes the difference in total seconds and then converts this value to hours. The absolute
    value is returned to ensure that the difference is always a positive number, regardless of the order
    of datetime1 and datetime2. This function is useful for measuring the time interval in terms of hours
    between two specific points in time.
    """
    time_difference: timedelta = datetime2 - datetime1
    return abs(time_difference.total_seconds() / 3600)


def int_def(text: str, default: int) -> int:
    """
    Attempts to convert a string to an integer. If the conversion fails due to a ValueError (i.e., the string
    is not a valid integer), it returns a default integer value.

    :param text: The string to convert to an integer.
    :param default: The default integer value to return if the conversion fails.

    :return: An integer, either the converted value of the string or the default value if the conversion is not
             possible.

    Note:
    This function is useful for parsing user input or data from external sources where integers are expected
    but not guaranteed. It provides a fail-safe method for integer conversion by returning a predetermined
    default value when conversion fails.
    """
    try:
        return int(text)
    except ValueError:
        return default


def convert_in_0_360(degree: float) -> float:
    """
    Converts an angle in degrees to a value within the range [0, 360). The function handles angles outside the
    standard geometric range by normalizing them to fit within these bounds.

    :param degree: The angle in degrees to be converted.

    :return: The angle normalized to the range [0, 360).

    Note:
    This function is particularly useful for geographic and navigational calculations where bearings or
    headings need to be expressed within a full 360-degree compass circle. If the input degree is negative
    or exceeds 360, it is correctly wrapped around to fit within the 0 to 360 degree range.
    """
    if -180 <= degree <= 180:
        return degree if degree >= 0 else degree + 360
    else:
        normalized: float = degree % 360
        return normalized if normalized != 0 else 0


def convert_in_180_180(degree: float) -> float:
    """
    Normalizes an angle in degrees to fall within the range [-180, 180]. This function continuously adjusts angles
    larger than 180 degrees or less than -180 degrees to ensure they fit within the standard navigational range.

    :param degree: The angle in degrees to be normalized.

    :return: The angle normalized to the range [-180, 180].

    Note:
    This normalization is common in applications involving directional data, such as navigation and GIS,
    where it's necessary to represent angles in a continuous circular format. The function adjusts degrees
    by wrapping them around the circle, so they always fall within the direct opposite bounds.
    """
    while degree > 180:
        degree -= 360
    while degree < -180:
        degree += 360
    return degree
