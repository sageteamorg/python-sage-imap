"""Integration tests: connect, select, search."""

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.services.mailbox import IMAPMailboxUIDService


def test_connect_select_inbox(imap_client):
    with IMAPMailboxUIDService(imap_client) as mailbox:
        result = mailbox.select("INBOX")
        assert result.success


def test_uid_search(imap_client):
    with IMAPMailboxUIDService(imap_client) as mailbox:
        mailbox.select("INBOX")
        result = mailbox.uid_search(IMAPSearchCriteria.ALL)
        assert result.success
