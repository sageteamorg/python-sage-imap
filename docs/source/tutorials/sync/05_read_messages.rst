Lesson 5 — Read messages efficiently
====================================

Goal
----

Download only what you need (headers vs full body), stream many messages in batches, and inspect parsed fields.

Parse modes
-----------

:class:`~sage_imap.helpers.parse_mode.ParseMode` controls how much data UID FETCH retrieves:

+------------------+------------------------------------------+
| Mode             | Use when                                 |
+==================+==========================================+
| ``HEADERS``      | Listing subjects, senders, dates         |
| ``FULL``         | Body text, attachments metadata          |
| (see API docs)   | Other modes for MIME-specific needs      |
+------------------+------------------------------------------+

.. tip::

   Start with ``HEADERS`` for dashboards and digests. Switch to ``FULL`` only for messages you will actually process.

Step 1 — Stream with ``iter_messages``
--------------------------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria, ParseMode
   from sage_imap.models.message import MessageSet

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.UNSEEN)
       msg_set = result.to_uid_message_set()
       if msg_set.is_empty():
           print("Inbox zero — nice work.")
       else:
           for msg in session.iter_messages(
               msg_set,
               parse_mode=ParseMode.HEADERS,
               batch_size=25,
           ):
               print(msg.uid, msg.subject, msg.from_address)

**``batch_size``** — number of messages fetched per IMAP round trip. Higher = fewer round trips, more memory.

Step 2 — Inspect a parsed message
---------------------------------

Each ``msg`` is an :class:`~sage_imap.models.email.EmailMessage`:

.. code-block:: python

   print(msg.date)
   print(msg.to_addresses)
   print(msg.has_attachments)  # when full parse was used

Step 3 — Limit work in large inboxes
------------------------------------

.. code-block:: python

   result = session.search(IMAPSearchCriteria.ALL)
   msg_set = result.to_uid_message_set()
   first_ten = MessageSet.from_uids(msg_set.parsed_ids[:10], mailbox="INBOX")

   for msg in session.iter_messages(first_ten, parse_mode=ParseMode.HEADERS):
       print(msg.subject)

.. note::

   For slicing patterns (ranges, sampling), see :doc:`../../getting_started/message_set`.

Step 4 — Check fetch failures
-----------------------------

If the server returns partial data, rely on ``result.success`` at search time and validate ``msg.uid`` is present before acting on a message.

Tips
----

- **Do not fetch ALL + FULL** on a 50k mailbox in one run — filter with search first.
- **Encoding** — subjects may be MIME-encoded; the parser normalizes common cases.
- **Attachments** — detecting attachments usually requires ``ParseMode.FULL``.

Exercise
--------

Build a “daily digest” script: unread in INBOX, print subject + from + date, headers only, max 20 messages.

Next: :doc:`06_flags_and_actions`
