from _typeshed import Incomplete
from sage_imap.exceptions import (
    IMAPFolderExistsError as IMAPFolderExistsError,
    IMAPFolderNotFoundError as IMAPFolderNotFoundError,
    IMAPFolderOperationError as IMAPFolderOperationError,
)
from sage_imap.helpers.typings import Mailbox as Mailbox
from sage_imap.services.client import IMAPClient as IMAPClient

logger: Incomplete

class IMAPFolderService:
    client: Incomplete
    def __init__(self, client: IMAPClient) -> None: ...
    def rename_folder(self, old_name: Mailbox, new_name: Mailbox) -> None: ...
    def delete_folder(self, folder_name: Mailbox) -> None: ...
    def create_folder(self, folder_name: Mailbox) -> None: ...
    def list_folders(self) -> list[Mailbox]: ...
