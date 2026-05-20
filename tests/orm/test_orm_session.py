"""Tests for ImapORM and AsyncImapORM sessions."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sage_imap.orm.async_session import AsyncImapORM
from sage_imap.orm.config import ConnectionPolicy
from sage_imap.orm.exceptions import OrmConfigurationError
from sage_imap.orm.managers import _active_orm
from sage_imap.orm.models.message import ImapMessage
from sage_imap.orm.session import ImapORM
from sage_imap.services.mailbox.models import MailboxOperationResult


class TestImapORM:
    def test_open_with_existing_session(self, mock_imap_session):
        with ImapORM.open("acct", session=mock_imap_session) as orm:
            assert orm.account_id == "acct"
            assert orm.session is mock_imap_session
            orm.select_mailbox("INBOX")
            assert orm.mailbox == "INBOX"

    def test_open_requires_config(self):
        with pytest.raises(OrmConfigurationError):
            with ImapORM.open("acct"):
                pass  # pragma: no cover

    def test_open_with_provider(self, account_config):
        provider = MagicMock()
        provider.get_config.return_value = account_config

        with patch.object(ImapORM, "_session_from_config") as create:
            create.return_value = MagicMock()
            create.return_value.connect = MagicMock()
            create.return_value.close = MagicMock()
            with ImapORM.open("acct-test", provider=provider) as orm:
                assert orm.account_id == "acct-test"
        provider.get_config.assert_called_once_with("acct-test")

    def test_long_lived_uses_registry(self, account_config):
        account_config.connection_policy = ConnectionPolicy.LONG_LIVED
        registry = MagicMock()
        session = MagicMock()
        session.client.is_connected.return_value = True
        registry.get_or_create.return_value = session

        with ImapORM.open("acct-test", config=account_config, registry=registry) as orm:
            assert orm._owns_session is False
            assert orm.session is session
        registry.get_or_create.assert_called_once()

    def test_manager_binding(self, sync_backend):
        orm = ImapORM("acct", sync_backend, _session=MagicMock(), _owns_session=False)
        orm.mailbox = "INBOX"
        with orm:
            qs = ImapMessage.objects.filter(unread=True)
            assert qs._backend is sync_backend
            assert qs._mailbox == "INBOX"
        assert _active_orm.get() is None

    def test_per_request_creates_owned_session(self, account_config):
        with patch.object(ImapORM, "_session_from_config") as create:
            session = MagicMock()
            create.return_value = session
            with ImapORM.open("acct-test", config=account_config) as orm:
                assert orm._owns_session is True
            session.close.assert_called_once()

    def test_session_from_config_pool(self, account_config):
        account_config.use_pool = True
        with patch("sage_imap.orm.session.IMAPSession") as SessionCls:
            inst = MagicMock()
            SessionCls.from_config.return_value = inst
            result = ImapORM._session_from_config(account_config)
            assert result.client.use_pool is True


@pytest.mark.asyncio
class TestAsyncImapORM:
    async def test_open_and_select(self, mock_async_session, account_config, mocker):
        mocker.patch(
            "sage_imap.aio.session.AsyncIMAPSession.from_config",
            return_value=mock_async_session,
        )
        async with AsyncImapORM.open("acct-test", config=account_config) as orm:
            assert orm.account_id == "acct-test"
            await orm.select_mailbox("INBOX")
            assert orm.mailbox == "INBOX"
        mock_async_session.connect.assert_awaited()
        mock_async_session.close.assert_awaited()

    async def test_open_missing_config(self):
        with pytest.raises(OrmConfigurationError):
            async with AsyncImapORM.open("acct"):
                pass  # pragma: no cover

    async def test_open_from_config(self, account_config, mocker):
        mocker.patch(
            "sage_imap.aio.session.AsyncIMAPSession.from_config",
            return_value=MagicMock(
                connect=AsyncMock(),
                close=AsyncMock(),
                select=AsyncMock(
                    return_value=MailboxOperationResult(
                        success=True, operation="select"
                    )
                ),
            ),
        )
        async with AsyncImapORM.open("acct-test", config=account_config) as orm:
            assert orm.account_id == "acct-test"

    async def test_missing_aioimaplib_raises(self, account_config, mocker):
        mocker.patch("importlib.util.find_spec", return_value=None)
        with pytest.raises(ImportError, match="orm,async"):
            async with AsyncImapORM.open("acct-test", config=account_config):
                pass  # pragma: no cover
