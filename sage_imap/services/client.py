import imaplib
import logging
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Dict, List, Optional

from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError

logger = logging.getLogger(__name__)


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
    password: str
    port: int = 993
    use_ssl: bool = True
    timeout: float = 30.0
    max_retries: int = 3
    retry_delay: float = 1.0
    retry_exponential_backoff: bool = True
    max_retry_delay: float = 30.0
    keepalive_interval: float = 300.0  # 5 minutes
    health_check_interval: float = 60.0  # 1 minute
    enable_monitoring: bool = True


class ConnectionPool:
    """Simple connection pool for IMAP connections."""

    def __init__(self, max_connections: int = 10):
        self.max_connections = max_connections
        self._connections: Dict[str, List[imaplib.IMAP4_SSL]] = {}
        self._lock = threading.Lock()
        self._connection_count = 0

    def get_connection_key(self, config: ConnectionConfig) -> str:
        """Generate a unique key for connection pooling."""
        return f"{config.host}:{config.port}:{config.username}"

    def get_connection(self, config: ConnectionConfig) -> Optional[imaplib.IMAP4_SSL]:
        """Get a connection from the pool."""
        key = self.get_connection_key(config)

        with self._lock:
            if key in self._connections and self._connections[key]:
                connection = self._connections[key].pop()
                logger.debug(f"Retrieved connection from pool for {key}")
                return connection

        return None

    def return_connection(
        self, config: ConnectionConfig, connection: imaplib.IMAP4_SSL
    ) -> None:
        """Return a connection to the pool."""
        key = self.get_connection_key(config)

        with self._lock:
            if key not in self._connections:
                self._connections[key] = []

            if len(self._connections[key]) < self.max_connections:
                self._connections[key].append(connection)
                logger.debug(f"Returned connection to pool for {key}")
            else:
                # Pool is full, close the connection
                try:
                    connection.logout()
                except:
                    pass

    def clear_pool(self) -> None:
        """Clear all connections from the pool."""
        with self._lock:
            for connections in self._connections.values():
                for connection in connections:
                    try:
                        connection.logout()
                    except:
                        pass
            self._connections.clear()


# Global connection pool instance
_connection_pool = ConnectionPool()


