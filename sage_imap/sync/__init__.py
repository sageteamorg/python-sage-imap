"""Incremental mailbox sync (CONDSTORE / MODSEQ)."""

from sage_imap.sync.condstore import parse_status_sync_fields
from sage_imap.sync.service import IMAPSyncService
from sage_imap.sync.state import MailboxSyncState

__all__ = [
    "MailboxSyncState",
    "IMAPSyncService",
    "parse_status_sync_fields",
]
