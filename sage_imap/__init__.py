"""
Python Sage IMAP - A Python package for managing IMAP connections and email operations.

This package provides a comprehensive set of tools for working with IMAP servers,
including connection management, mailbox operations, and email handling.
"""

__version__ = "1.0.0"
__author__ = "Sepehr Akbarzadeh"
__email__ = "sepehr@sageteam.org"
__license__ = "MIT"

from .models.email import EmailMessage
from .models.message import MessageSet

# Import main components for easy access
from .services.client import IMAPClient
from .services.flag import IMAPFlagService
from .services.folder import IMAPFolderService
from .services.mailbox import IMAPMailboxService

__all__ = [
    "IMAPClient",
    "IMAPMailboxService",
    "IMAPFolderService",
    "IMAPFlagService",
    "EmailMessage",
    "MessageSet",
    "__version__",
]
