from email.message import Message
from email.utils import parsedate_to_datetime
from enum import StrEnum
from typing import List, Optional, Union

from sage_imap.utils import convert_to_local_time


class EmailMessage:
    # pylint: disable=too-many-instance-attributes
    """
    A class to represent an email message.

    Parameters
    ----------
    message_id : str
        The unique message ID of the email.
    message : Message
        The email message object.
    flags : List[str]
        List of flags associated with the email message.

    Attributes
    ----------
    message_id : str
        The unique message ID of the email.
    subject : str
        The subject of the email.
    from_address : str
        The sender's email address.
    to_address : List[str]
        List of recipient email addresses.
    cc_address : List[str]
        List of CC recipient email addresses.
    bcc_address : List[str]
        List of BCC recipient email addresses.
    date : str or None
        The date the email was sent, in ISO format.
    body : str
        The body content of the email.
    attachments : List[dict]
        List of attachments in the email.
    flags : List[str]
        List of flags associated with the email message.

    Methods
    -------
    parse_date(date_str: Optional[str]):
        Parses the date string to a datetime object and returns it in ISO format.
    get_body(message: Message) -> str:
        Extracts and returns the body content from the email message.
    get_attachments(message: Message) -> List[dict]:
        Extracts and returns the attachments from the email message.
    decode_payload(part) -> str:
        Decodes the email payload to a string.
    has_attachments() -> bool:
        Checks if the email message has attachments.
    get_attachment_filenames() -> List[str]:
        Returns a list of filenames of the attachments.
    """

    def __init__(self, message_id: str, message: Message, flags: List[str]):
        self.message_id: str = message_id
        self.subject: str = message["subject"]
        self.from_address: str = message["from"]
        self.to_address: List[str] = message.get_all("to", [])
        self.cc_address: List[str] = message.get_all("cc", [])
        self.bcc_address: List[str] = message.get_all("bcc", [])
        self.date: Optional[str] = self.parse_date(message["date"])
        self.body: str = self.get_body(message)
        self.attachments: List[dict] = self.get_attachments(message)
        self.flags: List[str] = flags

    def __repr__(self) -> str:
        return f"EmailMessage(message_id={self.message_id!r}, subject={self.subject!r})"

    def parse_date(self, date_str: Optional[str]) -> Optional[str]:
        """
        Parses the date string to a datetime object and returns it in ISO format.

        Parameters
        ----------
        date_str : Optional[str]
            The date string to parse.

        Returns
        -------
        str or None
            The ISO formatted date string or None if date_str is None.
        """
        if date_str:
            parsed_date = parsedate_to_datetime(date_str)
            return convert_to_local_time(parsed_date).replace(microsecond=0).isoformat()
        return None

    def get_body(self, message: Message) -> str:
        """
        Extracts and returns the body content from the email message.

        Parameters
        ----------
        message : Message
            The email message object.

        Returns
        -------
        str
            The body content of the email.
        """
        if message.is_multipart():
            for part in message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition:
                    if content_type in ["text/plain", "text/html"]:
                        return self.decode_payload(part)
        else:
            return self.decode_payload(message)
        return ""

    def get_attachments(self, message: Message) -> List[dict]:
        """
        Extracts and returns the attachments from the email message.

        Parameters
        ----------
        message : Message
            The email message object.

        Returns
        -------
        List[dict]
            A list of dictionaries, each containing filename,
            content_type, and payload of an attachment.
        """
        attachments = []
        if message.is_multipart():
            for part in message.walk():
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" in content_disposition:
                    attachment = {
                        "filename": part.get_filename(),
                        "content_type": part.get_content_type(),
                        "payload": part.get_payload(decode=True),
                    }
                    attachments.append(attachment)
        return attachments

    def decode_payload(self, part: Message) -> str:
        """
        Decodes the email payload to a string.

        Parameters
        ----------
        part : Message
            The part of the email message to decode.

        Returns
        -------
        str
            The decoded payload as a string.
        """
        payload = part.get_payload(decode=True)

        if isinstance(payload, bytes):
            charset = part.get_content_charset()
            if charset is None:
                charset = "utf-8"  # Default to 'utf-8' if no charset is specified

            try:
                decoded_payload = payload.decode(charset, errors="replace")
                return decoded_payload
            except (LookupError, UnicodeDecodeError):
                return payload.decode("utf-8", errors="replace")  # Fallback to 'utf-8'

        elif isinstance(payload, str):
            return payload

        elif isinstance(payload, list):
            # If the payload is a list, join all parts as a single string
            return "".join(self.decode_payload(part) for part in payload)

        # In case the payload is a Message object or any other type
        return str(payload)

    def has_attachments(self) -> bool:
        """
        Checks if the email message has attachments.

        Returns
        -------
        bool
            True if the email has attachments, False otherwise.
        """
        return len(self.attachments) > 0

    def get_attachment_filenames(self) -> List[str]:
        """
        Returns a list of filenames of the attachments.

        Returns
        -------
        List[str]
            A list of filenames of the attachments.
        """
        return [attachment["filename"] for attachment in self.attachments]


