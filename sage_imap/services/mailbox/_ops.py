"""Shared mailbox read-path helpers (sync transport; no asyncio)."""

from __future__ import annotations

import logging
import time
from typing import Any, AsyncIterator, Iterator, Optional, Protocol, Union

from sage_imap.exceptions import IMAPSearchError
from sage_imap.helpers.enums import MessagePart
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.fetch_parser import iter_messages_from_fetch
from sage_imap.models.message import MessageSet, MessageSetBatchIterator
from sage_imap.protocols.imap_transport import IMAPResponse
from sage_imap.services.mailbox.models import MailboxOperationResult

logger = logging.getLogger(__name__)


class SearchTransport(Protocol):
    def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse: ...


class FetchTransport(Protocol):
    def fetch(
        self, msg_set: MessageSet, parts: str, use_uid: Optional[bool] = None
    ) -> IMAPResponse: ...


class AsyncSearchTransport(Protocol):
    async def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse: ...


class AsyncFetchTransport(Protocol):
    async def fetch(
        self, msg_set: MessageSet, parts: str, use_uid: Optional[bool] = None
    ) -> IMAPResponse: ...


def uid_search_via_transport(
    transport: SearchTransport,
    criteria: Union[IMAPSearchCriteria, str],
    *,
    charset: Optional[str] = None,
    monitor: Any = None,
) -> MailboxOperationResult:
    """Run UID SEARCH and return :class:`MailboxOperationResult`."""
    start_time = time.time()
    criteria_str = str(criteria)
    try:
        logger.debug("Searching emails with UID criteria: %s", criteria_str)
        status, data = transport.search(criteria_str, charset, use_uid=True)
        if status != "OK":
            execution_time = time.time() - start_time
            if monitor:
                monitor.record_operation("uid_search", execution_time, False)
            logger.error("Failed to search emails: %s", data)
            raise IMAPSearchError(f"Failed to search emails: {data}")

        msg_ids = data[0].split() if data and data[0] else []
        msg_id_strs = [
            msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
            for msg_id in msg_ids
        ]
        execution_time = time.time() - start_time
        if monitor:
            monitor.record_operation("uid_search", execution_time)
        logger.info("UID search successful, found %d emails.", len(msg_id_strs))
        return MailboxOperationResult(
            success=True,
            operation="uid_search",
            message_count=len(msg_id_strs),
            affected_messages=msg_id_strs,
            execution_time=execution_time,
            metadata={"criteria": criteria_str, "charset": charset},
        )
    except Exception as e:
        execution_time = time.time() - start_time
        if monitor:
            monitor.record_operation("uid_search", execution_time, False)
        logger.error("Exception occurred during UID search: %s", e)
        return MailboxOperationResult(
            success=False,
            operation="uid_search",
            execution_time=execution_time,
            error_message=str(e),
        )


def iter_uid_fetch_via_transport(
    transport: FetchTransport,
    msg_set: MessageSet,
    msg_part: MessagePart = MessagePart.RFC822,
    *,
    parse_mode: ParseMode = ParseMode.FULL,
    batch_size: int = 50,
    mailbox: Optional[str] = None,
) -> Iterator[EmailMessage]:
    """Stream UID FETCH results using batched :class:`MessageSetBatchIterator`."""
    if msg_set.is_empty():
        return

    fetch_spec = f"({msg_part} FLAGS UID)"
    for batch in MessageSetBatchIterator(msg_set, batch_size):
        status, data = transport.fetch(batch, fetch_spec)
        if status != "OK":
            logger.warning("FETCH batch failed for %s: %s", batch.msg_ids, status)
            continue
        yield from iter_messages_from_fetch(
            data,
            parse_mode=parse_mode,
            mailbox=mailbox,
            is_uid_fetch=True,
        )


async def uid_search_via_transport_async(
    transport: AsyncSearchTransport,
    criteria: Union[IMAPSearchCriteria, str],
    *,
    charset: Optional[str] = None,
    monitor: Any = None,
) -> MailboxOperationResult:
    """Async UID SEARCH via transport; same result shape as :func:`uid_search_via_transport`."""
    start_time = time.time()
    criteria_str = str(criteria)
    try:
        logger.debug("Searching emails with UID criteria: %s", criteria_str)
        status, data = await transport.search(criteria_str, charset, use_uid=True)
        if status != "OK":
            execution_time = time.time() - start_time
            if monitor:
                monitor.record_operation("uid_search", execution_time, False)
            logger.error("Failed to search emails: %s", data)
            raise IMAPSearchError(f"Failed to search emails: {data}")

        msg_ids = data[0].split() if data and data[0] else []
        msg_id_strs = [
            msg_id.decode("utf-8") if isinstance(msg_id, bytes) else str(msg_id)
            for msg_id in msg_ids
        ]
        execution_time = time.time() - start_time
        if monitor:
            monitor.record_operation("uid_search", execution_time)
        logger.info("UID search successful, found %d emails.", len(msg_id_strs))
        return MailboxOperationResult(
            success=True,
            operation="uid_search",
            message_count=len(msg_id_strs),
            affected_messages=msg_id_strs,
            execution_time=execution_time,
            metadata={"criteria": criteria_str, "charset": charset},
        )
    except Exception as e:
        execution_time = time.time() - start_time
        if monitor:
            monitor.record_operation("uid_search", execution_time, False)
        logger.error("Exception occurred during UID search: %s", e)
        return MailboxOperationResult(
            success=False,
            operation="uid_search",
            execution_time=execution_time,
            error_message=str(e),
        )


async def iter_uid_fetch_via_transport_async(
    transport: AsyncFetchTransport,
    msg_set: MessageSet,
    msg_part: MessagePart = MessagePart.RFC822,
    *,
    parse_mode: ParseMode = ParseMode.FULL,
    batch_size: int = 50,
    mailbox: Optional[str] = None,
) -> AsyncIterator[EmailMessage]:
    """Async UID FETCH batches; same parsing as :func:`iter_uid_fetch_via_transport`."""
    if msg_set.is_empty():
        return

    fetch_spec = f"({msg_part} FLAGS UID)"
    for batch in MessageSetBatchIterator(msg_set, batch_size):
        status, data = await transport.fetch(batch, fetch_spec)
        if status != "OK":
            logger.warning("FETCH batch failed for %s: %s", batch.msg_ids, status)
            continue
        for msg in iter_messages_from_fetch(
            data,
            parse_mode=parse_mode,
            mailbox=mailbox,
            is_uid_fetch=True,
        ):
            yield msg
