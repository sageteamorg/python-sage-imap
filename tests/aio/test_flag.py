"""Tests for AsyncIMAPFlagService."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.aio.flag import AsyncIMAPFlagService
from sage_imap.exceptions import IMAPFlagOperationError
from sage_imap.helpers.enums import Flag
from sage_imap.models.message import MessageSet


class TestAsyncIMAPFlagService:
    async def test_add_flag(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        mailbox.current_selection = "INBOX"
        svc = AsyncIMAPFlagService(mailbox)
        svc.current_selection = "INBOX"
        result = await svc.add_flag(MessageSet.from_uids([1]), Flag.SEEN)
        assert result.success

    async def test_remove_flag(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        mailbox.current_selection = "INBOX"
        svc = AsyncIMAPFlagService(mailbox)
        svc.current_selection = "INBOX"
        result = await svc.remove_flag(MessageSet.from_uids([2]), Flag.SEEN)
        assert result.success

    async def test_store_failure(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.protocol.store = AsyncMock(
            return_value=mock_aio_response("NO", [])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        mailbox.current_selection = "INBOX"
        svc = AsyncIMAPFlagService(mailbox)
        svc.current_selection = "INBOX"
        result = await svc.add_flag(MessageSet.from_uids([1]), Flag.SEEN)
        assert not result.success

    async def test_store_raises_flag_error(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.protocol.store = AsyncMock(side_effect=RuntimeError("boom"))
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        mailbox.current_selection = "INBOX"
        svc = AsyncIMAPFlagService(mailbox)
        svc.current_selection = "INBOX"
        with pytest.raises(IMAPFlagOperationError):
            await svc.add_flag(MessageSet.from_uids([1]), Flag.SEEN)
