"""Coverage tests for IDLE, sync, streaming fetch, session, OAuth, and SPECIAL-USE."""

from __future__ import annotations

import imaplib
import json
import socket
import time
from unittest.mock import Mock, patch

import pytest

from sage_imap.auth.oauth2 import OAuth2Config, OAuth2TokenResponse, ensure_access_token
from sage_imap.exceptions import IMAPConnectionError
from sage_imap.helpers.enums import DefaultMailboxes
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.special_use import (
    NamespaceMap,
    SpecialUse,
    folder_matches_special_use,
    parse_namespace_response,
)
from sage_imap.models.fetch_parser import (
    iter_messages_from_fetch,
    message_from_fetch_part,
)
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.folder import FolderInfo, IMAPFolderService
from sage_imap.services.idle import (
    IdleEvent,
    IdleWaitResult,
    IMAPIdleSession,
    IMAPIdleWatcher,
)
from sage_imap.services.mailbox import IMAPMailboxUIDService
from sage_imap.services.transport import IMAPTransport
from sage_imap.session import IMAPSession
from sage_imap.sync.condstore import (
    build_changedsince_criteria,
    highest_modseq_from_fields,
    parse_select_sync_fields,
)
from sage_imap.sync.state import MailboxSyncState

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Coverage
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <cov@example.com>
Content-Type: text/plain

