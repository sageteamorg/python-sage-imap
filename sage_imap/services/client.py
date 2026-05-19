import functools
import imaplib
import logging
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sage_imap.decorators import retry_on_failure
from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError
from sage_imap.services.transport import IMAPTransport

logger = logging.getLogger(__name__)


@functools.lru_cache(maxsize=256)
def _resolve_host(host: str) -> str:
    """Cache DNS lookups for repeated connections to the same host."""
    return socket.gethostbyname(host)


@dataclass
class ConnectionMetrics:
    """Metrics for IMAP connection monitoring."""

    connection_attempts: int = 0
    successful_connections: int = 0
    failed_connections: int = 0
    reconnection_attempts: int = 0
    last_connection_time: Optional[datetime] = None
    last_error: Optional[Exception] = None
    total_operations: int = 0
    failed_operations: int = 0
    average_response_time: float = 0.0
    connection_uptime: timedelta = field(default_factory=lambda: timedelta(0))


@dataclass
class ConnectionConfig:
    """Configuration for IMAP connection."""

    host: str
    username: str
    password: str = ""
    port: int = 993
    use_ssl: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_exponential_backoff: bool = True
    max_retry_delay: float = 30.0
    keepalive_interval: float = 300.0
    health_check_interval: float = 60.0
    enable_monitoring: bool = True
    enable_background_health: bool = False
    oauth_access_token: Optional[str] = None
    ssl_verify: bool = True


class _PooledConnection:
    """Wrapper tracking pool lease state."""

    __slots__ = ("connection", "in_use")

    def __init__(self, connection: imaplib.IMAP4) -> None:
        self.connection = connection
        self.in_use = False


class ConnectionPool:
    """
    Experimental connection pool for IMAP connections.

    Not thread-safe across multiple clients sharing one pool entry.
    """

    def __init__(self, max_connections: int = 10) -> None:
        self.max_connections = max_connections
        self._connections: Dict[str, List[_PooledConnection]] = {}
        self._lock = threading.Lock()

    def get_connection_key(self, config: ConnectionConfig) -> str:
        return f"{config.host}:{config.port}:{config.username}"

    def get_connection(self, config: ConnectionConfig) -> Optional[imaplib.IMAP4]:
        key = self.get_connection_key(config)
        with self._lock:
            pool = self._connections.get(key, [])
            for entry in pool:
                if not entry.in_use:
                    entry.in_use = True
                    logger.debug("Retrieved connection from pool for %s", key)
                    return entry.connection
        return None

    def return_connection(
        self, config: ConnectionConfig, connection: imaplib.IMAP4
    ) -> None:
        key = self.get_connection_key(config)
        with self._lock:
            if key not in self._connections:
                self._connections[key] = []
            for entry in self._connections[key]:
                if entry.connection is connection:
                    entry.in_use = False
                    logger.debug("Returned connection to pool for %s", key)
                    return
            if len(self._connections[key]) < self.max_connections:
                self._connections[key].append(_PooledConnection(connection))
                self._connections[key][-1].in_use = False
            else:
                try:
                    connection.logout()
                except Exception as e:
                    logger.debug("Failed to logout pooled connection: %s", e)

    def clear_pool(self) -> None:
        with self._lock:
            for entries in self._connections.values():
                for entry in entries:
                    try:
                        entry.connection.logout()
                    except Exception as e:
                        logger.debug("Failed to logout connection: %s", e)
            self._connections.clear()


_connection_pool = ConnectionPool()


