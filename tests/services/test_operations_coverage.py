"""Targeted coverage tests for sage_imap.services.mailbox.operations."""

import builtins
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from sage_imap.exceptions import IMAPMailboxSelectionError
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
UID_FLAG_LINE = b"1 (UID 100 FLAGS (\\Seen)) {5}"


def _svc(uid=False):
    client = Mock()
    client.transport = Mock()
    client.append = Mock(return_value=("OK", []))
    client.transport.append = client.append
    cls = IMAPMailboxUIDService if uid else IMAPMailboxService
    svc = cls(client)
    svc.current_selection = "INBOX"
    return svc, client


class TestCreateMessageSetCoverage:
    def test_create_message_set_empty_results(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b""])
        with pytest.raises(Exception, match="No messages found"):
            svc.create_message_set_from_search(IMAPSearchCriteria.ALL)

    def test_uid_create_message_set_search_failure(self):
        svc, client = _svc(uid=True)
        client.transport.search.return_value = ("NO", [b"err"])
        with pytest.raises(Exception, match="UID search failed"):
            svc.create_message_set_from_search(IMAPSearchCriteria.ALL)


class TestTrashDeleteMoveRestoreExceptions:
    def test_trash_exception_handler(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.validator.validate_message_set = Mock(
            side_effect=RuntimeError("trash boom")
        )
        result = svc.trash(msg_set, "Trash")
        assert not result.success
        assert "trash boom" in result.error_message

    def test_delete_trash_failure(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.trash = Mock(return_value=Mock(success=False, error_message="trash failed"))
        result = svc.delete(msg_set, "Trash")
        assert not result.success
        assert "trash failed" in result.error_message

    def test_delete_exception_handler(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.validator.validate_mailbox = Mock(side_effect=ValueError("delete err"))
        result = svc.delete(msg_set, "Trash")
        assert not result.success

    def test_move_exception_handler(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.validator.validate_mailbox = Mock(side_effect=OSError("move err"))
        result = svc.move(msg_set, "Archive")
        assert not result.success

    def test_restore_safe_select_fails(self):
        svc, client = _svc()
        client.transport.select.side_effect = [("OK", []), ("NO", [])]
        client.transport.move.return_value = ("OK", {})
        client.transport.check.return_value = ("OK", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        )
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert not result.success
        assert "safe mailbox" in result.error_message

    def test_restore_store_flags_fails(self):
        svc, client = _svc()
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})
        client.transport.store_flags.return_value = ("NO", [])
        client.transport.check.return_value = ("OK", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        )
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert not result.success
        assert "deleted flag" in result.error_message

    def test_restore_exception_handler(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.validator.validate_mailbox = Mock(side_effect=RuntimeError("restore err"))
        result = svc.restore(msg_set, "Trash", "INBOX")
        assert not result.success


class TestFetchMalformedResponses:
    def test_fetch_skips_empty_and_malformed(self):
        svc, client = _svc()
        client.transport.fetch.return_value = (
            "OK",
            [
                (FLAG_LINE, b""),
                (FLAG_LINE, "not-bytes"),
                "not-a-tuple",
                (FLAG_LINE, SAMPLE_EML),
            ],
        )
        msg_set = MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        result = svc.fetch(msg_set, MessagePart.RFC822)
        assert result.success
        assert result.metadata["processed_count"] == 1

    def test_fetch_message_processing_exception(self):
        svc, client = _svc()
        client.transport.fetch.return_value = ("OK", [(FLAG_LINE, SAMPLE_EML)])
        msg_set = MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        with patch(
            "sage_imap.services.mailbox.operations.EmailMessage.read_from_eml_bytes",
            side_effect=ValueError("bad eml"),
        ):
            result = svc.fetch(msg_set, MessagePart.RFC822)
        assert result.success
        assert result.metadata["processed_count"] == 0


class TestUploadEmlCoverage:
    def test_upload_eml_invalid_email_types(self):
        svc, _ = _svc()
        svc.bulk_operation_batch_size = 1
        result = svc.upload_eml(
            [
                SimpleNamespace(subject="x"),
                EmailMessage.read_from_eml_bytes(SAMPLE_EML),
            ],
            Flag.SEEN,
            "INBOX",
        )
        assert result.failed_messages >= 1
        assert any("EmailMessage" in e for e in result.errors)

    def test_upload_eml_missing_date_raw(self):
        svc, _ = _svc()
        bad = SimpleNamespace(subject="no-date-raw")
        result = svc.upload_eml([bad], Flag.SEEN, "INBOX")  # type: ignore[list-item]
        assert result.failed_messages == 1

    def test_upload_eml_email_missing_date_or_raw_attrs(self):
        svc, _ = _svc()
        email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)

        real_hasattr = builtins.hasattr

        def hasattr_without_date_raw(obj, name):
            if isinstance(obj, EmailMessage) and name in ("date", "raw"):
                return False
            return real_hasattr(obj, name)

        with patch("builtins.hasattr", hasattr_without_date_raw):
            result = svc.upload_eml([email], Flag.SEEN, "INBOX")
        assert result.failed_messages == 1
        assert any("date" in e and "raw" in e for e in result.errors)

    def test_upload_eml_per_email_exception(self):
        svc, client = _svc()
        email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
        client.append.side_effect = RuntimeError("append failed")
        result = svc.upload_eml([email], Flag.SEEN, "INBOX")
        assert result.failed_messages == 1

    def test_upload_eml_batch_progress_logging(self):
        svc, _ = _svc()
        svc.bulk_operation_batch_size = 1
        emails = [EmailMessage.read_from_eml_bytes(SAMPLE_EML) for _ in range(10)]
        result = svc.upload_eml(emails, Flag.SEEN, "INBOX")
        assert result.successful_messages == 10
        assert result.batches_processed == 10

    def test_upload_eml_outer_exception(self):
        svc, _ = _svc()
        svc.validator.validate_email_data = Mock(side_effect=TypeError("bad data"))
        result = svc.upload_eml([], Flag.SEEN, "INBOX")
        assert result.failed_messages == 0
        assert result.errors == ["bad data"]


class TestBulkOperationsCoverage:
    def test_bulk_move_failure_and_exception(self):
        svc, client = _svc()
        client.transport.move.return_value = ("NO", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.bulk_move([(msg_set, "Archive")])
        assert result.failed_messages == 1

        svc.move = Mock(side_effect=RuntimeError("move boom"))
        result = svc.bulk_move([(msg_set, "Archive")])
        assert result.failed_messages == 1
        assert any("exception" in e for e in result.errors)

    def test_bulk_move_progress_and_outer_exception(self):
        svc, client = _svc()
        client.transport.move.return_value = ("OK", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        pairs = [(msg_set, "Archive") for _ in range(10)]
        result = svc.bulk_move(pairs)
        assert result.successful_messages == 10

        real_record = svc.monitor.record_operation
        bulk_move_records = [0]

        def selective_record(op, *args, **kwargs):
            if op == "bulk_move":
                bulk_move_records[0] += 1
                if bulk_move_records[0] == 1:
                    raise RuntimeError("bulk_move outer")
            return real_record(op, *args, **kwargs)

        with patch.object(
            svc.monitor, "record_operation", side_effect=selective_record
        ):
            result = svc.bulk_move([(msg_set, "Archive")])
        assert result.errors == ["bulk_move outer"]

    def test_bulk_delete_failure_and_exception(self):
        svc, _ = _svc()
        msg_set = MessageSet.from_sequence_numbers([1])
        svc.delete = Mock(return_value=Mock(success=False, error_message="del fail"))
        result = svc.bulk_delete([(msg_set, "Trash")])
        assert result.failed_messages == 1

        svc.delete = Mock(side_effect=RuntimeError("del boom"))
        result = svc.bulk_delete([(msg_set, "Trash")])
        assert any("exception" in e for e in result.errors)

    def test_bulk_delete_progress_and_outer_exception(self):
        svc, client = _svc()
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})
        client.transport.check.return_value = ("OK", [])
        client.transport.expunge.return_value = ("OK", [])
        msg_set = MessageSet.from_sequence_numbers([1])
        pairs = [(msg_set, "Trash") for _ in range(10)]
        result = svc.bulk_delete(pairs)
        assert result.successful_messages == 10

        real_record = svc.monitor.record_operation
        bulk_delete_records = [0]

        def selective_record(op, *args, **kwargs):
            if op == "bulk_delete":
                bulk_delete_records[0] += 1
                if bulk_delete_records[0] == 1:
                    raise RuntimeError("bulk_delete outer")
            return real_record(op, *args, **kwargs)

        with patch.object(
            svc.monitor, "record_operation", side_effect=selective_record
        ):
            result = svc.bulk_delete([(msg_set, "Trash")])
        assert result.errors == ["bulk_delete outer"]


class TestMailboxStatisticsCoverage:
    def test_get_mailbox_statistics_status_failure(self):
        svc, client = _svc()
        client.transport.status.return_value = ("NO", [])
        stats = svc.get_mailbox_statistics("INBOX")
        assert stats.total_messages == 0

    def test_get_mailbox_statistics_exception(self):
        svc, _ = _svc()
        svc.status = Mock(side_effect=RuntimeError("status boom"))
        stats = svc.get_mailbox_statistics("INBOX")
        assert stats.total_messages == 0

    def test_get_mailbox_statistics_no_mailbox_raises(self):
        svc, _ = _svc()
        svc.current_selection = None
        with pytest.raises(IMAPMailboxSelectionError):
            svc.get_mailbox_statistics()


class TestSearchAndProcessCoverage:
    def test_search_and_process_search_fails(self):
        svc, client = _svc()
        client.transport.search.return_value = ("NO", [b"err"])
        result = svc.search_and_process(IMAPSearchCriteria.ALL, lambda e: None)
        assert result.errors
        assert "Search failed" in result.errors[0]

    def test_search_and_process_fetch_batch_fails(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b"1"])
        client.transport.fetch.return_value = ("NO", [])
        result = svc.search_and_process(
            IMAPSearchCriteria.ALL, lambda e: None, batch_size=1
        )
        assert result.failed_messages >= 1

    def test_search_and_process_processor_and_batch_errors(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b"1 2"])
        client.transport.fetch.return_value = ("OK", [(FLAG_LINE, SAMPLE_EML)])

        def bad_processor(_email):
            raise ValueError("proc fail")

        result = svc.search_and_process(
            IMAPSearchCriteria.ALL, bad_processor, batch_size=1
        )
        assert result.failed_messages >= 1
        assert any("Processing failed" in e for e in result.errors)

    def test_search_and_process_batch_exception(self):
        svc, client = _svc()
        client.transport.search.return_value = ("OK", [b"1"])
        msg_set = MessageSet.from_sequence_numbers([1], mailbox="INBOX")
        svc.fetch = Mock(side_effect=RuntimeError("fetch boom"))
        with patch(
            "sage_imap.services.mailbox.operations.MessageSet.from_sequence_numbers",
            return_value=msg_set,
        ):
            result = svc.search_and_process(
                IMAPSearchCriteria.ALL, lambda e: None, batch_size=1
            )
        assert result.failed_messages >= 1
        assert any("processing failed" in e.lower() for e in result.errors)

    def test_search_and_process_progress_and_outer_exception(self):
        svc, client = _svc()
        ids = " ".join(str(i) for i in range(1, 11))
        client.transport.search.return_value = ("OK", [ids.encode()])
        client.transport.fetch.return_value = ("OK", [(FLAG_LINE, SAMPLE_EML)])
        result = svc.search_and_process(
            IMAPSearchCriteria.ALL, lambda e: None, batch_size=1
        )
        assert result.batches_processed == 10

        svc.search = Mock(side_effect=RuntimeError("outer"))
        result = svc.search_and_process(IMAPSearchCriteria.ALL, lambda e: None)
        assert result.errors == ["outer"]


