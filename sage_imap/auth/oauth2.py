"""OAuth2 helpers for IMAP XOAUTH2 authentication."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class OAuth2Config:
    """Configuration for OAuth2 token exchange."""

    client_id: str
    client_secret: str
    token_url: str
    scopes: Optional[list[str]] = None
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None
    expires_at: Optional[float] = None

    def is_access_token_expired(self, skew_seconds: float = 60.0) -> bool:
        """Return True if the cached access token is missing or near expiry."""
        if not self.access_token or self.expires_at is None:
            return True
        return time.time() >= (self.expires_at - skew_seconds)


@dataclass
class OAuth2TokenResponse:
    """Token endpoint response used for refresh flows."""

    access_token: str
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    token_type: str = "Bearer"
    raw: Dict[str, Any] = field(default_factory=dict)

    def apply_to_config(self, config: OAuth2Config) -> None:
        """Update *config* with tokens from this response (for rotation)."""
        config.access_token = self.access_token
        if self.refresh_token:
            config.refresh_token = self.refresh_token
        if self.expires_in is not None:
            config.expires_at = time.time() + float(self.expires_in)


def build_xoauth2_string(username: str, access_token: str) -> str:
    """Build SASL XOAUTH2 initial client response."""
    return f"user={username}\x01auth=Bearer {access_token}\x01\x01"


def _parse_token_response(body: Dict[str, Any]) -> OAuth2TokenResponse:
    token = body.get("access_token")
    if not token:
        raise ValueError(f"No access_token in response: {body}")
    return OAuth2TokenResponse(
        access_token=str(token),
        expires_in=body.get("expires_in"),
        refresh_token=body.get("refresh_token"),
        token_type=str(body.get("token_type", "Bearer")),
        raw=body,
    )


def _post_token_request(data: Dict[str, str], token_url: str) -> Dict[str, Any]:
    encoded = urllib.parse.urlencode(data).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=encoded,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        return json.loads(response.read().decode("utf-8"))


def refresh_access_token(config: OAuth2Config) -> OAuth2TokenResponse:
    """
    Obtain a new access token using the refresh_token grant.

    Updates ``config`` in place when the provider returns a rotated refresh token
    or expiry metadata.
    """
    if not config.refresh_token:
        raise ValueError("refresh_token is required for refresh_access_token")

    body = _post_token_request(
        {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        },
        config.token_url,
    )
    result = _parse_token_response(body)
    result.apply_to_config(config)
    return result


def fetch_access_token(config: OAuth2Config) -> str:
    """
    Fetch an access token using refresh_token grant (stdlib urllib only).

    Prefer :func:`refresh_access_token` when you need expiry and token rotation.
    """
    return refresh_access_token(config).access_token


def ensure_access_token(config: OAuth2Config, skew_seconds: float = 60.0) -> str:
    """
    Return a valid access token, refreshing when expired or missing.

    Parameters
    ----------
    config:
        OAuth2 configuration with ``refresh_token``.
    skew_seconds:
        Refresh this many seconds before ``expires_at``.
    """
    if not config.is_access_token_expired(skew_seconds):
        if config.access_token is None:
            raise ValueError("access_token missing despite valid expiry")
        return config.access_token
    return refresh_access_token(config).access_token
