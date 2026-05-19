"""Tests for BaseMailboxService."""

from unittest.mock import Mock

from sage_imap.helpers.enums import MailboxStatusItems
from sage_imap.services.mailbox.base import BaseMailboxService


def _service(transport=None):
    client = Mock()
    client.transport = transport or Mock()
    return BaseMailboxService(client)


class TestBaseMailboxService:
    def test_context_manager_closes(self):
        svc = _service()
        svc.close = Mock(return_value=Mock(success=True))
        with svc:
            pass
        svc.close.assert_called_once()

    def test_select_already_selected(self):
        svc = _service()
        svc.current_selection = "INBOX"
        result = svc.select("INBOX")
        assert result.success
        assert result.metadata.get("already_selected")

    def test_select_success(self):
        transport = Mock()
        transport.select.return_value = ("OK", [b"1"])
        svc = _service(transport)
        result = svc.select("INBOX")
        assert result.success
        assert svc.current_selection == "INBOX"

    def test_select_failure_status(self):
        transport = Mock()
        transport.select.return_value = ("NO", [])
        svc = _service(transport)
        result = svc.select("INBOX")
        assert not result.success

    def test_close_no_selection(self):
        svc = _service()
        svc.current_selection = None
        assert svc.close().success

    def test_close_success(self):
        transport = Mock()
        transport.close.return_value = ("OK", [])
        svc = _service(transport)
        svc.current_selection = "INBOX"
        result = svc.close()
        assert result.success
        assert svc.current_selection is None

    def test_close_bad_status(self):
        transport = Mock()
        transport.close.return_value = ("NO", [])
        svc = _service(transport)
        svc.current_selection = "INBOX"
        assert not svc.close().success

    def test_check_success_and_failure(self):
        transport = Mock()
        transport.check.return_value = ("OK", [])
        svc = _service(transport)
        assert svc.check().success

        transport.check.return_value = ("NO", [])
        assert not svc.check().success

    def test_status_success_and_failure(self):
        transport = Mock()
        transport.status.return_value = ("OK", [b"(MESSAGES 1)"])
        svc = _service(transport)
        result = svc.status("INBOX", MailboxStatusItems.MESSAGES)
        assert result.success

        transport.status.return_value = ("NO", [])
        assert not svc.status("INBOX", MailboxStatusItems.MESSAGES).success

    def test_get_monitoring_statistics(self):
        svc = _service()
        svc.select("INBOX")
        stats = svc.get_monitoring_statistics()
        assert "total_operations" in stats