class TestUIDOperationsCoverage:
    def test_uid_trash_move_failure(self):
        svc, client = _svc(uid=True)
        client.transport.store_flags.return_value = ("OK", [])
        client.transport.move.return_value = ("NO", {})
        msg_set = MessageSet.from_uids([100])
        result = svc.uid_trash(msg_set, "Trash")
        assert not result.success

    def test_uid_trash_exception_handler(self):
        svc, _ = _svc(uid=True)
        msg_set = MessageSet.from_uids([100])
        svc.validator.validate_message_set = Mock(side_effect=RuntimeError("uid trash"))
        result = svc.uid_trash(msg_set, "Trash")
        assert not result.success

    def test_uid_delete_trash_failure(self):
        svc, _ = _svc(uid=True)
        msg_set = MessageSet.from_uids([100])
        svc.uid_trash = Mock(return_value=Mock(success=False, error_message="fail"))
        result = svc.uid_delete(msg_set, "Trash")
        assert not result.success

    def test_uid_delete_exception_handler(self):
        svc, _ = _svc(uid=True)
        msg_set = MessageSet.from_uids([100])
        svc.validator.validate_mailbox = Mock(side_effect=ValueError("uid del"))
        result = svc.uid_delete(msg_set, "Trash")
        assert not result.success

    def test_uid_move_failure_and_exception(self):
        svc, client = _svc(uid=True)
        client.transport.move.return_value = ("NO", {})
        msg_set = MessageSet.from_uids([100])
        assert not svc.uid_move(msg_set, "Archive").success

        svc.validator.validate_mailbox = Mock(side_effect=OSError("uid move"))
        result = svc.uid_move(msg_set, "Archive")
        assert not result.success

    def test_uid_restore_select_trash_fails(self):
        svc, client = _svc(uid=True)
        client.transport.select.return_value = ("NO", [])
        msg_set = MessageSet.from_uids([100])
        assert not svc.uid_restore(msg_set, "Trash", "INBOX").success

    def test_uid_restore_move_fails(self):
        svc, client = _svc(uid=True)
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("NO", {})
        client.transport.check.return_value = ("OK", [])
        msg_set = MessageSet.from_uids([100])
        assert not svc.uid_restore(msg_set, "Trash", "INBOX").success

    def test_uid_restore_safe_select_fails(self):
        svc, client = _svc(uid=True)
        client.transport.check.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})

        def select_by_mailbox(mailbox):
            if mailbox == "Trash":
                return ("OK", [])
            return ("NO", [])

        client.transport.select.side_effect = select_by_mailbox
        msg_set = MessageSet.from_uids([100])
        result = svc.uid_restore(msg_set, "Trash", "INBOX")
        assert not result.success
        assert "safe mailbox" in result.error_message

    def test_uid_restore_store_flags_and_exception(self):
        svc, client = _svc(uid=True)
        client.transport.select.return_value = ("OK", [])
        client.transport.move.return_value = ("OK", {})
        client.transport.store_flags.return_value = ("NO", [])
        client.transport.resolve_uids_after_copy = Mock(
            return_value=MessageSet.from_uids([101], mailbox="INBOX")
        )
        msg_set = MessageSet.from_uids([100])
        result = svc.uid_restore(msg_set, "Trash", "INBOX")
        assert not result.success

        svc.validator.validate_mailbox = Mock(side_effect=RuntimeError("uid restore"))
        result = svc.uid_restore(msg_set, "Trash", "INBOX")
        assert not result.success

    def test_uid_fetch_malformed_and_processing_error(self):
        svc, client = _svc(uid=True)
        client.transport.fetch.return_value = (
            "OK",
            [
                (UID_FLAG_LINE, b""),
                "bad-response",
                (UID_FLAG_LINE, SAMPLE_EML),
            ],
        )
        msg_set = MessageSet.from_uids([100], mailbox="INBOX")
        result = svc.uid_fetch(msg_set, MessagePart.RFC822)
        assert result.success
        assert result.metadata["processed_count"] == 1

        client.transport.fetch.return_value = ("OK", [(UID_FLAG_LINE, SAMPLE_EML)])
        with patch(
            "sage_imap.services.mailbox.operations.EmailMessage.read_from_eml_bytes",
            side_effect=ValueError("uid bad eml"),
        ):
            result = svc.uid_fetch(msg_set, MessagePart.RFC822)
        assert result.metadata["processed_count"] == 0


