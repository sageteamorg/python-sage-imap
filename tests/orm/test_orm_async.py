"""Async ORM unit tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.orm.backends.async_ import AsyncImapBackend
from sage_imap.orm.config import LoadLevel
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
            from sage_imap.orm.models.message import ImapMessage

            yield ImapMessage.from_uid("a1", "INBOX", uid, backend=backend)

    backend.fetch_messages = _fetch
    qs = MessageQuerySet(backend, account_id="a1", mailbox="INBOX").with_load_level(
        LoadLevel.HEADERS
    )
    msgs = await qs.fetch_all_async()
    assert len(msgs) == 1
    assert msgs[0].uid == 5
