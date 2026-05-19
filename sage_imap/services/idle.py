"""IMAP IDLE with reconnection support."""

from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, List, Optional

from sage_imap.exceptions import IMAPConnectionError

if TYPE_CHECKING:
    from sage_imap.services.client import IMAPClient
    from sage_imap.services.mailbox import IMAPMailboxService

logger = logging.getLogger(__name__)

_IDLE_LINE_RE = re.compile(
    rb"^\*?\s*(\d+)\s+(EXISTS|EXPUNGE|FETCH|RECENT|FLAGS)",
    re.IGNORECASE,
)


@dataclass
class IdleEvent:
    """One untagged IDLE notification line."""

    raw: str
    sequence: Optional[int] = None
    event_type: Optional[str] = None

    @classmethod
    def from_line(cls, line: bytes) -> "IdleEvent":
        text = line.decode("utf-8", errors="replace").strip()
        match = _IDLE_LINE_RE.match(line.strip())
        if match:
            kind = match.group(2)
            if isinstance(kind, bytes):
                kind = kind.decode("ascii", errors="replace")
            return cls(
                raw=text,
                sequence=int(match.group(1)),
                event_type=str(kind).upper(),
            )
        return cls(raw=text)


@dataclass
class IdleWaitResult:
    """Result of waiting in IDLE."""

    events: List[IdleEvent] = field(default_factory=list)
    timed_out: bool = False
    reconnected: bool = False


class IMAPIdleSession:
    """
      Manage a single IDLE session on one connection.

    Only one thread should use IDLE on a connection at a time.
    """

    def __init__(self, client: "IMAPClient", mailbox: str) -> None:
        self.client = client
        self.mailbox = mailbox
        self._active = False

    def __enter__(self) -> "IMAPIdleSession":
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.done()

    def start(self) -> None:
        if not self.client.transport.has_capability("IDLE"):
            raise IMAPConnectionError(
                "Server does not support IDLE",
                code="idle_not_supported",
            )
        self.client.transport.idle_start()
        self._active = True

    def done(self) -> None:
        if self._active:
            self.client.transport.idle_done()
            self._active = False

    def wait(self, timeout: float = 60.0) -> IdleWaitResult:
        """
        Block until an untagged IDLE line arrives or ``timeout`` elapses.

        Caller must have called :meth:`start` first (or use as context manager).
        """
        if not self._active:
            raise RuntimeError("IDLE not started; call start() first")
        lines = self.client.transport.idle_read_lines(timeout=timeout)
        events = [IdleEvent.from_line(line) for line in lines if line.strip()]
        return IdleWaitResult(events=events, timed_out=not events)


class IMAPIdleWatcher:
    """
      Long-running IDLE loop with automatic reconnect and mailbox re-select.

      Parameters
      ----------
      client:
          Connected :class:`IMAPClient`.
      mailbox_service:
          Mailbox service used to ``select`` after reconnect.
      mailbox:
          Mailbox to watch (e.g. ``INBOX``).
      on_events:
          Callback invoked with :class:`IdleEvent` list after each IDLE cycle.
      idle_timeout:
          Seconds to wait per IDLE iteration (default 5 minutes).
    reconnect_delay:
          Delay before reconnect after errors.
    """

    def __init__(
        self,
        client: "IMAPClient",
        mailbox_service: "IMAPMailboxService",
        mailbox: str,
        on_events: Callable[[List[IdleEvent]], None],
        *,
        idle_timeout: float = 300.0,
        reconnect_delay: float = 5.0,
    ) -> None:
        self.client = client
        self.mailbox_service = mailbox_service
        self.mailbox = mailbox
        self.on_events = on_events
        self.idle_timeout = idle_timeout
        self.reconnect_delay = reconnect_delay
        self._running = False

    def stop(self) -> None:
        self._running = False

    def run_once(self) -> IdleWaitResult:
        """Run one IDLE wait cycle (start → wait → done)."""
        with IMAPIdleSession(self.client, self.mailbox) as session:
            return session.wait(timeout=self.idle_timeout)

    def run_until_stopped(self, max_cycles: Optional[int] = None) -> None:
        """
        Run IDLE in a loop, reconnecting on connection loss.

        Set ``max_cycles`` for testing; ``None`` runs until :meth:`stop`.
        """
        self._running = True
        cycles = 0
        while self._running:
            if max_cycles is not None and cycles >= max_cycles:
                break
            cycles += 1
            try:
                if not self.client.is_connected():
                    self.client.reconnect(self.mailbox)
                    self.mailbox_service.select(self.mailbox)
                result = self.run_once()
                if result.events:
                    self.on_events(result.events)
            except Exception as e:
                logger.warning("IDLE cycle failed: %s", e)
                try:
                    self.client.reconnect(self.mailbox)
                    self.mailbox_service.select(self.mailbox)
                except Exception as reconnect_err:
                    logger.error("IDLE reconnect failed: %s", reconnect_err)
                    time.sleep(self.reconnect_delay)
