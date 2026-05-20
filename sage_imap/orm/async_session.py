"""Async ORM session root."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import TYPE_CHECKING, AsyncIterator, Optional

from sage_imap.orm.backends.async_ import AsyncImapBackend
from sage_imap.orm.config import AccountProvider, ImapAccountConfig
from sage_imap.orm.exceptions import OrmConfigurationError
from sage_imap.orm.managers import _active_orm

if TYPE_CHECKING:
    from sage_imap.aio.session import AsyncIMAPSession


class AsyncImapORM:
    """Async ORM entry (requires ``python-sage-imap[orm,async]``)."""

    def __init__(
        self,
        account_id: str,
        backend: AsyncImapBackend,
        *,
        config: Optional[ImapAccountConfig] = None,
        _session: Optional["AsyncIMAPSession"] = None,
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
    @asynccontextmanager
    async def open(
        cls,
        account_id: str,
        *,
        provider: Optional[AccountProvider] = None,
        config: Optional[ImapAccountConfig] = None,
        session: Optional["AsyncIMAPSession"] = None,
    ) -> AsyncIterator["AsyncImapORM"]:
        import importlib.util

        if importlib.util.find_spec("aioimaplib") is None:
            raise ImportError(
                "Async ORM requires python-sage-imap[async]. "
                "Install with: pip install python-sage-imap[orm,async]"
            )
        from sage_imap.aio.session import AsyncIMAPSession

        if config is None and provider is not None:
            config = provider.get_config(account_id)
        if session is None:
            if config is None:
                raise OrmConfigurationError(
                    "Provide config, provider, or an existing AsyncIMAPSession"
                )
            conn = config.to_connection_config()
            session = AsyncIMAPSession.from_config(
                conn, oauth_config=config.oauth_config
            )
            owns = True
        else:
            owns = False
        backend = AsyncImapBackend(session, account_id)
        orm = cls(
            account_id, backend, config=config, _session=session, _owns_session=owns
        )
        async with orm:
            yield orm

    async def __aenter__(self) -> "AsyncImapORM":
        if self._session and self._owns_session:
            await self._session.connect()
        self._token = _active_orm.set(self)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._token is not None:
            _active_orm.reset(self._token)
            self._token = None
        if self._session and self._owns_session:
            await self._session.close()

    async def select_mailbox(self, name: str) -> None:
        result = await self.backend.select_mailbox(name)
        if result.success:
            self.mailbox = name

    @property
    def session(self) -> Optional["AsyncIMAPSession"]:
        return self._session
