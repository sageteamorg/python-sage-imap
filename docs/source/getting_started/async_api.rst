.. _async_api:

Async IMAP (v2)
===============

Python Sage IMAP provides a first-class async API under **``sage_imap.aio``**, backed by
`aioimaplib <https://github.com/bamthoor/aioimaplib>`_.

Install
-------

.. code-block:: bash

   pip install python-sage-imap[async]

The core package stays stdlib-only; the ``[async]`` extra adds ``aioimaplib`` and ``httpx``
(for OAuth token refresh).

Quick start
-----------

.. code-block:: python

   import asyncio
   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.helpers.search import IMAPSearchCriteria

   async def main():
       async with AsyncIMAPSession(
           "imap.example.com", "user@example.com", "secret"
       ) as session:
           await session.select("INBOX")
           result = await session.search(IMAPSearchCriteria.UNSEEN)
           async for msg in session.iter_messages(result.to_uid_message_set()):
               print(msg.subject)

   asyncio.run(main())

For a full lesson path with sync comparisons, see :doc:`../tutorials/async/index`.

Sync vs async
-------------

+------------------+-----------------------------+----------------------------------+
| Concern          | Sync                        | Async                            |
+==================+=============================+==================================+
| Entry            | ``IMAPSession``             | ``AsyncIMAPSession``             |
+------------------+-----------------------------+----------------------------------+
| Transport        | ``imaplib`` + ``RLock``     | ``aioimaplib`` + ``asyncio.Lock``|
+------------------+-----------------------------+----------------------------------+
| OAuth refresh    | stdlib                      | ``httpx`` (or thread fallback)   |
+------------------+-----------------------------+----------------------------------+

Async is **not** exported from top-level ``sage_imap``; import ``sage_imap.aio`` explicitly.

One connection per task
-----------------------

A single IMAP connection supports one command stream. Commands on
:class:`~sage_imap.aio.transport.AsyncIMAPTransport` are serialized with an
``asyncio.Lock`` — do not assume parallel commands on one client without understanding
this constraint.

IDLE
----

.. code-block:: python

   from sage_imap.aio.idle import AsyncIMAPIdleSession

   async with AsyncIMAPIdleSession(client, "INBOX") as idle:
       result = await idle.wait(timeout=120.0)
       for event in result.events:
           print(event.event_type, event.sequence)

See also :doc:`migration_v2`.