def retry_on_failure(
    max_retries: int = 3, delay: float = 1.0, exponential_backoff: bool = True
):
    """Decorator for retrying failed operations."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. Retrying in {current_delay}s..."
                        )
                        time.sleep(current_delay)

                        if exponential_backoff:
                            current_delay = min(
                                current_delay * 2, 30.0
                            )  # Cap at 30 seconds
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )

            raise last_exception

        return wrapper

    return decorator


def monitor_operation(func):
    """Decorator to monitor operation performance."""

    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if not hasattr(self, "metrics") or not self.config.enable_monitoring:
            return func(self, *args, **kwargs)

        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            self.metrics.total_operations += 1

            # Update average response time
            response_time = time.time() - start_time
            total_ops = self.metrics.total_operations
            self.metrics.average_response_time = (
                self.metrics.average_response_time * (total_ops - 1) + response_time
            ) / total_ops

            return result
        except Exception:
            self.metrics.failed_operations += 1
            raise

    return wrapper


class IMAPClient:
    """Enhanced IMAP client with advanced connection management and monitoring.

    Purpose
    -------
    This class provides a robust way to establish and manage connections to an IMAP server,
    with features like connection pooling, retry logic, health monitoring, and comprehensive
    error handling. It ensures proper cleanup and provides detailed metrics for monitoring.

    Parameters
    ----------
    host : str
        The hostname of the IMAP server.
    username : str
        The username for logging into the IMAP server.
    password : str
        The password for logging into the IMAP server.
    port : int, optional
        The port number for the IMAP server (default: 993 for SSL).
    use_ssl : bool, optional
        Whether to use SSL connection (default: True).
    timeout : float, optional
        Connection timeout in seconds (default: 30.0).
    max_retries : int, optional
        Maximum number of retry attempts (default: 3).
    retry_delay : float, optional
        Initial delay between retries in seconds (default: 1.0).
    **kwargs : dict
        Additional configuration options.

    Attributes
    ----------
    config : ConnectionConfig
        Configuration object containing all connection parameters.
    connection : imaplib.IMAP4_SSL or None
        The active IMAP connection object.
    metrics : ConnectionMetrics
        Metrics object for monitoring connection performance.

    Methods
    -------
    connect()
        Establishes an IMAP connection with retry logic.
    disconnect()
        Closes the IMAP connection and cleans up resources.
    is_connected()
        Checks if the connection is active and healthy.
    health_check()
        Performs a health check on the connection.
    get_metrics()
        Returns current connection metrics.
    reset_metrics()
        Resets all connection metrics.

    Example
    -------
    Using as context manager with enhanced features:
    >>> config = ConnectionConfig(
    ...     host='imap.example.com',
    ...     username='user@example.com',
    ...     password='password',
    ...     max_retries=5,
    ...     retry_delay=2.0
    ... )
    >>> with IMAPClient.from_config(config) as client:
    ...     status, messages = client.select("INBOX")
    ...     metrics = client.get_metrics()
    ...     print(f"Operations: {metrics.total_operations}")

    Using with connection pooling:
    >>> client = IMAPClient('imap.example.com', 'user', 'pass', use_pool=True)
    >>> client.connect()
    >>> # Connection is automatically returned to pool on disconnect
    >>> client.disconnect()
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        port: int = 993,
        use_ssl: bool = True,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        use_pool: bool = False,
        **kwargs,
    ):
        self.config = ConnectionConfig(
            host=host,
            username=username,
            password=password,
            port=port,
            use_ssl=use_ssl,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            **kwargs,
        )
        self.connection: Optional[imaplib.IMAP4_SSL] = None
        self.metrics = ConnectionMetrics()
        self.use_pool = use_pool
        self._connection_start_time: Optional[datetime] = None
        self._health_check_thread: Optional[threading.Thread] = None
        self._stop_health_check = threading.Event()

        logger.debug(f"IMAPClient initialized with host: {self.config.host}")

    @classmethod
    def from_config(cls, config: ConnectionConfig, **kwargs) -> "IMAPClient":
        """Create IMAPClient from configuration object."""
        return cls(
            host=config.host,
            username=config.username,
            password=config.password,
            port=config.port,
            use_ssl=config.use_ssl,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
            **kwargs,
        )

    @retry_on_failure()
    def connect(self) -> imaplib.IMAP4_SSL:
        """
        Establishes an IMAP connection with enhanced retry logic and monitoring.

        This method attempts to connect to the IMAP server with automatic retry on failure,
        connection pooling support, and comprehensive error handling. It also starts
        health monitoring if enabled.

        Returns
        -------
        imaplib.IMAP4_SSL
            The established IMAP connection object.

        Raises
        ------
        IMAPConnectionError
            If connection cannot be established after all retries.
        IMAPAuthenticationError
            If authentication fails.
        """
        self.metrics.connection_attempts += 1

        if self.connection is not None:
            if self.is_connected():
                logger.debug("Already connected to the IMAP server.")
                return self.connection
            else:
                logger.warning("Existing connection is stale, reconnecting...")
                self.disconnect()

        # Try to get connection from pool
        if self.use_pool:
            pooled_connection = _connection_pool.get_connection(self.config)
            if pooled_connection:
                try:
                    # Verify pooled connection is still valid
                    pooled_connection.noop()
                    self.connection = pooled_connection
                    self.metrics.successful_connections += 1
                    self._connection_start_time = datetime.now()
                    logger.info("Using pooled IMAP connection.")
                    return self.connection
                except:
                    logger.debug("Pooled connection is stale, creating new one")

        try:
            logger.debug(f"Resolving IMAP server hostname: {self.config.host}")
            resolved_host = socket.gethostbyname(self.config.host)
            logger.debug(f"Resolved hostname to IP: {resolved_host}")

            logger.debug("Establishing IMAP connection...")
            if self.config.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.config.host, self.config.port)
            else:
                self.connection = imaplib.IMAP4(self.config.host, self.config.port)

            # Set socket timeout
            if hasattr(self.connection, "sock"):
                self.connection.sock.settimeout(self.config.timeout)

            logger.info("IMAP connection established successfully.")
        except socket.gaierror as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            logger.error(f"Failed to resolve hostname: {e}")
            raise IMAPConnectionError("Failed to resolve hostname.") from e
        except (imaplib.IMAP4.error, socket.error) as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            logger.error(f"Failed to establish IMAP connection: {e}")
            raise IMAPConnectionError("Failed to establish IMAP connection.") from e

        try:
            logger.debug("Logging in to IMAP server...")
            self.connection.login(self.config.username, self.config.password)
            logger.info("Logged in to IMAP server successfully.")

            self.metrics.successful_connections += 1
            self.metrics.last_connection_time = datetime.now()
            self._connection_start_time = datetime.now()

            # Start health monitoring if enabled
            if self.config.enable_monitoring and self.config.health_check_interval > 0:
                self._start_health_monitoring()

        except imaplib.IMAP4.error as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            logger.error(f"IMAP login failed: {e}")
            # Close the connection since authentication failed
            try:
                self.connection.logout()
            except:
                pass
            self.connection = None
            raise IMAPAuthenticationError("IMAP login failed.") from e

        return self.connection

    def disconnect(self) -> None:
        """
        Closes the IMAP connection with proper cleanup and pool management.

        This method safely closes the connection, stops health monitoring,
        and optionally returns the connection to the pool for reuse.
        """
        self._stop_health_check.set()

        if self._health_check_thread and self._health_check_thread.is_alive():
            self._health_check_thread.join(timeout=1.0)

        if self.connection:
            try:
                # Update connection uptime
                if self._connection_start_time:
                    self.metrics.connection_uptime += (
                        datetime.now() - self._connection_start_time
                    )

                # Return to pool if enabled and connection is healthy
                if self.use_pool and self.is_connected():
                    _connection_pool.return_connection(self.config, self.connection)
                    logger.debug("Connection returned to pool.")
                else:
                    logger.debug("Logging out from IMAP server...")
                    self.connection.logout()
                    logger.info("Logged out from IMAP server successfully.")

            except Exception as e:
                logger.warning(f"Error during disconnect: {e}")
            finally:
                self.connection = None
                self._connection_start_time = None
        else:
            logger.debug("No connection to disconnect from.")

    @monitor_operation
    def is_connected(self) -> bool:
        """
        Check if the connection is active and healthy.

        Returns
        -------
        bool
            True if connection is active and responsive, False otherwise.
        """
        if not self.connection:
            return False

        try:
            # Send NOOP command to check connection health
            status, _ = self.connection.noop()
            return status == "OK"
        except Exception as e:
            logger.debug(f"Connection health check failed: {e}")
            # If connection check fails, mark connection as None
            self.connection = None
            return False

    @monitor_operation
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check on the connection.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing health status and metrics.
        """
        health_status = {
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
        """Get current connection metrics."""
        return self.metrics

    def reset_metrics(self) -> None:
        """Reset all connection metrics."""
        self.metrics = ConnectionMetrics()

    def _start_health_monitoring(self) -> None:
        """Start background health monitoring thread."""
        if self._health_check_thread and self._health_check_thread.is_alive():
            return

        self._stop_health_check.clear()
        self._health_check_thread = threading.Thread(
            target=self._health_monitor_loop, daemon=True
        )
        self._health_check_thread.start()
        logger.debug("Health monitoring started.")

    def _health_monitor_loop(self) -> None:
        """Background health monitoring loop."""
        while not self._stop_health_check.wait(self.config.health_check_interval):
            try:
                if not self.is_connected():
                    logger.warning("Health check failed - connection lost")
                    self.metrics.reconnection_attempts += 1
                    try:
                        self.connect()
                        logger.info("Connection restored by health monitor")
                    except Exception as e:
                        logger.error(
                            f"Health monitor failed to restore connection: {e}"
                        )
            except Exception as e:
                logger.error(f"Error in health monitor: {e}")

    @contextmanager
    def temporary_connection(self):
        """Context manager for temporary connections."""
        was_connected = self.is_connected()

        if not was_connected:
            self.connect()

        try:
            yield self.connection
        finally:
            if not was_connected:
                self.disconnect()

    def __enter__(self) -> imaplib.IMAP4_SSL:
        """Context manager entry - establishes connection."""
        return self.connect()

    def __exit__(
        self,
        exc_type: Optional[type],
        exc_value: Optional[BaseException],
        traceback: Optional[object],
    ) -> None:
        """Context manager exit - closes connection."""
        self.disconnect()

    def __del__(self):
        """Destructor to ensure proper cleanup."""
        try:
            self.disconnect()
        except:
            pass

    # Delegate IMAP operations to the connection with monitoring
    def __getattr__(self, name):
        """Delegate attribute access to the underlying connection."""
        if self.connection is None:
            raise AttributeError(f"No connection available for attribute '{name}'")

        attr = getattr(self.connection, name)

        # If it's a method, wrap it with monitoring
        if callable(attr):

            def wrapper(*args, **kwargs):
                # Apply monitoring if enabled
                if hasattr(self, "metrics") and self.config.enable_monitoring:
                    start_time = time.time()
                    try:
                        result = attr(*args, **kwargs)
                        self.metrics.total_operations += 1

                        # Update average response time
                        response_time = time.time() - start_time
                        total_ops = self.metrics.total_operations
                        self.metrics.average_response_time = (
                            self.metrics.average_response_time * (total_ops - 1)
                            + response_time
                        ) / total_ops

                        return result
                    except Exception:
                        self.metrics.failed_operations += 1
                        raise
                else:
                    # No monitoring, just call the method directly
                    return attr(*args, **kwargs)

            return wrapper

        return attr


# Utility functions for connection management
def clear_connection_pool():
    """Clear the global connection pool."""
    _connection_pool.clear_pool()


def get_pool_stats() -> Dict[str, Any]:
    """Get statistics about the connection pool."""
    return {
        "max_connections": _connection_pool.max_connections,
        "active_pools": len(_connection_pool._connections),
        "total_pooled_connections": sum(
            len(conns) for conns in _connection_pool._connections.values()
        ),
    }
