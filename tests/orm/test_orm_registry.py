"""Tests for ImapConnectionRegistry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sage_imap.orm.config import ConnectionPolicy, ImapAccountConfig
from sage_imap.orm.connections.registry import (
    ImapConnectionRegistry,
    _RegistryHolder,
    get_connection_registry,
)
from sage_imap.orm.exceptions import OrmConfigurationError


@pytest.fixture(autouse=True)
def _reset_registry():
    _RegistryHolder.registry = None
    yield
    _RegistryHolder.registry = None


class TestImapConnectionRegistry:
    def test_per_request_creates_new_session(self, account_config):
        account_config.connection_policy = ConnectionPolicy.PER_REQUEST
        registry = ImapConnectionRegistry()
        with patch.object(registry, "_create_session") as create:
            s1 = MagicMock()
            s2 = MagicMock()
            create.side_effect = [s1, s2]
            assert registry.get_or_create(account_config) is s1
            assert registry.get_or_create(account_config) is s2

    def test_long_lived_reuses_connected_session(self, account_config):
        account_config.connection_policy = ConnectionPolicy.LONG_LIVED
        registry = ImapConnectionRegistry()
        session = MagicMock()
        session.client.is_connected.return_value = True
        with patch.object(registry, "_create_session", return_value=session):
            first = registry.get_or_create(account_config)
            second = registry.get_or_create(account_config)
            assert first is second
            session.connect.assert_called_once()

    def test_recreates_when_disconnected(self, account_config):
        account_config.connection_policy = ConnectionPolicy.LONG_LIVED
        registry = ImapConnectionRegistry()
        old = MagicMock()
        old.client.is_connected.return_value = False
        new = MagicMock()
        new.client.is_connected.return_value = True
        registry._sessions[account_config.account_id] = old
        with patch.object(registry, "_create_session", return_value=new):
            result = registry.get_or_create(account_config)
            assert result is new

    def test_release_and_clear(self, account_config):
        registry = ImapConnectionRegistry()
        session = MagicMock()
        registry._sessions["acct-test"] = session
        registry.release("acct-test", disconnect=True)
        session.close.assert_called_once()
        registry._sessions["acct-test"] = session
        session.close.side_effect = RuntimeError("boom")
        registry.clear()  # suppresses close errors

    def test_create_requires_host_username(self):
        cfg = ImapAccountConfig(account_id="x", host="", username="")
        with pytest.raises(OrmConfigurationError):
            ImapConnectionRegistry._create_session(cfg)

    def test_pooled_sets_use_pool(self, account_config):
        account_config.connection_policy = ConnectionPolicy.POOLED
        with patch("sage_imap.orm.connections.registry.IMAPSession") as SessionCls:
            inst = MagicMock()
            SessionCls.from_config.return_value = inst
            ImapConnectionRegistry._create_session(account_config)
            assert inst.client.use_pool is True

    def test_get_connection_registry_singleton(self):
        r1 = get_connection_registry()
        r2 = get_connection_registry()
        assert r1 is r2
