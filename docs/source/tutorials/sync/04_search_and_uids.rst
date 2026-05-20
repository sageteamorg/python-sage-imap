Lesson 4 — Search and stable message identity (UIDs)
====================================================

Goal
----

Find messages with expressive criteria and convert results into a :class:`~sage_imap.models.message.MessageSet` for later fetch or flag updates.

Why UID SEARCH?
---------------

After you search, you might fetch, mark read, or move messages. If someone sends mail while your script runs, **sequence numbers shift** but **UIDs stay valid** for messages still in the folder. Always prefer:

.. code-block:: python

   result = session.search(criteria)          # UID SEARCH via session
   msg_set = result.to_uid_message_set()

Step 1 — Common searches
------------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")

       unread = session.search(IMAPSearchCriteria.UNSEEN)
       print("Unread:", unread.message_count)

       from_boss = session.search(
           IMAPSearchCriteria.from_address("boss@company.com")
       )
       print("From boss:", from_boss.message_count)

       recent_subject = session.search(
           IMAPSearchCriteria.and_criteria(
               IMAPSearchCriteria.since("01-Jan-2025"),
               IMAPSearchCriteria.subject("invoice"),
           )
       )
       print("Invoices since Jan 2025:", recent_subject.message_count)

Step 2 — Turn results into a MessageSet
---------------------------------------

.. code-block:: python

   result = session.search(IMAPSearchCriteria.UNSEEN)
   if result.success and result.message_count:
       msg_set = result.to_uid_message_set()
       print("First UID:", msg_set.parsed_ids[0])
       print("Total UIDs:", len(msg_set.parsed_ids))
   else:
       print("Nothing to do.")

Step 3 — Empty results are normal
---------------------------------

.. code-block:: python

   msg_set = result.to_uid_message_set()
   if msg_set.is_empty():
       print("No matching messages.")
       return

.. tip::

   Treat “zero results” as success, not an error. Many cron jobs exit quietly when there is nothing new.

Step 4 — Combine criteria carefully
-----------------------------------

- **AND** — all conditions must match.
- **OR** — any condition matches.
- Dates use IMAP format: ``01-Jan-2025``.

Full reference: :doc:`../../getting_started/search`.

Charset and older servers
-------------------------

By default, ``session.search(...)`` does **not** send ``CHARSET UTF-8`` — only plain ASCII criteria like ``ALL`` or ``UNSEEN``. Many servers (including some cPanel/Dovecot setups) reject ``CHARSET`` entirely.

If you search non-ASCII text (for example a subject in Persian), pass charset explicitly **only when** your server supports it:

.. code-block:: python

   result = session.search(
       IMAPSearchCriteria.subject("فاکتور"),
       charset="UTF-8",
   )

The transport layer can also pick ``UTF-8`` automatically when the criteria string contains non-ASCII characters and you leave ``charset=None``.

.. tip::

   If you see ``Unknown argument UTF-8`` in a SEARCH error, remove ``charset="UTF-8"`` or upgrade to a library version that defaults to ``charset=None``.

Step 5 — Manual MessageSet (advanced)
---------------------------------------

When you already know UIDs (from a saved file or database):

.. code-block:: python

   from sage_imap.models.message import MessageSet

   msg_set = MessageSet.from_uids([101, 102, 205], mailbox="INBOX")

Exercise
--------

1. Search unread messages from the last 7 days (hint: ``since()``).
2. Print how many match; if any, print the first three UIDs only.

Next: :doc:`05_read_messages`
