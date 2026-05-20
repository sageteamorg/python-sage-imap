"""Model managers for the IMAP ORM."""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any, Optional

from sage_imap.orm.queryset import MessageQuerySet

if TYPE_CHECKING:
    from sage_imap.orm.session import ImapORM


_active_orm: ContextVar[Optional["ImapORM"]] = ContextVar(
    "sage_imap_active_orm", default=None
)


class MessageManager:
    """Access via ``ImapMessage.objects``."""

    def filter(self, *args: Any, **kwargs: Any) -> MessageQuerySet:
        return self._base_qs().filter(*args, **kwargs)

    def all(self) -> MessageQuerySet:
        return self._base_qs()

    def get(self, uid: int) -> MessageQuerySet:
        return self._base_qs().filter(uid=uid).limit(1)

    def changed_since(self, checkpoint: Any) -> MessageQuerySet:
        state = checkpoint.state if hasattr(checkpoint, "state") else checkpoint
        return self._base_qs().changed_since(state)

    def _base_qs(self) -> MessageQuerySet:
        orm = _active_orm.get()
        if orm is None:
            return MessageQuerySet()
        return MessageQuerySet(
            orm.backend,
            account_id=orm.account_id,
            mailbox=orm.mailbox,
        )


class _ManagerDescriptor:
    def __get__(self, obj: Any, owner: type) -> MessageManager:
        return MessageManager()


objects = MessageManager()
