Lesson 9 — CONDSTORE sync and IDLE (async)
==========================================

Goal
----

Incrementally process mailbox changes and wait for push notifications without blocking the entire process.

Part A — CONDSTORE (async)
--------------------------

.. code-block:: python

   import asyncio

   from sage_imap.aio import AsyncIMAPSession

   async def main() -> None:
       async with AsyncIMAPSession(host, user, password) as session:
           await session.select("INBOX")
           state = await session.capture_sync_state("INBOX")

           changed = await session.find_changed_since(state)
           if changed.is_empty():
               print("No changes.")
           else:
               async for msg in session.iter_messages(changed, batch_size=50):
                   print(msg.uid, msg.subject)

           state = session.sync.apply_after_sync(state)  # sync helper — no I/O

   asyncio.run(main())

Compared to sync
~~~~~~~~~~~~~~~~

+-------------------------------------+--------------------------------------+
| Sync                                | Async                                |
+=====================================+======================================+
| ``state = session.capture_sync_state()`` | ``await session.capture_sync_state()`` |
| ``session.find_changed_since(state)``    | ``await session.find_changed_since(state)`` |
+-------------------------------------+--------------------------------------+

Persist ``state`` between process runs the same way as the sync lesson.

Part B — Async IDLE
-------------------

.. code-block:: python

   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.aio.idle import AsyncIMAPIdleSession

   async with AsyncIMAPSession(host, user, password) as session:
       await session.select("INBOX")
       async with AsyncIMAPIdleSession(session.client, "INBOX") as idle:
           result = await idle.wait(timeout=120.0)
           for event in result.events:
               print(event.event_type, event.sequence)

.. tip::

   IDLE holds the connection. In asyncio this is natural: other tasks can run **only if** they use **other** connections or do not share the locked transport.

When async shines
-----------------

Combine IDLE with other ``await`` work (timers, HTTP callbacks) in one process — sync IDLE would block the whole thread.

Next: :doc:`10_production`
