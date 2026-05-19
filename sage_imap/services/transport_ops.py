"""Shared IMAP transport helpers (COPYUID parsing, UID sets) used by sync and async transports."""

from __future__ import annotations

import re
from typing import List, Optional

from sage_imap.protocols.imap_transport import IMAPResponse

_COPYUID_RE = re.compile(
    r"\[COPYUID\s+(\d+)\s+([\d:,]+)\s+([\d:,]+)\]",
    re.IGNORECASE,
)


def parse_copyuid(response: IMAPResponse) -> Optional[dict]:
    """Parse UIDPLUS COPYUID from an IMAP COPY/MOVE response."""
    _, data = response
    if not data:
        return None
    for item in data:
        if item is None:
            continue
        text = (
            item.decode("utf-8", errors="replace")
            if isinstance(item, bytes)
            else str(item)
        )
        match = _COPYUID_RE.search(text)
        if match:
            return {
                "uidvalidity": int(match.group(1)),
                "source_uids": match.group(2),
                "dest_uids": match.group(3),
            }
    return None


def expand_uid_set(uid_spec: str) -> List[int]:
    """Expand IMAP UID set syntax (e.g. ``1,3:5``) into a sorted unique list."""
    uids: List[int] = []
    for part in uid_spec.split(","):
        part = part.strip()
        if ":" in part:
            start_s, end_s = part.split(":", 1)
            start, end = int(start_s), int(end_s)
            uids.extend(range(start, end + 1))
        elif part.isdigit():
            uids.append(int(part))
    return sorted(set(uids))
