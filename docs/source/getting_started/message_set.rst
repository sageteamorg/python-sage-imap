MessageSet: Enhanced Message Operations
=======================================

The ``MessageSet`` class is a powerful tool for managing sets of email messages in Python Sage IMAP. It provides comprehensive support for both UIDs and sequence numbers, with a strong emphasis on **UID-based operations for reliability**.

**⚠️ IMPORTANT: Always use UIDs for production applications!**

Core Concepts
-------------

**What is MessageSet?**
  A MessageSet represents a collection of email messages identified by their UIDs (recommended) or sequence numbers. It provides validation, optimization, batch processing, and integration with EmailMessage objects.

**Why Use MessageSet?**
  - **Reliable operations**: UID-based message identification
  - **Batch processing**: Handle large message sets efficiently
  - **Performance optimization**: Automatic range compression
  - **Comprehensive validation**: Robust error handling
  - **Service integration**: Works seamlessly with IMAP services

**UID vs Sequence Numbers**
  - **UIDs**: Persistent, reliable, recommended for production
  - **Sequence Numbers**: Session-specific, volatile, use with caution

Creating MessageSets
--------------------

**Recommended: UID-Based Creation**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.models.message import MessageSet
   
   # Create from UIDs (recommended approach)
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   print(msg_set.msg_ids)      # Output: "1001,1002,1003"
   print(msg_set.is_uid)       # Output: True
   print(msg_set.mailbox)      # Output: "INBOX"

**Description:** Creates a MessageSet from a list of UIDs. This is the recommended approach for reliable message operations.

**From EmailMessage Objects**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.models.message import MessageSet
   
   # Create from EmailMessage objects (prefers UIDs)
   msg_set = MessageSet.from_email_messages(email_list)
   print(f"Created set with {len(msg_set)} messages")
   print(f"Using UIDs: {msg_set.is_uid}")

**Description:** Creates a MessageSet from EmailMessage objects. Automatically prefers UIDs when available, falls back to sequence numbers with warnings.

**Range Operations**
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # UID range (recommended)
   msg_set = MessageSet.from_range(1000, 2000, is_uid=True, mailbox="INBOX")
   print(msg_set.msg_ids)      # Output: "1000:2000"
   
   # Get all messages with UIDs
   all_msgs = MessageSet.from_range(1, "*", is_uid=True, mailbox="INBOX")
   print(all_msgs.msg_ids)     # Output: "1:*"
   
   # Convenience method for all messages
   all_msgs = MessageSet.all_messages(is_uid=True, mailbox="INBOX")

**Description:** Creates MessageSets from ranges of IDs. Supports open-ended ranges with "*" for getting all messages.

**Sequence Numbers (Use with Caution)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ⚠️ WARNING: Only for immediate, positional operations
   msg_set = MessageSet.from_sequence_numbers([1, 2, 3], mailbox="INBOX")
   print(msg_set.is_uid)       # Output: False
   # Logs warning: "Using sequence numbers for MessageSet. Consider using UIDs..."

**Description:** Creates MessageSet from sequence numbers. **Not recommended for production** due to reliability issues.

Advanced Features
-----------------

**Batch Processing**
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process large message sets in batches
   large_set = MessageSet.from_uids(list(range(1000, 10000)), mailbox="INBOX")
   
   for batch in large_set.iter_batches(batch_size=100):
       print(f"Processing batch with {len(batch)} messages")
       # Process each batch
       result = uid_service.uid_fetch(batch, MessagePart.RFC822)
       process_messages(result.metadata['fetched_messages'])

**Description:** Efficiently process large message sets by breaking them into smaller, manageable batches.

**Set Operations**
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Create two message sets
   set1 = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   set2 = MessageSet.from_uids([1003, 1004, 1005], mailbox="INBOX")
   
   # Union (combine sets)
   combined = set1.union(set2)
   print(combined.msg_ids)     # Output: "1001,1002,1003,1003,1004,1005"
   
   # Intersection (common messages)
   common = set1.intersection(set2)
   print(common.msg_ids)       # Output: "1003"
   
   # Subtraction (remove messages)
   remaining = set1.subtract(set2)
   print(remaining.msg_ids)    # Output: "1001,1002"

**Description:** Perform set operations on message sets for complex filtering and processing workflows.

