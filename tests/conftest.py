"""Shared pytest fixtures."""

import pytest


@pytest.fixture
def mock_imap_connection(mocker):
    """Minimal mock imaplib connection."""
    conn = mocker.Mock()
    conn.noop.return_value = ("OK", [None])
    conn.capability.return_value = (
        "OK",
        [b"IMAP4rev1 IDLE MOVE UIDPLUS AUTH=PLAIN AUTH=XOAUTH2"],
    )
    conn.login.return_value = ("OK", [b"Logged in"])
    conn.logout.return_value = ("BYE", [b"Logout"])
    conn.select.return_value = ("OK", [b"3"])
    conn.search.return_value = ("OK", [b"1 2 3"])
    conn.uid.return_value = ("OK", [b"100 101"])
    conn.fetch.return_value = ("OK", [])
    conn.store.return_value = ("OK", [])
    conn.copy.return_value = ("OK", [b"[COPYUID 1 5 10]"])
    conn.expunge.return_value = ("OK", [])
    conn.sock = mocker.Mock()
    return conn
