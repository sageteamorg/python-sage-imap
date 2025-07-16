import hashlib
import logging
import mimetypes
import os
import re
import zipfile
from datetime import datetime, timezone
from email.header import decode_header
from email.utils import formatdate, parsedate_to_datetime
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, List, Optional, Union

from sage_imap.exceptions import (
    IMAPClientError,
    IMAPConfigurationError,
    IMAPEmptyFileError,
    IMAPInvalidEmailDateError,
)
from sage_imap.models.email import EmailIterator, EmailMessage

logger = logging.getLogger(__name__)

# Constants for validation
MAX_FILENAME_LENGTH = 255
MAX_SUBJECT_LENGTH = 998  # RFC 5322 limit
VALID_EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

# Common MIME types for attachments
COMMON_MIME_TYPES = {
    ".txt": "text/plain",
    ".html": "text/html",
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".zip": "application/zip",
    ".rar": "application/x-rar-compressed",
}


def convert_to_local_time(dt: datetime) -> datetime:
    """
    Converts a datetime object to the local time zone with enhanced validation.

    Parameters
    ----------
    dt : datetime
        The datetime object to convert.

    Returns
    -------
    datetime
        The converted datetime object in the local time zone.

    Raises
    ------
    IMAPInvalidEmailDateError
        If the datetime object is invalid or cannot be converted.
    """
    if not isinstance(dt, datetime):
        raise IMAPInvalidEmailDateError(f"Expected datetime object, got {type(dt)}")

    try:
        if dt.tzinfo is None:
            # Assume UTC if no timezone info
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone()
    except (ValueError, OverflowError) as e:
        raise IMAPInvalidEmailDateError(
            f"Failed to convert datetime to local time: {e}"
        )


def parse_email_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse email date string to datetime object with better error handling.

    Parameters
    ----------
    date_str : Optional[str]
        Email date string in various formats.

    Returns
    -------
    Optional[datetime]
        Parsed datetime object or None if parsing fails.

    Raises
    ------
    IMAPInvalidEmailDateError
        If the date string is invalid and cannot be parsed.
    """
    if not date_str:
        return None

    try:
        # Try standard email date parsing first
        return parsedate_to_datetime(date_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse email date '{date_str}': {e}")

        # Try alternative parsing methods
        date_formats = [
            "%a, %d %b %Y %H:%M:%S %z",
            "%d %b %Y %H:%M:%S %z",
            "%Y-%m-%d %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M:%S",
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        raise IMAPInvalidEmailDateError(f"Unable to parse date string: {date_str}")


def format_email_date(dt: datetime) -> str:
    """
    Format datetime object to email date string.

    Parameters
    ----------
    dt : datetime
        Datetime object to format.

    Returns
    -------
    str
        Formatted email date string.
    """
    if not isinstance(dt, datetime):
        raise IMAPInvalidEmailDateError(f"Expected datetime object, got {type(dt)}")

    return formatdate(dt.timestamp(), localtime=True)


def sanitize_filename(filename: str, max_length: int = MAX_FILENAME_LENGTH) -> str:
    """
    Sanitize filename to prevent security issues and ensure compatibility.

    Parameters
    ----------
    filename : str
        Original filename.
    max_length : int, optional
        Maximum filename length, by default MAX_FILENAME_LENGTH.

    Returns
    -------
    str
        Sanitized filename.
    """
    if not filename:
        return "untitled"

    # Remove path separators and dangerous characters
    filename = os.path.basename(filename)
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", filename)

    # Remove leading/trailing dots and spaces
    filename = filename.strip(". ")

    # Ensure filename is not empty after sanitization
    if not filename:
        filename = "untitled"

    # Truncate if too long, preserving extension
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext

    return filename


def validate_email_address(email: str) -> bool:
    """
    Validate email address format.

    Parameters
    ----------
    email : str
        Email address to validate.

    Returns
    -------
    bool
        True if email is valid, False otherwise.
    """
    if not email or not isinstance(email, str):
        return False

    # Basic regex validation
    if not VALID_EMAIL_REGEX.match(email):
        return False

    # Additional checks
    if len(email) > 254:  # RFC 5321 limit
        return False

    local, domain = email.rsplit("@", 1)
    if len(local) > 64:  # RFC 5321 limit
        return False

    return True


def normalize_subject(subject: str) -> str:
    """
    Normalize email subject by removing extra whitespace and limiting length.

    Parameters
    ----------
    subject : str
        Original subject.

    Returns
    -------
    str
        Normalized subject.
    """
    if not subject:
        return ""

    # Decode encoded headers
    try:
        decoded_parts = decode_header(subject)
        decoded_subject = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                if encoding:
                    decoded_subject += part.decode(encoding, errors="replace")
                else:
                    decoded_subject += part.decode("utf-8", errors="replace")
            else:
                decoded_subject += part

        subject = decoded_subject
    except Exception as e:
        logger.warning(f"Failed to decode subject header: {e}")

    # Normalize whitespace
    subject = re.sub(r"\s+", " ", subject).strip()

    # Limit length
    if len(subject) > MAX_SUBJECT_LENGTH:
        subject = subject[: MAX_SUBJECT_LENGTH - 3] + "..."

    return subject


def get_mime_type(filename: str) -> str:
    """
    Get MIME type for a file based on its extension.

    Parameters
    ----------
    filename : str
        Filename to get MIME type for.

    Returns
    -------
    str
        MIME type string.
    """
    if not filename:
        return "application/octet-stream"

    # Get extension
    _, ext = os.path.splitext(filename.lower())

    # Try common types first for better performance
    if ext in COMMON_MIME_TYPES:
        return COMMON_MIME_TYPES[ext]

    # Fall back to mimetypes module
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def calculate_file_hash(file_path: Path, algorithm: str = "md5") -> str:
    """
    Calculate hash of a file.

    Parameters
    ----------
    file_path : Path
        Path to the file.
    algorithm : str, optional
        Hash algorithm to use, by default 'md5'.

    Returns
    -------
    str
        Hexadecimal hash string.

    Raises
    ------
    IMAPEmptyFileError
        If the file is empty.
    FileNotFoundError
        If the file doesn't exist.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_path.stat().st_size == 0:
        raise IMAPEmptyFileError(f"File is empty: {file_path}")

    try:
        hash_obj = hashlib.new(algorithm)
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        raise IMAPClientError(f"Failed to calculate {algorithm} hash: {e}")


