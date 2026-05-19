"""
Python Sage IMAP - A Python package for managing IMAP connections and email operations.
"""

__version__ = "1.0.0"
__author__ = "Sepehr Akbarzadeh"
__email__ = "sepehr@sageteam.org"
__license__ = "MIT"

from sage_imap.auth.oauth2 import OAuth2Config
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, ConnectionMetrics, IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import IMAPFolderService
from sage_imap.services.idle import IdleEvent, IMAPIdleSession, IMAPIdleWatcher
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService
from sage_imap.sync import IMAPSyncService, MailboxSyncState

__all__ = [
    "IMAPClient",
    "ConnectionConfig",
    "ConnectionMetrics",
    "IMAPMailboxService",
    "IMAPMailboxUIDService",
    "IMAPFolderService",
    "IMAPFlagService",
    "EmailMessage",
    "MessageSet",
    "IMAPSearchCriteria",
    "OAuth2Config",
    "ParseMode",
    "MailboxSyncState",
    "IMAPSyncService",
    "IMAPIdleSession",
    "IMAPIdleWatcher",
    "IdleEvent",
    "__version__",
]
