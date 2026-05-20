"""IDLE subscriptions for ORM (dedicated connection recommended)."""

from __future__ import annotations

from contextlib import asynccontextmanager, contextmanager
from typing import TYPE_CHECKING, AsyncIterator, Iterator, Optional

if TYPE_CHECKING:
    from sage_imap.orm.config import ImapAccountConfig


class IdleSubscription:
    """Sync IDLE wrapper using a dedicated IMAPSession."""

    def __init__(self, session: object, mailbox: str) -> None:
        self._session = session
        self.mailbox = mailbox
        self._idle: Optional[object] = None

    @classmethod
    @contextmanager
    def for_mailbox(
        cls,
        account_id: str,
        mailbox: str,
        *,
        config: Optional["ImapAccountConfig"] = None,
        provider: Optional[object] = None,
    ) -> Iterator["IdleSubscription"]:
        from sage_imap.orm.session import ImapORM
        from sage_imap.services.idle import IMAPIdleSession

        if config is None and provider is not None:
            config = provider.get_config(account_id)
        if config is None:
            raise ValueError("config or provider required")
        with ImapORM.open(account_id, config=config) as orm:
            orm.select_mailbox(mailbox)
            session = orm.session
            if session is None:
                raise RuntimeError("ORM session not connected")
            with IMAPIdleSession(session.client, mailbox) as idle:
                sub = cls(session, mailbox)
                sub._idle = idle
                yield sub

    def wait(self, timeout: float = 120.0):
        from sage_imap.services.idle import IMAPIdleSession

        idle = getattr(self, "_idle", None)
        if idle is None:
            idle = IMAPIdleSession(self._session.client, self.mailbox)  # type: ignore[attr-defined]
            idle.start()
            try:
                return idle.wait(timeout=timeout)
            finally:
                idle.done()
        return idle.wait(timeout=timeout)


class AsyncIdleSubscription:
    """Async IDLE wrapper (requires sage_imap.aio.idle)."""

    def __init__(self, session: object, mailbox: str) -> None:
        self._session = session
        self.mailbox = mailbox
        self._idle: Optional[object] = None

    @classmethod
    @asynccontextmanager
    async def for_mailbox(
        cls,
        account_id: str,
        mailbox: str,
        *,
        config: Optional["ImapAccountConfig"] = None,
        provider: Optional[object] = None,
    ) -> AsyncIterator["AsyncIdleSubscription"]:
        from sage_imap.orm.async_session import AsyncImapORM

        async with AsyncImapORM.open(
            account_id, config=config, provider=provider  # type: ignore[arg-type]
        ) as orm:
            await orm.select_mailbox(mailbox)
            session = orm.session
            if session is None:
                raise RuntimeError("ORM session not connected")
            from sage_imap.aio.idle import AsyncIMAPIdleSession

            async with AsyncIMAPIdleSession(session.client, mailbox) as idle:
                sub = cls(session, mailbox)
                sub._idle = idle
                yield sub

    async def wait(self, timeout: float = 120.0):
        idle = getattr(self, "_idle", None)
        if idle is None:
            raise RuntimeError("IdleSubscription used outside context manager")
        return await idle.wait(timeout=timeout)
