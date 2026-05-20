Lesson 3 — Filters, Q objects, and querysets
============================================

Goal
----

Build IMAP SEARCH criteria with keyword filters, ``Q`` composition, and raw criteria — then inspect what will be sent to the server.

Queryset basics
---------------

``ImapMessage.objects`` returns a **lazy** :class:`~sage_imap.orm.queryset.MessageQuerySet`. Methods return clones; nothing runs until you call ``iter()``, ``fetch_all()``, ``uids()``, or ``count()``.

.. code-block:: python

   qs = (
       ImapMessage.objects
       .filter(unread=True, from_address="alerts@bank.com")
       .limit(20)
   )
   for msg in qs.iter():
       ...

Keyword filters
---------------

These map to :class:`~sage_imap.helpers.search.IMAPSearchCriteria` helpers:

+------------------+----------------------------------+
| Keyword          | IMAP meaning                     |
+==================+==================================+
| ``unread=True``  | ``UNSEEN``                       |
| ``seen=True``    | ``SEEN``                         |
| ``flagged=True`` | ``FLAGGED``                      |
| ``from_address`` | ``FROM "..."``                   |
| ``subject``      | ``SUBJECT "..."``                |
| ``since``        | ``SINCE date``                   |
| ``recent_days``  | ``RECENT`` window                |
| ``uid``          | ``UID n`` or range               |
+------------------+----------------------------------+

Example — invoices this year:

.. code-block:: python

   qs = ImapMessage.objects.filter(
       subject="invoice",
       since="01-Jan-2025",
   )

``exclude()`` — negated filters
-------------------------------

.. code-block:: python

   qs = ImapMessage.objects.exclude(deleted=True)

Q objects — AND / OR / NOT
--------------------------

.. code-block:: python

   from sage_imap.orm import Q

   qs = ImapMessage.objects.filter(
       Q(unread=True) & Q(from_address="boss@company.com")
   )

   qs = ImapMessage.objects.filter(
       Q(seen=True) | Q(flagged=True)
   )

   qs = ImapMessage.objects.filter(~Q(draft=True))

``Q`` mirrors Django-style composition but compiles to IMAP SEARCH strings, not SQL.

Raw criteria
------------

When you already know the SEARCH string:

.. code-block:: python

   qs = ImapMessage.objects.raw_criteria('(SUBJECT "urgent" UNSEEN)')

Prefer keyword filters when possible — they handle quoting and charset rules consistently.

Inspect compiled criteria
-------------------------

.. code-block:: python

   criteria = qs.compile_criteria()
   print(criteria)   # debug before hitting production mailboxes

Get one message by UID
----------------------

.. code-block:: python

   msg = ImapMessage.objects.get(uid=12345)
   if msg:
       print(msg.subject)

``get()`` applies ``limit(1)`` and fetches a single row.

UID list only
-------------

.. code-block:: python

   msg_set = ImapMessage.objects.filter(unread=True).uids()
   print(msg_set.parsed_ids)

Useful before bulk flag operations on the session API.

Next: :doc:`04_load_levels_and_schemas`
