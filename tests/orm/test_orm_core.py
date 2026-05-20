"""ORM unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.orm.backends.sync import SyncImapBackend
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.models.message import ImapMessage
from sage_imap.orm.q import Q
from sage_imap.orm.queryset import MessageQuerySet
from sage_imap.orm.schemas.message import ImapMessageSummarySchema
from sage_imap.services.mailbox.models import MailboxOperationResult


class TestQ:
    def test_filter_kwargs_unread(self):
        q = Q(unread=True)
        assert q.compile() == str(IMAPSearchCriteria.UNSEEN)

    def test_and_composition(self):
        q = Q(unread=True) & Q(from_address="a@b.com")
        compiled = q.compile()
        assert "UNSEEN" in compiled
        assert "FROM" in compiled

    def test_or_composition(self):
        q = Q(seen=True) | Q(flagged=True)
        compiled = q.compile()
        assert "OR" in compiled or "SEEN" in compiled


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

    def test_compile_all_by_default(self):
        qs = MessageQuerySet(self._backend(), account_id="acct1", mailbox="INBOX")
        assert qs.compile_criteria() == str(IMAPSearchCriteria.ALL)

    def test_limit_offset(self):
        qs = MessageQuerySet(self._backend(), account_id="acct1", mailbox="INBOX")
        uids = qs.limit(2).offset(1).uids().parsed_ids
        assert uids == [20, 30]

    def test_cursor_after(self):
        qs = MessageQuerySet(self._backend(), account_id="acct1", mailbox="INBOX")
        uids = qs.cursor(after_uid=15).uids().parsed_ids
        assert uids == [20, 30]

    def test_count(self):
        qs = MessageQuerySet(self._backend(), account_id="acct1", mailbox="INBOX")
        assert qs.count() == 3

    def test_fetch_identity_skips_search_fetch(self):
        backend = self._backend()
        qs = (
            MessageQuerySet(backend, account_id="acct1", mailbox="INBOX")
            .limit(1)
            .with_load_level(LoadLevel.IDENTITY)
        )
        msgs = qs.fetch_all()
        assert len(msgs) == 1
        assert msgs[0].uid == 10
        backend.fetch_messages.assert_not_called()


class TestSchemas:
    def test_summary_schema(self):
        msg = ImapMessage(
            account_id="a1",
            mailbox="INBOX",
            uid=42,
            subject="Hello",
            from_address="x@y.com",
            flags=["\\Seen"],
        )
        schema = ImapMessageSummarySchema.from_imap_message(msg)
        data = schema.model_dump(mode="json")
        assert data["uid"] == 42
        assert data["account_id"] == "a1"
        assert data["subject"] == "Hello"
