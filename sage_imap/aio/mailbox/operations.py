"""Async UID mailbox operations."""

from __future__ import annotations

import logging
import time
from typing import AsyncIterator, Optional

from sage_imap.aio.client import AsyncIMAPClient
from sage_imap.aio.mailbox.base import AsyncBaseMailboxService
from sage_imap.decorators import async_mailbox_selection_required
from sage_imap.exceptions import IMAPMailboxError
from sage_imap.helpers.enums import Flag, FlagCommand, MessagePart
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.typings import Mailbox
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.mailbox import _ops as mailbox_ops
from sage_imap.services.mailbox.models import MailboxOperationResult

logger = logging.getLogger(__name__)


class AsyncIMAPMailboxUIDService(AsyncBaseMailboxService):
    """Async UID mailbox service mirroring :class:`~sage_imap.services.mailbox.operations.IMAPMailboxUIDService`."""

    def __init__(self, client: AsyncIMAPClient) -> None:
        super().__init__(client)
        self.bulk_operation_batch_size = 100
        self._sync_service = None

    @async_mailbox_selection_required
    async def uid_search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = None
    ) -> MailboxOperationResult:
        return await mailbox_ops.uid_search_via_transport_async(
            self.client.transport,
            criteria,
            charset=charset,
            monitor=self.monitor,
        )

    async def create_message_set_from_search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = None
    ) -> MessageSet:
        search_result = await self.uid_search(criteria, charset)
        if not search_result.success:
            raise IMAPMailboxError(f"UID search failed: {search_result.error_message}")
        if not search_result.affected_messages:
            raise IMAPMailboxError("No messages found matching search criteria")
        uids = [int(uid) for uid in search_result.affected_messages]
        return MessageSet.from_uids(uids, mailbox=self.current_selection)

    async def iter_uid_fetch(
        self,
        msg_set: MessageSet,
        msg_part: MessagePart = MessagePart.RFC822,
        *,
        parse_mode: ParseMode = ParseMode.FULL,
        batch_size: int = 50,
    ) -> AsyncIterator[EmailMessage]:
        self.validator.validate_message_set(
            msg_set, expected_mailbox=self.current_selection
        )
        async for msg in mailbox_ops.iter_uid_fetch_via_transport_async(
            self.client.transport,
            msg_set,
            msg_part,
            parse_mode=parse_mode,
            batch_size=batch_size,
            mailbox=self.current_selection,
        ):
            yield msg

    @async_mailbox_selection_required
    async def uid_move(
        self, msg_set: MessageSet, destination_mailbox: Mailbox
    ) -> MailboxOperationResult:
        start_time = time.time()
        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(destination_mailbox)
            status, move_meta = await self.client.transport.move(
                msg_set, destination_mailbox
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_move", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_move",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to move messages: {status}",
                    metadata=move_meta,
                )
            check_result = await self.check()
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_move", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="uid_move",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "destination_mailbox": destination_mailbox,
                    "check_result": check_result.success,
                    **move_meta,
                },
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_move", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="uid_move",
                execution_time=execution_time,
                error_message=str(e),
            )

    @async_mailbox_selection_required
    async def uid_trash(
        self, msg_set: MessageSet, trash_mailbox: Mailbox
    ) -> MailboxOperationResult:
        start_time = time.time()
        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)
            status, _ = await self.client.transport.store_flags(
                msg_set, FlagCommand.ADD, Flag.DELETED
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_trash", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_trash",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to mark messages for deletion: {status}",
                )
            move_result = await self.uid_move(msg_set, trash_mailbox)
            execution_time = time.time() - start_time
            if not move_result.success:
                self.monitor.record_operation("uid_trash", execution_time, False)
                return move_result
            self.monitor.record_operation("uid_trash", execution_time)
            move_result.operation = "uid_trash"
            return move_result
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_trash", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="uid_trash",
                execution_time=execution_time,
                error_message=str(e),
            )

    @property
    def sync(self):
        if self._sync_service is None:
            from sage_imap.aio.sync.service import AsyncIMAPSyncService

            self._sync_service = AsyncIMAPSyncService(self)
        return self._sync_service
