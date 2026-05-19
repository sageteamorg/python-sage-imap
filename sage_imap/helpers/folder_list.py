"""Parse IMAP LIST responses into :class:`~sage_imap.services.folder.FolderInfo`."""

from __future__ import annotations

import logging
import re
from typing import Any, List

logger = logging.getLogger(__name__)


def parse_folder_attributes(attributes_str: str) -> List[str]:
    """Parse LIST attribute string into normalized attribute tokens."""
    if not attributes_str:
        return []
    attributes_str = attributes_str.strip("()")
    if not attributes_str:
        return []
    return [attr.strip("\\") for attr in attributes_str.split()]


def parse_folder_list_response(response: List[Any]) -> List[Any]:
    """
    Parse folder list response from IMAP LIST command.

    Parameters
    ----------
    response:
        Raw LIST response lines (bytes or str).
    """
    from sage_imap.models.folder import FolderInfo

    folders: List[FolderInfo] = []

    for item in response:
        if not item:
            continue

        try:
            folder_str = item.decode("utf-8") if isinstance(item, bytes) else str(item)
            match = re.match(r'\(([^)]*)\)\s+"([^"]*)"\s+"([^"]*)"', folder_str)
            if not match:
                match = re.match(r"\(([^)]*)\)\s+([^\s]+)\s+(.+)", folder_str)
                if not match:
                    logger.warning("Could not parse folder response: %s", folder_str)
                    continue

            attributes_str, delimiter, name = match.groups()
            attributes = parse_folder_attributes(attributes_str)

            folders.append(
                FolderInfo(
                    name=name,
                    delimiter=delimiter,
                    attributes=attributes,
                    exists=True,
                    selectable="\\Noselect" not in attributes,
                    has_children="\\HasChildren" in attributes,
                    has_no_children="\\HasNoChildren" in attributes,
                    marked="\\Marked" in attributes,
                    unmarked="\\Unmarked" in attributes,
                )
            )
        except Exception as e:
            logger.warning("Error parsing folder response %r: %s", item, e)
            continue

    return folders
