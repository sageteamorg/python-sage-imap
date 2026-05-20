Tutorials
=========

These tutorials teach you how to work with a real mailbox using Python — **no web server, no database, no backend framework required**. You only need Python, your email provider's IMAP settings, and this library.

Two parallel tracks
-------------------

Choose one path based on how you want your program to run:

.. list-table::
   :header-rows: 1
   :widths: 20 40 40

   * - Track
     - Best for
     - Entry point
   * - :doc:`sync/index`
     - Scripts, cron jobs, notebooks, CLI tools, beginners
     - ``IMAPSession`` (blocking, familiar ``with`` syntax)
   * - :doc:`async/index`
     - asyncio apps, bots, services that also do network I/O
     - ``AsyncIMAPSession`` (``async with``, ``await``, ``async for``)

Both tracks cover the **same mailbox skills** in the same order. The async track explains what changes at each step so you can compare with sync.

IMAP ORM track (optional)
-------------------------

If you build multi-tenant apps or JSON APIs on top of mail, follow :doc:`orm/index` after you understand basic IMAP (sync lesson 2+ is enough). Requires ``pip install python-sage-imap[orm]``.

Course map (sync / async tracks)
------------------------

+--------+-----------------------------+------------------------------------------+
| Step   | Topic                       | You will be able to                      |
+========+=============================+==========================================+
| 1      | Welcome & mental model      | Explain IMAP vs "logging into webmail"   |
| 2      | Setup & first connection    | Connect safely and list INBOX size         |
| 3      | Explore folders             | List folders, select mailboxes, read status|
| 4      | Search & UIDs               | Find mail reliably with UID SEARCH         |
| 5      | Read messages               | Stream headers or full bodies in batches   |
| 6      | Flags & actions             | Mark read, star, move, copy, delete        |
| 7      | Folders & SPECIAL-USE       | Trash, Sent, create/rename folders         |
| 8      | Providers & OAuth           | Gmail, Outlook, app passwords, OAuth2      |
| 9      | Sync & live mail            | CONDSTORE incremental sync, IDLE           |
| 10     | Production playbook         | Errors, scale, security checklist          |
+--------+-----------------------------+------------------------------------------+

Before you start
----------------

1. Read :doc:`../getting_started/installation` if you have not installed the package yet.
2. Skim :doc:`../getting_started/what_is_imap` if IMAP terminology is new to you.
3. Keep credentials out of source code — use environment variables or a ``.env`` file that is **not** committed to git.

Reference material (not part of the tutorial sequence)
------------------------------------------------------

Use these pages while you learn or after you finish a track:

- :doc:`../getting_started/search` — full search criteria reference
- :doc:`../getting_started/message_set` — ``MessageSet`` ranges and batching
- :doc:`../getting_started/headers` — header parsing details
- :doc:`../getting_started/best_practices` — production conventions
- :doc:`../troubleshooting` — when something fails

.. toctree::
   :maxdepth: 2
   :caption: Tutorial tracks

   sync/index
   async/index
   orm/index
