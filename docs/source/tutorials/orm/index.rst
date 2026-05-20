IMAP ORM Tutorial
=================

This track teaches the optional **IMAP ORM** — a manager/queryset layer over live mailboxes. There is no SQL database: every query becomes **UID SEARCH** and batched **UID FETCH** on your provider.

When to use the ORM
-------------------

Use ``sage_imap.orm`` when you want:

- Readable filters — ``ImapMessage.objects.filter(unread=True, from_address="boss@co.com")``
- Explicit pagination — ``limit()``, ``offset()``, ``cursor(after_uid=...)``
- API-friendly payloads — Pydantic schemas for JSON responses
- Multi-tenant apps — ``account_id`` on every entity plus ``ImapAccountConfig``
- The same patterns in sync and async

Keep using :class:`~sage_imap.session.IMAPSession` directly when you need maximum control over raw IMAP or minimal dependencies (ORM requires ``pip install python-sage-imap[orm]``).

Prerequisites
-------------

- Python 3.10+
- Completed :doc:`../sync/02_setup_and_connect` **or** equivalent IMAP connection experience
- ``pip install python-sage-imap[orm]`` (add ``[async]`` for lesson 8)

Course map
----------

+--------+-----------------------------+------------------------------------------+
| Lesson | Topic                       | You will be able to                      |
+========+=============================+==========================================+
| 1      | Welcome & mental model      | Choose ORM vs session API                |
| 2      | Install & first query       | Open ``ImapORM`` and list unread mail    |
| 3      | Filters & Q objects         | Compose SEARCH criteria safely           |
| 4      | Load levels & schemas       | Control FETCH depth and export JSON      |
| 5      | Pagination & actions        | Page results and mark/move/delete        |
| 6      | Multi-tenant & connections  | Configure accounts and pooling           |
| 7      | Sync & IDLE                 | CONDSTORE checkpoints and live mail      |
| 8      | Async ORM                   | Same patterns with ``AsyncImapORM``      |
+--------+-----------------------------+------------------------------------------+

Reference
---------

- :doc:`../../orm/index` — API overview and quick starts
- :doc:`../../getting_started/search` — underlying SEARCH criteria
- Runnable examples: ``examples/10_orm_sync.py``, ``examples/11_orm_async.py``

.. toctree::
   :maxdepth: 1
   :caption: ORM lessons (1 → 8)

   01_welcome
   02_install_and_connect
   03_filters_and_querysets
   04_load_levels_and_schemas
   05_pagination_and_actions
   06_multi_tenant
   07_sync_and_idle
   08_async_orm
