"""Final statement coverage for remaining gaps."""

import zipfile
from unittest.mock import Mock

import pytest

from sage_imap.exceptions import IMAPFolderOperationError
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import IMAPFolderService
from sage_imap.services.transport import IMAPTransport
from sage_imap.utils import (
    extract_email_domain,
    is_valid_message_id,
    normalize_subject,
    read_eml_files_from_zip,
    safe_filename_from_subject,
)

SAMPLE = b"""From: a@example.com
Subject: Hi
Message-ID: <id@example.com>

Body
"""


def test_email_iterator_with_filtered_indices():
    emails = [
        EmailMessage(message_id="<1@x.com>", subject="A"),
        EmailMessage(message_id="<2@x.com>", subject="B"),
    ]
    it = EmailIterator(emails)
    it._filtered_indices = [0, 1]
    assert it[0].subject == "A"
    assert it[1].subject == "B"
    assert len(it) == 2
    assert list(reversed(it))
    assert it.count(lambda e: True) == 2
    assert emails[0] in it
    assert len(it[0:1]) == 1
    with pytest.raises(IndexError):
        _ = it[5]
    nested = EmailIterator(emails)
    nested._filtered_indices = [0, 1]
    assert len(nested.filter(lambda e: e.subject)) == 2


def test_email_save_filename_collision(tmp_path):
    e = EmailMessage(message_id="<x@y.com>", subject="Same", date="d", raw=SAMPLE)
    path = tmp_path / "out"
    paths = EmailIterator([e, e]).save_all_to_directory(path, "{subject}.eml")
    assert len(paths) == 2
    assert paths[0] != paths[1]


def test_email_filter_case_sensitive():
    e = EmailMessage(message_id="<x@y.com>", plain_body="Hello")
    found = EmailIterator([e]).filter_by_body_content("hello", case_sensitive=True)
    assert len(list(found)) == 0


def test_utils_normalize_subject_bytes_no_encoding(mocker):
    mocker.patch("sage_imap.utils.decode_header", return_value=[(b"Hi", None)])
    assert "Hi" in normalize_subject("raw")


def test_utils_normalize_subject_decode_error(mocker):
    mocker.patch("sage_imap.utils.decode_header", side_effect=ValueError("bad"))
    assert normalize_subject("=?bad?=")


def test_utils_zip_read_failure_validate(mocker, tmp_path):
    zpath = tmp_path / "z.zip"
    with zipfile.ZipFile(zpath, "w") as zf:
        zf.writestr("a.eml", SAMPLE)
    mocker.patch(
        "sage_imap.utils.EmailMessage.read_from_eml_bytes",
        side_effect=ValueError("bad"),
    )
    with pytest.raises(Exception):
        read_eml_files_from_zip(zpath, validate_emails=True)


def test_utils_message_id_edge():
    assert is_valid_message_id("a@" + "x" * 300) is False


def test_message_id_ranges_cached_property():
    ms = MessageSet(msg_ids="5:10", is_uid=True)
    _ = ms.id_ranges
    assert ms.id_ranges == [(5, 10)]


def test_message_get_first_from_range_only():
    ms = MessageSet(msg_ids="10:20", is_uid=True)
    assert ms.parsed_ids == []
    assert ms.get_first_id() == 10


def test_message_intersection_empty():
    with pytest.raises(ValueError):
        MessageSet.from_uids([1]).intersection(MessageSet.from_uids([2]))


def test_message_intersection_success():
    result = MessageSet.from_uids([1, 3]).intersection(MessageSet.from_uids([3, 5]))
    assert "3" in result.msg_ids


def test_message_get_first_id_non_int_range_start():
    ms = MessageSet(msg_ids="10:20", is_uid=True)
    ms._parsed_ids = []
    ms._id_ranges = [("*", 10)]
    assert ms.get_first_id() is None


def test_client_background_health_on_connect(mocker):
    mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
    conn = mocker.Mock()
    conn.sock = mocker.Mock()
    mocker.patch("imaplib.IMAP4_SSL", return_value=conn)
    cfg = ConnectionConfig(
        host="h",
        username="u",
        password="p",
        enable_background_health=True,
        health_check_interval=1,
        max_retries=0,
    )
    client = IMAPClient.from_config(cfg, enable_monitoring=False)
    client.connect()
    assert client._health_check_thread is not None


