"""
High-level IMAP session facade.

Use :class:`IMAPSession` as the primary entry point: it wires the client,
UID mailbox service, folders, flags, and sync helpers behind one object.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.folder import IMAPFolderService
from sage_imap.services.mailbox import IMAPMailboxUIDService
from sage_imap.services.mailbox.models import MailboxOperationResult

if TYPE_CHECKING:
    from sage_imap.auth.oauth2 import OAuth2Config
    from sage_imap.helpers.special_use import NamespaceMap, SpecialUse
    from sage_imap.sync import IMAPSyncService, MailboxSyncState

logger = logging.getLogger(__name__)


class IMAPSession:
    """
    Unified facade over client, mailbox, folder, and flag services.

    Example
    -------
    >>> with IMAPSession("imap.example.com", "user@example.com", "secret") as session:
    ...     session.select("INBOX")
    ...     result = session.search(IMAPSearchCriteria.UNSEEN)
    ...     trash = session.folders.resolve_standard_mailbox("Trash")
    ...     for msg in session.iter_messages(result.to_uid_message_set()):
    ...         print(msg.subject)
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
        self.client = IMAPClient.from_config(self.config)
        self._mailbox: Optional[IMAPMailboxUIDService] = None
        self._folders: Optional[IMAPFolderService] = None
        self._flags: Optional[IMAPFlagService] = None

    @classmethod
    def from_config(
        cls,
        config: ConnectionConfig,
        *,
        oauth_config: Optional["OAuth2Config"] = None,
    ) -> "IMAPSession":
        """Build a session from an existing :class:`ConnectionConfig`."""
        return cls("", "", config=config, oauth_config=oauth_config)

    @property
    def mailbox(self) -> IMAPMailboxUIDService:
        if self._mailbox is None:
            self._mailbox = IMAPMailboxUIDService(self.client)
        return self._mailbox

    @property
    def folders(self) -> IMAPFolderService:
        if self._folders is None:
            self._folders = IMAPFolderService(self.client)
        return self._folders

    @property
    def flags(self) -> IMAPFlagService:
        if self._flags is None:
            self._flags = IMAPFlagService(self.mailbox)
        return self._flags

    @property
    def sync(self) -> "IMAPSyncService":
        return self.mailbox.sync

    def __enter__(self) -> "IMAPSession":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def connect(self) -> None:
        """Authenticate and bind the transport layer."""
        if self.oauth_config is not None:
            self.client.connect_with_oauth(
                self.oauth_config, username=self.config.username
            )
        else:
            self.client.connect()

    def close(self) -> None:
        """Close the selected mailbox and disconnect."""
        try:
            self.mailbox.close()
        except Exception as e:
            logger.debug("Mailbox close during session shutdown: %s", e)
        self.client.disconnect()

    def select(self, mailbox: str = "INBOX") -> MailboxOperationResult:
        """Select a mailbox for UID operations."""
        return self.mailbox.select(mailbox)

    def search(
        self,
        criteria: Union[IMAPSearchCriteria, str],
        charset: Optional[str] = None,
    ) -> MailboxOperationResult:
        """UID SEARCH in the current mailbox.

        Charset is omitted by default (ASCII criteria). Pass ``charset="UTF-8"``
        only when the server supports SEARCH CHARSET and your criteria need it.
        """
        return self.mailbox.uid_search(criteria, charset=charset)

    def iter_messages(
        self,
        msg_set: MessageSet,
        *,
        parse_mode: ParseMode = ParseMode.FULL,
        batch_size: int = 50,
    ) -> Iterator[EmailMessage]:
        """Stream messages with batched UID FETCH."""
        yield from self.mailbox.iter_uid_fetch(
            msg_set, parse_mode=parse_mode, batch_size=batch_size
        )

    def capture_sync_state(self, mailbox: Optional[str] = None) -> "MailboxSyncState":
        """Snapshot CONDSTORE / UIDVALIDITY state for incremental sync."""
        name = mailbox or self.mailbox.current_selection or "INBOX"
        return self.sync.capture_state(name)

    def find_changed_since(self, state: "MailboxSyncState") -> MessageSet:
        """Return UIDs changed since a prior sync state."""
        return self.sync.find_changed_uids(state)

    def namespace(self, *, refresh: bool = False) -> "NamespaceMap":
        """Server folder namespaces (RFC 2342)."""
        return self.folders.get_namespace(refresh=refresh)

    def special_folder(self, use: Union["SpecialUse", str]) -> Optional[str]:
        """Resolve SPECIAL-USE folder name (e.g. Sent, Trash)."""
        info = self.folders.find_by_special_use(use)
        return info.name if info else None
