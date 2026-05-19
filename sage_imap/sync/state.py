"""Persistent-friendly mailbox sync checkpoint."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional


@dataclass
class MailboxSyncState:
    """
    Checkpoint for incremental sync of one mailbox.

    Compare ``uidvalidity`` after reconnect; if it changed, full resync is required.
    Use ``highest_modseq`` with CONDSTORE CHANGEDSINCE for incremental updates.
    """

    mailbox: str
    uidvalidity: Optional[int] = None
    uidnext: Optional[int] = None
    highest_modseq: Optional[int] = None
    message_count: Optional[int] = None
    unseen_count: Optional[int] = None
    last_sync_at: Optional[datetime] = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def is_stale(self, server_uidvalidity: int) -> bool:
        """Return True if server UIDVALIDITY differs (mailbox was recreated)."""
        if self.uidvalidity is None:
            return False
        return self.uidvalidity != server_uidvalidity

    def touch(self) -> None:
        self.last_sync_at = datetime.now(timezone.utc)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        if self.last_sync_at:
            data["last_sync_at"] = self.last_sync_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MailboxSyncState":
        last = data.get("last_sync_at")
        if isinstance(last, str):
            data = {**data, "last_sync_at": datetime.fromisoformat(last)}
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
