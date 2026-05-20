"""ORM configuration: accounts, connection policy, load levels."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Optional, Protocol

if TYPE_CHECKING:
    from sage_imap.auth.oauth2 import OAuth2Config
    from sage_imap.services.client import ConnectionConfig


class LoadLevel(StrEnum):
    """How much of each message to FETCH and parse."""

    IDENTITY = "identity"
    HEADERS = "headers"
    FULL = "full"


class ConnectionPolicy(StrEnum):
    """How the ORM obtains IMAP connections for an account."""

    PER_REQUEST = "per_request"
    POOLED = "pooled"
    LONG_LIVED = "long_lived"


@dataclass
class ImapAccountConfig:
    """Connection profile for one tenant account (credentials live in app storage)."""

    account_id: str
    host: str
    username: str
    password: str = ""
    port: int = 993
    use_ssl: bool = True
    oauth_config: Optional["OAuth2Config"] = None
    connection_policy: ConnectionPolicy = ConnectionPolicy.PER_REQUEST
    use_pool: bool = False
    default_load_level: LoadLevel = LoadLevel.HEADERS
    dialect: Optional[str] = None
    extra: dict = field(default_factory=dict)

    def to_connection_config(self) -> "ConnectionConfig":
        from sage_imap.services.client import ConnectionConfig

        return ConnectionConfig(
            host=self.host,
            username=self.username,
            password=self.password,
            port=self.port,
            use_ssl=self.use_ssl,
        )


class AccountProvider(Protocol):
    """App-implemented lookup of :class:`ImapAccountConfig` by ``account_id``."""

    def get_config(self, account_id: str) -> ImapAccountConfig: ...