def test_client_disconnect_joins_thread(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    thread = mocker.Mock()
    thread.is_alive.return_value = True
    client._health_check_thread = thread
    client.connection = mocker.Mock()
    client.transport.bind(client.connection)
    client.disconnect()
    thread.join.assert_called()


def test_client_health_monitor_outer_except(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    client.config.health_check_interval = 0.01

    def wait_side_effect(_t):
        client._stop_health_check.set()
        return True

    mocker.patch.object(client._stop_health_check, "wait", side_effect=wait_side_effect)
    mocker.patch.object(client, "is_connected", side_effect=RuntimeError("check fail"))
    client._health_monitor_loop()


def test_flag_uid_warning_and_empty_fetch(mocker):
    from sage_imap.services.mailbox import IMAPMailboxService

    mailbox = IMAPMailboxService(Mock())
    svc = IMAPFlagService(mailbox)
    ms = MessageSet.from_sequence_numbers([1])
    svc._validate_message_set(ms)
    mailbox.client.fetch = mocker.Mock(return_value=("OK", []))
    assert svc.get_message_flags("1") == []


def test_folder_list_status_exception(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.list = mocker.Mock(
        return_value=("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
    )
    svc.client.status = mocker.Mock(side_effect=RuntimeError("status"))
    folders = svc.list_folders()
    assert folders


def test_folder_quota_no_bytes_items(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.getquota = mocker.Mock(return_value=("OK", ["STORAGE 1 1000"]))
    assert svc.get_folder_quota("INBOX") is not None


def test_transport_search_charset_branches(mocker):
    conn = mocker.Mock()
    conn.uid.return_value = ("OK", [b"1"])
    conn.search.return_value = ("OK", [b"1"])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *a, **k: func(conn)
    transport.search("ALL", use_uid=True)
    transport.search("ALL", charset="UTF-8", use_uid=False)
    transport.search("café", use_uid=False)


def test_email_group_and_sort_bad_dates():
    e = EmailMessage(message_id="<x@y.com>", date="bad")
    groups = EmailIterator([e]).group_by_date()
    assert "Unknown" in groups
    sorted_desc = EmailIterator([e]).sort_by_date(ascending=False)
    assert len(list(sorted_desc)) == 1


def test_email_iterator_get_current_filtered():
    emails = [EmailMessage(message_id=f"<{i}@x.com>") for i in range(3)]
    it = EmailIterator(emails)
    it._filtered_indices = [0, 2]
    sorted_by_size = it.sort_by_size()
    assert len(list(sorted_by_size)) == 2


def test_message_id_ranges_early_cache():
    ms = MessageSet(msg_ids="1:5", is_uid=True)
    ms._id_ranges = [(1, 5)]
    assert ms.id_ranges == [(1, 5)]


def test_utils_safe_filename_underscore_only():
    assert safe_filename_from_subject("   ") == "untitled"


def test_utils_extract_domain_attribute_error():
    class DomainPart(str):
        def lower(self):
            raise AttributeError("no lower")

    class BadEmail(str):
        def split(self, sep=None, maxsplit=-1):
            return [DomainPart("example.com")]

    assert extract_email_domain(BadEmail("a@b.com")) is None


def test_folder_list_raises_outer(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.list = mocker.Mock(side_effect=RuntimeError("list fail"))
    with pytest.raises(IMAPFolderOperationError):
        svc.list_folders()


def test_transport_uid_search_with_charset(mocker):
    conn = mocker.Mock()
    conn.uid.return_value = ("OK", [b"1"])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *a, **k: func(conn)
    transport.search("café", use_uid=True)


def test_transport_capabilities_precached():
    conn = Mock()
    transport = IMAPTransport(conn)
    transport._capabilities = frozenset({"IMAP4REV1"})
    assert transport.get_capabilities() == frozenset({"IMAP4REV1"})


def test_email_decode_payload_final_utf8_fallback():
    class TrickyBytes(bytes):
        decode_calls = 0

        def decode(self, encoding="utf-8", errors="strict"):
            if errors == "replace":
                TrickyBytes.decode_calls += 1
                if TrickyBytes.decode_calls == 1:
                    raise LookupError(encoding)
                if TrickyBytes.decode_calls <= 4:
                    raise UnicodeDecodeError(encoding, self, 0, 1, "x")
                return "ok"
            return super().decode(encoding, errors=errors)

    TrickyBytes.decode_calls = 0
    msg = EmailMessage(message_id="<x@y.com>")
    part = Mock()
    part.get_payload = Mock(return_value=TrickyBytes(b"\xff"))
    part.get_content_charset = Mock(return_value="utf-8")
    assert msg.decode_payload(part) == "ok"


def test_flag_empty_message_set_validation():
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    svc = IMAPFlagService(IMAPMailboxUIDService(Mock()))
    empty = MessageSet.from_uids([1])
    empty.msg_ids = ""
    with pytest.raises(ValueError):
        svc._validate_message_set(empty)


def test_email_filtered_next_and_stop():
    e = EmailMessage(message_id="<x@y.com>")
    it = EmailIterator([e])
    it._filtered_indices = [0]
    assert next(it) is e
    with pytest.raises(StopIteration):
        next(it)


def test_email_group_unknown_no_date():
    e = EmailMessage(message_id="<x@y.com>")
    groups = EmailIterator([e]).group_by_date()
    assert "Unknown" in groups


def test_email_sort_bad_date_descending():
    bad = EmailMessage(message_id="<bad@y.com>", date="not-valid")
    no_date = EmailMessage(message_id="<node@y.com>")
    it = EmailIterator([bad, no_date])
    assert len(list(it.sort_by_date(ascending=False))) == 2


def test_utils_safe_filename_single_underscore():
    assert safe_filename_from_subject("?") == "untitled"


def test_folder_quota_non_bytes_response(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.getquota = mocker.Mock(return_value=("OK", [b"STORAGE 100 1000"]))
    quota = svc.get_folder_quota("INBOX")
    assert quota is not None and "raw" in quota


def test_folder_quota_not_supported():
    client = Mock(spec=["list", "create"])
    svc = IMAPFolderService(client)
    assert svc.get_folder_quota("INBOX") is None


def test_transport_capability_method(mocker):
    conn = mocker.Mock()
    conn.capability.return_value = ("OK", [b"IMAP4rev1"])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *a, **k: getattr(conn, func.__name__)()
    assert transport.capability()[0] == "OK"


def test_transport_uid_search_no_charset(mocker):
    conn = mocker.Mock()
    conn.uid.return_value = ("OK", [b""])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *a, **k: func(conn)
    transport.search("ALL", use_uid=True)


def test_transport_uid_command(mocker):
    conn = mocker.Mock()
    conn.uid.return_value = ("OK", [])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *a, **k: getattr(conn, "uid")(*a, **k)
    transport.uid("FETCH", "1", "(FLAGS)")


def test_client_health_monitor_outer_exception(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    client.config.health_check_interval = 0.01
    calls = {"n": 0}

    def wait_side_effect(_t):
        calls["n"] += 1
        if calls["n"] >= 2:
            client._stop_health_check.set()
            return True
        return False

    mocker.patch.object(client._stop_health_check, "wait", side_effect=wait_side_effect)
    mocker.patch.object(client, "is_connected", side_effect=RuntimeError("outer"))
    client._health_monitor_loop()


def test_flag_get_flags_bytes_only_response(mocker):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    mailbox = IMAPMailboxUIDService(Mock())
    svc = IMAPFlagService(mailbox)
    mailbox.client.fetch = mocker.Mock(return_value=("OK", [b"1 (FLAGS (\\Seen))"]))
    flags = svc.get_message_flags("1")
    assert isinstance(flags, list)


def test_utils_message_id_value_error():
    class BadId(str):
        def strip(self, chars=None):
            return self

        def rsplit(self, *args, **kwargs):
            raise ValueError("bad")

    assert is_valid_message_id(BadId("a@b.com")) is False