**Optimization Features**
~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Automatic range compression
   msg_set = MessageSet.from_uids([1, 2, 3, 5, 6, 7, 10], mailbox="INBOX")
   print(msg_set.msg_ids)      # Output: "1:3,5:7,10"
   
   # Split large sets
   large_set = MessageSet.from_uids(list(range(1000, 2000)), mailbox="INBOX")
   smaller_sets = large_set.split_by_size(max_size=100)
   print(f"Split into {len(smaller_sets)} smaller sets")

**Description:** Automatic optimization converts consecutive IDs to ranges for better performance.

Message Set Properties
----------------------

**Inspection Methods**
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # Basic properties
   print(f"Empty: {msg_set.is_empty()}")           # Output: False
   print(f"Single message: {msg_set.is_single_message()}")  # Output: False
   print(f"Has ranges: {msg_set.is_range_only()}")          # Output: False
   print(f"Estimated count: {len(msg_set)}")       # Output: 3
   
   # ID access
   print(f"First ID: {msg_set.get_first_id()}")    # Output: 1001
   print(f"Last ID: {msg_set.get_last_id()}")      # Output: 1003
   print(f"Contains 1002: {1002 in msg_set}")      # Output: True

**Parsed Data Access**
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # Access parsed data
   print(f"Individual IDs: {msg_set.parsed_ids}")     # Output: [1001, 1002, 1003]
   print(f"ID ranges: {msg_set.id_ranges}")           # Output: []
   print(f"Has open range: {msg_set.has_open_range()}")  # Output: False
   
   # Iteration
   for msg_id in msg_set:
       print(f"Processing message {msg_id}")

**Dictionary Conversion**
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   msg_dict = msg_set.to_dict()
   
   print(msg_dict)
   # Output: {
   #     'msg_ids': '1001,1002,1003',
   #     'is_uid': True,
   #     'mailbox': 'INBOX',
   #     'estimated_count': 3,
   #     'individual_ids': [1001, 1002, 1003],
   #     'ranges': [],
   #     'has_open_range': False,
   #     'first_id': 1001,
   #     'last_id': 1003
   # }

Working with Services
---------------------

**UID Service Integration (Recommended)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.models.message import MessageSet
   from sage_imap.helpers.enums import MessagePart
   
   # Create UID service
   uid_service = IMAPMailboxUIDService(client)
   uid_service.select("INBOX")
   
   # Create message set from search results
   search_result = uid_service.uid_search(IMAPSearchCriteria.recent(7))
   msg_set = MessageSet.from_uids(search_result.affected_messages, mailbox="INBOX")
   
   # Use with UID operations
   fetch_result = uid_service.uid_fetch(msg_set, MessagePart.RFC822)
   move_result = uid_service.uid_move(msg_set, "Archive")

**Regular Service Integration (Not Recommended)**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.services import IMAPMailboxService
   
   # ⚠️ WARNING: Uses sequence numbers
   regular_service = IMAPMailboxService(client)
   regular_service.select("INBOX")
   
   # This returns sequence numbers (not recommended)
   search_result = regular_service.search(IMAPSearchCriteria.recent(7))
   msg_set = MessageSet.from_sequence_numbers(search_result.affected_messages, mailbox="INBOX")
   # Logs warning about using sequence numbers

Validation and Error Handling
-----------------------------

**Automatic Validation**
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Valid UID creation
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # Automatic validation during creation
   try:
       msg_set = MessageSet.from_uids([], mailbox="INBOX")
   except ValueError as e:
       print(e)  # Output: "UID list cannot be empty"

**Mailbox Validation**
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # Validate for specific mailbox
   try:
       msg_set.validate_for_mailbox("SENT")
   except ValueError as e:
       print(e)  # Output: "MessageSet is for mailbox 'INBOX' but trying to use with mailbox 'SENT'"

**Enhanced Error Messages**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   try:
       # Invalid range
       msg_set = MessageSet(msg_ids="300:200", is_uid=True)
   except ValueError as e:
       print(e)  # Output: "Invalid range: start (300) > end (200)"
   
   try:
       # Invalid message ID
       msg_set = MessageSet(msg_ids="abc", is_uid=True)
   except ValueError as e:
       print(e)  # Output: "Invalid message ID: abc"

Utility Functions
-----------------

**Convenience Functions**
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.models.message import create_uid_set, create_sequence_set, merge_message_sets
   
   # Convenience functions
   uid_set = create_uid_set([1001, 1002, 1003], mailbox="INBOX")
   seq_set = create_sequence_set([1, 2, 3], mailbox="INBOX")  # Not recommended
   
   # Merge multiple sets
   merged = merge_message_sets([uid_set, another_uid_set])

