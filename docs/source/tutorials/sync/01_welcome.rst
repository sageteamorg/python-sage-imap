Lesson 1 — Welcome: your mailbox without a backend
====================================================

Goal
----

By the end of this lesson you will understand **what you are building** and why Python Sage IMAP fits beginners who do not run a server.

What “no backend” means here
----------------------------

Many tutorials assume you already have:

- A web API
- A database
- User accounts you manage

**You do not need any of that** to read your own email. Your email provider (Gmail, Outlook, Fastmail, your host) already stores messages. IMAP is the protocol that lets a program talk to that storage — the same way a phone mail app does.

Your script is a **client**, not a server:

.. code-block:: text

   [ Your Python script ]  ----IMAP (TLS)---->  [ Provider mail server ]

That is enough to:

- List folders (Inbox, Sent, …)
- Search for unread mail
- Download subjects and bodies
- Mark messages read or move them to Trash

Webmail vs IMAP (mental model)
------------------------------

+------------------+---------------------------+---------------------------+
|                  | Web browser               | Your Python script        |
+==================+===========================+===========================+
| You open         | gmail.com                 | ``IMAPSession(...)``      |
| Login            | Google’s website          | Username + app password   |
| “Show unread”    | Click UI filter           | ``search(UNSEEN)``        |
| Read a message   | Click message             | ``iter_messages(...)``    |
+------------------+---------------------------+---------------------------+

.. tip::

   If you can log in to webmail, you can automate the same mailbox — you just need **IMAP enabled** and the correct host name (for example ``imap.gmail.com``).

Why UIDs matter (preview)
-------------------------

IMAP has two ways to point at a message:

- **Sequence number** — position in the folder (1, 2, 3…). Changes when mail arrives or is deleted.
- **UID** — stable ID for that message **in that folder** until the folder is reset.

This library is built around **UIDs** so your search results still make sense after the mailbox changes. You will use UID search and UID fetch in every lesson.

The API you will use: ``IMAPSession``
-------------------------------------

Lower-level classes like ``IMAPClient`` exist for advanced control. For learning and most apps, use the session facade:

.. code-block:: python

   from sage_imap import IMAPSession

   with IMAPSession("imap.example.com", "you@example.com", "secret") as session:
       session.select("INBOX")
       # search, read, move, ...

``with`` ensures the connection closes even if your script crashes — like closing a file.

What you will build by lesson 10
--------------------------------

1. Connect and prove INBOX is reachable
2. Browse folders and counts
3. Find unread mail from a sender
4. Print subjects without downloading every attachment
5. Mark read / flag important / move to folder
6. Use Trash and Sent reliably (SPECIAL-USE)
7. Authenticate with Gmail or Microsoft securely
8. Sync only **changes** since last run (CONDSTORE)
9. Wait for new mail (IDLE)
10. Handle errors and large mailboxes like production code

Checklist before lesson 2
-------------------------

- [ ] Python 3.10+ installed
- [ ] An email account with IMAP access enabled
- [ ] Host, username, and password (or app password) ready
- [ ] Plan to store secrets in environment variables, not in git

Next: :doc:`02_setup_and_connect`
