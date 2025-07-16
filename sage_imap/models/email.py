import email
import hashlib
import logging
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from email import policy
from email.utils import parsedate_to_datetime
from functools import cached_property
from pathlib import Path
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

    def __post_init__(self) -> None:
        """Validate and sanitize attachment data."""
        if not self.filename:
            raise ValueError("Attachment filename cannot be empty")

        # Sanitize filename to prevent path traversal attacks
        self.filename = self._sanitize_filename(self.filename)

        # Validate content type
        if not self.content_type:
            self.content_type = "application/octet-stream"

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename to prevent security issues."""
        # Remove path separators and dangerous characters
        filename = os.path.basename(filename)
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        return filename[:255]  # Limit filename length

    @cached_property
    def size(self) -> int:
        """Get attachment size in bytes."""
        return len(self.payload)

    @cached_property
    def is_image(self) -> bool:
        """Check if attachment is an image."""
        return self.content_type.startswith("image/")

    @cached_property
    def is_text(self) -> bool:
        """Check if attachment is text-based."""
        return self.content_type.startswith("text/")

    def save_to_file(self, directory: Union[str, Path]) -> Path:
        """Save attachment to a file."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        file_path = directory / self.filename

        # Handle filename conflicts
        counter = 1
        original_path = file_path
        while file_path.exists():
            stem = original_path.stem
            suffix = original_path.suffix
            file_path = directory / f"{stem}_{counter}{suffix}"
            counter += 1

        with open(file_path, "wb") as f:
            f.write(self.payload)

        logger.info(f"Attachment saved to: {file_path}")
        return file_path


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

    # Internal fields for caching
    _parsed: bool = field(default=False, init=False, repr=False)
    _parse_error: Optional[Exception] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.raw and not self._parsed:
            try:
                self.parse_eml_content()
            except Exception as e:
                logger.error(f"Failed to parse email content: {e}")
                self._parse_error = e

    @classmethod
    def read_from_eml_file(cls, file_path: Union[str, Path]) -> "EmailMessage":
        """Read email from .eml file with better error handling."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Email file not found: {file_path}")

        if not file_path.suffix.lower() == ".eml":
            logger.warning(f"File {file_path} doesn't have .eml extension")

        try:
            with open(file_path, "rb") as f:
                raw_content = f.read()
        except IOError as e:
            raise IOError(f"Failed to read email file {file_path}: {e}")

        if not raw_content:
            raise ValueError(f"Email file {file_path} is empty")

        instance = cls(message_id="")
        instance.raw = raw_content
        instance.parse_eml_content()
        return instance

    @classmethod
    def read_from_eml_bytes(cls, eml_bytes: bytes) -> "EmailMessage":
        """Read email from bytes with validation."""
        if not eml_bytes:
            raise ValueError("Email bytes cannot be empty")

        instance = cls(message_id="")
        instance.raw = eml_bytes
        instance.parse_eml_content()
        return instance

    def parse_eml_content(self) -> None:
        """Parse email content with enhanced error handling."""
        if not self.raw:
            raise ValueError("No raw email content to parse")

        try:
            email_message = email.message_from_bytes(self.raw, policy=policy.default)
        except Exception as e:
            logger.error(f"Failed to parse email message: {e}")
            raise ValueError(f"Invalid email format: {e}")

        try:
            self.message_id = self.sanitize_message_id(
                email_message.get("Message-ID", "")
            )
            self.subject = self._safe_header_decode(email_message.get("subject", ""))
            self.from_address = self._parse_email_address(email_message.get("from", ""))
            self.to_address = self._parse_email_addresses(
                email_message.get_all("to", [])
            )
            self.cc_address = self._parse_email_addresses(
                email_message.get_all("cc", [])
            )
            self.bcc_address = self._parse_email_addresses(
                email_message.get_all("bcc", [])
            )
            self.date = self.parse_date(email_message.get("date"))
            self.plain_body, self.html_body = self.extract_body(email_message)
            self.attachments = self.extract_attachments(email_message)
            self.headers = {k: v for k, v in email_message.items()}
            self.size = len(self.raw)
            self._parsed = True
        except Exception as e:
            logger.error(f"Error parsing email fields: {e}")
            self._parse_error = e
            raise

    def _safe_header_decode(self, header_value: str) -> str:
        """Safely decode email header values."""
        if not header_value:
            return ""

        try:
            # Handle encoded headers
            from email.header import decode_header

            decoded_parts = decode_header(header_value)
            decoded_header = ""

            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    if encoding:
                        decoded_header += part.decode(encoding, errors="replace")
                    else:
                        decoded_header += part.decode("utf-8", errors="replace")
                else:
                    decoded_header += part

            return decoded_header.strip()
        except Exception as e:
            logger.warning(f"Failed to decode header '{header_value}': {e}")
            return str(header_value)

    def _parse_email_address(self, addr_str: str) -> Optional[EmailAddress]:
        """Parse a single email address with validation."""
        if not addr_str:
            return None

        try:
            return EmailAddress(addr_str)
        except Exception as e:
            logger.warning(f"Failed to parse email address '{addr_str}': {e}")
            return None

    def _parse_email_addresses(self, addr_list: List[str]) -> List[EmailAddress]:
        """Parse multiple email addresses with validation."""
        addresses = []
        for addr_str in addr_list:
            if addr_str:
                try:
                    addresses.append(EmailAddress(addr_str))
                except Exception as e:
                    logger.warning(f"Failed to parse email address '{addr_str}': {e}")
        return addresses

    def sanitize_message_id(self, message_id: str) -> Optional[str]:
        """Sanitize message ID with better validation."""
        if not message_id:
            return None

        # Clean up the message ID
        message_id = message_id.strip()

        # Extract ID from angle brackets
        pattern = r"<([^>]+)>"
        match = re.search(pattern, message_id)

        if match:
            sanitized_id = match.group(1).strip()
            if sanitized_id:
                return f"<{sanitized_id}>"

        # If no angle brackets, check if it's a valid message ID format
        if "@" in message_id and "." in message_id:
            return f"<{message_id}>"

        return None

    def parse_date(self, date_str: Optional[str]) -> Optional[EmailDate]:
        """Parse email date with better error handling."""
        if not date_str:
            return None

        try:
            parsed_date = parsedate_to_datetime(date_str)
            if parsed_date:
                return EmailDate(parsed_date.replace(microsecond=0).isoformat())
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")

        return None

    def extract_body(self, message: email.message.EmailMessage) -> Tuple[str, str]:
        """Extract email body with improved handling."""
        plain_body = ""
        html_body = ""

        try:
            if message.is_multipart():
                for part in message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))

                    if "attachment" not in content_disposition:
                        if content_type == "text/plain":
                            plain_body += self.decode_payload(part)
                        elif content_type == "text/html":
                            html_body += self.decode_payload(part)
            else:
                content_type = message.get_content_type()
                if content_type == "text/plain":
                    plain_body = self.decode_payload(message)
                elif content_type == "text/html":
                    html_body = self.decode_payload(message)
        except Exception as e:
            logger.error(f"Error extracting email body: {e}")

        return plain_body.strip(), html_body.strip()

    def extract_attachments(
        self, message: email.message.EmailMessage
    ) -> List[Attachment]:
        """Extract attachments with better error handling."""
        attachments = []

        try:
            for part in message.walk():
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition or part.get_filename():
                    try:
                        filename = part.get_filename()
                        if not filename:
                            # Generate filename if missing
                            ext = self._get_extension_from_content_type(
                                part.get_content_type()
                            )
                            filename = f"attachment_{len(attachments) + 1}{ext}"

                        payload = part.get_payload(decode=True)
                        if payload:
                            attachment = Attachment(
                                id=part.get("X-Attachment-Id"),
                                filename=filename,
                                content_type=part.get_content_type()
                                or "application/octet-stream",
                                payload=payload,
                                content_id=part.get("Content-ID"),
                                content_transfer_encoding=part.get(
                                    "Content-Transfer-Encoding"
                                ),
                            )
                            attachments.append(attachment)
                    except Exception as e:
                        logger.warning(f"Failed to extract attachment: {e}")
        except Exception as e:
            logger.error(f"Error extracting attachments: {e}")

        return attachments

    def _get_extension_from_content_type(self, content_type: str) -> str:
        """Get file extension from content type."""
        if not content_type:
            return ".bin"

        extension_map = {
            "text/plain": ".txt",
            "text/html": ".html",
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "application/pdf": ".pdf",
            "application/zip": ".zip",
            "application/json": ".json",
            "application/xml": ".xml",
        }

        return extension_map.get(content_type.lower(), ".bin")

    @staticmethod
    def extract_flags(flag_data: bytes) -> List[Flag]:
        """Extract flags with better error handling."""
        flags = []
        flag_mapping = {
            "\\Seen": Flag.SEEN,
            "\\Answered": Flag.ANSWERED,
            "\\Flagged": Flag.FLAGGED,
            "\\Deleted": Flag.DELETED,
            "\\Draft": Flag.DRAFT,
            "\\Recent": Flag.RECENT,
        }

        try:
            # Extract flags from the flag_data
            match = re.search(rb"FLAGS \(([^)]*)\)", flag_data)
            if match:
                flag_str = match.group(1).decode("utf-8", errors="replace")
                for flag in flag_str.split():
                    if flag in flag_mapping:
                        flags.append(flag_mapping[flag])
        except Exception as e:
            logger.warning(f"Failed to extract flags: {e}")

        return flags

    def decode_payload(self, part: email.message.EmailMessage) -> str:
        """Decode email payload with better error handling."""
        try:
            payload = part.get_payload(decode=True)

            if isinstance(payload, bytes):
                charset = part.get_content_charset() or "utf-8"
                try:
                    return payload.decode(charset, errors="replace")
                except (LookupError, UnicodeDecodeError):
                    # Try common encodings
                    for encoding in ["utf-8", "latin-1", "cp1252"]:
                        try:
                            return payload.decode(encoding, errors="replace")
                        except (LookupError, UnicodeDecodeError):
                            continue
                    return payload.decode("utf-8", errors="replace")
            elif isinstance(payload, str):
                return payload
            elif isinstance(payload, list):
                return "".join(self.decode_payload(p) for p in payload)

            return str(payload)
        except Exception as e:
            logger.warning(f"Failed to decode payload: {e}")
            return ""

    # Cached properties for performance
    @cached_property
    def content_hash(self) -> str:
        """Generate hash of email content for deduplication."""
        if not self.raw:
            return ""
        return hashlib.md5(self.raw).hexdigest()

    @cached_property
    def all_recipients(self) -> List[EmailAddress]:
        """Get all recipients (to, cc, bcc)."""
        return self.to_address + self.cc_address + self.bcc_address

    @cached_property
    def is_multipart(self) -> bool:
        """Check if email is multipart."""
        return bool(self.attachments) or (
            bool(self.plain_body) and bool(self.html_body)
        )

    @cached_property
    def total_attachment_size(self) -> int:
        """Get total size of all attachments."""
        return sum(attachment.size for attachment in self.attachments)

    # Utility methods
    def has_attachments(self) -> bool:
        """Check if email has attachments."""
        return bool(self.attachments)

    def get_attachment_filenames(self) -> List[str]:
        """Get list of attachment filenames."""
        return [attachment.filename for attachment in self.attachments]

    def get_attachments_by_type(self, content_type: str) -> List[Attachment]:
        """Get attachments by content type."""
        return [
            att for att in self.attachments if att.content_type.startswith(content_type)
        ]

    def get_image_attachments(self) -> List[Attachment]:
        """Get image attachments."""
        return [att for att in self.attachments if att.is_image]

    def has_html_body(self) -> bool:
        """Check if email has HTML body."""
        return bool(self.html_body.strip())

    def has_plain_body(self) -> bool:
        """Check if email has plain text body."""
        return bool(self.plain_body.strip())

    def get_body_preview(self, max_length: int = 100) -> str:
        """Get preview of email body."""
        body = self.plain_body or self.html_body
        if len(body) <= max_length:
            return body
        return body[:max_length] + "..."

    def is_reply(self) -> bool:
        """Check if email is a reply."""
        return self.subject.lower().startswith(("re:", "reply:"))

    def is_forward(self) -> bool:
        """Check if email is a forward."""
        return self.subject.lower().startswith(("fwd:", "fw:", "forward:"))

    def write_to_eml_file(self, file_path: Union[str, Path]) -> Path:
        """Write email to .eml file with better error handling."""
        if not self.raw:
            raise ValueError("No raw email content to write")

        file_path = Path(file_path)

        if not file_path.suffix:
            file_path = file_path.with_suffix(".eml")
        elif file_path.suffix.lower() != ".eml":
            logger.warning(f"File path {file_path} doesn't have .eml extension")

        # Create directory if it doesn't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, "wb") as f:
                f.write(self.raw)
            logger.info(f"Email written to: {file_path}")
            return file_path
        except IOError as e:
            raise IOError(f"Failed to write email to {file_path}: {e}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert email to dictionary representation."""
        return {
            "message_id": self.message_id,
            "subject": self.subject,
            "from_address": str(self.from_address) if self.from_address else None,
            "to_address": [str(addr) for addr in self.to_address],
            "cc_address": [str(addr) for addr in self.cc_address],
            "bcc_address": [str(addr) for addr in self.bcc_address],
            "date": self.date,
            "plain_body": self.plain_body,
            "html_body": self.html_body,
            "attachments": [
                {
                    "filename": att.filename,
                    "content_type": att.content_type,
                    "size": att.size,
                }
                for att in self.attachments
            ],
            "flags": [flag.value for flag in self.flags],
            "size": self.size,
            "sequence_number": self.sequence_number,
            "uid": self.uid,
            "has_attachments": self.has_attachments(),
            "is_multipart": self.is_multipart,
            "content_hash": self.content_hash,
        }

    def __str__(self) -> str:
        """String representation of email."""
        return f"Email(subject='{self.subject}', from={self.from_address}, size={self.size})"


