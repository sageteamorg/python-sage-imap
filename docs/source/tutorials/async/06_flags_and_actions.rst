Lesson 6 — Flags and mailbox actions (async)
============================================

Goal
----

Mark messages read and move mail using async mailbox/flag services.

Flags
-----

.. code-block:: python

   async with AsyncIMAPSession(host, user, password) as session:
       await session.select("INBOX")
       result = await session.search(IMAPSearchCriteria.UNSEEN)
       msg_set = result.to_uid_message_set()
       if not msg_set.is_empty():
           from sage_imap.helpers.enums import Flag

           await session.flags.add_flag(msg_set, Flag.SEEN)

Compared to sync
~~~~~~~~~~~~~~~~

If the flag service method is async, **await** it. Convenience methods (``mark_as_read``, etc.) mirror the sync API on the async session’s ``flags`` property.

Move
----

.. code-block:: python

   async with AsyncIMAPSession(host, user, password) as session:
       await session.select("INBOX")
       result = await session.search(
           IMAPSearchCriteria.from_address("newsletter@example.com")
       )
       msg_set = result.to_uid_message_set()
       if msg_set.is_empty():
           return
       move_result = await session.mailbox.uid_move(msg_set, "Archive")
       if move_result.success:
           print("Moved", move_result.message_count)

Check ``MailboxOperationResult.success`` the same way as sync.

Delete
------

Resolve Trash with ``SpecialUse`` (see :doc:`../sync/07_folders_and_special_use`), then:

.. code-block:: python

   trash = await session.special_folder(SpecialUse.TRASH)
   await session.mailbox.uid_trash(msg_set, trash)

.. tip::

   When unsure whether a helper is sync or async, check the return type in your IDE or the API docs — await only coroutines.

Next: :doc:`07_folders_and_special_use`
