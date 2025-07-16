import logging
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from sage_imap.decorators import mailbox_selection_required
from sage_imap.exceptions import (
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxError,
    IMAPMailboxFetchError,
    IMAPMailboxSaveSentError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
    IMAPMailboxUploadError,
    IMAPSearchError,
)
from sage_imap.helpers.enums import Flag, FlagCommand, MailboxStatusItems, MessagePart
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.typings import Mailbox, RawEmail
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient

logger = logging.getLogger(__name__)

__all__ = [
    "IMAPMailboxService",
    "IMAPMailboxUIDService",
    "MailboxOperationResult",
    "BulkOperationResult",
]


@dataclass
class MailboxOperationResult:
    """Result of a mailbox operation with detailed feedback."""

    success: bool
    operation: str
    message_count: int = 0
    affected_messages: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.message_count == 0 and self.affected_messages:
            self.message_count = len(self.affected_messages)


@dataclass
class BulkOperationResult:
    """Result of bulk operations with detailed statistics."""

    operation: str
    total_messages: int
    successful_messages: int
    failed_messages: int
    execution_time: float
    batch_size: int
    batches_processed: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def success_rate(self) -> float:
        """Calculate success rate as a percentage."""
        if self.total_messages == 0:
            return 0.0
        return (self.successful_messages / self.total_messages) * 100

    @property
    def is_successful(self) -> bool:
        """Check if operation was successful (100% success rate)."""
        return self.success_rate == 100.0


@dataclass
class MailboxStatistics:
    """Comprehensive mailbox statistics."""

    total_messages: int
    unread_messages: int
    flagged_messages: int
    recent_messages: int
    size_bytes: int
    oldest_message_date: Optional[datetime] = None
    newest_message_date: Optional[datetime] = None
    message_size_distribution: Dict[str, int] = field(default_factory=dict)
    flag_distribution: Dict[str, int] = field(default_factory=dict)
    sender_distribution: Dict[str, int] = field(default_factory=dict)


class MailboxValidator:
    """Validation utilities for mailbox operations."""

    @staticmethod
    def validate_message_set(msg_set: MessageSet) -> bool:
        """Validate MessageSet object."""
        if not isinstance(msg_set, MessageSet):
            raise IMAPMailboxError("msg_set must be a MessageSet instance")

        if not msg_set.msg_ids:
            raise IMAPMailboxError("MessageSet cannot be empty")

        # Validate message IDs format
        for msg_id in msg_set.msg_ids:
            if not isinstance(msg_id, (str, int)):
                raise IMAPMailboxError(f"Invalid message ID format: {msg_id}")

        return True

    @staticmethod
    def validate_mailbox(mailbox: Mailbox) -> bool:
        """Validate mailbox name."""
        if not mailbox:
            raise IMAPMailboxSelectionError("Mailbox name cannot be empty")

        if not isinstance(mailbox, str):
            raise IMAPMailboxSelectionError("Mailbox must be a string")

        # Check for potentially dangerous characters
        dangerous_chars = ["..", "/", "\\", "\0"]
        for char in dangerous_chars:
            if char in mailbox:
                raise IMAPMailboxSelectionError(
                    f"Mailbox name contains dangerous character: {char}"
                )

        return True

    @staticmethod
    def validate_email_data(emails: Union[EmailIterator, List[EmailMessage]]) -> bool:
        """Validate email data for upload operations."""
        if not isinstance(emails, (list, EmailIterator)):
            raise IMAPMailboxUploadError("emails must be a list or an EmailIterator")

        if isinstance(emails, list) and len(emails) == 0:
            raise IMAPMailboxUploadError("Email list cannot be empty")

        return True


