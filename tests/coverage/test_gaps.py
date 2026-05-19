"""Tests targeting remaining coverage gaps across sage_imap modules."""

import builtins
import signal
import sys
import zipfile
from datetime import datetime, timezone
from email import message_from_bytes
from unittest.mock import Mock, patch

import pytest

from sage_imap.decorators import (
    cache_result,
    circuit_breaker,
    clear_performance_metrics,
    get_performance_metrics,
    log_function_calls,
    performance_monitor,
    timeout,
)
from sage_imap.exceptions import IMAPClientError
from sage_imap.helpers.enums import Flag
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import (
    MessageSet,
    MessageSetBatchIterator,
    _expand_message_set_ids,
)
from sage_imap.services.client import ConnectionConfig, ConnectionPool, IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import IMAPFolderService
from sage_imap.services.mailbox.models import (
    BulkOperationResult,
    MailboxOperationResult,
    MailboxValidator,
)
from sage_imap.services.transport import IMAPTransport
from sage_imap.utils import (
    convert_to_local_time,
    deduplicate_emails,
    format_bytes,
    is_valid_message_id,
    merge_email_iterators,
    parse_email_date,
    read_eml_files_from_directory,
    read_eml_files_from_zip,
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


# --- decorators ---


def test_performance_monitor_psutil_import_error(mocker):
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "psutil":
            raise ImportError("no psutil")
        return real_import(name, *args, **kwargs)

    mocker.patch("builtins.__import__", side_effect=fake_import)

    @performance_monitor(track_memory=True, log_performance=True, store_metrics=False)
    def work():
        return 1

    assert work() == 1


def test_performance_monitor_logs_time_and_memory(mocker):
    proc = mocker.Mock()
    proc.memory_info.side_effect = [mocker.Mock(rss=1000), mocker.Mock(rss=2000)]
    psutil = mocker.Mock()
    psutil.Process.return_value = proc
    mocker.patch.dict(sys.modules, {"psutil": psutil})
    clear_performance_metrics()

    @performance_monitor(track_memory=True, log_performance=True)
    def work():
        return 2

    assert work() == 2
    assert get_performance_metrics()


def test_log_function_calls_no_args_no_result():
    @log_function_calls(log_args=False, log_result=False, log_exceptions=False)
    def fn():
        return 3

    assert fn() == 3


def test_log_function_calls_raises_without_log():
    @log_function_calls(log_exceptions=False)
    def fn():
        raise ValueError("x")

    with pytest.raises(ValueError):
        fn()


def test_cache_result_expired_entry_removed(mocker):
    now = {"t": 100.0}
    mocker.patch("sage_imap.decorators.time.time", side_effect=lambda: now["t"])

    @cache_result(ttl=5, maxsize=10)
    def fn(x):
        return x * 2

    assert fn(2) == 4
    now["t"] = 200.0
    assert fn(2) == 4


def test_circuit_breaker_half_open_success(mocker):
    clock = {"t": 1.0}

    def fake_time():
        return clock["t"]

    mocker.patch("sage_imap.decorators.time.time", side_effect=fake_time)

    @circuit_breaker(failure_threshold=1, recovery_timeout=5)
    def fn(should_fail=False):
        if should_fail:
            raise RuntimeError("fail")
        return "ok"

    with pytest.raises(RuntimeError):
        fn(should_fail=True)
    with pytest.raises(IMAPClientError):
        fn(should_fail=True)
    clock["t"] = 20.0
    assert fn(should_fail=False) == "ok"


def test_timeout_handler_raises(mocker):
    fake_signal = mocker.Mock()
    fake_signal.SIGALRM = 14

    def trigger_timeout(sig, handler):
        handler(sig, None)

    fake_signal.signal.side_effect = trigger_timeout
    fake_signal.alarm = mocker.Mock()
    mocker.patch.dict(sys.modules, {"signal": fake_signal})

    @timeout(1)
    def slow():
        return "done"

    with pytest.raises(IMAPClientError):
        slow()


def test_timeout_decorator_with_mock_signal(mocker):
    fake_signal = mocker.Mock()
    fake_signal.SIGALRM = 14
    fake_signal.signal.return_value = signal.SIG_DFL
    fake_signal.alarm = mocker.Mock()
    mocker.patch.dict(sys.modules, {"signal": fake_signal})

    @timeout(2)
    def quick():
        return "done"

    assert quick() == "done"
    fake_signal.signal.assert_called()
    fake_signal.alarm.assert_called()


# --- utils ---


def test_convert_local_time_overflow():
    class OverflowDatetime(datetime):
        def astimezone(self, tz=None):
            raise OverflowError("overflow")

    dt = OverflowDatetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with pytest.raises(Exception):
        convert_to_local_time(dt)


def test_validate_email_local_part_too_long():
    local = "x" * 65
    assert validate_email_address(f"{local}@example.com") is False


def test_parse_email_date_raises_after_alternatives():
    with pytest.raises(Exception):
        parse_email_date("completely-invalid-date-xyz")


def test_read_eml_skip_no_message_id(tmp_path):
    d = tmp_path / "emails"
    d.mkdir()
    (d / "a.eml").write_bytes(b"From: a@b.com\nSubject: X\n\nBody without message id\n")
    with pytest.raises(Exception):
        read_eml_files_from_directory(d, validate_emails=True)


def test_read_eml_directory_read_error_raises(tmp_path, mocker):
    d = tmp_path / "emails"
    d.mkdir()
    (d / "a.eml").write_bytes(SAMPLE_EML)
    mocker.patch(
        "sage_imap.utils.EmailMessage.read_from_eml_file",
        side_effect=ValueError("bad eml"),
    )
    with pytest.raises(Exception):
        read_eml_files_from_directory(d, validate_emails=True)


def test_read_eml_zip_nested_and_edge_cases(tmp_path):
    inner = tmp_path / "inner.zip"
    with zipfile.ZipFile(inner, "w") as zf:
        zf.writestr("a.eml", SAMPLE_EML)
    outer = tmp_path / "outer.zip"
    with zipfile.ZipFile(outer, "w") as zf:
        zf.writestr("nested.zip", inner.read_bytes())
        zf.writestr("empty.eml", b"")
        zf.writestr("bad.eml", b"not an email")
    with pytest.raises(Exception):
        read_eml_files_from_zip(outer)
    outer2 = tmp_path / "outer2.zip"
    with zipfile.ZipFile(outer2, "w") as zf:
        zf.writestr("a.eml", SAMPLE_EML)
        zf.writestr("nested.zip", inner.read_bytes())
    it = read_eml_files_from_zip(outer2, extract_nested_zips=True)
    assert len(list(it)) >= 1


def test_format_bytes_petabyte():
    assert "PB" in format_bytes(1024**6)


def test_is_valid_message_id_edge_cases():
    assert is_valid_message_id("a@nodot") is False
    assert is_valid_message_id("") is False


def test_deduplicate_with_custom_key():
    e = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
    it = deduplicate_emails([e, e], key_func=lambda x: x.message_id)
    assert len(list(it)) == 1


def test_merge_with_none_iterator():
    e = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
    from sage_imap.models.email import EmailIterator

    merged = merge_email_iterators(EmailIterator([e]), None)
    assert len(list(merged)) == 1


# --- message ---


def test_message_set_id_ranges_cached():
    ms = MessageSet.from_range(1, 5, is_uid=True)
    assert ms.id_ranges
    assert ms.id_ranges == ms.id_ranges


def test_message_set_get_first_last_from_range():
    ms = MessageSet(msg_ids="10:20", is_uid=True)
    assert ms.get_first_id() == 10
    assert ms.get_last_id() == 20


def test_message_set_split_by_size_ranges_warning():
    ms = MessageSet(msg_ids="1:100", is_uid=True)
    chunks = ms.split_by_size(10)
    assert len(chunks) == 1


def test_expand_message_set_ids_open_range():
    ms = MessageSet(msg_ids="1:*", is_uid=True)
    with pytest.raises(ValueError):
        _expand_message_set_ids(ms)


def test_expand_message_set_ids_too_many():
    ms = MessageSet.from_range(1, 20000, is_uid=True)
    with pytest.raises(ValueError):
        _expand_message_set_ids(ms, max_ids=100)


def test_message_set_batch_iterator():
    ms = MessageSet.from_uids([1, 2, 3])
    batches = list(MessageSetBatchIterator(ms, batch_size=2))
    assert len(batches) == 2


# --- client ---


def test_pool_return_existing_and_overflow_logout(mocker):
    pool = ConnectionPool(max_connections=1)
    config = ConnectionConfig(host="h", username="u", password="p")
    c1 = mocker.Mock()
    pool.return_connection(config, c1)
    assert pool.get_connection(config) is c1
    c2 = mocker.Mock()
    c2.logout = mocker.Mock(side_effect=OSError("logout fail"))
    pool.return_connection(config, c2)


def test_pool_clear_logout_failure(mocker):
    pool = ConnectionPool()
    config = ConnectionConfig(host="h", username="u", password="p")
    conn = mocker.Mock()
    conn.logout = mocker.Mock(side_effect=OSError("clear fail"))
    pool.return_connection(config, conn)
    pool.clear_pool()


def test_client_stale_reconnect_and_login_failures(mocker):
    mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
    mock_conn = mocker.Mock()
    mock_conn.sock = mocker.Mock()
    mocker.patch("imaplib.IMAP4_SSL", return_value=mock_conn)
    client = IMAPClient("h", "u", "p", enable_monitoring=True, max_retries=0)
    client.connection = mocker.Mock()
    client._stale = False
    mocker.patch.object(client, "is_connected", return_value=False)
    mocker.patch.object(IMAPClient, "disconnect")
    client._connect_impl()
    mock_conn.login.side_effect = __import__("imaplib").IMAP4.error("auth")
    client.connection = None
    with pytest.raises(Exception):
        client._connect_impl()


def test_client_health_monitor_start_and_errors(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=True)
    client._health_check_thread = mocker.Mock()
    client._health_check_thread.is_alive.return_value = True
    client._start_health_monitoring()
    client._health_check_thread = None
    client._start_health_monitoring()


def test_client_getattr_non_callable_and_monitor_fail(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=True)
    client.connection = mocker.Mock()
    client.connection.capability = "not-callable"
    assert client.capability == "not-callable"
    client.connection.fetch = mocker.Mock(side_effect=RuntimeError("fail"))
    client.transport.bind(client.connection)
    with pytest.raises(RuntimeError):
        client.fetch("1", "(FLAGS)")


def test_client_health_check_with_connection_age(mocker):
    client = IMAPClient("h", "u", "p", enable_monitoring=True)
    client.connection = mocker.Mock()
    client.transport.bind(client.connection)
    client.transport.noop = mocker.Mock(return_value=("OK", []))
    client._connection_start_time = datetime.now()
    h = client.health_check()
    assert h["connection_age"] is not None


# --- transport ---


def _patch_transport_run(transport, conn):
    transport._run = lambda func, *args, **kw: getattr(conn, func.__name__)(*args, **kw)


def test_transport_all_imap_methods(mocker):
    conn = mocker.Mock()
    conn.capability.return_value = ("OK", [b"IMAP4rev1"])
    for meth in (
        "select",
        "close",
        "check",
        "status",
        "expunge",
        "list",
        "create",
        "delete",
        "rename",
        "subscribe",
        "unsubscribe",
        "lsub",
        "append",
        "authenticate",
    ):
        setattr(conn, meth, mocker.Mock(return_value=("OK", [])))
    transport = IMAPTransport(conn)
    _patch_transport_run(transport, conn)
    transport.select("INBOX")
    transport.close()
    transport.check()
    transport.status("INBOX", "(MESSAGES)")
    transport.expunge()
    transport.list()
    transport.create("X")
    transport.delete("X")
    transport.rename("A", "B")
    transport.subscribe("A")
    transport.unsubscribe("A")
    transport.lsub()
    transport.append("INBOX", None, None, b"raw")
    transport.authenticate("PLAIN", lambda x: b"")


def test_transport_search_ascii_charset(mocker):
    conn = mocker.Mock()
    conn.search.return_value = ("OK", [b"1"])
    transport = IMAPTransport(conn)
    transport.search("ALL", use_uid=False)


def test_transport_fetch_sequence_and_set_flags(mocker):
    conn = mocker.Mock()
    conn.fetch.return_value = ("OK", [])
    conn.store.return_value = ("OK", [])
    transport = IMAPTransport(conn)
    seq = MessageSet.from_sequence_numbers([1])
    transport.fetch(seq, "RFC822", use_uid=False)
    transport.set_flags(seq, [Flag.SEEN])


def test_transport_copy_sequence_and_move_non_uid_has_move(mocker):
    conn = mocker.Mock()
    conn.capability.return_value = ("OK", [b"MOVE"])
    conn.copy.return_value = ("OK", [b"[COPYUID 1 1 2]"])
    conn.move = mocker.Mock(return_value=("OK", []))
    transport = IMAPTransport(conn)
    seq = MessageSet.from_sequence_numbers([1])
    transport.copy(seq, "Archive")
    transport.move(seq, "Archive")


def test_transport_parse_copyuid_none_data():
    assert IMAPTransport._parse_copyuid(("OK", None)) is None


def test_transport_resolve_returns_source_when_empty(mocker):
    conn = mocker.Mock()
    transport = IMAPTransport(conn)
    source = MessageSet.from_uids([1])
    result = transport.resolve_uids_after_copy(source, ("OK", []), {}, None)
    assert result is source


# --- flag ---


def test_flag_service_exception_in_execute(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = IMAPClient("h", "u", "p")
    client.connection = mock_imap_connection
    client.transport.bind(mock_imap_connection)
    mailbox = IMAPMailboxUIDService(client)
    mailbox.current_selection = "INBOX"
    mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
    svc = IMAPFlagService(mailbox)
    msg_set = MessageSet.from_uids([1])
    svc._validate_message_set = mocker.Mock(side_effect=RuntimeError("boom"))
    with pytest.raises(Exception):
        svc.add_flag(msg_set, Flag.SEEN)


def test_flag_invalid_flag_type():
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    mailbox = IMAPMailboxUIDService(Mock())
    svc = IMAPFlagService(mailbox)
    with pytest.raises(ValueError):
        svc._validate_flags("not-a-flag")  # type: ignore[arg-type]


def test_flag_set_flags_exception(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = IMAPClient("h", "u", "p")
    client.connection = mock_imap_connection
    client.transport.bind(mock_imap_connection)
    mailbox = IMAPMailboxUIDService(client)
    mailbox.current_selection = "INBOX"
    mailbox.check = mocker.Mock(side_effect=RuntimeError("check fail"))
    svc = IMAPFlagService(mailbox)
    msg_set = MessageSet.from_uids([1])
    with pytest.raises(Exception):
        svc.set_flags(msg_set, [Flag.SEEN])


def test_flag_get_message_flags_bytes_response(mocker, mock_imap_connection):
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    client = IMAPClient("h", "u", "p")
    mailbox = IMAPMailboxUIDService(client)
    svc = IMAPFlagService(mailbox)
    client.fetch = mocker.Mock(return_value=("OK", [b"1 (FLAGS (\\Seen))"]))
    flags = svc.get_message_flags("1")
    assert isinstance(flags, list)


def test_flag_sync_skips_no_sequence(mocker, mock_imap_connection):
    from sage_imap.models.email import EmailIterator
    from sage_imap.services.mailbox import IMAPMailboxUIDService

    mailbox = IMAPMailboxUIDService(Mock())
    svc = IMAPFlagService(mailbox)
    email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
    email.sequence_number = None
    synced = svc.sync_flags_with_emails(EmailIterator([email]))
    assert synced == {}


# --- folder ---


def test_folder_validation_errors():
    svc = IMAPFolderService(Mock())
    with pytest.raises(ValueError):
        svc._validate_folder_name("")
    with pytest.raises(ValueError):
        svc._validate_folder_name("bad|name")
    with pytest.raises(ValueError):
        svc._validate_folder_name("x" * 300)


def test_folder_parse_list_unparseable(mocker):
    svc = IMAPFolderService(Mock())
    folders = svc._parse_folder_list_response([b"not a valid list response"])
    assert folders == []


def test_folder_create_with_parent(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.create = mocker.Mock(return_value=("OK", []))
    mocker.patch.object(svc, "folder_exists", return_value=False)
    result = svc.create_folder("Child", parent="Parent")
    assert result.success


def test_folder_rename_default_and_exists(mocker):
    svc = IMAPFolderService(Mock())
    client = svc.client
    mocker.patch.object(svc, "folder_exists", side_effect=[True, True])
    with pytest.raises(Exception):
        svc.rename_folder("INBOX", "Other")
    mocker.patch.object(svc, "folder_exists", side_effect=[True, False])
    client.rename.return_value = ("OK", [])
    mocker.patch.object(svc, "_is_default_folder", side_effect=[True, False])
    with pytest.raises(Exception):
        svc.rename_folder("INBOX", "X")


def test_folder_delete_not_found_and_has_children(mocker):
    svc = IMAPFolderService(Mock())
    mocker.patch.object(svc, "folder_exists", return_value=False)
    with pytest.raises(Exception):
        svc.delete_folder("Missing")
    mocker.patch.object(svc, "folder_exists", return_value=True)
    info = mocker.Mock()
    info.has_children = True
    mocker.patch.object(svc, "get_folder_info", return_value=info)
    with pytest.raises(Exception):
        svc.delete_folder("Parent")


def test_folder_delete_bad_response(mocker):
    svc = IMAPFolderService(Mock())
    client = svc.client
    mocker.patch.object(svc, "folder_exists", return_value=True)
    mocker.patch.object(
        svc,
        "get_folder_info",
        return_value=__import__(
            "sage_imap.services.folder", fromlist=["FolderInfo"]
        ).FolderInfo(name="X", has_children=False),
    )
    client.delete.return_value = ("NO", [b"NONEXISTENT"])
    with pytest.raises(Exception):
        svc.delete_folder("X")


def test_folder_list_status_failures(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.list = mocker.Mock(
        return_value=("OK", [b'(\\HasNoChildren) "/" "INBOX"'])
    )
    svc.client.status = mocker.Mock(side_effect=Exception("status fail"))
    folders = svc.list_folders()
    assert folders


def test_folder_get_folder_quota_supported(mocker):
    svc = IMAPFolderService(Mock())
    svc.client.getquota = mocker.Mock(return_value=("OK", [b"STORAGE 1 1000"]))
    quota = svc.get_folder_quota("INBOX")
    assert quota is not None


def test_folder_copy_structure_inner_fail(mocker):
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
    mocker.patch.object(svc, "create_folder", side_effect=RuntimeError("create failed"))
    results = svc.copy_folder_structure("Parent", "Archive")
    assert len(results) == 1
    assert not results[0].success


# --- mailbox models ---


def test_mailbox_operation_result_post_init_count():
    r = MailboxOperationResult(
        success=True, operation="x", affected_messages=["1", "2"]
    )
    assert r.message_count == 2


def test_mailbox_validator_expected_mailbox_and_empty_list():
    from sage_imap.exceptions import IMAPMailboxError, IMAPMailboxUploadError

    ms = MessageSet.from_uids([1], mailbox="INBOX")
    with pytest.raises(IMAPMailboxError):
        MailboxValidator.validate_message_set(ms, "Other")
    with pytest.raises(IMAPMailboxUploadError):
        MailboxValidator.validate_email_data([])


def test_bulk_result_empty_total():
    b = BulkOperationResult(
        operation="x",
        total_messages=0,
        successful_messages=0,
        failed_messages=0,
        execution_time=0.0,
        batch_size=1,
        batches_processed=0,
    )
    assert b.success_rate == 0.0


# --- email gaps ---


def test_email_post_init_parse_failure(mocker):
    mocker.patch.object(
        EmailMessage, "parse_eml_content", side_effect=ValueError("bad")
    )
    EmailMessage(message_id="", raw=SAMPLE_EML)


def test_email_read_file_io_error(tmp_path, mocker):
    path = tmp_path / "x.eml"
    path.write_bytes(SAMPLE_EML)
    mocker.patch("builtins.open", side_effect=OSError("denied"))
    with pytest.raises(OSError):
        EmailMessage.read_from_eml_file(path)


def test_email_parse_message_from_bytes_fail(mocker):
    inst = EmailMessage(message_id="")
    inst.raw = SAMPLE_EML
    mocker.patch("email.message_from_bytes", side_effect=ValueError("invalid format"))
    with pytest.raises(ValueError):
        inst.parse_eml_content()


def test_email_parse_fields_failure(mocker):
    inst = EmailMessage(message_id="")
    inst.raw = SAMPLE_EML
    mocker.patch(
        "email.message_from_bytes",
        return_value=message_from_bytes(SAMPLE_EML),
    )
    mocker.patch.object(
        EmailMessage, "sanitize_message_id", side_effect=RuntimeError("x")
    )
    with pytest.raises(Exception):
        inst.parse_eml_content()


def test_email_header_decode_bytes_with_encoding():
    em = message_from_bytes(
        b"Subject: =?utf-8?B?SGk=?=\n\n",
        policy=__import__("email").policy.default,
    )
    msg = EmailMessage(message_id="<x@y.com>")
    msg._safe_header_decode(em["Subject"])


def test_email_header_decode_exception():
    msg = EmailMessage(message_id="<x@y.com>")
    mocker_inst = msg
    with patch.object(
        EmailMessage,
        "_safe_header_decode",
        wraps=EmailMessage._safe_header_decode,
    ):
        with patch("email.header.decode_header", side_effect=ValueError("bad")):
            result = EmailMessage._safe_header_decode(mocker_inst, "=?bad?=")
    assert result
