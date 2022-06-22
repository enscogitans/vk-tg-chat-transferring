import datetime
from pathlib import PurePath

data_dir = PurePath("data")


def make_ts(hour, minute) -> datetime.datetime:
    """It is always March 15, but time changes"""
    return datetime.datetime(2022, 3, 15, hour, minute, tzinfo=datetime.timezone.utc)
