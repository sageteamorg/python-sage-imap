Lesson 5 — Pagination and message actions
=========================================

Goal
----

Page through large result sets with ``limit``/``offset``/``cursor``, then mark, move, or delete messages through entity methods.

Explicit pagination
-------------------

Unlike SQL OFFSET, IMAP has no server-side page index. The ORM applies pagination **after** UID SEARCH on the client:

.. code-block:: python

   page1 = ImapMessage.objects.filter(unread=True).limit(20).offset(0)
   page2 = ImapMessage.objects.filter(unread=True).limit(20).offset(20)

For infinite scroll, prefer **UID cursors** (stable when new mail arrives):

.. code-block:: python

   first = ImapMessage.objects.filter(unread=True).limit(20).fetch_all()
   last_uid = first[-1].uid if first else None

   if last_uid:
       next_page = (
           ImapMessage.objects.filter(unread=True)
           .cursor(after_uid=last_uid)
           .limit(20)
       )

``cursor(before_uid=...)`` returns UIDs strictly less than the given UID.

Batch size
----------

Control FETCH batching (default 50):

.. code-block:: python

   qs = ImapMessage.objects.filter(unread=True).limit(200)
   qs._batch_size = 25   # advanced; prefer keeping default unless profiling

Materialize once
----------------

.. code-block:: python

   messages = ImapMessage.objects.filter(unread=True).limit(10).fetch_all()

Async variant (lesson 8): ``await qs.fetch_all_async()``.

Per-message actions
-------------------

After you have ``ImapMessage`` instances with a loaded backend:

.. code-block:: python

   msg = ImapMessage.objects.get(uid=100)
   if msg:
       msg.mark_seen()
       msg.move_to("Archive")
       msg.delete(trash_folder="Trash")   # provider-specific trash name

Async counterparts: ``await msg.amark_seen()``, ``amove_to()``, ``adelete()``.

Bulk mark seen on a queryset
----------------------------

.. code-block:: python

   qs = ImapMessage.objects.filter(unread=True).limit(100)
   updated = qs.bulk_mark_seen()
   print(f"Marked {updated} as read")

This fetches messages (respecting ``LoadLevel``) then applies ``\\Seen`` per UID.

When actions fail
-----------------

- Ensure ``select_mailbox`` ran inside the same ``ImapORM.open()`` block.
- ``move_to`` / ``delete`` need valid folder names from ``ImapFolder.objects.list()``.
- Use SPECIAL-USE trash from the session API if the provider exposes it (see sync lesson 7).

Next: :doc:`06_multi_tenant`
