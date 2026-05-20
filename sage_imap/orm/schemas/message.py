"""Message JSON schemas."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from sage_imap.orm.models.message import ImapMessage


class AttachmentSchema(BaseModel):
    filename: str
    content_type: str
    size: int = 0


class ImapMessageSummarySchema(BaseModel):
    account_id: str
    mailbox: str
    uid: int
    message_id: Optional[str] = None
    subject: str = ""
    from_address: Optional[str] = None
    date: Optional[datetime] = None
    flags: list[str] = Field(default_factory=list)
    has_attachments: bool = False
    size: int = 0

    @classmethod
    def from_imap_message(cls, msg: "ImapMessage") -> "ImapMessageSummarySchema":
        return cls(
            account_id=msg.account_id,
            mailbox=msg.mailbox,
            uid=msg.uid,
            message_id=msg.message_id or None,
            subject=msg.subject,
            from_address=msg.from_address,
            date=msg.date,
            flags=list(msg.flags),
            has_attachments=msg.has_attachments,
            size=msg.size,
        )


class ImapMessageDetailSchema(ImapMessageSummarySchema):
    to_addresses: list[str] = Field(default_factory=list)
    cc_addresses: list[str] = Field(default_factory=list)
    plain_body: str = ""
    html_body: str = ""
    attachments: list[AttachmentSchema] = Field(default_factory=list)

    @classmethod
    def from_imap_message(
        cls,
        msg: "ImapMessage",
        *,
        include_body: bool = True,
    ) -> "ImapMessageDetailSchema":
        base = ImapMessageSummarySchema.from_imap_message(msg)
        data = base.model_dump()
        data["to_addresses"] = list(msg.to_addresses)
        data["cc_addresses"] = list(msg.cc_addresses)
        if include_body:
            data["plain_body"] = msg.plain_body
            data["html_body"] = msg.html_body
            data["attachments"] = [
                AttachmentSchema(
                    filename=a.filename,
                    content_type=a.content_type,
                    size=a.size,
                )
                for a in msg.attachments
            ]
        return cls(**data)
