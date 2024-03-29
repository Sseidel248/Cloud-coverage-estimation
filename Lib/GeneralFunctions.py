"""
File name:      GeneralFunctions.py
Author:         Sebastian Seidel
Date:           2024-**-**
Description:
"""
import pathlib
import numpy as np
from typing import List
from pathlib import Path
from datetime import datetime, timedelta


def get_files(look_up_path: str, extension: str) -> List[str]:
    pathes: list[Path] = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    files: list[str] = [str(path) for path in pathes]
    return files


def round_to_nearest_hour(date_time):
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
        rounded_date = date_time_in_minutes - np.timedelta64(minutes, "m")
        return rounded_date.astype("datetime64[h]")
    else:
        raise TypeError("Unsupported type. Only datetime.datetime and numpy.datetime64 are supported.")


def datetime_to_strf(date_time: datetime) -> str:
    return date_time.strftime("%Y%m%d%H")


def hours_difference(datetime1: datetime, datetime2: datetime) -> float:
    time_difference: timedelta = datetime2 - datetime1
    return abs(time_difference.total_seconds() / 3600)


def int_def(text: str, default: int) -> int:
    try:
        return int(text)
    except ValueError:
        return default


def in_range(value: float | datetime, min_val: float | datetime, max_value: float | datetime) -> bool:
    return min_val <= value <= max_value


def convert_in_0_360(degree: float) -> float:
    if -180 <= degree <= 180:
        return degree if degree >= 0 else degree + 360
    else:
        normalized: float = degree % 360
        return normalized if normalized != 0 else 0


def convert_in_180_180(degree: float) -> float:
    while degree > 180:
        degree -= 360
    while degree < -180:
        degree += 360
    return degree
