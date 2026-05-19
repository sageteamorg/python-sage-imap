"""Async IMAP client with transport layer, pooling hooks, and health monitoring."""

from __future__ import annotations

import asyncio
import logging
import socket
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sage_imap.aio.transport import AsyncIMAPTransport, _require_aioimaplib
from sage_imap.decorators import async_retry_on_failure
from sage_imap.exceptions import IMAPAuthenticationError, IMAPConnectionError
from sage_imap.services.client import (
    ConnectionConfig,
    ConnectionMetrics,
    build_ssl_context,
)

if TYPE_CHECKING:
    from sage_imap.auth.oauth2 import OAuth2Config  # pragma: no cover

logger = logging.getLogger(__name__)


class AsyncIMAPClient:
    """Async IMAP client mirroring :class:`~sage_imap.services.client.IMAPClient`."""

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
        **kwargs: Any,
    ) -> None:
        _require_aioimaplib()
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
        self.connection: Optional[Any] = None
        self.transport = AsyncIMAPTransport()
        self.metrics = ConnectionMetrics()
        self.authenticated = False
        self._connection_start_time: Optional[datetime] = None
        self._health_task: Optional[asyncio.Task] = None
        self._stop_health = asyncio.Event()
        self._stale = False
        self._selected_mailbox: Optional[str] = None

    @classmethod
    def from_config(cls, config: ConnectionConfig, **kwargs: Any) -> "AsyncIMAPClient":
        client = cls(
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
        client.config = config
        return client

    async def _connect_impl(self) -> Any:
        import aioimaplib

        self.metrics.connection_attempts += 1
        if self.connection is not None and not self._stale:
            if await self.is_connected():
                return self.connection
            await self.disconnect()

        try:
            if self.config.use_ssl:
                ssl_context = build_ssl_context(self.config)
                self.connection = aioimaplib.IMAP4_SSL(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout,
                    ssl_context=ssl_context,
                )
            else:
                self.connection = aioimaplib.IMAP4(
                    host=self.config.host,
                    port=self.config.port,
                    timeout=self.config.timeout,
                )
            await self.connection.wait_hello_from_server()
            self.transport.bind(self.connection)
        except (socket.gaierror, OSError, asyncio.TimeoutError) as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            raise IMAPConnectionError(
                "Failed to establish async IMAP connection."
            ) from e

        try:
            if self.config.oauth_access_token:
                await self._authenticate_oauth2(
                    self.config.username, self.config.oauth_access_token
                )
            else:
                resp = await self.connection.login(
                    self.config.username, self.config.password
                )
                if resp.result != "OK":
                    raise IMAPAuthenticationError("IMAP login failed.")
            self.authenticated = True
            self._stale = False
            self.metrics.successful_connections += 1
            self.metrics.last_connection_time = datetime.now()
            self._connection_start_time = datetime.now()
            if (
                self.config.enable_background_health
                and self.config.health_check_interval > 0
            ):
                await self._start_health_monitoring()
        except Exception as e:
            self.metrics.failed_connections += 1
            self.metrics.last_error = e
            await self.disconnect()
            if isinstance(e, IMAPAuthenticationError):
                raise
            raise IMAPAuthenticationError("IMAP login failed.") from e

        return self.connection

    async def connect(self) -> Any:
        decorated = async_retry_on_failure(
            max_retries=self.config.max_retries,
            delay=self.config.retry_delay,
            exponential_backoff=self.config.retry_exponential_backoff,
            exceptions=(IMAPConnectionError, socket.gaierror, OSError),
        )(self._connect_impl)
        return await decorated()

    async def connect_oauth2(self, username: str, access_token: str) -> Any:
        self.config.username = username
        self.config.oauth_access_token = access_token
        self.config.password = ""  # nosec B105 — OAuth2 uses token, not password
        return await self.connect()

    async def connect_with_oauth(
        self,
        oauth_config: "OAuth2Config",
        username: Optional[str] = None,
        *,
        refresh: bool = True,
        skew_seconds: float = 60.0,
    ) -> Any:
        from sage_imap.auth.oauth2_async import ensure_access_token_async

        if username:
            self.config.username = username
        if refresh:
            token = await ensure_access_token_async(oauth_config, skew_seconds)
        else:
            if not oauth_config.access_token:
                raise ValueError("access_token required when refresh=False")
            token = oauth_config.access_token
        return await self.connect_oauth2(self.config.username, token)

    async def _authenticate_oauth2(self, username: str, access_token: str) -> None:
        resp = await self.connection.xoauth2(username, access_token)
        if resp.result != "OK":
            raise IMAPAuthenticationError("XOAUTH2 authentication failed.")

    async def reconnect(self, mailbox: Optional[str] = None) -> Any:
        target = mailbox if mailbox is not None else self._selected_mailbox
        self.metrics.reconnection_attempts += 1
        await self.disconnect()
        conn = await self.connect()
        if target:
            self._selected_mailbox = target
        return conn

    def note_selected_mailbox(self, mailbox: Optional[str]) -> None:
        self._selected_mailbox = mailbox

    async def disconnect(self) -> None:
        self._stop_health.set()
        if self._health_task and not self._health_task.done():
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        if self.connection:
            try:
                if self._connection_start_time:
                    self.metrics.connection_uptime += (
                        datetime.now() - self._connection_start_time
                    )
                await self.connection.logout()
            except Exception as e:
                logger.warning("Error during async disconnect: %s", e)
            finally:
                self.connection = None
                self.transport.unbind()
                self.authenticated = False
                self._connection_start_time = None
                self._stale = False

    async def is_connected(self) -> bool:
        if not self.connection:
            return False
        try:
            status, _ = await self.transport.noop()
            if status == "OK":
                self._stale = False
                return True
            self._stale = True
            return False
        except Exception as e:
            logger.debug("Async connection health check failed: %s", e)
            self._stale = True
            return False

    async def health_check(self) -> Dict[str, Any]:
        health_status: Dict[str, Any] = {
            "is_connected": await self.is_connected(),
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

    async def _start_health_monitoring(self) -> None:
        if self._health_task and not self._health_task.done():
            return
        self._stop_health.clear()
        self._health_task = asyncio.create_task(self._health_monitor_loop())

    async def _health_monitor_loop(self) -> None:
        interval = self.config.health_check_interval
        while not self._stop_health.is_set():
            try:
                await asyncio.wait_for(self._stop_health.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass
            try:
                if not await self.is_connected():
                    logger.warning("Async health check failed - reconnecting")
                    self.metrics.reconnection_attempts += 1
                    self._stale = True
                    await self.connect()
            except Exception as e:
                logger.error("Error in async health monitor: %s", e)

    async def __aenter__(self) -> "AsyncIMAPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect()
