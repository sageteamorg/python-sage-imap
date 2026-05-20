"""QuerySet: compile filters, paginate, and materialize ImapMessage rows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Iterator, Optional, Union

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet
from sage_imap.orm.config import LoadLevel
from sage_imap.orm.exceptions import OrmMailboxNotSelectedError, OrmNotConnectedError
from sage_imap.orm.q import Q, _filters_to_criteria

if TYPE_CHECKING:
    from sage_imap.orm.backends.protocol import ImapBackend
    from sage_imap.orm.models.message import ImapMessage
    from sage_imap.sync.state import MailboxSyncState


def _expand_uids(msg_set: MessageSet) -> list[int]:
    """Expand MessageSet UIDs including compact ranges like ``1:2``."""
    ids = list(msg_set.parsed_ids)
    for start, end in msg_set.id_ranges:
        if isinstance(start, int) and isinstance(end, int):
            ids.extend(range(start, end + 1))
    return sorted(set(ids))


class MessageQuerySet:
    """Lazy IMAP message queryset (UID SEARCH + batched FETCH)."""

    def __init__(
        self,
        backend: Optional["ImapBackend"] = None,
        *,
        account_id: str = "",
        mailbox: Optional[str] = None,
    ) -> None:
        self._backend = backend
        self._account_id = account_id
        self._mailbox = mailbox
        self._criteria_parts: list[str] = []
        self._raw: Optional[str] = None
        self._limit: Optional[int] = None
        self._offset: int = 0
        self._cursor_after: Optional[int] = None
        self._cursor_before: Optional[int] = None
        self._load_level: Optional[LoadLevel] = None
        self._order_by: Optional[str] = None
        self._changed_since: Optional["MailboxSyncState"] = None
        self._batch_size: int = 50

    def _require_backend(self) -> "ImapBackend":
        if self._backend is None:
            raise OrmNotConnectedError("No active ImapORM session")
        return self._backend

    def using_backend(self, backend: "ImapBackend") -> "MessageQuerySet":
        clone = self._clone()
        clone._backend = backend
        clone._account_id = backend.account_id
        clone._mailbox = backend.mailbox
        return clone

    def filter(self, *args: Union[Q, str], **kwargs: Any) -> "MessageQuerySet":
        clone = self._clone()
        for arg in args:
            if isinstance(arg, Q):
                clone._criteria_parts.append(arg.compile())
            else:
                clone._criteria_parts.append(str(arg))
        if kwargs:
            clone._criteria_parts.append(_filters_to_criteria(kwargs))
        return clone

    def exclude(self, **kwargs: Any) -> "MessageQuerySet":
        criteria = _filters_to_criteria(kwargs)
        return self.filter(Q(criteria, _negated=True))

    def raw_criteria(self, criteria: str) -> "MessageQuerySet":
        clone = self._clone()
        clone._raw = criteria
        return clone

    def limit(self, n: int) -> "MessageQuerySet":
        clone = self._clone()
        clone._limit = n
        return clone

    def offset(self, n: int) -> "MessageQuerySet":
        clone = self._clone()
        clone._offset = n
        return clone

    def cursor(
        self,
        *,
        after_uid: Optional[int] = None,
        before_uid: Optional[int] = None,
    ) -> "MessageQuerySet":
        clone = self._clone()
        clone._cursor_after = after_uid
        clone._cursor_before = before_uid
        return clone

    def with_load_level(self, level: LoadLevel) -> "MessageQuerySet":
        clone = self._clone()
        clone._load_level = level
        return clone

    def order_by(self, field: str) -> "MessageQuerySet":
        clone = self._clone()
        clone._order_by = field
        return clone

    def changed_since(self, state: "MailboxSyncState") -> "MessageQuerySet":
        clone = self._clone()
        clone._changed_since = state
        return clone

    def compile_criteria(self) -> str:
        if self._raw:
            return self._raw
        if not self._criteria_parts:
            return str(IMAPSearchCriteria.ALL)
        if len(self._criteria_parts) == 1:
            return self._criteria_parts[0]
        return IMAPSearchCriteria.and_criteria(*self._criteria_parts)

    def uids(self) -> MessageSet:
        backend = self._require_backend()
        mailbox = self._resolve_mailbox(backend)
        if self._changed_since is not None:
            msg_set = backend.find_changed_uids(self._changed_since)
        else:
            result = backend.uid_search(self.compile_criteria())
            if not result.success:
                return MessageSet.empty(mailbox=mailbox)
            msg_set = result.to_uid_message_set(mailbox=mailbox)
        return self._apply_pagination(msg_set)

    def count(self) -> int:
        return len(_expand_uids(self.uids()))

    def iter(self) -> Iterator["ImapMessage"]:
        from sage_imap.orm.models.message import ImapMessage

        backend = self._require_backend()
        mailbox = self._resolve_mailbox(backend)
        uid_list = _expand_uids(self.uids())
        msg_set = (
            MessageSet.from_uids(uid_list, mailbox=mailbox)
            if uid_list
            else MessageSet.empty(mailbox=mailbox)
        )
        level = self._load_level or LoadLevel.HEADERS
        if level == LoadLevel.IDENTITY:
            messages = [
                ImapMessage.from_uid(backend.account_id, mailbox, uid, backend=backend)
                for uid in uid_list
            ]
        else:
            messages = list(
                backend.fetch_messages(
                    msg_set, load_level=level, batch_size=self._batch_size
                )
            )
        if self._order_by:
            messages = self._sort_messages(messages)
        yield from messages

    def fetch_all(self) -> list["ImapMessage"]:
        return list(self.iter())

    def bulk_mark_seen(self) -> int:
        from sage_imap.orm.models.message import ImapMessage

        backend = self._require_backend()
        uids = _expand_uids(self.uids())
        for uid in uids:
            msg = ImapMessage.from_uid(
                backend.account_id, self._resolve_mailbox(backend), uid, backend=backend
            )
            backend.mark_seen(msg)
        return len(uids)

    async def uids_async(self) -> MessageSet:
        backend = self._require_backend()
        mailbox = self._resolve_mailbox(backend)
        if self._changed_since is not None:
            msg_set = await backend.find_changed_uids(self._changed_since)  # type: ignore[misc]
        else:
            result = await backend.uid_search(self.compile_criteria())  # type: ignore[misc]
            if not result.success:
                return MessageSet.empty(mailbox=mailbox)
            msg_set = result.to_uid_message_set(mailbox=mailbox)
        return self._apply_pagination(msg_set)

    async def count_async(self) -> int:
        return len(_expand_uids(await self.uids_async()))

    async def iter_async(self):
        from sage_imap.orm.models.message import ImapMessage

        backend = self._require_backend()
        mailbox = self._resolve_mailbox(backend)
        uid_list = _expand_uids(await self.uids_async())
        msg_set = (
            MessageSet.from_uids(uid_list, mailbox=mailbox)
            if uid_list
            else MessageSet.empty(mailbox=mailbox)
        )
        level = self._load_level or LoadLevel.HEADERS
        if level == LoadLevel.IDENTITY:
            messages = [
                ImapMessage.from_uid(backend.account_id, mailbox, uid, backend=backend)
                for uid in uid_list
            ]
        else:
            messages = []
            async for msg in backend.fetch_messages(  # type: ignore[attr-defined]
                msg_set, load_level=level, batch_size=self._batch_size
            ):
                messages.append(msg)
        if self._order_by:
            messages = self._sort_messages(messages)
        for msg in messages:
            yield msg

    async def fetch_all_async(self) -> list["ImapMessage"]:
        return [m async for m in self.iter_async()]

    async def bulk_mark_seen_async(self) -> int:
        from sage_imap.orm.models.message import ImapMessage

        backend = self._require_backend()
        uids = _expand_uids(await self.uids_async())
        for uid in uids:
            msg = ImapMessage.from_uid(
                backend.account_id, self._resolve_mailbox(backend), uid, backend=backend
            )
            await backend.mark_seen(msg)  # type: ignore[misc]
        return len(uids)

    def _resolve_mailbox(self, backend: "ImapBackend") -> str:
        mailbox = self._mailbox or backend.mailbox
        if not mailbox:
            raise OrmMailboxNotSelectedError(
                "Select a mailbox before querying messages"
            )
        return mailbox

    def _apply_pagination(self, msg_set: MessageSet) -> MessageSet:
        ids = _expand_uids(msg_set)
        if self._cursor_after is not None:
            ids = [u for u in ids if u > self._cursor_after]
        if self._cursor_before is not None:
            ids = [u for u in ids if u < self._cursor_before]
        if self._offset:
            ids = ids[self._offset :]
        if self._limit is not None:
            ids = ids[: self._limit]
        if not ids:
            return MessageSet.empty(mailbox=msg_set.mailbox)
        return MessageSet.from_uids(ids, mailbox=msg_set.mailbox)

    def _sort_messages(self, messages: list["ImapMessage"]) -> list["ImapMessage"]:
        field = self._order_by or ""
        reverse = field.startswith("-")
        key_name = field.lstrip("-")
        if key_name in ("date", "-date"):
            return sorted(
                messages,
                key=lambda m: m.date or __import__("datetime").datetime.min,
                reverse=reverse,
            )
        if key_name in ("uid", "-uid"):
            return sorted(messages, key=lambda m: m.uid, reverse=reverse)
        if key_name in ("subject", "-subject"):
            return sorted(messages, key=lambda m: m.subject.lower(), reverse=reverse)
        return messages

    def _clone(self) -> "MessageQuerySet":
        qs = MessageQuerySet(
            self._backend,
            account_id=self._account_id,
            mailbox=self._mailbox,
        )
        qs._criteria_parts = list(self._criteria_parts)
        qs._raw = self._raw
        qs._limit = self._limit
        qs._offset = self._offset
        qs._cursor_after = self._cursor_after
        qs._cursor_before = self._cursor_before
        qs._load_level = self._load_level
        qs._order_by = self._order_by
        qs._changed_since = self._changed_since
        qs._batch_size = self._batch_size
        return qs
