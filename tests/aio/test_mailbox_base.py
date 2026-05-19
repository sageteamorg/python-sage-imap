"""Tests for AsyncBaseMailboxService."""

from unittest.mock import AsyncMock, MagicMock

from sage_imap.aio.mailbox.base import AsyncBaseMailboxService
from sage_imap.helpers.enums import MailboxStatusItems


class TestAsyncBaseMailboxService:
    async def test_select_already_selected(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        svc.current_selection = "INBOX"
        result = await svc.select("INBOX")
        assert result.success
        assert result.metadata.get("already_selected")

    async def test_select_success(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        result = await svc.select("INBOX")
        assert result.success
        assert svc.current_selection == "INBOX"

    async def test_select_failure(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.select = AsyncMock(return_value=mock_aio_response("NO", []))
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        result = await svc.select("INBOX")
        assert not result.success

    async def test_close_no_selection(self):
        svc = AsyncBaseMailboxService(MagicMock())
        result = await svc.close()
        assert result.success
        assert result.metadata.get("no_mailbox_selected")

    async def test_close_success(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        svc.current_selection = "INBOX"
        result = await svc.close()
        assert result.success
        assert svc.current_selection is None

    async def test_check_success(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        result = await svc.check()
        assert result.success

    async def test_status_success(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.status = AsyncMock(
            return_value=mock_aio_response(lines=[b"INBOX (MESSAGES 1)"])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncBaseMailboxService(client)
        result = await svc.status("INBOX", MailboxStatusItems.MESSAGES)
        assert result.success
