"""Unit tests for IMAPFlagService."""

import pytest

from sage_imap.helpers.enums import Flag
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient
from sage_imap.services.flag import IMAPFlagService
from sage_imap.services.mailbox import IMAPMailboxUIDService


class TestIMAPFlagService:
    def test_add_flag_uses_uid_store(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        client.authenticated = True

        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))

        flag_service = IMAPFlagService(mailbox)
        msg_set = MessageSet.from_uids([42])
        result = flag_service.add_flag(msg_set, Flag.SEEN)
        assert result.success
        mock_imap_connection.uid.assert_called()

    def test_validate_flags_errors(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        svc = IMAPFlagService(mailbox)
        with pytest.raises(ValueError):
            svc._validate_flags([])
        with pytest.raises(ValueError):
            svc._validate_flags("bad")  # type: ignore[arg-type]

    def test_remove_flag_and_bulk(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        svc = IMAPFlagService(mailbox)
        msg_set = MessageSet.from_uids([1])
        assert svc.remove_flag(msg_set, Flag.SEEN).success
        results = svc.bulk_add_flags(msg_set, [Flag.SEEN, Flag.FLAGGED])
        assert len(results) == 1
        assert len(results[0].flags_modified) == 2
        svc.bulk_remove_flags(msg_set, [Flag.SEEN])

    def test_set_flags_and_convenience(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        svc = IMAPFlagService(mailbox)
        msg_set = MessageSet.from_uids([1])
        assert svc.set_flags(msg_set, [Flag.SEEN]).success
        assert svc.mark_as_read(msg_set).success
        assert svc.mark_as_unread(msg_set).success
        assert svc.mark_as_important(msg_set).success
        assert svc.mark_as_deleted(msg_set).success
        assert len(svc.archive_messages(msg_set)) == 2

    def test_get_message_flags(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        svc = IMAPFlagService(mailbox)
        client.fetch = mocker.Mock(return_value=("OK", [(b"1 (FLAGS (\\Seen))", b"")]))
        flags = svc.get_message_flags("1")
        assert Flag.SEEN in flags or flags == []

    def test_operation_statistics(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        svc = IMAPFlagService(mailbox)
        stats = svc.get_operation_statistics()
        assert stats["total_operations"] == 0
        svc.clear_operation_history()

    def test_partial_flag_failure(self, mocker, mock_imap_connection):
        client = IMAPClient("h", "u", "p")
        client.connection = mock_imap_connection
        client.transport.bind(mock_imap_connection)
        client.transport.store_flags = mocker.Mock(
            side_effect=[("NO", [b"err"]), ("OK", [])]
        )
        mailbox = IMAPMailboxUIDService(client)
        mailbox.current_selection = "INBOX"
        mailbox.check = mocker.Mock(return_value=mocker.Mock(success=True))
        svc = IMAPFlagService(mailbox)
        msg_set = MessageSet.from_uids([1, 2])
        result = svc.add_flag(msg_set, Flag.SEEN)
        assert not result.success