class TestProcessMessagesInBatchesCoverage:
    def test_warnings_for_sequence_and_mailbox_mismatch(self):
        svc, client = _svc(uid=True)
        client.transport.fetch.return_value = ("OK", [(UID_FLAG_LINE, SAMPLE_EML)])
        seq_set = MessageSet.from_sequence_numbers([1, 2], mailbox="Other")
        svc.process_messages_in_batches(seq_set, lambda e: None, batch_size=1)

    def test_batch_fetch_failure(self):
        svc, client = _svc(uid=True)
        client.transport.fetch.return_value = ("NO", [])
        msg_set = MessageSet.from_uids([100, 101], mailbox="INBOX")
        result = svc.process_messages_in_batches(msg_set, lambda e: None, batch_size=1)
        assert result.failed_messages >= 2

    def test_processor_and_batch_exceptions(self):
        svc, client = _svc(uid=True)
        client.transport.fetch.return_value = ("OK", [(UID_FLAG_LINE, SAMPLE_EML)])
        msg_set = MessageSet.from_uids([100, 101], mailbox="INBOX")

        def bad(_email):
            raise RuntimeError("proc")

        result = svc.process_messages_in_batches(msg_set, bad, batch_size=1)
        assert result.failed_messages >= 2

        svc.uid_fetch = Mock(side_effect=RuntimeError("batch fail"))
        result = svc.process_messages_in_batches(msg_set, lambda e: None, batch_size=1)
        assert any("processing failed" in e.lower() for e in result.errors)

    def test_batch_progress_and_outer_exception(self):
        svc, client = _svc(uid=True)
        client.transport.fetch.return_value = ("OK", [(UID_FLAG_LINE, SAMPLE_EML)])
        uids = list(range(100, 110))
        msg_set = MessageSet.from_uids(uids, mailbox="INBOX")
        result = svc.process_messages_in_batches(msg_set, lambda e: None, batch_size=1)
        assert result.batches_processed == 10

        msg_set = MessageSet.from_uids([100], mailbox="INBOX")
        with patch.object(
            msg_set, "iter_batches", side_effect=RuntimeError("iter fail")
        ):
            result = svc.process_messages_in_batches(
                msg_set, lambda e: None, batch_size=1
            )
        assert any("Batch processing failed" in e for e in result.errors)
