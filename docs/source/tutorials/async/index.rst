Async Tutorial
==============

This track mirrors the :doc:`../sync/index` step by step, using :class:`~sage_imap.aio.session.AsyncIMAPSession`. Read the sync lesson first if a concept is new; here we focus on **what changes** when you use ``async``/``await``.

.. important::

   Install the async extra first::

      pip install python-sage-imap[async]

.. note::

   **Sync vs async in one sentence:** the mailbox operations are the same; only the *calling style* changes — ``session.select()`` becomes ``await session.select()``, and ``for msg in ...`` becomes ``async for msg in ...``.

.. toctree::
   :maxdepth: 1
   :caption: Async lessons (1 → 10)

   01_welcome
   02_setup_and_connect
   03_explore_mailbox
   04_search_and_uids
   05_read_messages
   06_flags_and_actions
   07_folders_and_special_use
   08_auth_providers
   09_sync_and_idle
   10_production
