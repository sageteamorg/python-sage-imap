"""
IMAP ORM — manager/queryset layer over live IMAP.

Requires::

    pip install python-sage-imap[orm]
"""

from __future__ import annotations

# Lazy exports via __getattr__; names are not defined at import time.
# pylint: disable=undefined-all-variable,unused-import

__all__ = [
    "ImapORM",
    "AsyncImapORM",
    "ImapMessage",
    "ImapFolder",
    "SyncCheckpoint",
    "IdleSubscription",
    "LoadLevel",
    "ConnectionPolicy",
    "ImapAccountConfig",
    "AccountProvider",
    "Q",
    "ErrorSchema",
    "OperationResultSchema",
    "ImapMessageSummarySchema",
    "ImapMessageDetailSchema",
]

_MISSING_ORM_EXTRA = (
    "IMAP ORM requires the [orm] extra. "
    "Install with: pip install python-sage-imap[orm]"
)


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    try:
        import pydantic as _pydantic  # noqa: F401
    except ImportError as exc:
        raise ImportError(_MISSING_ORM_EXTRA) from exc

    if name == "ImapORM":
        from sage_imap.orm.session import ImapORM

        return ImapORM
    if name == "AsyncImapORM":
        from sage_imap.orm.async_session import AsyncImapORM

        return AsyncImapORM
    if name == "ImapMessage":
        from sage_imap.orm.models.message import ImapMessage

        return ImapMessage
    if name == "ImapFolder":
        from sage_imap.orm.models.folder import ImapFolder

        return ImapFolder
    if name == "SyncCheckpoint":
        from sage_imap.orm.models.checkpoint import SyncCheckpoint

        return SyncCheckpoint
    if name == "IdleSubscription":
        from sage_imap.orm.idle import IdleSubscription

        return IdleSubscription
    if name in (
        "LoadLevel",
        "ConnectionPolicy",
        "ImapAccountConfig",
        "AccountProvider",
    ):
        from sage_imap.orm import config as cfg

        return getattr(cfg, name)
    if name == "Q":
        from sage_imap.orm.q import Q

        return Q
    if name == "ErrorSchema":
        from sage_imap.orm.schemas.error import ErrorSchema

        return ErrorSchema
    if name == "OperationResultSchema":
        from sage_imap.orm.schemas.error import OperationResultSchema

        return OperationResultSchema
    if name == "ImapMessageSummarySchema":
        from sage_imap.orm.schemas.message import ImapMessageSummarySchema

        return ImapMessageSummarySchema
    if name == "ImapMessageDetailSchema":
        from sage_imap.orm.schemas.message import ImapMessageDetailSchema

        return ImapMessageDetailSchema
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
