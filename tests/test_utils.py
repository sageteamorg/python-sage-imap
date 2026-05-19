"""Tests for sage_imap.utils."""

import zipfile
from datetime import datetime, timezone

import pytest

from sage_imap.exceptions import (
    IMAPClientError,
    IMAPConfigurationError,
    IMAPEmptyFileError,
    IMAPInvalidEmailDateError,
)
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.utils import (
    batch_process,
    calculate_content_hash,
    calculate_file_hash,
    convert_to_local_time,
    create_safe_directory,
    deduplicate_emails,
    extract_email_domain,
    format_bytes,
    format_email_date,
    get_file_extension,
    get_mime_type,
    is_english,
    is_valid_message_id,
    merge_email_iterators,
    normalize_subject,
    parse_email_date,
    read_eml_files_from_directory,
    read_eml_files_from_zip,
    safe_filename_from_subject,
    sanitize_filename,
    validate_directory_path,
    validate_email_address,
)

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Hi
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <id@example.com>
Content-Type: text/plain

Body
"""


def test_convert_to_local_time_naive_and_aware():
    naive = datetime(2020, 1, 1, 12, 0, 0)
    assert convert_to_local_time(naive).tzinfo is not None
    aware = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert convert_to_local_time(aware).tzinfo is not None


def test_convert_to_local_time_invalid_type():
    with pytest.raises(IMAPInvalidEmailDateError):
        convert_to_local_time("not-a-date")  # type: ignore[arg-type]


def test_parse_email_date_none_and_valid():
    assert parse_email_date(None) is None
    dt = parse_email_date("Wed, 12 Oct 2022 14:30:00 +0000")
    assert dt is not None


def test_parse_email_date_alternative_format():
    dt = parse_email_date("2022-10-12 14:30:00")
    assert dt.year == 2022


def test_parse_email_date_invalid():
    with pytest.raises(IMAPInvalidEmailDateError):
        parse_email_date("not a date at all xyz")


def test_format_email_date():
    dt = datetime(2022, 10, 12, 14, 30, 0, tzinfo=timezone.utc)
    assert isinstance(format_email_date(dt), str)


def test_format_email_date_invalid():
    with pytest.raises(IMAPInvalidEmailDateError):
        format_email_date("x")  # type: ignore[arg-type]


def test_sanitize_filename():
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("../../evil.txt") == "evil.txt"
    assert sanitize_filename("   ") == "untitled"
    long_name = "a" * 300 + ".txt"
    assert len(sanitize_filename(long_name)) <= 255


def test_validate_email_address():
    assert validate_email_address("user@example.com") is True
    assert validate_email_address("bad") is False
    assert validate_email_address("") is False
    assert validate_email_address("x" * 300 + "@example.com") is False


def test_normalize_subject_empty_and_encoded():
    assert normalize_subject("") == ""
    encoded = "=?utf-8?B?SGk=?="
    assert normalize_subject(encoded)
    long_subj = "x" * 1100
    assert len(normalize_subject(long_subj)) <= 998


def test_get_mime_type():
    assert get_mime_type("") == "application/octet-stream"
    assert get_mime_type("file.pdf") == "application/pdf"
    assert get_mime_type("unknown.zzzzzzz") == "application/octet-stream"


def test_calculate_hashes(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"hello")
    assert calculate_file_hash(f) == calculate_content_hash(b"hello")
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    with pytest.raises(IMAPEmptyFileError):
        calculate_file_hash(empty)
    with pytest.raises(IMAPEmptyFileError):
        calculate_content_hash(b"")
    with pytest.raises(FileNotFoundError):
        calculate_file_hash(tmp_path / "missing.bin")


def test_calculate_file_hash_failure(mocker, tmp_path):
    f = tmp_path / "x.bin"
    f.write_bytes(b"x")
    mocker.patch("hashlib.new", side_effect=ValueError("bad algo"))
    with pytest.raises(IMAPClientError):
        calculate_file_hash(f, algorithm="bad")


def test_read_eml_from_directory(tmp_path):
    d = tmp_path / "emails"
    d.mkdir()
    (d / "a.eml").write_bytes(SAMPLE_EML)
    it = read_eml_files_from_directory(d)
    assert len(list(it)) == 1


def test_read_eml_directory_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_eml_files_from_directory(tmp_path / "nope")
    f = tmp_path / "file.txt"
    f.write_text("x")
    with pytest.raises(IMAPConfigurationError):
        read_eml_files_from_directory(f)
    empty = tmp_path / "empty"
    empty.mkdir()
    with pytest.raises(IMAPClientError):
        read_eml_files_from_directory(empty)


def test_read_eml_from_zip(tmp_path):
    zpath = tmp_path / "mails.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("a.eml", SAMPLE_EML)
    it = read_eml_files_from_zip(zpath)
    assert len(list(it)) == 1


def test_read_eml_zip_errors(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_eml_files_from_zip(tmp_path / "nope.zip")
    d = tmp_path / "dir"
    d.mkdir()
    with pytest.raises(IMAPConfigurationError):
        read_eml_files_from_zip(d)
    bad = tmp_path / "bad.txt"
    bad.write_text("x")
    with pytest.raises(IMAPConfigurationError):
        read_eml_files_from_zip(bad)
    empty_zip = tmp_path / "empty.zip"
    with zipfile.ZipFile(empty_zip, "w"):
        pass
    with pytest.raises(IMAPClientError):
        read_eml_files_from_zip(empty_zip)


def test_is_english_and_message_id():
    assert is_english("hello") is True
    assert is_english("héllo") is False
    assert is_english("") is True
    assert is_english(1) is False  # type: ignore[arg-type]
    assert is_valid_message_id("<a@b.com>") is True
    assert is_valid_message_id("invalid") is False


def test_get_file_extension_and_format_bytes():
    assert get_file_extension("file.PDF") == ".pdf"
    assert get_file_extension("") == ""
    assert format_bytes(-1) == "0 B"
    assert "KB" in format_bytes(2048)


def test_extract_email_domain():
    assert extract_email_domain("u@Example.COM") == "example.com"
    assert extract_email_domain("bad") is None


def test_batch_process_and_iterators(sample_email_message):
    assert batch_process([]) == []
    assert batch_process([1, 2, 3], batch_size=0) == [1, 2, 3]
    out = batch_process([1, 2], processor=lambda b: [x * 2 for x in b])
    assert out == [2, 4]
    e1 = EmailIterator([sample_email_message])
    e2 = EmailIterator([sample_email_message])
    merged = merge_email_iterators(e1, e2)
    assert len(list(merged)) == 2
    deduped = deduplicate_emails(merged)
    assert len(list(deduped)) == 1


def test_create_safe_directory_and_validate_path(tmp_path, mocker):
    target = tmp_path / "a" / "b"
    assert create_safe_directory(target).is_dir()
    mocker.patch("pathlib.Path.mkdir", side_effect=OSError("denied"))
    with pytest.raises(IMAPConfigurationError):
        create_safe_directory(tmp_path / "c")
    assert validate_directory_path(str(tmp_path)) == tmp_path
    with pytest.raises(IMAPConfigurationError):
        validate_directory_path("")
    f = tmp_path / "notdir"
    f.write_text("x")
    with pytest.raises(IMAPConfigurationError):
        validate_directory_path(f)


def test_safe_filename_from_subject():
    assert safe_filename_from_subject("") == "untitled"
    assert safe_filename_from_subject("Re: Hello") != ""


@pytest.fixture
def sample_email_message():
    return EmailMessage.read_from_eml_bytes(SAMPLE_EML)
