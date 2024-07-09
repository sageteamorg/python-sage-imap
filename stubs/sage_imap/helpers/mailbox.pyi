from enum import StrEnum

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
