# test_imap_errors.py
import pytest

from sage_imap.exceptions import (
    IMAPAuthenticationError,
    IMAPClientError,
    IMAPConfigurationError,
    IMAPConnectionError,
    IMAPDefaultFolderError,
    IMAPFlagError,
    IMAPFlagOperationError,
    IMAPFolderError,
    IMAPFolderExistsError,
    IMAPFolderNotFoundError,
    IMAPFolderOperationError,
    IMAPMailboxCheckError,
    IMAPMailboxClosureError,
    IMAPMailboxDeleteError,
    IMAPMailboxError,
    IMAPMailboxFetchError,
    IMAPMailboxMoveError,
    IMAPMailboxPermanentDeleteError,
    IMAPMailboxSaveSentError,
    IMAPMailboxSelectionError,
    IMAPMailboxStatusError,
    IMAPSearchError,
    IMAPUnexpectedError,
)


def test_imap_client_error_default():
    error = IMAPClientError()
    assert error.detail == "A server error occurred."
    assert error.code == "error"
    assert error.status_code == 500
    assert str(error) == "A server error occurred. (Code: error, Status Code: 500)"


def test_imap_client_error_custom():
    error = IMAPClientError(detail="Custom error", code="custom_error", status_code=400)
    assert error.detail == "Custom error"
    assert error.code == "custom_error"
    assert error.status_code == 400
    assert str(error) == "Custom error (Code: custom_error, Status Code: 400)"


def test_imap_configuration_error():
    error = IMAPConfigurationError()
    assert error.detail == "Invalid IMAP configuration."
    assert error.code == "configuration_error"
    assert error.status_code == 400


def test_imap_connection_error():
    error = IMAPConnectionError()
    assert error.detail == "Failed to connect to IMAP server."
    assert error.code == "connection_error"
    assert error.status_code == 502


def test_imap_authentication_error():
    error = IMAPAuthenticationError()
    assert error.detail == "Failed to authenticate with IMAP server."
    assert error.code == "authentication_error"
    assert error.status_code == 401


def test_imap_folder_error():
    error = IMAPFolderError()
    assert error.detail == "A folder-related error occurred."
    assert error.code == "folder_error"
    assert error.status_code == 500


def test_imap_folder_operation_error():
    error = IMAPFolderOperationError()
    assert error.detail == "Failed to perform folder operation."
    assert error.code == "folder_operation_error"
    assert error.status_code == 500


def test_imap_folder_not_found_error():
    error = IMAPFolderNotFoundError()
    assert error.detail == "Folder not found."
    assert error.code == "folder_not_found_error"
    assert error.status_code == 404


def test_imap_folder_exists_error():
    error = IMAPFolderExistsError()
    assert error.detail == "Folder already exists."
    assert error.code == "folder_exists_error"
    assert error.status_code == 409


def test_imap_default_folder_error():
    error = IMAPDefaultFolderError()
    assert error.detail == "Operation not allowed on default folder."
    assert error.code == "default_folder_error"
    assert error.status_code == 403


def test_imap_unexpected_error():
    error = IMAPUnexpectedError()
    assert error.detail == "An unexpected error occurred with the IMAP server."
    assert error.code == "unexpected_error"
    assert error.status_code == 500


def test_imap_flag_error():
    error = IMAPFlagError()
    assert error.detail == "A flag-related error occurred."
    assert error.code == "flag_error"
    assert error.status_code == 500


def test_imap_flag_operation_error():
    error = IMAPFlagOperationError()
    assert error.detail == "Failed to perform flag operation."
    assert error.code == "flag_operation_error"
    assert error.status_code == 500


def test_imap_mailbox_error():
    error = IMAPMailboxError()
    assert error.detail == "A mailbox-related error occurred."
    assert error.code == "mailbox_error"
    assert error.status_code == 500


def test_imap_mailbox_selection_error():
    error = IMAPMailboxSelectionError()
    assert error.detail == "Failed to select mailbox."
    assert error.code == "mailbox_selection_error"
    assert error.status_code == 500


def test_imap_mailbox_closure_error():
    error = IMAPMailboxClosureError()
    assert error.detail == "Failed to close mailbox."
    assert error.code == "mailbox_closure_error"
    assert error.status_code == 500


def test_imap_mailbox_check_error():
    error = IMAPMailboxCheckError()
    assert error.detail == "Failed to perform mailbox check."
    assert error.code == "mailbox_check_error"
    assert error.status_code == 500


def test_imap_mailbox_delete_error():
    error = IMAPMailboxDeleteError()
    assert error.detail == "Failed to delete email."
    assert error.code == "delete_error"
    assert error.status_code == 500


def test_imap_mailbox_permanent_delete_error():
    error = IMAPMailboxPermanentDeleteError()
    assert error.detail == "Failed to permanently delete email."
    assert error.code == "permanent_delete_error"
    assert error.status_code == 500


def test_imap_mailbox_move_error():
    error = IMAPMailboxMoveError()
    assert error.detail == "Failed to move email."
    assert error.code == "move_error"
    assert error.status_code == 500


def test_imap_search_error():
    error = IMAPSearchError()
    assert error.detail == "Failed to search emails."
    assert error.code == "search_error"
    assert error.status_code == 500


def test_imap_mailbox_save_sent_error():
    error = IMAPMailboxSaveSentError()
    assert error.detail == "Failed to save sent email."
    assert error.code == "save_sent_error"
    assert error.status_code == 500


def test_imap_mailbox_status_error():
    error = IMAPMailboxStatusError()
    assert error.detail == "Failed to get mailbox status."
    assert error.code == "status_error"
    assert error.status_code == 500


def test_imap_mailbox_fetch_error():
    error = IMAPMailboxFetchError()
    assert error.detail == "Failed to fetch email messages."
    assert error.code == "fetch_error"
    assert error.status_code == 500


if __name__ == "__main__":
    pytest.main()
