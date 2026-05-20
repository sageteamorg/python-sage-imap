"""Sync IMAP backend adapter over :class:`~sage_imap.session.IMAPSession`."""

from __future__ import annotations

from typing import Iterator, Optional, Union

from sage_imap.helpers.enums import Flag
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.special_use import SpecialUse
from sage_imap.models.message import MessageSet
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.models.message import ImapMessage
from sage_imap.services.mailbox.models import MailboxOperationResult
from sage_imap.session import IMAPSession
from sage_imap.sync.state import MailboxSyncState


def _parse_mode_for(load_level: LoadLevel) -> ParseMode:
    if load_level == LoadLevel.FULL:
        return ParseMode.FULL
    if load_level == LoadLevel.IDENTITY:
        return ParseMode.MINIMAL
    return ParseMode.HEADERS


class SyncImapBackend:
    """Wraps :class:`IMAPSession` for the ORM layer."""

    def __init__(self, session: IMAPSession, account_id: str) -> None:
        self._session = session
        self.account_id = account_id
        self.mailbox: Optional[str] = None

    def select_mailbox(self, name: str) -> MailboxOperationResult:
        result = self._session.select(name)
        if result.success:
            self.mailbox = name
        return result

    def uid_search(
        self,
        criteria: Union[IMAPSearchCriteria, str],
        *,
        charset: Optional[str] = None,
    ) -> MailboxOperationResult:
        return self._session.search(criteria, charset=charset)

    def fetch_messages(
        self,
        msg_set: MessageSet,
        *,
        load_level: LoadLevel = LoadLevel.HEADERS,
        batch_size: int = 50,
    ) -> Iterator[ImapMessage]:
        if load_level == LoadLevel.IDENTITY:
            for uid in msg_set.parsed_ids:
                msg = ImapMessage.from_uid(
                    self.account_id,
                    msg_set.mailbox or self.mailbox or "INBOX",
                    uid,
                    backend=self,
                )
                yield msg
            return
        parse_mode = _parse_mode_for(load_level)
        for fetched in self._session.iter_messages(
            msg_set, parse_mode=parse_mode, batch_size=batch_size
        ):
            imap_msg = ImapMessage.from_fetched(self.account_id, fetched)
            imap_msg._backend = self
            yield imap_msg

    def mark_seen(self, message: ImapMessage) -> None:
        msg_set = MessageSet.from_uids([message.uid], mailbox=message.mailbox)
        self._session.flags.add_flag(msg_set, Flag.SEEN)

    def mark_unseen(self, message: ImapMessage) -> None:
        msg_set = MessageSet.from_uids([message.uid], mailbox=message.mailbox)
        self._session.flags.remove_flag(msg_set, Flag.SEEN)

    def move_messages(
        self, uids: list[int], destination: str
    ) -> MailboxOperationResult:
        mailbox = self.mailbox or "INBOX"
        msg_set = MessageSet.from_uids(uids, mailbox=mailbox)
        return self._session.mailbox.uid_move(msg_set, destination)

    def delete_messages(
        self,
        uids: list[int],
        *,
        trash_folder: Optional[str] = None,
    ) -> MailboxOperationResult:
        mailbox = self.mailbox or "INBOX"
        msg_set = MessageSet.from_uids(uids, mailbox=mailbox)
        trash = trash_folder or self._session.special_folder(SpecialUse.TRASH)
        if not trash:
            raise ValueError("Trash folder not found")
        return self._session.mailbox.uid_trash(msg_set, trash)

    def capture_sync_state(self, mailbox: str) -> MailboxSyncState:
        return self._session.capture_sync_state(mailbox)

    def find_changed_uids(self, state: MailboxSyncState) -> MessageSet:
        return self._session.find_changed_since(state)

    def apply_after_sync(self, state: MailboxSyncState) -> MailboxSyncState:
        return self._session.sync.apply_after_sync(state)
