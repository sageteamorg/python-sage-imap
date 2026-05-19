"""Shared fixtures for async IMAP tests."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_aio_response():
    def _make(result="OK", lines=None):
        resp = MagicMock()
        resp.result = result
        resp.lines = lines or []
        return resp

    return _make


@pytest.fixture
def mock_aio_connection(mock_aio_response):
    conn = MagicMock()
    conn.protocol = MagicMock()
    conn.protocol.capabilities = {"IMAP4REV1", "IDLE", "UIDPLUS", "MOVE", "CONDSTORE"}
    conn.noop = AsyncMock(return_value=mock_aio_response())
    conn.login = AsyncMock(return_value=mock_aio_response())
    conn.logout = AsyncMock(return_value=mock_aio_response())
    conn.select = AsyncMock(return_value=mock_aio_response(lines=[b"1 EXISTS"]))
    conn.close = AsyncMock(return_value=mock_aio_response())
    conn.check = AsyncMock(return_value=mock_aio_response())
    conn.uid_search = AsyncMock(
        return_value=mock_aio_response(lines=[b"* SEARCH 1 2 3"])
    )
    conn.wait_hello_from_server = AsyncMock(return_value=None)
    conn.protocol.fetch = AsyncMock(
        return_value=mock_aio_response(
            lines=[
                b"* 1 FETCH (UID 1 FLAGS (\\Seen) RFC822 {4}",
                b"data",
            ]
        )
    )
    conn.protocol.store = AsyncMock(return_value=mock_aio_response())
    conn.protocol.move = AsyncMock(return_value=mock_aio_response())
    conn.protocol.copy = AsyncMock(return_value=mock_aio_response())
    conn.protocol.capabilities = {
        "IMAP4REV1",
        "IDLE",
        "UIDPLUS",
        "MOVE",
        "CONDSTORE",
        "NAMESPACE",
    }
    conn.status = AsyncMock(return_value=mock_aio_response())
    conn.expunge = AsyncMock(return_value=mock_aio_response())
    conn.create = AsyncMock(return_value=mock_aio_response())
    conn.delete = AsyncMock(return_value=mock_aio_response())
    conn.rename = AsyncMock(return_value=mock_aio_response())
    conn.namespace = AsyncMock(
        return_value=mock_aio_response(lines=[b'(("" "/")) NIL'])
    )
    conn.append = AsyncMock(return_value=mock_aio_response())
    conn.list = AsyncMock(
        return_value=mock_aio_response(
            lines=[b'(\\HasNoChildren) "/" "INBOX"', b'(\\Sent) "/" "Sent"']
        )
    )
    conn.idle_start = AsyncMock(return_value=mock_aio_response())
    conn.idle_done = MagicMock()
    conn.wait_server_push = AsyncMock(
        return_value=mock_aio_response(lines=[b"* 1 EXISTS"])
    )
    conn.xoauth2 = AsyncMock(return_value=mock_aio_response())
    conn.search = AsyncMock(return_value=mock_aio_response(lines=[b"* SEARCH 1"]))
    return conn
