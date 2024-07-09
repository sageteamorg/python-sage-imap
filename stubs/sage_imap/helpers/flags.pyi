from _typeshed import Incomplete
from enum import StrEnum

logger: Incomplete

class Flags(StrEnum):
    SEEN: str
    ANSWERED: str
    FLAGGED: str
    DELETED: str
    DRAFT: str
    RECENT: str

class FlagCommand(StrEnum):
    ADD: str
    REMOVE: str
