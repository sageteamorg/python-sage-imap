.. _large_volume_handling:

Large Volume Email Handling
===========================

This example demonstrates how to handle large volumes of emails efficiently using Python Sage IMAP with **UID-based operations**, batching, and optimization techniques.

**⚠️ IMPORTANT: This example emphasizes performance and reliability for large-scale email processing!**

Overview
--------

You'll learn how to:

- Process thousands of emails efficiently
- Use batching for memory management
- Implement parallel processing
- Optimize search operations
- Handle rate limiting and timeouts
- Monitor processing performance
- Implement resumable operations
- Use caching for repeated operations

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of performance optimization

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Large Volume Email Handling Example
   
   This example demonstrates efficient handling of large volumes of emails
   using batching, parallel processing, and optimization techniques.
   """
   
   import logging
   import time
   import threading
   import concurrent.futures
   from datetime import datetime, timedelta
   from typing import List, Dict, Optional, Iterator, Tuple
   from collections import defaultdict
   import json
   import pickle
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
   
   
   class LargeVolumeHandler:
       """
       Efficient handler for large volumes of emails.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the large volume handler.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 60.0  # Longer timeout for large operations
           }
           
           # Performance tracking
           self.performance_stats = {
               'total_processed': 0,
               'total_errors': 0,
               'processing_times': [],
               'batch_sizes': [],
               'start_time': None
           }
           
           # Configuration
           self.default_batch_size = 100
           self.max_workers = 4
           self.cache_dir = Path("email_cache")
           self.cache_dir.mkdir(exist_ok=True)
           
       def demonstrate_large_volume_operations(self):
           """
           Demonstrate comprehensive large volume operations.
           """
           logger.info("=== Large Volume Email Handling Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Initialize performance tracking
                   self.performance_stats['start_time'] = time.time()
                   
                   # Basic large volume processing
                   self.demonstrate_batch_processing(uid_service)
                   
                   # Parallel processing
                   self.demonstrate_parallel_processing(uid_service)
                   
                   # Memory-efficient processing
                   self.demonstrate_memory_efficient_processing(uid_service)
                   
                   # Search optimization
                   self.demonstrate_search_optimization(uid_service)
                   
                   # Resumable operations
                   self.demonstrate_resumable_operations(uid_service)
                   
                   # Performance monitoring
                   self.demonstrate_performance_monitoring(uid_service)
                   
                   # Rate limiting and throttling
                   self.demonstrate_rate_limiting(uid_service)
                   
                   # Generate final report
                   self.generate_performance_report()
                   
                   logger.info("✓ Large volume operations completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Large volume operations failed: {e}")
               raise
   
       def demonstrate_batch_processing(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate efficient batch processing of large message sets.
           """
           logger.info("--- Batch Processing Operations ---")
           
           try:
               # Get all messages for batch processing
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               
               if all_messages.is_empty():
                   logger.info("📧 No messages for batch processing")
                   return
               
               logger.info(f"📧 Processing {len(all_messages)} messages in batches")
               
               # Adaptive batch sizing
               self.adaptive_batch_processing(uid_service, all_messages)
               
               # Fixed batch processing
               self.fixed_batch_processing(uid_service, all_messages)
               
               # Priority batch processing
               self.priority_batch_processing(uid_service, all_messages)
               
               logger.info("  ✓ Batch processing operations completed")
               
           except Exception as e:
               logger.error(f"Failed batch processing: {e}")
   
       def adaptive_batch_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Adaptive batch processing that adjusts batch size based on performance.
           """
           logger.info("--- Adaptive Batch Processing ---")
           
           try:
               batch_size = self.default_batch_size
               processed_count = 0
               
               logger.info(f"  📧 Starting with batch size: {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   start_time = time.time()
                   
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   processing_time = time.time() - start_time
                   
                   if result.success:
                       processed_count += len(batch)
                       
                       # Adaptive batch size adjustment
                       if processing_time < 2.0:  # Too fast, increase batch size
                           batch_size = min(batch_size * 1.2, 200)
                       elif processing_time > 5.0:  # Too slow, decrease batch size
                           batch_size = max(batch_size * 0.8, 50)
                       
                       logger.info(f"    ✓ Batch {batch_num}: {len(batch)} messages "
                                  f"({processing_time:.2f}s, next batch: {int(batch_size)})")
                   else:
                       logger.warning(f"    ⚠ Batch {batch_num} failed: {result.error_message}")
                   
                   # Update performance stats
                   self.performance_stats['processing_times'].append(processing_time)
                   self.performance_stats['batch_sizes'].append(len(batch))
                   
                   # Limit demo to first 5 batches
                   if batch_num >= 5:
                       logger.info("    ... stopping adaptive demo at batch 5")
                       break
               
               logger.info(f"  ✓ Adaptive processing: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed adaptive batch processing: {e}")
   
       def fixed_batch_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Fixed batch size processing with performance tracking.
           """
           logger.info("--- Fixed Batch Processing ---")
           
           try:
               batch_size = 75
               processed_count = 0
               
               logger.info(f"  📧 Using fixed batch size: {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   start_time = time.time()
                   
                   # Process batch with error handling
                   try:
                       result = self.process_batch(uid_service, batch, batch_num)
                       processing_time = time.time() - start_time
                       
                       if result.success:
                           processed_count += len(batch)
                           logger.info(f"    ✓ Batch {batch_num}: {len(batch)} messages ({processing_time:.2f}s)")
                       else:
                           logger.warning(f"    ⚠ Batch {batch_num} failed: {result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Batch {batch_num} error: {e}")
                       continue
                   
                   # Brief pause to avoid overwhelming server
                   time.sleep(0.1)
                   
                   # Limit demo to first 3 batches
                   if batch_num >= 3:
                       logger.info("    ... stopping fixed demo at batch 3")
                       break
               
               logger.info(f"  ✓ Fixed processing: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed fixed batch processing: {e}")
   
       def priority_batch_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Priority-based batch processing for important messages first.
           """
           logger.info("--- Priority Batch Processing ---")
           
           try:
               # Separate messages by priority
               priority_groups = self.group_messages_by_priority(uid_service, messages)
               
               total_processed = 0
               
               # Process in priority order
               for priority, message_set in priority_groups.items():
                   if message_set.is_empty():
                       continue
                   
                   logger.info(f"  📧 Processing {priority} priority: {len(message_set)} messages")
                   
                   # Use smaller batches for high priority
                   batch_size = 25 if priority == 'high' else 50
                   
                   processed_count = 0
                   for batch_num, batch in enumerate(message_set.iter_batches(batch_size=batch_size), 1):
                       result = self.process_batch(uid_service, batch, batch_num, priority)
                       
                       if result.success:
                           processed_count += len(batch)
                       
                       # Limit demo batches
                       if batch_num >= 2:
                           logger.info(f"    ... stopping {priority} demo at batch 2")
                           break
                   
                   total_processed += processed_count
                   logger.info(f"    ✓ {priority} priority: {processed_count} messages processed")
               
               logger.info(f"  ✓ Priority processing: {total_processed} messages processed")
               
           except Exception as e:
               logger.error(f"Failed priority batch processing: {e}")
   
       def group_messages_by_priority(self, uid_service: IMAPMailboxUIDService, messages: MessageSet) -> Dict[str, MessageSet]:
           """
           Group messages by priority levels.
           """
           try:
               priority_groups = {
                   'high': MessageSet.from_uids([], mailbox="INBOX"),
                   'medium': MessageSet.from_uids([], mailbox="INBOX"),
                   'low': MessageSet.from_uids([], mailbox="INBOX")
               }
               
               # High priority: flagged messages
               high_priority = uid_service.create_message_set_from_search(IMAPSearchCriteria.FLAGGED)
               if not high_priority.is_empty():
                   priority_groups['high'] = messages.intersection(high_priority)
               
               # Medium priority: recent messages
               medium_priority = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               if not medium_priority.is_empty():
                   priority_groups['medium'] = messages.intersection(medium_priority).subtract(priority_groups['high'])
               
               # Low priority: everything else
               priority_groups['low'] = messages.subtract(priority_groups['high']).subtract(priority_groups['medium'])
               
               return priority_groups
               
           except Exception as e:
               logger.error(f"Failed to group messages by priority: {e}")
               return {
                   'high': MessageSet.from_uids([], mailbox="INBOX"),
                   'medium': MessageSet.from_uids([], mailbox="INBOX"),
                   'low': messages
               }
   
       def process_batch(self, uid_service: IMAPMailboxUIDService, batch: MessageSet, batch_num: int, priority: str = None) -> 'ProcessingResult':
           """
           Process a single batch of messages.
           """
           try:
               # Fetch message headers for processing
               fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   # Process each message in the batch
                   for message in messages:
                       # Simulate message processing
                       self.process_single_message(message, priority)
                   
                   return ProcessingResult(success=True, processed_count=len(messages))
               else:
                   return ProcessingResult(success=False, error_message=fetch_result.error_message)
           
           except Exception as e:
               return ProcessingResult(success=False, error_message=str(e))
   
       def process_single_message(self, message, priority: str = None):
           """
           Process a single message.
           """
           try:
               # Simulate processing time
               time.sleep(0.01)
               
               # Update performance stats
               self.performance_stats['total_processed'] += 1
               
               # Log processing (limited to avoid spam)
               if self.performance_stats['total_processed'] % 100 == 0:
                   logger.debug(f"Processed {self.performance_stats['total_processed']} messages")
           
           except Exception as e:
               self.performance_stats['total_errors'] += 1
               logger.error(f"Error processing message {message.uid}: {e}")
   
       def demonstrate_parallel_processing(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate parallel processing of large message sets.
           """
           logger.info("--- Parallel Processing Operations ---")
           
           try:
               # Get messages for parallel processing
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No recent messages for parallel processing")
                   return
               
               logger.info(f"📧 Parallel processing {len(recent_messages)} recent messages")
               
               # Thread-based parallel processing
               self.thread_based_parallel_processing(recent_messages)
               
               # Process pool parallel processing
               self.process_pool_parallel_processing(recent_messages)
               
               logger.info("  ✓ Parallel processing operations completed")
               
           except Exception as e:
               logger.error(f"Failed parallel processing: {e}")
   
       def thread_based_parallel_processing(self, messages: MessageSet):
           """
           Thread-based parallel processing.
           """
           logger.info("--- Thread-Based Parallel Processing ---")
           
           try:
               # Split messages into chunks for parallel processing
               num_threads = self.max_workers
               chunk_size = len(messages) // num_threads
               
               if chunk_size == 0:
                   chunk_size = 1
               
               logger.info(f"  📧 Using {num_threads} threads, chunk size: {chunk_size}")
               
               # Create chunks
               chunks = []
               all_uids = list(messages.parsed_ids)
               
               for i in range(0, len(all_uids), chunk_size):
                   chunk_uids = all_uids[i:i + chunk_size]
                   chunk = MessageSet.from_uids(chunk_uids, mailbox="INBOX")
                   chunks.append(chunk)
               
               # Process chunks in parallel
               with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                   futures = []
                   
                   for i, chunk in enumerate(chunks):
                       future = executor.submit(self.process_chunk_parallel, chunk, i + 1)
                       futures.append(future)
                   
                   # Wait for all threads to complete
                   completed_count = 0
                   for future in concurrent.futures.as_completed(futures):
                       try:
                           result = future.result()
                           if result.success:
                               completed_count += result.processed_count
                               logger.info(f"    ✓ Thread completed: {result.processed_count} messages")
                           else:
                               logger.warning(f"    ⚠ Thread failed: {result.error_message}")
                       except Exception as e:
                           logger.error(f"    ❌ Thread error: {e}")
               
               logger.info(f"  ✓ Thread-based processing: {completed_count} messages completed")
               
           except Exception as e:
               logger.error(f"Failed thread-based parallel processing: {e}")
   
       def process_pool_parallel_processing(self, messages: MessageSet):
           """
           Process pool parallel processing.
           """
           logger.info("--- Process Pool Parallel Processing ---")
           
           try:
               # Note: This is a simplified demonstration
               # In practice, you'd need to handle IMAP connections in each process
               
               logger.info(f"  📧 Would process {len(messages)} messages using process pool")
               logger.info(f"  📧 Process pool requires connection management per process")
               logger.info(f"  📧 Thread pool is often more suitable for IMAP operations")
               
               # For demonstration, we'll simulate the concept
               num_processes = min(self.max_workers, 2)  # Limit processes for demo
               
               # Split messages into process chunks
               chunk_size = len(messages) // num_processes
               
               logger.info(f"  📧 Would use {num_processes} processes, chunk size: {chunk_size}")
               
               # Simulate process pool results
               simulated_results = []
               for i in range(num_processes):
                   simulated_results.append(ProcessingResult(
                       success=True, 
                       processed_count=chunk_size
                   ))
               
               total_processed = sum(r.processed_count for r in simulated_results if r.success)
               logger.info(f"  ✓ Process pool simulation: {total_processed} messages would be processed")
               
           except Exception as e:
               logger.error(f"Failed process pool parallel processing: {e}")
   
       def process_chunk_parallel(self, chunk: MessageSet, thread_id: int) -> 'ProcessingResult':
           """
           Process a chunk of messages in parallel.
           """
           try:
               # Create separate connection for this thread
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Process the chunk
                   result = self.process_batch(uid_service, chunk, thread_id)
                   
                   return result
           
           except Exception as e:
               return ProcessingResult(success=False, error_message=str(e))
   
       def demonstrate_memory_efficient_processing(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate memory-efficient processing for very large datasets.
           """
           logger.info("--- Memory-Efficient Processing ---")
           
           try:
               # Get all messages
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               
               if all_messages.is_empty():
                   logger.info("📧 No messages for memory-efficient processing")
                   return
               
               logger.info(f"📧 Memory-efficient processing of {len(all_messages)} messages")
               
               # Streaming processing
               self.streaming_message_processing(uid_service, all_messages)
               
               # Lazy loading processing
               self.lazy_loading_processing(uid_service, all_messages)
               
               # Chunked processing with garbage collection
               self.chunked_processing_with_gc(uid_service, all_messages)
               
               logger.info("  ✓ Memory-efficient processing completed")
               
           except Exception as e:
               logger.error(f"Failed memory-efficient processing: {e}")
   
       def streaming_message_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Stream messages for processing without loading all into memory.
           """
           logger.info("--- Streaming Message Processing ---")
           
           try:
               processed_count = 0
               batch_size = 50  # Small batch size for memory efficiency
               
               logger.info(f"  📧 Streaming processing with batch size: {batch_size}")
               
               # Process in small batches to minimize memory usage
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   # Process batch immediately and discard
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   if result.success:
                       processed_count += result.processed_count
                   
                   # Force garbage collection for large datasets
                   if batch_num % 10 == 0:
                       import gc
                       gc.collect()
                   
                   # Limit demo
                   if batch_num >= 5:
                       logger.info("    ... stopping streaming demo at batch 5")
                       break
               
               logger.info(f"  ✓ Streaming processing: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed streaming processing: {e}")
   
       def lazy_loading_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Lazy loading processing - only load data when needed.
           """
           logger.info("--- Lazy Loading Processing ---")
           
           try:
               processed_count = 0
               
               # Create iterator for lazy loading
               message_iterator = self.create_lazy_message_iterator(uid_service, messages)
               
               logger.info(f"  📧 Lazy loading processing iterator created")
               
               # Process messages one by one
               for count, message_data in enumerate(message_iterator, 1):
                   # Process message data
                   self.process_message_data(message_data)
                   processed_count += 1
                   
                   # Limit demo
                   if count >= 20:
                       logger.info("    ... stopping lazy loading demo at 20 messages")
                       break
               
               logger.info(f"  ✓ Lazy loading processing: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed lazy loading processing: {e}")
   
       def create_lazy_message_iterator(self, uid_service: IMAPMailboxUIDService, messages: MessageSet) -> Iterator[Dict]:
           """
           Create a lazy iterator for message processing.
           """
           batch_size = 10
           
           for batch in messages.iter_batches(batch_size=batch_size):
               # Fetch this batch
               fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
               
               if fetch_result.success:
                   batch_messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   for message in batch_messages:
                       yield {
                           'uid': message.uid,
                           'subject': message.subject,
                           'sender': str(message.from_address),
                           'date': message.date,
                           'size': message.size
                       }
   
       def process_message_data(self, message_data: Dict):
           """
           Process message data from lazy loading.
           """
           # Simulate processing
           time.sleep(0.001)
           
           # Log every 10th message
           if self.performance_stats['total_processed'] % 10 == 0:
               logger.debug(f"Lazy processed: {message_data['subject']}")
   
       def chunked_processing_with_gc(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Chunked processing with explicit garbage collection.
           """
           logger.info("--- Chunked Processing with Garbage Collection ---")
           
           try:
               import gc
               
               chunk_size = 100
               processed_count = 0
               
               logger.info(f"  📧 Chunked processing with GC, chunk size: {chunk_size}")
               
               for chunk_num, chunk in enumerate(messages.iter_batches(batch_size=chunk_size), 1):
                   # Process chunk
                   result = self.process_batch(uid_service, chunk, chunk_num)
                   
                   if result.success:
                       processed_count += result.processed_count
                   
                   # Explicit garbage collection every 5 chunks
                   if chunk_num % 5 == 0:
                       gc.collect()
                       logger.info(f"    🗑 Garbage collection at chunk {chunk_num}")
                   
                   # Limit demo
                   if chunk_num >= 3:
                       logger.info("    ... stopping chunked GC demo at chunk 3")
                       break
               
               logger.info(f"  ✓ Chunked GC processing: {processed_count} messages processed")
               
           except Exception as e:
               logger.error(f"Failed chunked processing with GC: {e}")
   
       def demonstrate_search_optimization(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate search optimization techniques for large datasets.
           """
           logger.info("--- Search Optimization ---")
           
           try:
               # Cached search operations
               self.cached_search_operations(uid_service)
               
               # Indexed search operations
               self.indexed_search_operations(uid_service)
               
               # Progressive search refinement
               self.progressive_search_refinement(uid_service)
               
               logger.info("  ✓ Search optimization completed")
               
           except Exception as e:
               logger.error(f"Failed search optimization: {e}")
   
       def cached_search_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate cached search operations.
           """
           logger.info("--- Cached Search Operations ---")
           
           try:
               # Create search cache
               search_cache = {}
               
               def cached_search(cache_key: str, criteria: IMAPSearchCriteria) -> MessageSet:
                   if cache_key not in search_cache:
                       start_time = time.time()
                       search_cache[cache_key] = uid_service.create_message_set_from_search(criteria)
                       search_time = time.time() - start_time
                       logger.info(f"    📊 Cached search '{cache_key}': {search_time:.3f}s")
                   else:
                       logger.info(f"    📊 Using cached result for '{cache_key}'")
                   
                   return search_cache[cache_key]
               
               # Perform searches with caching
               searches = [
                   ("all_messages", IMAPSearchCriteria.ALL),
                   ("unread_messages", IMAPSearchCriteria.UNSEEN),
                   ("flagged_messages", IMAPSearchCriteria.FLAGGED),
                   ("recent_messages", IMAPSearchCriteria.since_days(7))
               ]
               
               for cache_key, criteria in searches:
                   messages = cached_search(cache_key, criteria)
                   logger.info(f"    📧 {cache_key}: {len(messages)} messages")
               
               # Demonstrate cache reuse
               logger.info("    📊 Demonstrating cache reuse:")
               cached_search("unread_messages", IMAPSearchCriteria.UNSEEN)
               cached_search("flagged_messages", IMAPSearchCriteria.FLAGGED)
               
               logger.info(f"  ✓ Search cache contains {len(search_cache)} entries")
               
           except Exception as e:
               logger.error(f"Failed cached search operations: {e}")
   
       def indexed_search_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate indexed search operations.
           """
           logger.info("--- Indexed Search Operations ---")
           
           try:
               # Build search index
               search_index = self.build_search_index(uid_service)
               
               # Use index for fast lookups
               self.use_search_index(search_index)
               
               logger.info("  ✓ Indexed search operations completed")
               
           except Exception as e:
               logger.error(f"Failed indexed search operations: {e}")
   
       def build_search_index(self, uid_service: IMAPMailboxUIDService) -> Dict:
           """
           Build a search index for common queries.
           """
           logger.info("--- Building Search Index ---")
           
           try:
               index = {
                   'by_sender': defaultdict(list),
                   'by_subject_keywords': defaultdict(list),
                   'by_date': defaultdict(list),
                   'by_size': defaultdict(list)
               }
               
               # Get recent messages for indexing
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("    📧 No recent messages for indexing")
                   return index
               
               # Process in batches to build index
               batch_size = 50
               indexed_count = 0
               
               for batch in recent_messages.iter_batches(batch_size=batch_size):
                   fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
                   
                   if fetch_result.success:
                       messages = fetch_result.metadata.get('fetched_messages', [])
                       
                       for message in messages:
                           # Index by sender
                           sender = str(message.from_address) if message.from_address else ""
                           if sender:
                               index['by_sender'][sender].append(message.uid)
                           
                           # Index by subject keywords
                           subject_words = message.subject.lower().split()
                           for word in subject_words:
                               if len(word) > 3:  # Index words longer than 3 characters
                                   index['by_subject_keywords'][word].append(message.uid)
                           
                           # Index by date
                           if message.date:
                               date_key = message.date.strftime("%Y-%m-%d")
                               index['by_date'][date_key].append(message.uid)
                           
                           # Index by size category
                           size_category = self.categorize_message_size(message.size)
                           index['by_size'][size_category].append(message.uid)
                           
                           indexed_count += 1
                   
                   # Limit indexing for demo
                   if indexed_count >= 100:
                       logger.info("    ... stopping indexing demo at 100 messages")
                       break
               
               logger.info(f"    📊 Search index built: {indexed_count} messages indexed")
               logger.info(f"    📊 Index contains:")
               logger.info(f"      • Senders: {len(index['by_sender'])}")
               logger.info(f"      • Keywords: {len(index['by_subject_keywords'])}")
               logger.info(f"      • Dates: {len(index['by_date'])}")
               logger.info(f"      • Size categories: {len(index['by_size'])}")
               
               return index
               
           except Exception as e:
               logger.error(f"Failed to build search index: {e}")
               return {}
   
       def use_search_index(self, index: Dict):
           """
           Use the search index for fast lookups.
           """
           logger.info("--- Using Search Index ---")
           
           try:
               # Search by sender
               if index['by_sender']:
                   sample_sender = list(index['by_sender'].keys())[0]
                   sender_messages = index['by_sender'][sample_sender]
                   logger.info(f"    📧 Messages from {sample_sender}: {len(sender_messages)}")
               
               # Search by keyword
               if index['by_subject_keywords']:
                   sample_keyword = list(index['by_subject_keywords'].keys())[0]
                   keyword_messages = index['by_subject_keywords'][sample_keyword]
                   logger.info(f"    📧 Messages with keyword '{sample_keyword}': {len(keyword_messages)}")
               
               # Search by date
               if index['by_date']:
                   sample_date = list(index['by_date'].keys())[0]
                   date_messages = index['by_date'][sample_date]
                   logger.info(f"    📧 Messages from {sample_date}: {len(date_messages)}")
               
               # Search by size
               if index['by_size']:
                   for size_category, messages in index['by_size'].items():
                       logger.info(f"    📧 {size_category.capitalize()} messages: {len(messages)}")
               
               logger.info("  ✓ Search index usage demonstrated")
               
           except Exception as e:
               logger.error(f"Failed to use search index: {e}")
   
       def categorize_message_size(self, size: int) -> str:
           """
           Categorize message by size.
           """
           if size < 1024:
               return "tiny"
           elif size < 10 * 1024:
               return "small"
           elif size < 100 * 1024:
               return "medium"
           elif size < 1024 * 1024:
               return "large"
           else:
               return "huge"
   
       def progressive_search_refinement(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate progressive search refinement.
           """
           logger.info("--- Progressive Search Refinement ---")
           
           try:
               # Start with broad search
               logger.info("    📧 Starting with broad search...")
               
               broad_search = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               logger.info(f"    📧 Broad search: {len(broad_search)} messages")
               
               # Refine by date
               logger.info("    📧 Refining by date (last 30 days)...")
               
               date_refined = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               logger.info(f"    📧 Date refined: {len(date_refined)} messages")
               
               # Further refine by status
               logger.info("    📧 Further refining by unread status...")
               
               status_refined = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.and_criteria(
                       IMAPSearchCriteria.since_days(30),
                       IMAPSearchCriteria.UNSEEN
                   )
               )
               logger.info(f"    📧 Status refined: {len(status_refined)} messages")
               
               # Final refinement by importance
               logger.info("    📧 Final refinement by importance...")
               
               final_refined = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.and_criteria(
                       IMAPSearchCriteria.since_days(30),
                       IMAPSearchCriteria.UNSEEN,
                       IMAPSearchCriteria.FLAGGED
                   )
               )
               logger.info(f"    📧 Final refined: {len(final_refined)} messages")
               
               # Show refinement efficiency
               if len(broad_search) > 0:
                   efficiency = (len(broad_search) - len(final_refined)) / len(broad_search) * 100
                   logger.info(f"    📊 Refinement efficiency: {efficiency:.1f}% reduction")
               
               logger.info("  ✓ Progressive search refinement completed")
               
           except Exception as e:
               logger.error(f"Failed progressive search refinement: {e}")
   
       def demonstrate_resumable_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate resumable operations for large datasets.
           """
           logger.info("--- Resumable Operations ---")
           
           try:
               # Create checkpoint system
               checkpoint_file = self.cache_dir / "processing_checkpoint.json"
               
               # Start resumable operation
               self.start_resumable_operation(uid_service, checkpoint_file)
               
               # Simulate interruption and resume
               self.simulate_resume_operation(uid_service, checkpoint_file)
               
               logger.info("  ✓ Resumable operations completed")
               
           except Exception as e:
               logger.error(f"Failed resumable operations: {e}")
   
       def start_resumable_operation(self, uid_service: IMAPMailboxUIDService, checkpoint_file: Path):
           """
           Start a resumable operation with checkpointing.
           """
           logger.info("--- Starting Resumable Operation ---")
           
           try:
               # Get messages to process
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               
               if all_messages.is_empty():
                   logger.info("    📧 No messages for resumable operation")
                   return
               
               # Create checkpoint data
               checkpoint_data = {
                   'total_messages': len(all_messages),
                   'processed_messages': 0,
                   'last_processed_uid': None,
                   'start_time': time.time(),
                   'batch_size': 25
               }
               
               # Save initial checkpoint
               self.save_checkpoint(checkpoint_file, checkpoint_data)
               
               logger.info(f"    📧 Starting resumable processing of {len(all_messages)} messages")
               
               # Process messages with checkpointing
               processed_count = 0
               for batch_num, batch in enumerate(all_messages.iter_batches(batch_size=25), 1):
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   if result.success:
                       processed_count += result.processed_count
                       
                       # Update checkpoint
                       checkpoint_data['processed_messages'] = processed_count
                       checkpoint_data['last_processed_uid'] = max(batch.parsed_ids)
                       self.save_checkpoint(checkpoint_file, checkpoint_data)
                   
                   # Simulate interruption after 3 batches
                   if batch_num >= 3:
                       logger.info(f"    ⏸ Simulating interruption after {processed_count} messages")
                       break
               
               logger.info(f"    📊 Processed {processed_count} messages before interruption")
               
           except Exception as e:
               logger.error(f"Failed to start resumable operation: {e}")
   
       def simulate_resume_operation(self, uid_service: IMAPMailboxUIDService, checkpoint_file: Path):
           """
           Simulate resuming an interrupted operation.
           """
           logger.info("--- Resuming Interrupted Operation ---")
           
           try:
               # Load checkpoint
               checkpoint_data = self.load_checkpoint(checkpoint_file)
               
               if not checkpoint_data:
                   logger.info("    📧 No checkpoint found to resume")
                   return
               
               logger.info(f"    📧 Resuming from checkpoint:")
               logger.info(f"      • Total messages: {checkpoint_data['total_messages']}")
               logger.info(f"      • Already processed: {checkpoint_data['processed_messages']}")
               logger.info(f"      • Last processed UID: {checkpoint_data['last_processed_uid']}")
               
               # Find remaining messages
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               
               if checkpoint_data['last_processed_uid']:
                   # Filter to get only unprocessed messages
                   remaining_uids = [uid for uid in all_messages.parsed_ids 
                                   if uid > checkpoint_data['last_processed_uid']]
                   
                   if remaining_uids:
                       remaining_messages = MessageSet.from_uids(remaining_uids, mailbox="INBOX")
                       
                       logger.info(f"    📧 Resuming with {len(remaining_messages)} remaining messages")
                       
                       # Continue processing
                       processed_count = checkpoint_data['processed_messages']
                       
                       for batch_num, batch in enumerate(remaining_messages.iter_batches(batch_size=25), 1):
                           result = self.process_batch(uid_service, batch, batch_num)
                           
                           if result.success:
                               processed_count += result.processed_count
                               
                               # Update checkpoint
                               checkpoint_data['processed_messages'] = processed_count
                               checkpoint_data['last_processed_uid'] = max(batch.parsed_ids)
                               self.save_checkpoint(checkpoint_file, checkpoint_data)
                           
                           # Limit resume demo
                           if batch_num >= 2:
                               logger.info("    ... stopping resume demo at batch 2")
                               break
                       
                       logger.info(f"    ✓ Resumed processing: {processed_count} total messages processed")
                   else:
                       logger.info("    📧 No remaining messages to process")
               
               # Clean up checkpoint
               if checkpoint_file.exists():
                   checkpoint_file.unlink()
                   logger.info("    🗑 Checkpoint file cleaned up")
               
           except Exception as e:
               logger.error(f"Failed to resume operation: {e}")
   
       def save_checkpoint(self, checkpoint_file: Path, checkpoint_data: Dict):
           """
           Save checkpoint data to file.
           """
           try:
               with open(checkpoint_file, 'w') as f:
                   json.dump(checkpoint_data, f, indent=2)
           except Exception as e:
               logger.error(f"Failed to save checkpoint: {e}")
   
       def load_checkpoint(self, checkpoint_file: Path) -> Optional[Dict]:
           """
           Load checkpoint data from file.
           """
           try:
               if checkpoint_file.exists():
                   with open(checkpoint_file, 'r') as f:
                       return json.load(f)
               return None
           except Exception as e:
               logger.error(f"Failed to load checkpoint: {e}")
               return None
   
       def demonstrate_performance_monitoring(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate performance monitoring during large operations.
           """
           logger.info("--- Performance Monitoring ---")
           
           try:
               # Real-time performance monitoring
               self.real_time_performance_monitoring(uid_service)
               
               # Performance analysis
               self.performance_analysis()
               
               # Resource usage monitoring
               self.resource_usage_monitoring()
               
               logger.info("  ✓ Performance monitoring completed")
               
           except Exception as e:
               logger.error(f"Failed performance monitoring: {e}")
   
       def real_time_performance_monitoring(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate real-time performance monitoring.
           """
           logger.info("--- Real-Time Performance Monitoring ---")
           
           try:
               # Get messages for monitoring
               messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               if messages.is_empty():
                   logger.info("    📧 No messages for performance monitoring")
                   return
               
               # Monitor processing with timing
               start_time = time.time()
               processed_count = 0
               batch_times = []
               
               logger.info(f"    📧 Monitoring processing of {len(messages)} messages")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=20), 1):
                   batch_start = time.time()
                   
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   batch_time = time.time() - batch_start
                   batch_times.append(batch_time)
                   
                   if result.success:
                       processed_count += result.processed_count
                   
                   # Real-time performance metrics
                   elapsed_time = time.time() - start_time
                   throughput = processed_count / elapsed_time if elapsed_time > 0 else 0
                   
                   logger.info(f"    📊 Batch {batch_num}: {batch_time:.2f}s, "
                              f"Throughput: {throughput:.1f} msg/s")
                   
                   # Limit monitoring demo
                   if batch_num >= 5:
                       logger.info("    ... stopping monitoring demo at batch 5")
                       break
               
               # Final metrics
               total_time = time.time() - start_time
               avg_batch_time = sum(batch_times) / len(batch_times) if batch_times else 0
               final_throughput = processed_count / total_time if total_time > 0 else 0
               
               logger.info(f"    📊 Final metrics:")
               logger.info(f"      • Total time: {total_time:.2f}s")
               logger.info(f"      • Average batch time: {avg_batch_time:.2f}s")
               logger.info(f"      • Final throughput: {final_throughput:.1f} msg/s")
               
           except Exception as e:
               logger.error(f"Failed real-time performance monitoring: {e}")
   
       def performance_analysis(self):
           """
           Analyze accumulated performance data.
           """
           logger.info("--- Performance Analysis ---")
           
           try:
               stats = self.performance_stats
               
               if not stats['processing_times']:
                   logger.info("    📊 No performance data to analyze")
                   return
               
               # Calculate metrics
               processing_times = stats['processing_times']
               total_time = sum(processing_times)
               avg_time = total_time / len(processing_times)
               min_time = min(processing_times)
               max_time = max(processing_times)
               
               # Calculate percentiles
               sorted_times = sorted(processing_times)
               p50 = sorted_times[len(sorted_times) // 2]
               p95 = sorted_times[int(len(sorted_times) * 0.95)]
               
               logger.info(f"    📊 Performance Analysis:")
               logger.info(f"      • Total processed: {stats['total_processed']}")
               logger.info(f"      • Total errors: {stats['total_errors']}")
               logger.info(f"      • Total batches: {len(processing_times)}")
               logger.info(f"      • Average batch time: {avg_time:.3f}s")
               logger.info(f"      • Min batch time: {min_time:.3f}s")
               logger.info(f"      • Max batch time: {max_time:.3f}s")
               logger.info(f"      • P50 batch time: {p50:.3f}s")
               logger.info(f"      • P95 batch time: {p95:.3f}s")
               
               # Calculate throughput
               if stats['start_time']:
                   elapsed = time.time() - stats['start_time']
                   throughput = stats['total_processed'] / elapsed if elapsed > 0 else 0
                   logger.info(f"      • Overall throughput: {throughput:.1f} msg/s")
               
               # Error rate
               error_rate = stats['total_errors'] / max(stats['total_processed'], 1) * 100
               logger.info(f"      • Error rate: {error_rate:.2f}%")
               
           except Exception as e:
               logger.error(f"Failed performance analysis: {e}")
   
       def resource_usage_monitoring(self):
           """
           Monitor resource usage during processing.
           """
           logger.info("--- Resource Usage Monitoring ---")
           
           try:
               import psutil
               import os
               
               # Get current process
               process = psutil.Process(os.getpid())
               
               # Memory usage
               memory_info = process.memory_info()
               memory_mb = memory_info.rss / 1024 / 1024
               
               # CPU usage
               cpu_percent = process.cpu_percent()
               
               logger.info(f"    📊 Resource Usage:")
               logger.info(f"      • Memory usage: {memory_mb:.1f} MB")
               logger.info(f"      • CPU usage: {cpu_percent:.1f}%")
               
               # System resources
               system_memory = psutil.virtual_memory()
               system_cpu = psutil.cpu_percent()
               
               logger.info(f"    📊 System Resources:")
               logger.info(f"      • System memory: {system_memory.percent:.1f}% used")
               logger.info(f"      • System CPU: {system_cpu:.1f}% used")
               
           except ImportError:
               logger.info("    📊 psutil not available for resource monitoring")
           except Exception as e:
               logger.error(f"Failed resource usage monitoring: {e}")
   
       def demonstrate_rate_limiting(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate rate limiting and throttling for server protection.
           """
           logger.info("--- Rate Limiting and Throttling ---")
           
           try:
               # Adaptive rate limiting
               self.adaptive_rate_limiting(uid_service)
               
               # Fixed rate limiting
               self.fixed_rate_limiting(uid_service)
               
               # Burst protection
               self.burst_protection(uid_service)
               
               logger.info("  ✓ Rate limiting and throttling completed")
               
           except Exception as e:
               logger.error(f"Failed rate limiting: {e}")
   
       def adaptive_rate_limiting(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate adaptive rate limiting based on server response.
           """
           logger.info("--- Adaptive Rate Limiting ---")
           
           try:
               messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               if messages.is_empty():
                   logger.info("    📧 No messages for rate limiting demo")
                   return
               
               # Adaptive rate limiting parameters
               min_delay = 0.1  # Minimum delay between operations
               max_delay = 2.0  # Maximum delay between operations
               current_delay = min_delay
               
               logger.info(f"    📊 Adaptive rate limiting: {min_delay}s - {max_delay}s")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=10), 1):
                   start_time = time.time()
                   
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   processing_time = time.time() - start_time
                   
                   if result.success:
                       # Successful operation - decrease delay
                       current_delay = max(min_delay, current_delay * 0.9)
                   else:
                       # Failed operation - increase delay
                       current_delay = min(max_delay, current_delay * 1.5)
                   
                   logger.info(f"    📊 Batch {batch_num}: {processing_time:.2f}s processing, "
                              f"{current_delay:.2f}s delay")
                   
                   # Apply adaptive delay
                   time.sleep(current_delay)
                   
                   # Limit demo
                   if batch_num >= 3:
                       logger.info("    ... stopping adaptive rate limiting demo at batch 3")
                       break
               
           except Exception as e:
               logger.error(f"Failed adaptive rate limiting: {e}")
   
       def fixed_rate_limiting(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate fixed rate limiting.
           """
           logger.info("--- Fixed Rate Limiting ---")
           
           try:
               messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               if messages.is_empty():
                   logger.info("    📧 No messages for fixed rate limiting demo")
                   return
               
               # Fixed rate limiting parameters
               operations_per_second = 2
               delay_between_operations = 1.0 / operations_per_second
               
               logger.info(f"    📊 Fixed rate limiting: {operations_per_second} ops/sec")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=5), 1):
                   start_time = time.time()
                   
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   processing_time = time.time() - start_time
                   
                   logger.info(f"    📊 Batch {batch_num}: {processing_time:.2f}s processing")
                   
                   # Apply fixed delay
                   time.sleep(delay_between_operations)
                   
                   # Limit demo
                   if batch_num >= 3:
                       logger.info("    ... stopping fixed rate limiting demo at batch 3")
                       break
               
           except Exception as e:
               logger.error(f"Failed fixed rate limiting: {e}")
   
       def burst_protection(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate burst protection mechanism.
           """
           logger.info("--- Burst Protection ---")
           
           try:
               # Burst protection parameters
               burst_limit = 5  # Maximum operations in burst
               burst_window = 10  # Time window for burst detection (seconds)
               burst_penalty = 2.0  # Penalty delay after burst
               
               logger.info(f"    📊 Burst protection: {burst_limit} ops in {burst_window}s window")
               
               # Track operations for burst detection
               operation_times = []
               
               messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7))
               
               if messages.is_empty():
                   logger.info("    📧 No messages for burst protection demo")
                   return
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=3), 1):
                   current_time = time.time()
                   
                   # Check for burst
                   recent_operations = [t for t in operation_times if current_time - t < burst_window]
                   
                   if len(recent_operations) >= burst_limit:
                       logger.info(f"    🚨 Burst detected! Applying penalty delay: {burst_penalty}s")
                       time.sleep(burst_penalty)
                       operation_times = []  # Reset after penalty
                   
                   # Process batch
                   result = self.process_batch(uid_service, batch, batch_num)
                   
                   # Record operation time
                   operation_times.append(current_time)
                   
                   logger.info(f"    📊 Batch {batch_num}: {len(recent_operations)} recent ops")
                   
                   # Limit demo
                   if batch_num >= 6:
                       logger.info("    ... stopping burst protection demo at batch 6")
                       break
               
           except Exception as e:
               logger.error(f"Failed burst protection: {e}")
   
       def generate_performance_report(self):
           """
           Generate a comprehensive performance report.
           """
           logger.info("--- Performance Report ---")
           
           try:
               stats = self.performance_stats
               
               if stats['start_time']:
                   total_elapsed = time.time() - stats['start_time']
               else:
                   total_elapsed = 0
               
               logger.info(f"📊 Large Volume Processing Report:")
               logger.info(f"  ══════════════════════════════════════")
               logger.info(f"  Total Messages Processed: {stats['total_processed']}")
               logger.info(f"  Total Errors: {stats['total_errors']}")
               logger.info(f"  Total Elapsed Time: {total_elapsed:.2f}s")
               
               if stats['total_processed'] > 0:
                   throughput = stats['total_processed'] / total_elapsed if total_elapsed > 0 else 0
                   error_rate = stats['total_errors'] / stats['total_processed'] * 100
                   
                   logger.info(f"  Overall Throughput: {throughput:.1f} messages/second")
                   logger.info(f"  Error Rate: {error_rate:.2f}%")
               
               if stats['processing_times']:
                   avg_batch_time = sum(stats['processing_times']) / len(stats['processing_times'])
                   logger.info(f"  Average Batch Time: {avg_batch_time:.3f}s")
               
               if stats['batch_sizes']:
                   avg_batch_size = sum(stats['batch_sizes']) / len(stats['batch_sizes'])
                   logger.info(f"  Average Batch Size: {avg_batch_size:.1f} messages")
               
               logger.info(f"  ══════════════════════════════════════")
               
               # Save report to file
               report_file = self.cache_dir / f"performance_report_{int(time.time())}.json"
               with open(report_file, 'w') as f:
                   json.dump({
                       'timestamp': datetime.now().isoformat(),
                       'total_processed': stats['total_processed'],
                       'total_errors': stats['total_errors'],
                       'total_elapsed': total_elapsed,
                       'throughput': stats['total_processed'] / total_elapsed if total_elapsed > 0 else 0,
                       'error_rate': stats['total_errors'] / max(stats['total_processed'], 1) * 100,
                       'processing_times': stats['processing_times'],
                       'batch_sizes': stats['batch_sizes']
                   }, f, indent=2)
               
               logger.info(f"  Report saved to: {report_file}")
               
           except Exception as e:
               logger.error(f"Failed to generate performance report: {e}")


   class ProcessingResult:
       """
       Result object for processing operations.
       """
       def __init__(self, success: bool, processed_count: int = 0, error_message: str = None):
           self.success = success
           self.processed_count = processed_count
           self.error_message = error_message


   def main():
       """
       Main function to run the large volume handling example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = LargeVolumeHandler(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_large_volume_operations()
           logger.info("🎉 Large volume handling example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Performance Optimization Techniques
-----------------------------------

Batch Processing
~~~~~~~~~~~~~~~~

.. code-block:: python

   # Optimal batch sizing
   batch_size = 100  # Adjust based on server performance
   
   for batch in message_set.iter_batches(batch_size=batch_size):
       result = uid_service.uid_fetch(batch, MessagePart.HEADER)
       # Process batch results

Parallel Processing
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Thread-based parallel processing
   with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
       futures = []
       
       for chunk in message_chunks:
           future = executor.submit(process_chunk, chunk)
           futures.append(future)
       
       # Wait for completion
       for future in concurrent.futures.as_completed(futures):
           result = future.result()

Memory Management
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Stream processing for memory efficiency
   def process_large_dataset(uid_service, messages):
       for batch in messages.iter_batches(batch_size=50):
           # Process batch immediately
           process_batch(uid_service, batch)
           
           # Force garbage collection periodically
           if batch_num % 10 == 0:
               import gc
               gc.collect()

Search Optimization
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Use caching for repeated searches
   search_cache = {}
   
   def cached_search(criteria, cache_key):
       if cache_key not in search_cache:
           search_cache[cache_key] = uid_service.create_message_set_from_search(criteria)
       return search_cache[cache_key]

Rate Limiting
~~~~~~~~~~~~~

.. code-block:: python

   # Adaptive rate limiting
   def adaptive_rate_limit(processing_time, current_delay):
       if processing_time < 1.0:
           return max(0.1, current_delay * 0.9)  # Decrease delay
       else:
           return min(2.0, current_delay * 1.2)  # Increase delay

Resumable Operations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Checkpoint system for resumable operations
   def save_checkpoint(processed_count, last_uid):
       checkpoint = {
           'processed_count': processed_count,
           'last_uid': last_uid,
           'timestamp': time.time()
       }
       
       with open('checkpoint.json', 'w') as f:
           json.dump(checkpoint, f)

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Real-time performance tracking
   class PerformanceTracker:
       def __init__(self):
           self.start_time = time.time()
           self.processed_count = 0
           self.error_count = 0
       
       def record_success(self):
           self.processed_count += 1
       
       def record_error(self):
           self.error_count += 1
       
       def get_throughput(self):
           elapsed = time.time() - self.start_time
           return self.processed_count / elapsed if elapsed > 0 else 0

Best Practices for Large Volumes
--------------------------------

✅ **DO:**

- Use UID-based operations for reliability

- Process in optimal batch sizes (50-200 messages)

- Implement proper error handling and retries

- Monitor performance and adjust parameters

- Use caching for repeated operations

- Implement rate limiting to protect servers

- Use resumable operations for very large datasets

- Monitor memory usage and implement garbage collection

❌ **DON'T:**

- Load all messages into memory at once

- Use sequence numbers for large operations

- Ignore server rate limits

- Process without error handling

- Skip performance monitoring

- Use fixed batch sizes for all scenarios

- Forget to implement checkpointing for long operations

Common Challenges and Solutions
-------------------------------

Challenge: Memory Usage
~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Stream processing with small batches

.. code-block:: python

   # Instead of loading all messages
   all_messages = fetch_all_messages()  # ❌ Memory intensive
   
   # Use streaming
   for batch in message_set.iter_batches(batch_size=50):  # ✅ Memory efficient
       process_batch(batch)

Challenge: Server Timeouts
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Implement retry logic and rate limiting

.. code-block:: python

   def process_with_retry(operation, max_retries=3):
       for attempt in range(max_retries):
           try:
               return operation()
           except TimeoutError:
               if attempt < max_retries - 1:
                   time.sleep(2 ** attempt)  # Exponential backoff
               else:
                   raise

Challenge: Network Interruptions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Solution**: Implement resumable operations

.. code-block:: python

   def resumable_operation(uid_service, checkpoint_file):
       checkpoint = load_checkpoint(checkpoint_file)
       
       # Resume from last processed UID
       if checkpoint:
           start_uid = checkpoint['last_processed_uid']
           messages = get_messages_after_uid(start_uid)
       else:
           messages = get_all_messages()
       
       # Process with checkpointing
       for batch in messages.iter_batches():
           process_batch(batch)
           save_checkpoint(checkpoint_file, batch.last_uid)

Next Steps
----------

For more advanced patterns, see:

- :doc:`client_advanced` - Advanced client features
- :doc:`production_patterns` - Production-ready patterns
- :doc:`monitoring_analytics` - Monitoring and analytics
- :doc:`error_handling` - Error handling patterns 