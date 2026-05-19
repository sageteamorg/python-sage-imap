"""Async mailbox operation tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.aio.mailbox.operations import AsyncIMAPMailboxUIDService
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet


class TestAsyncMailboxOperations:
    async def test_uid_search(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH 42"])
        )
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        result = await svc.uid_search(IMAPSearchCriteria.ALL)
        assert result.success
        assert "42" in result.affected_messages

    async def test_iter_uid_fetch(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        msg_set = MessageSet.from_uids([1])
        messages = []
        async for msg in svc.iter_uid_fetch(msg_set, batch_size=10):
            messages.append(msg)
        assert isinstance(messages, list)

    async def test_uid_search_failure(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response("NO", [b"bad"])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        result = await svc.uid_search(IMAPSearchCriteria.ALL)
        assert not result.success

    async def test_create_message_set_from_search(
        self, mock_aio_connection, mock_aio_response
    ):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH 7"])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        msg_set = await svc.create_message_set_from_search(IMAPSearchCriteria.ALL)
        assert 7 in msg_set

    async def test_create_message_set_raises_when_empty(
        self, mock_aio_connection, mock_aio_response
    ):
        from sage_imap.aio.transport import AsyncIMAPTransport
        from sage_imap.exceptions import IMAPMailboxError

        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH"])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        with pytest.raises(IMAPMailboxError):
            await svc.create_message_set_from_search(IMAPSearchCriteria.ALL)

    async def test_uid_move(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        result = await svc.uid_move(MessageSet.from_uids([1]), "Archive")
        assert result.success

    async def test_uid_trash(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        result = await svc.uid_trash(MessageSet.from_uids([1]), "Trash")
        assert result.success

    async def test_sync_property_lazy(self, mock_aio_connection):
        from sage_imap.aio.sync.service import AsyncIMAPSyncService
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPMailboxUIDService(client)
        assert isinstance(svc.sync, AsyncIMAPSyncService)
