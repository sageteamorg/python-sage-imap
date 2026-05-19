"""Mailbox service result types and validation."""

import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from sage_imap.exceptions import (
    IMAPMailboxError,
    IMAPMailboxSelectionError,
    IMAPMailboxUploadError,
)
from sage_imap.helpers.typings import Mailbox
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet

logger = logging.getLogger(__name__)


@dataclass
class MailboxOperationResult:
    success: bool
    operation: str
    message_count: int = 0
    affected_messages: List[str] = field(default_factory=list)
    execution_time: float = 0.0
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.message_count == 0 and self.affected_messages:
            self.message_count = len(self.affected_messages)

    def to_uid_message_set(self, mailbox: Optional[str] = None) -> MessageSet:
        """Build a UID :class:`MessageSet` from search/fetch affected message IDs."""
        if not self.affected_messages:
            return MessageSet.empty(mailbox=mailbox)
        uids = [int(uid) for uid in self.affected_messages if str(uid).isdigit()]
        if not uids:
            return MessageSet.empty(mailbox=mailbox)
        return MessageSet.from_uids(uids, mailbox=mailbox)


@dataclass
class BulkOperationResult:
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
        if self.total_messages == 0:
            return 0.0
        return (self.successful_messages / self.total_messages) * 100

    @property
    def is_successful(self) -> bool:
        return self.success_rate == 100.0


@dataclass
class MailboxStatistics:
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
    @staticmethod
    def validate_message_set(
        msg_set: MessageSet, expected_mailbox: Optional[str] = None
    ) -> bool:
        if not isinstance(msg_set, MessageSet):
            raise IMAPMailboxError("msg_set must be a MessageSet instance")
        if msg_set.is_empty():
            raise IMAPMailboxError("MessageSet cannot be empty")
        if expected_mailbox:
            try:
                msg_set.validate_for_mailbox(expected_mailbox)
            except ValueError as e:
                raise IMAPMailboxError(f"MessageSet validation failed: {e}") from e
        if not msg_set.is_uid:
            logger.warning(
                "MessageSet contains sequence numbers. "
                "Consider using UIDs for reliable operations."
            )
        return True

    @staticmethod
    def validate_mailbox(mailbox: Mailbox) -> bool:
        if not mailbox:
            raise IMAPMailboxSelectionError("Mailbox name cannot be empty")
        if not isinstance(mailbox, str):
            raise IMAPMailboxSelectionError("Mailbox must be a string")
        for char in ("..", "\0"):
            if char in mailbox:
                raise IMAPMailboxSelectionError(
                    f"Mailbox name contains dangerous sequence: {char!r}"
                )
        return True

    @staticmethod
    def validate_email_data(emails: Union[EmailIterator, List[EmailMessage]]) -> bool:
        if not isinstance(emails, (list, EmailIterator)):
            raise IMAPMailboxUploadError("emails must be a list or an EmailIterator")
        if isinstance(emails, list) and len(emails) == 0:
            raise IMAPMailboxUploadError("Email list cannot be empty")
        return True


class MailboxMonitor:
    def __init__(self) -> None:
        self.operation_counts = defaultdict(int)
        self.operation_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.last_operations: List[dict] = []
        self.start_time = time.time()

    def record_operation(
        self, operation: str, execution_time: float, success: bool = True
    ) -> None:
        self.operation_counts[operation] += 1
        self.operation_times[operation].append(execution_time)
        if not success:
            self.error_counts[operation] += 1
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
        stats: Dict[str, Any] = {
            "uptime": time.time() - self.start_time,
            "total_operations": sum(self.operation_counts.values()),
            "operations_by_type": dict(self.operation_counts),
            "error_counts": dict(self.error_counts),
            "average_times": {},
            "recent_operations": self.last_operations[-10:],
        }
        for operation, times in self.operation_times.items():
            if times:
                stats["average_times"][operation] = sum(times) / len(times)
        return stats
