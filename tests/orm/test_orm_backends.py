"""Tests for sync and async ORM backends."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.models.message import MessageSet
from sage_imap.orm.backends.sync import _parse_mode_for
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.models.message import ImapMessage


class TestParseModeFor:
    def test_levels(self):
        assert _parse_mode_for(LoadLevel.FULL) == ParseMode.FULL
        assert _parse_mode_for(LoadLevel.IDENTITY) == ParseMode.MINIMAL
        assert _parse_mode_for(LoadLevel.HEADERS) == ParseMode.HEADERS


class TestSyncImapBackend:
    def test_select_and_search(self, sync_backend, mock_imap_session):
        mock_imap_session.select.reset_mock()
        result = sync_backend.select_mailbox("INBOX")
        assert result.success
        assert sync_backend.mailbox == "INBOX"
        mock_imap_session.select.assert_called_once_with("INBOX")

        search = sync_backend.uid_search("ALL")
        mock_imap_session.search.assert_called_with("ALL", charset=None)
        assert search.success

    def test_fetch_identity_and_full(
        self, sync_backend, sample_email, mock_imap_session
    ):
        msg_set = MessageSet.from_uids([10], mailbox="INBOX")
        identity = list(
            sync_backend.fetch_messages(msg_set, load_level=LoadLevel.IDENTITY)
        )
        assert len(identity) == 1
        assert identity[0].uid == 10

        sample_email.uid = 10
        mock_imap_session.iter_messages.return_value = iter([sample_email])
        full = list(sync_backend.fetch_messages(msg_set, load_level=LoadLevel.FULL))
        assert full[0].subject == "Test Subject"
        mock_imap_session.iter_messages.assert_called_once()
        assert (
            mock_imap_session.iter_messages.call_args.kwargs["parse_mode"]
            == ParseMode.FULL
        )

    def test_mark_seen_unseen(self, sync_backend, mock_imap_session):
        msg = ImapMessage.from_uid("acct-test", "INBOX", 10, backend=sync_backend)
        sync_backend.mark_seen(msg)
        sync_backend.mark_unseen(msg)
        assert mock_imap_session.flags.add_flag.called
        assert mock_imap_session.flags.remove_flag.called

    def test_move_and_delete(self, sync_backend, mock_imap_session):
        sync_backend.move_messages([10], "Archive")
        mock_imap_session.mailbox.uid_move.assert_called_once()

        sync_backend.delete_messages([10])
        mock_imap_session.mailbox.uid_trash.assert_called_once()

    def test_delete_without_trash_raises(self, sync_backend, mock_imap_session):
        mock_imap_session.special_folder.return_value = None
        with pytest.raises(ValueError, match="Trash folder not found"):
            sync_backend.delete_messages([10])

    def test_sync_state_helpers(self, sync_backend, mock_imap_session, sync_state):
        state = sync_backend.capture_sync_state("INBOX")
        assert state.mailbox == "INBOX"
        changed = sync_backend.find_changed_uids(sync_state)
        assert changed.parsed_ids == [20]
        sync_backend.apply_after_sync(sync_state)
        mock_imap_session.sync.apply_after_sync.assert_called_once()


@pytest.mark.asyncio
class TestAsyncImapBackend:
    async def test_select_search_fetch(
        self, async_backend, mock_async_session, sample_email
    ):
        result = await async_backend.select_mailbox("INBOX")
        assert result.success
        assert async_backend.mailbox == "INBOX"

        await async_backend.uid_search("ALL")
        mock_async_session.search.assert_awaited()

        msg_set = MessageSet.from_uids([5], mailbox="INBOX")
        sample_email.uid = 5

        async def _messages(*_args, **_kwargs):
            yield sample_email

        mock_async_session.iter_messages = _messages
        msgs = [
            m
            async for m in async_backend.fetch_messages(
                msg_set, load_level=LoadLevel.HEADERS
            )
        ]
        assert len(msgs) == 1

    async def test_mark_move_delete(self, async_backend, mock_async_session):
        msg = ImapMessage.from_uid("acct-test", "INBOX", 5, backend=async_backend)
        await async_backend.mark_seen(msg)
        await async_backend.mark_unseen(msg)
        await async_backend.move_messages([5], "Trash")
        await async_backend.delete_messages([5])
        mock_async_session.flags.add_flag.assert_awaited()
        mock_async_session.mailbox.uid_trash.assert_awaited()

    async def test_delete_no_trash(self, async_backend, mock_async_session):
        mock_async_session.special_folder = AsyncMock(return_value=None)
        with pytest.raises(ValueError, match="Trash folder not found"):
            await async_backend.delete_messages([5])

    async def test_sync_helpers(self, async_backend, mock_async_session, sync_state):
        state = await async_backend.capture_sync_state("INBOX")
        assert state.uidvalidity == 2
        changed = await async_backend.find_changed_uids(sync_state)
        assert changed.parsed_ids == [5]
        applied = await async_backend.apply_after_sync(sync_state)
        assert applied.mailbox == "INBOX"

    async def test_fetch_identity(self, async_backend):
        msg_set = MessageSet.from_uids([7], mailbox="INBOX")
        msgs = [
            m
            async for m in async_backend.fetch_messages(
                msg_set, load_level=LoadLevel.IDENTITY
            )
        ]
        assert msgs[0].uid == 7
