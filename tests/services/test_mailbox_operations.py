"""Unit tests for mailbox operations with mocked transport."""

from unittest.mock import Mock

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet
from sage_imap.services.client import IMAPClient
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService


def _client_with_transport():
    client = Mock(spec=IMAPClient)
    client.transport = Mock()
    return client


class TestMailboxSearch:
    def test_search_uses_charset(self):
        client = _client_with_transport()
        client.transport.search.return_value = ("OK", [b"1 2"])
        svc = IMAPMailboxService(client)
        svc.current_selection = "INBOX"
        result = svc.search(IMAPSearchCriteria.ALL, charset="UTF-8")
        assert result.success
        client.transport.search.assert_called_with(
            str(IMAPSearchCriteria.ALL), "UTF-8", use_uid=False
        )

    def test_uid_search(self):
        client = _client_with_transport()
        client.transport.search.return_value = ("OK", [b"100"])
        svc = IMAPMailboxUIDService(client)
        svc.current_selection = "INBOX"
        result = svc.uid_search(IMAPSearchCriteria.UNSEEN)
        assert result.success
        client.transport.search.assert_called_with(
            str(IMAPSearchCriteria.UNSEEN), None, use_uid=True
        )


class TestMailboxMove:
    def test_move_delegates_to_transport(self):
        client = _client_with_transport()
        client.transport.move.return_value = ("OK", {"method": "MOVE"})
        svc = IMAPMailboxService(client)
        svc.current_selection = "INBOX"
        svc.check = Mock(return_value=Mock(success=True))
        msg_set = MessageSet.from_sequence_numbers([1])
        result = svc.move(msg_set, "Archive")
        assert result.success
        client.transport.move.assert_called_once()
