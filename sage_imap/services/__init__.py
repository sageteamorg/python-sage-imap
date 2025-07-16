from .client import (
    ConnectionConfig,
    ConnectionMetrics,
    IMAPClient,
    clear_connection_pool,
    get_pool_stats,
)
from .flag import FlagOperationResult, IMAPFlagService
from .folder import FolderInfo, FolderOperationResult, IMAPFolderService
from .mailbox import IMAPMailboxService, IMAPMailboxUIDService

__all__ = [
    # Client
    "IMAPClient",
    "ConnectionConfig",
    "ConnectionMetrics",
    "clear_connection_pool",
    "get_pool_stats",
    # Flag service
    "IMAPFlagService",
    "FlagOperationResult",
    # Folder service
    "IMAPFolderService",
    "FolderInfo",
    "FolderOperationResult",
    # Mailbox service
    "IMAPMailboxService",
    "IMAPMailboxUIDService",
]
