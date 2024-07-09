import pytest

from sage_imap.helpers.mailbox import DefaultMailboxes, MailboxStatusItems


def test_default_mailboxes_enum():
    assert DefaultMailboxes.INBOX == "INBOX"
    assert DefaultMailboxes.SENT == "Sent"
    assert DefaultMailboxes.DRAFTS == "Drafts"
    assert DefaultMailboxes.TRASH == "Trash"
    assert DefaultMailboxes.SPAM == "Spam"
    assert DefaultMailboxes.ARCHIVE == "Archive"


def test_mailbox_status_items_enum():
    assert MailboxStatusItems.MESSAGES == "MESSAGES"
    assert MailboxStatusItems.RECENT == "RECENT"
    assert MailboxStatusItems.UIDNEXT == "UIDNEXT"
    assert MailboxStatusItems.UIDVALIDITY == "UIDVALIDITY"
    assert MailboxStatusItems.UNSEEN == "UNSEEN"
