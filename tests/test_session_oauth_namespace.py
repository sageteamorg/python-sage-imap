"""Tests for IMAPSession, namespace/SPECIAL-USE, OAuth refresh, and SSL context."""

import json
import ssl
from unittest.mock import Mock

from sage_imap.auth.oauth2 import (
    OAuth2Config,
    ensure_access_token,
    refresh_access_token,
)
from sage_imap.helpers.special_use import (
    NamespaceMap,
    SpecialUse,
    build_special_folder_map,
    folder_matches_special_use,
    parse_namespace_response,
)
from sage_imap.services.client import ConnectionConfig, build_ssl_context
from sage_imap.services.folder import FolderInfo, IMAPFolderService
from sage_imap.session import IMAPSession


class TestSpecialUseAndNamespace:
    def test_parse_namespace(self):
        data = [b'(("" "/")) (("" "/")) NIL']
        ns = parse_namespace_response(data)
        assert ns.personal is not None
        assert ns.personal.delimiter == "/"

    def test_special_use_matching(self):
        attrs = ["\\HasNoChildren", "\\Sent"]
        assert folder_matches_special_use(attrs, SpecialUse.SENT)

    def test_build_special_folder_map(self):
        folders = [
            FolderInfo(name="INBOX", attributes=[]),
            FolderInfo(name="Sent Items", attributes=["\\Sent"]),
        ]
        mapping = build_special_folder_map(folders)
        assert mapping[SpecialUse.SENT].name == "Sent Items"
        assert mapping[SpecialUse.INBOX].name == "INBOX"

    def test_folder_get_namespace_and_special(self, mocker):
        client = Mock()
        client.transport = Mock()
        client.transport.namespace.return_value = ("OK", [b'(("" "/")) NIL'])
        client.transport.list.return_value = (
            "OK",
            [
                b'(\\HasNoChildren \\Sent) "/" "Sent"',
                b'(\\HasNoChildren) "/" "INBOX"',
            ],
        )
        svc = IMAPFolderService(client)
        ns = svc.get_namespace()
        assert isinstance(ns, NamespaceMap)
        special = svc.get_special_folders()
        assert special[SpecialUse.SENT].name == "Sent"
        assert svc.resolve_standard_mailbox(SpecialUse.TRASH) is None


class TestOAuthRefresh:
    def test_refresh_updates_config(self, mocker):
        body = json.dumps(
            {"access_token": "new", "expires_in": 3600, "refresh_token": "rotated"}
        ).encode()
        response = mocker.Mock()
        response.read.return_value = body
        response.__enter__ = mocker.Mock(return_value=response)
        response.__exit__ = mocker.Mock(return_value=False)
        mocker.patch("urllib.request.urlopen", return_value=response)

        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="old",
        )
        result = refresh_access_token(cfg)
        assert result.access_token == "new"
        assert cfg.access_token == "new"
        assert cfg.refresh_token == "rotated"
        assert cfg.expires_at is not None

    def test_ensure_access_token_cached(self, mocker):
        cfg = OAuth2Config(
            client_id="id",
            client_secret="secret",
            token_url="https://oauth.example/token",
            refresh_token="r",
            access_token="cached",
            expires_at=9999999999.0,
        )
        mocker.patch("sage_imap.auth.oauth2.refresh_access_token")
        assert ensure_access_token(cfg) == "cached"


class TestSslContext:
    def test_custom_ssl_context(self):
        ctx = ssl.create_default_context()
        config = ConnectionConfig(
            host="h", username="u", ssl_context=ctx, ssl_verify=True
        )
        assert build_ssl_context(config) is ctx

    def test_ssl_verify_false(self):
        config = ConnectionConfig(host="h", username="u", ssl_verify=False)
        ctx = build_ssl_context(config)
        assert isinstance(ctx, ssl.SSLContext)


class TestIMAPSession:
    def test_session_wires_services(self, mocker):
        session = IMAPSession("h", "u", "p")
        mocker.patch.object(session.client, "connect")
        mocker.patch.object(session.client, "disconnect")
        mocker.patch.object(session.mailbox, "close")
        with session:
            assert session.folders is not None
            assert session.flags is not None
        session.client.connect.assert_called_once()
        session.client.disconnect.assert_called_once()

    def test_connect_with_oauth(self, mocker):
        session = IMAPSession(
            "h",
            "u",
            oauth_config=OAuth2Config(
                client_id="id",
                client_secret="s",
                token_url="https://t",
                refresh_token="r",
            ),
        )
        mocker.patch.object(
            session.client, "connect_with_oauth", return_value=mocker.Mock()
        )
        mocker.patch.object(session.client, "disconnect")
        mocker.patch.object(session.mailbox, "close")
        session.connect()
        session.client.connect_with_oauth.assert_called_once()