def calculate_content_hash(content: bytes, algorithm: str = "md5") -> str:
    """
    Calculate hash of content bytes.

    Parameters
    ----------
    content : bytes
        Content to hash.
    algorithm : str, optional
        Hash algorithm to use, by default 'md5'.

    Returns
    -------
    str
        Hexadecimal hash string.
    """
    if not content:
        raise IMAPEmptyFileError("Content is empty")

    try:
        hash_obj = hashlib.new(algorithm)
        hash_obj.update(content)
        return hash_obj.hexdigest()
    except Exception as e:
        raise IMAPClientError(f"Failed to calculate {algorithm} hash: {e}")


def read_eml_files_from_directory(
    directory_path: Path, recursive: bool = False, validate_emails: bool = True
) -> EmailIterator:
    """
    Reads all .eml files from the specified directory and returns an EmailIterator.

    Parameters
    ----------
    directory_path : Path
        Path to the directory containing .eml files.
    recursive : bool, optional
        Whether to search subdirectories recursively, by default False.
    validate_emails : bool, optional
        Whether to validate email content, by default True.

    Returns
    -------
    EmailIterator
        An iterator containing all the email messages read from the directory.

    Raises
    ------
    FileNotFoundError
        If the directory doesn't exist.
    IMAPEmptyFileError
        If no .eml files are found.
    """
    if not directory_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    if not directory_path.is_dir():
        raise IMAPConfigurationError(f"Path is not a directory: {directory_path}")

    email_list = []
    pattern = "**/*.eml" if recursive else "*.eml"

    try:
        eml_files = list(directory_path.glob(pattern))

        if not eml_files:
            raise IMAPEmptyFileError(
                f"No .eml files found in directory: {directory_path}"
            )

        for file_path in eml_files:
            try:
                email_message = EmailMessage.read_from_eml_file(file_path)

                if validate_emails and not email_message.message_id:
                    logger.warning(
                        f"Email file {file_path} has no message ID, skipping"
                    )
                    continue

                email_list.append(email_message)
            except Exception as e:
                logger.error(f"Failed to read email file {file_path}: {e}")
                if validate_emails:
                    raise
    except Exception as e:
        raise IMAPClientError(f"Failed to read emails from directory: {e}")

    if not email_list:
        raise IMAPEmptyFileError("No valid emails found in directory")

    logger.info(f"Successfully read {len(email_list)} emails from {directory_path}")
    return EmailIterator(email_list)


