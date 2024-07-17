import email
import logging
import os
import re
from dataclasses import dataclass, field
from difflib import get_close_matches
from email import policy
from email.utils import parsedate_to_datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from sage_imap.helpers.enums import Flag
from sage_imap.helpers.typings import EmailAddress, EmailDate

logger = logging.getLogger(__name__)


@dataclass
class Attachment:
    filename: str
    content_type: str
    payload: bytes = field(repr=False)
    id: Optional[str] = field(default=None)
    content_id: Optional[str] = field(default=None)
    content_transfer_encoding: Optional[str] = field(default=None)


@dataclass
class EmailMessage:
    message_id: str = field(repr=False)
    subject: str = ""
    from_address: Optional[EmailAddress] = field(default=None, repr=False)
    to_address: List[EmailAddress] = field(default_factory=list, repr=False)
    cc_address: List[EmailAddress] = field(default_factory=list, repr=False)
    bcc_address: List[EmailAddress] = field(default_factory=list, repr=False)
    date: Optional[EmailDate] = field(default=None, repr=False)
    raw: Optional[bytes] = field(default=None, repr=False)
    plain_body: str = field(default="", repr=False)
    html_body: str = field(default="", repr=False)
    attachments: List[Attachment] = field(default_factory=list, repr=False)
    flags: List[Flag] = field(default_factory=list, repr=False)
    headers: Dict[str, Any] = field(default_factory=dict, repr=False)
    size: int = field(default=0, repr=True)
    sequence_number: Optional[int] = field(default=None, repr=True)
    uid: Optional[int] = field(default=None, repr=True)

    def __post_init__(self) -> None:
        if self.raw:
            self.parse_eml_content()

    @classmethod
    def read_from_eml_file(cls, file_path: str) -> "EmailMessage":
        with open(file_path, "rb") as f:
            raw_content = f.read()
        instance = cls(message_id="")
        instance.raw = raw_content
        instance.parse_eml_content()
        return instance

    @classmethod
    def read_from_eml_bytes(cls, eml_bytes: bytes) -> "EmailMessage":
        instance = cls(message_id="")
        instance.raw = eml_bytes
        instance.parse_eml_content()
        return instance

    def parse_eml_content(self) -> None:
        email_message = email.message_from_bytes(self.raw, policy=policy.default)
        self.message_id = self.sanitize_message_id(email_message.get("Message-ID", ""))
        self.subject = email_message.get("subject", "")
        self.from_address = EmailAddress(email_message.get("from", ""))
        self.to_address = [
            EmailAddress(addr) for addr in email_message.get_all("to", [])
        ]
        self.cc_address = [
            EmailAddress(addr) for addr in email_message.get_all("cc", [])
        ]
        self.bcc_address = [
            EmailAddress(addr) for addr in email_message.get_all("bcc", [])
        ]
        self.date = self.parse_date(email_message.get("date"))
        self.plain_body, self.html_body = self.extract_body(email_message)
        self.attachments = self.extract_attachments(email_message)
        self.headers = {k: v for k, v in email_message.items()}

    def sanitize_message_id(self, message_id: str) -> Optional[str]:
        pattern = r"<([^>]*)>"
        match = re.search(pattern, message_id)

        if match:
            sanitized_message_id = "<" + match.group(1) + ">"
        else:
            sanitized_message_id = None

        return sanitized_message_id

    def parse_date(self, date_str: Optional[str]) -> Optional[EmailDate]:
        if date_str:
            parsed_date = parsedate_to_datetime(date_str)
            if parsed_date:
                return EmailDate(parsed_date.replace(microsecond=0).isoformat())
        return None

    def extract_body(self, message: email.message.EmailMessage) -> Tuple[str, str]:
        plain_body = ""
        html_body = ""
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if (
                    content_type == "text/plain"
                    and "attachment" not in content_disposition
                ):
                    plain_body += self.decode_payload(part)
                elif (
                    content_type == "text/html"
                    and "attachment" not in content_disposition
                ):
                    html_body += self.decode_payload(part)
        else:
            content_type = message.get_content_type()
            if content_type == "text/plain":
                plain_body = self.decode_payload(message)
            elif content_type == "text/html":
                html_body = self.decode_payload(message)
        return plain_body, html_body

    def extract_attachments(
        self, message: email.message.EmailMessage
    ) -> List[Attachment]:
        attachments = []
        for part in message.walk():
            content_disposition = str(part.get("Content-Disposition"))
            if "attachment" in content_disposition:
                attachments.append(
                    Attachment(
                        id=part.get("X-Attachment-Id"),
                        filename=part.get_filename(),
                        content_type=part.get_content_type(),
                        payload=part.get_payload(decode=True),
                        content_id=part.get("Content-ID"),
                        content_transfer_encoding=part.get("Content-Transfer-Encoding"),
                    )
                )
        return attachments

    @staticmethod
    def extract_flags(flag_data: bytes) -> List[Flag]:
        flags = []
        flag_mapping = {
            "\\Seen": Flag.SEEN,
            "\\Answered": Flag.ANSWERED,
            "\\Flagged": Flag.FLAGGED,
            "\\Deleted": Flag.DELETED,
            "\\Draft": Flag.DRAFT,
            "\\Recent": Flag.RECENT,
        }

        # Extract flags from the flag_data
        match = re.search(rb"FLAGS \(([^)]*)\)", flag_data)
        if match:
            flag_str = match.group(1).decode("utf-8")
            for flag in flag_str.split():
                if flag in flag_mapping:
                    flags.append(flag_mapping[flag])

        return flags

    def decode_payload(self, part: email.message.EmailMessage) -> str:
        payload = part.get_payload(decode=True)
        if isinstance(payload, bytes):
            charset = part.get_content_charset() or "utf-8"
            try:
                return payload.decode(charset, errors="replace")
            except (LookupError, UnicodeDecodeError):
                return payload.decode("utf-8", errors="replace")
        elif isinstance(payload, str):
            return payload
        elif isinstance(payload, list):
            return "".join(self.decode_payload(p) for p in payload)
        return str(payload)

    def has_attachments(self) -> bool:
        return bool(self.attachments)

    def get_attachment_filenames(self) -> List[str]:
        return [attachment.filename for attachment in self.attachments]

    def write_to_eml_file(self, file_path: str) -> None:
        if not file_path.endswith(".eml"):
            file_path += ".eml"

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(self.raw)


