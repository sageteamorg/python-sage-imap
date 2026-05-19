"""Tests for IDLE, CONDSTORE sync, and streaming fetch."""

from unittest.mock import Mock

from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.models.email import EmailMessage
from sage_imap.models.fetch_parser import iter_messages_from_fetch
from sage_imap.models.message import MessageSet
from sage_imap.services.idle import IdleEvent, IMAPIdleSession
from sage_imap.services.mailbox import IMAPMailboxUIDService
from sage_imap.sync.condstore import parse_status_sync_fields
from sage_imap.sync.state import MailboxSyncState

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Test
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <id@example.com>
Content-Type: text/plain

Hello
"""


class TestCondstoreParsing:
    def test_parse_status_sync_fields(self):
        text = "INBOX (MESSAGES 10 UIDVALIDITY 42 UIDNEXT 100 HIGHESTMODSEQ 999)"
        fields = parse_status_sync_fields(text)
        assert fields["MESSAGES"] == 10
        assert fields["UIDVALIDITY"] == 42
        assert fields["HIGHESTMODSEQ"] == 999

    def test_sync_state_stale(self):
        state = MailboxSyncState(mailbox="INBOX", uidvalidity=1)
        assert state.is_stale(2) is True
        assert state.is_stale(1) is False

    def test_sync_state_roundtrip(self):
        state = MailboxSyncState(mailbox="INBOX", uidvalidity=5, highest_modseq=10)
        restored = MailboxSyncState.from_dict(state.to_dict())
        assert restored.mailbox == "INBOX"
        assert restored.uidvalidity == 5


class TestParseMode:
    def test_minimal_parse_skips_body(self):
        msg = EmailMessage.read_from_eml_bytes(SAMPLE_EML, parse_mode=ParseMode.MINIMAL)
        assert msg.subject == "Test"
        assert msg.plain_body == ""

    def test_raw_parse_skips_mime(self):
        msg = EmailMessage.read_from_eml_bytes(SAMPLE_EML, parse_mode=ParseMode.RAW)
        assert msg.raw == SAMPLE_EML
        assert msg._parsed is True


class TestStreamingFetch:
    def test_iter_messages_from_fetch(self):
        flag_line = b"1 (UID 100 FLAGS (\\Seen))"
        data = [(flag_line, SAMPLE_EML)]
        messages = list(
            iter_messages_from_fetch(
                data, parse_mode=ParseMode.MINIMAL, mailbox="INBOX"
            )
        )
        assert len(messages) == 1
        assert messages[0].uid == 100

    def test_iter_uid_fetch_batches(self, mocker):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.fetch.return_value = (
            "OK",
            [(b"1 (UID 1 FLAGS (\\Seen))", SAMPLE_EML)],
        )
        svc = IMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        msg_set = MessageSet.from_uids([1, 2])
        messages = list(
            svc.iter_uid_fetch(msg_set, parse_mode=ParseMode.MINIMAL, batch_size=1)
        )
        assert len(messages) == 2
        assert transport.fetch.call_count == 2


class TestIdle:
    def test_idle_event_from_line(self):
        event = IdleEvent.from_line(b"* 42 EXISTS")
        assert event.sequence == 42
        assert event.event_type == "EXISTS"

    def test_idle_session_start_done(self):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability.return_value = True
        transport.idle_read_lines.return_value = [b"* 1 EXISTS"]

        session = IMAPIdleSession(client, "INBOX")
        with session:
            result = session.wait(timeout=1.0)
        transport.idle_start.assert_called_once()
        transport.idle_done.assert_called_once()
        assert result.events[0].event_type == "EXISTS"


class TestSyncService:
    def test_capture_state(self, mocker):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.status.return_value = (
            "OK",
            [b"INBOX (MESSAGES 3 UIDVALIDITY 7 UIDNEXT 10 HIGHESTMODSEQ 55)"],
        )
        mocker.patch.object(transport, "has_capability", return_value=True)
        svc = IMAPMailboxUIDService(client)
        state = svc.sync.capture_state("INBOX")
        assert state.uidvalidity == 7
        assert state.highest_modseq == 55

    def test_find_changed_uids(self, mocker):
        client = Mock()
        transport = Mock()
        client.transport = transport
        transport.has_capability = mocker.Mock(return_value=True)
        transport.search.return_value = ("OK", [b"100 101"])
        svc = IMAPMailboxUIDService(client)
        previous = MailboxSyncState(mailbox="INBOX", highest_modseq=50)
        changed = svc.sync.find_changed_uids(previous)
        assert 100 in changed and 101 in changed
        assert changed.msg_ids == "100:101"
