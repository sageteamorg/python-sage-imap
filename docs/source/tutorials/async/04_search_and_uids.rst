Lesson 4 — Search and UIDs (async)
==================================

Goal
----

Run UID SEARCH asynchronously and build a ``MessageSet``.

Same rules as :doc:`../sync/04_search_and_uids` — always ``to_uid_message_set()``.

Example
-------

.. code-block:: python

   import asyncio

   from sage_imap.aio import AsyncIMAPSession
   from sage_imap.helpers.search import IMAPSearchCriteria

   async def main() -> None:
       async with AsyncIMAPSession(host, user, password) as session:
           await session.select("INBOX")

           unread = await session.search(IMAPSearchCriteria.UNSEEN)
           print("Unread:", unread.message_count)

           msg_set = unread.to_uid_message_set()
           if msg_set.is_empty():
               return
           print("First UID:", msg_set.msg_ids[0])

   asyncio.run(main())

Compared to sync
~~~~~~~~~~~~~~~~

Every ``session.search`` becomes ``await session.search``. Result objects (``message_count``, ``success``, ``to_uid_message_set()``) are identical.

Complex criteria
----------------

.. code-block:: python

   result = await session.search(
       IMAPSearchCriteria.and_criteria(
           IMAPSearchCriteria.since("01-Jan-2025"),
           IMAPSearchCriteria.subject("invoice"),
       )
   )

Reference: :doc:`../../getting_started/search`.

Charset
-------

Same as the sync lesson: leave ``charset`` unset for ``ALL`` / ``UNSEEN``. Only pass ``charset="UTF-8"`` when searching non-ASCII text and your server supports SEARCH CHARSET.

Next: :doc:`05_read_messages`
