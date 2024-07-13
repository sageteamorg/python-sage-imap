from typing import Optional


class IMAPClientError(Exception):
    """Base class for all IMAP client exceptions."""

    status_code: int = 500
    default_detail: str = "A server error occurred."
    default_code: str = "error"

    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if status_code is None:
            status_code = self.status_code
        self.detail: str = detail
        self.code: str = code
        self.status_code: int = status_code

    def __str__(self) -> str:
        return f"{self.detail} (Code: {self.code}, Status Code: {self.status_code})"


class IMAPConfigurationError(IMAPClientError):
    """Exception raised for configuration errors."""

    status_code = 400
    default_detail = "Invalid IMAP configuration."
    default_code = "configuration_error"


class IMAPConnectionError(IMAPClientError):
    """Exception raised for connection errors."""

    status_code = 502
    default_detail = "Failed to connect to IMAP server."
    default_code = "connection_error"


class IMAPAuthenticationError(IMAPClientError):
    """Exception raised for authentication errors."""

    status_code = 401
    default_detail = "Failed to authenticate with IMAP server."
    default_code = "authentication_error"


class IMAPFolderError(IMAPClientError):
    """Base class for IMAP folder errors."""

    status_code = 500
    default_detail = "A folder-related error occurred."
    default_code = "folder_error"


class IMAPFolderOperationError(IMAPFolderError):
    """Exception raised for general folder operation errors."""

    status_code = 500
    default_detail = "Failed to perform folder operation."
    default_code = "folder_operation_error"


class IMAPFolderNotFoundError(IMAPFolderError):
    """Exception raised when a folder is not found."""

    status_code = 404
    default_detail = "Folder not found."
    default_code = "folder_not_found_error"


class IMAPFolderExistsError(IMAPFolderError):
    """Exception raised when a folder already exists."""

    status_code = 409
    default_detail = "Folder already exists."
    default_code = "folder_exists_error"


class IMAPDefaultFolderError(IMAPFolderError):
    """Exception raised when trying to perform an operation on a default folder."""

    status_code = 403
    default_detail = "Operation not allowed on default folder."
    default_code = "default_folder_error"


class IMAPUnexpectedError(IMAPClientError):
    """Exception raised for unexpected IMAP errors."""

    status_code = 500
    default_detail = "An unexpected error occurred with the IMAP server."
    default_code = "unexpected_error"


class IMAPFlagError(IMAPClientError):
    """Base class for IMAP flag errors."""

    status_code = 500
    default_detail = "A flag-related error occurred."
    default_code = "flag_error"


class IMAPFlagOperationError(IMAPFlagError):
    """Exception raised for flag operation errors."""

    status_code = 500
    default_detail = "Failed to perform flag operation."
    default_code = "flag_operation_error"


class IMAPMailboxError(IMAPClientError):
    """Base class for IMAP mailbox errors."""

    status_code = 500
    default_detail = "A mailbox-related error occurred."
    default_code = "mailbox_error"


class IMAPMailboxSelectionError(IMAPMailboxError):
    """Exception raised for mailbox selection errors."""

    status_code = 500
    default_detail = "Failed to select mailbox."
    default_code = "mailbox_selection_error"


class IMAPMailboxClosureError(IMAPMailboxError):
    """Exception raised for mailbox closure errors."""

    status_code = 500
    default_detail = "Failed to close mailbox."
    default_code = "mailbox_closure_error"


class IMAPMailboxCheckError(IMAPMailboxError):
    """Exception raised for mailbox check errors."""

    status_code = 500
    default_detail = "Failed to perform mailbox check."
    default_code = "mailbox_check_error"


class IMAPMailboxDeleteError(IMAPMailboxError):
    """Exception raised for delete errors."""

    status_code = 500
    default_detail = "Failed to delete email."
    default_code = "delete_error"


class IMAPMailboxPermanentDeleteError(IMAPMailboxDeleteError):
    """Exception raised for permanent delete errors."""

    status_code = 500
    default_detail = "Failed to permanently delete email."
    default_code = "permanent_delete_error"


class IMAPMailboxMoveError(IMAPMailboxError):
    """Exception raised for move errors."""

    status_code = 500
    default_detail = "Failed to move email."
    default_code = "move_error"


class IMAPSearchError(IMAPMailboxError):
    """Exception raised for search errors."""

    status_code = 500
    default_detail = "Failed to search emails."
    default_code = "search_error"


class IMAPMailboxSaveSentError(IMAPMailboxError):
    """Exception raised for errors while saving sent emails."""

    status_code = 500
    default_detail = "Failed to save sent email."
    default_code = "save_sent_error"


class IMAPMailboxStatusError(IMAPMailboxError):
    """Exception raised for errors while getting mailbox status."""

    status_code = 500
    default_detail = "Failed to get mailbox status."
    default_code = "status_error"


class IMAPMailboxFetchError(IMAPMailboxError):
    """Exception raised for fetch operation errors."""

    status_code = 500
    default_detail = "Failed to fetch email messages."
    default_code = "fetch_error"


class EmailException(Exception):
    """Custom exception for email related errors."""

    status_code: int = 500
    default_detail: str = "A server error occurred."
    default_code: str = "error"

    def __init__(
        self,
        detail: Optional[str] = None,
        code: Optional[str] = None,
        status_code: Optional[int] = None,
    ):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        if status_code is None:
            status_code = self.status_code
        self.detail: str = detail
        self.code: str = code
        self.status_code: int = status_code

    def __str__(self) -> str:
        return f"{self.detail} (Code: {self.code}, Status Code: {self.status_code})"