def monitor_operation(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if not self.config.enable_monitoring:
            return func(self, *args, **kwargs)
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            self._record_operation_success(time.time() - start_time)
            return result
        except Exception:
            self.metrics.failed_operations += 1
            raise

    return wrapper


class IMAPClient:
    """Enhanced IMAP client with transport layer, pooling, and monitoring."""

    def __init__(
        self,
        host: str,
        username: str,
        password: Optional[str] = None,
        port: int = 993,
        use_ssl: bool = True,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        use_pool: bool = False,
        **kwargs,
    ) -> None:
        self.config = ConnectionConfig(
            host=host,
            username=username,
            password=password or "",
            port=port,
            use_ssl=use_ssl,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs,
        )
        self.connection: Optional[imaplib.IMAP4] = None
        self.transport = IMAPTransport()
        self.metrics = ConnectionMetrics()
        self.use_pool = use_pool
        self.authenticated = False
        self._connection_start_time: Optional[datetime] = None
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()
        self._stale = False
        self._selected_mailbox: Optional[str] = None

        logger.debug("IMAPClient initialized with host: %s", self.config.host)

    @classmethod
    def from_config(cls, config: ConnectionConfig, **kwargs) -> "IMAPClient":
        use_pool = kwargs.pop("use_pool", False)
        client = cls(
            host=config.host,
            username=config.username,
            password=config.password,
            port=config.port,
            use_ssl=config.use_ssl,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            use_pool=use_pool,
            **kwargs,
        )
        client.config = config
        return client

    def _record_operation_success(self, response_time: float) -> None:
        self.metrics.total_operations += 1
        total_ops = self.metrics.total_operations
        self.metrics.average_response_time = (
            self.metrics.average_response_time * (total_ops - 1) + response_time
        ) / total_ops

    def _connect_impl(self) -> imaplib.IMAP4:
        self.metrics.connection_attempts += 1

        if self.connection is not None and not self._stale:
            if self.is_connected():
                return self.connection
            logger.warning("Existing connection is stale, reconnecting...")
            self.disconnect()

        if self.use_pool:
            pooled = _connection_pool.get_connection(self.config)
            if pooled:
                try:
                    pooled.noop()
                    self.connection = pooled
                    self.transport.bind(pooled)
                    self._stale = False
                    self.authenticated = True
                    self.metrics.successful_connections += 1
                    self._connection_start_time = datetime.now()
                    logger.info("Using pooled IMAP connection.")
                    return self.connection
                except Exception:
                    logger.debug("Pooled connection is stale, creating new one")

        try:
            _resolve_host(self.config.host)
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.config.host, self.config.port)
            else:
                self.connection = imaplib.IMAP4(self.config.host, self.config.port)
                if hasattr(self.connection, "starttls"):
                    self.connection.starttls()

            if hasattr(self.connection, "sock") and self.connection.sock:
                self.connection.sock.settimeout(self.config.timeout)

            self.transport.bind(self.connection)
            logger.info("IMAP connection established successfully.")
        except socket.gaierror as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            raise IMAPConnectionError("Failed to resolve hostname.") from e
        except (imaplib.IMAP4.error, OSError) as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            raise IMAPConnectionError("Failed to establish IMAP connection.") from e

        try:
            if self.config.oauth_access_token:
                self._authenticate_oauth2(
                    self.config.username, self.config.oauth_access_token
                )
            else:
                self.connection.login(self.config.username, self.config.password)
            self.authenticated = True
            self._stale = False
            self.metrics.successful_connections += 1
            self.metrics.last_connection_time = datetime.now()
            self._connection_start_time = datetime.now()

            if (
                self.config.enable_background_health
                and self.config.health_check_interval > 0
            ):
                self._start_health_monitoring()
        except imaplib.IMAP4.error as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            try:
                self.connection.logout()
            except Exception as logout_err:
                logger.debug("Logout during failed login cleanup: %s", logout_err)
            self.connection = None
            self.transport.unbind()
            self.authenticated = False
            raise IMAPAuthenticationError("IMAP login failed.") from e

        return self.connection

    def connect(self) -> imaplib.IMAP4:
        decorated = retry_on_failure(
            max_retries=self.config.max_retries,
            delay=self.config.retry_delay,
            exponential_backoff=self.config.retry_exponential_backoff,
            exceptions=(
                IMAPConnectionError,
                socket.gaierror,
                OSError,
            ),
        )(self._connect_impl)
        return decorated()

    def connect_oauth2(self, username: str, access_token: str) -> imaplib.IMAP4:
        """Connect using XOAUTH2 (call before connect or set on config)."""
        self.config.username = username
        self.config.oauth_access_token = access_token
        self.config.password = ""  # nosec B105 — OAuth2 uses token, not password
        return self.connect()

    def _authenticate_oauth2(self, username: str, access_token: str) -> None:
        from sage_imap.auth.oauth2 import build_xoauth2_string

        auth_string = build_xoauth2_string(username, access_token)
        self.connection.authenticate("XOAUTH2", lambda _: auth_string.encode("utf-8"))

    def reconnect(self, mailbox: Optional[str] = None) -> imaplib.IMAP4:
        """
        Disconnect and connect again; optionally remember mailbox for re-select.

        Mailbox services should call ``select()`` after reconnect when
        ``mailbox`` is provided.
        """
        target = mailbox if mailbox is not None else self._selected_mailbox
        self.metrics.reconnection_attempts += 1
        self.disconnect()
        conn = self.connect()
        if target:
            self._selected_mailbox = target
        return conn

    def note_selected_mailbox(self, mailbox: Optional[str]) -> None:
        """Record the mailbox selected on this connection (used by IDLE reconnect)."""
        self._selected_mailbox = mailbox

    def disconnect(self) -> None:
        self._stop_health_check.set()
        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=1.0)

        if self.connection:
            try:
                if self._connection_start_time:
                    self.metrics.connection_uptime += (
                        datetime.now() - self._connection_start_time
                    )
                if self.use_pool and not self._stale:
                    _connection_pool.return_connection(self.config, self.connection)
                else:
                    self.connection.logout()
            except Exception as e:
                logger.warning("Error during disconnect: %s", e)
            finally:
                self.connection = None
                self.transport.unbind()
                self.authenticated = False
                self._connection_start_time = None
                self._stale = False

    @monitor_operation
    def is_connected(self) -> bool:
        if not self.connection:
            return False
        try:
            status, _ = self.transport.noop()
            if status == "OK":
                self._stale = False
                return True
            self._stale = True
            return False
        except Exception as e:
            logger.debug("Connection health check failed: %s", e)
            self._stale = True
            return False

    @monitor_operation
    def health_check(self) -> Dict[str, Any]:
        health_status: Dict[str, Any] = {
            "is_connected": self.is_connected(),
            "connection_age": None,
            "last_operation": self.metrics.last_connection_time,
            "total_operations": self.metrics.total_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": 0.0,
            "average_response_time": self.metrics.average_response_time,
            "last_error": (
                str(self.metrics.last_error) if self.metrics.last_error else None
            ),
            "stale": self._stale,
        }
        if self._connection_start_time:
            health_status["connection_age"] = (
                datetime.now() - self._connection_start_time
            ).total_seconds()
        if self.metrics.total_operations > 0:
            health_status["success_rate"] = (
                (self.metrics.total_operations - self.metrics.failed_operations)
                / self.metrics.total_operations
                * 100
            )
        return health_status

    def get_metrics(self) -> ConnectionMetrics:
        return self.metrics

    def reset_metrics(self) -> None:
        self.metrics = ConnectionMetrics()

    def _start_health_monitoring(self) -> None:
        if self._health_check_thread and self._health_check_thread.is_alive():
            return
        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_monitor_loop, daemon=True
        )
        self._health_check_thread.start()

    def _health_monitor_loop(self) -> None:
        while not self._stop_health_check.wait(self.config.health_check_interval):
            try:
                if not self.is_connected():
                    logger.warning("Health check failed - connection lost")
                    self.metrics.reconnection_attempts += 1
                    try:
                        self._stale = True
                        self.connect()
                    except Exception as e:
                        logger.error("Health monitor reconnect failed: %s", e)
            except Exception as e:
                logger.error("Error in health monitor: %s", e)

    @contextmanager
    def temporary_connection(self):
        was_connected = self.is_connected()
        if not was_connected:
            self.connect()
        try:
            yield self
        finally:
            if not was_connected:
                self.disconnect()

    def __enter__(self) -> "IMAPClient":
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.disconnect()

    def __getattr__(self, name: str):
        if self.connection is None:
            raise AttributeError(f"No connection available for attribute '{name}'")
        attr = getattr(self.connection, name)
        if not callable(attr):
            return attr

        def wrapper(*args, **kwargs):
            if self.config.enable_monitoring:
                start_time = time.time()
                try:
                    result = attr(*args, **kwargs)
                    self._record_operation_success(time.time() - start_time)
                    return result
                except Exception:
                    self.metrics.failed_operations += 1
                    raise
            return attr(*args, **kwargs)

        return wrapper


def clear_connection_pool() -> None:
    _connection_pool.clear_pool()


def get_pool_stats() -> Dict[str, Any]:
    total = sum(len(v) for v in _connection_pool._connections.values())
    return {
        "max_connections": _connection_pool.max_connections,
        "active_pools": len(_connection_pool._connections),
        "total_pooled_connections": total,
    }
