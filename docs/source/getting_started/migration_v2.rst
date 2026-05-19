.. _migration_v2:

Migrating to v2
===============

Version **2.0.0** adds ``sage_imap.aio`` and keeps the sync stack on ``imaplib``. There is
no breaking change to existing sync imports from ``sage_imap`` except the version bump.

What changed
------------

- **New:** ``sage_imap.aio`` — ``AsyncIMAPSession``, ``AsyncIMAPClient``, mailbox/folder/flag/sync/IDLE parity.
- **New:** Optional install extra ``[async]`` (``aioimaplib``, ``httpx``).
- **New:** Shared mailbox read-path in ``services/mailbox/_ops.py`` (UID search + batched fetch).
- **Unchanged:** Top-level exports — ``IMAPSession``, ``IMAPClient``, ``IMAPMailboxUIDService``, etc.

Recommended practices
---------------------

1. Prefer :class:`~sage_imap.session.IMAPSession` for new sync code.
2. Use **UID** operations (``uid_search``, ``iter_uid_fetch``) rather than sequence numbers.
3. For asyncio apps, use ``AsyncIMAPSession`` instead of wrapping sync calls in executors.
4. Install ``python-sage-imap[async]`` only when you need ``sage_imap.aio``.

From 1.x patterns
-----------------

**Old (manual services):**

.. code-block:: python

   from sage_imap.services import IMAPClient, IMAPMailboxService
   with IMAPClient(host, user, password) as client:
       with IMAPMailboxService(client) as mb:
           mb.select("INBOX")
           result = mb.search(...)

**New (session):**

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria
   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.ALL)

Further reading in the repository: ``docs/MIGRATION_v2.md``, ``docs/ASYNC.md``, ``CHANGELOG.md``.
