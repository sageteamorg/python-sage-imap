"""OAuth2 helpers for IMAP XOAUTH2 authentication."""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Optional


@dataclass
class OAuth2Config:
    """Configuration for OAuth2 token exchange."""

    client_id: str
    client_secret: str
    token_url: str
    scopes: Optional[list[str]] = None
    refresh_token: Optional[str] = None


def build_xoauth2_string(username: str, access_token: str) -> str:
    """Build SASL XOAUTH2 initial client response."""
    return f"user={username}\x01auth=Bearer {access_token}\x01\x01"


def fetch_access_token(config: OAuth2Config) -> str:
    """
    Fetch an access token using refresh_token grant (stdlib urllib only).

    Raises
    ------
    urllib.error.URLError
        On network or HTTP errors.
    ValueError
        If the token response is invalid.
    """
    if not config.refresh_token:
        raise ValueError("refresh_token is required for fetch_access_token")

    data = urllib.parse.urlencode(
        {
            "client_id": config.client_id,
            "client_secret": config.client_secret,
            "refresh_token": config.refresh_token,
            "grant_type": "refresh_token",
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        config.token_url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    with urllib.request.urlopen(request, timeout=30) as response:  # nosec B310
        body = json.loads(response.read().decode("utf-8"))

    token = body.get("access_token")
    if not token:
        raise ValueError(f"No access_token in response: {body}")
    return str(token)
