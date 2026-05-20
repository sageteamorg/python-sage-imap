Lesson 5 — Read messages (async)
================================

Goal
----

Stream parsed messages with ``async for`` and batched UID FETCH.

Compared to sync
~~~~~~~~~~~~~~~~

+----------------------------+----------------------------------------+
| Sync                       | Async                                  |
+============================+========================================+
| ``for msg in session.iter_messages(...)`` | ``async for msg in session.iter_messages(...)`` |
+----------------------------+----------------------------------------+

Example — unread digest (headers only)
--------------------------------------

.. code-block:: python

   import asyncio

   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.helpers.parse_mode import ParseMode
   from sage_imap.helpers.search import IMAPSearchCriteria

   async def main() -> None:
       async with AsyncIMAPSession(host, user, password) as session:
           await session.select("INBOX")
           result = await session.search(IMAPSearchCriteria.UNSEEN)
           msg_set = result.to_uid_message_set()
           if msg_set.is_empty():
               print("No unread mail.")
               return

           count = 0
           async for msg in session.iter_messages(
               msg_set,
               parse_mode=ParseMode.HEADERS,
               batch_size=25,
           ):
               count += 1
               print(msg.uid, msg.subject)
           print(f"Listed {count} messages")

   asyncio.run(main())

Tips
----

- **``batch_size``** — same trade-off as sync (round trips vs memory).
- **Other asyncio tasks** — while ``await`` waits on IMAP, your loop can progress other coroutines *in the same process* (not on the same IMAP connection).
- Start with ``HEADERS``; use ``ParseMode.FULL`` only when needed.

Next: :doc:`06_flags_and_actions`
