Lesson 2 — Install and your first ORM query
===========================================

Goal
----

Install the ORM extra, open an ``ImapORM`` session, select INBOX, and print unread subjects.

Step 1 — Install
----------------

.. code-block:: bash

   pip install python-sage-imap[orm]

If you use Poetry in this repository:

.. code-block:: bash

   poetry install -E orm

Step 2 — Account configuration
------------------------------

``ImapAccountConfig`` describes **one mailbox account** in your app (often one row in your user table):

.. code-block:: python

   import os
   from sage_imap.orm import ImapAccountConfig

   config = ImapAccountConfig(
       account_id="user-42",          # your tenant / user id
       host=os.environ["IMAP_HOST"],
       username=os.environ["IMAP_USER"],
       password=os.environ["IMAP_PASSWORD"],
       port=993,
       use_ssl=True,
   )

``account_id`` is copied onto every ``ImapMessage`` and schema so APIs never confuse tenants.

Step 3 — Open the ORM and select INBOX
--------------------------------------

.. code-block:: python

   from sage_imap.orm import ImapMessage, ImapORM

   with ImapORM.open("user-42", config=config) as orm:
       orm.select_mailbox("INBOX")
       qs = ImapMessage.objects.filter(unread=True).limit(10)
       for msg in qs.iter():
           print(msg.uid, msg.subject or "(no subject)")

Important details:

- **``ImapORM.open(account_id, config=...)``** — ``account_id`` must match ``config.account_id`` when you pass both.
- **``select_mailbox``** — required before message querysets run; raises if the mailbox is missing.
- **``iter()``** — executes SEARCH + FETCH; the queryset alone does not hit the network.

Step 4 — Count without fetching bodies
--------------------------------------

.. code-block:: python

   with ImapORM.open("user-42", config=config) as orm:
       orm.select_mailbox("INBOX")
       n = ImapMessage.objects.filter(unread=True).count()
       print(f"{n} unread messages")

``count()`` runs UID SEARCH only — useful for dashboards.

Step 5 — List folders
---------------------

.. code-block:: python

   from sage_imap.orm import ImapFolder

   with ImapORM.open("user-42", config=config) as orm:
       for folder in ImapFolder.objects.list():
           print(folder.name, folder.attributes)

Use ``ImapFolder.objects.get("INBOX", enrich=True)`` for status (message/unseen counts) when the server supports it.

Troubleshooting
---------------

+-------------------------------+------------------------------------------+
| Symptom                       | Fix                                      |
+===============================+==========================================+
| ``ImportError: [orm] extra``  | ``pip install python-sage-imap[orm]``    |
| ``OrmMailboxNotSelectedError``| Call ``orm.select_mailbox(...)`` first   |
| ``OrmNotConnectedError``      | Use code inside ``with ImapORM.open()``  |
| Login fails                   | App password, OAuth, or host/port        |
+-------------------------------+------------------------------------------+

Runnable script: ``examples/10_orm_sync.py``.

Next: :doc:`03_filters_and_querysets`
