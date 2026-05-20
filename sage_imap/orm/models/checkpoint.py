"""Sync checkpoint entity wrapping MailboxSyncState."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from sage_imap.sync.state import MailboxSyncState


@dataclass
class SyncCheckpoint:
    account_id: str
    mailbox: str
    state: MailboxSyncState = field(
        default_factory=lambda: MailboxSyncState(mailbox="INBOX")
    )

    @classmethod
    def capture(cls, account_id: str, mailbox: str, backend: Any) -> "SyncCheckpoint":
        state = backend.capture_sync_state(mailbox)
        return cls(account_id=account_id, mailbox=mailbox, state=state)

    def refresh(self, backend: Any) -> "SyncCheckpoint":
        self.state = backend.capture_sync_state(self.mailbox)
        return self

    def apply(self, backend: Any) -> "SyncCheckpoint":
        from sage_imap.orm.backends.async_ import AsyncImapBackend

        if isinstance(backend, AsyncImapBackend):
            raise RuntimeError("Use await checkpoint.apply_async() for async backends")
        self.state = backend.apply_after_sync(self.state)
        return self

    async def apply_async(self, backend: Any) -> "SyncCheckpoint":
        self.state = await backend.apply_after_sync(self.state)
        return self

    async def refresh_async(self, backend: Any) -> "SyncCheckpoint":
        self.state = await backend.capture_sync_state(self.mailbox)
        return self


class SyncCheckpointManager:
    def for_mailbox(self, account_id: str, mailbox: str) -> SyncCheckpoint:
        from sage_imap.orm.managers import _active_orm

        orm = _active_orm.get()
        if orm is None:
            return SyncCheckpoint(account_id=account_id, mailbox=mailbox)
        cp = SyncCheckpoint.capture(account_id, mailbox, orm.backend)
        return cp

    async def for_mailbox_async(self, account_id: str, mailbox: str) -> SyncCheckpoint:
        from sage_imap.orm.managers import _active_orm

        orm = _active_orm.get()
        if orm is None:
            return SyncCheckpoint(account_id=account_id, mailbox=mailbox)
        state = await orm.backend.capture_sync_state(mailbox)  # type: ignore[misc]
        return SyncCheckpoint(account_id=account_id, mailbox=mailbox, state=state)


class _SyncCheckpointManagerDescriptor:
    def __get__(self, obj: Any, owner: type) -> SyncCheckpointManager:
        return SyncCheckpointManager()


SyncCheckpoint.objects = _SyncCheckpointManagerDescriptor()  # type: ignore[attr-defined]
