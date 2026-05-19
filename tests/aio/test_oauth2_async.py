"""Tests for async OAuth2 token refresh."""

import time
from unittest.mock import AsyncMock, MagicMock

from sage_imap.auth.oauth2 import OAuth2Config, OAuth2TokenResponse
from sage_imap.auth.oauth2_async import (
    ensure_access_token_async,
    refresh_access_token_async,
)


class TestRefreshAccessTokenAsync:
    async def test_uses_httpx_when_available(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="refresh",
        )
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "access_token": "async_tok",
            "expires_in": 3600,
        }
        mock_response.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        mocker.patch("httpx.AsyncClient", return_value=mock_client)

        result = await refresh_access_token_async(cfg)
        assert result.access_token == "async_tok"
        assert cfg.access_token == "async_tok"

    async def test_falls_back_to_thread_without_httpx(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="refresh",
        )
        mocker.patch.dict("sys.modules", {"httpx": None})
        expected = OAuth2TokenResponse(access_token="thread_tok")
        mocker.patch(
            "sage_imap.auth.oauth2_async.refresh_access_token",
            return_value=expected,
        )
        mocker.patch(
            "asyncio.to_thread",
            new=AsyncMock(return_value=expected),
        )
        result = await refresh_access_token_async(cfg)
        assert result.access_token == "thread_tok"


class TestEnsureAccessTokenAsync:
    async def test_returns_cached_token(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            access_token="valid",
            expires_at=time.time() + 3600,
        )
        mocker.patch(
            "sage_imap.auth.oauth2_async.refresh_access_token_async",
            new=AsyncMock(),
        )
        assert await ensure_access_token_async(cfg) == "valid"

    async def test_refreshes_when_expired(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="r",
            expires_at=0.0,
        )
        mocker.patch(
            "sage_imap.auth.oauth2_async.refresh_access_token_async",
            new=AsyncMock(return_value=OAuth2TokenResponse(access_token="fresh")),
        )
        assert await ensure_access_token_async(cfg) == "fresh"
