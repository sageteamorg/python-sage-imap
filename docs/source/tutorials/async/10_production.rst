Lesson 10 — Production playbook (async)
========================================

Goal
----

Run asyncio mailbox jobs safely at scale.

Error handling
--------------

Same exception types as sync (:class:`~sage_imap.exceptions.IMAPConnectionError`, etc.). Wrap ``asyncio.run(main())`` at the top level:

.. code-block:: python

   import asyncio
   import logging

   logging.basicConfig(level=logging.INFO)

   def main_entry() -> None:
       try:
           asyncio.run(sync_inbox())
       except KeyboardInterrupt:
           pass

Concurrency rules
-----------------

+-----------------------------+--------------------------------------------------+
| Rule                        | Why                                              |
+=============================+==================================================+
| One command stream per client | Transport lock serializes IMAP                   |
| Multiple mailboxes          | Use multiple ``AsyncIMAPSession`` instances        |
| Do not share one client     | Race conditions and protocol errors              |
| ``gather`` on one session   | Commands still run one-at-a-time — no speedup    |
+-----------------------------+--------------------------------------------------+

.. important::

   ``asyncio.gather(fetch1, fetch2)`` on the **same** session does not parallelize IMAP. Use separate sessions (separate logins) if you truly need parallel throughput.

Performance
-----------

Same checklist as :doc:`../sync/10_production`:

- Search before full body fetch
- Tune ``batch_size``
- Prefer CONDSTORE over full scans
- ``ParseMode.HEADERS`` for listings

Graceful shutdown
-----------------

.. code-block:: python

   async with AsyncIMAPSession(host, user, password) as session:
       try:
           await work(session)
       finally:
           pass  # __aexit__ closes mailbox and disconnects

Choosing sync vs async (summary)
--------------------------------

+---------------------------+---------------------------+
| Stay on sync              | Prefer async              |
+===========================+===========================+
| Cron script once per hour | Bot + HTTP API same process|
| Learning IMAP basics      | Already using FastAPI/aiohttp|
| Minimal dependencies      | IDLE + other I/O together |
+---------------------------+---------------------------+

You finished both tracks when you can explain **UID workflow**, **auth**, **incremental sync**, and **when async helps** — not just syntax differences.

Reference: :doc:`../../getting_started/async_api`, :doc:`../../getting_started/best_practices`.
