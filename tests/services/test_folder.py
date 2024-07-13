import pytest
from unittest.mock import Mock
from sage_imap.exceptions import (
    IMAPFolderExistsError,
    IMAPFolderNotFoundError,
    IMAPFolderOperationError,
    IMAPUnexpectedError,
)
from sage_imap.helpers.mailbox import DefaultMailboxes
from sage_imap.services.client import IMAPClient
from sage_imap.services.folder import IMAPFolderService

@pytest.fixture
def mock_client():
    client = Mock(spec=IMAPClient)
    client.create = Mock()
    client.rename = Mock()
    client.delete = Mock()
    client.list = Mock()
    return client

@pytest.fixture
def folder_service(mock_client):
    return IMAPFolderService(mock_client)

def test_create_folder_success(folder_service, mock_client):
    mock_client.create.return_value = ("OK", [b""])
    folder_service.create_folder("TestFolder")
    mock_client.create.assert_called_once_with("TestFolder")

def test_create_folder_exists(folder_service, mock_client):
    mock_client.create.return_value = ("NO", [b"ALREADYEXISTS"])
    with pytest.raises(IMAPFolderExistsError):
        folder_service.create_folder("ExistingFolder")
    mock_client.create.assert_called_once_with("ExistingFolder")

def test_create_folder_operation_error(folder_service, mock_client):
    mock_client.create.return_value = ("NO", [b"Some error"])
    with pytest.raises(IMAPFolderOperationError):
        folder_service.create_folder("ErrorFolder")
    mock_client.create.assert_called_once_with("ErrorFolder")

def test_create_folder_exception(folder_service, mock_client):
    mock_client.create.side_effect = Exception("Unexpected error")
    with pytest.raises(IMAPFolderOperationError):
        folder_service.create_folder("ExceptionFolder")
    mock_client.create.assert_called_once_with("ExceptionFolder")

def test_rename_folder_success(folder_service, mock_client):
    mock_client.rename.return_value = ("OK", [b""])
    folder_service.rename_folder("OldFolder", "NewFolder")
    mock_client.rename.assert_called_once_with("OldFolder", "NewFolder")

def test_rename_folder_not_found(folder_service, mock_client):
    mock_client.rename.return_value = ("NO", [b"NONEXISTENT"])
    with pytest.raises(IMAPFolderNotFoundError):
        folder_service.rename_folder("NonExistentFolder", "NewFolder")
    mock_client.rename.assert_called_once_with("NonExistentFolder", "NewFolder")

def test_rename_folder_operation_error(folder_service, mock_client):
    mock_client.rename.return_value = ("NO", [b"Some error"])
    with pytest.raises(IMAPFolderOperationError):
        folder_service.rename_folder("OldFolder", "ErrorFolder")
    mock_client.rename.assert_called_once_with("OldFolder", "ErrorFolder")

def test_rename_folder_exception(folder_service, mock_client):
    mock_client.rename.side_effect = Exception("Unexpected error")
    with pytest.raises(IMAPFolderOperationError):
        folder_service.rename_folder("OldFolder", "ExceptionFolder")
    mock_client.rename.assert_called_once_with("OldFolder", "ExceptionFolder")

def test_delete_folder_success(folder_service, mock_client):
    mock_client.delete.return_value = ("OK", [b""])
    folder_service.delete_folder("TestFolder")
    mock_client.delete.assert_called_once_with("TestFolder")

def test_delete_folder_not_found(folder_service, mock_client):
    mock_client.delete.return_value = ("NO", [b"NONEXISTENT"])
    with pytest.raises(IMAPFolderNotFoundError):
        folder_service.delete_folder("NonExistentFolder")
    mock_client.delete.assert_called_once_with("NonExistentFolder")

def test_delete_folder_operation_error(folder_service, mock_client):
    mock_client.delete.return_value = ("NO", [b"Some error"])
    with pytest.raises(IMAPFolderOperationError):
        folder_service.delete_folder("ErrorFolder")
    mock_client.delete.assert_called_once_with("ErrorFolder")

def test_delete_folder_exception(folder_service, mock_client):
    mock_client.delete.side_effect = Exception("Unexpected error")
    with pytest.raises(IMAPFolderOperationError):
        folder_service.delete_folder("ExceptionFolder")
    mock_client.delete.assert_called_once_with("ExceptionFolder")

def test_delete_default_folder(folder_service):
    with pytest.raises(IMAPUnexpectedError):
        folder_service.delete_folder(DefaultMailboxes.INBOX.value)

def test_list_folders_success(folder_service, mock_client):
    mock_client.list.return_value = ("OK", [b'(\\HasNoChildren) "/" INBOX', b'(\\HasNoChildren) "/" Sent'])
    folders = folder_service.list_folders()
    assert folders == ["INBOX", "Sent"]
    mock_client.list.assert_called_once()

def test_list_folders_operation_error(folder_service, mock_client):
    mock_client.list.return_value = ("NO", [b"Some error"])
    with pytest.raises(IMAPFolderOperationError):
        folder_service.list_folders()
    mock_client.list.assert_called_once()

def test_list_folders_exception(folder_service, mock_client):
    mock_client.list.side_effect = Exception("Unexpected error")
    with pytest.raises(IMAPFolderOperationError):
        folder_service.list_folders()
    mock_client.list.assert_called_once()
