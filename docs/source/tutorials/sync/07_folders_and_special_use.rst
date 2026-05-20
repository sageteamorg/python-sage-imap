Lesson 7 — Folders and SPECIAL-USE mailboxes
============================================

Goal
----

Find standard folders (Trash, Sent, Drafts) without hard-coding provider-specific names, and perform basic folder lifecycle operations.

SPECIAL-USE — stop guessing folder names
----------------------------------------

Gmail uses ``[Gmail]/Trash``; another host might use ``Deleted Items``. Use :class:`~sage_imap.helpers.special_use.SpecialUse`:

.. code-block:: python

   from sage_imap import IMAPSession, SpecialUse

   with IMAPSession(host, user, password) as session:
       trash = session.special_folder(SpecialUse.TRASH)
       sent = session.special_folder(SpecialUse.SENT)
       drafts = session.special_folder(SpecialUse.DRAFTS)

       print("Trash:", trash)
       print("Sent:", sent)

Or via folder service:

.. code-block:: python

   info = session.folders.find_by_special_use(SpecialUse.SENT)
   if info:
       print("Sent folder:", info.name)

.. tip::

   Cache folder names once per run — they rarely change. Do not embed ``"[Gmail]/Sent Mail"`` in source if you can avoid it.

Create, rename, delete folders
------------------------------

.. code-block:: python

   with IMAPSession(host, user, password) as session:
       # Names depend on server namespace — often simple names work:
       session.folders.create_folder("Projects/2025")
       session.folders.rename_folder("Projects/2025", "Projects/2026")
       # session.folders.delete_folder("Projects/old")  # careful!

Namespaces (shared / personal)
--------------------------------

Some servers expose multiple namespaces (personal vs shared):

.. code-block:: python

   ns = session.namespace()
   print(ns.personal, ns.other)

Useful when you see duplicate folder trees.

Move mail to Trash the portable way
-----------------------------------

.. code-block:: python

   from sage_imap import IMAPSession, IMAPSearchCriteria, SpecialUse

   with IMAPSession(host, user, password) as session:
       session.select("INBOX")
       trash = session.special_folder(SpecialUse.TRASH)
       if not trash:
           raise RuntimeError("Trash not advertised")

       spam = session.search(IMAPSearchCriteria.from_address("spam@example.com"))
       msg_set = spam.to_uid_message_set()
       if not msg_set.is_empty():
           session.mailbox.move(msg_set, trash)

Exercise
--------

1. Print all SPECIAL-USE folders your account exposes.
2. Create a folder ``Tutorial/Test`` and move one message into it.

Next: :doc:`08_auth_providers`
