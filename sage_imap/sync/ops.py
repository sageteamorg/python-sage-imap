"""Shared CONDSTORE / UID search helpers for sync and async sync services."""

from __future__ import annotations

import logging
from typing import List, Optional, Protocol

from sage_imap.models.message import MessageSet
from sage_imap.protocols.imap_transport import IMAPResponse
from sage_imap.sync.condstore import build_changedsince_criteria
from sage_imap.sync.state import MailboxSyncState

logger = logging.getLogger(__name__)


class SearchTransport(Protocol):
    def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse: ...

    def has_capability(self, name: str) -> bool: ...


def uids_from_search_response(data: list) -> List[int]:
    """Parse UID list from imaplib-style SEARCH response data."""
    uids: List[int] = []
    if not data or not data[0]:
        return uids
    raw_ids = data[0]
    if isinstance(raw_ids, bytes):
        raw_ids = raw_ids.decode("ascii", errors="replace")
    for part in str(raw_ids).split():
        if part.isdigit():
            uids.append(int(part))
    return uids


def find_changed_uids_via_transport(
    transport: SearchTransport,
    previous: MailboxSyncState,
    *,
    charset: Optional[str] = None,
) -> MessageSet:
    """
    Return UIDs changed since ``previous.highest_modseq`` using CONDSTORE CHANGEDSINCE.

    Mirrors :meth:`~sage_imap.sync.service.IMAPSyncService.find_changed_uids`.
    """
    if previous.highest_modseq is None:
        logger.info(
            "No prior MODSEQ; incremental search skipped for %s", previous.mailbox
        )
        return MessageSet.empty(mailbox=previous.mailbox)

    if not transport.has_capability("CONDSTORE"):
        logger.warning("Server does not advertise CONDSTORE")
        return MessageSet.empty(mailbox=previous.mailbox)

    criteria = build_changedsince_criteria(previous.highest_modseq)
    status, data = transport.search(criteria, charset=charset, use_uid=True)
    if status != "OK":
        return MessageSet.empty(mailbox=previous.mailbox)
    uids = uids_from_search_response(data)
    return MessageSet.from_uids(uids, mailbox=previous.mailbox)


class AsyncSearchTransport(Protocol):
    async def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse: ...

    async def has_capability(self, name: str) -> bool: ...


async def find_changed_uids_via_transport_async(
    transport: AsyncSearchTransport,
    previous: MailboxSyncState,
    *,
    charset: Optional[str] = None,
) -> MessageSet:
    """Async variant of :func:`find_changed_uids_via_transport`."""
    if previous.highest_modseq is None:
        logger.info(
            "No prior MODSEQ; incremental search skipped for %s", previous.mailbox
        )
        return MessageSet.empty(mailbox=previous.mailbox)

    if not await transport.has_capability("CONDSTORE"):
        logger.warning("Server does not advertise CONDSTORE")
        return MessageSet.empty(mailbox=previous.mailbox)

    criteria = build_changedsince_criteria(previous.highest_modseq)
    status, data = await transport.search(criteria, charset=charset, use_uid=True)
    if status != "OK":
        return MessageSet.empty(mailbox=previous.mailbox)
    uids = uids_from_search_response(data)
    return MessageSet.from_uids(uids, mailbox=previous.mailbox)
