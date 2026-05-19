"""Unit tests for IMAPFolderService cache."""

from datetime import datetime, timedelta

from sage_imap.services.folder import IMAPFolderService


class TestIMAPFolderService:
    def test_cache_expiry_uses_timedelta(self, mocker):
        client = mocker.Mock()
        client.list = mocker.Mock(return_value=("OK", []))
        client.status = mocker.Mock(return_value=("OK", [b"INBOX (MESSAGES 0)"]))
        service = IMAPFolderService(client)
        before = datetime.now()
        service.list_folders()
        assert service._cache_expiry is not None
        assert service._cache_expiry > before + timedelta(seconds=200)
