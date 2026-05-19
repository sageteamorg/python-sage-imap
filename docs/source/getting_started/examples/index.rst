Example guides
==============

These pages walk through patterns from the repository ``examples/`` directory. They focus on **UID-based** operations, which remain stable when the mailbox changes.

.. important::

   Prefer UIDs over sequence numbers in production. Sequence numbers can change when messages are added or removed.

Guides in this section:

- :doc:`basic_usage` — client connection and capabilities
- :doc:`uid_search_operations` — search criteria and UID SEARCH
- :doc:`message_set_usage` — ``MessageSet`` ranges and batching
- :doc:`mailbox_management` — move, copy, append, expunge
- :doc:`flag_operations` — flags and bulk STORE
- :doc:`folder_management` — create, rename, list folders
- :doc:`client_advanced` — OAuth, TLS, pooling, health checks
- :doc:`large_volume_handling` — streaming and batch fetch
- :doc:`smtp_integration` — sending mail (companion to IMAP)
- :doc:`production_patterns` — deployment-oriented patterns
- :doc:`error_handling` — exceptions and recovery
- :doc:`monitoring_analytics` — metrics and observability
- :doc:`outlook_integration` — Exchange and Office 365 notes

.. toctree::
   :hidden:

   basic_usage
   uid_search_operations
   message_set_usage
   mailbox_management
   flag_operations
   folder_management
   client_advanced
   large_volume_handling
   smtp_integration
   production_patterns
   error_handling
   monitoring_analytics
   outlook_integration
