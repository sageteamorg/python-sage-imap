"""Tests for AsyncIMAPSyncService."""

from unittest.mock import AsyncMock, MagicMock

from sage_imap.aio.sync.service import AsyncIMAPSyncService
from sage_imap.sync.state import MailboxSyncState


class TestAsyncIMAPSyncService:
    async def test_capture_state(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.status = AsyncMock(
            return_value=mock_aio_response(
                lines=[b"INBOX (MESSAGES 3 UIDVALIDITY 7 UIDNEXT 10 HIGHESTMODSEQ 55)"]
            )
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        svc = AsyncIMAPSyncService(mailbox)
        state = await svc.capture_state("INBOX")
        assert state.uidvalidity == 7
        assert state.highest_modseq == 55

    async def test_capture_state_status_failure(
        self, mock_aio_connection, mock_aio_response
    ):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.status = AsyncMock(return_value=mock_aio_response("NO", []))
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        svc = AsyncIMAPSyncService(mailbox)
        state = await svc.capture_state("INBOX")
        assert state.uidvalidity is None

    async def test_find_changed_uids_no_modseq(self):
        svc = AsyncIMAPSyncService(MagicMock())
        empty = await svc.find_changed_uids(
            MailboxSyncState(mailbox="INBOX", highest_modseq=None)
        )
        assert empty.is_empty()

    async def test_find_changed_uids(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.mailbox.operations import AsyncIMAPMailboxUIDService
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH 100 101"])
        )
        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = AsyncIMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        state = MailboxSyncState(mailbox="INBOX", highest_modseq=50)
        changed = await mailbox.sync.find_changed_uids(state)
        assert 100 in changed and 101 in changed

    async def test_supports_condstore(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        client = MagicMock()
        client.transport = AsyncIMAPTransport()
        client.transport.bind(mock_aio_connection)
        mailbox = MagicMock()
        mailbox.client = client
        svc = AsyncIMAPSyncService(mailbox)
        assert await svc.supports_condstore() is True
