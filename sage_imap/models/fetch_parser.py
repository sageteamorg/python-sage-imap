"""Parse IMAP FETCH responses into EmailMessage with configurable depth."""

from __future__ import annotations

import logging
import re
from typing import Any, Iterator, List, Optional

from sage_imap.helpers.parse_mode import ParseMode
from sage_imap.models.email import EmailMessage

logger = logging.getLogger(__name__)

_UID_FLAGS_RE = re.compile(
    rb"(\d+) \(UID (\d+) FLAGS \([^\)]*\)",
)
_SEQ_FLAGS_RE = re.compile(
    rb"(\d+) \(.*FLAGS \([^\)]*\)",
)


def _extract_metadata(
    flag_data: bytes, is_uid_fetch: bool
) -> tuple[Optional[int], Optional[int]]:
    if is_uid_fetch:
        match = _UID_FLAGS_RE.search(flag_data)
        if match:
            return int(match.group(1)), int(match.group(2))
    match = _SEQ_FLAGS_RE.search(flag_data)
    if match:
        return int(match.group(1)), None
    return None, None


def message_from_fetch_part(
    flag_data: bytes,
    msg_data: bytes,
    *,
    parse_mode: ParseMode = ParseMode.FULL,
    mailbox: Optional[str] = None,
    is_uid_fetch: bool = True,
) -> Optional[EmailMessage]:
    """Build an :class:`EmailMessage` from one FETCH tuple."""
    if not msg_data:
        return None

    if parse_mode == ParseMode.RAW:
        email_message = EmailMessage(message_id="", raw=msg_data)
        email_message.size = len(msg_data)
    else:
        email_message = EmailMessage(message_id="", raw=msg_data)
        email_message.parse_eml_content(mode=parse_mode)

    if isinstance(flag_data, bytes):
        email_message.flags = EmailMessage.extract_flags(flag_data)
        seq, uid = _extract_metadata(flag_data, is_uid_fetch)
        if seq is not None:
            email_message.sequence_number = seq
        if uid is not None:
            email_message.uid = uid

    email_message.size = len(msg_data)
    if mailbox:
        email_message.mailbox = mailbox
    return email_message


def iter_messages_from_fetch(
    fetch_data: List[Any],
    *,
    parse_mode: ParseMode = ParseMode.FULL,
    mailbox: Optional[str] = None,
    is_uid_fetch: bool = True,
) -> Iterator[EmailMessage]:
    """Yield :class:`EmailMessage` instances from an imaplib FETCH data list."""
    for response_part in fetch_data or []:
        if not isinstance(response_part, tuple) or len(response_part) != 2:
            continue
        flag_data, msg_data = response_part
        if not isinstance(msg_data, bytes) or not msg_data:
            continue
        try:
            message = message_from_fetch_part(
                flag_data if isinstance(flag_data, bytes) else b"",
                msg_data,
                parse_mode=parse_mode,
                mailbox=mailbox,
                is_uid_fetch=is_uid_fetch,
            )
            if message:
                yield message
        except Exception as e:
            logger.warning("Skipping malformed FETCH part: %s", e)
