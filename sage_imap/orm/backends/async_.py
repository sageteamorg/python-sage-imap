"""Async IMAP backend adapter."""

from __future__ import annotations

from typing import AsyncIterator, Optional, Union

from sage_imap.aio.session import AsyncIMAPSession
from sage_imap.helpers.enums import Flag
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.helpers.special_use import SpecialUse
from sage_imap.models.message import MessageSet
from sage_imap.orm.backends.sync import _parse_mode_for
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.models.message import ImapMessage
from sage_imap.services.mailbox.models import MailboxOperationResult
from sage_imap.sync.state import MailboxSyncState


class AsyncImapBackend:
    def __init__(self, session: AsyncIMAPSession, account_id: str) -> None:
        self._session = session
        self.account_id = account_id
        self.mailbox: Optional[str] = None

    async def select_mailbox(self, name: str) -> MailboxOperationResult:
        result = await self._session.select(name)
        if result.success:
            self.mailbox = name
        return result

    async def uid_search(
        self,
        criteria: Union[IMAPSearchCriteria, str],
        *,
        charset: Optional[str] = None,
    ) -> MailboxOperationResult:
        return await self._session.search(criteria, charset=charset)

    async def fetch_messages(
        self,
        msg_set: MessageSet,
        *,
        load_level: LoadLevel = LoadLevel.HEADERS,
        batch_size: int = 50,
    ) -> AsyncIterator[ImapMessage]:
        if load_level == LoadLevel.IDENTITY:
            for uid in msg_set.parsed_ids:
                yield ImapMessage.from_uid(
                    self.account_id,
                    msg_set.mailbox or self.mailbox or "INBOX",
                    uid,
                    backend=self,
                )
            return
        parse_mode = _parse_mode_for(load_level)
        async for fetched in self._session.iter_messages(
            msg_set, parse_mode=parse_mode, batch_size=batch_size
        ):
            imap_msg = ImapMessage.from_fetched(self.account_id, fetched)
            imap_msg._backend = self
            yield imap_msg

    async def mark_seen(self, message: ImapMessage) -> None:
        msg_set = MessageSet.from_uids([message.uid], mailbox=message.mailbox)
        await self._session.flags.add_flag(msg_set, Flag.SEEN)

    async def mark_unseen(self, message: ImapMessage) -> None:
        msg_set = MessageSet.from_uids([message.uid], mailbox=message.mailbox)
        await self._session.flags.remove_flag(msg_set, Flag.SEEN)

    async def move_messages(
        self, uids: list[int], destination: str
    ) -> MailboxOperationResult:
        mailbox = self.mailbox or "INBOX"
        msg_set = MessageSet.from_uids(uids, mailbox=mailbox)
        return await self._session.mailbox.uid_move(msg_set, destination)

    async def delete_messages(
        self,
        uids: list[int],
        *,
        trash_folder: Optional[str] = None,
    ) -> MailboxOperationResult:
        mailbox = self.mailbox or "INBOX"
        msg_set = MessageSet.from_uids(uids, mailbox=mailbox)
        trash = trash_folder or await self._session.special_folder(SpecialUse.TRASH)
        if not trash:
            raise ValueError("Trash folder not found")
        return await self._session.mailbox.uid_trash(msg_set, trash)

    async def capture_sync_state(self, mailbox: str) -> MailboxSyncState:
        return await self._session.capture_sync_state(mailbox)

    async def find_changed_uids(self, state: MailboxSyncState) -> MessageSet:
        return await self._session.find_changed_since(state)

    async def apply_after_sync(self, state: MailboxSyncState) -> MailboxSyncState:
        return await self.capture_sync_state(state.mailbox)
