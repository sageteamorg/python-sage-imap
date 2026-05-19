"""IMAP transport layer: thread-safe, capability-aware command routing."""

from __future__ import annotations

import imaplib
import logging
import socket
import threading
from typing import Any, List, Optional, Tuple, Union

from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet
from sage_imap.services.transport_ops import expand_uid_set, parse_copyuid

logger = logging.getLogger(__name__)

IMAPResponse = Tuple[str, List[Any]]


class IMAPTransport:
    """
    Low-level IMAP command router bound to a single imaplib connection.

    All operations are serialized with an RLock for thread safety.

    Structurally implements :class:`~sage_imap.protocols.imap_transport.IMAPTransportProtocol`.
    """

    def __init__(self, connection: Optional[imaplib.IMAP4] = None) -> None:
        self._connection: Optional[imaplib.IMAP4] = connection
        self._lock = threading.RLock()
        self._capabilities: Optional[frozenset[str]] = None

    @property
    def connection(self) -> Optional[imaplib.IMAP4]:
        return self._connection

    def bind(self, connection: imaplib.IMAP4) -> None:
        """Attach an authenticated imaplib connection."""
        with self._lock:
            self._connection = connection
            self._capabilities = None

    def unbind(self) -> None:
        with self._lock:
            self._connection = None
            self._capabilities = None

    def _require_connection(self) -> imaplib.IMAP4:
        if self._connection is None:
            raise imaplib.IMAP4.error("No IMAP connection available")
        return self._connection

    def _run(self, func, *args, **kwargs) -> Any:
        with self._lock:
            conn = self._require_connection()
            return func(conn, *args, **kwargs)

    def noop(self) -> IMAPResponse:
        return self._run(imaplib.IMAP4.noop)

    def capability(self) -> IMAPResponse:
        return self._run(imaplib.IMAP4.capability)

    def get_capabilities(self) -> frozenset[str]:
        if self._capabilities is not None:
            return self._capabilities
        with self._lock:
            if self._capabilities is not None:  # pragma: no cover
                return self._capabilities
            caps: set[str] = set()
            try:
                status, data = self._require_connection().capability()
                if status == "OK" and data:
                    raw = data[0]
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", errors="replace")
                    caps = {c.upper() for c in raw.split()}
            except Exception as e:
                logger.debug("Failed to read capabilities: %s", e)
            self._capabilities = frozenset(caps)
            return self._capabilities

    def has_capability(self, name: str) -> bool:
        return name.upper() in self.get_capabilities()

    def select(self, mailbox: Optional[str] = "INBOX") -> IMAPResponse:
        return self._run(imaplib.IMAP4.select, mailbox)

    def close(self) -> IMAPResponse:
        return self._run(imaplib.IMAP4.close)

    def check(self) -> IMAPResponse:
        return self._run(imaplib.IMAP4.check)

    def status(self, mailbox: str, names: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.status, mailbox, names)

    def expunge(self) -> IMAPResponse:
        return self._run(imaplib.IMAP4.expunge)

    def list(self, directory: str = "", pattern: str = "*") -> IMAPResponse:
        return self._run(imaplib.IMAP4.list, directory, pattern)

    def namespace(self) -> IMAPResponse:
        """Return NAMESPACE response (RFC 2342) when supported."""
        if not self.has_capability("NAMESPACE"):
            return "NO", [b"NAMESPACE not supported"]
        return self._run(imaplib.IMAP4.namespace)

    def create(self, mailbox: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.create, mailbox)

    def delete(self, mailbox: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.delete, mailbox)

    def rename(self, old: str, new: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.rename, old, new)

    def subscribe(self, mailbox: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.subscribe, mailbox)

    def unsubscribe(self, mailbox: str) -> IMAPResponse:
        return self._run(imaplib.IMAP4.unsubscribe, mailbox)

    def lsub(self, directory: str = "", pattern: str = "*") -> IMAPResponse:
        return self._run(imaplib.IMAP4.lsub, directory, pattern)

    def append(
        self,
        mailbox: str,
        flags: Optional[str],
        date_time: Optional[str],
        message: Union[bytes, str],
    ) -> IMAPResponse:
        return self._run(imaplib.IMAP4.append, mailbox, flags, date_time, message)

    def authenticate(self, mechanism: str, authobject) -> IMAPResponse:
        return self._run(imaplib.IMAP4.authenticate, mechanism, authobject)

    def _charset_for_search(
        self, criteria: str, charset: Optional[str]
    ) -> Optional[str]:
        if charset:
            return charset
        try:
            criteria.encode("ascii")
            return None
        except UnicodeEncodeError:
            return "UTF-8"

    def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse:
        charset_arg = self._charset_for_search(criteria, charset)

        def _search(conn: imaplib.IMAP4) -> IMAPResponse:
            if use_uid:
                if charset_arg:
                    return conn.uid("SEARCH", charset_arg, criteria)
                return conn.uid("SEARCH", None, criteria)
            if charset_arg:
                return conn.search(charset_arg, criteria)
            return conn.search(None, criteria)

        return self._run(_search)

    def uid(self, command: str, *args) -> IMAPResponse:
        return self._run(imaplib.IMAP4.uid, command, *args)

    def idle_start(self) -> str:
        """
        Enter IDLE state. Do not hold other commands until :meth:`idle_done`.

        Only one IDLE session per connection; not re-entrant with other commands.
        """
        with self._lock:
            conn = self._require_connection()
            if not hasattr(conn, "idle"):
                raise imaplib.IMAP4.error("IDLE not supported by server")
            typ, _ = conn.idle()
            return typ

    def idle_done(self) -> IMAPResponse:
        """Exit IDLE (sends DONE)."""
        with self._lock:
            conn = self._require_connection()
            if hasattr(conn, "done"):
                return conn.done()
            return conn._simple_command("DONE")

    def idle_read_lines(self, timeout: float = 60.0) -> List[bytes]:
        """
        Read untagged lines while in IDLE until timeout.

        Must be called after :meth:`idle_start` and before :meth:`idle_done`.
        """
        conn = self._require_connection()
        lines: List[bytes] = []
        sock = getattr(conn, "sock", None) or getattr(conn, "socket", None)
        if sock is None:
            return lines
        old_timeout = sock.gettimeout()
        try:
            sock.settimeout(timeout)
            while True:
                try:
                    line = conn.readline()
                except socket.timeout:
                    break
                if not line:
                    break
                if line.strip() in (b"+ idling", b"+ Idling"):
                    continue
                if line.startswith(b"+"):
                    continue
                lines.append(line)
                if line.startswith(b"*"):
                    break
        finally:
            try:
                sock.settimeout(old_timeout)
            except OSError:
                pass
        return lines

    def fetch(
        self, msg_set: MessageSet, parts: str, use_uid: Optional[bool] = None
    ) -> IMAPResponse:
        use_uid = msg_set.is_uid if use_uid is None else use_uid
        ids = msg_set.msg_ids

        def _fetch(conn: imaplib.IMAP4) -> IMAPResponse:
            if use_uid:
                return conn.uid("FETCH", ids, parts)
            return conn.fetch(ids, parts)

        return self._run(_fetch)

    def store_flags(
        self,
        msg_set: MessageSet,
        command: Union[FlagCommand, str],
        *flags: Union[Flag, str],
    ) -> IMAPResponse:
        cmd = command.value if isinstance(command, FlagCommand) else command
        flag_values = tuple(f.value if isinstance(f, Flag) else f for f in flags)
        ids = msg_set.msg_ids

        def _store(conn: imaplib.IMAP4) -> IMAPResponse:
            if msg_set.is_uid:
                return conn.uid("STORE", ids, cmd, *flag_values)
            return conn.store(ids, cmd, *flag_values)

        return self._run(_store)

    def set_flags(self, msg_set: MessageSet, flags: List[Flag]) -> IMAPResponse:
        flag_string = " ".join(f.value for f in flags)
        ids = msg_set.msg_ids

        def _set(conn: imaplib.IMAP4) -> IMAPResponse:
            if msg_set.is_uid:
                return conn.uid("STORE", ids, "FLAGS", f"({flag_string})")
            return conn.store(ids, "FLAGS", f"({flag_string})")

        return self._run(_set)

    def copy(self, msg_set: MessageSet, destination: str) -> Tuple[IMAPResponse, dict]:
        """Copy messages; returns (response, metadata with copyuid if available)."""
        ids = msg_set.msg_ids
        metadata: dict = {"method": "COPY"}

        def _copy(conn: imaplib.IMAP4) -> IMAPResponse:
            if msg_set.is_uid:
                return conn.uid("COPY", ids, destination)
            return conn.copy(ids, destination)

        response = self._run(_copy)
        metadata["copyuid"] = parse_copyuid(response)
        return response[0], metadata

    def move(self, msg_set: MessageSet, destination: str) -> Tuple[IMAPResponse, dict]:
        """
        Move messages using MOVE extension when available, else COPY+DELETE+EXPUNGE.
        """
        if self.has_capability("MOVE"):
            ids = msg_set.msg_ids
            metadata: dict = {"method": "MOVE"}

            def _move(conn: imaplib.IMAP4) -> IMAPResponse:
                if msg_set.is_uid:
                    return conn.uid("MOVE", ids, destination)
                if hasattr(conn, "move"):
                    return conn.move(ids, destination)
                return conn._simple_command("MOVE", ids, destination)

            response = self._run(_move)
            metadata["copyuid"] = parse_copyuid(response)
            return response[0], metadata

        status, copy_meta = self.copy(msg_set, destination)
        if status != "OK":
            return status, {"method": "COPY_DELETE", **copy_meta}

        store_status, _ = self.store_flags(msg_set, FlagCommand.ADD, Flag.DELETED)
        if store_status != "OK":
            return store_status, {
                "method": "COPY_DELETE",
                "warning": "copied but not marked deleted",
                **copy_meta,
            }

        expunge_status, _ = self.expunge()
        return expunge_status, {"method": "COPY_DELETE", **copy_meta}

    def search_by_message_ids(
        self, message_ids: List[str], mailbox_charset: Optional[str] = "UTF-8"
    ) -> List[int]:
        """Search UIDs by RFC Message-ID headers."""
        uids: List[int] = []
        for mid in message_ids:
            if not mid:
                continue
            criteria = f'HEADER "Message-ID" "{mid.strip("<>")}"'
            status, data = self.search(criteria, charset=mailbox_charset, use_uid=True)
            if status == "OK" and data and data[0]:
                for uid in data[0].split():
                    uids.append(int(uid))
        return uids

    def resolve_uids_after_copy(
        self,
        source_set: MessageSet,
        _copy_response: IMAPResponse,
        copy_metadata: dict,
        message_ids: Optional[List[str]] = None,
    ) -> MessageSet:
        """
        Map source UIDs to destination UIDs after a copy/move using COPYUID or Message-ID.
        """
        copyuid = copy_metadata.get("copyuid")
        if copyuid and source_set.is_uid:
            dest_part = copyuid.get("dest_uids", "")
            dest_uids = expand_uid_set(dest_part)
            if dest_uids:
                return MessageSet.from_uids(dest_uids, mailbox=source_set.mailbox)

        if message_ids:
            found = self.search_by_message_ids(message_ids)
            if found:
                return MessageSet.from_uids(found, mailbox=source_set.mailbox)

        return source_set

    # Backward-compatible aliases for tests and subclasses.
    _parse_copyuid = staticmethod(parse_copyuid)
    _expand_uid_set = staticmethod(expand_uid_set)
