"""UID mailbox operation coverage tests."""

from unittest.mock import Mock

import pytest

from sage_imap.helpers.enums import MessagePart
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet
from sage_imap.services.mailbox import IMAPMailboxUIDService

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Hi
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <id@example.com>
Content-Type: text/plain

Body
"""
FLAG_LINE = b"1 (FLAGS (\\Seen) UID 100) {5}"


def _uid_svc():
    client = Mock()
    client.transport = Mock()
    client.append = Mock(return_value=("OK", []))
    svc = IMAPMailboxUIDService(client)
    svc.current_selection = "INBOX"
    return svc, client


class TestUIDMailboxOperations:
    def test_uid_search_exception(self):
        svc, client = _uid_svc()
        client.transport.search.side_effect = RuntimeError("fail")
        assert not svc.uid_search(IMAPSearchCriteria.ALL).success

    def test_uid_restore_success(self):
        svc, client = _uid_svc()
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {"copyuid": {"dest_uids": "101"}})
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.check.return_value = ("OK", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_uids([101], mailbox="INBOX")
        )
        msg_set = MessageSet.from_uids([100], mailbox="Trash")
        result = svc.uid_restore(msg_set, "Trash", "INBOX")
        assert result.success

    def test_uid_restore_store_flags_fail(self):
        svc, client = _uid_svc()
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})
        client.transport.store_flags.return_value = ("NO", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_uids([101])
        )
        msg_set = MessageSet.from_uids([100])
        result = svc.uid_restore(msg_set, "Trash", "INBOX")
        assert not result.success

    def test_uid_fetch(self):
        svc, client = _uid_svc()
        client.transport.fetch.return_value = ("OK", [(FLAG_LINE, SAMPLE_EML)])
        msg_set = MessageSet.from_uids([100], mailbox="INBOX")
        result = svc.uid_fetch(msg_set, MessagePart.RFC822)
        assert result.success

    def test_uid_fetch_failure(self):
        svc, client = _uid_svc()
        client.transport.fetch.return_value = ("NO", [])
        msg_set = MessageSet.from_uids([100], mailbox="INBOX")
        assert not svc.uid_fetch(msg_set, MessagePart.RFC822).success

    def test_uid_create_message_set_no_results(self):
        svc, client = _uid_svc()
        client.transport.search.return_value = ("OK", [b""])
        with pytest.raises(Exception):
            svc.create_message_set_from_search(IMAPSearchCriteria.ALL)

    def test_process_messages_in_batches(self):
        svc, client = _uid_svc()
        client.transport.fetch.return_value = ("OK", [(FLAG_LINE, SAMPLE_EML)])
        msg_set = MessageSet.from_uids([100, 101], mailbox="INBOX")
        processed = []

        def handler(email):
            processed.append(email)

        result = svc.process_messages_in_batches(
            msg_set, handler, batch_size=1, msg_part=MessagePart.RFC822
        )
        assert result.total_messages == 2

    def test_uid_trash_move_failures(self):
        svc, client = _uid_svc()
        client.transport.store_flags.return_value = ("NO", [])
        msg_set = MessageSet.from_uids([1])
        assert not svc.uid_trash(msg_set, "Trash").success
