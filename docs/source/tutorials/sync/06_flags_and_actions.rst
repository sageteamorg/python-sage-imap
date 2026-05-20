Lesson 6 — Flags, move, copy, and delete
========================================

Goal
----

Change mailbox state: mark read/unread, flag important, move to another folder, and delete safely.

Flags — read, starred, deleted
------------------------------

Use ``session.flags`` after selecting the mailbox:

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.UNSEEN)
       msg_set = result.to_uid_message_set()
       if msg_set.is_empty():
           return

       # Mark first batch as read
       session.flags.mark_as_read(msg_set)
       print("Marked as read:", len(msg_set.msg_ids))

Convenience methods include ``mark_as_unread``, ``mark_as_important``, ``mark_as_deleted``.

.. tip::

   “Read” in webmail = ``\Seen`` flag on the server. Your script and your phone stay in sync because both talk to the same IMAP store.

Move and copy
-------------

Operations go through ``session.mailbox`` (UID-aware service):

.. code-block:: python

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       result = session.search(IMAPSearchCriteria.from_address("newsletter@example.com"))
       msg_set = result.to_uid_message_set()
       if msg_set.is_empty():
           return

       move_result = session.mailbox.uid_move(msg_set, "Archive")
       if move_result.success:
           print(f"Moved {move_result.message_count} messages.")
       else:
           print("Move failed:", move_result.error_message)

Use the **exact destination folder name** from ``session.folders.list_folders()``.

Delete (trash then expunge)
---------------------------

Permanent delete typically moves to Trash then expunges. Use mailbox helpers and resolve Trash via SPECIAL-USE (lesson 7):

.. code-block:: python

   from sage_imap import IMAPSession, SpecialUse

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       trash = session.special_folder(SpecialUse.TRASH)
       if not trash:
           raise RuntimeError("Could not find Trash folder")

       result = session.search(IMAPSearchCriteria.DELETED)
       msg_set = result.to_uid_message_set()
       if not msg_set.is_empty():
           session.mailbox.delete(msg_set, trash)

.. important::

   Deleting mail is irreversible on many providers once expunged. Test on a single UID first.

Workflow pattern
----------------

A robust automation loop:

1. ``select`` mailbox
2. ``search`` → ``to_uid_message_set()``
3. ``iter_messages`` to inspect (optional)
4. ``flags`` / ``mailbox.move`` / ``mailbox.delete``
5. Log ``MailboxOperationResult.success``

Exercise
--------

1. Find unread messages older than 30 days (search + date).
2. Move them to ``Archive`` (or a folder you create in lesson 7).
3. Mark them read.

Next: :doc:`07_folders_and_special_use`
