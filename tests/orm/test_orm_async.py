"""Async ORM unit tests."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.orm.async_session import AsyncImapORM
from sage_imap.orm.backends.async_ import AsyncImapBackend
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.exceptions import OrmMailboxNotSelectedError, OrmNotConnectedError
from sage_imap.orm.models.message import ImapMessage
from sage_imap.orm.queryset import MessageQuerySet
from sage_imap.services.mailbox.models import MailboxOperationResult


@pytest.mark.asyncio
async def test_count_async():
    backend = MagicMock()
    backend.account_id = "a1"
    backend.mailbox = "INBOX"
    backend.uid_search = AsyncMock(
        return_value=MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["1", "2"],
        )
    )
    qs = MessageQuerySet(backend, account_id="a1", mailbox="INBOX")
    assert await qs.count_async() == 2


@pytest.mark.asyncio
async def test_iter_async_identity():
    backend = MagicMock(spec=AsyncImapBackend)
    backend.account_id = "a1"
    backend.mailbox = "INBOX"
    backend.uid_search = AsyncMock(
        return_value=MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["5"],
        )
    )

    async def _fetch(msg_set, *, load_level=LoadLevel.HEADERS, batch_size=50):
        for uid in msg_set.parsed_ids:
            yield ImapMessage.from_uid("a1", "INBOX", uid, backend=backend)

    backend.fetch_messages = _fetch
    qs = MessageQuerySet(backend, account_id="a1", mailbox="INBOX").with_load_level(
        LoadLevel.HEADERS
    )
    msgs = await qs.fetch_all_async()
    assert len(msgs) == 1
    assert msgs[0].uid == 5


@pytest.mark.asyncio
async def test_uids_async_changed_since(async_backend, sync_state):
    qs = MessageQuerySet(async_backend, account_id="acct-test", mailbox="INBOX")
    uids = (await qs.changed_since(sync_state).uids_async()).parsed_ids
    assert uids == [5]


@pytest.mark.asyncio
async def test_bulk_mark_seen_async(async_backend):
    qs = MessageQuerySet(async_backend, account_id="acct-test", mailbox="INBOX")
    count = await qs.limit(1).bulk_mark_seen_async()
    assert count == 1
    async_backend._session.flags.add_flag.assert_awaited()


@pytest.mark.asyncio
async def test_iter_async_with_fetch(async_backend, sample_email, mock_async_session):
    sample_email.uid = 5

    async def _messages(*_args, **_kwargs):
        yield sample_email

    mock_async_session.iter_messages = _messages
    qs = MessageQuerySet(async_backend, account_id="acct-test", mailbox="INBOX")
    msgs = await qs.with_load_level(LoadLevel.FULL).fetch_all_async()
    assert msgs[0].subject == "Test Subject"


@pytest.mark.asyncio
async def test_uids_async_failed_search():
    backend = MagicMock()
    backend.account_id = "a"
    backend.mailbox = "INBOX"
    backend.uid_search = AsyncMock(
        return_value=MailboxOperationResult(success=False, operation="uid_search")
    )
    qs = MessageQuerySet(backend, account_id="a", mailbox="INBOX")
    assert await qs.count_async() == 0


@pytest.mark.asyncio
async def test_iter_async_identity_only():
    backend = MagicMock(spec=AsyncImapBackend)
    backend.account_id = "a1"
    backend.mailbox = "INBOX"
    backend.uid_search = AsyncMock(
        return_value=MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["9"],
        )
    )
    qs = MessageQuerySet(backend, account_id="a1", mailbox="INBOX").with_load_level(
        LoadLevel.IDENTITY
    )
    msgs = await qs.fetch_all_async()
    assert len(msgs) == 1
    assert msgs[0].uid == 9


@pytest.mark.asyncio
async def test_async_queryset_errors():
    qs = MessageQuerySet()
    with pytest.raises(OrmNotConnectedError):
        await qs.uids_async()
    backend = MagicMock()
    backend.account_id = "a"
    backend.mailbox = None
    qs2 = MessageQuerySet(backend, account_id="a", mailbox=None)
    with pytest.raises(OrmMailboxNotSelectedError):
        await qs2.uids_async()


@pytest.mark.asyncio
async def test_async_orm_manager_binding(async_backend):
    async with AsyncImapORM.open("acct", session=async_backend._session) as orm:
        await orm.select_mailbox("INBOX")
        qs = ImapMessage.objects.filter(unread=True)
        assert qs._backend is orm.backend
        assert qs._mailbox == "INBOX"


@pytest.mark.asyncio
async def test_order_by_async(async_backend, mock_async_session, sample_email):
    sample_email.uid = 5
    d = datetime(2026, 3, 1, tzinfo=timezone.utc)

    async def _messages(*_args, **_kwargs):
        yield sample_email

    mock_async_session.iter_messages = _messages
    backend = async_backend
    backend.uid_search = AsyncMock(
        return_value=MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["5"],
        )
    )
    qs = MessageQuerySet(backend, account_id="acct-test", mailbox="INBOX")
    msg = ImapMessage.from_uid("acct-test", "INBOX", 5, backend=backend)
    msg.date = d

    async def _fetch(_msg_set, *, load_level=LoadLevel.HEADERS, batch_size=50):
        yield msg

    backend.fetch_messages = _fetch
    msgs = await qs.order_by("uid").fetch_all_async()
    assert msgs[0].uid == 5
