"""Tests for mailbox validators and models."""

import pytest

from sage_imap.exceptions import IMAPMailboxSelectionError
from sage_imap.models.message import MessageSet
from sage_imap.services.mailbox.models import MailboxValidator


class TestMailboxValidator:
    def test_validate_mailbox_allows_slash(self):
        MailboxValidator.validate_mailbox("Projects/Work")

    def test_validate_mailbox_rejects_dotdot(self):
        with pytest.raises(IMAPMailboxSelectionError):
            MailboxValidator.validate_mailbox("..")

    def test_validate_message_set_requires_instance(self):
        with pytest.raises(Exception):
            MailboxValidator.validate_message_set("not-a-set")  # type: ignore[arg-type]

    def test_validate_message_set_empty(self):
        with pytest.raises(Exception):
            MailboxValidator.validate_message_set(MessageSet.from_uids([]))

    def test_validate_email_data(self):
        from sage_imap.models.email import EmailIterator

        MailboxValidator.validate_email_data(EmailIterator([]))
        with pytest.raises(Exception):
            MailboxValidator.validate_email_data("bad")  # type: ignore[arg-type]


def test_bulk_operation_result_properties():
    from sage_imap.services.mailbox.models import BulkOperationResult

    bulk = BulkOperationResult(
        operation="x",
        total_messages=10,
        successful_messages=10,
        failed_messages=0,
        execution_time=0.1,
        batch_size=5,
        batches_processed=2,
    )
    assert bulk.success_rate == 100.0
    assert bulk.is_successful

    empty = BulkOperationResult(
        operation="x",
        total_messages=0,
        successful_messages=0,
        failed_messages=0,
        execution_time=0.0,
        batch_size=1,
        batches_processed=0,
    )
    assert empty.success_rate == 0.0


def test_mailbox_monitor_trims_history():
    from sage_imap.services.mailbox.models import MailboxMonitor

    mon = MailboxMonitor()
    for _ in range(105):
        mon.record_operation("op", 0.01)
    assert len(mon.last_operations) <= 100
