"""Async base mailbox service: select, close, check, status."""

from __future__ import annotations

import logging
import time
from typing import Optional

from sage_imap.aio.client import AsyncIMAPClient
from sage_imap.exceptions import (
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
)
from sage_imap.helpers.enums import MailboxStatusItems
from sage_imap.helpers.typings import Mailbox
from sage_imap.services.mailbox.models import (
    MailboxMonitor,
    MailboxOperationResult,
    MailboxValidator,
)

logger = logging.getLogger(__name__)


class AsyncBaseMailboxService:
    def __init__(self, client: AsyncIMAPClient) -> None:
        self.client = client
        self.current_selection: Optional[str] = None
        self.monitor = MailboxMonitor()
        self.validator = MailboxValidator()

    async def select(self, mailbox: Optional[str]) -> MailboxOperationResult:
        start_time = time.time()
        if self.current_selection == mailbox:
            execution_time = time.time() - start_time
            self.monitor.record_operation("select", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="select",
                execution_time=execution_time,
                metadata={"mailbox": mailbox, "already_selected": True},
            )
        try:
            if mailbox:
                self.validator.validate_mailbox(mailbox)
            status, response = await self.client.transport.select(mailbox)
            if status != "OK":
                raise IMAPMailboxSelectionError(f"Failed to select mailbox: {status}")
            self.current_selection = mailbox
            self.client.note_selected_mailbox(mailbox)
            execution_time = time.time() - start_time
            self.monitor.record_operation("select", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="select",
                execution_time=execution_time,
                metadata={"mailbox": mailbox, "response": response},
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("select", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="select",
                execution_time=execution_time,
                error_message=str(e),
            )

    async def close(self) -> MailboxOperationResult:
        start_time = time.time()
        if not self.current_selection:
            return MailboxOperationResult(
                success=True,
                operation="close",
                execution_time=time.time() - start_time,
                metadata={"no_mailbox_selected": True},
            )
        try:
            status, response = await self.client.transport.close()
            if status != "OK":
                raise IMAPMailboxClosureError(f"Failed to close mailbox: {status}")
            closed = self.current_selection
            self.current_selection = None
            execution_time = time.time() - start_time
            self.monitor.record_operation("close", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="close",
                execution_time=execution_time,
                metadata={"closed_mailbox": closed},
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("close", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="close",
                execution_time=execution_time,
                error_message=str(e),
            )

    async def check(self) -> MailboxOperationResult:
        start_time = time.time()
        try:
            status, response = await self.client.transport.check()
            if status != "OK":
                raise IMAPMailboxCheckError(f"Failed to check mailbox: {status}")
            execution_time = time.time() - start_time
            self.monitor.record_operation("check", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="check",
                execution_time=execution_time,
                metadata={"response": response},
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("check", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="check",
                execution_time=execution_time,
                error_message=str(e),
            )

    async def status(
        self, mailbox: Mailbox, items: MailboxStatusItems
    ) -> MailboxOperationResult:
        start_time = time.time()
        try:
            self.validator.validate_mailbox(mailbox)
            status, response = await self.client.transport.status(mailbox, f"({items})")
            if status != "OK":
                raise IMAPMailboxStatusError(f"Failed to get mailbox status: {status}")
            execution_time = time.time() - start_time
            self.monitor.record_operation("status", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="status",
                execution_time=execution_time,
                metadata={
                    "mailbox": mailbox,
                    "items": str(items),
                    "response": response,
                },
            )
        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("status", execution_time, False)
            return MailboxOperationResult(
                success=False,
                operation="status",
                execution_time=execution_time,
                error_message=str(e),
            )
