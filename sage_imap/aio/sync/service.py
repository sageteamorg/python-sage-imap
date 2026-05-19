"""Async incremental sync using shared CONDSTORE parsers."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sage_imap.helpers.enums import MailboxStatusItems
from sage_imap.models.message import MessageSet
from sage_imap.sync.condstore import (
    highest_modseq_from_fields,
    parse_status_sync_fields,
)
from sage_imap.sync.ops import find_changed_uids_via_transport_async
from sage_imap.sync.state import MailboxSyncState

if TYPE_CHECKING:
    from sage_imap.aio.mailbox.operations import AsyncIMAPMailboxUIDService

logger = logging.getLogger(__name__)

_CONDSTORE_STATUS = (
    MailboxStatusItems.MESSAGES,
    MailboxStatusItems.UIDVALIDITY,
    MailboxStatusItems.UIDNEXT,
    MailboxStatusItems.UNSEEN,
    MailboxStatusItems.HIGHESTMODSEQ,
)


class AsyncIMAPSyncService:
    """Async variant of :class:`~sage_imap.sync.service.IMAPSyncService`."""

    def __init__(self, mailbox_service: "AsyncIMAPMailboxUIDService") -> None:
        self.mailbox = mailbox_service
        self.client = mailbox_service.client

    async def supports_condstore(self) -> bool:
        return await self.client.transport.has_capability("CONDSTORE")

    async def capture_state(self, mailbox: str) -> MailboxSyncState:
        items = " ".join(_CONDSTORE_STATUS)
        status, response = await self.client.transport.status(mailbox, f"({items})")
        state = MailboxSyncState(mailbox=mailbox)
        if status != "OK" or not response:
            logger.warning("STATUS failed for sync state on %s: %s", mailbox, status)
            return state
        raw = response[0]
        text = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else str(raw)
        )
        fields = parse_status_sync_fields(text)
        state.uidvalidity = fields.get("UIDVALIDITY")
        state.uidnext = fields.get("UIDNEXT")
        state.message_count = fields.get("MESSAGES")
        state.unseen_count = fields.get("UNSEEN")
        state.highest_modseq = highest_modseq_from_fields(fields)
        state.touch()
        return state

    async def find_changed_uids(self, state: MailboxSyncState) -> MessageSet:
        return await find_changed_uids_via_transport_async(self.client.transport, state)