class EmailIterator:
    """
    An iterator class for a list of email messages.

    Parameters
    ----------
    email_list : List[EmailMessage]
        A list of EmailMessage objects.

    Methods
    -------
    __iter__():
        Returns the iterator object.
    __next__():
        Returns the next EmailMessage object in the list.
    __getitem__(index):
        Returns the EmailMessage object at the specified index or a slice of
        EmailIterator.
    __len__():
        Returns the number of email messages in the list.
    __repr__():
        Returns a string representation of the EmailIterator object.
    """

    def __init__(self, email_list: List[EmailMessage]):
        self._email_list = email_list
        self._index = 0

    def __iter__(self) -> "EmailIterator":
        return self

    def __next__(self) -> EmailMessage:
        if self._index < len(self._email_list):
            email_message = self._email_list[self._index]
            self._index += 1
            return email_message
        raise StopIteration

    def __getitem__(
        self, index: Union[int, slice]
    ) -> Union[EmailMessage, "EmailIterator"]:
        if isinstance(index, int):
            if index < 0 or index >= len(self._email_list):
                raise IndexError("Index out of range")
            return self._email_list[index]
        if isinstance(index, slice):
            return EmailIterator(self._email_list[index])
        raise TypeError("Invalid argument type")

    def __len__(self) -> int:
        return len(self._email_list)

    def __repr__(self) -> str:
        return f"EmailIterator({len(self._email_list)} emails)"


class Priority(StrEnum):
    """
    Enum for specifying the priority of an email.

    Values:
        HIGH (str): High priority (value '1').
            - Use this for urgent emails.
            - Email clients usually display these emails with a distinct marker or place them at the top of the inbox.
            - High priority emails are more likely to bypass spam filters.
            - Auto-responders may prioritize these emails for faster responses.

        NORMAL (str): Normal priority (value '3').
            - Default setting for regular emails.
            - Email clients treat these as standard emails.
            - Normal priority emails are subject to regular spam filtering.
            - Auto-responders treat these emails with standard response times.

        LOW (str): Low priority (value '5').
            - Use for less important emails.
            - Email clients may display these emails with a lower marker or place them at the bottom of the inbox.
            - Low priority emails might be more scrutinized by spam filters.
            - Auto-responders may delay responses to these emails.
    """

    HIGH = "1"
    NORMAL = "3"
    LOW = "5"


class SpamResult(StrEnum):
    """
    Enum for indicating the spam status of an email.

    Values:
        DEFAULT (str): Default status (value 'default'). No specific spam status.
        SPAM (str): Email is marked as spam (value 'spam').
        NOT_SPAM (str): Email is marked as not spam (value 'not-spam').
    """

    DEFAULT = "default"
    SPAM = "spam"
    NOT_SPAM = "not-spam"


class AutoResponseSuppress(StrEnum):
    """
    Enum for controlling auto-responses for an email.

    Values:
        ALL (str): Suppress all auto-responses (value 'All').
        DR (str): Suppress delivery receipts (value 'DR').
        NDN (str): Suppress non-delivery notifications (value 'NDN').
        RN (str): Suppress read notifications (value 'RN').
        NRN (str): Suppress non-read notifications (value 'NRN').
        OOF (str): Suppress out-of-office replies (value 'OOF').
        AutoReply (str): Suppress automatic replies (value 'AutoReply').
    """

    ALL = "All"
    DR = "DR"
    NDN = "NDN"
    RN = "RN"
    NRN = "NRN"
    OOF = "OOF"
    AutoReply = "AutoReply"


class ContentType(StrEnum):
    """
    Enum for specifying the content type of an email.

    Values:
        PLAIN (str): Plain text content with UTF-8 charset (value 'text/plain; charset=UTF-8').
        HTML (str): HTML content with UTF-8 charset (value 'text/html; charset=UTF-8').
        MULTIPART (str): Mixed content, usually for emails with attachments (value 'multipart/mixed').
    """

    PLAIN = "text/plain; charset=UTF-8"
    HTML = "text/html; charset=UTF-8"
    MULTIPART = "multipart/mixed"


class ContentTransferEncoding(StrEnum):
    """
    Enum for specifying the encoding used to transfer email content.

    Values:
        SEVEN_BIT (str): 7-bit encoding (value '7bit'). Default for simple text.
        BASE64 (str): Base64 encoding (value 'base64'). Used for attachments and binary data.
        QUOTED_PRINTABLE (str): Quoted-printable encoding (value 'quoted-printable'). Used for text with special characters.
    """

    SEVEN_BIT = "7bit"
    BASE64 = "base64"
    QUOTED_PRINTABLE = "quoted-printable"
