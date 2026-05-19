"""OAuth2 helper tests."""

import json

import pytest

from sage_imap.auth.oauth2 import OAuth2Config, build_xoauth2_string, fetch_access_token


def test_build_xoauth2_string():
    s = build_xoauth2_string("user@example.com", "token123")
    assert "user=user@example.com" in s
    assert "auth=Bearer token123" in s


def test_oauth2_config_dataclass():
    cfg = OAuth2Config(
        client_id="id",
        client_secret="secret",
        token_url="https://oauth.example/token",
    )
    assert cfg.scopes is None


def test_fetch_access_token_requires_refresh():
    cfg = OAuth2Config("id", "secret", "https://oauth.example/token")
    with pytest.raises(ValueError, match="refresh_token"):
        fetch_access_token(cfg)


def test_fetch_access_token_success(mocker):
    body = json.dumps({"access_token": "tok123"}).encode()
    response = mocker.Mock()
    response.read.return_value = body
    response.__enter__ = mocker.Mock(return_value=response)
    response.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("urllib.request.urlopen", return_value=response)

    cfg = OAuth2Config(
        client_id="id",
        client_secret="secret",
        token_url="https://oauth.example/token",
        refresh_token="refresh",
    )
    assert fetch_access_token(cfg) == "tok123"


def test_fetch_access_token_missing_token(mocker):
    body = json.dumps({"token_type": "bearer"}).encode()
    response = mocker.Mock()
    response.read.return_value = body
    response.__enter__ = mocker.Mock(return_value=response)
    response.__exit__ = mocker.Mock(return_value=False)
    mocker.patch("urllib.request.urlopen", return_value=response)

    cfg = OAuth2Config(
        client_id="id",
        client_secret="secret",
        token_url="https://oauth.example/token",
        refresh_token="refresh",
    )
    with pytest.raises(ValueError, match="access_token"):
        fetch_access_token(cfg)
