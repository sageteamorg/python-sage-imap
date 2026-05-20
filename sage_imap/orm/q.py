"""Composable IMAP SEARCH filters (Q objects)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional, Union

from sage_imap.helpers.search import IMAPSearchCriteria


@dataclass
class Q:
    """
    Build IMAP SEARCH criteria with AND / OR / NOT composition.

    Keyword filters map to :class:`IMAPSearchCriteria` helpers.
    """

    connector: str = "AND"
    children: list[Union["Q", str]] = field(default_factory=list)
    negated: bool = False

    def __init__(
        self,
        *args: Union["Q", str],
        _connector: str = "AND",
        _negated: bool = False,
        **filters: Any,
    ) -> None:
        self.connector = _connector
        self.negated = _negated
        self.children = list(args)
        if filters:
            self.children.append(_filters_to_criteria(filters))

    def __and__(self, other: "Q") -> "Q":
        return Q(self, other, _connector="AND")

    def __or__(self, other: "Q") -> "Q":
        return Q(self, other, _connector="OR")

    def __invert__(self) -> "Q":
        return Q(*self.children, _connector=self.connector, _negated=not self.negated)

    def compile(self) -> str:
        if not self.children:
            return str(IMAPSearchCriteria.ALL)
        parts: list[str] = []
        for child in self.children:
            if isinstance(child, Q):
                parts.append(child.compile())
            else:
                parts.append(str(child))
        if len(parts) == 1:
            expr = parts[0]
        elif self.connector == "OR":
            expr = IMAPSearchCriteria.or_criteria(*parts)
        else:
            expr = IMAPSearchCriteria.and_criteria(*parts)
        if self.negated:
            return f"NOT {expr}"
        return expr


def _filters_to_criteria(filters: dict[str, Any]) -> str:
    parts: list[str] = []
    for key, value in filters.items():
        if value is None:
            continue
        part = _single_filter(key, value)
        if part:
            parts.append(part)
    if not parts:
        return str(IMAPSearchCriteria.ALL)
    if len(parts) == 1:
        return parts[0]
    return IMAPSearchCriteria.and_criteria(*parts)


def _single_filter(key: str, value: Any) -> Optional[str]:
    if key == "unread" and value:
        return str(IMAPSearchCriteria.UNSEEN)
    if key == "seen" and value:
        return str(IMAPSearchCriteria.SEEN)
    if key == "flagged" and value:
        return str(IMAPSearchCriteria.FLAGGED)
    if key == "answered" and value:
        return str(IMAPSearchCriteria.ANSWERED)
    if key == "deleted" and value:
        return str(IMAPSearchCriteria.DELETED)
    if key == "draft" and value:
        return str(IMAPSearchCriteria.DRAFT)
    if key == "from_address" and value:
        return IMAPSearchCriteria.from_address(str(value))
    if key == "to_address" and value:
        return IMAPSearchCriteria.to_address(str(value))
    if key == "subject" and value:
        return IMAPSearchCriteria.subject(str(value))
    if key == "body" and value:
        return IMAPSearchCriteria.body(str(value))
    if key == "text" and value:
        return IMAPSearchCriteria.text(str(value))
    if key == "since" and value:
        return IMAPSearchCriteria.since(str(value))
    if key == "before" and value:
        return IMAPSearchCriteria.before(str(value))
    if key == "on" and value:
        return IMAPSearchCriteria.on(str(value))
    if key == "recent_days" and value:
        return IMAPSearchCriteria.recent(int(value))
    if key == "uid" and value is not None:
        return IMAPSearchCriteria.uid(str(value))
    return None
