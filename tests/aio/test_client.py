"""Tests for AsyncIMAPClient."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sage_imap.aio.client import AsyncIMAPClient
from sage_imap.services.client import ConnectionConfig


class TestAsyncIMAPClient:
    async def test_connect_binds_transport(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            client = AsyncIMAPClient("imap.test", "user", "pass")
            await client.connect()
            assert client.authenticated
            assert client.transport.connection is mock_imap
            await client.disconnect()

    async def test_from_config(self):
        config = ConnectionConfig(host="h", username="u", password="p")
        client = AsyncIMAPClient.from_config(config)
        assert client.config.host == "h"

    async def test_connect_oauth2(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.xoauth2 = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            client = AsyncIMAPClient("imap.test", "user")
            await client.connect_oauth2("user", "token")
            assert client.authenticated
            await client.disconnect()

    async def test_connect_with_oauth(self, mock_aio_response, mocker):
        from sage_imap.auth.oauth2 import OAuth2Config

        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.xoauth2 = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        mocker.patch(
            "sage_imap.auth.oauth2_async.ensure_access_token_async",
            new=AsyncMock(return_value="oauth_tok"),
        )
        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            client = AsyncIMAPClient("imap.test", "user")
            cfg = OAuth2Config("id", "secret", "https://t", refresh_token="r")
            await client.connect_with_oauth(cfg)
            assert client.authenticated

    async def test_connect_with_oauth_refresh_false_no_token(self):
        from sage_imap.auth.oauth2 import OAuth2Config

        client = AsyncIMAPClient("imap.test", "user")
        cfg = OAuth2Config("id", "secret", "https://t")
        with pytest.raises(ValueError, match="access_token"):
            await client.connect_with_oauth(cfg, refresh=False)

    async def test_login_failure(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock(return_value=MagicMock(result="NO", lines=[]))
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            from sage_imap.exceptions import IMAPAuthenticationError

            client = AsyncIMAPClient("imap.test", "user", "bad")
            with pytest.raises(IMAPAuthenticationError):
                await client.connect()

    async def test_is_connected_and_health_check(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock(return_value=mock_aio_response())
        mock_imap.noop = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            client = AsyncIMAPClient("imap.test", "user", "pass")
            await client.connect()
            assert await client.is_connected()
            health = await client.health_check()
            assert health["is_connected"] is True
            await client.disconnect()

    async def test_reconnect(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock(return_value=mock_aio_response())
        mock_imap.noop = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            client = AsyncIMAPClient("imap.test", "user", "pass")
            await client.connect()
            client.note_selected_mailbox("INBOX")
            await client.reconnect()
            assert client._selected_mailbox == "INBOX"
            await client.disconnect()

    async def test_context_manager(self, mock_aio_response):
        mock_imap = MagicMock()
        mock_imap.wait_hello_from_server = AsyncMock()
        mock_imap.login = AsyncMock(return_value=mock_aio_response())
        mock_imap.logout = AsyncMock(return_value=mock_aio_response())
        mock_imap.protocol = MagicMock()
        mock_imap.protocol.capabilities = {"IMAP4REV1"}

        with patch("aioimaplib.IMAP4_SSL", return_value=mock_imap):
            async with AsyncIMAPClient("imap.test", "user", "pass") as client:
                assert client.authenticated
