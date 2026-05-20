"""Sync ORM session root."""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Iterator, Optional

from sage_imap.orm.backends.sync import SyncImapBackend
from sage_imap.orm.config import AccountProvider, ImapAccountConfig
from sage_imap.orm.exceptions import OrmConfigurationError
from sage_imap.orm.managers import _active_orm
from sage_imap.session import IMAPSession

if TYPE_CHECKING:
    pass


class ImapORM:
    """
    Sync ORM entry point.

    Example
    -------
    >>> with ImapORM.open(account_id="a1", config=cfg) as orm:
    ...     orm.select_mailbox("INBOX")
    ...     for msg in ImapMessage.objects.filter(unread=True).limit(10).iter():
    ...         print(msg.subject)
    """

    def __init__(
        self,
        account_id: str,
        backend: SyncImapBackend,
        *,
        config: Optional[ImapAccountConfig] = None,
        _session: Optional[IMAPSession] = None,
        _owns_session: bool = True,
    ) -> None:
        self.account_id = account_id
        self.backend = backend
        self.config = config
        self.mailbox: Optional[str] = None
        self._session = _session
        self._owns_session = _owns_session
        self._token = None

    @classmethod
    @contextmanager
    def open(
        cls,
        account_id: str,
        *,
        provider: Optional[AccountProvider] = None,
        config: Optional[ImapAccountConfig] = None,
        session: Optional[IMAPSession] = None,
        registry: Optional[object] = None,
    ) -> Iterator["ImapORM"]:
        from sage_imap.orm.config import ConnectionPolicy
        from sage_imap.orm.connections.registry import get_connection_registry

        if config is None and provider is not None:
            config = provider.get_config(account_id)
        owns = False
        if session is None:
            if config is None:
                raise OrmConfigurationError(
                    "Provide config, provider, or an existing IMAPSession"
                )
            reg = registry or get_connection_registry()
            if config.connection_policy in (
                ConnectionPolicy.POOLED,
                ConnectionPolicy.LONG_LIVED,
            ):
                session = reg.get_or_create(config)  # type: ignore[union-attr]
                owns = False
            else:
                session = cls._session_from_config(config)
                owns = True
        backend = SyncImapBackend(session, account_id)
        orm = cls(
            account_id, backend, config=config, _session=session, _owns_session=owns
        )
        with orm:
            yield orm

    @staticmethod
    def _session_from_config(config: ImapAccountConfig) -> IMAPSession:
        conn = config.to_connection_config()
        if config.use_pool or config.connection_policy.value == "pooled":
            session = IMAPSession.from_config(conn, oauth_config=config.oauth_config)
            session.client.use_pool = True
            return session
        return IMAPSession.from_config(conn, oauth_config=config.oauth_config)

    def __enter__(self) -> "ImapORM":
        if self._session and self._owns_session:
            self._session.connect()
        self._token = _active_orm.set(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            _active_orm.reset(self._token)
            self._token = None
        if self._session and self._owns_session:
            self._session.close()

    def select_mailbox(self, name: str) -> None:
        result = self.backend.select_mailbox(name)
        if result.success:
            self.mailbox = name

    @property
    def session(self) -> Optional[IMAPSession]:
        return self._session
