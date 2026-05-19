"""Tests for shared sync/CONDSTORE helpers."""

from unittest.mock import Mock

from sage_imap.sync.ops import (
    find_changed_uids_via_transport,
    uids_from_search_response,
)
from sage_imap.sync.state import MailboxSyncState


class TestSyncOps:
    def test_uids_from_search_response(self):
        assert uids_from_search_response([b"1 2 3"]) == [1, 2, 3]

    def test_find_changed_no_modseq(self):
        transport = Mock()
        empty = find_changed_uids_via_transport(
            transport, MailboxSyncState(mailbox="INBOX")
        )
        assert empty.is_empty()
        transport.search.assert_not_called()

    def test_find_changed_no_condstore(self):
        transport = Mock()
        transport.has_capability.return_value = False
        empty = find_changed_uids_via_transport(
            transport, MailboxSyncState(mailbox="INBOX", highest_modseq=5)
        )
        assert empty.is_empty()

    def test_find_changed_uids(self):
        transport = Mock()
        transport.has_capability.return_value = True
        transport.search.return_value = ("OK", [b"10 11"])
        changed = find_changed_uids_via_transport(
            transport, MailboxSyncState(mailbox="INBOX", highest_modseq=5)
        )
        assert changed.msg_ids == "10:11"
