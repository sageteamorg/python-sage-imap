"""Folder metadata models (shared by sync and async folder services)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class FolderInfo:
    """Information about an IMAP folder."""

    name: str
    delimiter: str = "/"
    attributes: Optional[List[str]] = None
    exists: bool = True
    selectable: bool = True
    has_children: bool = False
    has_no_children: bool = False
    marked: bool = False
    unmarked: bool = False
    message_count: Optional[int] = None
    recent_count: Optional[int] = None
    unseen_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.attributes is None:
            self.attributes = []
