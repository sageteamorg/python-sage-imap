import logging
from enum import StrEnum

logger = logging.getLogger(__name__)


class Flags(StrEnum):
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