def read_eml_files_from_zip(
    zip_path: Path, validate_emails: bool = True, extract_nested_zips: bool = False
) -> EmailIterator:
    """
    Reads all .eml files from the specified zip file and returns an EmailIterator.

    Parameters
    ----------
    zip_path : Path
        Path to the zip file containing .eml files.
    validate_emails : bool, optional
        Whether to validate email content, by default True.
    extract_nested_zips : bool, optional
        Whether to extract nested zip files, by default False.

    Returns
    -------
    EmailIterator
        An iterator containing all the email messages read from the zip file.

    Raises
    ------
    FileNotFoundError
        If the zip file doesn't exist.
    IMAPEmptyFileError
        If no .eml files are found or zip is empty.
    """
    if not zip_path.exists():
        raise FileNotFoundError(f"Zip file not found: {zip_path}")

    if not zip_path.is_file():
        raise IMAPConfigurationError(f"Path is not a file: {zip_path}")

    if zip_path.suffix.lower() != ".zip":
        raise IMAPConfigurationError(f"File is not a zip file: {zip_path}")

    if zip_path.stat().st_size == 0:
        raise IMAPEmptyFileError(f"Zip file is empty: {zip_path}")

    email_list = []

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            eml_files = [f for f in zip_ref.namelist() if f.lower().endswith(".eml")]

            if not eml_files:
                raise IMAPEmptyFileError(f"No .eml files found in zip: {zip_path}")

            for filename in eml_files:
                try:
                    with zip_ref.open(filename) as eml_file:
                        eml_bytes = eml_file.read()

                        if not eml_bytes:
                            logger.warning(f"Empty file in zip: {filename}")
                            continue

                        email_message = EmailMessage.read_from_eml_bytes(eml_bytes)

                        if validate_emails and not email_message.message_id:
                            logger.warning(
                                f"Email file {filename} has no message ID, skipping"
                            )
                            continue

                        email_list.append(email_message)
                except Exception as e:
                    logger.error(f"Failed to read email file {filename} from zip: {e}")
                    if validate_emails:
                        raise

            # Handle nested zips if requested
            if extract_nested_zips:
                nested_zips = [
                    f for f in zip_ref.namelist() if f.lower().endswith(".zip")
                ]
                for nested_zip in nested_zips:
                    try:
                        with zip_ref.open(nested_zip) as nested_file:
                            nested_bytes = nested_file.read()
                            temp_path = Path(f"/tmp/{nested_zip}")
                            temp_path.parent.mkdir(exist_ok=True)

                            with open(temp_path, "wb") as temp_file:
                                temp_file.write(nested_bytes)

                            nested_emails = read_eml_files_from_zip(
                                temp_path, validate_emails, False
                            )
                            email_list.extend(nested_emails.to_list())

                            # Clean up temp file
                            temp_path.unlink(missing_ok=True)
                    except Exception as e:
                        logger.error(f"Failed to process nested zip {nested_zip}: {e}")

    except zipfile.BadZipFile:
        raise IMAPConfigurationError(f"Invalid zip file: {zip_path}")
    except Exception as e:
        raise IMAPClientError(f"Failed to read emails from zip: {e}")

    if not email_list:
        raise IMAPEmptyFileError("No valid emails found in zip file")

    logger.info(f"Successfully read {len(email_list)} emails from {zip_path}")
    return EmailIterator(email_list)


def is_english(s: str) -> bool:
    """
    Checks if a string contains only ASCII characters with better validation.

    Parameters
    ----------
    s : str
        The string to check.

    Returns
    -------
    bool
        True if the string contains only ASCII characters, False otherwise.
    """
    if not isinstance(s, str):
        return False

    if not s:
        return True  # Empty string is considered ASCII

    try:
        s.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def is_valid_message_id(message_id: str) -> bool:
    """
    Validate message ID format according to RFC 5322.

    Parameters
    ----------
    message_id : str
        Message ID to validate.

    Returns
    -------
    bool
        True if message ID is valid, False otherwise.
    """
    if not message_id or not isinstance(message_id, str):
        return False

    # Remove angle brackets if present
    message_id = message_id.strip("<>")

    # Basic format: local-part@domain
    if "@" not in message_id:
        return False

    try:
        local, domain = message_id.rsplit("@", 1)

        # Check local part
        if not local or len(local) > 64:
            return False

        # Check domain part
        if not domain or len(domain) > 253:
            return False

        # Domain should have at least one dot
        if "." not in domain:
            return False

        return True
    except ValueError:
        return False


@lru_cache(maxsize=128)
def get_file_extension(filename: str) -> str:
    """
    Get file extension with caching for performance.

    Parameters
    ----------
    filename : str
        Filename to get extension from.

    Returns
    -------
    str
        File extension including the dot, or empty string if no extension.
    """
    if not filename:
        return ""

    return os.path.splitext(filename.lower())[1]


