"""Async IMAP transport backed by aioimaplib with per-connection asyncio.Lock."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, List, Optional, Tuple, Union

from sage_imap.aio._response import (
    fetch_lines_to_imaplib_data,
    response_to_imap,
    search_data_from_lines,
)
from sage_imap.helpers.enums import Flag, FlagCommand
from sage_imap.models.message import MessageSet
from sage_imap.protocols.imap_transport import IMAPResponse
from sage_imap.services.transport_ops import expand_uid_set, parse_copyuid

logger = logging.getLogger(__name__)

try:
    import aioimaplib
except ImportError as _exc:  # pragma: no cover
    aioimaplib = None  # type: ignore[assignment]
    _AIOIMAP_IMPORT_ERROR = _exc
else:
    _AIOIMAP_IMPORT_ERROR = None


def _require_aioimaplib() -> None:
    if aioimaplib is None:
        raise ImportError(
            "Async IMAP requires aioimaplib. Install with: pip install python-sage-imap[async]"
        ) from _AIOIMAP_IMPORT_ERROR


class AsyncIMAPTransport:
    """
    Low-level async IMAP command router bound to a single aioimaplib connection.

    All operations are serialized with :class:`asyncio.Lock`.
    """

    def __init__(self, connection: Optional[Any] = None) -> None:
        _require_aioimaplib()
        self._connection = connection
        self._lock = asyncio.Lock()
        self._capabilities: Optional[frozenset[str]] = None
        self._idle_active = False

    @property
    def connection(self) -> Optional[Any]:
        return self._connection

    def bind(self, connection: Any) -> None:
        self._connection = connection
        self._capabilities = None

    def unbind(self) -> None:
        self._connection = None
        self._capabilities = None
        self._idle_active = False

    def _require_connection(self) -> Any:
        if self._connection is None:
            raise RuntimeError("No async IMAP connection available")
        return self._connection

    async def _run(self, coro):
        async with self._lock:
            return await coro

    @staticmethod
    def _norm(response: Any) -> IMAPResponse:
        status, lines = response_to_imap(response)
        return status, lines

    async def noop(self) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().noop())

        return await self._run(_op())

    async def capability(self) -> IMAPResponse:
        conn = self._require_connection()
        caps = sorted(conn.protocol.capabilities) if conn.protocol else []
        line = ("CAPABILITY " + " ".join(caps)).encode() if caps else b""
        return "OK", [line]

    async def get_capabilities(self) -> frozenset[str]:
        if self._capabilities is not None:
            return self._capabilities
        conn = self._require_connection()
        caps = {c.upper() for c in (conn.protocol.capabilities or set())}
        self._capabilities = frozenset(caps)
        return self._capabilities

    async def has_capability(self, name: str) -> bool:
        return name.upper() in await self.get_capabilities()

    async def select(self, mailbox: Optional[str] = "INBOX") -> IMAPResponse:
        async def _op():
            return self._norm(
                await self._require_connection().select(mailbox or "INBOX")
            )

        return await self._run(_op())

    async def close(self) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().close())

        return await self._run(_op())

    async def check(self) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().check())

        return await self._run(_op())

    async def status(self, mailbox: str, names: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().status(mailbox, names))

        return await self._run(_op())

    async def expunge(self) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().expunge())

        return await self._run(_op())

    async def list(self, directory: str = "", pattern: str = "*") -> IMAPResponse:
        from aioimaplib.aioimaplib import quoted

        async def _op():
            reference_name = quoted(directory) if directory else '""'
            mailbox_pattern = quoted(pattern)
            return self._norm(
                await self._require_connection().list(
                    reference_name,
                    mailbox_pattern,
                )
            )

        return await self._run(_op())

    async def namespace(self) -> IMAPResponse:
        if not await self.has_capability("NAMESPACE"):
            return "NO", [b"NAMESPACE not supported"]

        async def _op():
            return self._norm(await self._require_connection().namespace())

        return await self._run(_op())

    async def create(self, mailbox: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().create(mailbox))

        return await self._run(_op())

    async def delete(self, mailbox: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().delete(mailbox))

        return await self._run(_op())

    async def rename(self, old: str, new: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().rename(old, new))

        return await self._run(_op())

    async def subscribe(self, mailbox: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().subscribe(mailbox))

        return await self._run(_op())

    async def unsubscribe(self, mailbox: str) -> IMAPResponse:
        async def _op():
            return self._norm(await self._require_connection().unsubscribe(mailbox))

        return await self._run(_op())

    async def lsub(self, directory: str = "", pattern: str = "*") -> IMAPResponse:
        from aioimaplib.aioimaplib import quoted

        async def _op():
            reference_name = quoted(directory) if directory else '""'
            mailbox_name = quoted(pattern)
            return self._norm(
                await self._require_connection().lsub(reference_name, mailbox_name)
            )

        return await self._run(_op())

    async def append(
        self,
        mailbox: str,
        flags: Optional[str],
        date_time: Optional[str],
        message: Union[bytes, str],
    ) -> IMAPResponse:
        msg_bytes = message.encode() if isinstance(message, str) else message

        async def _op():
            return self._norm(
                await self._require_connection().append(
                    msg_bytes, mailbox=mailbox, flags=flags, date=date_time
                )
            )

        return await self._run(_op())

    async def authenticate(self, mechanism: str, authobject) -> IMAPResponse:
        mech = mechanism.upper()
        if mech == "XOAUTH2":
            raw = authobject(None)
            if isinstance(raw, bytes):
                token = raw.decode("utf-8", errors="replace")
            else:
                token = str(raw)
            user = ""
            return await self._run(
                self._norm(await self._require_connection().xoauth2(user, token))
            )
        raise NotImplementedError(f"Async authenticate not implemented for {mechanism}")

    @staticmethod
    def _charset_for_search(criteria: str, charset: Optional[str]) -> Optional[str]:
        if charset:
            return charset
        try:
            criteria.encode("ascii")
            return None
        except UnicodeEncodeError:
            return "UTF-8"

    async def search(
        self, criteria: str, charset: Optional[str] = None, use_uid: bool = False
    ) -> IMAPResponse:
        charset_arg = self._charset_for_search(criteria, charset)
        parts = criteria.split()

        async def _op():
            conn = self._require_connection()
            if use_uid:
                if charset_arg:
                    resp = await conn.uid_search("CHARSET", charset_arg, *parts)
                else:
                    resp = await conn.uid_search(*parts)
            else:
                if charset_arg:
                    resp = await conn.search("CHARSET", charset_arg, *parts)
                else:
                    resp = await conn.search(*parts)
            status, lines = response_to_imap(resp)
            return status, search_data_from_lines(lines)

        return await self._run(_op())

    async def uid(self, command: str, *args) -> IMAPResponse:
        async def _op():
            resp = await self._require_connection().uid(command, *args)
            status, lines = response_to_imap(resp)
            if command.upper() == "FETCH":
                return status, fetch_lines_to_imaplib_data(lines)
            return status, lines

        return await self._run(_op())

    async def idle_start(self) -> str:
        async with self._lock:
            conn = self._require_connection()
            caps = {c.upper() for c in (conn.protocol.capabilities or set())}
            if "IDLE" not in caps:
                raise RuntimeError("IDLE not supported by server")
            await conn.idle_start()
            self._idle_active = True
            return "OK"

    async def idle_done(self) -> IMAPResponse:
        async with self._lock:
            conn = self._require_connection()
            conn.idle_done()
            self._idle_active = False
            return "OK", []

    async def idle_read_lines(self, timeout: float = 60.0) -> List[bytes]:
        if not self._idle_active:
            return []
        conn = self._require_connection()
        try:
            resp = await asyncio.wait_for(conn.wait_server_push(), timeout=timeout)
            _, lines = response_to_imap(resp)
            return [ln for ln in lines if isinstance(ln, (bytes, bytearray))]
        except asyncio.TimeoutError:
            return []

    async def fetch(
        self, msg_set: MessageSet, parts: str, use_uid: Optional[bool] = None
    ) -> IMAPResponse:
        use_uid = msg_set.is_uid if use_uid is None else use_uid
        ids = msg_set.msg_ids

        async def _op():
            conn = self._require_connection()
            resp = await conn.protocol.fetch(ids, parts, by_uid=use_uid)
            status, lines = response_to_imap(resp)
            return status, fetch_lines_to_imaplib_data(lines)

        return await self._run(_op())

    async def store_flags(
        self,
        msg_set: MessageSet,
        command: Union[FlagCommand, str],
        *flags: Union[Flag, str],
    ) -> IMAPResponse:
        cmd = command.value if isinstance(command, FlagCommand) else command
        flag_values = tuple(f.value if isinstance(f, Flag) else f for f in flags)
        ids = msg_set.msg_ids

        async def _op():
            conn = self._require_connection()
            resp = await conn.protocol.store(
                ids, cmd, *flag_values, by_uid=msg_set.is_uid
            )
            return self._norm(resp)

        return await self._run(_op())

    async def set_flags(self, msg_set: MessageSet, flags: List[Flag]) -> IMAPResponse:
        flag_string = " ".join(f.value for f in flags)
        ids = msg_set.msg_ids

        async def _op():
            conn = self._require_connection()
            resp = await conn.protocol.store(
                ids, "FLAGS", f"({flag_string})", by_uid=msg_set.is_uid
            )
            return self._norm(resp)

        return await self._run(_op())

    async def copy(
        self, msg_set: MessageSet, destination: str
    ) -> Tuple[IMAPResponse, dict]:
        ids = msg_set.msg_ids
        metadata: dict = {"method": "COPY"}

        async def _op():
            conn = self._require_connection()
            resp = await conn.protocol.copy(ids, destination, by_uid=msg_set.is_uid)
            return self._norm(resp)

        response = await self._run(_op())
        metadata["copyuid"] = parse_copyuid(response)
        return response[0], metadata

    async def move(
        self, msg_set: MessageSet, destination: str
    ) -> Tuple[IMAPResponse, dict]:
        if await self.has_capability("MOVE"):
            ids = msg_set.msg_ids
            metadata: dict = {"method": "MOVE"}

            async def _op():
                conn = self._require_connection()
                resp = await conn.protocol.move(ids, destination, by_uid=msg_set.is_uid)
                return self._norm(resp)

            response = await self._run(_op())
            metadata["copyuid"] = parse_copyuid(response)
            return response[0], metadata

        # COPY + DELETE + EXPUNGE fallback
        status, copy_meta = await self.copy(msg_set, destination)
        if status != "OK":
            return status, {"method": "COPY_DELETE", **copy_meta}
        store_status, _ = await self.store_flags(msg_set, FlagCommand.ADD, Flag.DELETED)
        if store_status != "OK":
            return store_status, {
                "method": "COPY_DELETE",
                "warning": "copied but not marked deleted",
                **copy_meta,
            }
        expunge_status, _ = await self.expunge()
        return expunge_status, {"method": "COPY_DELETE", **copy_meta}

    async def search_by_message_ids(
        self, message_ids: List[str], mailbox_charset: Optional[str] = "UTF-8"
    ) -> List[int]:
        uids: List[int] = []
        for mid in message_ids:
            if not mid:
                continue
            criteria = f'HEADER "Message-ID" "{mid.strip("<>")}"'
            status, data = await self.search(
                criteria, charset=mailbox_charset, use_uid=True
            )
            if status == "OK" and data and data[0]:
                for uid in data[0].split():
                    uids.append(int(uid))
        return uids

    async def resolve_uids_after_copy(
        self,
        source_set: MessageSet,
        _copy_response: IMAPResponse,
        copy_metadata: dict,
        message_ids: Optional[List[str]] = None,
    ) -> MessageSet:
        copyuid = copy_metadata.get("copyuid")
        if copyuid and source_set.is_uid:
            dest_part = copyuid.get("dest_uids", "")
            dest_uids = expand_uid_set(dest_part)
            if dest_uids:
                return MessageSet.from_uids(dest_uids, mailbox=source_set.mailbox)
        if message_ids:
            found = await self.search_by_message_ids(message_ids)
            if found:
                return MessageSet.from_uids(found, mailbox=source_set.mailbox)
        return source_set
