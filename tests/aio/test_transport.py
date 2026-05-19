"""Tests for AsyncIMAPTransport."""

from unittest.mock import AsyncMock

import pytest

from sage_imap.aio._response import fetch_lines_to_imaplib_data, search_data_from_lines
from sage_imap.aio.transport import AsyncIMAPTransport
from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet


class TestAsyncIMAPTransport:
    async def test_search_uid_normalizes_data(
        self, mock_aio_connection, mock_aio_response
    ):
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH 10 20"])
        )
        status, data = await transport.search("UNSEEN", use_uid=True)
        assert status == "OK"
        assert b"10" in data[0]

    async def test_fetch_batches(self, mock_aio_connection, mock_aio_response):
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        msg_set = MessageSet.from_uids([1])
        status, data = await transport.fetch(msg_set, "(RFC822 FLAGS UID)")
        assert status == "OK"
        assert isinstance(data, list)

    async def test_store_flags_uid(self, mock_aio_connection):
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        msg_set = MessageSet.from_uids([5])
        status, _ = await transport.store_flags(msg_set, FlagCommand.ADD, Flag.SEEN)
        assert status == "OK"
        mock_aio_connection.protocol.store.assert_awaited()


class TestAsyncIMAPTransportExtended:
    async def test_require_connection_raises(self):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        with pytest.raises(RuntimeError, match="No async IMAP"):
            await transport.noop()

    async def test_namespace_not_supported(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.protocol.capabilities = {"IMAP4REV1"}
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, _ = await transport.namespace()
        assert status == "NO"

    async def test_idle_lifecycle(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        assert await transport.idle_start() == "OK"
        lines = await transport.idle_read_lines(timeout=1.0)
        assert lines
        status, _ = await transport.idle_done()
        assert status == "OK"

    async def test_idle_read_when_inactive(self):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        assert await transport.idle_read_lines() == []

    async def test_idle_start_not_supported(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.protocol.capabilities = set()
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        with pytest.raises(RuntimeError, match="IDLE"):
            await transport.idle_start()

    async def test_move_with_capability(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        msg_set = MessageSet.from_uids([1, 2])
        status, meta = await transport.move(msg_set, "Archive")
        assert status == "OK"
        assert meta.get("method") == "MOVE"

    async def test_copy(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, meta = await transport.copy(MessageSet.from_uids([1]), "Sent")
        assert status == "OK"
        assert "copyuid" in meta

    async def test_uid_fetch_command(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.uid = AsyncMock(
            return_value=mock_aio_response(
                lines=[b"* 1 FETCH (UID 1 FLAGS (\\Seen) RFC822 {4}", b"data"]
            )
        )
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, data = await transport.uid("FETCH", "1", "(RFC822)")
        assert status == "OK"
        assert data

    async def test_search_non_uid_with_charset(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, data = await transport.search("UNSEEN", charset="UTF-8", use_uid=False)
        assert status == "OK"

    async def test_get_capabilities_cached(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        caps1 = await transport.get_capabilities()
        caps2 = await transport.get_capabilities()
        assert caps1 == caps2

    async def test_append(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, _ = await transport.append("INBOX", None, None, b"From: a\r\n\r\n")
        assert status == "OK"

    async def test_move_fallback_without_move_capability(
        self, mock_aio_connection, mock_aio_response
    ):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.protocol.capabilities = {"IMAP4REV1", "UIDPLUS"}
        mock_aio_connection.protocol.store = AsyncMock(return_value=mock_aio_response())
        mock_aio_connection.expunge = AsyncMock(return_value=mock_aio_response())
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        transport._capabilities = frozenset({"IMAP4REV1", "UIDPLUS"})
        msg_set = MessageSet.from_uids([1])
        status, meta = await transport.move(msg_set, "Archive")
        assert status == "OK"
        mock_aio_connection.protocol.copy.assert_awaited()
        mock_aio_connection.protocol.move.assert_not_awaited()
        assert meta.get("method") in ("COPY_DELETE", "COPY")

    async def test_idle_read_timeout(self, mock_aio_connection):
        import asyncio

        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        await transport.idle_start()
        mock_aio_connection.wait_server_push = AsyncMock(
            side_effect=asyncio.TimeoutError()
        )
        assert await transport.idle_read_lines(timeout=0.01) == []
        await transport.idle_done()

    async def test_search_by_message_ids(self, mock_aio_connection, mock_aio_response):
        from sage_imap.aio.transport import AsyncIMAPTransport

        mock_aio_connection.uid_search = AsyncMock(
            return_value=mock_aio_response(lines=[b"* SEARCH 99"])
        )
        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        uids = await transport.search_by_message_ids(["<id@example.com>"])
        assert uids == [99]

    async def test_set_flags(self, mock_aio_connection):
        from sage_imap.aio.transport import AsyncIMAPTransport

        transport = AsyncIMAPTransport()
        transport.bind(mock_aio_connection)
        status, _ = await transport.set_flags(MessageSet.from_uids([1]), [Flag.SEEN])
        assert status == "OK"


class TestResponseHelpers:
    def test_search_data_from_lines(self):
        assert search_data_from_lines([b"* SEARCH 1 2"]) == [b"1 2"]

    def test_fetch_lines_to_imaplib_data(self):
        lines = [b"* 1 FETCH (UID 1 FLAGS (\\Seen) RFC822 {4}", b"body"]
        data = fetch_lines_to_imaplib_data(lines)
        assert len(data) == 1
        assert data[0][1] == b"body"
