"""IMAP mailbox services."""

from sage_imap.services.mailbox.models import (
    BulkOperationResult,
    MailboxOperationResult,
    MailboxStatistics,
    MailboxValidator,
)
from sage_imap.services.mailbox.operations import (
    IMAPMailboxService,
    IMAPMailboxUIDService,
)

__all__ = [
    "IMAPMailboxService",
    "IMAPMailboxUIDService",
    "MailboxOperationResult",
    "BulkOperationResult",
    "MailboxStatistics",
    "MailboxValidator",
]
