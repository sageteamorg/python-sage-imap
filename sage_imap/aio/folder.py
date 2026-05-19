"""Async folder management service."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from sage_imap.aio.client import AsyncIMAPClient
from sage_imap.helpers.special_use import (
    NamespaceMap,
    SpecialUse,
    build_special_folder_map,
    parse_namespace_response,
)
from sage_imap.services.folder import (
    _STATUS_MESSAGES_RE,
    _STATUS_RECENT_RE,
    _STATUS_UNSEEN_RE,
    FolderInfo,
    IMAPFolderService,
)

logger = logging.getLogger(__name__)


class AsyncIMAPFolderService:
    """Async folder operations mirroring :class:`~sage_imap.services.folder.IMAPFolderService`."""

    def __init__(self, client: AsyncIMAPClient) -> None:
        self.client = client
        self._parser = IMAPFolderService.__new__(IMAPFolderService)
        self._folder_cache: Dict[str, List[FolderInfo]] = {}
        self._namespace_cache: Optional[NamespaceMap] = None
        self._special_folders_cache: Optional[Dict[SpecialUse, FolderInfo]] = None
        self._cache_expiry: Optional[datetime] = None
        self._cache_duration = 300

    async def list_folders(
        self,
        pattern: str = "*",
        reference: str = "",
        *,
        enrich: bool = False,
    ) -> List[FolderInfo]:
        cache_key = f"{reference}:{pattern}:enrich={enrich}"
        if (
            self._cache_expiry
            and datetime.now() < self._cache_expiry
            and cache_key in self._folder_cache
        ):
            return list(self._folder_cache[cache_key])

        status, response = await self.client.transport.list(reference, pattern)
        if status != "OK":
            logger.error("Failed to list folders: %s", response)
            return []

        folders = self._parser._parse_folder_list_response(response)
        if enrich:
            for folder in folders:
                if folder.selectable:
                    await self._apply_status_to_folder(folder)

        self._folder_cache[cache_key] = folders
        self._cache_expiry = datetime.now() + timedelta(seconds=self._cache_duration)
        return folders

    async def _apply_status_to_folder(self, folder: FolderInfo) -> None:
        status, response = await self.client.transport.status(
            folder.name, "(MESSAGES RECENT UNSEEN)"
        )
        if status != "OK" or not response:
            return
        status_str = response[0]
        if isinstance(status_str, bytes):
            status_str = status_str.decode("utf-8", errors="replace")
        messages_match = _STATUS_MESSAGES_RE.search(status_str)
        recent_match = _STATUS_RECENT_RE.search(status_str)
        unseen_match = _STATUS_UNSEEN_RE.search(status_str)
        if messages_match:
            folder.message_count = int(messages_match.group(1))
        if recent_match:
            folder.recent_count = int(recent_match.group(1))
        if unseen_match:
            folder.unseen_count = int(unseen_match.group(1))

    async def get_namespace(self, *, refresh: bool = False) -> NamespaceMap:
        if self._namespace_cache is not None and not refresh:
            return self._namespace_cache
        status, response = await self.client.transport.namespace()
        if status != "OK":
            return NamespaceMap()
        self._namespace_cache = parse_namespace_response(response)
        return self._namespace_cache

    async def get_special_folders(
        self, *, enrich: bool = False, refresh: bool = False
    ) -> Dict[SpecialUse, FolderInfo]:
        if self._special_folders_cache is not None and not refresh:
            return dict(self._special_folders_cache)
        folders = await self.list_folders(enrich=enrich)
        self._special_folders_cache = build_special_folder_map(folders)
        return dict(self._special_folders_cache)

    async def find_by_special_use(
        self, use: Union[SpecialUse, str], *, enrich: bool = False
    ) -> Optional[FolderInfo]:
        if isinstance(use, str):
            use = SpecialUse(use.replace("\\", ""))
        return (await self.get_special_folders(enrich=enrich)).get(use)