class EmailIterator:
    """Enhanced email iterator with improved filtering, sorting, and performance."""

    def __init__(self, email_list: List[EmailMessage]):
        self._email_list = email_list
        self._index = 0
        self._filtered_indices: Optional[List[int]] = None

    def __iter__(self) -> "EmailIterator":
        self._index = 0
        return self

    def __next__(self) -> EmailMessage:
        if self._filtered_indices is not None:
            if self._index >= len(self._filtered_indices):
                raise StopIteration
            email_message = self._email_list[self._filtered_indices[self._index]]
        else:
            if self._index >= len(self._email_list):
                raise StopIteration
            email_message = self._email_list[self._index]

        self._index += 1
        return email_message

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[EmailMessage, "EmailIterator"]:
        if isinstance(index, int):
            if self._filtered_indices is not None:
                if index < 0 or index >= len(self._filtered_indices):
                    raise IndexError("Index out of range")
                return self._email_list[self._filtered_indices[index]]
            else:
                if index < 0 or index >= len(self._email_list):
                    raise IndexError("Index out of range")
                return self._email_list[index]
        elif isinstance(index, slice):
            if self._filtered_indices is not None:
                filtered_emails = [
                    self._email_list[i] for i in self._filtered_indices[index]
                ]
            else:
                filtered_emails = self._email_list[index]
            return EmailIterator(filtered_emails)
        else:
            raise TypeError("Invalid argument type")

    def __len__(self) -> int:
        if self._filtered_indices is not None:
            return len(self._filtered_indices)
        return len(self._email_list)

    def __repr__(self) -> str:
        return f"EmailIterator({len(self)} emails)"

    def __bool__(self) -> bool:
        """Check if iterator has any emails."""
        return len(self) > 0

    def reset(self) -> None:
        """Reset iterator to beginning."""
        self._index = 0

    def current_position(self) -> int:
        """Get current position in iterator."""
        return self._index

    def __reversed__(self) -> "EmailIterator":
        """Return reversed iterator."""
        if self._filtered_indices is not None:
            reversed_emails = [
                self._email_list[i] for i in reversed(self._filtered_indices)
            ]
        else:
            reversed_emails = list(reversed(self._email_list))
        return EmailIterator(reversed_emails)

    def __contains__(self, item: EmailMessage) -> bool:
        """Check if email is in iterator."""
        if self._filtered_indices is not None:
            return any(self._email_list[i] == item for i in self._filtered_indices)
        return item in self._email_list

    def count(self, condition: Callable[[EmailMessage], bool]) -> int:
        """Count emails matching condition."""
        if self._filtered_indices is not None:
            return sum(
                1 for i in self._filtered_indices if condition(self._email_list[i])
            )
        return sum(1 for email in self._email_list if condition(email))

    def filter(self, criteria: Callable[[EmailMessage], bool]) -> "EmailIterator":
        """Filter emails by criteria."""
        if self._filtered_indices is not None:
            filtered_emails = [
                self._email_list[i]
                for i in self._filtered_indices
                if criteria(self._email_list[i])
            ]
        else:
            filtered_emails = [email for email in self._email_list if criteria(email)]
        return EmailIterator(filtered_emails)

    def filter_by_header(
        self, key: str, value: Optional[str] = None
    ) -> "EmailIterator":
        """Filter by header key or key-value pair."""
        if value is None:
            return self.filter(lambda email: key in email.headers)
        else:
            return self.filter(lambda email: email.headers.get(key) == value)

    def filter_by_subject_part(
        self, part: str, case_sensitive: bool = False
    ) -> "EmailIterator":
        """Filter by subject containing specific text."""
        if case_sensitive:
            return self.filter(lambda email: part in email.subject)
        else:
            part_lower = part.lower()
            return self.filter(lambda email: part_lower in email.subject.lower())

    def filter_by_subject_regex(self, pattern: str, flags: int = 0) -> "EmailIterator":
        """Filter by subject matching regex pattern."""
        compiled_pattern = re.compile(pattern, flags)
        return self.filter(
            lambda email: compiled_pattern.search(email.subject) is not None
        )

    def filter_by_sender(
        self, sender: str, exact_match: bool = False
    ) -> "EmailIterator":
        """Filter by sender email address."""
        if exact_match:
            return self.filter(
                lambda email: email.from_address and str(email.from_address) == sender
            )
        else:
            sender_lower = sender.lower()
            return self.filter(
                lambda email: email.from_address
                and sender_lower in str(email.from_address).lower()
            )

    def filter_by_recipient(
        self, recipient: str, exact_match: bool = False
    ) -> "EmailIterator":
        """Filter by recipient in to, cc, or bcc fields."""
        if exact_match:
            return self.filter(
                lambda email: any(
                    str(addr) == recipient for addr in email.all_recipients
                )
            )
        else:
            recipient_lower = recipient.lower()
            return self.filter(
                lambda email: any(
                    recipient_lower in str(addr).lower()
                    for addr in email.all_recipients
                )
            )

    def filter_by_date_range(
        self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None
    ) -> "EmailIterator":
        """Filter by date range."""

        def date_filter(email: EmailMessage) -> bool:
            if not email.date:
                return False

            try:
                email_date = datetime.fromisoformat(email.date.replace("Z", "+00:00"))
                if start_date and email_date < start_date:
                    return False
                if end_date and email_date > end_date:
                    return False
                return True
            except (ValueError, TypeError):
                return False

        return self.filter(date_filter)

    def filter_by_size_range(
        self, min_size: Optional[int] = None, max_size: Optional[int] = None
    ) -> "EmailIterator":
        """Filter by email size range."""

        def size_filter(email: EmailMessage) -> bool:
            if min_size is not None and email.size < min_size:
                return False
            if max_size is not None and email.size > max_size:
                return False
            return True

        return self.filter(size_filter)

    def filter_by_flags(
        self, flags: List[Flag], match_all: bool = False
    ) -> "EmailIterator":
        """Filter by email flags."""
        if match_all:
            return self.filter(lambda email: all(flag in email.flags for flag in flags))
        else:
            return self.filter(lambda email: any(flag in email.flags for flag in flags))

    def filter_by_attachment_count(
        self, min_count: int = 0, max_count: Optional[int] = None
    ) -> "EmailIterator":
        """Filter by number of attachments."""

        def attachment_filter(email: EmailMessage) -> bool:
            count = len(email.attachments)
            if count < min_count:
                return False
            if max_count is not None and count > max_count:
                return False
            return True

        return self.filter(attachment_filter)

    def filter_by_content_type(self, content_type: str) -> "EmailIterator":
        """Filter by attachment content type."""
        return self.filter(
            lambda email: any(
                att.content_type.startswith(content_type) for att in email.attachments
            )
        )

    def find_by_message_id(self, message_id: str) -> Optional[EmailMessage]:
        """Find email by message ID."""
        return self.find(lambda email: email.message_id == message_id)

    def find(self, condition: Callable[[EmailMessage], bool]) -> Optional[EmailMessage]:
        """Find first email matching condition."""
        for email in self:
            if condition(email):
                return email
        return None

    def find_all(self, condition: Callable[[EmailMessage], bool]) -> "EmailIterator":
        """Find all emails matching condition."""
        return self.filter(condition)

    def filter_by_attachment(self) -> "EmailIterator":
        """Filter emails that have attachments."""
        return self.filter(lambda email: email.has_attachments())

    def filter_without_attachment(self) -> "EmailIterator":
        """Filter emails without attachments."""
        return self.filter(lambda email: not email.has_attachments())

    def filter_by_body_content(
        self,
        content: str,
        case_sensitive: bool = False,
        html_only: bool = False,
        plain_only: bool = False,
    ) -> "EmailIterator":
        """Filter by body content."""
        if case_sensitive:
            search_func = lambda text: content in text
        else:
            content_lower = content.lower()
            search_func = lambda text: content_lower in text.lower()

        def body_filter(email: EmailMessage) -> bool:
            if html_only:
                return search_func(email.html_body)
            elif plain_only:
                return search_func(email.plain_body)
            else:
                return search_func(email.plain_body) or search_func(email.html_body)

        return self.filter(body_filter)

    def get_total_size(self) -> int:
        """Get total size of all emails."""
        return sum(email.size for email in self)

    def get_total_attachment_size(self) -> int:
        """Get total size of all attachments."""
        return sum(email.total_attachment_size for email in self)

    def get_unique_senders(self) -> List[str]:
        """Get list of unique sender addresses."""
        senders = set()
        for email in self:
            if email.from_address:
                senders.add(str(email.from_address))
        return sorted(list(senders))

    def get_unique_recipients(self) -> List[str]:
        """Get list of unique recipient addresses."""
        recipients = set()
        for email in self:
            for addr in email.all_recipients:
                recipients.add(str(addr))
        return sorted(list(recipients))

    def get_date_range(self) -> Tuple[Optional[str], Optional[str]]:
        """Get date range of emails (earliest, latest)."""
        dates = [email.date for email in self if email.date]
        if not dates:
            return None, None
        return min(dates), max(dates)

    def group_by_sender(self) -> Dict[str, "EmailIterator"]:
        """Group emails by sender."""
        groups = {}
        for email in self:
            sender = str(email.from_address) if email.from_address else "Unknown"
            if sender not in groups:
                groups[sender] = []
            groups[sender].append(email)

        return {sender: EmailIterator(emails) for sender, emails in groups.items()}

    def group_by_date(
        self, date_format: str = "%Y-%m-%d"
    ) -> Dict[str, "EmailIterator"]:
        """Group emails by date."""
        groups = {}
        for email in self:
            if email.date:
                try:
                    date_obj = datetime.fromisoformat(email.date.replace("Z", "+00:00"))
                    date_key = date_obj.strftime(date_format)
                except (ValueError, TypeError):
                    date_key = "Unknown"
            else:
                date_key = "Unknown"

            if date_key not in groups:
                groups[date_key] = []
            groups[date_key].append(email)

        return {date_key: EmailIterator(emails) for date_key, emails in groups.items()}

    def sort_by_date(self, ascending: bool = True) -> "EmailIterator":
        """Sort emails by date."""

        def date_key(email: EmailMessage) -> datetime:
            if email.date:
                try:
                    return datetime.fromisoformat(email.date.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    return datetime.min if ascending else datetime.max
            return datetime.min if ascending else datetime.max

        sorted_emails = sorted(
            self._get_current_emails(), key=date_key, reverse=not ascending
        )
        return EmailIterator(sorted_emails)

    def sort_by_size(self, ascending: bool = True) -> "EmailIterator":
        """Sort emails by size."""
        sorted_emails = sorted(
            self._get_current_emails(),
            key=lambda email: email.size,
            reverse=not ascending,
        )
        return EmailIterator(sorted_emails)

    def sort_by_subject(self, ascending: bool = True) -> "EmailIterator":
        """Sort emails by subject."""
        sorted_emails = sorted(
            self._get_current_emails(),
            key=lambda email: email.subject.lower(),
            reverse=not ascending,
        )
        return EmailIterator(sorted_emails)

    def sort_by_sender(self, ascending: bool = True) -> "EmailIterator":
        """Sort emails by sender."""

        def sender_key(email: EmailMessage) -> str:
            return str(email.from_address).lower() if email.from_address else ""

        sorted_emails = sorted(
            self._get_current_emails(), key=sender_key, reverse=not ascending
        )
        return EmailIterator(sorted_emails)

    def sort_by_attachment_count(self, ascending: bool = True) -> "EmailIterator":
        """Sort emails by number of attachments."""
        sorted_emails = sorted(
            self._get_current_emails(),
            key=lambda email: len(email.attachments),
            reverse=not ascending,
        )
        return EmailIterator(sorted_emails)

    def _get_current_emails(self) -> List[EmailMessage]:
        """Get current list of emails (considering filters)."""
        if self._filtered_indices is not None:
            return [self._email_list[i] for i in self._filtered_indices]
        return self._email_list

    def take(self, count: int) -> "EmailIterator":
        """Take first N emails."""
        current_emails = self._get_current_emails()
        return EmailIterator(current_emails[:count])

    def skip(self, count: int) -> "EmailIterator":
        """Skip first N emails."""
        current_emails = self._get_current_emails()
        return EmailIterator(current_emails[count:])

    def page(self, page_number: int, page_size: int) -> "EmailIterator":
        """Get specific page of emails."""
        start_index = (page_number - 1) * page_size
        end_index = start_index + page_size
        current_emails = self._get_current_emails()
        return EmailIterator(current_emails[start_index:end_index])

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the email collection."""
        emails = list(self)

        if not emails:
            return {
                "total_emails": 0,
                "total_size": 0,
                "total_attachment_size": 0,
                "unique_senders": 0,
                "unique_recipients": 0,
                "emails_with_attachments": 0,
                "date_range": (None, None),
            }

        return {
            "total_emails": len(emails),
            "total_size": sum(email.size for email in emails),
            "total_attachment_size": sum(
                email.total_attachment_size for email in emails
            ),
            "unique_senders": len(self.get_unique_senders()),
            "unique_recipients": len(self.get_unique_recipients()),
            "emails_with_attachments": len(self.filter_by_attachment()),
            "average_size": sum(email.size for email in emails) / len(emails),
            "date_range": self.get_date_range(),
            "flag_distribution": self._get_flag_distribution(),
            "content_type_distribution": self._get_content_type_distribution(),
        }

    def _get_flag_distribution(self) -> Dict[str, int]:
        """Get distribution of flags across emails."""
        flag_counts = {}
        for email in self:
            for flag in email.flags:
                flag_name = flag.value
                flag_counts[flag_name] = flag_counts.get(flag_name, 0) + 1
        return flag_counts

    def _get_content_type_distribution(self) -> Dict[str, int]:
        """Get distribution of attachment content types."""
        content_type_counts = {}
        for email in self:
            for attachment in email.attachments:
                content_type = attachment.content_type
                content_type_counts[content_type] = (
                    content_type_counts.get(content_type, 0) + 1
                )
        return content_type_counts

    def to_list(self) -> List[EmailMessage]:
        """Convert iterator to list."""
        return list(self)

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Convert iterator to list of dictionaries."""
        return [email.to_dict() for email in self]

    def save_all_to_directory(
        self, directory: Union[str, Path], filename_template: str = "{subject}_{date}"
    ) -> List[Path]:
        """Save all emails to .eml files in directory."""
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        saved_files = []
        for i, email in enumerate(self):
            try:
                # Create filename from template
                filename = filename_template.format(
                    subject=re.sub(r'[<>:"/\\|?*]', "_", email.subject[:50]),
                    date=email.date or f"email_{i}",
                    message_id=email.message_id or f"msg_{i}",
                    index=i,
                )

                if not filename.endswith(".eml"):
                    filename += ".eml"

                file_path = directory / filename

                # Handle filename conflicts
                counter = 1
                original_path = file_path
                while file_path.exists():
                    stem = original_path.stem
                    file_path = directory / f"{stem}_{counter}.eml"
                    counter += 1

                saved_path = email.write_to_eml_file(file_path)
                saved_files.append(saved_path)

            except Exception as e:
                logger.error(f"Failed to save email {i}: {e}")

        return saved_files

    def chain(self, other: "EmailIterator") -> "EmailIterator":
        """Chain two iterators together."""
        combined_emails = self.to_list() + other.to_list()
        return EmailIterator(combined_emails)

    def deduplicate(
        self, key_func: Optional[Callable[[EmailMessage], str]] = None
    ) -> "EmailIterator":
        """Remove duplicate emails."""
        if key_func is None:
            key_func = lambda email: email.content_hash

        seen = set()
        unique_emails = []

        for email in self:
            key = key_func(email)
            if key not in seen:
                seen.add(key)
                unique_emails.append(email)

        return EmailIterator(unique_emails)
