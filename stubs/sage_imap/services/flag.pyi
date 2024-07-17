from _typeshed import Incomplete
from sage_imap.exceptions import IMAPFlagOperationError as IMAPFlagOperationError
from sage_imap.helpers.flags import FlagCommand as FlagCommand, Flags as Flags
from sage_imap.models.message import MessageSet as MessageSet

logger: Incomplete

class IMAPFlagService:
    mailbox: Incomplete
    def __init__(self, mailbox: IMAPMailboxService) -> None: ...
    def add_flag(self, msg_ids: MessageSet, flag: Flags) -> None: ...
    def remove_flag(self, msg_ids: MessageSet, flag: Flags) -> None: ...
