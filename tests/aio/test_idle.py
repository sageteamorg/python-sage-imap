"""Tests for async IDLE session and watcher."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.aio.idle import AsyncIMAPIdleSession, AsyncIMAPIdleWatcher
from sage_imap.exceptions import IMAPConnectionError


class TestAsyncIMAPIdleSession:
    async def test_context_manager(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)

        async with AsyncIMAPIdleSession(client, "INBOX") as session:
            assert session._active
        assert not session._active
        mock_aio_connection.idle_done.assert_called()

    async def test_start_requires_idle_capability(self):
        client = MagicMock()
        client.transport = MagicMock()
        client.transport.has_capability = AsyncMock(return_value=False)
        session = AsyncIMAPIdleSession(client, "INBOX")
        with pytest.raises(IMAPConnectionError, match="IDLE"):
            await session.start()

    async def test_wait_not_started(self):
        session = AsyncIMAPIdleSession(MagicMock(), "INBOX")
        with pytest.raises(RuntimeError, match="not started"):
            await session.wait()

    async def test_wait_timeout(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        mock_aio_connection.wait_server_push = AsyncMock(
            return_value=MagicMock(result="OK", lines=[])
        )
        client.transport = transport

        session = AsyncIMAPIdleSession(client, "INBOX")
        await session.start()
        result = await session.wait(timeout=0.1)
        await session.done()
        assert result.timed_out is True


class TestAsyncIMAPIdleWatcher:
    async def test_start_and_stop(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        client.transport = transport
        events = []

        watcher = AsyncIMAPIdleWatcher(
            client, "INBOX", on_event=lambda e: events.append(e), poll_timeout=0.01
        )
        await watcher.start()
        await watcher.stop()
        assert watcher._task is None or watcher._task.done()
