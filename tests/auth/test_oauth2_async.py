"""Tests for auth.oauth2_async (also covered in tests/aio)."""

import time
from unittest.mock import AsyncMock, MagicMock

from sage_imap.auth.oauth2 import OAuth2Config
from sage_imap.auth.oauth2_async import ensure_access_token_async


class TestOAuth2AsyncAuthModule:
    async def test_ensure_refreshes_missing_token(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="r",
            expires_at=time.time() + 3600,
        )
        mocker.patch(
            "sage_imap.auth.oauth2_async.refresh_access_token_async",
            new=AsyncMock(return_value=MagicMock(access_token="new")),
        )
        assert await ensure_access_token_async(cfg) == "new"
