"""Rich IMAP message entity (ORM-owned, not EmailMessage)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from sage_imap.models.email import EmailMessage
    from sage_imap.orm.backends.protocol import ImapBackend


@dataclass
class ImapAttachment:
    filename: str
    content_type: str
    size: int = 0
    payload: bytes = field(default=b"", repr=False)


@dataclass
class ImapMessage:
    """Message entity keyed by ``(account_id, mailbox, uid)``."""

    account_id: str
    mailbox: str
    uid: int
    message_id: str = ""
    subject: str = ""
    from_address: Optional[str] = None
    to_addresses: list[str] = field(default_factory=list)
    cc_addresses: list[str] = field(default_factory=list)
    date: Optional[datetime] = None
    flags: list[str] = field(default_factory=list)
    plain_body: str = field(default="", repr=False)
    html_body: str = field(default="", repr=False)
    attachments: list[ImapAttachment] = field(default_factory=list, repr=False)
    size: int = 0
    has_attachments: bool = False
    _backend: Any = field(default=None, repr=False, compare=False)

    @classmethod
    def from_uid(
        cls,
        account_id: str,
        mailbox: str,
        uid: int,
        *,
        backend: Optional["ImapBackend"] = None,
    ) -> "ImapMessage":
        return cls(
            account_id=account_id,
            mailbox=mailbox,
            uid=uid,
            _backend=backend,
        )

    @classmethod
    def from_fetched(
        cls,
        account_id: str,
        fetched: "EmailMessage",
    ) -> "ImapMessage":
        flags = [f.value if hasattr(f, "value") else str(f) for f in fetched.flags]
        attachments = [
            ImapAttachment(
                filename=a.filename,
                content_type=a.content_type,
                size=a.size,
            )
            for a in fetched.attachments
        ]
        from_addr = str(fetched.from_address) if fetched.from_address else None
        msg_date = fetched.date
        if isinstance(msg_date, str):
            try:
                msg_date = datetime.fromisoformat(msg_date)
            except ValueError:
                msg_date = None
        return cls(
            account_id=account_id,
            mailbox=fetched.mailbox or "INBOX",
            uid=int(fetched.uid or 0),
            message_id=fetched.message_id or "",
            subject=fetched.subject or "",
            from_address=from_addr,
            to_addresses=[str(a) for a in fetched.to_address],
            cc_addresses=[str(a) for a in fetched.cc_address],
            date=msg_date if isinstance(msg_date, datetime) else None,
            flags=flags,
            plain_body=fetched.plain_body or "",
            html_body=fetched.html_body or "",
            attachments=attachments,
            size=fetched.size or 0,
            has_attachments=fetched.has_attachments(),
        )

    def _require_backend(self) -> "ImapBackend":
        if self._backend is None:
            raise RuntimeError("ImapMessage is not bound to an ORM backend")
        return self._backend

    def mark_seen(self) -> None:
        backend = self._require_backend()
        result = backend.mark_seen(self)
        if hasattr(result, "__await__"):
            raise RuntimeError("Use await msg.amark_seen() with AsyncImapORM")

    async def amark_seen(self) -> None:
        await self._require_backend().mark_seen(self)  # type: ignore[misc]

    async def amark_unseen(self) -> None:
        await self._require_backend().mark_unseen(self)  # type: ignore[misc]

    async def amove_to(self, folder: str) -> None:
        await self._require_backend().move_messages([self.uid], folder)  # type: ignore[misc]

    async def adelete(self, *, trash_folder: Optional[str] = None) -> None:
        await self._require_backend().delete_messages(  # type: ignore[misc]
            [self.uid], trash_folder=trash_folder
        )

    def mark_unseen(self) -> None:
        self._require_backend().mark_unseen(self)

    def move_to(self, folder: str) -> None:
        self._require_backend().move_messages([self.uid], folder)

    def delete(self, *, trash_folder: Optional[str] = None) -> None:
        self._require_backend().delete_messages([self.uid], trash_folder=trash_folder)


class _MessageManagerDescriptor:
    def __get__(self, obj: Any, owner: type) -> Any:
        from sage_imap.orm.managers import MessageManager

        return MessageManager()


ImapMessage.objects = _MessageManagerDescriptor()  # type: ignore[attr-defined]
