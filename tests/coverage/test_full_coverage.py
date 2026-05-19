"""Targeted tests for remaining uncovered statement lines."""

import imaplib
import zipfile
from datetime import datetime, timezone
from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import Mock

import pytest

from sage_imap.decorators import cache_result
from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPClientError,
    IMAPConfigurationError,
    IMAPEmptyFileError,
    IMAPFolderNotFoundError,
    IMAPFolderOperationError,
    IMAPMailboxError,
    IMAPMailboxSelectionError,
    IMAPMailboxUploadError,
)
from sage_imap.helpers.enums import Flag
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import (
    ConnectionConfig,
    ConnectionPool,
    IMAPClient,
    monitor_operation,
)
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import FolderInfo, IMAPFolderService
from sage_imap.services.mailbox.models import MailboxValidator
from sage_imap.services.transport import IMAPTransport
from sage_imap.utils import (
    calculate_content_hash,
    extract_email_domain,
    is_valid_message_id,
    normalize_subject,
    read_eml_files_from_zip,
    safe_filename_from_subject,
)

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Hi
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <id@example.com>
Content-Type: text/plain

Body
"""


# --- decorators ---


def test_cache_result_hit_within_ttl(mocker):
    clock = {"t": 100.0}
    mocker.patch("sage_imap.decorators.time.time", side_effect=lambda: clock["t"])
    calls = []

    @cache_result(ttl=60)
    def fn(x):
        calls.append(1)
        return x * 2

    assert fn(1) == 2
    assert fn(1) == 2
    assert len(calls) == 1


# --- folder ---


class TestFolderFullCoverage:
    def test_parse_folder_attributes_empty(self):
        svc = IMAPFolderService(Mock())
        assert svc._parse_folder_attributes("") == []
        assert svc._parse_folder_attributes("()") == []

    def test_parse_folder_list_skips_empty_and_bad_items(self, mocker):
        svc = IMAPFolderService(Mock())
        folders = svc._parse_folder_list_response(
            [
                b"",
                b'(\\HasNoChildren) "/" "INBOX"',
                b"\xff\xfe invalid bytes",
            ]
        )
        assert len(folders) >= 1

    def test_create_folder_not_ok(self, mocker):
        svc = IMAPFolderService(Mock())
        svc.client.create = mocker.Mock(return_value=("NO", [b"ERR"]))
        mocker.patch.object(svc, "folder_exists", return_value=False)
        with pytest.raises(IMAPFolderOperationError):
            svc.create_folder("NewBox")

    def test_rename_folder_not_found_and_errors(self, mocker):
        svc = IMAPFolderService(Mock())
        mocker.patch.object(svc, "folder_exists", return_value=False)
        with pytest.raises(IMAPFolderNotFoundError):
            svc.rename_folder("Missing", "New")

        mocker.patch.object(svc, "folder_exists", side_effect=[True, False])
        mocker.patch.object(svc, "_is_default_folder", return_value=False)
        svc.client.rename = mocker.Mock(return_value=("NO", [b"NONEXISTENT"]))
        with pytest.raises(IMAPFolderNotFoundError):
            svc.rename_folder("Old", "New")

        mocker.patch.object(svc, "folder_exists", side_effect=[True, False])
        svc.client.rename = mocker.Mock(return_value=("NO", [b"GENERIC"]))
        with pytest.raises(IMAPFolderOperationError):
            svc.rename_folder("Old", "New")

    def test_delete_folder_error_responses(self, mocker):
        svc = IMAPFolderService(Mock())
        info = FolderInfo(name="X", has_children=False)
        mocker.patch.object(svc, "folder_exists", return_value=True)
        mocker.patch.object(svc, "get_folder_info", return_value=info)
        mocker.patch.object(svc, "_is_default_folder", return_value=False)
        svc.client.delete = mocker.Mock(return_value=("NO", [b"NONEXISTENT"]))
        with pytest.raises(IMAPFolderNotFoundError):
            svc.delete_folder("X")
        svc.client.delete = mocker.Mock(return_value=("NO", [b"FAIL"]))
        with pytest.raises(IMAPFolderOperationError):
            svc.delete_folder("X")

    def test_list_folders_not_ok_and_status_counts(self, mocker):
        svc = IMAPFolderService(Mock())
        svc.client.list = mocker.Mock(return_value=("NO", []))
        assert svc.list_folders() == []

        svc.client.list = mocker.Mock(
            return_value=("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
        )
        svc.client.status = mocker.Mock(
            return_value=(
                "OK",
                [b"INBOX (MESSAGES 5 RECENT 1 UNSEEN 2)"],
            )
        )
        folders = svc.list_folders()
        assert folders[0].message_count == 5
        assert folders[0].recent_count == 1
        assert folders[0].unseen_count == 2

    def test_folder_hierarchy_root_only(self, mocker):
        svc = IMAPFolderService(Mock())
        mocker.patch.object(
            svc,
            "list_folders",
            return_value=[FolderInfo(name="INBOX", delimiter="/")],
        )
        h = svc.get_folder_hierarchy()
        assert "INBOX" in h[""]

    def test_subscribe_unsubscribe_lsub_quota(self, mocker):
        svc = IMAPFolderService(Mock())
        mocker.patch.object(svc, "folder_exists", return_value=False)
        with pytest.raises(IMAPFolderNotFoundError):
            svc.subscribe_folder("X")

        mocker.patch.object(svc, "folder_exists", return_value=True)
        svc.client.subscribe = mocker.Mock(return_value=("NO", [b"ERR"]))
        with pytest.raises(IMAPFolderOperationError):
            svc.subscribe_folder("X")

        svc.client.unsubscribe = mocker.Mock(return_value=("NO", [b"ERR"]))
        with pytest.raises(IMAPFolderOperationError):
            svc.unsubscribe_folder("X")

        svc.client.lsub = mocker.Mock(return_value=("NO", []))
        assert svc.list_subscribed_folders() == []

        svc.client.lsub = mocker.Mock(side_effect=RuntimeError("lsub fail"))
        with pytest.raises(IMAPFolderOperationError):
            svc.list_subscribed_folders()

        svc.client.getquota = mocker.Mock(return_value=("OK", [b"STORAGE 1 1000"]))
        quota = svc.get_folder_quota("INBOX")
        assert quota is not None and "raw" in quota


# --- email ---


def _email_list():
    e1 = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
    e2 = EmailMessage(
        message_id="<two@example.com>",
        subject="Other",
        plain_body="hello world",
        date="not-a-date",
    )
    e3 = EmailMessage(
        message_id="<three@example.com>",
        subject="Re: ___",
        plain_body="HELLO",
        date="2022-10-12T14:30:00+00:00",
        flags=[Flag.SEEN],
    )
    return [e1, e2, e3]


def test_email_post_init_parse_error(mocker):
    mocker.patch.object(
        EmailMessage, "parse_eml_content", side_effect=ValueError("bad parse")
    )
    msg = EmailMessage(message_id="<x@y.com>", raw=SAMPLE_EML)
    assert msg._parse_error is not None


def test_email_header_decode_no_encoding(mocker):
    msg = EmailMessage(message_id="<x@y.com>")
    mocker.patch(
        "email.header.decode_header",
        return_value=[(b"raw-bytes", None)],
    )
    assert msg._safe_header_decode("Subject")


def test_email_parse_addresses(mocker):
    msg = EmailMessage(message_id="<x@y.com>")
    mocker.patch("sage_imap.models.email.EmailAddress", side_effect=ValueError("bad"))
    assert msg._parse_email_address("a@b.com") is None
    assert msg._parse_email_addresses(["a@b.com", "c@d.com"]) == []


def test_email_decode_payload_fallbacks(mocker):
    msg = EmailMessage(message_id="<x@y.com>")
    part = Mock()
    part.get_payload = Mock(return_value=b"data")
    part.get_content_charset = Mock(return_value="unknown-charset")
    assert msg.decode_payload(part)
    part2 = Mock()
    part2.get_payload = Mock(return_value=42)
    part2.get_content_charset = Mock(return_value=None)
    assert msg.decode_payload(part2) == "42"


def test_email_extract_attachment_no_filename():
    multipart = MIMEMultipart()
    part = MIMEText("data", "plain")
    part.add_header("Content-Disposition", "attachment")
    multipart.attach(part)
    em = message_from_bytes(multipart.as_bytes())
    inst = EmailMessage(message_id="<x@y.com>")
    atts = inst.extract_attachments(em)
    assert atts


def test_email_iterator_filtered_paths():
    it = EmailIterator(_email_list())
    filtered = it.filter(lambda e: e.subject)
    assert filtered[0]
    assert len(filtered) == 3
    assert list(reversed(filtered))
    assert filtered.count(lambda e: True) == 3
    assert filtered[0] in filtered
    sliced = filtered[0:2]
    assert len(sliced) == 2
    with pytest.raises(IndexError):
        _ = filtered[99]
    nested = filtered.filter(lambda e: e.plain_body)
    assert len(nested) == 3


def test_email_iterator_date_and_group_sort(tmp_path):
    it = EmailIterator(_email_list())
    bad = it.filter_by_date_range(start_date=datetime(2020, 1, 1, tzinfo=timezone.utc))
    assert len(list(bad)) >= 1
    groups = it.group_by_date()
    assert "Unknown" in groups
    emails = _email_list()
    for em in emails:
        em.date = "2022-10-12T14:30:00"
    assert len(list(EmailIterator(emails).sort_by_date(ascending=True))) == 3
    case = it.filter_by_body_content("HELLO", case_sensitive=True)
    assert len(list(case)) >= 1
    emails = _email_list()
    for em in emails:
        em.raw = SAMPLE_EML
        em.date = "2022-10-12"
    saved = EmailIterator(emails).save_all_to_directory(tmp_path)
    EmailIterator(emails).save_all_to_directory(tmp_path)
    assert saved


# --- message ---


def test_message_set_id_ranges_cache():
    ms = MessageSet(msg_ids="10:20", is_uid=True)
    assert ms.id_ranges
    ms._id_ranges = [(10, 20)]
    assert ms.id_ranges == [(10, 20)]


def test_message_set_intersection_and_subtract_empty():
    a = MessageSet.from_uids([1])
    with pytest.raises(ValueError):
        a.intersection(MessageSet.from_uids([2]))
    with pytest.raises(ValueError):
        a.subtract(MessageSet.from_uids([1]))


def test_message_set_split_by_size_chunks():
    ms = MessageSet(msg_ids=[i for i in range(1, 26, 2)], is_uid=True)
    chunks = ms.split_by_size(5)
    assert len(chunks) == 3


# --- client ---


def test_connection_pool_clear_logout_error(mocker):
    pool = ConnectionPool()
    config = ConnectionConfig(host="h", username="u", password="p")
    conn = mocker.Mock()
    conn.logout = mocker.Mock(side_effect=OSError("logout"))
    pool.return_connection(config, conn)
    pool.clear_pool()


def test_monitor_operation_failure(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=True)
    client.config.enable_monitoring = True

    @monitor_operation
    def boom(self):
        raise RuntimeError("fail")

    with pytest.raises(RuntimeError):
        boom(client)
    assert client.metrics.failed_operations >= 1


def test_client_connect_health_and_login_cleanup(mocker):
    mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
    mock_conn = mocker.Mock()
    mock_conn.sock = mocker.Mock()
    mocker.patch("imaplib.IMAP4_SSL", return_value=mock_conn)
    config = ConnectionConfig(
        host="h",
        username="u",
        password="p",
        enable_background_health=True,
        health_check_interval=1,
        max_retries=0,
    )
    client = IMAPClient.from_config(config, enable_monitoring=False)
    mock_conn.login.side_effect = imaplib.IMAP4.error("auth")
    mock_conn.logout.side_effect = OSError("logout fail")
    with pytest.raises(IMAPAuthenticationError):
        client.connect()
    assert client.connection is None


def test_client_disconnect_and_is_connected(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    assert client.is_connected() is False
    client.connection = mocker.Mock()
    client._connection_start_time = datetime.now()
    client._health_check_thread = mocker.Mock()
    client._health_check_thread.is_alive.return_value = False
    client.transport.bind(client.connection)
    client.transport.noop = mocker.Mock(return_value=("OK", []))
    client.disconnect()


def test_client_health_monitor_reconnect_fail(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    client.config.health_check_interval = 0.01
    client._stop_health_check.clear()

    def wait_side_effect(timeout):
        client._stop_health_check.set()
        return True

    mocker.patch.object(client._stop_health_check, "wait", side_effect=wait_side_effect)
    mocker.patch.object(client, "is_connected", return_value=False)
    mocker.patch.object(client, "connect", side_effect=RuntimeError("reconnect"))
    client._health_monitor_loop()


# --- flag ---


def test_flag_validate_and_execute_paths(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    mailbox = IMAPMailboxUIDService(Mock())
    svc = IMAPFlagService(mailbox)
    assert svc._validate_flags(Flag.SEEN) == [Flag.SEEN]
    with pytest.raises(ValueError):
        svc._validate_flags([Flag.SEEN, "bad"])  # type: ignore[list-item]
    with pytest.raises(ValueError):
        svc._validate_message_set(MessageSet(msg_ids="", is_uid=True))

    client = IMAPClient("h", "u", "p")
    client.connection = mock_imap_connection
    client.transport.bind(mock_imap_connection)
    mailbox = IMAPMailboxUIDService(client)
    mailbox.current_selection = "INBOX"
    mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
    svc = IMAPFlagService(mailbox)
    msg_set = MessageSet.from_uids([1])
    mock_imap_connection.uid.side_effect = RuntimeError("store fail")
    result = svc.add_flag(msg_set, Flag.SEEN)
    assert not result.success

    mock_imap_connection.uid.side_effect = None
    mock_imap_connection.uid.return_value = ("OK", [])
    svc.operation_history = [mocker.Mock(success=True)] * 101
    svc.add_flag(msg_set, Flag.SEEN)
    assert len(svc.operation_history) == 100

    mailbox.client.fetch = mocker.Mock(side_effect=RuntimeError("fetch"))
    assert svc.get_message_flags("1") == []

    email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
    email.flags = [Flag.SEEN, Flag.FLAGGED]
    summary = svc.get_flag_summary(EmailIterator([email]))
    assert Flag.SEEN.value in summary


# --- transport ---


def test_transport_capabilities_cached(mocker):
    conn = mocker.create_autospec(imaplib.IMAP4, instance=True)
    conn.capability.return_value = ("OK", [b"IMAP4rev1 MOVE"])
    transport = IMAPTransport(conn)
    caps1 = transport.get_capabilities()
    caps2 = transport.get_capabilities()
    assert caps1 == caps2
    conn.capability.assert_called_once()


def test_transport_move_copy_delete_fallback(mocker):
    transport = IMAPTransport(mocker.Mock())
    transport._capabilities = frozenset({"IMAP4REV1"})
    mocker.patch.object(
        transport, "copy", return_value=("OK", {"method": "COPY", "copyuid": None})
    )
    mocker.patch.object(transport, "store_flags", return_value=("OK", {}))
    mocker.patch.object(transport, "expunge", return_value=("OK", []))
    seq = MessageSet.from_sequence_numbers([1])
    status, meta = transport.move(seq, "Archive")
    assert status == "OK"
    transport.store_flags.assert_called_once()
    transport.expunge.assert_called_once()
    assert "COPY" in meta.get("method", "")


# --- utils ---


def test_utils_subject_and_hash_and_zip(tmp_path, mocker):
    mocker.patch(
        "sage_imap.utils.decode_header",
        return_value=[(b"bytes", None)],
    )
    assert normalize_subject("=?utf-8?B?SGk=?=")

    mocker.patch(
        "sage_imap.utils.decode_header",
        side_effect=ValueError("bad header"),
    )
    assert normalize_subject("=?bad?=")

    mocker.patch("hashlib.new", side_effect=ValueError("bad algo"))
    with pytest.raises(IMAPClientError):
        calculate_content_hash(b"data", "md5")

    empty_zip = tmp_path / "empty.zip"
    empty_zip.write_bytes(b"")
    with pytest.raises(IMAPEmptyFileError):
        read_eml_files_from_zip(empty_zip)

    bad_zip = tmp_path / "bad.zip"
    bad_zip.write_bytes(b"not a zip")
    with pytest.raises(IMAPConfigurationError):
        read_eml_files_from_zip(bad_zip)

    assert is_valid_message_id("x" * 65 + "@example.com") is False
    assert is_valid_message_id("a@" + "x" * 254) is False
    assert extract_email_domain("") is None
    assert safe_filename_from_subject("") == "untitled"


def test_mailbox_validator_edges():
    empty_set = MessageSet.from_uids([1])
    empty_set.msg_ids = ""
    with pytest.raises(IMAPMailboxError):
        MailboxValidator.validate_message_set(empty_set)
    with pytest.raises(IMAPMailboxSelectionError):
        MailboxValidator.validate_mailbox("")
    with pytest.raises(IMAPMailboxSelectionError):
        MailboxValidator.validate_mailbox(123)  # type: ignore[arg-type]
    with pytest.raises(IMAPMailboxUploadError):
        MailboxValidator.validate_email_data([])


def test_utils_zip_validate_raises(tmp_path):
    zpath = tmp_path / "z.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("bad.eml", b"not valid email content")
    with pytest.raises(Exception):
        read_eml_files_from_zip(zpath, validate_emails=True)
