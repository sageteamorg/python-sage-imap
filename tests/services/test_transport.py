"""Unit tests for IMAPTransport."""

import imaplib
from unittest.mock import Mock

import pytest

from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet
from sage_imap.services.transport import IMAPTransport


def _patch_run_on_conn(transport, conn):
    """Route transport._run to connection methods (imaplib unbound methods)."""

    def _run(func, *args, **kwargs):
        return getattr(conn, func.__name__)(*args, **kwargs)

    transport._run = _run


class TestIMAPTransport:
    def test_store_flags_uid_mode(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        msg_set = MessageSet.from_uids([1, 2, 3])
        status, _ = transport.store_flags(msg_set, FlagCommand.ADD, Flag.SEEN)
        assert status == "OK"
        mock_imap_connection.uid.assert_called_with("STORE", "1:3", "+FLAGS", "\\Seen")

    def test_store_flags_sequence_mode(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        msg_set = MessageSet.from_sequence_numbers([1, 2])
        transport.store_flags(msg_set, FlagCommand.REMOVE, Flag.FLAGGED)
        mock_imap_connection.store.assert_called_with("1:2", "-FLAGS", "\\Flagged")

    def test_search_with_charset(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        transport.search("SUBJECT café", charset="UTF-8", use_uid=True)
        mock_imap_connection.uid.assert_called_with("SEARCH", "UTF-8", "SUBJECT café")

    def test_move_uses_uid_move_when_supported(self, mocker):
        conn = mocker.create_autospec(imaplib.IMAP4, instance=True)
        conn.capability.return_value = (
            "OK",
            [b"IMAP4rev1 MOVE UIDPLUS"],
        )
        conn.uid.return_value = ("OK", [None])
        transport = IMAPTransport(conn)
        msg_set = MessageSet.from_uids([5])
        status, meta = transport.move(msg_set, "Archive")
        assert status == "OK"
        assert meta["method"] == "MOVE"
        conn.uid.assert_any_call("MOVE", "5", "Archive")

    def test_parse_copyuid(self):
        response = ("OK", [b"[COPYUID 123 5 10]"])
        parsed = IMAPTransport._parse_copyuid(response)
        assert parsed["uidvalidity"] == 123
        assert parsed["source_uids"] == "5"
        assert parsed["dest_uids"] == "10"

    def test_bind_unbind_and_require_connection(self):
        transport = IMAPTransport()
        assert transport.connection is None
        with pytest.raises(imaplib.IMAP4.error):
            transport.noop()
        conn = Mock(spec=imaplib.IMAP4)
        transport.bind(conn)
        assert transport.connection is conn
        transport.unbind()
        assert transport.connection is None

    def test_get_capabilities_cached(self, mocker):
        conn = mocker.create_autospec(imaplib.IMAP4, instance=True)
        conn.capability.return_value = ("OK", [b"IMAP4rev1 MOVE"])
        transport = IMAPTransport(conn)
        caps1 = transport.get_capabilities()
        caps2 = transport.get_capabilities()
        assert "MOVE" in caps1
        assert caps1 is caps2
        conn.capability.assert_called_once()

    def test_get_capabilities_failure(self, mocker):
        conn = mocker.create_autospec(imaplib.IMAP4, instance=True)
        conn.capability.side_effect = RuntimeError("fail")
        transport = IMAPTransport(conn)
        assert transport.get_capabilities() == frozenset()

    def test_has_capability(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        assert transport.has_capability("move") is True

    def test_basic_commands(self, mock_imap_connection):
        mock_imap_connection.append.return_value = ("OK", [])
        mock_imap_connection.select.return_value = ("OK", [b"1"])
        mock_imap_connection.close.return_value = ("OK", [])
        mock_imap_connection.check.return_value = ("OK", [])
        mock_imap_connection.status.return_value = ("OK", [])
        mock_imap_connection.expunge.return_value = ("OK", [])
        mock_imap_connection.list.return_value = ("OK", [])
        mock_imap_connection.create.return_value = ("OK", [])
        mock_imap_connection.delete.return_value = ("OK", [])
        mock_imap_connection.rename.return_value = ("OK", [])
        mock_imap_connection.subscribe.return_value = ("OK", [])
        mock_imap_connection.unsubscribe.return_value = ("OK", [])
        mock_imap_connection.lsub.return_value = ("OK", [])
        transport = IMAPTransport(mock_imap_connection)
        _patch_run_on_conn(transport, mock_imap_connection)
        transport.select("INBOX")
        transport.close()
        transport.check()
        transport.status("INBOX", "(MESSAGES)")
        transport.expunge()
        transport.list()
        transport.create("Test")
        transport.delete("Test")
        transport.rename("A", "B")
        transport.subscribe("A")
        transport.unsubscribe("A")
        transport.lsub()
        transport.append("INBOX", None, None, b"raw")
        mock_imap_connection.append.assert_called()

    def test_search_ascii_no_charset(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        transport.search("ALL", use_uid=False)
        mock_imap_connection.search.assert_called_with(None, "ALL")

    def test_uid_fetch_and_set_flags(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        msg_set = MessageSet.from_uids([1])
        transport.fetch(msg_set, "RFC822")
        transport.set_flags(msg_set, [Flag.SEEN, Flag.FLAGGED])
        mock_imap_connection.uid.assert_called()

    def test_copy_returns_metadata(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        msg_set = MessageSet.from_uids([1])
        status, meta = transport.copy(msg_set, "Archive")
        assert status == "OK"
        assert meta["method"] == "COPY"

    def test_move_copy_fails(self, mocker):
        conn = mocker.Mock()
        conn.capability.return_value = ("OK", [b"IMAP4rev1"])

        def uid_side_effect(cmd, *args):
            if cmd == "COPY":
                return ("NO", [])
            return ("OK", [])

        conn.uid.side_effect = uid_side_effect
        transport = IMAPTransport(conn)
        status, meta = transport.move(MessageSet.from_uids([1]), "Trash")
        assert status == "NO"

    def test_move_store_fails(self, mocker):
        conn = mocker.Mock()
        conn.capability.return_value = ("OK", [b"IMAP4rev1"])

        def uid_side_effect(cmd, *args):
            if cmd == "COPY":
                return ("OK", [b"[COPYUID 1 5 10]"])
            if cmd == "STORE":
                return ("NO", [])
            return ("OK", [])

        conn.uid.side_effect = uid_side_effect
        transport = IMAPTransport(conn)
        status, meta = transport.move(MessageSet.from_uids([1]), "Trash")
        assert status == "NO"
        assert "warning" in meta

    def test_move_sequence_with_move_method(self, mocker):
        conn = mocker.create_autospec(imaplib.IMAP4, instance=True)
        conn.capability.return_value = ("OK", [b"MOVE"])
        conn.move = mocker.Mock(return_value=("OK", []))
        transport = IMAPTransport(conn)
        msg_set = MessageSet.from_sequence_numbers([1])
        status, meta = transport.move(msg_set, "Archive")
        assert status == "OK"
        conn.move.assert_called()

    def test_parse_copyuid_empty_and_string_item(self):
        assert IMAPTransport._parse_copyuid(("OK", [])) is None
        parsed = IMAPTransport._parse_copyuid(("OK", ["[COPYUID 1 2 3]"]))
        assert parsed["uidvalidity"] == 1

    def test_search_by_message_ids(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        mock_imap_connection.uid.return_value = ("OK", [b"100 101"])
        uids = transport.search_by_message_ids(["<a@b.com>", ""])
        assert uids == [100, 101]

    def test_expand_uid_set(self):
        assert IMAPTransport._expand_uid_set("1,3:5") == [1, 3, 4, 5]

    def test_resolve_uids_after_copy(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        source = MessageSet.from_uids([5])
        meta = {"copyuid": {"dest_uids": "10"}}
        resolved = transport.resolve_uids_after_copy(
            source, ("OK", []), meta, message_ids=None
        )
        assert "10" in str(resolved.msg_ids)

    def test_resolve_uids_by_message_id(self, mock_imap_connection):
        transport = IMAPTransport(mock_imap_connection)
        mock_imap_connection.uid.return_value = ("OK", [b"99"])
        source = MessageSet.from_uids([5])
        resolved = transport.resolve_uids_after_copy(
            source, ("OK", []), {}, message_ids=["<x@y.com>"]
        )
        assert "99" in str(resolved.msg_ids)

    def test_authenticate(self, mock_imap_connection):
        mock_imap_connection.authenticate.return_value = ("OK", [])
        transport = IMAPTransport(mock_imap_connection)
        _patch_run_on_conn(transport, mock_imap_connection)
        transport.authenticate("PLAIN", lambda x: b"")
        mock_imap_connection.authenticate.assert_called()
