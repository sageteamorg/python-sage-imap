"""Extended flag service tests."""

import pytest

from sage_imap.helpers.enums import Flag
from sage_imap.models.email import EmailIterator, EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService

SAMPLE_EML = b"""From: a@example.com
Subject: T
Message-ID: <id@example.com>
Content-Type: text/plain

Body
"""


class TestFlagServiceExtended:
    def _svc(self, mocker, mock_imap_connection, uid=True):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox_cls = IMAPMailboxUIDService if uid else IMAPMailboxService
        mailbox = mailbox_cls(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        return IMAPFlagService(mailbox)

    def test_validate_message_set_errors(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection)
        with pytest.raises(ValueError):
            svc._validate_message_set(MessageSet.from_uids([]))
        with pytest.raises(ValueError):
            svc._validate_message_set("bad")  # type: ignore[arg-type]

    def test_set_flags_failure(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection)
        mock_imap_connection.uid.return_value = ("NO", [b"err"])
        msg_set = MessageSet.from_uids([1])
        result = svc.set_flags(msg_set, [Flag.SEEN])
        assert not result.success

    def test_get_message_flags_fetch_fail(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection)
        svc.mailbox.client.fetch = mocker.Mock(return_value=("NO", []))
        assert svc.get_message_flags("1") == []

    def test_sync_flags_and_summary(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection)
        email = EmailMessage.read_from_eml_bytes(SAMPLE_EML)
        email.sequence_number = 1
        email.flags = [Flag.SEEN]
        svc.mailbox.client.fetch = mocker.Mock(
            return_value=("OK", [(b"1 (FLAGS (\\Seen))", b"")])
        )
        it = EmailIterator([email])
        synced = svc.sync_flags_with_emails(it)
        assert "1" in synced
        summary = svc.get_flag_summary(it)
        assert summary.get("\\Seen", 0) >= 0

    def test_statistics_after_operations(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection)
        msg_set = MessageSet.from_uids([1])
        svc.add_flag(msg_set, Flag.SEEN)
        stats = svc.get_operation_statistics()
        assert stats["total_operations"] >= 1
        svc.clear_operation_history()

    def test_non_uid_mailbox_warning(self, mocker, mock_imap_connection):
        svc = self._svc(mocker, mock_imap_connection, uid=False)
        msg_set = MessageSet.from_uids([1])
        svc.add_flag(msg_set, Flag.SEEN)
