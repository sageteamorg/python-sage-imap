"""Pydantic schema exports."""

from sage_imap.orm.schemas.error import ErrorSchema, OperationResultSchema
from sage_imap.orm.schemas.message import (
    AttachmentSchema,
    ImapMessageDetailSchema,
    ImapMessageSummarySchema,
)

__all__ = [
    "ErrorSchema",
    "OperationResultSchema",
    "AttachmentSchema",
    "ImapMessageSummarySchema",
    "ImapMessageDetailSchema",
]
