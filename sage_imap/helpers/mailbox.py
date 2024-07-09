from enum import StrEnum


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
