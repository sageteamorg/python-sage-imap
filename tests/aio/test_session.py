"""Tests for AsyncIMAPSession."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.aio.session import AsyncIMAPSession
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet


class TestAsyncIMAPSession:
    async def test_search_delegates_to_mailbox(self, mock_aio_response):
        session = AsyncIMAPSession("imap.test", "user", "pass")
        session.client = MagicMock()
        session.client.transport = MagicMock()
        session._mailbox = MagicMock()
        session._mailbox.uid_search = AsyncMock(
            return_value=MagicMock(success=True, affected_messages=["1"])
        )
        result = await session.search(IMAPSearchCriteria.UNSEEN)
        assert result.success
        session._mailbox.uid_search.assert_awaited_once()

    def test_import_guard_message(self):
        import sage_imap.aio as aio_pkg

        assert "[async]" in aio_pkg._MISSING_ASYNC_EXTRA

    def test_init_requires_host_when_no_config(self):
        with pytest.raises(ValueError, match="host and username"):
            AsyncIMAPSession("", "")

    async def test_from_config(self):
        from sage_imap.services.client import ConnectionConfig

        config = ConnectionConfig(host="h", username="u", password="p")
        session = AsyncIMAPSession.from_config(config)
        assert session.config is config

    async def test_context_manager(self, mocker):
        session = AsyncIMAPSession("h", "u", "p")
        mocker.patch.object(session.client, "connect", new=AsyncMock())
        mocker.patch.object(session.client, "disconnect", new=AsyncMock())
        mocker.patch.object(session.mailbox, "close", new=AsyncMock())
        async with session:
            pass
        session.client.connect.assert_awaited_once()
        session.client.disconnect.assert_awaited_once()

    async def test_oauth_connect(self, mocker):
        from sage_imap.auth.oauth2 import OAuth2Config

        session = AsyncIMAPSession(
            "h", "u", oauth_config=OAuth2Config("id", "s", "https://t")
        )
        mocker.patch.object(session.client, "connect_with_oauth", new=AsyncMock())
        await session.connect()
        session.client.connect_with_oauth.assert_awaited_once()

    async def test_iter_messages(self, mocker):
        session = AsyncIMAPSession("h", "u", "p")

        async def _gen():
            yield MagicMock()

        session._mailbox = MagicMock()
        session._mailbox.iter_uid_fetch = mocker.Mock(return_value=_gen())
        msgs = [m async for m in session.iter_messages(MessageSet.from_uids([1]))]
        assert len(msgs) == 1

    async def test_capture_sync_and_namespace(self, mocker):
        session = AsyncIMAPSession("h", "u", "p")
        session._mailbox = MagicMock()
        session._mailbox.current_selection = "INBOX"
        session._mailbox.sync = MagicMock()
        session._mailbox.sync.capture_state = AsyncMock(
            return_value=MagicMock(mailbox="INBOX")
        )
        session._mailbox.sync.find_changed_uids = AsyncMock(
            return_value=MessageSet.empty(mailbox="INBOX")
        )
        session._folders = MagicMock()
        session._folders.get_namespace = AsyncMock(return_value=MagicMock())
        session._folders.find_by_special_use = AsyncMock(return_value=None)

        await session.capture_sync_state()
        await session.find_changed_since(MagicMock())
        await session.namespace()
        assert await session.special_folder("Sent") is None
