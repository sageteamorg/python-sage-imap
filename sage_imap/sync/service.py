"""High-level incremental sync using CONDSTORE when available."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from sage_imap.helpers.enums import MailboxStatusItems
from sage_imap.models.message import MessageSet
from sage_imap.sync.condstore import (
    highest_modseq_from_fields,
    parse_select_sync_fields,
    parse_status_sync_fields,
)
from sage_imap.sync.ops import find_changed_uids_via_transport
from sage_imap.sync.state import MailboxSyncState

if TYPE_CHECKING:
    from sage_imap.services.mailbox import IMAPMailboxUIDService  # pragma: no cover

logger = logging.getLogger(__name__)

_CONDSTORE_STATUS = (
    MailboxStatusItems.MESSAGES,
    MailboxStatusItems.UIDVALIDITY,
    MailboxStatusItems.UIDNEXT,
    MailboxStatusItems.UNSEEN,
    MailboxStatusItems.HIGHESTMODSEQ,
)


class IMAPSyncService:
    """Capture and apply mailbox sync state for incremental updates."""

    def __init__(self, mailbox_service: "IMAPMailboxUIDService") -> None:
        self.mailbox = mailbox_service
        self.client = mailbox_service.client

    def supports_condstore(self) -> bool:
        return self.client.transport.has_capability("CONDSTORE")

    def capture_state(self, mailbox: str) -> MailboxSyncState:
        """
        Read UIDVALIDITY / UIDNEXT / HIGHESTMODSEQ for a mailbox via STATUS.

        Does not require the mailbox to be selected.
        """
        items = " ".join(_CONDSTORE_STATUS)
        status, response = self.client.transport.status(mailbox, f"({items})")
        state = MailboxSyncState(mailbox=mailbox)
        if status != "OK" or not response:
            logger.warning("STATUS failed for sync state on %s: %s", mailbox, status)
            return state

        raw = response[0]
        text = (
            raw.decode("utf-8", errors="replace")
            if isinstance(raw, bytes)
            else str(raw)
        )
        fields = parse_status_sync_fields(text)
        state.uidvalidity = fields.get("UIDVALIDITY")
        state.uidnext = fields.get("UIDNEXT")
        state.message_count = fields.get("MESSAGES")
        state.unseen_count = fields.get("UNSEEN")
        state.highest_modseq = highest_modseq_from_fields(fields)
        state.touch()
        return state

    def capture_state_from_selection(self, mailbox: str) -> MailboxSyncState:
        """Capture sync fields after SELECT (uses STATUS + SELECT response hints)."""
        state = self.capture_state(mailbox)
        try:
            status, data = self.client.transport.select(mailbox)
            if status == "OK" and data:
                fields = parse_select_sync_fields(list(data))
                state.uidvalidity = fields.get("UIDVALIDITY", state.uidvalidity)
                state.uidnext = fields.get("UIDNEXT", state.uidnext)
                modseq = highest_modseq_from_fields(fields)
                if modseq is not None:
                    state.highest_modseq = modseq
        except Exception as e:
            logger.debug("Could not parse SELECT sync fields: %s", e)
        state.touch()
        return state

    def find_changed_uids(
        self,
        previous: MailboxSyncState,
        *,
        charset: Optional[str] = None,
    ) -> MessageSet:
        """
        Return UIDs changed since ``previous.highest_modseq`` (CONDSTORE).

        If CONDSTORE is unavailable or no modseq is stored, returns an empty UID set.
        """
        return find_changed_uids_via_transport(
            self.client.transport, previous, charset=charset
        )

    def apply_after_sync(self, state: MailboxSyncState) -> MailboxSyncState:
        """Refresh MODSEQ and counts after processing changes."""
        return self.capture_state(state.mailbox)
