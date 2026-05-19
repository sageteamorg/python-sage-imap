"""High-level async IMAP session facade."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, AsyncIterator, Optional, Union

from sage_imap.aio.client import AsyncIMAPClient
from sage_imap.aio.flag import AsyncIMAPFlagService
from sage_imap.aio.folder import AsyncIMAPFolderService
from sage_imap.aio.mailbox import AsyncIMAPMailboxUIDService
from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig
from sage_imap.services.mailbox.models import MailboxOperationResult

if TYPE_CHECKING:
    from sage_imap.auth.oauth2 import OAuth2Config
    from sage_imap.helpers.special_use import NamespaceMap, SpecialUse
    from sage_imap.sync import MailboxSyncState

logger = logging.getLogger(__name__)


class AsyncIMAPSession:
    """
    Unified async facade over client, mailbox, folder, and flag services.

    Import from ``sage_imap.aio`` (requires ``pip install python-sage-imap[async]``).
    """

    def __init__(
        self,
        host: str = "",
        username: str = "",
        password: Optional[str] = None,
        *,
        port: int = 993,
        use_ssl: bool = True,
        config: Optional[ConnectionConfig] = None,
        oauth_config: Optional["OAuth2Config"] = None,
        **kwargs: Any,
    ) -> None:
        if config is not None:
            self.config = config
        else:
            if not host or not username:
                raise ValueError(
                    "host and username are required when config is omitted"
                )
            self.config = ConnectionConfig(
                host=host,
                username=username,
                password=password or "",
                port=port,
                use_ssl=use_ssl,
                **kwargs,
            )
        self.oauth_config = oauth_config
        self.client = AsyncIMAPClient.from_config(self.config)
        self._mailbox: Optional[AsyncIMAPMailboxUIDService] = None
        self._folders: Optional[AsyncIMAPFolderService] = None
        self._flags: Optional[AsyncIMAPFlagService] = None

    @classmethod
    def from_config(
        cls,
        config: ConnectionConfig,
        *,
        oauth_config: Optional["OAuth2Config"] = None,
    ) -> "AsyncIMAPSession":
        return cls("", "", config=config, oauth_config=oauth_config)

    @property
    def mailbox(self) -> AsyncIMAPMailboxUIDService:
        if self._mailbox is None:
            self._mailbox = AsyncIMAPMailboxUIDService(self.client)
        return self._mailbox

    @property
    def folders(self) -> AsyncIMAPFolderService:
        if self._folders is None:
            self._folders = AsyncIMAPFolderService(self.client)
        return self._folders

    @property
    def flags(self) -> AsyncIMAPFlagService:
        if self._flags is None:
            self._flags = AsyncIMAPFlagService(self.mailbox)
        return self._flags

    @property
    def sync(self):
        return self.mailbox.sync

    async def __aenter__(self) -> "AsyncIMAPSession":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def connect(self) -> None:
        if self.oauth_config is not None:
            await self.client.connect_with_oauth(
                self.oauth_config, username=self.config.username
            )
        else:
            await self.client.connect()

    async def close(self) -> None:
        try:
            await self.mailbox.close()
        except Exception as e:
            logger.debug("Mailbox close during async session shutdown: %s", e)
        await self.client.disconnect()

    async def select(self, mailbox: str = "INBOX") -> MailboxOperationResult:
        return await self.mailbox.select(mailbox)

    async def search(
        self, criteria: Union[IMAPSearchCriteria, str], charset: str = "UTF-8"
    ) -> MailboxOperationResult:
        return await self.mailbox.uid_search(criteria, charset=charset)

    async def iter_messages(
        self,
        msg_set: MessageSet,
        *,
        parse_mode: ParseMode = ParseMode.FULL,
        batch_size: int = 50,
    ) -> AsyncIterator[EmailMessage]:
        async for msg in self.mailbox.iter_uid_fetch(
            msg_set, parse_mode=parse_mode, batch_size=batch_size
        ):
            yield msg

    async def capture_sync_state(
        self, mailbox: Optional[str] = None
    ) -> "MailboxSyncState":
        name = mailbox or self.mailbox.current_selection or "INBOX"
        return await self.sync.capture_state(name)

    async def find_changed_since(self, state: "MailboxSyncState") -> MessageSet:
        return await self.sync.find_changed_uids(state)

    async def namespace(self, *, refresh: bool = False) -> "NamespaceMap":
        return await self.folders.get_namespace(refresh=refresh)

    async def special_folder(self, use: Union["SpecialUse", str]) -> Optional[str]:
        info = await self.folders.find_by_special_use(use)
        return info.name if info else None
