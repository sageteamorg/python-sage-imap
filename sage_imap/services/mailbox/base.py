"""Base mailbox service: select, close, check, status."""

import logging
import time
from typing import Any, Dict, Optional

from sage_imap.exceptions import (
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
)
from sage_imap.helpers.enums import MailboxStatusItems
from sage_imap.helpers.typings import Mailbox
from sage_imap.services.client import IMAPClient
from sage_imap.services.mailbox.models import (
    MailboxMonitor,
    MailboxOperationResult,
    MailboxValidator,
)

logger = logging.getLogger(__name__)


class BaseMailboxService:
    def __init__(self, client: IMAPClient) -> None:
        self.client = client
        self.current_selection: Optional[str] = None
        self.monitor = MailboxMonitor()
        self.validator = MailboxValidator()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def select(self, mailbox: Optional[str]) -> MailboxOperationResult:
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
            status, response = self.client.transport.select(mailbox)
            if status != "OK":
                raise IMAPMailboxSelectionError(f"Failed to select mailbox: {status}")
            self.current_selection = mailbox
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

    def close(self) -> MailboxOperationResult:
        start_time = time.time()
        if not self.current_selection:
            return MailboxOperationResult(
                success=True,
                operation="close",
                execution_time=time.time() - start_time,
                metadata={"no_mailbox_selected": True},
            )
        try:
            status, response = self.client.transport.close()
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

    def check(self) -> MailboxOperationResult:
        start_time = time.time()
        try:
            status, response = self.client.transport.check()
            if status != "OK":
                raise IMAPMailboxCheckError(f"IMAP CHECK command failed: {status}")
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

    def status(
        self, mailbox: Mailbox, *status_items: MailboxStatusItems
    ) -> MailboxOperationResult:
        start_time = time.time()
        try:
            self.validator.validate_mailbox(mailbox)
            items = " ".join(item.value for item in status_items)
            status_items_str = f"({items})"
            status, response = self.client.transport.status(mailbox, status_items_str)
            if status != "OK":
                raise IMAPMailboxStatusError(
                    f"Failed to get status for mailbox: {mailbox}"
                )
            execution_time = time.time() - start_time
            self.monitor.record_operation("status", execution_time)
            return MailboxOperationResult(
                success=True,
                operation="status",
                execution_time=execution_time,
                metadata={"mailbox": mailbox, "status_response": response},
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

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        return self.monitor.get_statistics()
