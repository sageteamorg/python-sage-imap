.. _message_set_usage:

Advanced MessageSet Usage
=========================

This example demonstrates advanced usage of the enhanced MessageSet class with all its powerful features including set operations, batch processing, and optimization techniques.

**⚠️ IMPORTANT: This example uses the enhanced MessageSet with UID-first approach!**

Overview
--------

You'll learn how to:

- Create MessageSet objects using various methods
- Perform set operations (union, intersection, difference)
- Use batch processing for efficient operations
- Optimize MessageSet for performance
- Handle large message sets efficiently
- Use MessageSet with search results
- Implement advanced filtering and sorting
- Cache and persist MessageSet objects

Prerequisites
-------------

- Python 3.10 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of the enhanced MessageSet class

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Advanced MessageSet Usage Example
   
   This example demonstrates advanced usage of the enhanced MessageSet class
   with all its powerful features and optimization techniques.
   """
   
   import logging
   import time
   import json
   import pickle
   from datetime import datetime, timedelta
   from typing import List, Dict, Optional, Set, Iterator
   from pathlib import Path
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService
   from sage_imap.helpers.search import IMAPSearchCriteria
   from sage_imap.models.message import MessageSet
   from sage_imap.helpers.enums import MessagePart, Flag
   from sage_imap.exceptions import IMAPOperationError
   
   # Configure logging
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   
   logger = logging.getLogger(__name__)
   
   
   class MessageSetUsageExample:
       """
       Advanced MessageSet usage demonstration.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the MessageSet usage example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
           # Create cache directory
           self.cache_dir = Path("message_set_cache")
           self.cache_dir.mkdir(exist_ok=True)
           
       def demonstrate_message_set_usage(self):
           """
           Demonstrate comprehensive MessageSet usage.
           """
           logger.info("=== Advanced MessageSet Usage Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Creation methods
                   self.demonstrate_creation_methods(uid_service)
                   
                   # Set operations
                   self.demonstrate_set_operations(uid_service)
                   
                   # Batch processing
                   self.demonstrate_batch_processing(uid_service)
                   
                   # Optimization techniques
                   self.demonstrate_optimization(uid_service)
                   
                   # Advanced filtering
                   self.demonstrate_advanced_filtering(uid_service)
                   
                   # Persistence and caching
                   self.demonstrate_persistence(uid_service)
                   
                   # Performance analysis
                   self.demonstrate_performance_analysis(uid_service)
                   
                   # Integration patterns
                   self.demonstrate_integration_patterns(uid_service)
                   
                   logger.info("✓ Advanced MessageSet usage completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Advanced MessageSet usage failed: {e}")
               raise
   
       def demonstrate_creation_methods(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate various MessageSet creation methods.
           """
           logger.info("--- MessageSet Creation Methods ---")
           
           try:
               # Method 1: From UIDs (recommended)
               sample_uids = [1001, 1002, 1003, 1005, 1006, 1007, 1010]
               uid_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               logger.info(f"✓ From UIDs: {uid_set}")
               logger.info(f"  • Count: {len(uid_set)}")
               logger.info(f"  • Optimized: {uid_set.optimized_string}")
               
               # Method 2: From sequence numbers
               seq_numbers = [1, 2, 3, 5, 6, 7, 10]
               seq_set = MessageSet.from_sequence_numbers(seq_numbers, mailbox="INBOX")
               logger.info(f"✓ From sequence numbers: {seq_set}")
               logger.info(f"  • Count: {len(seq_set)}")
               
               # Method 3: From range
               range_set = MessageSet.from_range(1000, 1020, mailbox="INBOX")
               logger.info(f"✓ From range: {range_set}")
               logger.info(f"  • Count: {len(range_set)}")
               
               # Method 4: All messages
               all_set = MessageSet.all_messages(mailbox="INBOX")
               logger.info(f"✓ All messages: {all_set}")
               
               # Method 5: From search results
               search_criteria = IMAPSearchCriteria.since_days(7)
               search_set = uid_service.create_message_set_from_search(search_criteria)
               logger.info(f"✓ From search: {len(search_set)} messages")
               
               # Method 6: From email messages
               if not search_set.is_empty():
                   # Fetch some messages
                   sample_search = MessageSet.from_uids(list(search_set.parsed_ids)[:5], mailbox="INBOX")
                   fetch_result = uid_service.uid_fetch(sample_search, MessagePart.HEADER)
                   
                   if fetch_result.success:
                       messages = fetch_result.metadata.get('fetched_messages', [])
                       if messages:
                           email_set = MessageSet.from_email_messages(messages)
                           logger.info(f"✓ From email messages: {len(email_set)} messages")
               
               logger.info("✓ MessageSet creation methods completed")
               
           except Exception as e:
               logger.error(f"Failed MessageSet creation methods: {e}")
   
       def demonstrate_set_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate set operations with MessageSet.
           """
           logger.info("--- MessageSet Set Operations ---")
           
           try:
               # Create sample MessageSets
               set_a = MessageSet.from_uids([1001, 1002, 1003, 1004, 1005], mailbox="INBOX")
               set_b = MessageSet.from_uids([1003, 1004, 1005, 1006, 1007], mailbox="INBOX")
               set_c = MessageSet.from_uids([1005, 1006, 1007, 1008, 1009], mailbox="INBOX")
               
               logger.info(f"📧 Set A: {set_a}")
               logger.info(f"📧 Set B: {set_b}")
               logger.info(f"📧 Set C: {set_c}")
               
               # Union operation
               union_ab = set_a.union(set_b)
               logger.info(f"✓ A ∪ B: {union_ab}")
               logger.info(f"  • Count: {len(union_ab)}")
               
               # Intersection operation
               intersection_ab = set_a.intersection(set_b)
               logger.info(f"✓ A ∩ B: {intersection_ab}")
               logger.info(f"  • Count: {len(intersection_ab)}")
               
               # Difference operation
               difference_ab = set_a.subtract(set_b)
               logger.info(f"✓ A - B: {difference_ab}")
               logger.info(f"  • Count: {len(difference_ab)}")
               
               # Symmetric difference
               sym_diff_ab = set_a.union(set_b).subtract(set_a.intersection(set_b))
               logger.info(f"✓ A ⊕ B: {sym_diff_ab}")
               logger.info(f"  • Count: {len(sym_diff_ab)}")
               
               # Multiple set operations
               multi_union = set_a.union(set_b).union(set_c)
               logger.info(f"✓ A ∪ B ∪ C: {multi_union}")
               logger.info(f"  • Count: {len(multi_union)}")
               
               # Complex operations
               complex_result = set_a.union(set_b).intersection(set_c)
               logger.info(f"✓ (A ∪ B) ∩ C: {complex_result}")
               logger.info(f"  • Count: {len(complex_result)}")
               
               # Demonstrate with real search results
               self.demonstrate_real_set_operations(uid_service)
               
               logger.info("✓ Set operations completed")
               
           except Exception as e:
               logger.error(f"Failed set operations: {e}")
   
       def demonstrate_real_set_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate set operations with real search results.
           """
           logger.info("--- Real Set Operations ---")
           
           try:
               # Get different message sets
               unread_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.UNSEEN)
               flagged_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.FLAGGED)
               recent_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               logger.info(f"📧 Unread messages: {len(unread_set)}")
               logger.info(f"📧 Flagged messages: {len(flagged_set)}")
               logger.info(f"📧 Recent messages: {len(recent_set)}")
               
               # Practical combinations
               if not unread_set.is_empty() and not flagged_set.is_empty():
                   # Unread AND flagged (high priority)
                   high_priority = unread_set.intersection(flagged_set)
                   logger.info(f"✓ High priority (unread ∩ flagged): {len(high_priority)}")
               
               if not unread_set.is_empty() and not recent_set.is_empty():
                   # Unread OR recent (needs attention)
                   needs_attention = unread_set.union(recent_set)
                   logger.info(f"✓ Needs attention (unread ∪ recent): {len(needs_attention)}")
               
               if not recent_set.is_empty() and not flagged_set.is_empty():
                   # Recent but not flagged (review candidates)
                   review_candidates = recent_set.subtract(flagged_set)
                   logger.info(f"✓ Review candidates (recent - flagged): {len(review_candidates)}")
               
               logger.info("✓ Real set operations completed")
               
           except Exception as e:
               logger.error(f"Failed real set operations: {e}")
   
       def demonstrate_batch_processing(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate batch processing with MessageSet.
           """
           logger.info("--- MessageSet Batch Processing ---")
           
           try:
               # Get a large set of messages
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               
               if all_messages.is_empty():
                   logger.info("📧 No messages for batch processing")
                   return
               
               logger.info(f"📧 Processing {len(all_messages)} messages in batches")
               
               # Basic batch processing
               self.demonstrate_basic_batching(uid_service, all_messages)
               
               # Adaptive batch processing
               self.demonstrate_adaptive_batching(uid_service, all_messages)
               
               # Parallel batch processing
               self.demonstrate_parallel_batching(uid_service, all_messages)
               
               logger.info("✓ Batch processing completed")
               
           except Exception as e:
               logger.error(f"Failed batch processing: {e}")
   
       def demonstrate_basic_batching(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate basic batch processing.
           """
           logger.info("--- Basic Batch Processing ---")
           
           try:
               batch_size = 50
               processed_count = 0
               
               logger.info(f"📧 Processing in batches of {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   start_time = time.time()
                   
                   # Process batch
                   fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
                   
                   processing_time = time.time() - start_time
                   
                   if fetch_result.success:
                       batch_messages = fetch_result.metadata.get('fetched_messages', [])
                       processed_count += len(batch_messages)
                       
                       logger.info(f"  ✓ Batch {batch_num}: {len(batch_messages)} messages ({processing_time:.2f}s)")
                   else:
                       logger.warning(f"  ⚠ Batch {batch_num} failed")
                   
                   # Limit demo to first 5 batches
                   if batch_num >= 5:
                       logger.info("  ... stopping demo at batch 5")
                       break
               
               logger.info(f"✓ Basic batching: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed basic batching: {e}")
   
       def demonstrate_adaptive_batching(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate adaptive batch processing.
           """
           logger.info("--- Adaptive Batch Processing ---")
           
           try:
               batch_size = 25
               processed_count = 0
               
               logger.info(f"📧 Adaptive batching starting with size {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   start_time = time.time()
                   
                   # Process batch
                   fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
                   
                   processing_time = time.time() - start_time
                   
                   if fetch_result.success:
                       batch_messages = fetch_result.metadata.get('fetched_messages', [])
                       processed_count += len(batch_messages)
                       
                       # Adaptive sizing
                       if processing_time < 1.0:
                           batch_size = min(batch_size * 1.2, 100)
                       elif processing_time > 3.0:
                           batch_size = max(batch_size * 0.8, 10)
                       
                       logger.info(f"  ✓ Batch {batch_num}: {len(batch_messages)} messages "
                                  f"({processing_time:.2f}s, next: {int(batch_size)})")
                   else:
                       logger.warning(f"  ⚠ Batch {batch_num} failed")
                   
                   # Limit demo to first 3 batches
                   if batch_num >= 3:
                       logger.info("  ... stopping adaptive demo at batch 3")
                       break
               
               logger.info(f"✓ Adaptive batching: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed adaptive batching: {e}")
   
       def demonstrate_parallel_batching(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate parallel batch processing.
           """
           logger.info("--- Parallel Batch Processing ---")
           
           try:
               # Split into chunks for parallel processing
               chunk_size = 30
               chunks = []
               
               for batch in messages.iter_batches(batch_size=chunk_size):
                   chunks.append(batch)
                   if len(chunks) >= 3:  # Limit for demo
                       break
               
               logger.info(f"📧 Processing {len(chunks)} chunks in parallel")
               
               # Process chunks (simulated parallel)
               results = []
               for i, chunk in enumerate(chunks):
                   try:
                       start_time = time.time()
                       fetch_result = uid_service.uid_fetch(chunk, MessagePart.HEADER)
                       processing_time = time.time() - start_time
                       
                       if fetch_result.success:
                           chunk_messages = fetch_result.metadata.get('fetched_messages', [])
                           results.append({
                               'chunk': i + 1,
                               'count': len(chunk_messages),
                               'time': processing_time,
                               'success': True
                           })
                       else:
                           results.append({
                               'chunk': i + 1,
                               'count': 0,
                               'time': processing_time,
                               'success': False
                           })
                   except Exception as e:
                       logger.error(f"  ❌ Chunk {i + 1} error: {e}")
               
               # Report results
               total_processed = sum(r['count'] for r in results if r['success'])
               avg_time = sum(r['time'] for r in results) / len(results) if results else 0
               
               logger.info(f"✓ Parallel batching: {total_processed} messages processed")
               logger.info(f"  • Average time per chunk: {avg_time:.2f}s")
               
           except Exception as e:
               logger.error(f"Failed parallel batching: {e}")
   
       def demonstrate_optimization(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate MessageSet optimization techniques.
           """
           logger.info("--- MessageSet Optimization ---")
           
           try:
               # Range compression
               self.demonstrate_range_compression()
               
               # Cached properties
               self.demonstrate_cached_properties(uid_service)
               
               # Memory optimization
               self.demonstrate_memory_optimization()
               
               # String optimization
               self.demonstrate_string_optimization()
               
               logger.info("✓ Optimization techniques completed")
               
           except Exception as e:
               logger.error(f"Failed optimization demonstration: {e}")
   
       def demonstrate_range_compression(self):
           """
           Demonstrate range compression optimization.
           """
           logger.info("--- Range Compression ---")
           
           try:
               # Create MessageSet with consecutive UIDs
               consecutive_uids = list(range(1000, 1020)) + list(range(1025, 1035)) + [1050, 1051, 1052]
               msg_set = MessageSet.from_uids(consecutive_uids, mailbox="INBOX")
               
               logger.info(f"📧 Original UIDs: {len(consecutive_uids)} UIDs")
               logger.info(f"📧 Compressed: {msg_set.optimized_string}")
               logger.info(f"📧 Efficiency: {len(msg_set.optimized_string)} chars vs {len(str(consecutive_uids))} chars")
               
               # Demonstrate compression benefit
               sparse_uids = [1001, 1003, 1005, 1007, 1009, 1011, 1013, 1015]
               sparse_set = MessageSet.from_uids(sparse_uids, mailbox="INBOX")
               
               logger.info(f"📧 Sparse UIDs: {sparse_set.optimized_string}")
               
               # Mixed pattern
               mixed_uids = [1, 2, 3, 5, 6, 7, 10, 15, 16, 17, 18, 25]
               mixed_set = MessageSet.from_uids(mixed_uids, mailbox="INBOX")
               
               logger.info(f"📧 Mixed pattern: {mixed_set.optimized_string}")
               
               logger.info("✓ Range compression demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed range compression: {e}")
   
       def demonstrate_cached_properties(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate cached properties optimization.
           """
           logger.info("--- Cached Properties ---")
           
           try:
               # Create a large MessageSet
               large_set = MessageSet.from_range(1000, 1500, mailbox="INBOX")
               
               # First access - cached
               start_time = time.time()
               count1 = len(large_set)
               first_access_time = time.time() - start_time
               
               # Second access - from cache
               start_time = time.time()
               count2 = len(large_set)
               second_access_time = time.time() - start_time
               
               logger.info(f"📧 MessageSet size: {count1}")
               logger.info(f"📊 First access time: {first_access_time:.6f}s")
               logger.info(f"📊 Second access time: {second_access_time:.6f}s")
               logger.info(f"📊 Speedup: {first_access_time/second_access_time:.1f}x")
               
               # Optimized string caching
               start_time = time.time()
               opt_str1 = large_set.optimized_string
               opt_time1 = time.time() - start_time
               
               start_time = time.time()
               opt_str2 = large_set.optimized_string
               opt_time2 = time.time() - start_time
               
               logger.info(f"📊 Optimized string first: {opt_time1:.6f}s")
               logger.info(f"📊 Optimized string cached: {opt_time2:.6f}s")
               
               logger.info("✓ Cached properties demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed cached properties: {e}")
   
       def demonstrate_memory_optimization(self):
           """
           Demonstrate memory optimization techniques.
           """
           logger.info("--- Memory Optimization ---")
           
           try:
               # Large MessageSet creation
               large_uids = list(range(1, 10001))  # 10,000 UIDs
               large_set = MessageSet.from_uids(large_uids, mailbox="INBOX")
               
               logger.info(f"📧 Large MessageSet: {len(large_set)} messages")
               
               # Memory-efficient iteration
               logger.info("📧 Memory-efficient iteration:")
               
               batch_count = 0
               for batch in large_set.iter_batches(batch_size=100):
                   batch_count += 1
                   if batch_count >= 5:  # Limit demo
                       break
               
               logger.info(f"  • Processed {batch_count} batches without loading all into memory")
               
               # Lazy evaluation
               logger.info("📧 Lazy evaluation benefits:")
               logger.info("  • Parsed IDs only computed when needed")
               logger.info("  • Optimized string cached after first computation")
               logger.info("  • Batch iteration doesn't load full dataset")
               
               logger.info("✓ Memory optimization demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed memory optimization: {e}")
   
       def demonstrate_string_optimization(self):
           """
           Demonstrate string optimization techniques.
           """
           logger.info("--- String Optimization ---")
           
           try:
               # Different patterns and their optimizations
               patterns = [
                   ("Sequential", list(range(1, 21))),
                   ("Sparse", [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]),
                   ("Mixed", [1, 2, 3, 5, 6, 7, 10, 15, 16, 17, 18, 25]),
                   ("Single", [1000]),
                   ("Pair", [1000, 1001]),
                   ("Large Range", list(range(1000, 2000)))
               ]
               
               for pattern_name, uids in patterns:
                   msg_set = MessageSet.from_uids(uids, mailbox="INBOX")
                   
                   # Compare basic vs optimized
                   basic_str = ",".join(map(str, uids))
                   optimized_str = msg_set.optimized_string
                   
                   compression_ratio = len(basic_str) / len(optimized_str) if optimized_str else 1
                   
                   logger.info(f"📧 {pattern_name}:")
                   logger.info(f"  • Basic: {basic_str[:50]}{'...' if len(basic_str) > 50 else ''}")
                   logger.info(f"  • Optimized: {optimized_str}")
                   logger.info(f"  • Compression: {compression_ratio:.1f}x")
               
               logger.info("✓ String optimization demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed string optimization: {e}")
   
       def demonstrate_advanced_filtering(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate advanced filtering with MessageSet.
           """
           logger.info("--- Advanced Filtering ---")
           
           try:
               # Get base message set
               base_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(30))
               
               if base_set.is_empty():
                   logger.info("📧 No messages for filtering demo")
                   return
               
               logger.info(f"📧 Base set: {len(base_set)} messages")
               
               # Multi-criteria filtering
               self.demonstrate_multi_criteria_filtering(uid_service, base_set)
               
               # Progressive filtering
               self.demonstrate_progressive_filtering(uid_service, base_set)
               
               # Custom filtering
               self.demonstrate_custom_filtering(uid_service, base_set)
               
               logger.info("✓ Advanced filtering completed")
               
           except Exception as e:
               logger.error(f"Failed advanced filtering: {e}")
   
       def demonstrate_multi_criteria_filtering(self, uid_service: IMAPMailboxUIDService, base_set: MessageSet):
           """
           Demonstrate multi-criteria filtering.
           """
           logger.info("--- Multi-Criteria Filtering ---")
           
           try:
               # Define filter criteria
               filters = [
                   ("Unread", IMAPSearchCriteria.UNSEEN),
                   ("Flagged", IMAPSearchCriteria.FLAGGED),
                   ("Large", IMAPSearchCriteria.larger(1024 * 1024)),
                   ("From Gmail", IMAPSearchCriteria.from_address("@gmail.com"))
               ]
               
               filter_results = {}
               
               for filter_name, criteria in filters:
                   try:
                       filtered_set = uid_service.create_message_set_from_search(criteria)
                       
                       # Intersect with base set
                       if not base_set.is_empty() and not filtered_set.is_empty():
                           result_set = base_set.intersection(filtered_set)
                           filter_results[filter_name] = result_set
                           logger.info(f"  • {filter_name}: {len(result_set)} messages")
                       else:
                           logger.info(f"  • {filter_name}: 0 messages")
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ {filter_name} filter failed: {e}")
               
               # Combine filters
               if len(filter_results) > 1:
                   combined_filter_names = list(filter_results.keys())[:2]
                   if len(combined_filter_names) == 2:
                       combined_set = filter_results[combined_filter_names[0]].intersection(
                           filter_results[combined_filter_names[1]]
                       )
                       logger.info(f"  • Combined ({' ∩ '.join(combined_filter_names)}): {len(combined_set)} messages")
               
               logger.info("✓ Multi-criteria filtering completed")
               
           except Exception as e:
               logger.error(f"Failed multi-criteria filtering: {e}")
   
       def demonstrate_progressive_filtering(self, uid_service: IMAPMailboxUIDService, base_set: MessageSet):
           """
           Demonstrate progressive filtering.
           """
           logger.info("--- Progressive Filtering ---")
           
           try:
               current_set = base_set
               logger.info(f"📧 Starting with: {len(current_set)} messages")
               
               # Progressive filter steps
               filter_steps = [
                   ("Recent (last 7 days)", IMAPSearchCriteria.since_days(7)),
                   ("Unread", IMAPSearchCriteria.UNSEEN),
                   ("Important", IMAPSearchCriteria.FLAGGED)
               ]
               
               for step_name, criteria in filter_steps:
                   try:
                       step_set = uid_service.create_message_set_from_search(criteria)
                       
                       if not current_set.is_empty() and not step_set.is_empty():
                           current_set = current_set.intersection(step_set)
                           logger.info(f"  • After {step_name}: {len(current_set)} messages")
                       else:
                           logger.info(f"  • After {step_name}: 0 messages")
                           break
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ {step_name} step failed: {e}")
               
               logger.info(f"✓ Progressive filtering result: {len(current_set)} messages")
               
           except Exception as e:
               logger.error(f"Failed progressive filtering: {e}")
   
       def demonstrate_custom_filtering(self, uid_service: IMAPMailboxUIDService, base_set: MessageSet):
           """
           Demonstrate custom filtering logic.
           """
           logger.info("--- Custom Filtering ---")
           
           try:
               # Custom filter: even UIDs only
               all_uids = list(base_set.parsed_ids)
               even_uids = [uid for uid in all_uids if uid % 2 == 0]
               
               if even_uids:
                   even_set = MessageSet.from_uids(even_uids, mailbox="INBOX")
                   logger.info(f"  • Even UIDs: {len(even_set)} messages")
               
               # Custom filter: UIDs divisible by 10
               divisible_uids = [uid for uid in all_uids if uid % 10 == 0]
               
               if divisible_uids:
                   divisible_set = MessageSet.from_uids(divisible_uids, mailbox="INBOX")
                   logger.info(f"  • Divisible by 10: {len(divisible_set)} messages")
               
               # Custom filter: UID ranges
               uid_ranges = [
                   (1000, 1099),
                   (1100, 1199),
                   (1200, 1299)
               ]
               
               range_sets = []
               for start, end in uid_ranges:
                   range_uids = [uid for uid in all_uids if start <= uid <= end]
                   if range_uids:
                       range_set = MessageSet.from_uids(range_uids, mailbox="INBOX")
                       range_sets.append(range_set)
                       logger.info(f"  • Range {start}-{end}: {len(range_set)} messages")
               
               # Combine range filters
               if len(range_sets) > 1:
                   combined_ranges = range_sets[0]
                   for range_set in range_sets[1:]:
                       combined_ranges = combined_ranges.union(range_set)
                   logger.info(f"  • All ranges combined: {len(combined_ranges)} messages")
               
               logger.info("✓ Custom filtering completed")
               
           except Exception as e:
               logger.error(f"Failed custom filtering: {e}")
   
       def demonstrate_persistence(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate MessageSet persistence and caching.
           """
           logger.info("--- MessageSet Persistence ---")
           
           try:
               # Create a MessageSet to persist
               test_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               if test_set.is_empty():
                   logger.info("📧 No messages for persistence demo")
                   return
               
               # JSON persistence
               self.demonstrate_json_persistence(test_set)
               
               # Binary persistence
               self.demonstrate_binary_persistence(test_set)
               
               # Cache management
               self.demonstrate_cache_management(test_set)
               
               logger.info("✓ Persistence demonstration completed")
               
           except Exception as e:
               logger.error(f"Failed persistence demonstration: {e}")
   
       def demonstrate_json_persistence(self, message_set: MessageSet):
           """
           Demonstrate JSON persistence.
           """
           logger.info("--- JSON Persistence ---")
           
           try:
               # Serialize to JSON
               json_file = self.cache_dir / "message_set.json"
               
               message_data = {
                   'mailbox': message_set.mailbox,
                   'is_uid': message_set.is_uid,
                   'ids': list(message_set.parsed_ids),
                   'timestamp': datetime.now().isoformat(),
                   'count': len(message_set)
               }
               
               with open(json_file, 'w') as f:
                   json.dump(message_data, f, indent=2)
               
               logger.info(f"📁 Saved to JSON: {json_file}")
               logger.info(f"  • Messages: {message_data['count']}")
               logger.info(f"  • File size: {json_file.stat().st_size} bytes")
               
               # Load from JSON
               with open(json_file, 'r') as f:
                   loaded_data = json.load(f)
               
               # Reconstruct MessageSet
               if loaded_data['is_uid']:
                   reconstructed_set = MessageSet.from_uids(
                       loaded_data['ids'], 
                       mailbox=loaded_data['mailbox']
                   )
               else:
                   reconstructed_set = MessageSet.from_sequence_numbers(
                       loaded_data['ids'],
                       mailbox=loaded_data['mailbox']
                   )
               
               logger.info(f"✓ Reconstructed MessageSet: {len(reconstructed_set)} messages")
               
               # Verify integrity
               if len(reconstructed_set) == len(message_set):
                   logger.info("✓ JSON persistence integrity verified")
               else:
                   logger.error("❌ JSON persistence integrity failed")
               
           except Exception as e:
               logger.error(f"Failed JSON persistence: {e}")
   
       def demonstrate_binary_persistence(self, message_set: MessageSet):
           """
           Demonstrate binary persistence using pickle.
           """
           logger.info("--- Binary Persistence ---")
           
           try:
               # Serialize to binary
               binary_file = self.cache_dir / "message_set.pickle"
               
               with open(binary_file, 'wb') as f:
                   pickle.dump(message_set, f)
               
               logger.info(f"📁 Saved to binary: {binary_file}")
               logger.info(f"  • File size: {binary_file.stat().st_size} bytes")
               
               # Load from binary
               with open(binary_file, 'rb') as f:
                   loaded_set = pickle.load(f)
               
               logger.info(f"✓ Loaded MessageSet: {len(loaded_set)} messages")
               
               # Verify integrity
               if len(loaded_set) == len(message_set):
                   logger.info("✓ Binary persistence integrity verified")
               else:
                   logger.error("❌ Binary persistence integrity failed")
               
               # Compare file sizes
               json_file = self.cache_dir / "message_set.json"
               if json_file.exists():
                   json_size = json_file.stat().st_size
                   binary_size = binary_file.stat().st_size
                   compression_ratio = json_size / binary_size
                   
                   logger.info(f"📊 Size comparison:")
                   logger.info(f"  • JSON: {json_size} bytes")
                   logger.info(f"  • Binary: {binary_size} bytes")
                   logger.info(f"  • Compression: {compression_ratio:.1f}x")
               
           except Exception as e:
               logger.error(f"Failed binary persistence: {e}")
   
       def demonstrate_cache_management(self, message_set: MessageSet):
           """
           Demonstrate cache management.
           """
           logger.info("--- Cache Management ---")
           
           try:
               # Create cache entries
               cache_entries = {
                   'recent': message_set,
                   'filtered': message_set.intersection(message_set),  # Self-intersection
                   'sample': MessageSet.from_uids(list(message_set.parsed_ids)[:10], mailbox="INBOX")
               }
               
               # Save cache entries
               for cache_name, cache_set in cache_entries.items():
                   cache_file = self.cache_dir / f"cache_{cache_name}.json"
                   
                   cache_data = {
                       'name': cache_name,
                       'mailbox': cache_set.mailbox,
                       'is_uid': cache_set.is_uid,
                       'ids': list(cache_set.parsed_ids),
                       'timestamp': datetime.now().isoformat(),
                       'count': len(cache_set)
                   }
                   
                   with open(cache_file, 'w') as f:
                       json.dump(cache_data, f)
                   
                   logger.info(f"📁 Cached {cache_name}: {len(cache_set)} messages")
               
               # Cache cleanup
               self.cleanup_old_cache_files()
               
               logger.info("✓ Cache management completed")
               
           except Exception as e:
               logger.error(f"Failed cache management: {e}")
   
       def cleanup_old_cache_files(self):
           """
           Cleanup old cache files.
           """
           try:
               # Find old cache files
               cache_files = list(self.cache_dir.glob("*.json"))
               current_time = datetime.now()
               
               for cache_file in cache_files:
                   try:
                       # Check file age
                       file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                       age = current_time - file_time
                       
                       if age > timedelta(hours=1):  # Old files
                           logger.info(f"🗑 Cleaning up old cache: {cache_file.name}")
                           # In production, you would delete old files
                           # cache_file.unlink()
                   
                   except Exception as e:
                       logger.warning(f"⚠ Could not check cache file {cache_file}: {e}")
               
           except Exception as e:
               logger.error(f"Failed cache cleanup: {e}")
   
       def demonstrate_performance_analysis(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate performance analysis of MessageSet operations.
           """
           logger.info("--- Performance Analysis ---")
           
           try:
               # Create test MessageSets
               small_set = MessageSet.from_range(1000, 1100, mailbox="INBOX")
               medium_set = MessageSet.from_range(1000, 1500, mailbox="INBOX")
               large_set = MessageSet.from_range(1000, 2000, mailbox="INBOX")
               
               test_sets = [
                   ("Small", small_set),
                   ("Medium", medium_set),
                   ("Large", large_set)
               ]
               
               # Performance tests
               operations = [
                   ("Length", lambda s: len(s)),
                   ("Optimization", lambda s: s.optimized_string),
                   ("Iteration", lambda s: list(s.iter_batches(batch_size=10)))
               ]
               
               logger.info("📊 Performance Analysis Results:")
               logger.info(f"{'Operation':<12} {'Small':<10} {'Medium':<10} {'Large':<10}")
               logger.info("-" * 50)
               
               for op_name, operation in operations:
                   times = []
                   
                   for set_name, test_set in test_sets:
                       start_time = time.time()
                       try:
                           result = operation(test_set)
                           elapsed = time.time() - start_time
                           times.append(f"{elapsed:.4f}s")
                       except Exception as e:
                           times.append("Error")
                   
                   logger.info(f"{op_name:<12} {times[0]:<10} {times[1]:<10} {times[2]:<10}")
               
               logger.info("✓ Performance analysis completed")
               
           except Exception as e:
               logger.error(f"Failed performance analysis: {e}")
   
       def demonstrate_integration_patterns(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate integration patterns with other components.
           """
           logger.info("--- Integration Patterns ---")
           
           try:
               # Search integration
               self.demonstrate_search_integration(uid_service)
               
               # Service integration
               self.demonstrate_service_integration(uid_service)
               
               # Workflow integration
               self.demonstrate_workflow_integration(uid_service)
               
               logger.info("✓ Integration patterns completed")
               
           except Exception as e:
               logger.error(f"Failed integration patterns: {e}")
   
       def demonstrate_search_integration(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate integration with search operations.
           """
           logger.info("--- Search Integration ---")
           
           try:
               # Complex search with MessageSet operations
               base_search = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               priority_search = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.FLAGGED
               )
               
               # Combine searches
               if not base_search.is_empty() and not priority_search.is_empty():
                   combined_result = base_search.intersection(priority_search)
                   logger.info(f"📧 Combined search result: {len(combined_result)} messages")
               
               # Multi-step search refinement
               refined_search = base_search
               
               refinements = [
                   ("Unread", IMAPSearchCriteria.UNSEEN),
                   ("Large", IMAPSearchCriteria.larger(1024))
               ]
               
               for refinement_name, criteria in refinements:
                   try:
                       refinement_set = uid_service.create_message_set_from_search(criteria)
                       if not refined_search.is_empty() and not refinement_set.is_empty():
                           refined_search = refined_search.intersection(refinement_set)
                           logger.info(f"📧 After {refinement_name}: {len(refined_search)} messages")
                   except Exception as e:
                       logger.warning(f"⚠ Refinement {refinement_name} failed: {e}")
               
               logger.info("✓ Search integration completed")
               
           except Exception as e:
               logger.error(f"Failed search integration: {e}")
   
       def demonstrate_service_integration(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate integration with IMAP services.
           """
           logger.info("--- Service Integration ---")
           
           try:
               # Get MessageSet from search
               sample_set = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               
               if sample_set.is_empty():
                   logger.info("📧 No messages for service integration")
                   return
               
               # Use with different services
               logger.info(f"📧 Using MessageSet with services:")
               
               # Fetch service
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.HEADER)
               if fetch_result.success:
                   logger.info(f"  ✓ Fetch service: {len(fetch_result.metadata.get('fetched_messages', []))} messages")
               
               # Flag service (would use IMAPFlagService)
               logger.info("  ✓ Flag service: Ready for flag operations")
               
               # Search service
               logger.info("  ✓ Search service: Integrated with search results")
               
               logger.info("✓ Service integration completed")
               
           except Exception as e:
               logger.error(f"Failed service integration: {e}")
   
       def demonstrate_workflow_integration(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate integration with workflow patterns.
           """
           logger.info("--- Workflow Integration ---")
           
           try:
               # Workflow: Process → Filter → Act
               logger.info("📧 Workflow: Process → Filter → Act")
               
               # Step 1: Process (get messages)
               all_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               
               if all_messages.is_empty():
                   logger.info("📧 No messages for workflow")
                   return
               
               logger.info(f"  1. Process: {len(all_messages)} messages")
               
               # Step 2: Filter (apply criteria)
               filtered_messages = all_messages
               
               # Apply filters
               for i, (filter_name, criteria) in enumerate([
                   ("Unread", IMAPSearchCriteria.UNSEEN),
                   ("Important", IMAPSearchCriteria.FLAGGED)
               ], 1):
                   try:
                       filter_set = uid_service.create_message_set_from_search(criteria)
                       if not filtered_messages.is_empty() and not filter_set.is_empty():
                           filtered_messages = filtered_messages.intersection(filter_set)
                           logger.info(f"  2.{i}. Filter {filter_name}: {len(filtered_messages)} messages")
                   except Exception as e:
                       logger.warning(f"  ⚠ Filter {filter_name} failed: {e}")
               
               # Step 3: Act (process results)
               logger.info(f"  3. Act: Processing {len(filtered_messages)} final messages")
               
               # Batch processing for action
               if not filtered_messages.is_empty():
                   action_count = 0
                   for batch in filtered_messages.iter_batches(batch_size=10):
                       action_count += len(batch)
                       # Simulate action
                       logger.info(f"     Action on batch: {len(batch)} messages")
                       
                       if action_count >= 20:  # Limit demo
                           break
               
               logger.info("✓ Workflow integration completed")
               
           except Exception as e:
               logger.error(f"Failed workflow integration: {e}")


   def main():
       """
       Main function to run the MessageSet usage example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = MessageSetUsageExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_message_set_usage()
           logger.info("🎉 Advanced MessageSet usage example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


MessageSet API Reference
------------------------

Creation Methods
~~~~~~~~~~~~~~~~

.. code-block:: python

   # From UIDs (recommended)
   msg_set = MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")
   
   # From sequence numbers
   msg_set = MessageSet.from_sequence_numbers([1, 2, 3], mailbox="INBOX")
   
   # From range
   msg_set = MessageSet.from_range(1000, 1020, mailbox="INBOX")
   
   # All messages
   msg_set = MessageSet.all_messages(mailbox="INBOX")
   
   # From email messages
   msg_set = MessageSet.from_email_messages(email_messages)

Set Operations
~~~~~~~~~~~~~~

.. code-block:: python

   # Union
   combined = set_a.union(set_b)
   
   # Intersection
   common = set_a.intersection(set_b)
   
   # Difference
   remaining = set_a.subtract(set_b)
   
   # Check if empty
   if not msg_set.is_empty():
       # Process messages
       pass

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Iterate in batches
   for batch in msg_set.iter_batches(batch_size=50):
       # Process batch
       result = uid_service.uid_fetch(batch, MessagePart.HEADER)
       
   # Adaptive batch sizing
   batch_size = 25
   for batch in msg_set.iter_batches(batch_size=batch_size):
       start_time = time.time()
       # Process batch
       processing_time = time.time() - start_time
       
       # Adjust batch size based on performance
       if processing_time < 1.0:
           batch_size = min(batch_size * 1.2, 100)
       elif processing_time > 3.0:
           batch_size = max(batch_size * 0.8, 10)

Optimization Features
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimized string representation
   optimized = msg_set.optimized_string
   
   # Cached properties
   count = len(msg_set)  # Cached after first access
   
   # Range compression
   # [1,2,3,5,6,7,10] becomes "1:3,5:7,10"

Persistence
~~~~~~~~~~~

.. code-block:: python

   # JSON persistence
   data = {
       'mailbox': msg_set.mailbox,
       'is_uid': msg_set.is_uid,
       'ids': list(msg_set.parsed_ids),
       'timestamp': datetime.now().isoformat()
   }
   
   with open('message_set.json', 'w') as f:
       json.dump(data, f)
   
   # Binary persistence
   with open('message_set.pickle', 'wb') as f:
       pickle.dump(msg_set, f)

Best Practices
--------------

✅ **DO:**

- Use `from_uids()` for reliable UID-based operations

- Implement batch processing for large sets

- Use set operations for complex filtering

- Cache frequently used MessageSet objects

- Use range compression for efficiency

- Implement proper error handling

❌ **DON'T:**
- Use sequence numbers in production

- Load all messages into memory at once

- Ignore batch processing for large sets

- Skip optimization for performance-critical code

- Forget to handle empty MessageSet objects

- Use inefficient string concatenation

Performance Tips
----------------

1. **Batch Processing**: Use `iter_batches()` for large sets

2. **Set Operations**: Use intersection/union instead of manual filtering

3. **Caching**: Cache frequently accessed MessageSet objects

4. **Range Compression**: Leverage automatic range optimization

5. **Lazy Evaluation**: Properties are computed only when needed

6. **Memory Management**: Use batch iteration to limit memory usage

Common Patterns
---------------

Search and Filter
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get base set
   base_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(30))
   
   # Apply filters
   unread_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.UNSEEN)
   
   # Combine
   result = base_set.intersection(unread_set)

Progressive Processing
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Start with all messages
   current_set = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
   
   # Apply progressive filters
   for filter_name, criteria in filters:
       filter_set = uid_service.create_message_set_from_search(criteria)
       current_set = current_set.intersection(filter_set)
       
       if current_set.is_empty():
           break

Batch Operations
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Process in batches
   for batch in large_message_set.iter_batches(batch_size=100):
       # Fetch batch
       result = uid_service.uid_fetch(batch, MessagePart.HEADER)
       
       # Process batch results
       if result.success:
           messages = result.metadata.get('fetched_messages', [])
           # Process messages

Next Steps
----------

For more advanced patterns, see:

- :doc:`large_volume_handling` - High-performance processing
- :doc:`production_patterns` - Production-ready patterns
- :doc:`mailbox_management` - Mailbox operations
- :doc:`uid_search_operations` - Advanced search patterns 