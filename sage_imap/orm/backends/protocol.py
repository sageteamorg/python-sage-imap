"""Backend protocol for sync and async IMAP ORM."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, Optional, Protocol, Union

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.orm.config import LoadLevel
from sage_imap.services.mailbox.models import MailboxOperationResult

if TYPE_CHECKING:
    from sage_imap.models.message import MessageSet
    from sage_imap.orm.models.message import ImapMessage
    from sage_imap.sync.state import MailboxSyncState


class ImapBackend(Protocol):
    account_id: str
    mailbox: Optional[str]

    def select_mailbox(self, name: str) -> MailboxOperationResult: ...

    def uid_search(
        self,
        criteria: Union[IMAPSearchCriteria, str],
        *,
        charset: Optional[str] = None,
    ) -> MailboxOperationResult: ...

    def fetch_messages(
        self,
        msg_set: "MessageSet",
        *,
        load_level: LoadLevel = LoadLevel.HEADERS,
        batch_size: int = 50,
    ) -> Iterator["ImapMessage"]: ...

    def mark_seen(self, message: "ImapMessage") -> None: ...

    def mark_unseen(self, message: "ImapMessage") -> None: ...

    def move_messages(
        self, uids: list[int], destination: str
    ) -> MailboxOperationResult: ...

    def delete_messages(
        self,
        uids: list[int],
        *,
        trash_folder: Optional[str] = None,
    ) -> MailboxOperationResult: ...

    def capture_sync_state(self, mailbox: str) -> "MailboxSyncState": ...

    def find_changed_uids(self, state: "MailboxSyncState") -> "MessageSet": ...
