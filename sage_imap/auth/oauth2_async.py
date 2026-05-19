"""Async OAuth2 token refresh via httpx (optional [async] extra)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sage_imap.auth.oauth2 import (
    OAuth2TokenResponse,
    _parse_token_response,
    refresh_access_token,
)

if TYPE_CHECKING:
    from sage_imap.auth.oauth2 import OAuth2Config


async def refresh_access_token_async(config: "OAuth2Config") -> OAuth2TokenResponse:
    """Refresh access token using httpx when available, else thread fallback."""
    try:
        import httpx
    except ImportError:
        import asyncio

        return await asyncio.to_thread(refresh_access_token, config)

    data = {
        "client_id": config.client_id,
        "client_secret": config.client_secret,
        "refresh_token": config.refresh_token,
        "grant_type": "refresh_token",
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config.token_url, data=data)
        response.raise_for_status()
        payload = response.json()
    result = _parse_token_response(payload)
    result.apply_to_config(config)
    return result


async def ensure_access_token_async(
    config: "OAuth2Config", skew_seconds: float = 60.0
) -> str:
    """Return a valid access token, refreshing via httpx when needed."""
    if config.is_access_token_expired(skew_seconds):
        token = await refresh_access_token_async(config)
        return token.access_token
    if not config.access_token:
        token = await refresh_access_token_async(config)
        return token.access_token
    return config.access_token
