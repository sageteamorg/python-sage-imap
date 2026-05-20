"""Shared ORM test fixtures."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from sage_imap.helpers.enums import Flag
from sage_imap.models.email import EmailMessage
from sage_imap.models.folder import FolderInfo
from sage_imap.models.message import MessageSet
from sage_imap.orm.backends.async_ import AsyncImapBackend
from sage_imap.orm.backends.sync import SyncImapBackend
from sage_imap.orm.config import ConnectionPolicy, ImapAccountConfig
from sage_imap.services.mailbox.models import MailboxOperationResult
from sage_imap.sync.state import MailboxSyncState


@pytest.fixture
def account_config() -> ImapAccountConfig:
    return ImapAccountConfig(
        account_id="acct-test",
        host="imap.example.com",
        username="user@example.com",
        password="secret",
        connection_policy=ConnectionPolicy.PER_REQUEST,
    )


@pytest.fixture
def mock_imap_session(mocker):
    """Mock :class:`~sage_imap.session.IMAPSession` for sync ORM tests."""
    session = mocker.Mock()
    session.client = mocker.Mock()
    session.client.is_connected.return_value = True
    session.client.use_pool = False
    session.connect = mocker.Mock()
    session.close = mocker.Mock()
    session.select.return_value = MailboxOperationResult(
        success=True, operation="select", message_count=3
    )
    session.search.return_value = MailboxOperationResult(
        success=True,
        operation="uid_search",
        affected_messages=["10", "20", "30"],
    )
    session.iter_messages.return_value = iter([])
    session.flags = mocker.Mock()
    session.flags.add_flag = mocker.Mock()
    session.flags.remove_flag = mocker.Mock()
    session.mailbox = mocker.Mock()
    session.mailbox.uid_move.return_value = MailboxOperationResult(
        success=True, operation="uid_move"
    )
    session.mailbox.uid_trash.return_value = MailboxOperationResult(
        success=True, operation="uid_trash"
    )
    session.special_folder.return_value = "Trash"
    session.folders = mocker.Mock()
    session.folders.list_folders.return_value = [
        FolderInfo(name="INBOX", message_count=3, unseen_count=1),
        FolderInfo(name="Trash", attributes=[r"\Trash"]),
    ]
    session.folders.get_folder_info.return_value = FolderInfo(
        name="INBOX", message_count=3, unseen_count=1
    )
    session.capture_sync_state.return_value = MailboxSyncState(
        mailbox="INBOX", uidvalidity=1, highest_modseq=100
    )
    session.find_changed_since.return_value = MessageSet.from_uids(
        [20], mailbox="INBOX"
    )
    session.sync = mocker.Mock()
    session.sync.apply_after_sync.side_effect = lambda s: s
    return session


@pytest.fixture
def sync_backend(mock_imap_session) -> SyncImapBackend:
    backend = SyncImapBackend(mock_imap_session, "acct-test")
    backend.select_mailbox("INBOX")
    return backend


@pytest.fixture
def mock_async_session(mocker):
    """Mock :class:`~sage_imap.aio.session.AsyncIMAPSession`."""
    session = mocker.Mock()
    session.connect = AsyncMock()
    session.close = AsyncMock()
    session.select = AsyncMock(
        return_value=MailboxOperationResult(success=True, operation="select")
    )
    session.search = AsyncMock(
        return_value=MailboxOperationResult(
            success=True,
            operation="uid_search",
            affected_messages=["5"],
        )
    )

    async def _empty_iter(*_args, **_kwargs):
        if False:  # pragma: no cover
            yield None

    session.iter_messages = _empty_iter
    session.flags = mocker.Mock()
    session.flags.add_flag = AsyncMock()
    session.flags.remove_flag = AsyncMock()
    session.mailbox = mocker.Mock()
    session.mailbox.uid_move = AsyncMock(
        return_value=MailboxOperationResult(success=True, operation="uid_move")
    )
    session.mailbox.uid_trash = AsyncMock(
        return_value=MailboxOperationResult(success=True, operation="uid_trash")
    )
    session.special_folder = AsyncMock(return_value="Trash")
    session.capture_sync_state = AsyncMock(
        return_value=MailboxSyncState(mailbox="INBOX", uidvalidity=2)
    )
    session.find_changed_since = AsyncMock(
        return_value=MessageSet.from_uids([5], mailbox="INBOX")
    )
    return session


@pytest.fixture
def async_backend(mock_async_session) -> AsyncImapBackend:
    backend = AsyncImapBackend(mock_async_session, "acct-test")
    return backend


@pytest.fixture
def sample_email() -> EmailMessage:
    msg = EmailMessage(
        message_id="<id@example.com>",
        subject="Test Subject",
        uid=42,
        mailbox="INBOX",
        plain_body="hello",
        html_body="<p>hi</p>",
        flags=[Flag.SEEN],
        size=1024,
    )
    msg.has_attachments = MagicMock(return_value=True)
    return msg


@pytest.fixture
def sync_state() -> MailboxSyncState:
    return MailboxSyncState(
        mailbox="INBOX",
        uidvalidity=1,
        highest_modseq=50,
        last_sync_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
