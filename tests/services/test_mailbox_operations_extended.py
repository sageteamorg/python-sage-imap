"""Extended mailbox operation tests with mocked transport."""

from unittest.mock import Mock

import pytest

from sage_imap.helpers.enums import Flag, MessagePart
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService

SAMPLE_EML = b"""From: a@example.com
To: b@example.com
Subject: Hi
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <id@example.com>
Content-Type: text/plain

Body
"""

FLAG_LINE = b"1 (FLAGS (\\Seen) UID 100) {5}"


def _svc(uid=False):
    client = Mock()
    client.transport = Mock()
    client.append = Mock(return_value=("OK", []))
    client.transport.append = client.append
    cls = IMAPMailboxUIDService if uid else IMAPMailboxService
    svc = cls(client)
    svc.current_selection = "INBOX"
    return svc, client


class TestMailboxOperationsExtended:
    def test_search_failure_and_exception(self):
        svc, client = _svc()
        client.transport.search.return_value = ("NO", [b"err"])
        assert not svc.search(IMAPSearchCriteria.ALL).success

        client.transport.search.side_effect = RuntimeError("boom")
        assert not svc.search(IMAPSearchCriteria.ALL).success

    def test_search_requires_selection(self):
        svc, _ = _svc()
        svc.current_selection = None
        with pytest.raises(Exception):
            svc.search(IMAPSearchCriteria.ALL)

    def test_create_message_set_from_search(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b"1 2"])
        msg_set = svc.create_message_set_from_search(IMAPSearchCriteria.ALL)
        assert not msg_set.is_uid

    def test_create_message_set_search_fails(self):
        svc, client = _svc()
        client.transport.search.return_value = ("NO", [])
        with pytest.raises(Exception):
            svc.create_message_set_from_search(IMAPSearchCriteria.ALL)

    def test_trash_and_delete(self):
        svc, client = _svc()
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {"method": "MOVE"})
        client.transport.check.return_value = ("OK", [])
        client.transport.expunge.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        assert svc.trash(msg_set, "Trash").success
        assert svc.delete(msg_set, "Trash").success

    def test_trash_move_fails(self):
        svc, client = _svc()
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.move.return_value = ("NO", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        assert not svc.trash(msg_set, "Trash").success

    def test_trash_store_fails(self):
        svc, client = _svc()
        client.transport.store_flags.return_value = ("NO", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        assert not svc.trash(msg_set, "Trash").success

    def test_move_failure(self):
        svc, client = _svc()
        client.transport.move.return_value = ("NO", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        assert not svc.move(msg_set, "Archive").success

    def test_fetch_success(self):
        svc, client = _svc()
        client.transport.fetch.return_value = (
            "OK",
            [(FLAG_LINE, SAMPLE_EML)],
        )
        msg_set = MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        result = svc.fetch(msg_set, MessagePart.RFC822)
        assert result.success
        assert result.metadata["processed_count"] >= 1

    def test_fetch_bad_status(self):
        svc, client = _svc()
        client.transport.fetch.return_value = ("NO", [])
        msg_set = MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        assert not svc.fetch(msg_set, MessagePart.RFC822).success

    def test_save_sent(self):
        svc, client = _svc()
        client.append.return_value = ("OK", [])
        assert svc.save_sent("Sent", SAMPLE_EML).success

    def test_save_sent_invalid_raw(self):
        svc, _ = _svc()
        assert not svc.save_sent("Sent", 123).success  # type: ignore[arg-type]

    def test_upload_eml(self):
        svc, client = _svc()
        email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
        result = svc.upload_eml([email], Flag.SEEN, "INBOX")
        assert result.successful_messages == 1

    def test_bulk_move_and_delete(self):
        svc, client = _svc()
        client.transport.move.return_value = ("OK", {})
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.check.return_value = ("OK", [])
        client.transport.expunge.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        bulk = svc.bulk_move([(msg_set, "Archive")])
        assert bulk.successful_messages == 1
        bulk_del = svc.bulk_delete([(msg_set, "Trash")])
        assert bulk_del.total_messages == 1

    def test_get_mailbox_statistics(self):
        svc, client = _svc()
        client.transport.status.return_value = (
            "OK",
            [b"INBOX (MESSAGES 5 RECENT 1 UNSEEN 2)"],
        )
        stats = svc.get_mailbox_statistics("INBOX")
        assert stats.total_messages == 5

    def test_get_mailbox_statistics_no_mailbox(self):
        svc, _ = _svc()
        svc.current_selection = None
        with pytest.raises(Exception):
            svc.get_mailbox_statistics()

    def test_save_sent_failure(self):
        svc, client = _svc()
        client.append = Mock(return_value=("NO", []))
        svc.client = client
        assert not svc.save_sent("Sent", SAMPLE_EML).success

    def test_upload_eml_partial_failure(self):
        svc, client = _svc()
        email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
        client.append = Mock(return_value=("NO", []))
        client.transport.append = client.append
        result = svc.upload_eml([email], Flag.SEEN, "INBOX")
        assert result.failed_messages == 1

    def test_search_and_process_no_results(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b""])
        result = svc.search_and_process(IMAPSearchCriteria.ALL, lambda e: None)
        assert result.total_messages == 0

    def test_search_and_process(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b"1"])
        client.transport.fetch.return_value = (
            "OK",
            [(FLAG_LINE, SAMPLE_EML)],
        )
        processed = []

        def proc(email):
            processed.append(email)

        result = svc.search_and_process(IMAPSearchCriteria.ALL, proc, batch_size=10)
        assert result.successful_messages >= 1

    def test_restore_select_trash_fails(self):
        svc, client = _svc()
        client.transport.select.return_value = ("NO", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert not result.success

    def test_restore_move_fails(self):
        svc, client = _svc()
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("NO", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert not result.success

    def test_restore_success(self):
        svc, client = _svc()
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = (
            "OK",
            {"method": "MOVE", "copyuid": {"dest_uids": "10"}},
        )
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.check.return_value = ("OK", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_uids([10], mailbox="INBOX")
        )
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.current_selection = "INBOX"
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert result.success

    def test_uid_search_failure(self):
        svc, client = _svc(uid=True)
        client.transport.search.return_value = ("NO", [])
        assert not svc.uid_search(IMAPSearchCriteria.ALL).success

    def test_uid_create_message_set(self):
        svc, client = _svc(uid=True)
        client.transport.search.return_value = ("OK", [b"100"])
        msg_set = svc.create_message_set_from_search(IMAPSearchCriteria.ALL)
        assert msg_set.is_uid

    def test_uid_move_trash_delete(self):
        svc, client = _svc(uid=True)
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})
        client.transport.check.return_value = ("OK", [])
        client.transport.expunge.return_value = ("OK", [])
        msg_set = MessageSet.from_uids([100])
        assert svc.uid_trash(msg_set, "Trash").success
        assert svc.uid_delete(msg_set, "Trash").success
        assert svc.uid_move(msg_set, "Archive").success
