"""Extended tests for IMAPFolderService."""

from unittest.mock import Mock

import pytest

from sage_imap.exceptions import IMAPDefaultFolderError, IMAPFolderExistsError
from sage_imap.services.folder import FolderInfo, IMAPFolderService

LIST_LINE = b'(\\HasNoChildren) "/" "Projects"'


class TestIMAPFolderServiceExtended:
    def _service(self, mocker):
        client = mocker.Mock()
        return IMAPFolderService(client), client

    def test_validate_folder_name(self):
        svc = IMAPFolderService(Mock())
        assert svc._validate_folder_name(" OK ") == "OK"
        with pytest.raises(ValueError):
            svc._validate_folder_name("")
        with pytest.raises(ValueError):
            svc._validate_folder_name("bad|name")

    def test_parse_folder_list(self):
        svc = IMAPFolderService(Mock())
        folders = svc._parse_folder_list_response([LIST_LINE, b"garbage"])
        assert len(folders) == 1
        assert folders[0].name == "Projects"

    def test_create_folder_success(self, mocker):
        svc, client = self._service(mocker)
        client.create.return_value = ("OK", [])
        mocker.patch.object(svc, "folder_exists", return_value=False)
        result = svc.create_folder("Work")
        assert result.success

    def test_create_folder_exists(self, mocker):
        svc, client = self._service(mocker)
        mocker.patch.object(svc, "folder_exists", return_value=True)
        with pytest.raises(IMAPFolderExistsError):
            svc.create_folder("Work")

    def test_rename_and_delete(self, mocker):
        svc, client = self._service(mocker)
        client.rename.return_value = ("OK", [])
        client.delete.return_value = ("OK", [])
        exists = mocker.patch.object(svc, "folder_exists")
        exists.side_effect = lambda name: name in ("A", "Custom")
        info = FolderInfo(name="Custom", has_children=False)
        mocker.patch.object(svc, "get_folder_info", return_value=info)
        assert svc.rename_folder("A", "B").success
        assert svc.delete_folder("Custom").success

    def test_delete_default_folder(self, mocker):
        svc, _ = self._service(mocker)
        mocker.patch.object(svc, "folder_exists", return_value=True)
        with pytest.raises(IMAPDefaultFolderError):
            svc.delete_folder("INBOX")

    def test_list_folders_and_cache(self, mocker):
        svc, client = self._service(mocker)
        client.list.return_value = ("OK", [LIST_LINE])
        client.status.return_value = ("OK", [b"Projects (MESSAGES 1)"])
        folders = svc.list_folders()
        assert len(folders) >= 1
        svc._cache_expiry = None
        cached = svc.list_folders()
        assert len(cached) == len(folders)

    def test_get_folder_info_and_exists(self, mocker):
        svc, client = self._service(mocker)
        client.list.return_value = ("OK", [LIST_LINE])
        info = svc.get_folder_info("Projects")
        assert info.name == "Projects"
        assert svc.folder_exists("Projects") is True
        assert svc.folder_exists("Missing") is False

    def test_get_folder_hierarchy(self, mocker):
        svc, client = self._service(mocker)
        client.list.return_value = (
            "OK",
            [b'(\\HasNoChildren) "/" "A/B"', b'(\\HasNoChildren) "/" "A/C"'],
        )
        client.status.return_value = ("OK", [b"(MESSAGES 0)"])
        hierarchy = svc.get_folder_hierarchy()
        assert "A" in hierarchy

    def test_subscribe_unsubscribe_lsub(self, mocker):
        svc, client = self._service(mocker)
        client.subscribe.return_value = ("OK", [])
        client.unsubscribe.return_value = ("OK", [])
        client.lsub.return_value = ("OK", [LIST_LINE])
        mocker.patch.object(svc, "folder_exists", return_value=True)
        assert svc.subscribe_folder("Projects").success
        assert svc.unsubscribe_folder("Projects").success
        assert len(svc.list_subscribed_folders()) >= 1

    def test_get_folder_statistics_and_clear(self, mocker):
        svc, client = self._service(mocker)
        client.list.return_value = ("OK", [LIST_LINE])
        client.status.return_value = ("OK", [b"(MESSAGES 0)"])
        client.create.return_value = ("OK", [])
        mocker.patch.object(svc, "folder_exists", return_value=False)
        svc.create_folder("X")
        stats = svc.get_folder_statistics()
        assert "total_folders" in stats
        svc.clear_operation_history()
        svc._clear_cache()

    def test_folder_info_post_init(self):
        info = FolderInfo(name="X")
        assert info.attributes == []

    def test_copy_folder_structure(self, mocker):
        svc, client = self._service(mocker)
        client.list.return_value = (
            "OK",
            [b'(\\HasNoChildren) "/" "Parent/Child"'],
        )
        client.status.return_value = ("OK", [b"(MESSAGES 0)"])
        client.create.return_value = ("OK", [])
        mocker.patch.object(svc, "folder_exists", return_value=False)
        results = svc.copy_folder_structure("Parent", "NewParent")
        assert isinstance(results, list)

    def test_get_folder_quota_unsupported(self, mocker):
        svc, client = self._service(mocker)
        mocker.patch.object(svc, "folder_exists", return_value=True)
        client.getquota = mocker.Mock(side_effect=AttributeError("no quota"))
        assert svc.get_folder_quota("INBOX") is None
