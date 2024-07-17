from _typeshed import Incomplete
from enum import StrEnum

logger: Incomplete

class Flag(StrEnum):
    SEEN: str
    ANSWERED: str
    FLAGGED: str
    DELETED: str
    DRAFT: str
    RECENT: str

class FlagCommand(StrEnum):
    ADD: str
    REMOVE: str

class Priority(StrEnum):
    HIGH: str
    NORMAL: str
    LOW: str

class SpamResult(StrEnum):
    DEFAULT: str
    SPAM: str
    NOT_SPAM: str

class AutoResponseSuppress(StrEnum):
    ALL: str
    DR: str
    NDN: str
    RN: str
    NRN: str
    OOF: str
    AutoReply: str

class ContentType(StrEnum):
    PLAIN: str
    HTML: str
    MULTIPART: str

class ContentTransferEncoding(StrEnum):
    SEVEN_BIT: str
    BASE64: str
    QUOTED_PRINTABLE: str

class DefaultMailboxes(StrEnum):
    INBOX: str
    SENT: str
    DRAFTS: str
    TRASH: str
    SPAM: str
    ARCHIVE: str

class MailboxStatusItems(StrEnum):
    MESSAGES: str
    RECENT: str
    UIDNEXT: str
    UIDVALIDITY: str
    UNSEEN: str

class MessagePart(StrEnum):
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

class ThreadingAlgorithm(StrEnum):
    REFERENCES: str
    ORDEREDSUBJECT: str
    THREAD: str
    SEQUENCE: str
