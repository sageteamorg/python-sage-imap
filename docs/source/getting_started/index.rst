.. _getting_started_index:

Getting started
===============

This section covers installation, your first connection, and the recommended APIs.

Suggested order:

1. :doc:`installation` — install the package (and the ``[async]`` extra if needed)
2. :doc:`first_steps` — connect, select a mailbox, search, and read messages
3. :doc:`imap_session` — use the ``IMAPSession`` facade for new projects
4. :doc:`async_api` — asyncio client (``sage_imap.aio``)
5. :doc:`migration_v2` — notes for upgrading to v2

For runnable scripts, see the `examples directory <https://github.com/sageteamorg/python-sage-imap/tree/main/examples>`_ on GitHub.

.. toctree::
   :hidden:

   installation
   first_steps
   imap_session
   async_api
   migration_v2
   introduction
   what_is_imap
   terminologies
   features
   search
   message_set
   headers
   best_practices
   common_patterns
   examples/basic_usage
   examples/uid_search_operations
   examples/message_set_usage
   examples/mailbox_management
   examples/flag_operations
   examples/folder_management
   examples/client_advanced
   examples/large_volume_handling
   examples/smtp_integration
   examples/production_patterns
   examples/error_handling
   examples/monitoring_analytics
   examples/outlook_integration
