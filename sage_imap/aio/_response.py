"""Normalize aioimaplib Response objects to imaplib-style (status, data) tuples."""

from __future__ import annotations

import re
from typing import Any, List, Tuple

# aioimaplib strips the leading "* " before appending FETCH lines to Command.lines.
_FETCH_HDR = re.compile(rb"^(?:\*\s+)?\d+ FETCH \(")


def response_to_imap(response: Any) -> Tuple[str, List[Any]]:
    """Convert aioimaplib ``Response`` to ``(status, data)`` like imaplib."""
    if response is None:
        return "NO", []
    if (
        isinstance(response, tuple)
        and len(response) == 2
        and isinstance(response[0], str)
    ):
        return response  # already normalized
    result = getattr(response, "result", "NO")
    lines = list(getattr(response, "lines", []) or [])
    return result, lines


def search_data_from_lines(lines: List[Any]) -> List[bytes]:
    """Extract UID/sequence list from SEARCH response lines."""
    for line in lines:
        if not isinstance(line, (bytes, bytearray)):
            continue
        text = bytes(line).decode("utf-8", errors="replace").strip()
        if not text:
            continue
        if "SEARCH" in text.upper():
            parts = text.split()
            idx = 0
            for i, part in enumerate(parts):
                if part == "*" or part.upper() in {"SEARCH", "UID"}:
                    idx = i + 1
            uids = " ".join(parts[idx:]).encode()
            return [uids] if uids else [b""]
        parts = text.split()
        if parts and all(part.isdigit() for part in parts):
            return [" ".join(parts).encode()]
    return [b""]


def fetch_lines_to_imaplib_data(lines: List[Any]) -> List[Any]:
    """
    Pair FETCH header lines with following literal bodies for :func:`iter_messages_from_fetch`.
    """
    data: List[Any] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if isinstance(line, (bytes, bytearray)) and _FETCH_HDR.match(bytes(line)):
            header = bytes(line)
            body = b""
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if isinstance(nxt, (bytes, bytearray)) and _FETCH_HDR.match(bytes(nxt)):
                    break
                if isinstance(nxt, (bytes, bytearray)) and not _FETCH_HDR.match(
                    bytes(nxt)
                ):
                    body = bytes(nxt)
                    j += 1
                    break
                j += 1
            if body:
                data.append((header, body))
            i = j
        else:
            i += 1
    return data
