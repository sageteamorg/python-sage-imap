"""Tests for AsyncIMAPFolderService."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.aio.folder import AsyncIMAPFolderService
from sage_imap.exceptions import IMAPFolderOperationError
from sage_imap.helpers.special_use import SpecialUse
from sage_imap.services.folder import FolderInfo


class TestAsyncIMAPFolderService:
    async def test_list_folders(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        folders = await svc.list_folders()
        assert any(f.name == "INBOX" for f in folders)

    async def test_list_folders_cached(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        first = await svc.list_folders()
        second = await svc.list_folders()
        assert first == second
        assert mock_aio_connection.list.await_count == 1

    async def test_list_folders_failure(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.list = AsyncMock(return_value=mock_aio_response("NO", []))
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        with pytest.raises(IMAPFolderOperationError):
            await svc.list_folders()

    async def test_list_folders_enrich(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.status = AsyncMock(
            return_value=mock_aio_response(
                lines=[b"INBOX (MESSAGES 5 RECENT 0 UNSEEN 2)"]
            )
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        folders = await svc.list_folders(enrich=True)
        inbox = next(f for f in folders if f.name == "INBOX")
        assert inbox.message_count == 5
        assert inbox.unseen_count == 2

    async def test_get_namespace(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        ns = await svc.get_namespace()
        assert ns.personal is not None

    async def test_get_special_folders(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        mapping = await svc.get_special_folders()
        assert SpecialUse.INBOX in mapping

    async def test_find_by_special_use_string(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        info = await svc.find_by_special_use("\\Sent")
        assert info is None or info.name == "Sent"

    async def test_cache_hit_by_key(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        svc = AsyncIMAPFolderService(client)
        svc._cache_expiry = datetime.now() + timedelta(seconds=300)
        svc._folder_cache[":*:enrich=False"] = [
            FolderInfo(name="Cached", attributes=[])
        ]
        folders = await svc.list_folders()
        assert folders[0].name == "Cached"
