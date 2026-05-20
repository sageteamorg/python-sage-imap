"""Multi-tenant connection registry."""

from __future__ import annotations

import contextlib
import threading
from typing import Dict, Optional

from sage_imap.orm.config import ConnectionPolicy, ImapAccountConfig
from sage_imap.orm.exceptions import OrmConfigurationError
from sage_imap.session import IMAPSession


class ImapConnectionRegistry:
    """In-memory registry of long-lived sessions keyed by account_id."""

    def __init__(self) -> None:
        self._sessions: Dict[str, IMAPSession] = {}
        self._lock = threading.RLock()

    def get_or_create(self, config: ImapAccountConfig) -> IMAPSession:
        if config.connection_policy == ConnectionPolicy.PER_REQUEST:
            return self._create_session(config)
        with self._lock:
            existing = self._sessions.get(config.account_id)
            if existing and existing.client.is_connected():
                return existing
            session = self._create_session(config)
            self._sessions[config.account_id] = session
            session.connect()
            return session

    def release(self, account_id: str, *, disconnect: bool = False) -> None:
        with self._lock:
            session = self._sessions.pop(account_id, None)
        if session and disconnect:
            session.close()

    def clear(self) -> None:
        with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            with contextlib.suppress(Exception):
                session.close()

    @staticmethod
    def _create_session(config: ImapAccountConfig) -> IMAPSession:
        if not config.host or not config.username:
            raise OrmConfigurationError("ImapAccountConfig requires host and username")
        conn = config.to_connection_config()
        session = IMAPSession.from_config(conn, oauth_config=config.oauth_config)
        if config.use_pool or config.connection_policy == ConnectionPolicy.POOLED:
            session.client.use_pool = True
        return session


class _RegistryHolder:
    registry: Optional[ImapConnectionRegistry] = None


def get_connection_registry() -> ImapConnectionRegistry:
    if _RegistryHolder.registry is None:
        _RegistryHolder.registry = ImapConnectionRegistry()
    return _RegistryHolder.registry
