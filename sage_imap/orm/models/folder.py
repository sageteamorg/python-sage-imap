"""Folder entity and manager."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    pass


@dataclass
class ImapFolder:
    account_id: str
    name: str
    delimiter: str = "/"
    attributes: list[str] = field(default_factory=list)
    selectable: bool = True
    message_count: Optional[int] = None
    unseen_count: Optional[int] = None
    _backend: Any = field(default=None, repr=False, compare=False)

    @classmethod
    def from_folder_info(
        cls, account_id: str, info: Any, *, backend: Any = None
    ) -> "ImapFolder":
        return cls(
            account_id=account_id,
            name=info.name,
            delimiter=getattr(info, "delimiter", "/") or "/",
            attributes=list(getattr(info, "attributes", None) or []),
            selectable=getattr(info, "selectable", True),
            message_count=getattr(info, "message_count", None),
            unseen_count=getattr(info, "unseen_count", None),
            _backend=backend,
        )


class FolderManager:
    def list(self, *, enrich: bool = False) -> list[ImapFolder]:
        from sage_imap.orm.managers import _active_orm

        orm = _active_orm.get()
        if orm is None or orm.backend is None:
            return []
        backend = orm.backend
        session = getattr(backend, "_session", None)
        if session is None:
            return []
        folders = session.folders.list_folders(enrich=enrich)
        return [
            ImapFolder.from_folder_info(orm.account_id, f, backend=backend)
            for f in folders
        ]

    def get(self, name: str, *, enrich: bool = True) -> Optional[ImapFolder]:
        from sage_imap.orm.managers import _active_orm

        orm = _active_orm.get()
        if orm is None:
            return None
        session = getattr(orm.backend, "_session", None)
        if session is None:
            return None
        info = session.folders.get_folder_info(name, enrich=enrich)
        return ImapFolder.from_folder_info(orm.account_id, info, backend=orm.backend)

    def trash(self) -> Optional[ImapFolder]:
        from sage_imap.helpers.special_use import SpecialUse
        from sage_imap.orm.managers import _active_orm

        orm = _active_orm.get()
        if orm is None:
            return None
        session = getattr(orm.backend, "_session", None)
        if session is None:
            return None
        name = session.special_folder(SpecialUse.TRASH)
        return self.get(name) if name else None


class _FolderManagerDescriptor:
    def __get__(self, obj: Any, owner: type) -> FolderManager:
        return FolderManager()


ImapFolder.objects = _FolderManagerDescriptor()  # type: ignore[attr-defined]
