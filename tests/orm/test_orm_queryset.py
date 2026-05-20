"""Tests for sage_imap.orm.queryset."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from sage_imap.models.message import MessageSet
from sage_imap.orm.backends.sync import SyncImapBackend
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.exceptions import OrmMailboxNotSelectedError, OrmNotConnectedError
from sage_imap.orm.models.message import ImapMessage
from sage_imap.orm.q import Q
from sage_imap.orm.queryset import MessageQuerySet, _expand_uids
from sage_imap.services.mailbox.models import MailboxOperationResult


class TestExpandUids:
    def test_expands_compact_ranges(self):
        msg_set = MessageSet.from_uids([1, 2], mailbox="INBOX")
        assert _expand_uids(msg_set) == [1, 2]


class TestMessageQuerySet:
    def _backend(self) -> MagicMock:
        backend = MagicMock(spec=SyncImapBackend)
        backend.account_id = "acct1"
        backend.mailbox = "INBOX"
        backend.uid_search.return_value = MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["10", "20", "30"],
        )
        return backend

    def test_no_backend_raises(self):
        qs = MessageQuerySet()
        with pytest.raises(OrmNotConnectedError):
            qs.uids()

    def test_no_mailbox_raises(self):
        backend = self._backend()
        backend.mailbox = None
        qs = MessageQuerySet(backend, account_id="acct1", mailbox=None)
        with pytest.raises(OrmMailboxNotSelectedError):
            qs.uids()

    def test_using_backend(self):
        backend = self._backend()
        qs = MessageQuerySet(account_id="x", mailbox="OLD")
        bound = qs.using_backend(backend)
        assert bound._mailbox == "INBOX"

    def test_filter_exclude_raw(self):
        backend = self._backend()
        qs = (
            MessageQuerySet(backend, account_id="a", mailbox="INBOX")
            .filter(Q(unread=True), "ALL")
            .exclude(seen=True)
            .raw_criteria("FLAGGED")
        )
        assert "FLAGGED" in qs.compile_criteria()

    def test_cursor_before(self):
        backend = self._backend()
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
        uids = qs.cursor(before_uid=25).uids().parsed_ids
        assert uids == [10, 20]

    def test_failed_search_returns_empty(self):
        backend = self._backend()
        backend.uid_search.return_value = MailboxOperationResult(
            success=False, operation="uid_search", error_message="fail"
        )
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
        assert qs.count() == 0

    def test_changed_since(self, sync_state):
        backend = self._backend()
        backend.find_changed_uids.return_value = MessageSet.from_uids(
            [20], mailbox="INBOX"
        )
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
        uids = qs.changed_since(sync_state).uids().parsed_ids
        assert uids == [20]
        backend.find_changed_uids.assert_called_once_with(sync_state)

    def test_order_by_date_and_uid(self):
        backend = self._backend()
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX").limit(3)
        d1 = datetime(2026, 1, 1, tzinfo=timezone.utc)
        d2 = datetime(2026, 2, 1, tzinfo=timezone.utc)
        d3 = datetime(2026, 1, 15, tzinfo=timezone.utc)
        msgs = [
            ImapMessage("a", "INBOX", 30, date=d2, subject="B"),
            ImapMessage("a", "INBOX", 10, date=d1, subject="A"),
            ImapMessage("a", "INBOX", 20, date=d3, subject="c"),
        ]
        backend.fetch_messages.side_effect = lambda *a, **k: iter(msgs)
        qs_level = qs.with_load_level(LoadLevel.HEADERS)
        ordered = qs_level.order_by("-date").fetch_all()
        assert ordered[0].uid == 30
        by_uid = qs_level.order_by("uid").fetch_all()
        assert [m.uid for m in by_uid] == [10, 20, 30]
        by_subject = qs_level.order_by("-subject").fetch_all()
        assert by_subject[0].subject == "c"

    def test_bulk_mark_seen(self):
        backend = self._backend()
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX").limit(2)
        count = qs.bulk_mark_seen()
        assert count == 2
        assert backend.mark_seen.call_count == 2

    def test_iter_full_load_level(self, sample_email, sync_backend):
        sample_email.uid = 10
        sync_backend._session.iter_messages.return_value = iter([sample_email])
        qs = MessageQuerySet(sync_backend, account_id="acct-test", mailbox="INBOX")
        msgs = qs.with_load_level(LoadLevel.FULL).limit(1).fetch_all()
        assert len(msgs) == 1
        assert msgs[0].subject == "Test Subject"
        assert msgs[0].uid == 10

    def test_multiple_criteria_anded(self):
        backend = self._backend()
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
        qs = qs.filter(unread=True).filter(flagged=True)
        criteria = qs.compile_criteria()
        assert "UNSEEN" in criteria
        assert "FLAGGED" in criteria

    def test_order_by_unknown_field_unchanged(self):
        backend = self._backend()
        msgs = [
            ImapMessage("a", "INBOX", 30),
            ImapMessage("a", "INBOX", 10),
        ]
        backend.fetch_messages.side_effect = lambda *a, **k: iter(msgs)
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX").limit(2)
        result = qs.order_by("unknown").fetch_all()
        assert [m.uid for m in result] == [30, 10]

    def test_empty_uid_list_identity(self):
        backend = self._backend()
        backend.uid_search.return_value = MailboxOperationResult(
            success=True, operation="uid_search", affected_messages=[]
        )
        qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
        assert qs.with_load_level(LoadLevel.IDENTITY).fetch_all() == []
