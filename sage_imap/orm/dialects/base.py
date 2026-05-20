"""Server dialect hints for LIST/SEARCH compatibility."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ImapDialect:
    """Per-server behavior overrides."""

    name: str = "default"
    list_reference: str = '""'
    search_charset_default: Optional[str] = None
    prefer_uid_move: bool = True


DEFAULT_DIALECT = ImapDialect()

DIALECTS: dict[str, ImapDialect] = {
    "default": DEFAULT_DIALECT,
    "dovecot": ImapDialect(name="dovecot", search_charset_default=None),
    "gmail": ImapDialect(name="gmail"),
    "exchange": ImapDialect(name="exchange"),
}


def resolve_dialect(name: Optional[str]) -> ImapDialect:
    if not name:
        return DEFAULT_DIALECT
    return DIALECTS.get(name.lower(), DEFAULT_DIALECT)
