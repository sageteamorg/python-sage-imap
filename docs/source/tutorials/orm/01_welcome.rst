Lesson 1 — Welcome: IMAP without SQL
====================================

Goal
----

Understand what the IMAP ORM is, what it is **not**, and when it helps your application.

What the ORM is
---------------

``sage_imap.orm`` is a thin, explicit layer on top of the same UID-first session API you already use:

.. code-block:: text

   [ Your app ]  →  ImapORM / managers  →  IMAPSession  →  [ IMAP server ]

- **Managers** — ``ImapMessage.objects``, ``ImapFolder.objects``, ``SyncCheckpoint.objects``
- **Querysets** — chain ``filter()``, ``limit()``, ``iter()`` before any network I/O runs
- **Entities** — ``ImapMessage``, ``ImapFolder`` carry ``account_id`` and ``mailbox`` for multi-tenant apps

There is **no ORM migration**, **no tables**, and **no lazy SQL**. Each queryset compiles to IMAP ``SEARCH`` criteria, resolves UIDs, then ``FETCH``es in batches (default 50).

What it is not
--------------

+---------------------------+--------------------------------+
| Myth                      | Reality                        |
+===========================+================================+
| "ORM = database"          | Data stays on the mail server  |
| "filter hits the DB"      | ``filter()`` only builds criteria|
| "save() persists rows"    | Use ``mark_seen()``, ``move_to()``|
| "Works offline"           | Requires a live IMAP connection|
+---------------------------+--------------------------------+

ORM vs ``IMAPSession``
----------------------

+------------------+---------------------------+---------------------------+
|                  | ``IMAPSession``           | ``ImapORM``               |
+==================+===========================+===========================+
| Style            | Explicit service calls    | Manager/queryset chains   |
| Dependencies     | Core package only         | ``[orm]`` extra (Pydantic)|
| Multi-tenant     | You wire accounts         | Built-in ``account_id``   |
| JSON APIs        | Manual dict building      | Pydantic schemas          |
| Best for         | Scripts, fine control     | Apps, SaaS mail features  |
+------------------+---------------------------+---------------------------+

You can mix both: open ``ImapORM`` with an existing ``IMAPSession`` when you need shared connection logic.

Install (preview)
-----------------

.. code-block:: bash

   pip install python-sage-imap[orm]

Async ORM (lesson 8):

.. code-block:: bash

   pip install python-sage-imap[orm,async]

Smallest working example
------------------------

.. code-block:: python

   from sage_imap.orm import ImapAccountConfig, ImapMessage, ImapORM

   config = ImapAccountConfig(
       account_id="demo",
       host="imap.example.com",
       username="you@example.com",
       password="secret",
   )

   with ImapORM.open("demo", config=config) as orm:
       orm.select_mailbox("INBOX")
       for msg in ImapMessage.objects.filter(unread=True).limit(5).iter():
           print(msg.uid, msg.subject)

``ImapORM.open()`` connects (unless you pass an existing session), sets the active ORM context, and tears down on exit — similar to ``with IMAPSession(...)``.

Checklist before lesson 2
-------------------------

- [ ] ``python-sage-imap[orm]`` installed
- [ ] IMAP host, username, and password (or app password) ready
- [ ] Credentials in environment variables, not committed to git

Next: :doc:`02_install_and_connect`
