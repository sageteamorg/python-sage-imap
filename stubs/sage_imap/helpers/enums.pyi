from _typeshed import Incomplete
from enum import StrEnum

logger: Incomplete

class Flag(StrEnum):
    SEEN = '\\Seen'
    ANSWERED = '\\Answered'
    FLAGGED = '\\Flagged'
    DELETED = '\\Deleted'
    DRAFT = '\\Draft'
    RECENT = '\\Recent'

class FlagCommand(StrEnum):
    ADD = '+FLAGS'
    REMOVE = '-FLAGS'

class Priority(StrEnum):
    HIGH = '1'
    NORMAL = '3'
    LOW = '5'

class SpamResult(StrEnum):
    DEFAULT = 'default'
    SPAM = 'spam'
    NOT_SPAM = 'not-spam'

class AutoResponseSuppress(StrEnum):
    ALL = 'All'
    DR = 'DR'
    NDN = 'NDN'
    RN = 'RN'
    NRN = 'NRN'
    OOF = 'OOF'
    AutoReply = 'AutoReply'

class ContentType(StrEnum):
    PLAIN = 'text/plain; charset=UTF-8'
    HTML = 'text/html; charset=UTF-8'
    MULTIPART = 'multipart/mixed'

class ContentTransferEncoding(StrEnum):
    SEVEN_BIT = '7bit'
    BASE64 = 'base64'
    QUOTED_PRINTABLE = 'quoted-printable'

class DefaultMailboxes(StrEnum):
    INBOX = 'INBOX'
    SENT = 'Sent'
    DRAFTS = 'Drafts'
    TRASH = 'Trash'
    SPAM = 'Spam'
    ARCHIVE = 'Archive'

class MailboxStatusItems(StrEnum):
    MESSAGES = 'MESSAGES'
    RECENT = 'RECENT'
    UIDNEXT = 'UIDNEXT'
    UIDVALIDITY = 'UIDVALIDITY'
    UNSEEN = 'UNSEEN'

class MessagePart(StrEnum):
    RFC822 = 'RFC822'
    BODY = 'BODY'
    BODY_TEXT = 'BODY[TEXT]'
    BODY_HEADER = 'BODY[HEADER]'
    BODY_HEADER_FIELDS = 'BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)]'
    FLAGS = 'FLAGS'
    MODSEQ = 'MODSEQ'
    BODY_STRUCTURE = 'BODYSTRUCTURE'
    BODY_PEEK = 'BODY.PEEK[]'
    BODY_PEEK_TEXT = 'BODY.PEEK[TEXT]'
    BODY_PEEK_HEADER = 'BODY.PEEK[HEADER]'
    BODY_PEEK_HEADER_FIELDS = 'BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)]'
    BODY_PEEK_ATTACHMENT = 'BODY.PEEK[2]'

class ThreadingAlgorithm(StrEnum):
    REFERENCES = 'REFERENCES'
    ORDEREDSUBJECT = 'ORDEREDSUBJECT'
    THREAD = 'THREAD'
    SEQUENCE = 'SEQUENCE'
