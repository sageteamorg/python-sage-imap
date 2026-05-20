"""Tests for ORM models: ImapMessage, ImapFolder, SyncCheckpoint, managers."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from sage_imap.models.email import EmailMessage
from sage_imap.models.folder import FolderInfo
from sage_imap.orm.managers import MessageManager, objects
from sage_imap.orm.models.checkpoint import SyncCheckpoint
from sage_imap.orm.models.folder import ImapFolder
from sage_imap.orm.models.message import ImapAttachment, ImapMessage
from sage_imap.orm.schemas.message import ImapMessageDetailSchema
from sage_imap.orm.session import ImapORM


class TestImapMessage:
    def test_from_fetched(self, sample_email):
        msg = ImapMessage.from_fetched("acct", sample_email)
        assert msg.uid == 42
        assert msg.subject == "Test Subject"
        assert msg.has_attachments is True
        assert len(msg.flags) >= 1

    def test_from_fetched_string_date(self):
        email = EmailMessage(message_id="x", date="2026-05-20T12:00:00+00:00")
        msg = ImapMessage.from_fetched("a", email)
        assert isinstance(msg.date, datetime)

    def test_from_fetched_invalid_date(self):
        email = EmailMessage(message_id="x", date="not-a-date")
        msg = ImapMessage.from_fetched("a", email)
        assert msg.date is None

    def test_sync_mutations(self, sync_backend):
        msg = ImapMessage.from_uid("acct", "INBOX", 10, backend=sync_backend)
        msg.mark_seen()
        msg.mark_unseen()
        msg.move_to("Archive")
        msg.delete()
        sync_backend._session.flags.add_flag.assert_called()
        sync_backend._session.mailbox.uid_trash.assert_called()

    def test_no_backend_raises(self):
        msg = ImapMessage("a", "INBOX", 1)
        with pytest.raises(RuntimeError, match="not bound"):
            msg.mark_seen()

    @pytest.mark.asyncio
    async def test_async_mutations(self, async_backend):
        msg = ImapMessage.from_uid("acct", "INBOX", 5, backend=async_backend)
        await msg.amark_seen()
        await msg.amark_unseen()
        await msg.amove_to("Trash")
        await msg.adelete()

    def test_mark_seen_detects_async_result(self, sync_backend):
        class _Awaitable:
            def __await__(self):
                return iter(())

        sync_backend.mark_seen = MagicMock(return_value=_Awaitable())
        msg = ImapMessage.from_uid("a", "INBOX", 1, backend=sync_backend)
        with pytest.raises(RuntimeError, match="amark_seen"):
            msg.mark_seen()

    def test_detail_schema(self):
        msg = ImapMessage(
            account_id="a",
            mailbox="INBOX",
            uid=1,
            subject="Hi",
            to_addresses=["b@c.com"],
            attachments=[
                ImapAttachment(filename="f.txt", content_type="text/plain", size=3)
            ],
            plain_body="body",
            html_body="<p>x</p>",
        )
        detail = ImapMessageDetailSchema.from_imap_message(msg)
        assert detail.plain_body == "body"
        assert detail.attachments[0].filename == "f.txt"
        no_body = ImapMessageDetailSchema.from_imap_message(msg, include_body=False)
        assert no_body.plain_body == ""


class TestMessageManager:
    def test_without_active_orm(self):
        mgr = MessageManager()
        qs = mgr.filter(unread=True)
        assert qs._backend is None
        assert mgr.all()._backend is None
        assert mgr.get(1)._limit == 1

    def test_changed_since_with_checkpoint(self, sync_backend, sync_state):
        cp = SyncCheckpoint("acct", "INBOX", state=sync_state)
        orm = ImapORM("acct", sync_backend, _owns_session=False)
        with orm:
            qs = ImapMessage.objects.changed_since(cp)
            assert qs._changed_since is sync_state


class TestImapFolder:
    def test_from_folder_info(self):
        info = FolderInfo(name="INBOX", message_count=5, unseen_count=2)
        folder = ImapFolder.from_folder_info("acct", info)
        assert folder.name == "INBOX"
        assert folder.message_count == 5

    def test_manager_list_and_get(self, sync_backend, mock_imap_session):
        orm = ImapORM(
            "acct", sync_backend, _session=mock_imap_session, _owns_session=False
        )
        with orm:
            folders = ImapFolder.objects.list()
            assert len(folders) == 2
            one = ImapFolder.objects.get("INBOX")
            assert one is not None
            assert one.name == "INBOX"
            trash = ImapFolder.objects.trash()
            assert trash is not None

    def test_manager_without_orm(self):
        assert ImapFolder.objects.list() == []
        assert ImapFolder.objects.get("INBOX") is None
        assert ImapFolder.objects.trash() is None

    def test_manager_list_no_session(self):
        from types import SimpleNamespace

        backend = SimpleNamespace(account_id="acct")
        orm = ImapORM("acct", backend, _owns_session=False)  # type: ignore[arg-type]
        with orm:
            assert ImapFolder.objects.list() == []


class TestSyncCheckpoint:
    def test_capture_refresh_apply(self, sync_backend, sync_state):
        cp = SyncCheckpoint.capture("acct", "INBOX", sync_backend)
        assert cp.state.mailbox == "INBOX"
        cp.refresh(sync_backend)
        cp.apply(sync_backend)

    def test_apply_async_backend_raises(self, async_backend, sync_state):
        cp = SyncCheckpoint("acct", "INBOX", state=sync_state)
        with pytest.raises(RuntimeError, match="apply_async"):
            cp.apply(async_backend)

    @pytest.mark.asyncio
    async def test_apply_and_refresh_async(self, async_backend, sync_state):
        cp = SyncCheckpoint("acct", "INBOX", state=sync_state)
        await cp.apply_async(async_backend)
        await cp.refresh_async(async_backend)

    def test_manager_for_mailbox(self, sync_backend):
        orm = ImapORM("acct", sync_backend, _owns_session=False)
        with orm:
            cp = SyncCheckpoint.objects.for_mailbox("acct", "INBOX")
            assert cp.account_id == "acct"

    def test_manager_for_mailbox_async_without_orm(self):
        import asyncio

        cp = asyncio.run(SyncCheckpoint.objects.for_mailbox_async("a", "INBOX"))
        assert cp.mailbox == "INBOX"

    @pytest.mark.asyncio
    async def test_manager_for_mailbox_async(self, async_backend):
        orm = ImapORM("acct", async_backend, _owns_session=False)
        with orm:
            cp = await SyncCheckpoint.objects.for_mailbox_async("acct", "INBOX")
            assert cp.mailbox == "INBOX"

    def test_manager_no_orm(self):
        cp = SyncCheckpoint.objects.for_mailbox("a", "INBOX")
        assert cp.mailbox == "INBOX"


class TestModuleObjects:
    def test_objects_alias(self):
        assert objects.filter(unread=True)._backend is None
