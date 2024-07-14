from datetime import datetime, timezone


def convert_to_local_time(dt: datetime) -> datetime:
    """
    Converts a datetime object to the local time zone.

    Parameters
    ----------
    dt : datetime
        The datetime object to convert.

    Returns
    -------
    datetime
        The converted datetime object in the local time zone.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def is_english(s: str) -> bool:
    """
    Checks if a string contains only ASCII characters.

    Parameters
    ----------
    s : str
        The string to check.

    Returns
    -------
    bool
        True if the string contains only ASCII characters, False otherwise.
    """
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        return False
    return True
