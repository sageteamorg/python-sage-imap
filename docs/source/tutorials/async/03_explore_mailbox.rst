Lesson 3 — Explore folders (async)
==================================

Goal
----

List folders and read STATUS using async service calls.

Concepts match :doc:`../sync/03_explore_mailbox`. Only syntax changes.

List folders
------------

.. code-block:: python

   import asyncio
   from sage_imap.aio import AsyncIMAPSession

   async def main() -> None:
       async with AsyncIMAPSession(host, user, password) as session:
           folders = await session.folders.list_folders()
           for info in folders[:20]:
               print(info.name)

Compared to sync
~~~~~~~~~~~~~~~~

- Sync: ``session.folders.list_folders()`` (blocking)
- Async: ``await session.folders.list_folders()`` — if the folder service exposes async methods; when using session-level sync wrappers on aio mailbox, use the async session’s folder service consistently.

.. note::

   Folder listing on ``AsyncIMAPFolderService`` follows the same patterns as sync; **await** any method that performs I/O.

Select and status
-----------------

.. code-block:: python

   async with AsyncIMAPSession(host, user, password) as session:
       from sage_imap.helpers.search import IMAPSearchCriteria

       sel = await session.select("INBOX")
       print("Messages:", sel.message_count)
       unread = await session.search(IMAPSearchCriteria.UNSEEN)
       print("Unseen:", unread.message_count)

Switch mailboxes in one session
-------------------------------

.. code-block:: python

   async with AsyncIMAPSession(host, user, password) as session:
       for mailbox in ("INBOX", "Archive"):
           result = await session.select(mailbox)
           if not result.success:
               continue
           sel = await session.select(mailbox)
           print(mailbox, sel.message_count)

Next: :doc:`04_search_and_uids`
