"""Structural protocol for IMAP transport implementations (sync and async)."""

from __future__ import annotations

from typing import Any, List, Optional, Protocol, Tuple, Union, runtime_checkable

from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet

IMAPResponse = Tuple[str, List[Any]]


@runtime_checkable
class IMAPTransportProtocol(Protocol):
    """Command surface shared by :class:`~sage_imap.services.transport.IMAPTransport` and async transport."""

    def noop(self) -> IMAPResponse: ...

    def capability(self) -> IMAPResponse: ...

    def get_capabilities(self) -> frozenset[str]: ...

    def has_capability(self, name: str) -> bool: ...

    def select(self, mailbox: Optional[str] = "INBOX") -> IMAPResponse: ...

    def close(self) -> IMAPResponse: ...

    def check(self) -> IMAPResponse: ...

    def status(self, mailbox: str, names: str) -> IMAPResponse: ...

    def expunge(self) -> IMAPResponse: ...

    def list(self, directory: str = "", pattern: str = "*") -> IMAPResponse: ...

    def namespace(self) -> IMAPResponse: ...

    def create(self, mailbox: str) -> IMAPResponse: ...

    def delete(self, mailbox: str) -> IMAPResponse: ...

    def rename(self, old: str, new: str) -> IMAPResponse: ...

    def subscribe(self, mailbox: str) -> IMAPResponse: ...

    def unsubscribe(self, mailbox: str) -> IMAPResponse: ...

    def lsub(self, directory: str = "", pattern: str = "*") -> IMAPResponse: ...

    def append(
        self,
        mailbox: str,
        flags: Optional[str],
        date_time: Optional[str],
        message: Union[bytes, str],
    ) -> IMAPResponse: ...

    def authenticate(self, mechanism: str, authobject) -> IMAPResponse: ...

    def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse: ...

    def uid(self, command: str, *args) -> IMAPResponse: ...

    def idle_start(self) -> str: ...

    def idle_done(self) -> IMAPResponse: ...

    def idle_read_lines(self, timeout: float = 60.0) -> List[bytes]: ...

    def fetch(
        self, msg_set: MessageSet, parts: str, use_uid: Optional[bool] = None
    ) -> IMAPResponse: ...

    def store_flags(
        self,
        msg_set: MessageSet,
        command: Union[FlagCommand, str],
        *flags: Union[Flag, str],
    ) -> IMAPResponse: ...

    def set_flags(self, msg_set: MessageSet, flags: List[Flag]) -> IMAPResponse: ...

    def copy(
        self, msg_set: MessageSet, destination: str
    ) -> Tuple[IMAPResponse, dict]: ...

    def move(
        self, msg_set: MessageSet, destination: str
    ) -> Tuple[IMAPResponse, dict]: ...

    def search_by_message_ids(
        self, message_ids: List[str], mailbox_charset: Optional[str] = "UTF-8"
    ) -> List[int]: ...

    def resolve_uids_after_copy(
        self,
        source_set: MessageSet,
        _copy_response: IMAPResponse,
        copy_metadata: dict,
        message_ids: Optional[List[str]] = None,
    ) -> MessageSet: ...
