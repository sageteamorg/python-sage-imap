from imaplib import IMAP4, IMAP4_SSL
from socket import gaierror
from unittest import mock

import pytest

from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPConnectionError,
    IMAPUnexpectedError,
)
from sage_imap.services.client import IMAPClient


@pytest.fixture
def imap_client():
    return IMAPClient("imap.example.com", "username", "password")


def test_imap_client_enter_success(imap_client):
    with mock.patch("imaplib.IMAP4_SSL") as mock_imap, mock.patch(
        "socket.gethostbyname", return_value="127.0.0.1"
    ):
        mock_connection = mock.Mock(spec=IMAP4_SSL)
        mock_imap.return_value = mock_connection

        with imap_client as client:
            assert client == mock_connection
            mock_connection.login.assert_called_once_with("username", "password")


def test_imap_client_enter_hostname_resolution_failure(imap_client):
    with mock.patch("socket.gethostbyname", side_effect=gaierror):
        with pytest.raises(IMAPConnectionError):
            with imap_client:
                pass


def test_imap_client_enter_connection_failure(imap_client):
    with mock.patch("socket.gethostbyname", return_value="127.0.0.1"), mock.patch(
        "imaplib.IMAP4_SSL", side_effect=IMAP4.error
    ):
        with pytest.raises(IMAPConnectionError):
            with imap_client:
                pass


def test_imap_client_enter_authentication_failure(imap_client):
    with mock.patch("socket.gethostbyname", return_value="127.0.0.1"), mock.patch(
        "imaplib.IMAP4_SSL"
    ) as mock_imap:
        mock_connection = mock.Mock(spec=IMAP4_SSL)
        mock_imap.return_value = mock_connection
        mock_connection.login.side_effect = IMAP4.error

        with pytest.raises(IMAPAuthenticationError):
            with imap_client:
                pass


def test_imap_client_exit_success(imap_client):
    with mock.patch("imaplib.IMAP4_SSL") as mock_imap, mock.patch(
        "socket.gethostbyname", return_value="127.0.0.1"
    ):
        mock_connection = mock.Mock(spec=IMAP4_SSL)
        mock_imap.return_value = mock_connection

        with imap_client:
            pass

        mock_connection.logout.assert_called_once()


def test_imap_client_exit_no_connection(imap_client):
    with mock.patch("imaplib.IMAP4_SSL") as mock_imap, mock.patch(
        "socket.gethostbyname", return_value="127.0.0.1"
    ):
        # Simulate no operation login method
        mock_connection = mock.Mock(spec=IMAP4_SSL)
        mock_connection.login = mock.Mock()
        mock_imap.return_value = mock_connection

        with imap_client:
            imap_client.connection = None  # Simulate loss of connection

        mock_connection.logout.assert_not_called()


def test_imap_client_exit_failure(imap_client):
    with mock.patch("imaplib.IMAP4_SSL") as mock_imap, mock.patch(
        "socket.gethostbyname", return_value="127.0.0.1"
    ):
        mock_connection = mock.Mock(spec=IMAP4_SSL)
        mock_imap.return_value = mock_connection
        mock_connection.logout.side_effect = IMAP4.error

        with pytest.raises(IMAPUnexpectedError):
            with imap_client:
                pass
