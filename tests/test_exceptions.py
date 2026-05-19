"""Tests for sage_imap.exceptions."""

from sage_imap.exceptions import IMAPClientError, IMAPConnectionError


def test_imap_client_error_defaults():
    err = IMAPClientError()
    assert err.detail == IMAPClientError.default_detail
    assert err.code == IMAPClientError.default_code
    assert "Code:" in str(err)


def test_imap_client_error_custom():
    err = IMAPClientError(detail="custom", code="x", status_code=418)
    assert err.status_code == 418
    assert "custom" in str(err)


def test_subclass_defaults():
    err = IMAPConnectionError()
    assert err.status_code == 502
    assert err.default_code == "connection_error"