class MailboxMonitor:
    """Monitoring and metrics for mailbox operations."""

    def __init__(self):
        self.operation_counts = defaultdict(int)
        self.operation_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.last_operations = []
        self.start_time = time.time()

    def record_operation(
        self, operation: str, execution_time: float, success: bool = True
    ):
        """Record an operation for monitoring."""
        self.operation_counts[operation] += 1
        self.operation_times[operation].append(execution_time)

        if not success:
            self.error_counts[operation] += 1

        # Keep last 100 operations
        self.last_operations.append(
            {
                "operation": operation,
                "timestamp": datetime.now(),
                "execution_time": execution_time,
                "success": success,
            }
        )

        if len(self.last_operations) > 100:
            self.last_operations.pop(0)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive operation statistics."""
        stats = {
            "uptime": time.time() - self.start_time,
            "total_operations": sum(self.operation_counts.values()),
            "operations_by_type": dict(self.operation_counts),
            "error_counts": dict(self.error_counts),
            "average_times": {},
            "recent_operations": self.last_operations[-10:],
        }

        # Calculate average execution times
        for operation, times in self.operation_times.items():
            if times:
                stats["average_times"][operation] = sum(times) / len(times)

        return stats


class BaseMailboxService:
    def __init__(self, client: IMAPClient) -> None:
        self.client: IMAPClient = client
        self.current_selection: Optional[str] = None
        self.monitor = MailboxMonitor()
        self.validator = MailboxValidator()

    def __enter__(self):
        logger.debug("Entering IMAPMailboxService context manager.")
        return self

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[Any],
    ) -> None:
        logger.debug("Exiting IMAPMailboxService context manager.")
        self.close()

    def select(self, mailbox: Optional[str]) -> MailboxOperationResult:
        """Select a mailbox with enhanced error handling and monitoring."""
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

            logger.debug("Selecting mailbox: %s", mailbox)
            status, response = self.client.select(mailbox)

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("select", execution_time, False)
                logger.error("Failed to select mailbox: %s", status)
                raise IMAPMailboxSelectionError(f"Failed to select mailbox: {status}")

            self.current_selection = mailbox
            execution_time = time.time() - start_time
            self.monitor.record_operation("select", execution_time)
            logger.info("Mailbox selected: %s", mailbox)

            return MailboxOperationResult(
                success=True,
                operation="select",
                execution_time=execution_time,
                metadata={"mailbox": mailbox, "response": response},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("select", execution_time, False)
            logger.error("Failed to select mailbox: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="select",
                execution_time=execution_time,
                error_message=str(e),
            )

    def close(self) -> MailboxOperationResult:
        """Close current mailbox with enhanced monitoring."""
        start_time = time.time()

        if not self.current_selection:
            execution_time = time.time() - start_time
            return MailboxOperationResult(
                success=True,
                operation="close",
                execution_time=execution_time,
                metadata={"no_mailbox_selected": True},
            )

        try:
            logger.debug("Closing mailbox: %s", self.current_selection)
            status, response = self.client.close()

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("close", execution_time, False)
                logger.error("Failed to close mailbox: %s", status)
                raise IMAPMailboxClosureError(f"Failed to close mailbox: {status}")

            closed_mailbox = self.current_selection
            self.current_selection = None
            execution_time = time.time() - start_time
            self.monitor.record_operation("close", execution_time)
            logger.info("Mailbox closed: %s", closed_mailbox)

            return MailboxOperationResult(
                success=True,
                operation="close",
                execution_time=execution_time,
                metadata={"closed_mailbox": closed_mailbox},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("close", execution_time, False)
            logger.error("Failed to close mailbox: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="close",
                execution_time=execution_time,
                error_message=str(e),
            )

    def check(self) -> MailboxOperationResult:
        """Perform mailbox check with enhanced monitoring."""
        start_time = time.time()

        try:
            logger.debug("Requesting checkpoint for the currently selected mailbox.")
            status, response = self.client.check()

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("check", execution_time, False)
                logger.error("Failed to perform CHECK command: %s", status)
                raise IMAPMailboxCheckError(f"IMAP CHECK command failed: {status}")

            execution_time = time.time() - start_time
            self.monitor.record_operation("check", execution_time)
            logger.info("IMAP CHECK command successful.")

            return MailboxOperationResult(
                success=True,
                operation="check",
                execution_time=execution_time,
                metadata={"response": response},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("check", execution_time, False)
            logger.error("Exception occurred during CHECK command: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="check",
                execution_time=execution_time,
                error_message=str(e),
            )

    def status(
        self, mailbox: Mailbox, *status_items: MailboxStatusItems
    ) -> MailboxOperationResult:
        """Get mailbox status with enhanced validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_mailbox(mailbox)

            logger.debug("Getting status for mailbox: %s", mailbox)
            status_items_str = self.__combine_status_items(*status_items)
            status, response = self.client.status(mailbox, status_items_str)

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("status", execution_time, False)
                logger.error("Failed to get status for mailbox: %s", mailbox)
                raise IMAPMailboxStatusError(
                    f"Failed to get status for mailbox: {mailbox}"
                )

            execution_time = time.time() - start_time
            self.monitor.record_operation("status", execution_time)
            logger.info("Status for mailbox %s: %s", mailbox, response)

            return MailboxOperationResult(
                success=True,
                operation="status",
                execution_time=execution_time,
                metadata={"mailbox": mailbox, "status_response": response},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("status", execution_time, False)
            logger.error(
                "Exception occurred while getting status for mailbox %s: %s", mailbox, e
            )
            return MailboxOperationResult(
                success=False,
                operation="status",
                execution_time=execution_time,
                error_message=str(e),
            )

    def __combine_status_items(self, *status_items: MailboxStatusItems) -> str:
        items = " ".join(item.value for item in status_items)
        return f"({items})"

    def get_monitoring_statistics(self) -> Dict[str, Any]:
        """Get comprehensive monitoring statistics."""
        return self.monitor.get_statistics()


class IMAPMailboxService(BaseMailboxService):
    """Enhanced IMAP Mailbox Service with comprehensive operations and monitoring."""

    def __init__(self, client: IMAPClient):
        super().__init__(client)
        self.bulk_operation_batch_size = 100
        self.max_concurrent_operations = 5

    @mailbox_selection_required
    def search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = "UTF-8"
    ) -> MailboxOperationResult:
        """Enhanced search with detailed result information."""
        start_time = time.time()

        try:
            logger.debug("Searching emails with criteria: %s", criteria)
            status, data = self.client.search(None, criteria)

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("search", execution_time, False)
                logger.error("Failed to search emails: %s", data)
                raise IMAPSearchError(f"Failed to search emails: {data}")

            msg_ids = data[0].split()
            msg_id_strs = [msg_id.decode("utf-8") for msg_id in msg_ids]

            execution_time = time.time() - start_time
            self.monitor.record_operation("search", execution_time)
            logger.info("Search successful, found %d emails.", len(msg_id_strs))

            return MailboxOperationResult(
                success=True,
                operation="search",
                message_count=len(msg_id_strs),
                affected_messages=msg_id_strs,
                execution_time=execution_time,
                metadata={"criteria": str(criteria), "charset": charset},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("search", execution_time, False)
            logger.error("Exception occurred during search: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="search",
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def trash(
        self, msg_set: MessageSet, trash_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced trash operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)

            logger.debug(
                "Marking messages %s for deletion and moving to %s.",
                msg_set.msg_ids,
                trash_mailbox,
            )

            # Mark the messages as deleted
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.ADD, Flag.DELETED
            )

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("trash", execution_time, False)
                logger.error(
                    "Failed to mark messages %s for deletion: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="trash",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to mark messages for deletion: {status}",
                )

            # Move the messages to the trash folder
            move_result = self.move(msg_set, trash_mailbox)
            if not move_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("trash", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="trash",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to move messages to trash: {move_result.error_message}",
                )

            check_result = self.check()
            execution_time = time.time() - start_time
            self.monitor.record_operation("trash", execution_time)

            return MailboxOperationResult(
                success=True,
                operation="trash",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("trash", execution_time, False)
            logger.error(
                "Exception occurred while trashing messages %s: %s", msg_set.msg_ids, e
            )
            return MailboxOperationResult(
                success=False,
                operation="trash",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    def delete(
        self, msg_set: MessageSet, trash_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced delete operation with comprehensive monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)

            logger.debug("Deleting messages %s permanently.", msg_set.msg_ids)

            # First trash the messages
            trash_result = self.trash(msg_set, trash_mailbox)
            if not trash_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("delete", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="delete",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to trash messages: {trash_result.error_message}",
                )

            # Permanently remove messages marked as deleted
            self.client.expunge()
            check_result = self.check()

            execution_time = time.time() - start_time
            self.monitor.record_operation("delete", execution_time)
            logger.info("Messages %s permanently deleted.", msg_set.msg_ids)

            return MailboxOperationResult(
                success=True,
                operation="delete",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("delete", execution_time, False)
            logger.error(
                "Exception occurred while deleting messages %s permanently: %s",
                msg_set.msg_ids,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="delete",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def move(
        self, msg_set: MessageSet, destination_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced move operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(destination_mailbox)

            logger.debug(
                "Moving messages %s to mailbox %s.",
                msg_set.msg_ids,
                destination_mailbox,
            )

            # Copy messages to destination
            status, _ = self.client.copy(msg_set.msg_ids, destination_mailbox)
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("move", execution_time, False)
                logger.error(
                    "Failed to copy messages %s to mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="move",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to copy messages to destination: {status}",
                )

            # Mark the messages as deleted in the current mailbox
            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.ADD, Flag.DELETED
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("move", execution_time, False)
                logger.error(
                    "Failed to mark messages %s for deletion: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="move",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to mark messages for deletion: {status}",
                    warnings=["Messages copied but not removed from source"],
                )

            # Permanently remove messages marked as deleted from the source mailbox
            self.client.expunge()
            check_result = self.check()

            execution_time = time.time() - start_time
            self.monitor.record_operation("move", execution_time)
            logger.info(
                "Messages %s moved to mailbox %s.", msg_set.msg_ids, destination_mailbox
            )

            return MailboxOperationResult(
                success=True,
                operation="move",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "destination_mailbox": destination_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("move", execution_time, False)
            logger.error(
                "Exception occurred while moving messages %s to mailbox %s: %s",
                msg_set.msg_ids,
                destination_mailbox,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="move",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    def restore(
        self, msg_set: MessageSet, trash_mailbox: Mailbox, safe_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced restore operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)
            self.validator.validate_mailbox(safe_mailbox)

            logger.debug(
                "Restoring messages %s from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )

            # Select trash mailbox
            select_result = self.select(trash_mailbox)
            if not select_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to select trash mailbox: {select_result.error_message}",
                )

            # Move messages from trash to safe mailbox
            move_result = self.move(msg_set, safe_mailbox)
            if not move_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to move messages: {move_result.error_message}",
                )

            # Select safe mailbox and remove deleted flag
            select_result = self.select(safe_mailbox)
            if not select_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to select safe mailbox: {select_result.error_message}",
                    warnings=["Messages moved but deleted flag not removed"],
                )

            status, _ = self.client.store(
                msg_set.msg_ids, FlagCommand.REMOVE, Flag.DELETED
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("restore", execution_time, False)
                logger.error(
                    "Failed to remove \\Deleted flag from messages %s: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to remove deleted flag: {status}",
                    warnings=["Messages moved but deleted flag not removed"],
                )

            check_result = self.check()
            execution_time = time.time() - start_time
            self.monitor.record_operation("restore", execution_time)
            logger.info(
                "Messages %s restored from trash to folder %s.",
                msg_set.msg_ids,
                safe_mailbox,
            )

            return MailboxOperationResult(
                success=True,
                operation="restore",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "safe_mailbox": safe_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("restore", execution_time, False)
            logger.error(
                "Exception occurred while restoring messages %s: %s", msg_set.msg_ids, e
            )
            return MailboxOperationResult(
                success=False,
                operation="restore",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def fetch(
        self, msg_set: MessageSet, msg_part: MessagePart
    ) -> MailboxOperationResult:
        """Enhanced fetch operation with comprehensive validation and EmailMessage integration."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)

            logger.debug(
                "Fetching message part %s for messages %s.", msg_part, msg_set.msg_ids
            )
            status, data = self.client.fetch(msg_set.msg_ids, f"({msg_part} FLAGS UID)")

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("fetch", execution_time, False)
                logger.error("Failed to fetch message part %s: %s", msg_part, status)
                raise IMAPMailboxFetchError(f"Failed to fetch message part: {status}")

            fetched_data = []
            processed_count = 0

            for response_part in data:
                if isinstance(response_part, tuple) and len(response_part) == 2:
                    try:
                        flag_data = response_part[0]
                        msg_data = response_part[1]

                        # Skip if msg_data is not bytes or is empty
                        if not isinstance(msg_data, bytes) or len(msg_data) == 0:
                            continue

                        # Create EmailMessage from bytes
                        email_message = EmailMessage.read_from_eml_bytes(msg_data)

                        # Extract and set flags
                        if isinstance(flag_data, bytes):
                            flags = EmailMessage.extract_flags(flag_data)
                            email_message.flags = flags

                            # Extract sequence number and UID
                            flag_data_str = flag_data.decode("utf-8", errors="ignore")
                            match = re.search(
                                r"(\d+) \(.*FLAGS \([^\)]*\) UID (\d+)", flag_data_str
                            )

                            if match:
                                email_message.sequence_number = int(match.group(1))
                                email_message.uid = int(match.group(2))

                        # Set additional metadata
                        email_message.size = len(msg_data)
                        email_message.mailbox = self.current_selection

                        fetched_data.append(email_message)
                        processed_count += 1

                    except Exception as e:
                        logger.warning("Failed to process message in fetch: %s", e)
                        continue
                else:
                    # Skip non-tuple responses or malformed responses
                    logger.debug("Skipping non-tuple response: %s", type(response_part))

            execution_time = time.time() - start_time
            self.monitor.record_operation("fetch", execution_time)
            logger.info("Fetched %d messages successfully.", processed_count)

            return MailboxOperationResult(
                success=True,
                operation="fetch",
                message_count=processed_count,
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "message_part": str(msg_part),
                    "fetched_messages": fetched_data,
                    "requested_count": len(msg_set.msg_ids),
                    "processed_count": processed_count,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("fetch", execution_time, False)
            logger.error("Exception occurred while fetching messages: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="fetch",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def save_sent(
        self,
        sent_mailbox: Mailbox,
        raw: RawEmail,
        flags: Flag = None,
        date_time: str = None,
    ) -> MailboxOperationResult:
        """Enhanced save sent operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_mailbox(sent_mailbox)

            if not isinstance(raw, (str, bytes)):
                execution_time = time.time() - start_time
                self.monitor.record_operation("save_sent", execution_time, False)
                logger.error("Invalid raw email type: %s", type(raw))
                raise IMAPMailboxSaveSentError(f"Invalid raw email type: {type(raw)}")

            logger.debug("Saving sent email to folder: %s", sent_mailbox)

            # Append the email to the specified folder
            status, response = self.client.append(sent_mailbox, flags, date_time, raw)

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("save_sent", execution_time, False)
                logger.error("Failed to save sent email to folder: %s", status)
                raise IMAPMailboxSaveSentError(f"Failed to save sent email: {status}")

            execution_time = time.time() - start_time
            self.monitor.record_operation("save_sent", execution_time)
            logger.info("Sent email saved to folder: %s", sent_mailbox)

            return MailboxOperationResult(
                success=True,
                operation="save_sent",
                message_count=1,
                execution_time=execution_time,
                metadata={
                    "sent_mailbox": sent_mailbox,
                    "flags": str(flags) if flags else None,
                    "date_time": date_time,
                    "email_size": len(raw) if isinstance(raw, (str, bytes)) else 0,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("save_sent", execution_time, False)
            logger.error("Exception occurred while saving sent email: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="save_sent",
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def upload_eml(
        self,
        emails: Union[EmailIterator, List[EmailMessage]],
        flags: Flag,
        mailbox: Mailbox,
    ) -> BulkOperationResult:
        """Enhanced bulk upload operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_email_data(emails)
            self.validator.validate_mailbox(mailbox)

            email_list = list(emails) if isinstance(emails, EmailIterator) else emails
            total_count = len(email_list)

            logger.debug("Uploading %d .eml files to mailbox: %s", total_count, mailbox)

            successful_count = 0
            failed_count = 0
            errors = []

            # Process in batches
            batch_size = self.bulk_operation_batch_size
            batches_processed = 0

            for i in range(0, total_count, batch_size):
                batch = email_list[i : i + batch_size]
                batches_processed += 1

                for email_message in batch:
                    try:
                        if not isinstance(email_message, EmailMessage):
                            raise IMAPMailboxUploadError(
                                "Each email must be an EmailMessage instance"
                            )

                        if not hasattr(email_message, "date") or not hasattr(
                            email_message, "raw"
                        ):
                            raise IMAPMailboxUploadError(
                                "Each email must have 'date' and 'raw' attributes"
                            )

                        status, _ = self.client.append(
                            mailbox, flags, email_message.date, email_message.raw
                        )

                        if status != "OK":
                            failed_count += 1
                            error_msg = f"Failed to upload email {getattr(email_message, 'subject', 'Unknown')}: {status}"
                            errors.append(error_msg)
                            logger.warning(error_msg)
                        else:
                            successful_count += 1

                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Exception uploading email: {str(e)}"
                        errors.append(error_msg)
                        logger.warning(error_msg)

                # Log progress
                if batches_processed % 10 == 0:
                    logger.info(
                        "Processed %d/%d batches",
                        batches_processed,
                        (total_count + batch_size - 1) // batch_size,
                    )

            execution_time = time.time() - start_time
            self.monitor.record_operation(
                "upload_eml", execution_time, successful_count == total_count
            )

            if successful_count == total_count:
                logger.info(
                    "All %d .eml files uploaded successfully to mailbox: %s",
                    total_count,
                    mailbox,
                )
            else:
                logger.warning(
                    "Uploaded %d/%d .eml files to mailbox: %s",
                    successful_count,
                    total_count,
                    mailbox,
                )

            return BulkOperationResult(
                operation="upload_eml",
                total_messages=total_count,
                successful_messages=successful_count,
                failed_messages=failed_count,
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=batches_processed,
                errors=errors,
                metadata={"mailbox": mailbox, "flags": str(flags) if flags else None},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("upload_eml", execution_time, False)

            return BulkOperationResult(
                operation="upload_eml",
                total_messages=len(emails) if hasattr(emails, "__len__") else 0,
                successful_messages=0,
                failed_messages=len(emails) if hasattr(emails, "__len__") else 0,
                execution_time=execution_time,
                batch_size=self.bulk_operation_batch_size,
                batches_processed=0,
                errors=[str(e)],
            )

    def bulk_move(
        self,
        message_sets: List[Tuple[MessageSet, Mailbox]],
        batch_size: Optional[int] = None,
    ) -> BulkOperationResult:
        """Bulk move operation with batch processing."""
        start_time = time.time()
        batch_size = batch_size or self.bulk_operation_batch_size

        try:
            total_operations = len(message_sets)
            successful_operations = 0
            failed_operations = 0
            errors = []

            logger.debug("Starting bulk move of %d message sets", total_operations)

            for i, (msg_set, destination) in enumerate(message_sets):
                try:
                    result = self.move(msg_set, destination)
                    if result.success:
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        errors.append(
                            f"Move operation {i+1} failed: {result.error_message}"
                        )

                except Exception as e:
                    failed_operations += 1
                    errors.append(f"Move operation {i+1} exception: {str(e)}")

                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(
                        "Processed %d/%d move operations", i + 1, total_operations
                    )

            execution_time = time.time() - start_time
            self.monitor.record_operation(
                "bulk_move", execution_time, successful_operations == total_operations
            )

            return BulkOperationResult(
                operation="bulk_move",
                total_messages=total_operations,
                successful_messages=successful_operations,
                failed_messages=failed_operations,
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=1,
                errors=errors,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("bulk_move", execution_time, False)

            return BulkOperationResult(
                operation="bulk_move",
                total_messages=len(message_sets),
                successful_messages=0,
                failed_messages=len(message_sets),
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=0,
                errors=[str(e)],
            )

    def bulk_delete(
        self,
        message_sets: List[Tuple[MessageSet, Mailbox]],
        batch_size: Optional[int] = None,
    ) -> BulkOperationResult:
        """Bulk delete operation with batch processing."""
        start_time = time.time()
        batch_size = batch_size or self.bulk_operation_batch_size

        try:
            total_operations = len(message_sets)
            successful_operations = 0
            failed_operations = 0
            errors = []

            logger.debug("Starting bulk delete of %d message sets", total_operations)

            for i, (msg_set, trash_mailbox) in enumerate(message_sets):
                try:
                    result = self.delete(msg_set, trash_mailbox)
                    if result.success:
                        successful_operations += 1
                    else:
                        failed_operations += 1
                        errors.append(
                            f"Delete operation {i+1} failed: {result.error_message}"
                        )

                except Exception as e:
                    failed_operations += 1
                    errors.append(f"Delete operation {i+1} exception: {str(e)}")

                # Log progress
                if (i + 1) % 10 == 0:
                    logger.info(
                        "Processed %d/%d delete operations", i + 1, total_operations
                    )

            execution_time = time.time() - start_time
            self.monitor.record_operation(
                "bulk_delete", execution_time, successful_operations == total_operations
            )

            return BulkOperationResult(
                operation="bulk_delete",
                total_messages=total_operations,
                successful_messages=successful_operations,
                failed_messages=failed_operations,
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=1,
                errors=errors,
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("bulk_delete", execution_time, False)

            return BulkOperationResult(
                operation="bulk_delete",
                total_messages=len(message_sets),
                successful_messages=0,
                failed_messages=len(message_sets),
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=0,
                errors=[str(e)],
            )

    def get_mailbox_statistics(
        self, mailbox: Optional[Mailbox] = None
    ) -> MailboxStatistics:
        """Get comprehensive mailbox statistics."""
        target_mailbox = mailbox or self.current_selection
        if not target_mailbox:
            raise IMAPMailboxSelectionError("No mailbox selected or specified")

        try:
            # Get basic mailbox status
            status_result = self.status(
                target_mailbox,
                MailboxStatusItems.MESSAGES,
                MailboxStatusItems.RECENT,
                MailboxStatusItems.UNSEEN,
            )

            if not status_result.success:
                raise IMAPMailboxStatusError(
                    f"Failed to get mailbox status: {status_result.error_message}"
                )

            # Parse status response
            status_data = status_result.metadata.get("status_response", [])
            total_messages = 0
            recent_messages = 0
            unseen_messages = 0

            # Extract counts from status response
            for item in status_data:
                if isinstance(item, bytes):
                    item = item.decode()
                if "MESSAGES" in item:
                    total_messages = int(re.search(r"MESSAGES (\d+)", item).group(1))
                if "RECENT" in item:
                    recent_messages = int(re.search(r"RECENT (\d+)", item).group(1))
                if "UNSEEN" in item:
                    unseen_messages = int(re.search(r"UNSEEN (\d+)", item).group(1))

            return MailboxStatistics(
                total_messages=total_messages,
                unread_messages=unseen_messages,
                flagged_messages=0,  # Would need additional search to get this
                recent_messages=recent_messages,
                size_bytes=0,  # Would need to fetch messages to calculate
                message_size_distribution={},
                flag_distribution={},
                sender_distribution={},
            )

        except Exception as e:
            logger.error("Failed to get mailbox statistics: %s", e)
            return MailboxStatistics(
                total_messages=0,
                unread_messages=0,
                flagged_messages=0,
                recent_messages=0,
                size_bytes=0,
            )

    def search_and_process(
        self,
        criteria: IMAPSearchCriteria,
        processor_func: callable,
        batch_size: Optional[int] = None,
        charset: Optional[str] = "UTF-8",
    ) -> BulkOperationResult:
        """Search for messages and process them in batches."""
        start_time = time.time()
        batch_size = batch_size or self.bulk_operation_batch_size

        try:
            # First, search for messages
            search_result = self.search(criteria, charset)
            if not search_result.success:
                return BulkOperationResult(
                    operation="search_and_process",
                    total_messages=0,
                    successful_messages=0,
                    failed_messages=0,
                    execution_time=time.time() - start_time,
                    batch_size=batch_size,
                    batches_processed=0,
                    errors=[f"Search failed: {search_result.error_message}"],
                )

            message_ids = search_result.affected_messages
            total_messages = len(message_ids)

            if total_messages == 0:
                return BulkOperationResult(
                    operation="search_and_process",
                    total_messages=0,
                    successful_messages=0,
                    failed_messages=0,
                    execution_time=time.time() - start_time,
                    batch_size=batch_size,
                    batches_processed=0,
                )

            successful_count = 0
            failed_count = 0
            errors = []
            batches_processed = 0

            # Process in batches
            for i in range(0, total_messages, batch_size):
                batch_ids = message_ids[i : i + batch_size]
                msg_set = MessageSet(batch_ids)
                batches_processed += 1

                try:
                    # Fetch messages in batch
                    fetch_result = self.fetch(msg_set, MessagePart.RFC822)
                    if not fetch_result.success:
                        failed_count += len(batch_ids)
                        errors.append(
                            f"Batch {batches_processed} fetch failed: {fetch_result.error_message}"
                        )
                        continue

                    # Process each message
                    fetched_messages = fetch_result.metadata.get("fetched_messages", [])
                    for email_message in fetched_messages:
                        try:
                            processor_func(email_message)
                            successful_count += 1
                        except Exception as e:
                            failed_count += 1
                            errors.append(f"Processing failed for message: {str(e)}")

                except Exception as e:
                    failed_count += len(batch_ids)
                    errors.append(
                        f"Batch {batches_processed} processing failed: {str(e)}"
                    )

                # Log progress
                if batches_processed % 10 == 0:
                    logger.info(
                        "Processed %d/%d batches",
                        batches_processed,
                        (total_messages + batch_size - 1) // batch_size,
                    )

            execution_time = time.time() - start_time
            self.monitor.record_operation(
                "search_and_process", execution_time, successful_count == total_messages
            )

            return BulkOperationResult(
                operation="search_and_process",
                total_messages=total_messages,
                successful_messages=successful_count,
                failed_messages=failed_count,
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=batches_processed,
                errors=errors,
                metadata={"search_criteria": str(criteria), "charset": charset},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("search_and_process", execution_time, False)

            return BulkOperationResult(
                operation="search_and_process",
                total_messages=0,
                successful_messages=0,
                failed_messages=0,
                execution_time=execution_time,
                batch_size=batch_size,
                batches_processed=0,
                errors=[str(e)],
            )


class IMAPMailboxUIDService(BaseMailboxService):
    """Enhanced IMAP Mailbox UID Service with comprehensive operations and monitoring."""

    def __init__(self, client: IMAPClient):
        super().__init__(client)
        self.bulk_operation_batch_size = 100

    @mailbox_selection_required
    def uid_search(
        self, criteria: IMAPSearchCriteria, charset: Optional[str] = "UTF-8"
    ) -> MailboxOperationResult:
        """Enhanced UID search with detailed result information."""
        start_time = time.time()

        try:
            logger.debug("Searching emails with UID criteria: %s", criteria)
            status, data = self.client.uid("SEARCH", criteria)

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_search", execution_time, False)
                logger.error("Failed to search emails: %s", data)
                raise IMAPSearchError(f"Failed to search emails: {data}")

            msg_ids = data[0].split()
            msg_id_strs = [msg_id.decode("utf-8") for msg_id in msg_ids]

            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_search", execution_time)
            logger.info("UID search successful, found %d emails.", len(msg_id_strs))

            return MailboxOperationResult(
                success=True,
                operation="uid_search",
                message_count=len(msg_id_strs),
                affected_messages=msg_id_strs,
                execution_time=execution_time,
                metadata={"criteria": str(criteria), "charset": charset},
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_search", execution_time, False)
            logger.error("Exception occurred during UID search: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="uid_search",
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def uid_trash(
        self, msg_set: MessageSet, trash_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced UID trash operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)

            logger.debug(
                "Marking messages %s for deletion and moving to %s (UID).",
                msg_set.msg_ids,
                trash_mailbox,
            )

            # Mark the messages as deleted using UID
            status, _ = self.client.uid(
                "STORE", msg_set.msg_ids, "+FLAGS", Flag.DELETED
            )

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_trash", execution_time, False)
                logger.error(
                    "Failed to mark messages %s for deletion: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="uid_trash",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to mark messages for deletion: {status}",
                )

            # Move the messages to the trash folder
            move_result = self.uid_move(msg_set, trash_mailbox)
            if not move_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_trash", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_trash",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to move messages to trash: {move_result.error_message}",
                )

            check_result = self.check()
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_trash", execution_time)

            return MailboxOperationResult(
                success=True,
                operation="uid_trash",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_trash", execution_time, False)
            logger.error(
                "Exception occurred while UID trashing messages %s: %s",
                msg_set.msg_ids,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="uid_trash",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    def uid_delete(
        self, msg_set: MessageSet, trash_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced UID delete operation with comprehensive monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)

            logger.debug("Deleting messages %s permanently (UID).", msg_set.msg_ids)

            # First trash the messages
            trash_result = self.uid_trash(msg_set, trash_mailbox)
            if not trash_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_delete", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_delete",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to trash messages: {trash_result.error_message}",
                )

            # Permanently remove messages marked as deleted
            self.client.expunge()
            check_result = self.check()

            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_delete", execution_time)
            logger.info("Messages %s permanently deleted (UID).", msg_set.msg_ids)

            return MailboxOperationResult(
                success=True,
                operation="uid_delete",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_delete", execution_time, False)
            logger.error(
                "Exception occurred while UID deleting messages %s: %s",
                msg_set.msg_ids,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="uid_delete",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def uid_move(
        self, msg_set: MessageSet, destination_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced UID move operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(destination_mailbox)

            logger.debug(
                "Moving messages %s to mailbox %s (UID).",
                msg_set.msg_ids,
                destination_mailbox,
            )

            # Copy messages to destination using UID
            status, _ = self.client.uid("COPY", msg_set.msg_ids, destination_mailbox)
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_move", execution_time, False)
                logger.error(
                    "Failed to copy messages %s to mailbox %s: %s",
                    msg_set.msg_ids,
                    destination_mailbox,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="uid_move",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to copy messages to destination: {status}",
                )

            # Mark the messages as deleted in the current mailbox using UID
            status, _ = self.client.uid(
                "STORE", msg_set.msg_ids, "+FLAGS", Flag.DELETED
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_move", execution_time, False)
                logger.error(
                    "Failed to mark messages %s for deletion: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="uid_move",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to mark messages for deletion: {status}",
                    warnings=["Messages copied but not removed from source"],
                )

            # Permanently remove messages marked as deleted from the source mailbox
            self.client.expunge()
            check_result = self.check()

            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_move", execution_time)
            logger.info(
                "Messages %s moved to mailbox %s (UID).",
                msg_set.msg_ids,
                destination_mailbox,
            )

            return MailboxOperationResult(
                success=True,
                operation="uid_move",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "destination_mailbox": destination_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_move", execution_time, False)
            logger.error(
                "Exception occurred while UID moving messages %s: %s",
                msg_set.msg_ids,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="uid_move",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    def uid_restore(
        self, msg_set: MessageSet, trash_mailbox: Mailbox, safe_mailbox: Mailbox
    ) -> MailboxOperationResult:
        """Enhanced UID restore operation with comprehensive validation and monitoring."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)
            self.validator.validate_mailbox(trash_mailbox)
            self.validator.validate_mailbox(safe_mailbox)

            logger.debug(
                "Restoring messages %s from trash to folder %s (UID).",
                msg_set.msg_ids,
                safe_mailbox,
            )

            # Select trash mailbox
            select_result = self.select(trash_mailbox)
            if not select_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to select trash mailbox: {select_result.error_message}",
                )

            # Move messages from trash to safe mailbox using UID
            move_result = self.uid_move(msg_set, safe_mailbox)
            if not move_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to move messages: {move_result.error_message}",
                )

            # Select safe mailbox and remove deleted flag using UID
            select_result = self.select(safe_mailbox)
            if not select_result.success:
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_restore", execution_time, False)
                return MailboxOperationResult(
                    success=False,
                    operation="uid_restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to select safe mailbox: {select_result.error_message}",
                    warnings=["Messages moved but deleted flag not removed"],
                )

            status, _ = self.client.uid(
                "STORE", msg_set.msg_ids, "-FLAGS", Flag.DELETED
            )
            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_restore", execution_time, False)
                logger.error(
                    "Failed to remove \\Deleted flag from messages %s: %s",
                    msg_set.msg_ids,
                    status,
                )
                return MailboxOperationResult(
                    success=False,
                    operation="uid_restore",
                    message_count=len(msg_set.msg_ids),
                    affected_messages=msg_set.msg_ids,
                    execution_time=execution_time,
                    error_message=f"Failed to remove deleted flag: {status}",
                    warnings=["Messages moved but deleted flag not removed"],
                )

            check_result = self.check()
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_restore", execution_time)
            logger.info(
                "Messages %s restored from trash to folder %s (UID).",
                msg_set.msg_ids,
                safe_mailbox,
            )

            return MailboxOperationResult(
                success=True,
                operation="uid_restore",
                message_count=len(msg_set.msg_ids),
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "trash_mailbox": trash_mailbox,
                    "safe_mailbox": safe_mailbox,
                    "check_result": check_result.success,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_restore", execution_time, False)
            logger.error(
                "Exception occurred while UID restoring messages %s: %s",
                msg_set.msg_ids,
                e,
            )
            return MailboxOperationResult(
                success=False,
                operation="uid_restore",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )

    @mailbox_selection_required
    def uid_fetch(
        self, msg_set: MessageSet, msg_part: MessagePart
    ) -> MailboxOperationResult:
        """Enhanced UID fetch operation with comprehensive validation and EmailMessage integration."""
        start_time = time.time()

        try:
            self.validator.validate_message_set(msg_set)

            logger.debug(
                "Fetching message part %s for messages %s (UID).",
                msg_part,
                msg_set.msg_ids,
            )
            status, data = self.client.uid(
                "FETCH", msg_set.msg_ids, f"({msg_part} FLAGS UID)"
            )

            if status != "OK":
                execution_time = time.time() - start_time
                self.monitor.record_operation("uid_fetch", execution_time, False)
                logger.error("Failed to fetch message part %s: %s", msg_part, status)
                raise IMAPMailboxFetchError(f"Failed to fetch message part: {status}")

            fetched_data = []
            processed_count = 0

            for response_part in data:
                if isinstance(response_part, tuple) and len(response_part) == 2:
                    try:
                        flag_data = response_part[0]
                        msg_data = response_part[1]

                        # Skip if msg_data is not bytes or is empty
                        if not isinstance(msg_data, bytes) or len(msg_data) == 0:
                            continue

                        # Create EmailMessage from bytes
                        email_message = EmailMessage.read_from_eml_bytes(msg_data)

                        # Extract and set flags
                        if isinstance(flag_data, bytes):
                            flags = EmailMessage.extract_flags(flag_data)
                            email_message.flags = flags

                            # Extract sequence number and UID (different pattern for UID fetch)
                            flag_data_str = flag_data.decode("utf-8", errors="ignore")
                            match = re.search(
                                r"(\d+) \(UID (\d+) FLAGS \([^\)]*\)", flag_data_str
                            )

                            if match:
                                email_message.sequence_number = int(match.group(1))
                                email_message.uid = int(match.group(2))

                        # Set additional metadata
                        email_message.size = len(msg_data)
                        email_message.mailbox = self.current_selection

                        fetched_data.append(email_message)
                        processed_count += 1

                    except Exception as e:
                        logger.warning("Failed to process message in UID fetch: %s", e)
                        continue
                else:
                    # Skip non-tuple responses or malformed responses
                    logger.debug(
                        "Skipping non-tuple response in UID fetch: %s",
                        type(response_part),
                    )

            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_fetch", execution_time)
            logger.info("UID fetched %d messages successfully.", processed_count)

            return MailboxOperationResult(
                success=True,
                operation="uid_fetch",
                message_count=processed_count,
                affected_messages=msg_set.msg_ids,
                execution_time=execution_time,
                metadata={
                    "message_part": str(msg_part),
                    "fetched_messages": fetched_data,
                    "requested_count": len(msg_set.msg_ids),
                    "processed_count": processed_count,
                },
            )

        except Exception as e:
            execution_time = time.time() - start_time
            self.monitor.record_operation("uid_fetch", execution_time, False)
            logger.error("Exception occurred while UID fetching messages: %s", e)
            return MailboxOperationResult(
                success=False,
                operation="uid_fetch",
                message_count=len(msg_set.msg_ids) if msg_set else 0,
                execution_time=execution_time,
                error_message=str(e),
            )
