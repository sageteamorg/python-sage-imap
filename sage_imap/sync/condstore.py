"""CONDSTORE field parsing and CHANGEDSINCE helpers."""

from __future__ import annotations

import re
from typing import Dict, Optional

_STATUS_FIELD_RE = re.compile(
    r"(MESSAGES|UIDVALIDITY|UIDNEXT|UNSEEN|HIGHESTMODSEQ|MODSEQ)\s+(\d+)",
    re.IGNORECASE,
)


def parse_status_sync_fields(status_line: str) -> Dict[str, int]:
    """
    Parse STATUS response text into numeric sync fields.

    Example input: ``"INBOX (MESSAGES 42 UIDVALIDITY 1 UIDNEXT 99 HIGHESTMODSEQ 120)"``
    """
    fields: Dict[str, int] = {}
    for match in _STATUS_FIELD_RE.finditer(status_line):
        fields[match.group(1).upper()] = int(match.group(2))
    return fields


def parse_select_sync_fields(select_data: list) -> Dict[str, int]:
    """Parse untagged SELECT/EXAMINE data for UIDVALIDITY / UIDNEXT when present."""
    fields: Dict[str, int] = {}
    for item in select_data or []:
        if item is None:
            continue
        text = (
            item.decode("utf-8", errors="replace")
            if isinstance(item, bytes)
            else str(item)
        )
        parsed = parse_status_sync_fields(text)
        fields.update(parsed)
    return fields


def build_changedsince_criteria(modseq: int) -> str:
    """Build SEARCH criteria for messages changed after ``modseq`` (RFC 4551)."""
    return f"CHANGEDSINCE {modseq}"


def highest_modseq_from_fields(fields: Dict[str, int]) -> Optional[int]:
    """Prefer HIGHESTMODSEQ; fall back to MODSEQ if server returns that name."""
    return fields.get("HIGHESTMODSEQ") or fields.get("MODSEQ")
