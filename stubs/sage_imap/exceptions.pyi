from _typeshed import Incomplete

class IMAPClientError(Exception):
    status_code: int
    default_detail: str
    default_code: str
    detail: Incomplete
    code: Incomplete
    def __init__(self, detail: str | None = None, code: str | None = None, status_code: int | None = None) -> None: ...

class IMAPConfigurationError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPConnectionError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPAuthenticationError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFolderError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFolderOperationError(IMAPFolderError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFolderNotFoundError(IMAPFolderError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFolderExistsError(IMAPFolderError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPDefaultFolderError(IMAPFolderError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPUnexpectedError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFlagError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPFlagOperationError(IMAPFlagError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxSelectionError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxClosureError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxCheckError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxDeleteError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxPermanentDeleteError(IMAPMailboxDeleteError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxMoveError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPSearchError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxSaveSentError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxStatusError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxFetchError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPAppendError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPMailboxUploadError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPThreadError(IMAPMailboxError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPEmptyFileError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str

class IMAPInvalidEmailDateError(IMAPClientError):
    status_code: int
    default_detail: str
    default_code: str
