"""Tests for ORM package surface: __init__, exceptions, dialects, idle."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.exceptions import IMAPClientError
from sage_imap.orm.dialects.base import DEFAULT_DIALECT, resolve_dialect
from sage_imap.orm.exceptions import (
    OrmConfigurationError,
    OrmError,
    OrmMailboxNotSelectedError,
    OrmNotConnectedError,
    error_schema_from_imap,
)
from sage_imap.orm.idle import AsyncIdleSubscription, IdleSubscription
from sage_imap.orm.schemas.error import OperationResultSchema


class TestOrmExceptions:
    def test_orm_error_to_schema(self):
        err = OrmError("oops", code="custom", details={"k": 1})
        schema = err.to_schema()
        assert schema.code == "custom"
        assert schema.details == {"k": 1}

    def test_subclass_codes(self):
        assert OrmConfigurationError().code == "orm_configuration_error"
        assert OrmNotConnectedError().code == "orm_not_connected"
        assert OrmMailboxNotSelectedError().code == "orm_mailbox_not_selected"

    def test_error_schema_from_imap(self):
        exc = IMAPClientError(detail="fail", code="imap_err", status_code=503)
        schema = error_schema_from_imap(exc)
        assert schema.message == "fail"
        assert schema.status_code == 503


class TestDialects:
    def test_resolve_default_and_known(self):
        assert resolve_dialect(None) is DEFAULT_DIALECT
        assert resolve_dialect("dovecot").name == "dovecot"
        assert resolve_dialect("UNKNOWN").name == "default"


class TestOrmLazyInit:
    def test_getattr_exports(self):
        import sage_imap.orm as orm_pkg

        assert orm_pkg.ImapORM.__name__ == "ImapORM"
        assert orm_pkg.AsyncImapORM.__name__ == "AsyncImapORM"
        assert orm_pkg.ImapMessage.__name__ == "ImapMessage"
        assert orm_pkg.ImapFolder.__name__ == "ImapFolder"
        assert orm_pkg.SyncCheckpoint.__name__ == "SyncCheckpoint"
        assert orm_pkg.IdleSubscription.__name__ == "IdleSubscription"
        assert orm_pkg.Q.__name__ == "Q"
        assert orm_pkg.LoadLevel.HEADERS == "headers"
        assert orm_pkg.ConnectionPolicy.PER_REQUEST == "per_request"
        assert orm_pkg.ImapAccountConfig.__name__ == "ImapAccountConfig"
        assert orm_pkg.ErrorSchema.__name__ == "ErrorSchema"
        assert orm_pkg.OperationResultSchema.__name__ == "OperationResultSchema"
        assert orm_pkg.ImapMessageSummarySchema.__name__ == "ImapMessageSummarySchema"
        assert orm_pkg.ImapMessageDetailSchema.__name__ == "ImapMessageDetailSchema"

    def test_missing_attr_raises(self):
        import sage_imap.orm as orm_pkg

        with pytest.raises(AttributeError):
            _ = orm_pkg.not_a_real_export  # type: ignore[attr-defined]

    def test_missing_pydantic_extra_message(self, monkeypatch):
        import sage_imap.orm as mod

        real_import = __builtins__["__import__"]

        def _import(name, *args, **kwargs):
            if name == "pydantic":
                raise ImportError("no pydantic")
            return real_import(name, *args, **kwargs)

        monkeypatch.setattr("builtins.__import__", _import)
        with pytest.raises(ImportError, match=r"\[orm\]"):
            mod.__getattr__("ImapORM")


class TestIdleSubscription:
    def test_sync_idle_context(self, account_config, mocker):
        mock_orm = MagicMock()
        mock_session = MagicMock()
        mock_orm.session = mock_session
        mock_orm.__enter__ = MagicMock(return_value=mock_orm)
        mock_orm.__exit__ = MagicMock(return_value=False)

        idle_ctx = MagicMock()
        idle_ctx.__enter__ = MagicMock(return_value=MagicMock())
        idle_ctx.__exit__ = MagicMock(return_value=False)

        from contextlib import contextmanager

        @contextmanager
        def _open(*_a, **_k):
            yield mock_orm

        mocker.patch("sage_imap.orm.session.ImapORM.open", _open)
        mocker.patch(
            "sage_imap.services.idle.IMAPIdleSession",
            return_value=idle_ctx,
        )
        with IdleSubscription.for_mailbox(
            "acct", "INBOX", config=account_config
        ) as sub:
            assert sub.mailbox == "INBOX"

    def test_sync_idle_no_session_raises(self, account_config, mocker):
        from contextlib import contextmanager

        mock_orm = MagicMock()
        mock_orm.session = None

        @contextmanager
        def _open(*_a, **_k):
            yield mock_orm

        mocker.patch("sage_imap.orm.session.ImapORM.open", _open)
        with pytest.raises(RuntimeError, match="not connected"):
            with IdleSubscription.for_mailbox("acct", "INBOX", config=account_config):
                pass  # pragma: no cover

    def test_sync_idle_without_config_raises(self):
        with pytest.raises(ValueError, match="config or provider"):
            with IdleSubscription.for_mailbox("acct", "INBOX"):
                pass  # pragma: no cover

    def test_wait_with_bound_idle(self):
        idle = MagicMock()
        idle.wait.return_value = ["EXISTS"]
        sub = IdleSubscription(MagicMock(), "INBOX")
        sub._idle = idle
        assert sub.wait(timeout=5.0) == ["EXISTS"]
        idle.wait.assert_called_once_with(timeout=5.0)

    def test_wait_without_context_uses_ephemeral_idle(self, mocker):
        session = MagicMock()
        idle = MagicMock()
        idle.wait.return_value = ["EXISTS"]
        mocker.patch(
            "sage_imap.services.idle.IMAPIdleSession",
            return_value=idle,
        )
        sub = IdleSubscription(session, "INBOX")
        assert sub.wait(timeout=1.0) == ["EXISTS"]
        idle.start.assert_called_once()
        idle.done.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_idle_context(self, account_config, mocker):
        mock_orm = MagicMock()
        mock_session = MagicMock()
        mock_orm.session = mock_session

        async def _aenter(*_a, **_k):
            return mock_orm

        async def _aexit(*_a, **_k):
            return None

        mock_orm.__aenter__ = _aenter
        mock_orm.__aexit__ = _aexit
        mock_orm.select_mailbox = mocker.AsyncMock()

        idle_ctx = MagicMock()
        idle_ctx.__aenter__ = mocker.AsyncMock(return_value=MagicMock())
        idle_ctx.__aexit__ = mocker.AsyncMock(return_value=None)

        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def _open(*_a, **_k):
            yield mock_orm

        mocker.patch("sage_imap.orm.async_session.AsyncImapORM.open", _open)
        mocker.patch(
            "sage_imap.aio.idle.AsyncIMAPIdleSession",
            return_value=idle_ctx,
        )
        async with AsyncIdleSubscription.for_mailbox(
            "acct", "INBOX", config=account_config
        ) as sub:
            assert sub.mailbox == "INBOX"

    @pytest.mark.asyncio
    async def test_async_idle_no_session(self, account_config, mocker):
        from contextlib import asynccontextmanager

        mock_orm = MagicMock()
        mock_orm.session = None
        mock_orm.select_mailbox = AsyncMock()

        @asynccontextmanager
        async def _open(*_a, **_k):
            yield mock_orm

        mocker.patch("sage_imap.orm.async_session.AsyncImapORM.open", _open)
        with pytest.raises(RuntimeError, match="not connected"):
            async with AsyncIdleSubscription.for_mailbox(
                "acct", "INBOX", config=account_config
            ):
                pass  # pragma: no cover
        mock_orm.select_mailbox.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_async_wait_with_bound_idle(self):
        idle = MagicMock()
        idle.wait = AsyncMock(return_value=["EXISTS"])
        sub = AsyncIdleSubscription(MagicMock(), "INBOX")
        sub._idle = idle
        assert await sub.wait(timeout=3.0) == ["EXISTS"]

    @pytest.mark.asyncio
    async def test_async_wait_without_idle_raises(self):
        sub = AsyncIdleSubscription(MagicMock(), "INBOX")
        with pytest.raises(RuntimeError, match="outside context"):
            await sub.wait()


class TestBackendProtocol:
    def test_protocol_import(self):
        from sage_imap.orm.backends.protocol import ImapBackend

        assert ImapBackend.__name__ == "ImapBackend"


class TestManagersModule:
    def test_objects_descriptor(self):
        from sage_imap.orm.managers import objects as mgr_objects

        assert mgr_objects.filter(unread=True)._backend is None


class TestOperationResultSchema:
    def test_defaults(self):
        schema = OperationResultSchema(success=True, operation="test")
        assert schema.affected_uids == []