class EmailIterator:
    def __init__(self, email_list: List[EmailMessage]):
        self._email_list = email_list
        self._index = 0

    def __iter__(self) -> "EmailIterator":
        self._index = 0
        return self

    def __next__(self) -> EmailMessage:
        if self._index >= len(self._email_list):
            raise StopIteration
        email_message = self._email_list[self._index]
        self._index += 1
        return email_message

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[EmailMessage, "EmailIterator"]:
        if isinstance(index, int):
            if index < 0 or index >= len(self._email_list):
                raise IndexError("Index out of range")
            return self._email_list[index]
        elif isinstance(index, slice):
            return EmailIterator(self._email_list[index])
        else:
            raise TypeError("Invalid argument type")

    def __len__(self) -> int:
        return len(self._email_list)

    def __repr__(self) -> str:
        return f"EmailIterator({len(self._email_list)} emails)"

    def reset(self) -> None:
        self._index = 0

    def current_position(self) -> int:
        return self._index

    def __reversed__(self) -> "EmailIterator":
        return EmailIterator(list(reversed(self._email_list)))

    def __contains__(self, item: EmailMessage) -> bool:
        return item in self._email_list

    def count(self, condition: Callable[[EmailMessage], bool]) -> int:
        return sum(1 for email in self._email_list if condition(email))

    def filter(self, criteria: Callable[[EmailMessage], bool]) -> "EmailIterator":
        filtered_emails = [email for email in self._email_list if criteria(email)]
        return EmailIterator(filtered_emails)

    def filter_by_header(self, key: str) -> "EmailIterator":
        return self.filter(lambda email: key in email.headers.keys())

    def filter_by_subject_part(self, part: str) -> "EmailIterator":
        subjects = [email.subject for email in self._email_list]
        close_matches = get_close_matches(part, subjects)
        return self.filter(lambda email: email.subject in close_matches)

    def find_by_message_id(self, message_id: str) -> Optional[EmailMessage]:
        return self.find(lambda email: email.message_id == message_id)

    def filter_by_attachment(self) -> "EmailIterator":
        return self.filter(lambda email: email.attachments != list())

    def get_total_size(self) -> int:
        return sum(email.size for email in self._email_list)
