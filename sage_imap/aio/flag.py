"""Async flag operations service."""

from __future__ import annotations

import logging
import time

from sage_imap.decorators import async_mailbox_selection_required
from sage_imap.exceptions import IMAPFlagOperationError
from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet
from sage_imap.services.flag import FlagOperationResult

logger = logging.getLogger(__name__)


class AsyncIMAPFlagService:
    """Async flag service mirroring :class:`~sage_imap.services.flag.IMAPFlagService`."""

    def __init__(self, mailbox) -> None:
        self.mailbox = mailbox

    @async_mailbox_selection_required
    async def add_flag(self, msg_ids: MessageSet, flag: Flag) -> FlagOperationResult:
        return await self._store(msg_ids, FlagCommand.ADD, flag)

    @async_mailbox_selection_required
    async def remove_flag(self, msg_ids: MessageSet, flag: Flag) -> FlagOperationResult:
        return await self._store(msg_ids, FlagCommand.REMOVE, flag)

    async def _store(
        self, msg_ids: MessageSet, command: FlagCommand, flag: Flag
    ) -> FlagOperationResult:
        start = time.time()
        try:
            status, _ = await self.mailbox.client.transport.store_flags(
                msg_ids, command, flag
            )
            elapsed = time.time() - start
            if status != "OK":
                return FlagOperationResult(
                    success=False,
                    message_count=len(msg_ids.msg_ids),
                    flags_modified=[flag],
                    operation_time=elapsed,
                    error_message=f"STORE failed: {status}",
                )
            return FlagOperationResult(
                success=True,
                message_count=len(msg_ids.msg_ids),
                flags_modified=[flag],
                operation_time=elapsed,
            )
        except Exception as e:
            elapsed = time.time() - start
            raise IMAPFlagOperationError(str(e)) from e