**Batch Iterator**
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from sage_imap.models.message import MessageSetBatchIterator
   
   large_set = MessageSet.from_uids(list(range(1000, 10000)), mailbox="INBOX")
   batch_iterator = MessageSetBatchIterator(large_set, batch_size=100)
   
   for batch in batch_iterator:
       print(f"Processing batch: {batch}")

Best Practices
--------------

**DO: Use UIDs for Reliability**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ RECOMMENDED: Always use UIDs
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # ✅ RECOMMENDED: Use UID service
   uid_service = IMAPMailboxUIDService(client)
   result = uid_service.uid_fetch(msg_set, MessagePart.RFC822)

**DON'T: Use Sequence Numbers in Production**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ❌ AVOID: Sequence numbers are unreliable
   msg_set = MessageSet.from_sequence_numbers([1, 2, 3], mailbox="INBOX")
   
   # ❌ AVOID: Regular service uses sequence numbers
   regular_service = IMAPMailboxService(client)
   result = regular_service.search(criteria)  # Returns sequence numbers

**DO: Use Batch Processing for Large Sets**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ RECOMMENDED: Process in batches
   large_set = MessageSet.from_uids(list(range(1000, 10000)), mailbox="INBOX")
   
   for batch in large_set.iter_batches(batch_size=100):
       result = uid_service.uid_fetch(batch, MessagePart.RFC822)
       process_messages(result.metadata['fetched_messages'])

**DO: Validate for Specific Mailboxes**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ RECOMMENDED: Validate context
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   msg_set.validate_for_mailbox("INBOX")  # Ensures consistency

**DO: Use Set Operations for Complex Filtering**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # ✅ RECOMMENDED: Combine operations
   recent_msgs = MessageSet.from_uids(recent_uids, mailbox="INBOX")
   important_msgs = MessageSet.from_uids(important_uids, mailbox="INBOX")
   
   # Get recent AND important messages
   urgent_msgs = recent_msgs.intersection(important_msgs)

Performance Considerations
--------------------------

**Automatic Optimization**
~~~~~~~~~~~~~~~~~~~~~~~~~~

The MessageSet class automatically optimizes ID representations:

.. code-block:: python

   # Input: [1, 2, 3, 5, 6, 7, 10]
   # Optimized: "1:3,5:7,10"
   msg_set = MessageSet.from_uids([1, 2, 3, 5, 6, 7, 10])
   print(msg_set.msg_ids)  # Output: "1:3,5:7,10"

**Caching for Performance**
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Expensive operations are cached using ``@cached_property``:

.. code-block:: python

   msg_set = MessageSet.from_uids([1001, 1002, 1003])
   
   # First access: parses and caches
   ids = msg_set.parsed_ids
   
   # Subsequent access: uses cached value
   ids_again = msg_set.parsed_ids  # No parsing overhead

**Memory-Efficient Iteration**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Memory-efficient batch processing
   large_set = MessageSet.from_uids(list(range(1000, 100000)))
   
   # Process without loading all messages into memory
   for batch in large_set.iter_batches(batch_size=1000):
       process_batch_efficiently(batch)

Migration Guide
---------------

**From Old MessageSet**
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Old approach (still works but not recommended)
   msg_set = MessageSet("1001,1002,1003")
   
   # New recommended approach
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")

**From Manual ID Management**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Old manual approach
   uids = [1001, 1002, 1003]
   uid_string = ",".join(map(str, uids))
   
   # New MessageSet approach
   msg_set = MessageSet.from_uids(uids, mailbox="INBOX")
   # Automatic optimization, validation, and features

Summary
-------

The enhanced MessageSet class provides:

- **Reliability**: UID-first approach for consistent operations
- **Performance**: Automatic optimization and caching
- **Scalability**: Batch processing for large datasets
- **Flexibility**: Support for various creation methods
- **Integration**: Seamless work with services and EmailMessage
- **Validation**: Comprehensive error handling and validation
- **Maintainability**: Clear APIs and extensive documentation

**Key Takeaways:**
- Always use UIDs for production applications
- Leverage batch processing for large message sets
- Use set operations for complex filtering
- Validate message sets for specific mailboxes
- Take advantage of automatic optimization features

By following these guidelines and using the enhanced MessageSet class, you'll build more reliable and efficient email processing applications with Python Sage IMAP.