Body
"""


class TestCondstoreHelpers:
    def test_parse_select_sync_fields(self):
        data = [b"UIDVALIDITY 99 UIDNEXT 10 HIGHESTMODSEQ 42"]
        fields = parse_select_sync_fields(data)
        assert fields["UIDVALIDITY"] == 99
        assert highest_modseq_from_fields(fields) == 42

    def test_parse_select_skips_none(self):
        assert parse_select_sync_fields([None, b""]) == {}

    def test_build_changedsince_criteria(self):
        assert build_changedsince_criteria(50) == "CHANGEDSINCE 50"


class TestSyncStateAndService:
    def test_is_stale_when_uidvalidity_none(self):
        state = MailboxSyncState(mailbox="INBOX")
        assert state.is_stale(1) is False

    def test_from_dict_without_last_sync(self):
        state = MailboxSyncState.from_dict({"mailbox": "X"})
        assert state.mailbox == "X"

    def test_capture_state_status_failure(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.status.return_value = ("NO", [])
        svc = IMAPMailboxUIDService(client)
        state = svc.sync.capture_state("INBOX")
        assert state.uidvalidity is None

    def test_capture_state_from_selection(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.status.return_value = (
            "OK",
            [b"INBOX (MESSAGES 1 UIDVALIDITY 1 UIDNEXT 2 HIGHESTMODSEQ 5)"],
        )
        transport.select.return_value = (
            "OK",
            [b"UIDVALIDITY 9 UIDNEXT 10 HIGHESTMODSEQ 99"],
        )
        svc = IMAPMailboxUIDService(client)
        state = svc.sync.capture_state_from_selection("INBOX")
        assert state.uidvalidity == 9
        assert state.highest_modseq == 99

    def test_capture_state_from_selection_handles_error(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.status.return_value = ("OK", [b"(MESSAGES 0)"])
        transport.select.side_effect = RuntimeError("select fail")
        svc = IMAPMailboxUIDService(client)
        state = svc.sync.capture_state_from_selection("INBOX")
        assert state.mailbox == "INBOX"

    def test_find_changed_no_modseq(self):
        svc = IMAPMailboxUIDService(Mock())
        empty = svc.sync.find_changed_uids(MailboxSyncState(mailbox="INBOX"))
        assert empty.is_empty()

    def test_find_changed_no_condstore(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability.return_value = False
        svc = IMAPMailboxUIDService(client)
        previous = MailboxSyncState(mailbox="INBOX", highest_modseq=1)
        assert svc.sync.find_changed_uids(previous).is_empty()

    def test_apply_after_sync(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.status.return_value = (
            "OK",
            [b"INBOX (MESSAGES 0 UIDVALIDITY 1 UIDNEXT 2 HIGHESTMODSEQ 3)"],
        )
        svc = IMAPMailboxUIDService(client)
        updated = svc.sync.apply_after_sync(MailboxSyncState(mailbox="INBOX"))
        assert updated.highest_modseq == 3


class TestFetchParser:
    def test_message_from_fetch_raw_and_headers(self):
        flag = b"2 (FLAGS (\\Seen))"
        raw = message_from_fetch_part(flag, SAMPLE_EML, parse_mode=ParseMode.RAW)
        assert raw is not None
        assert raw.raw == SAMPLE_EML

        headers = message_from_fetch_part(
            flag, SAMPLE_EML, parse_mode=ParseMode.HEADERS, mailbox="INBOX"
        )
        assert headers is not None
        assert headers.mailbox == "INBOX"
        assert headers.subject == "Coverage"

    def test_sequence_fetch_metadata(self):
        flag = b"3 (FLAGS (\\Seen))"
        msg = message_from_fetch_part(
            flag, SAMPLE_EML, parse_mode=ParseMode.MINIMAL, is_uid_fetch=False
        )
        assert msg is not None
        assert msg.sequence_number == 3
        assert msg.uid is None

    def test_iter_skips_bad_parts(self):
        data = [
            "not a tuple",
            (b"1 (UID 1 FLAGS (\\Seen))", b""),
            (b"2 (UID 2 FLAGS (\\Seen))", SAMPLE_EML),
        ]
        messages = list(
            iter_messages_from_fetch(data, parse_mode=ParseMode.RAW, is_uid_fetch=True)
        )
        assert len(messages) == 1
        assert messages[0].uid == 2

    def test_iter_handles_parse_error(self, mocker):
        mocker.patch(
            "sage_imap.models.fetch_parser.message_from_fetch_part",
            side_effect=ValueError("bad"),
        )
        data = [(b"1 (UID 1 FLAGS (\\Seen))", SAMPLE_EML)]
        assert list(iter_messages_from_fetch(data)) == []


class TestTransportIdle:
    def test_namespace_not_supported(self):
        transport = IMAPTransport(Mock())
        transport._capabilities = frozenset()
        status, _ = transport.namespace()
        assert status == "NO"

    def test_namespace_ok(self, mocker):
        transport = IMAPTransport(mocker.Mock())
        transport._capabilities = frozenset(["NAMESPACE"])
        mocker.patch.object(
            transport,
            "_run",
            return_value=("OK", [b'(("" "/")) NIL']),
        )
        status, data = transport.namespace()
        assert status == "OK"
        assert data

    def test_idle_start_without_idle_method(self):
        conn = Mock(spec=[])
        transport = IMAPTransport(conn)
        with pytest.raises(imaplib.IMAP4.error):
            transport.idle_start()

    def test_idle_done_simple_command(self, mocker):
        conn = mocker.Mock(spec=["_simple_command"])
        conn._simple_command.return_value = ("OK", [])
        transport = IMAPTransport(conn)
        status, _ = transport.idle_done()
        assert status == "OK"

    def test_idle_read_lines_no_socket(self):
        conn = Mock(spec=["readline"])
        transport = IMAPTransport(conn)
        assert transport.idle_read_lines() == []

    def test_idle_read_lines_reads_event(self, mocker):
        conn = mocker.Mock()
        sock = mocker.Mock()
        sock.gettimeout.return_value = None
        conn.sock = sock
        conn.readline.side_effect = [b"+ idling", b"* 2 EXISTS", b""]
        transport = IMAPTransport(conn)
        lines = transport.idle_read_lines(timeout=1.0)
        assert any(b"EXISTS" in line for line in lines)

    def test_idle_read_lines_timeout(self, mocker):
        conn = mocker.Mock()
        sock = mocker.Mock()
        sock.gettimeout.return_value = None
        conn.sock = sock
        conn.readline.side_effect = socket.timeout()
        transport = IMAPTransport(conn)
        assert transport.idle_read_lines(timeout=0.1) == []

    def test_idle_read_lines_oserror_on_restore_timeout(self, mocker):
        conn = mocker.Mock()
        sock = mocker.Mock()
        sock.gettimeout.side_effect = [None, OSError("gone")]
        conn.sock = sock
        conn.readline.return_value = b"* 1 RECENT"
        transport = IMAPTransport(conn)
        lines = transport.idle_read_lines(timeout=1.0)
        assert lines


class TestIdleSessionAndWatcher:
    def test_idle_start_requires_capability(self):
        client = Mock()
        client.transport = Mock()
        client.transport.has_capability.return_value = False
        with pytest.raises(IMAPConnectionError):
            IMAPIdleSession(client, "INBOX").start()

    def test_idle_wait_not_started(self):
        session = IMAPIdleSession(Mock(), "INBOX")
        with pytest.raises(RuntimeError, match="not started"):
            session.wait()

    def test_idle_wait_timeout(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability.return_value = True
        transport.idle_read_lines.return_value = []
        session = IMAPIdleSession(client, "INBOX")
        session.start()
        result = session.wait(timeout=0.1)
        session.done()
        assert result.timed_out is True

    def test_idle_event_non_matching_line(self):
        event = IdleEvent.from_line(b"OK IDLE completed")
        assert event.sequence is None
        assert event.raw

    def test_idle_watcher_run_once(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability.return_value = True
        transport.idle_read_lines.return_value = [b"* 1 EXISTS"]
        mailbox = Mock()
        watcher = IMAPIdleWatcher(client, mailbox, "INBOX", lambda e: None)
        result = watcher.run_once()
        assert result.events[0].event_type == "EXISTS"

    def test_idle_watcher_reconnect_cycle(self, mocker):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability.return_value = True
        transport.idle_read_lines.return_value = [b"* 3 EXPUNGE"]
        client.is_connected.return_value = False
        client.reconnect = Mock()
        mailbox = Mock()
        mailbox.select = Mock(return_value=Mock(success=True))
        seen = []

        watcher = IMAPIdleWatcher(
            client, mailbox, "INBOX", lambda events: seen.append(events)
        )
        watcher.run_until_stopped(max_cycles=1)
        client.reconnect.assert_called_once()
        assert len(seen) == 1

    def test_idle_watcher_stop(self):
        watcher = IMAPIdleWatcher(Mock(), Mock(), "INBOX", lambda e: None)
        watcher.stop()
        assert watcher._running is False

    def test_idle_session_done_when_inactive(self):
        session = IMAPIdleSession(Mock(), "INBOX")
        session.done()

    def test_idle_watcher_reconnect_after_cycle_error(self, mocker):
        client = Mock()
        client.is_connected.return_value = True
        client.transport = Mock()
        client.transport.has_capability.return_value = True
        mailbox = Mock()
        mailbox.select.return_value = Mock(success=True)
        watcher = IMAPIdleWatcher(client, mailbox, "INBOX", lambda e: None)
        mocker.patch.object(
            watcher,
            "run_once",
            side_effect=[RuntimeError("idle"), IdleWaitResult(events=[])],
        )
        watcher.run_until_stopped(max_cycles=2)
        client.reconnect.assert_called_once()

    def test_idle_watcher_reconnect_failure_sleeps(self, mocker):
        client = Mock()
        client.is_connected.return_value = True
        client.transport = Mock()
        client.transport.has_capability.return_value = True
        mocker.patch.object(
            IMAPIdleWatcher,
            "run_once",
            side_effect=RuntimeError("idle broke"),
        )
        client.reconnect.side_effect = RuntimeError("nope")
        mailbox = Mock()
        watcher = IMAPIdleWatcher(
            client, mailbox, "INBOX", lambda e: None, reconnect_delay=0.01
        )
        with patch("sage_imap.services.idle.time.sleep") as sleep_mock:
            watcher.run_until_stopped(max_cycles=1)
        sleep_mock.assert_called()


class TestSpecialUseAndFolder:
    def test_namespace_parse_empty_and_nil(self):
        assert parse_namespace_response([]) == NamespaceMap()
        assert parse_namespace_response([b"NIL"]).personal is None

    def test_namespace_multi_tuples(self):
        data = [b'(("" "/")) (("~" "/")) (("#shared/" "/"))']
        ns = parse_namespace_response(data)
        assert ns.personal.prefix == ""
        assert len(ns.other_users) == 1
        assert len(ns.shared) == 1

    def test_namespace_primary_delimiter_default(self):
        assert NamespaceMap().primary_delimiter() == "/"

    def test_special_use_imap_attribute(self):
        assert SpecialUse.SENT.imap_attribute() == "\\Sent"

    def test_folder_matches_without_backslash(self):
        assert folder_matches_special_use(["Sent"], SpecialUse.SENT)

    def test_get_namespace_cached_and_failure(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.namespace.return_value = ("NO", [])
        svc = IMAPFolderService(client)
        assert svc.get_namespace().personal is None
        transport.namespace.return_value = ("OK", [b'(("" "/")) NIL'])
        ns1 = svc.get_namespace(refresh=True)
        ns2 = svc.get_namespace()
        assert ns1.personal is not None
        assert ns2 is ns1

    def test_get_special_folders_cached(self, mocker):
        svc = IMAPFolderService(Mock())
        folders = [FolderInfo(name="INBOX", attributes=["\\Inbox"])]
        mocker.patch.object(svc, "list_folders", return_value=folders)
        first = svc.get_special_folders()
        second = svc.get_special_folders()
        assert first == second
        assert svc.list_folders.call_count == 1

    def test_find_by_special_use_string(self, mocker):
        svc = IMAPFolderService(Mock())
        mocker.patch.object(
            svc,
            "get_special_folders",
            return_value={
                SpecialUse.SENT: FolderInfo(name="Sent", attributes=["\\Sent"])
            },
        )
        info = svc.find_by_special_use("\\Sent")
        assert info.name == "Sent"

    def test_resolve_standard_mailbox_paths(self, mocker):
        svc = IMAPFolderService(Mock())
        mocker.patch.object(
            svc,
            "find_by_special_use",
            return_value=FolderInfo(name="[Gmail]/Sent Mail", attributes=["\\Sent"]),
        )
        assert (
            svc.resolve_standard_mailbox(DefaultMailboxes.SENT) == "[Gmail]/Sent Mail"
        )
        mocker.patch.object(svc, "find_by_special_use", return_value=None)
        assert svc.resolve_standard_mailbox(SpecialUse.TRASH) is None
        mocker.patch.object(
            svc,
            "list_folders",
            return_value=[FolderInfo(name="Archive/2024", delimiter="/")],
        )
        assert svc.resolve_standard_mailbox("Archive/2024") == "Archive/2024"
        assert svc.resolve_standard_mailbox("Missing") == "Missing"


class TestOAuthAndClient:
    def test_oauth_expired_and_refresh_path(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="s",
            token_url="https://t",
            refresh_token="r",
            expires_at=0.0,
        )
        assert cfg.is_access_token_expired() is True
        body = json.dumps({"access_token": "fresh", "expires_in": 60}).encode()
        response = mocker.Mock()
        response.read.return_value = body
        response.__enter__ = mocker.Mock(return_value=response)
        response.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("urllib.request.urlopen", return_value=response)
        token = ensure_access_token(cfg)
        assert token == "fresh"

    def test_oauth_token_response_apply(self):
        cfg = OAuth2Config("id", "s", "https://t")
        resp = OAuth2TokenResponse(
            access_token="a", expires_in=10, refresh_token="new_r"
        )
        resp.apply_to_config(cfg)
        assert cfg.access_token == "a"
        assert cfg.refresh_token == "new_r"
        assert cfg.expires_at is not None

    def test_connect_with_oauth_refresh_false_no_token(self):
        client = IMAPClient("h", "u")
        cfg = OAuth2Config("id", "s", "https://t")
        with pytest.raises(ValueError, match="access_token"):
            client.connect_with_oauth(cfg, refresh=False)

    def test_connect_with_oauth_uses_cached_token(self, mocker):
        client = IMAPClient("h", "u")
        cfg = OAuth2Config(
            client_id="id",
            client_secret="s",
            token_url="https://t",
            refresh_token="r",
            access_token="cached",
            expires_at=time.time() + 3600,
        )
        mocker.patch.object(client, "connect_oauth2", return_value=Mock())
        client.connect_with_oauth(cfg)
        client.connect_oauth2.assert_called_once_with("u", "cached")

    def test_connect_with_oauth_refreshes_when_expired(self, mocker):
        client = IMAPClient("h", "u")
        cfg = OAuth2Config(
            client_id="id",
            client_secret="s",
            token_url="https://t",
            refresh_token="r",
            expires_at=0.0,
        )
        mocker.patch(
            "sage_imap.auth.oauth2.refresh_access_token",
            return_value=OAuth2TokenResponse(access_token="new"),
        )
        mocker.patch.object(client, "connect_oauth2", return_value=Mock())
        client.connect_with_oauth(cfg)
        client.connect_oauth2.assert_called_with("u", "new")


class TestIMAPSessionFacade:
    def test_init_requires_host_when_no_config(self):
        with pytest.raises(ValueError, match="host and username"):
            IMAPSession("", "")

    def test_from_config_and_properties(self):
        config = ConnectionConfig(host="h", username="u", password="p")
        session = IMAPSession.from_config(config)
        assert session.config is config
        assert session.mailbox is not None
        assert session.folders is not None
        assert session.flags is not None
        assert session.sync is session.mailbox.sync

    def test_session_oauth_connect(self, mocker):
        session = IMAPSession(
            "h", "u", oauth_config=OAuth2Config("id", "s", "https://t")
        )
        mocker.patch.object(session.client, "connect_with_oauth")
        session.connect()
        session.client.connect_with_oauth.assert_called_once()

    def test_session_workflow(self, mocker):
        session = IMAPSession("h", "u", "p")
        mocker.patch.object(session.client, "connect")
        mocker.patch.object(session.client, "disconnect")
        mocker.patch.object(
            session.mailbox,
            "select",
            return_value=Mock(success=True),
        )
        mocker.patch.object(
            session.mailbox,
            "uid_search",
            return_value=Mock(success=True, affected_messages=["1"]),
        )
        mocker.patch.object(session.mailbox, "close")
        mocker.patch.object(
            session.mailbox,
            "iter_uid_fetch",
            return_value=iter([]),
        )
        mocker.patch.object(
            session.sync,
            "capture_state",
            return_value=MailboxSyncState(mailbox="INBOX"),
        )
        mocker.patch.object(
            session.sync,
            "find_changed_uids",
            return_value=MessageSet.empty(mailbox="INBOX"),
        )
        mocker.patch.object(
            session.folders,
            "get_namespace",
            return_value=NamespaceMap(),
        )
        mocker.patch.object(session.folders, "find_by_special_use", return_value=None)

        with session:
            session.select("INBOX")
            result = session.search(IMAPSearchCriteria.ALL)
            list(session.iter_messages(result.to_uid_message_set()))
            session.capture_sync_state()
            session.find_changed_since(MailboxSyncState(mailbox="INBOX"))
            session.namespace()
            assert session.special_folder(SpecialUse.SENT) is None

    def test_session_close_swallows_mailbox_error(self, mocker):
        session = IMAPSession("h", "u", "p")
        mocker.patch.object(session.client, "connect")
        mocker.patch.object(session.client, "disconnect")
        mocker.patch.object(session.mailbox, "close", side_effect=RuntimeError("close"))
        session.connect()
        session.close()


class TestMessageSetEmpty:
    def test_empty_message_set(self):
        ms = MessageSet.empty(mailbox="INBOX")
        assert ms.is_empty()
        assert ms.mailbox == "INBOX"
        assert list(ms.iter_batches(2)) == []
