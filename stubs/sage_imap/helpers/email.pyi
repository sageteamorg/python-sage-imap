from _typeshed import Incomplete
from email.message import Message
from enum import StrEnum
from sage_imap.utils import convert_to_local_time as convert_to_local_time

class EmailMessage:
    message_id: Incomplete
    subject: Incomplete
    from_address: Incomplete
    to_address: Incomplete
    cc_address: Incomplete
    bcc_address: Incomplete
    date: Incomplete
    body: Incomplete
    attachments: Incomplete
    flags: Incomplete
    def __init__(self, message_id: str, message: Message, flags: list[str]) -> None: ...
    def parse_date(self, date_str: str | None) -> str | None: ...
    def get_body(self, message: Message) -> str: ...
    def get_attachments(self, message: Message) -> list[dict]: ...
    def decode_payload(self, part: Message) -> str: ...
    def has_attachments(self) -> bool: ...
    def get_attachment_filenames(self) -> list[str]: ...

class EmailIterator:
    def __init__(self, email_list: list[EmailMessage]) -> None: ...
    def __iter__(self) -> EmailIterator: ...
    def __next__(self) -> EmailMessage: ...
    def __getitem__(self, index: int | slice) -> EmailMessage | EmailIterator: ...
    def __len__(self) -> int: ...

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
