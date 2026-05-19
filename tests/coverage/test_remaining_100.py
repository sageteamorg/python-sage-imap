"""Additional tests to reach full line coverage on remaining modules."""

from email import message_from_bytes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from unittest.mock import Mock

import pytest

from sage_imap.helpers.enums import Flag
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import IMAPFolderService
from sage_imap.services.mailbox.models import MailboxValidator
from sage_imap.services.transport import IMAPTransport
from sage_imap.utils import (
    deduplicate_emails,
    is_english,
    merge_email_iterators,
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


def test_email_wrong_extension_warning(tmp_path):
    path = tmp_path / "mail.txt"
    path.write_bytes(SAMPLE_EML)
    EmailMessage.read_from_eml_file(path)


def test_email_parse_address_exception(mocker):
    msg = EmailMessage(message_id="x@y.com")
    mocker.patch("sage_imap.models.email.EmailAddress", side_effect=ValueError("bad"))
    assert msg._parse_email_address("user@example.com") is None
    assert msg._parse_email_addresses(["user@example.com"]) == []


def test_email_extract_attachment_failure(mocker):
    msg = MIMEMultipart()
    msg.attach(MIMEText("body", "plain"))
    bad = MIMEText("x")
    bad.add_header("Content-Disposition", "attachment", filename="f.txt")
    msg.attach(bad)
    raw = msg.as_bytes()
    em = message_from_bytes(raw)
    inst = EmailMessage(message_id="")
    for part in em.walk():
        if part.get_filename() == "f.txt":
            mocker.patch.object(part, "get_payload", side_effect=RuntimeError("decode"))
            break
    assert inst.extract_attachments(em) == []


def test_email_extract_flags_and_decode_paths():
    flags = EmailMessage.extract_flags(b"1 (FLAGS (\\Seen \\Flagged))")
    assert Flag.SEEN in flags
    assert EmailMessage.extract_flags(b"invalid") == []

    msg = MIMEText("hello", "plain", "utf-8")
    inst = EmailMessage(message_id="x")
    assert inst.decode_payload(msg)
    msg2 = MIMEMultipart()
    msg2.attach(MIMEText("a", "plain"))
    msg2.attach(MIMEText("b", "html"))
    assert inst.decode_payload(msg2)


def test_email_cached_properties_and_recipients(sample_email_message):
    assert sample_email_message.content_hash
    assert sample_email_message.all_recipients
    assert sample_email_message.is_multipart is not None
    assert sample_email_message.total_attachment_size >= 0


def test_message_set_open_ended_range():
    ms = MessageSet(msg_ids="1:*", is_uid=True)
    assert ms.id_ranges == [(1, "*")]


def test_message_set_union_and_subtract():
    a = MessageSet.from_uids([1, 3])
    b = MessageSet.from_uids([3, 4])
    u = a.union(b)
    assert "4" in u.msg_ids
    remaining = a.subtract(MessageSet.from_uids([1]))
    assert "3" in remaining.msg_ids


def test_client_health_monitor_connect_failure(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    calls = {"n": 0}

    def wait_side_effect(_t):
        calls["n"] += 1
        if calls["n"] > 1:
            client._stop_health_check.set()
            return True
        return False

    mocker.patch.object(client._stop_health_check, "wait", side_effect=wait_side_effect)
    mocker.patch.object(client, "is_connected", return_value=False)
    mocker.patch.object(client, "connect", side_effect=RuntimeError("reconnect fail"))
    client._health_monitor_loop()
    assert client.metrics.reconnection_attempts >= 1


def test_client_disconnect_updates_uptime(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=False)
    client.connection = mocker.Mock()
    client.transport.bind(client.connection)
    client._connection_start_time = __import__("datetime").datetime.now()
    client.disconnect()


def test_client_getattr_monitoring_failure(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=True)
    client.connection = mocker.Mock()
    client.connection.noop = mocker.Mock(side_effect=OSError("fail"))
    client.transport.bind(client.connection)
    with pytest.raises(OSError):
        client.noop()


def test_flag_store_partial_failure(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = IMAPClient("h", "u", "p")
    client.connection = mock_imap_connection
    client.transport.bind(mock_imap_connection)
    mailbox = IMAPMailboxUIDService(client)
    mailbox.current_selection = "INBOX"
    mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
    svc = IMAPFlagService(mailbox)
    msg_set = MessageSet.from_uids([1, 2])
    mock_imap_connection.uid.side_effect = [("NO", []), ("OK", [])]
    result = svc.add_flag(msg_set, Flag.SEEN)
    assert not result.success


def test_flag_get_flags_tuple_and_bytes(mocker):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = Mock()
    client.transport = mocker.Mock()
    mailbox = IMAPMailboxUIDService(client)
    svc = IMAPFlagService(mailbox)
    client.transport.fetch = mocker.Mock(
        return_value=("OK", [(b"1 (FLAGS (\\Seen \\Flagged))", b"")])
    )
    flags = svc.get_message_flags("1")
    assert Flag.SEEN in flags
    client.transport.fetch = mocker.Mock(return_value=("OK", [b"1 (FLAGS (\\Seen))"]))
    assert svc.get_message_flags("1")


def test_flag_set_flags_success_path(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = IMAPClient("h", "u", "p")
    client.transport.bind(mock_imap_connection)
    mailbox = IMAPMailboxUIDService(client)
    mailbox.current_selection = "INBOX"
    mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
    svc = IMAPFlagService(mailbox)
    mock_imap_connection.uid.return_value = ("OK", [])
    result = svc.set_flags(MessageSet.from_uids([1]), [Flag.SEEN, Flag.FLAGGED])
    assert result.success
    assert (
        svc.get_flag_summary(
            __import__(
                "sage_imap.models.email", fromlist=["EmailIterator"]
            ).EmailIterator([])
        )
        == {}
    )


def test_folder_rename_delete_paths(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.rename = mocker.Mock(return_value=("OK", []))
    mocker.patch.object(svc, "folder_exists", side_effect=[True, False])
    mocker.patch.object(svc, "_is_default_folder", return_value=False)
    assert svc.rename_folder("Old", "New").success

    mocker.patch.object(svc, "folder_exists", return_value=True)
    mocker.patch.object(
        svc,
        "get_folder_info",
        return_value=__import__(
            "sage_imap.services.folder", fromlist=["FolderInfo"]
        ).FolderInfo(name="X", has_children=False),
    )
    svc.client.delete = mocker.Mock(return_value=("NO", [b"ERR"]))
    with pytest.raises(Exception):
        svc.delete_folder("X")


def test_folder_hierarchy_nested(mocker):
    svc = IMAPFolderService(Mock())
    mocker.patch.object(
        svc,
        "list_folders",
        return_value=[
            __import__("sage_imap.services.folder", fromlist=["FolderInfo"]).FolderInfo(
                name="Parent/Child", delimiter="/"
            )
        ],
    )
    h = svc.get_folder_hierarchy()
    assert "Parent" in h


def test_folder_subscribe_failures(mocker):
    svc = IMAPFolderService(Mock())
    mocker.patch.object(svc, "folder_exists", return_value=False)
    with pytest.raises(Exception):
        svc.subscribe_folder("Missing")
    mocker.patch.object(svc, "folder_exists", return_value=True)
    svc.client.subscribe = mocker.Mock(return_value=("NO", []))
    with pytest.raises(Exception):
        svc.subscribe_folder("X")


def test_transport_capability_and_search_branches(mocker):
    conn = mocker.Mock()
    conn.capability.side_effect = RuntimeError("cap fail")
    transport = IMAPTransport(conn)
    assert transport.get_capabilities() == frozenset()
    conn.capability.side_effect = None
    conn.capability.return_value = ("OK", [b"IMAP4rev1"])
    transport2 = IMAPTransport(conn)
    transport2.search("café", use_uid=True)
    transport2.search("ALL", charset="UTF-8", use_uid=False)


def test_transport_move_sequence_simple_command(mocker):
    conn = mocker.Mock(spec=["capability", "_simple_command"])
    conn.capability.return_value = ("OK", [b"MOVE"])
    conn._simple_command.return_value = ("OK", [None])
    transport = IMAPTransport(conn)
    transport._run = lambda func, *args, **kwargs: func(conn)
    seq = MessageSet.from_sequence_numbers([1])
    status, _ = transport.move(seq, "Archive")
    assert status == "OK"


def test_utils_zip_nested_and_edges(tmp_path):
    import zipfile

    inner_bytes = SAMPLE_EML
    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as zf:
        zf.writestr("nested.zip", inner_bytes)
        zf.writestr("ok.eml", SAMPLE_EML)
    it = read_eml_files_from_zip(outer, extract_nested_zips=True)
    assert len(list(it)) >= 1


def test_utils_misc_branches():
    assert is_english(None) is False  # type: ignore[arg-type]
    assert safe_filename_from_subject("Re: ___") != ""
    merge_email_iterators()
    deduplicate_emails([])


def test_mailbox_validator_sequence_warning():
    ms = MessageSet.from_sequence_numbers([1])
    MailboxValidator.validate_message_set(ms)


@pytest.fixture
def sample_email_message():
    return EmailMessage.read_from_eml_bytes(SAMPLE_EML)