def create_safe_directory(path: Path, mode: int = 0o755) -> Path:
    """
    Create directory safely with proper permissions.

    Parameters
    ----------
    path : Path
        Directory path to create.
    mode : int, optional
        Directory permissions, by default 0o755.

    Returns
    -------
    Path
        Created directory path.

    Raises
    ------
    IMAPConfigurationError
        If directory creation fails.
    """
    try:
        path.mkdir(parents=True, exist_ok=True, mode=mode)
        return path
    except Exception as e:
        raise IMAPConfigurationError(f"Failed to create directory {path}: {e}")


def format_bytes(size: int) -> str:
    """
    Format byte size in human-readable format.

    Parameters
    ----------
    size : int
        Size in bytes.

    Returns
    -------
    str
        Formatted size string.
    """
    if size < 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0

    return f"{size:.1f} PB"


def extract_email_domain(email: str) -> Optional[str]:
    """
    Extract domain from email address.

    Parameters
    ----------
    email : str
        Email address.

    Returns
    -------
    Optional[str]
        Domain part of email, or None if invalid.
    """
    if not email or "@" not in email:
        return None

    try:
        return email.split("@")[-1].lower()
    except (IndexError, AttributeError):
        return None


def batch_process(
    items: List[Any],
    batch_size: int = 100,
    processor: Callable[[List[Any]], Any] = None,
) -> List[Any]:
    """
    Process items in batches for better performance.

    Parameters
    ----------
    items : List[Any]
        Items to process.
    batch_size : int, optional
        Size of each batch, by default 100.
    processor : Callable[[List[Any]], Any], optional
        Function to process each batch, by default None.

    Returns
    -------
    List[Any]
        Processed results.
    """
    if not items:
        return []

    if batch_size <= 0:
        batch_size = len(items)

    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        if processor:
            result = processor(batch)
            if result is not None:
                results.extend(result if isinstance(result, list) else [result])
        else:
            results.extend(batch)

    return results


def merge_email_iterators(*iterators: EmailIterator) -> EmailIterator:
    """
    Merge multiple email iterators into one.

    Parameters
    ----------
    *iterators : EmailIterator
        Email iterators to merge.

    Returns
    -------
    EmailIterator
        Merged email iterator.
    """
    all_emails = []
    for iterator in iterators:
        if iterator:
            all_emails.extend(iterator.to_list())

    return EmailIterator(all_emails)


def deduplicate_emails(
    emails: EmailIterator, key_func: Optional[Callable[[EmailMessage], str]] = None
) -> EmailIterator:
    """
    Remove duplicate emails from iterator.

    Parameters
    ----------
    emails : EmailIterator
        Email iterator to deduplicate.
    key_func : Optional[Callable[[EmailMessage], str]], optional
        Function to generate deduplication key, by default uses message_id.

    Returns
    -------
    EmailIterator
        Deduplicated email iterator.
    """
    if key_func is None:
        key_func = lambda email: email.message_id

    seen = set()
    unique_emails = []

    for email in emails:
        key = key_func(email)
        if key not in seen:
            seen.add(key)
            unique_emails.append(email)

    return EmailIterator(unique_emails)


def validate_directory_path(path: Union[str, Path]) -> Path:
    """
    Validate and normalize directory path.

    Parameters
    ----------
    path : Union[str, Path]
        Directory path to validate.

    Returns
    -------
    Path
        Validated Path object.

    Raises
    ------
    IMAPConfigurationError
        If path is invalid.
    """
    if not path:
        raise IMAPConfigurationError("Directory path cannot be empty")

    path = Path(path)

    if path.exists() and not path.is_dir():
        raise IMAPConfigurationError(f"Path exists but is not a directory: {path}")

    return path


def safe_filename_from_subject(subject: str, max_length: int = 50) -> str:
    """
    Create safe filename from email subject.

    Parameters
    ----------
    subject : str
        Email subject.
    max_length : int, optional
        Maximum filename length, by default 50.

    Returns
    -------
    str
        Safe filename.
    """
    if not subject:
        return "untitled"

    # Remove common email prefixes
    subject = re.sub(r"^(re:|fwd?:|reply:)\s*", "", subject, flags=re.IGNORECASE)

    # Create safe filename
    filename = sanitize_filename(subject, max_length)

    # Ensure it's not empty
    if not filename or filename == "_":
        filename = "untitled"

    return filename
