Lesson 3 — Explore folders and mailbox status
=============================================

Goal
----

List folders on the server, select different mailboxes, and read counts (total, unseen) without downloading bodies.

Step 1 — List folders
---------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria

   with IMAPSession(host, user, password) as session:
       folders = session.folders.list_folders()
       for info in folders[:20]:  # preview first 20
           print(info.name, info.delimiter, info.attributes)

.. note::

   Folder names may be encoded (for example ``INBOX``, ``[Gmail]/Sent Mail``). Always use the **exact** name returned when you ``select()``.

.. tip::

   If ``list_folders()`` fails with ``Invalid pattern`` on an older server, upgrade to the latest library build (empty LIST reference is sent as ``""`` per RFC 3501). You can also list one folder with ``get_folder_info("INBOX")``.

``FolderInfo.attributes`` holds LIST flags such as ``\\HasNoChildren`` and ``\\Noselect`` (not a field named ``flags``).

Step 2 — Select a mailbox and read STATUS
-----------------------------------------

``select()`` must run before search/fetch in that mailbox:

.. code-block:: python

   with IMAPSession(host, user, password) as session:
       result = session.select("INBOX")
       print("Total messages (from SELECT):", result.message_count)

       unread = session.search(IMAPSearchCriteria.UNSEEN)
       print("Unseen:", unread.message_count)

Import ``IMAPSearchCriteria`` at the top. SELECT gives the live count; UID SEARCH for ``UNSEEN`` is the portable way to count unread without parsing STATUS responses.

Step 3 — Switch folders in one session
--------------------------------------

.. code-block:: python

   with IMAPSession(host, user, password) as session:
       for mailbox in ("INBOX", "Archive"):
           try:
               session.select(mailbox)
           except Exception as exc:
               print(f"Skipping {mailbox}: {exc}")
               continue
           sel = session.select(mailbox)
           print(mailbox, "→", sel.message_count, "messages")

.. tip::

   One ``IMAPSession`` = one connection. You can visit many folders sequentially; you do not need a new login per folder.

Step 4 — Check the select result
--------------------------------

``select()`` returns :class:`~sage_imap.services.mailbox.models.MailboxOperationResult`:

.. code-block:: python

   result = session.select("INBOX")
   if not result.success:
       print("Select failed:", result.error_message)
   else:
       print("Selected; message count:", result.message_count)

Tips
----

- **INBOX is special** — it exists on virtually every account; good default for scripts.
- **Hierarchy** — nested folders use a delimiter (often ``/``). The library’s folder list helpers understand tree structures; see :doc:`../../getting_started/features`.
- **Read-only vs read-write** — some folders may be read-only; move/delete will fail there.

Exercise
--------

Write a script that prints a table: folder name, total messages, unseen count (skip folders you cannot open).

Next: :doc:`04_search_and_uids`
