"""Async IMAP IDLE support."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from sage_imap.exceptions import IMAPConnectionError
from sage_imap.services.idle import IdleEvent

if TYPE_CHECKING:
    from sage_imap.aio.client import AsyncIMAPClient

logger = logging.getLogger(__name__)


@dataclass
class AsyncIdleWaitResult:
    events: List[IdleEvent] = field(default_factory=list)
    timed_out: bool = False


class AsyncIMAPIdleSession:
    """Manage a single async IDLE session on one connection."""

    def __init__(self, client: "AsyncIMAPClient", mailbox: str) -> None:
        self.client = client
        self.mailbox = mailbox
        self._active = False

    async def __aenter__(self) -> "AsyncIMAPIdleSession":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.done()

    async def start(self) -> None:
        if not await self.client.transport.has_capability("IDLE"):
            raise IMAPConnectionError(
                "Server does not support IDLE",
                code="idle_not_supported",
            )
        await self.client.transport.idle_start()
        self._active = True

    async def done(self) -> None:
        if self._active:
            await self.client.transport.idle_done()
            self._active = False

    async def wait(self, timeout: float = 60.0) -> AsyncIdleWaitResult:
        if not self._active:
            raise RuntimeError("IDLE not started; call start() first")
        lines = await self.client.transport.idle_read_lines(timeout=timeout)
        events = [IdleEvent.from_line(line) for line in lines if line.strip()]
        return AsyncIdleWaitResult(events=events, timed_out=not events)


class AsyncIMAPIdleWatcher:
    """Background IDLE watcher as an :class:`asyncio.Task`."""

    def __init__(
        self,
        client: "AsyncIMAPClient",
        mailbox: str,
        on_event=None,
        *,
        poll_timeout: float = 60.0,
    ) -> None:
        self._session = AsyncIMAPIdleSession(client, mailbox)
        self._on_event = on_event
        self._poll_timeout = poll_timeout
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        await self._session.start()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        await self._session.done()

    async def _loop(self) -> None:
        while True:
            result = await self._session.wait(timeout=self._poll_timeout)
            for event in result.events:
                if self._on_event:
                    self._on_event(event)
