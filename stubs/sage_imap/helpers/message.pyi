from dataclasses import dataclass
from enum import StrEnum
from sage_imap.helpers.typings import MessageSetType as MessageSetType

@dataclass
class MessageSet:
    msg_ids: MessageSetType = ...
    def __post_init__(self) -> None: ...
    def __init__(self, msg_ids=...) -> None: ...

class MessageParts(StrEnum):
    RFC822: str
    BODY: str
    BODY_TEXT: str
    BODY_HEADER: str
    BODY_HEADER_FIELDS: str
    FLAGS: str
    MODSEQ: str
    BODY_STRUCTURE: str
    BODY_PEEK: str
    BODY_PEEK_TEXT: str
    BODY_PEEK_HEADER: str
    BODY_PEEK_HEADER_FIELDS: str
    BODY_PEEK_ATTACHMENT: str
