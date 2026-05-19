"""
Async IMAP API (``sage_imap.aio``).

Requires optional dependencies::

    pip install python-sage-imap[async]
"""

from __future__ import annotations

# Lazy exports via __getattr__; names are not defined at import time.
# pylint: disable=undefined-all-variable

__all__ = [
    "AsyncIMAPClient",
    "AsyncIMAPTransport",
    "AsyncIMAPSession",
    "AsyncIMAPMailboxUIDService",
    "AsyncIMAPFolderService",
    "AsyncIMAPFlagService",
    "AsyncIMAPSyncService",
    "AsyncIMAPIdleSession",
    "AsyncIMAPIdleWatcher",
]

_MISSING_ASYNC_EXTRA = (
    "Async IMAP requires the [async] extra. "
    "Install with: pip install python-sage-imap[async]"
)


def __getattr__(name: str):
    if name in __all__:
        try:
            import aioimaplib  # noqa: F401  # pylint: disable=unused-import,import-outside-toplevel
        except ImportError as exc:
            raise ImportError(_MISSING_ASYNC_EXTRA) from exc

        if name == "AsyncIMAPClient":
            from sage_imap.aio.client import AsyncIMAPClient

            return AsyncIMAPClient
        if name == "AsyncIMAPTransport":
            from sage_imap.aio.transport import AsyncIMAPTransport

            return AsyncIMAPTransport
        if name == "AsyncIMAPSession":
            from sage_imap.aio.session import AsyncIMAPSession

            return AsyncIMAPSession
        if name == "AsyncIMAPMailboxUIDService":
            from sage_imap.aio.mailbox import AsyncIMAPMailboxUIDService

            return AsyncIMAPMailboxUIDService
        if name == "AsyncIMAPFolderService":
            from sage_imap.aio.folder import AsyncIMAPFolderService

            return AsyncIMAPFolderService
        if name == "AsyncIMAPFlagService":
            from sage_imap.aio.flag import AsyncIMAPFlagService

            return AsyncIMAPFlagService
        if name == "AsyncIMAPSyncService":
            from sage_imap.aio.sync import AsyncIMAPSyncService

            return AsyncIMAPSyncService
        if name in ("AsyncIMAPIdleSession", "AsyncIMAPIdleWatcher"):
            from sage_imap.aio.idle import AsyncIMAPIdleSession, AsyncIMAPIdleWatcher

            return (
                AsyncIMAPIdleSession
                if name == "AsyncIMAPIdleSession"
                else AsyncIMAPIdleWatcher
            )
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
