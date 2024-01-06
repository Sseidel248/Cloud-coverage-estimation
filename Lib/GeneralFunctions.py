"""
File name:      GeneralFunctions.py
Author:         Sebastian Seidel
Date:           2024-**-**
Description:
"""
import pathlib
from typing import List
from pathlib import Path
from datetime import datetime, timedelta


def get_files(look_up_path: str, extension: str) -> List[Path]:
    files = list(pathlib.Path(look_up_path).glob(f"**/*{extension}"))
    return files


def round_to_nearest_hour(date_time: datetime) -> datetime:
    rounded_date = date_time.replace(second=0, microsecond=0, minute=0)
    if date_time.minute >= 30:
        rounded_date += timedelta(hours=1)
    return rounded_date


def hours_difference(datetime1: datetime, datetime2: datetime) -> float:
    time_difference = datetime2 - datetime1
    return abs(time_difference.total_seconds() / 3600)


def int_def(text: str, default: int) -> int:
    try:
        return int(text)
    except ValueError:
        return default
