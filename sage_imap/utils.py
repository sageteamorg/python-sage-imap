import os
from pathlib import Path
import zipfile
from datetime import datetime, timezone
from sage_imap.helpers.email import EmailMessage, EmailIterator

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


def read_eml_files_from_directory(directory_path: Path) -> EmailIterator:
    """
    Reads all .eml files from the specified directory and returns an EmailIterator.

    Parameters
    ----------
    directory_path : str
        Path to the directory containing .eml files.

    Returns
    -------
    EmailIterator
        An iterator containing all the email messages read from the directory.
    """
    email_list = []
    for filename in os.listdir(directory_path):
        if filename.endswith(".eml"):
            file_path = os.path.join(directory_path, filename)
            email_message = EmailMessage.read_from_eml_file(file_path)
            email_list.append(email_message)
    return EmailIterator(email_list)


def read_eml_files_from_zip(zip_path: Path) -> EmailIterator:
    """
    Reads all .eml files from the specified zip file and returns an EmailIterator.

    Parameters
    ----------
    zip_path : Path
        Path to the zip file containing .eml files.

    Returns
    -------
    EmailIterator
        An iterator containing all the email messages read from the zip file.
        
    Raises
    ------
    ValueError
        If the specified path is not a zip file.
    """
    if not zip_path.is_file() or zip_path.suffix.lower() != '.zip':
        raise ValueError("The specified path is not a zip file.")
    
    email_list = []
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        for filename in zip_ref.namelist():
            if filename.endswith(".eml"):
                with zip_ref.open(filename) as eml_file:
                    eml_bytes = eml_file.read()
                    email_message = EmailMessage.read_from_eml_bytes(eml_bytes)
                    email_list.append(email_message)
    return EmailIterator(email_list)
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
