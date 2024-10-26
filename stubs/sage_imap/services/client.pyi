import imaplib
from _typeshed import Incomplete
from sage_imap.exceptions import (
    IMAPAuthenticationError as IMAPAuthenticationError,
    IMAPConnectionError as IMAPConnectionError,
    IMAPUnexpectedError as IMAPUnexpectedError,
)

logger: Incomplete

class IMAPClient:
    host: Incomplete
    username: Incomplete
    password: Incomplete
    connection: Incomplete
    def __init__(self, host: str, username: str, password: str) -> None: ...
    def __enter__(self) -> imaplib.IMAP4_SSL: ...
    def __exit__(
        self,
        exc_type: type | None,
        exc_value: BaseException | None,
        traceback: object | None,
    ) -> None: ...
