"""Unit tests for IMAPClient."""

import imaplib
import socket

import pytest

from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError
from sage_imap.services.client import (
    ConnectionConfig,
    ConnectionPool,
    IMAPClient,
    clear_connection_pool,
    get_pool_stats,
)


class TestConnectionPool:
    def test_pool_get_return_and_clear(self, mocker):
        pool = ConnectionPool(max_connections=2)
        config = ConnectionConfig(host="h", username="u", password="p")
        conn = mocker.Mock()
        assert pool.get_connection(config) is None
        pool.return_connection(config, conn)
        assert pool.get_connection(config) is conn
        pool.return_connection(config, conn)
        pool.clear_pool()

    def test_pool_logout_on_overflow(self, mocker):
        pool = ConnectionPool(max_connections=1)
        config = ConnectionConfig(host="h", username="u", password="p")
        c1, c2 = mocker.Mock(), mocker.Mock()
        pool.return_connection(config, c1)
        pool.return_connection(config, c2)
        c2.logout.assert_called()


class TestIMAPClient:
    def test_context_manager_returns_client(self, mocker):
        mocker.patch.object(IMAPClient, "_connect_impl", return_value=mocker.Mock())
        with IMAPClient("host", "user", "pass") as client:
            assert isinstance(client, IMAPClient)

    def test_is_connected_does_not_clear_connection_on_failure(self, mocker):
        client = IMAPClient("host", "user", "pass")
        client.connection = mocker.Mock()
        client.transport.bind(client.connection)
        client.transport.noop = mocker.Mock(side_effect=imaplib.IMAP4.error("bye"))
        assert client.is_connected() is False
        assert client.connection is not None
        assert client._stale is True

    def test_connect_uses_config_retries(self, mocker):
        calls = []

        def flaky_connect(self):
            calls.append(1)
            if len(calls) < 2:
                raise IMAPConnectionError("fail")
            self.connection = mocker.Mock()
            self.transport.bind(self.connection)
            self.authenticated = True
            return self.connection

        mocker.patch.object(IMAPClient, "_connect_impl", flaky_connect)
        client = IMAPClient("host", "user", "pass", max_retries=2, retry_delay=0)
        client.connect()
        assert len(calls) == 2

    def test_from_config_preserves_config(self):
        config = ConnectionConfig(
            host="imap.test", username="u", password="p", enable_background_health=True
        )
        client = IMAPClient.from_config(config)
        assert client.config.enable_background_health is True

    def test_connect_ssl_and_login(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.sock = mocker.Mock()
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4_SSL", return_value=mock_conn)
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        client.connect()
        assert client.authenticated
        mock_conn.login.assert_called_with("user", "pass")

    def test_connect_oauth2(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.sock = mocker.Mock()
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4_SSL", return_value=mock_conn)
        client = IMAPClient("host", "user", enable_monitoring=False)
        client.connect_oauth2("user", "token")
        mock_conn.authenticate.assert_called()

    def test_connect_non_ssl_starttls(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.sock = mocker.Mock()
        mock_conn.starttls = mocker.Mock()
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4", return_value=mock_conn)
        client = IMAPClient(
            "host", "user", "pass", use_ssl=False, enable_monitoring=False
        )
        client.connect()
        mock_conn.starttls.assert_called()

    def test_connect_gaierror(self, mocker):
        mocker.patch("socket.gethostbyname", side_effect=socket.gaierror)
        client = IMAPClient(
            "host", "user", "pass", max_retries=0, enable_monitoring=False
        )
        with pytest.raises(IMAPConnectionError):
            client.connect()

    def test_connect_imap_error(self, mocker):
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4_SSL", side_effect=OSError("fail"))
        client = IMAPClient(
            "host", "user", "pass", max_retries=0, enable_monitoring=False
        )
        with pytest.raises(IMAPConnectionError):
            client.connect()

    def test_connect_login_failure(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.sock = mocker.Mock()
        mock_conn.login.side_effect = imaplib.IMAP4.error("auth")
        mock_conn.logout = mocker.Mock()
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4_SSL", return_value=mock_conn)
        client = IMAPClient(
            "host", "user", "pass", max_retries=0, enable_monitoring=False
        )
        with pytest.raises(IMAPAuthenticationError):
            client.connect()

    def test_connect_uses_pooled_connection(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.noop.return_value = ("OK", [])
        mocker.patch(
            "sage_imap.services.client._connection_pool.get_connection",
            return_value=mock_conn,
        )
        client = IMAPClient(
            "host", "user", "pass", use_pool=True, enable_monitoring=False
        )
        client.connect()
        assert client.connection is mock_conn

    def test_connect_stale_pooled(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.noop.side_effect = Exception("stale")
        mocker.patch(
            "sage_imap.services.client._connection_pool.get_connection",
            return_value=mock_conn,
        )
        new_conn = mocker.Mock()
        new_conn.sock = mocker.Mock()
        mocker.patch("socket.gethostbyname", return_value="127.0.0.1")
        mocker.patch("imaplib.IMAP4_SSL", return_value=new_conn)
        client = IMAPClient(
            "host", "user", "pass", use_pool=True, enable_monitoring=False
        )
        client.connect()
        assert client.connection is new_conn

    def test_reuse_existing_connection(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        client.connection = mocker.Mock()
        client.transport.bind(client.connection)
        client._stale = False
        mocker.patch.object(client, "is_connected", return_value=True)
        client.connect()
        assert client.connection is not None

    def test_disconnect_with_pool(self, mocker):
        mock_conn = mocker.Mock()
        mocker.patch("sage_imap.services.client._connection_pool.return_connection")
        client = IMAPClient(
            "host", "user", "pass", use_pool=True, enable_monitoring=False
        )
        client.connection = mock_conn
        client.transport.bind(mock_conn)
        client.disconnect()
        assert client.connection is None

    def test_disconnect_logout_error(self, mocker):
        mock_conn = mocker.Mock()
        mock_conn.logout.side_effect = Exception("bye")
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        client.connection = mock_conn
        client.transport.bind(mock_conn)
        client.disconnect()
        assert client.connection is None

    def test_health_check_and_metrics(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=True)
        client.connection = mocker.Mock()
        client.transport.bind(client.connection)
        client.transport.noop = mocker.Mock(return_value=("OK", []))
        status = client.health_check()
        assert status["is_connected"] is True
        client.reset_metrics()
        assert client.get_metrics().total_operations == 0

    def test_health_check_not_ok(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        client.connection = mocker.Mock()
        client.transport.bind(client.connection)
        client.transport.noop = mocker.Mock(return_value=("NO", []))
        assert client.is_connected() is False

    def test_temporary_connection(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        mocker.patch.object(client, "is_connected", return_value=False)
        mocker.patch.object(client, "connect")
        mocker.patch.object(client, "disconnect")
        with client.temporary_connection() as c:
            assert c is client
        client.connect.assert_called_once()
        client.disconnect.assert_called_once()

    def test_getattr_delegates(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=True)
        client.connection = mocker.Mock()
        client.connection.capability = mocker.Mock(return_value=("OK", []))
        client.transport.bind(client.connection)
        assert client.capability()[0] == "OK"

    def test_getattr_no_connection(self):
        client = IMAPClient("host", "user", "pass")
        with pytest.raises(AttributeError):
            client.capability()

    def test_monitor_operation_disabled(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        client.connection = mocker.Mock()
        client.connection.capability = mocker.Mock(return_value=("OK", []))
        client.transport.bind(client.connection)
        client.capability()

    def test_clear_pool_and_stats(self):
        clear_connection_pool()
        stats = get_pool_stats()
        assert "max_connections" in stats

    def test_record_operation_success(self):
        client = IMAPClient("host", "user", "pass", enable_monitoring=True)
        client._record_operation_success(0.5)
        client._record_operation_success(0.3)
        assert client.metrics.total_operations == 2

    def test_health_monitor_loop_reconnects(self, mocker):
        client = IMAPClient("host", "user", "pass", enable_monitoring=False)
        mocker.patch.object(client, "is_connected", return_value=False)
        mocker.patch.object(client, "connect")
        client._stop_health_check.clear()

        calls = {"n": 0}

        def wait_side_effect(_timeout):
            calls["n"] += 1
            if calls["n"] > 1:
                client._stop_health_check.set()
                return True
            return False

        mocker.patch.object(
            client._stop_health_check, "wait", side_effect=wait_side_effect
        )
        client._health_monitor_loop()
        assert client.metrics.reconnection_attempts >= 1
