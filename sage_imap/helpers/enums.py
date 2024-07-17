import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class Flag(StrEnum):
    """
    Enum representing different IMAP flags used to indicate the state of email messages.

    Purpose
    -------
    This enumeration defines standard IMAP flags that can be associated with email
    messages. These flags help in identifying the status and handling of emails within
    the mailbox.

    Attributes
    ----------
    SEEN : str
        The flag indicating that the message has been read.
    ANSWERED : str
        The flag indicating that the message has been answered.
    FLAGGED : str
        The flag indicating that the message is marked as important.
    DELETED : str
        The flag indicating that the message is marked for deletion.
    DRAFT : str
        The flag indicating that the message is a draft.
    RECENT : str
        The flag indicating that the message is recent.
    """

    SEEN = "\\Seen"
    ANSWERED = "\\Answered"
    FLAGGED = "\\Flagged"
    DELETED = "\\Deleted"
    DRAFT = "\\Draft"
    RECENT = "\\Recent"


class FlagCommand(StrEnum):
    """
    Enum representing commands to add or remove flags from email messages.

    Purpose
    -------
    This enumeration defines commands used to modify the flags associated with
    email messages.
    These commands are used in IMAP operations to update the state of messages.

    Attributes
    ----------
    ADD : str
        The command to add flags to a message.
    REMOVE : str
        The command to remove flags from a message.
    """

    ADD = "+FLAGS"
    REMOVE = "-FLAGS"


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


class DefaultMailboxes(StrEnum):
    """
    Enum representing default mailboxes in an email system.

    Purpose:
    This enumeration defines a set of standard mailboxes typically used in email clients
    and servers to organize emails. These predefined mailboxes help in categorizing
    emails based on their state or purpose.

    Attributes
    ----------
    INBOX : str
        The primary mailbox where incoming emails are delivered.
    SENT : str
        The mailbox containing emails that have been sent by the user.
    DRAFTS : str
        The mailbox containing email drafts that have been saved but not yet sent.
    TRASH : str
        The mailbox containing emails that have been deleted by the user.
    SPAM : str
        The mailbox containing emails identified as spam or junk.
    ARCHIVE : str
        The mailbox for storing emails that the user wants to keep but not in the
        primary inbox.

    Notes
    -----
    Using a standardized set of mailboxes ensures consistency in how emails are
    categorized and accessed across different email clients and services. It also
    simplifies the development of email handling features by providing a clear structure
    for organizing emails.
    """

    INBOX = "INBOX"
    SENT = "Sent"
    DRAFTS = "Drafts"
    TRASH = "Trash"
    SPAM = "Spam"
    ARCHIVE = "Archive"


class MailboxStatusItems(StrEnum):
    """
    Enum representing various status items of a mailbox in an email system.

    Purpose:
    This enumeration defines different status items that can be associated with a
    mailbox. These items provide important metadata about the state and contents of
    the mailbox, which is useful for email clients and servers to manage and display
    email information.

    Attributes
    ----------
    MESSAGES : str
        The number of messages in the mailbox.
    RECENT : str
        The number of messages with the \\Recent flag set, indicating they are newly
        arrived.
    UIDNEXT : str
        The next unique identifier (UID) value that will be assigned to a new message.
    UIDVALIDITY : str
        The unique identifier validity value, which changes if the mailbox is deleted
        and recreated.
    UNSEEN : str
        The number of messages which do not have the \\Seen flag set, indicating they
        are unread.

    Notes
    -----
    These status items provide essential information for managing and interacting with
    a mailbox. They help email clients to display the current state of a mailbox, such
    as the number of unread messages, and assist in the efficient handling of email
    operations, such as fetching new messages or maintaining the integrity of unique
    identifiers.
    """

    MESSAGES = "MESSAGES"
    RECENT = "RECENT"
    UIDNEXT = "UIDNEXT"
    UIDVALIDITY = "UIDVALIDITY"
    UNSEEN = "UNSEEN"


class MessagePart(StrEnum):
    """
    Enum representing different parts of an email message to be fetched.

    Purpose
    -------
    This enumeration defines various parts of an email message that can be fetched using
    IMAP commands.These parts provide flexibility in retrieving specific information
    from an email without fetching the entire message.

    Attributes
    ----------
    RFC822 : str
        Fetches the entire raw email message.
    BODY : str
        Fetches the entire body of the message.
    BODY_TEXT : str
        Fetches the plain text portion of the message body.
    BODY_HEADER : str
        Fetches the header of the message.
    BODY_HEADER_FIELDS : str
        Fetches specific header fields (From, To, Subject, Date).
    FLAGS : str
        Fetches the flags associated with the message (e.g., \\Seen, \\Answered).
    MODSEQ : str
        Fetches the modification sequence of the message (useful for CONDSTORE).
    BODY_STRUCTURE : str
        Fetches the structure of the message body (e.g., MIME parts).
    BODY_PEEK : str
        Fetches the entire message without setting the \\Seen flag.
    BODY_PEEK_TEXT : str
        Fetches the plain text portion of the message body without setting the \\Seen
        flag.
    BODY_PEEK_HEADER : str
        Fetches the header of the message without setting the \\Seen flag.
    BODY_PEEK_HEADER_FIELDS : str
        Fetches specific header fields without setting the \\Seen flag.
    BODY_PEEK_ATTACHMENT : str
        Fetches the second part of the body (commonly used for attachments) without
        setting the \\Seen flag.
    """

    RFC822 = "RFC822"
    BODY = "BODY"
    BODY_TEXT = "BODY[TEXT]"
    BODY_HEADER = "BODY[HEADER]"
    BODY_HEADER_FIELDS = "BODY[HEADER.FIELDS (FROM TO SUBJECT DATE)]"
    FLAGS = "FLAGS"
    MODSEQ = "MODSEQ"
    BODY_STRUCTURE = "BODYSTRUCTURE"
    BODY_PEEK = "BODY.PEEK[]"
    BODY_PEEK_TEXT = "BODY.PEEK[TEXT]"
    BODY_PEEK_HEADER = "BODY.PEEK[HEADER]"
    BODY_PEEK_HEADER_FIELDS = "BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)]"
    BODY_PEEK_ATTACHMENT = "BODY.PEEK[2]"


class ThreadingAlgorithm(StrEnum):
    REFERENCES = "REFERENCES"
    ORDEREDSUBJECT = "ORDEREDSUBJECT"
    THREAD = "THREAD"
    SEQUENCE = "SEQUENCE"
