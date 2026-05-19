"""RFC 6154 SPECIAL-USE folder attributes and RFC 2342 NAMESPACE parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from sage_imap.services.folder import FolderInfo  # pragma: no cover


class SpecialUse(StrEnum):
    """
    Standard IMAP SPECIAL-USE mailbox attributes (RFC 6154).

    Use with :meth:`IMAPFolderService.find_by_special_use` or
    :meth:`IMAPFolderService.get_special_folders`.
    """

    INBOX = "Inbox"
    SENT = "Sent"
    TRASH = "Trash"
    DRAFTS = "Drafts"
    JUNK = "Junk"
    ARCHIVE = "Archive"
    ALL = "All"
    FLAGGED = "Flagged"

    def imap_attribute(self) -> str:
        """Return the LIST attribute form (e.g. ``\\Sent``)."""
        return f"\\{self.value}"


@dataclass
class NamespaceInfo:
    """One IMAP namespace (personal, other users, or shared)."""

    prefix: str
    delimiter: str


@dataclass
class NamespaceMap:
    """Parsed NAMESPACE response."""

    personal: Optional[NamespaceInfo] = None
    other_users: List[NamespaceInfo] = field(default_factory=list)
    shared: List[NamespaceInfo] = field(default_factory=list)

    def primary_delimiter(self) -> str:
        if self.personal:
            return self.personal.delimiter
        return "/"


_NAMESPACE_TUPLE_RE = re.compile(r'\(\s*"([^"]*)"\s+"([^"]*)"\s*\)')


def parse_namespace_response(data: List[Any]) -> NamespaceMap:
    """
    Parse NAMESPACE response data into structured namespaces.

    Assigns the first (prefix, delimiter) tuple to personal, the second to
    other users, and any further tuples to shared — matching common server layouts.
    """
    result = NamespaceMap()
    if not data:
        return result

    raw = data[0]
    text = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else str(raw)
    if text.strip().upper() == "NIL":
        return result

    matches = _NAMESPACE_TUPLE_RE.findall(text)
    if not matches:
        return result

    result.personal = NamespaceInfo(prefix=matches[0][0], delimiter=matches[0][1])
    if len(matches) > 1:
        result.other_users.append(
            NamespaceInfo(prefix=matches[1][0], delimiter=matches[1][1])
        )
    for pair in matches[2:]:
        result.shared.append(NamespaceInfo(prefix=pair[0], delimiter=pair[1]))
    return result


def folder_matches_special_use(attributes: List[str], use: SpecialUse) -> bool:
    """Return True if folder LIST attributes include the SPECIAL-USE flag."""
    target = use.imap_attribute().lower()
    for attr in attributes:
        normalized = attr if attr.startswith("\\") else f"\\{attr}"
        if normalized.lower() == target.lower():
            return True
    return False


def build_special_folder_map(
    folders: List["FolderInfo"],
) -> Dict[SpecialUse, "FolderInfo"]:
    """Map SPECIAL-USE roles to folder info from a LIST result."""
    found: Dict[SpecialUse, FolderInfo] = {}
    for folder in folders:
        for use in SpecialUse:
            if use in found:
                continue
            if folder_matches_special_use(folder.attributes, use):
                found[use] = folder
    if SpecialUse.INBOX not in found:
        for folder in folders:
            if folder.name.upper() == "INBOX":
                found[SpecialUse.INBOX] = folder
                break
    return found
