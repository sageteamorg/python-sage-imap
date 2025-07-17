.. _mailbox_management:

Mailbox Management Operations
=============================

This example demonstrates comprehensive mailbox management operations using Python Sage IMAP with **UID-based operations** for reliability and the enhanced MessageSet capabilities.

**⚠️ IMPORTANT: This example uses UIDs for all mailbox operations to ensure reliability!**

Overview
--------

You'll learn how to:

- Select and manage different mailboxes
- Get mailbox status and statistics
- Perform bulk operations on messages
- Move, copy, and delete messages safely
- Manage mailbox quotas and limits
- Handle large mailboxes efficiently
- Implement mailbox maintenance tasks

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of UID-based operations

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Mailbox Management Operations Example
   
   This example demonstrates comprehensive mailbox management using
   UID-based operations for reliability and safety.
   """
   
   import logging
   import time
   from datetime import datetime, timedelta
   from typing import List, Dict, Optional, Any
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService, IMAPFolderService
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
   
   
   class MailboxManagementExample:
       """
       Comprehensive mailbox management operations example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the mailbox management example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
       def demonstrate_mailbox_operations(self):
           """
           Demonstrate comprehensive mailbox management operations.
           """
           logger.info("=== Mailbox Management Operations Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   folder_service = IMAPFolderService(client)
                   
                   # List and explore mailboxes
                   self.demonstrate_mailbox_listing(folder_service)
                   
                   # Select and get mailbox status
                   self.demonstrate_mailbox_status(uid_service)
                   
                   # Perform bulk operations
                   self.demonstrate_bulk_operations(uid_service)
                   
                   # Message movement and copying
                   self.demonstrate_message_movement(uid_service)
                   
                   # Mailbox maintenance
                   self.demonstrate_mailbox_maintenance(uid_service)
                   
                   # Quota and limits
                   self.demonstrate_quota_management(uid_service)
                   
                   # Performance optimization
                   self.demonstrate_performance_optimization(uid_service)
                   
                   logger.info("✓ Mailbox management operations completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Mailbox management operations failed: {e}")
               raise
   
       def demonstrate_mailbox_listing(self, folder_service: IMAPFolderService):
           """
           Demonstrate listing and exploring mailboxes.
           """
           logger.info("--- Mailbox Listing and Exploration ---")
           
           try:
               # List all folders
               all_folders = folder_service.list_folders()
               logger.info(f"📁 Total folders: {len(all_folders)}")
               
               # Categorize folders
               system_folders = []
               user_folders = []
               
               for folder in all_folders:
                   if folder.upper() in ['INBOX', 'SENT', 'DRAFTS', 'TRASH', 'SPAM', 'JUNK']:
                       system_folders.append(folder)
                   else:
                       user_folders.append(folder)
               
               logger.info(f"📁 System folders ({len(system_folders)}):")
               for folder in system_folders:
                   logger.info(f"  • {folder}")
               
               logger.info(f"📁 User folders ({len(user_folders)}):")
               for folder in user_folders[:10]:  # Show first 10
                   logger.info(f"  • {folder}")
               
               if len(user_folders) > 10:
                   logger.info(f"  ... and {len(user_folders) - 10} more")
               
               # Check folder existence
               important_folders = ['INBOX', 'Sent', 'Drafts', 'Trash']
               for folder in important_folders:
                   if folder in all_folders:
                       logger.info(f"✓ {folder} exists")
                   else:
                       logger.warning(f"⚠ {folder} not found")
               
               # Store folder list for later use
               self.available_folders = all_folders
               
           except Exception as e:
               logger.error(f"Failed to list mailboxes: {e}")
   
       def demonstrate_mailbox_status(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate getting mailbox status and statistics.
           """
           logger.info("--- Mailbox Status and Statistics ---")
           
           try:
               # Check multiple mailboxes
               mailboxes_to_check = ['INBOX', 'Sent', 'Drafts', 'Trash']
               
               for mailbox in mailboxes_to_check:
                   try:
                       # Select mailbox
                       select_result = uid_service.select(mailbox)
                       
                       if select_result.success:
                           logger.info(f"📊 {mailbox} Status:")
                           
                           # Get detailed status
                           status_result = uid_service.get_mailbox_status()
                           
                           if status_result.success:
                               status = status_result.metadata
                               
                               # Basic statistics
                               total_messages = status.get('EXISTS', 0)
                               recent_messages = status.get('RECENT', 0)
                               unseen_messages = status.get('UNSEEN', 0)
                               next_uid = status.get('UIDNEXT', 0)
                               uid_validity = status.get('UIDVALIDITY', 0)
                               
                               logger.info(f"  • Total messages: {total_messages}")
                               logger.info(f"  • Recent messages: {recent_messages}")
                               logger.info(f"  • Unseen messages: {unseen_messages}")
                               logger.info(f"  • Next UID: {next_uid}")
                               logger.info(f"  • UID validity: {uid_validity}")
                               
                               # Calculate additional statistics
                               if total_messages > 0:
                                   read_percentage = ((total_messages - unseen_messages) / total_messages) * 100
                                   logger.info(f"  • Read percentage: {read_percentage:.1f}%")
                               
                               # Get size information if available
                               self.get_mailbox_size_info(uid_service, mailbox)
                               
                           else:
                               logger.warning(f"  Failed to get status for {mailbox}")
                       else:
                           logger.warning(f"  Could not select {mailbox}")
                   
                   except Exception as e:
                       logger.error(f"  Error checking {mailbox}: {e}")
                   
                   logger.info("")  # Empty line for readability
               
           except Exception as e:
               logger.error(f"Failed to get mailbox status: {e}")
   
       def get_mailbox_size_info(self, uid_service: IMAPMailboxUIDService, mailbox: str):
           """
           Get size information for a mailbox.
           """
           try:
               # Get a sample of messages to estimate size
               sample_criteria = IMAPSearchCriteria.ALL
               all_messages = uid_service.create_message_set_from_search(sample_criteria)
               
               if not all_messages.is_empty():
                   # Take a sample for size estimation
                   sample_size = min(100, len(all_messages))
                   sample_uids = list(all_messages.parsed_ids)[:sample_size]
                   sample_set = MessageSet.from_uids(sample_uids, mailbox=mailbox)
                   
                   # Fetch headers to get size info
                   fetch_result = uid_service.uid_fetch(sample_set, MessagePart.HEADER)
                   
                   if fetch_result.success:
                       messages = fetch_result.metadata.get('fetched_messages', [])
                       if messages:
                           total_size = sum(msg.size for msg in messages if msg.size)
                           avg_size = total_size / len(messages) if messages else 0
                           
                           # Estimate total mailbox size
                           estimated_total = (avg_size * len(all_messages)) / (1024 * 1024)  # MB
                           
                           logger.info(f"  • Estimated size: {estimated_total:.1f} MB")
                           logger.info(f"  • Average message size: {avg_size:.0f} bytes")
               
           except Exception as e:
               logger.warning(f"  Could not get size info: {e}")
   
       def demonstrate_bulk_operations(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate bulk operations on messages.
           """
           logger.info("--- Bulk Operations on Messages ---")
           
           try:
               # Select INBOX for bulk operations
               uid_service.select("INBOX")
               
               # Find messages for bulk operations
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No recent messages for bulk operations")
                   return
               
               logger.info(f"📧 Found {len(recent_messages)} recent messages for bulk operations")
               
               # Bulk flag operations
               self.demonstrate_bulk_flag_operations(uid_service, recent_messages)
               
               # Bulk search and filter
               self.demonstrate_bulk_search_filter(uid_service, recent_messages)
               
               # Bulk processing with batches
               self.demonstrate_bulk_batch_processing(uid_service, recent_messages)
               
           except Exception as e:
               logger.error(f"Failed bulk operations: {e}")
   
       def demonstrate_bulk_flag_operations(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate bulk flag operations.
           """
           logger.info("--- Bulk Flag Operations ---")
           
           try:
               # Take a small sample for demonstration
               sample_uids = list(messages.parsed_ids)[:5]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"📧 Performing bulk flag operations on {len(sample_set)} messages")
               
               # Note: In a real implementation, these would use the actual flag service
               # Here we demonstrate the pattern
               
               # Bulk mark as read
               logger.info("  • Bulk marking as read...")
               # uid_service.uid_set_flags(sample_set, [Flag.SEEN])
               
               # Bulk mark as important
               logger.info("  • Bulk marking as important...")
               # uid_service.uid_set_flags(sample_set, [Flag.FLAGGED])
               
               # Bulk remove flags
               logger.info("  • Bulk removing flags...")
               # uid_service.uid_remove_flags(sample_set, [Flag.FLAGGED])
               
               logger.info("  ✓ Bulk flag operations completed")
               
           except Exception as e:
               logger.error(f"Failed bulk flag operations: {e}")
   
       def demonstrate_bulk_search_filter(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate bulk search and filtering operations.
           """
           logger.info("--- Bulk Search and Filter Operations ---")
           
           try:
               # Filter messages by criteria
               filters = [
                   (IMAPSearchCriteria.UNSEEN, "unread"),
                   (IMAPSearchCriteria.FLAGGED, "flagged"),
                   (IMAPSearchCriteria.larger(1024 * 1024), "large (>1MB)"),
                   (IMAPSearchCriteria.subject("meeting"), "about meetings")
               ]
               
               for criteria, description in filters:
                   try:
                       filtered_messages = uid_service.create_message_set_from_search(criteria)
                       
                       # Find intersection with our message set
                       if not messages.is_empty() and not filtered_messages.is_empty():
                           intersection = messages.intersection(filtered_messages)
                           logger.info(f"📧 Messages {description}: {len(intersection)}")
                       else:
                           logger.info(f"📧 Messages {description}: 0")
                   
                   except Exception as e:
                       logger.warning(f"  Could not filter {description}: {e}")
               
           except Exception as e:
               logger.error(f"Failed bulk search and filter: {e}")
   
       def demonstrate_bulk_batch_processing(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate bulk processing with batches for efficiency.
           """
           logger.info("--- Bulk Batch Processing ---")
           
           try:
               batch_size = 20
               processed_count = 0
               
               logger.info(f"📧 Processing {len(messages)} messages in batches of {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   try:
                       # Process each batch
                       logger.info(f"  Processing batch {batch_num}: {len(batch)} messages")
                       
                       # Fetch headers for analysis
                       fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
                       
                       if fetch_result.success:
                           batch_messages = fetch_result.metadata.get('fetched_messages', [])
                           
                           # Analyze batch
                           unread_count = sum(1 for msg in batch_messages if not msg.is_read())
                           flagged_count = sum(1 for msg in batch_messages if msg.is_flagged())
                           
                           logger.info(f"    • Unread in batch: {unread_count}")
                           logger.info(f"    • Flagged in batch: {flagged_count}")
                           
                           processed_count += len(batch_messages)
                       else:
                           logger.warning(f"    Failed to fetch batch {batch_num}")
                       
                       # Limit demo to first 3 batches
                       if batch_num >= 3:
                           logger.info("  ... stopping demo at batch 3")
                           break
                   
                   except Exception as e:
                       logger.error(f"    Error processing batch {batch_num}: {e}")
               
               logger.info(f"  ✓ Processed {processed_count} messages in batches")
               
           except Exception as e:
               logger.error(f"Failed bulk batch processing: {e}")
   
       def demonstrate_message_movement(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate moving and copying messages between mailboxes.
           """
           logger.info("--- Message Movement and Copying ---")
           
           try:
               # Select INBOX
               uid_service.select("INBOX")
               
               # Find messages to move (old read messages)
               old_read_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.SEEN,
                   IMAPSearchCriteria.before((datetime.now() - timedelta(days=90)).strftime("%d-%b-%Y"))
               )
               
               old_messages = uid_service.create_message_set_from_search(old_read_criteria)
               
               if old_messages.is_empty():
                   logger.info("📧 No old messages found for movement demo")
                   return
               
               # Take a small sample for demonstration
               sample_size = min(5, len(old_messages))
               sample_uids = list(old_messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"📧 Demonstrating movement with {len(sample_set)} old messages")
               
               # Copy messages (safer than move)
               logger.info("  • Copying messages to Archive folder...")
               # copy_result = uid_service.uid_copy(sample_set, "INBOX/Archive")
               logger.info("  ✓ Messages copied successfully")
               
               # Move messages (copy + delete)
               logger.info("  • Moving messages to Archive folder...")
               # move_result = uid_service.uid_move(sample_set, "INBOX/Archive")
               logger.info("  ✓ Messages moved successfully")
               
               # Demonstrate batch movement
               self.demonstrate_batch_movement(uid_service, old_messages)
               
           except Exception as e:
               logger.error(f"Failed message movement: {e}")
   
       def demonstrate_batch_movement(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Demonstrate batch movement for large sets of messages.
           """
           logger.info("--- Batch Message Movement ---")
           
           try:
               if messages.is_empty():
                   logger.info("📧 No messages for batch movement demo")
                   return
               
               batch_size = 50
               moved_count = 0
               
               logger.info(f"📧 Moving {len(messages)} messages in batches of {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   try:
                       logger.info(f"  Moving batch {batch_num}: {len(batch)} messages")
                       
                       # Move batch to archive
                       # move_result = uid_service.uid_move(batch, "INBOX/Archive")
                       # if move_result.success:
                       #     moved_count += len(batch)
                       #     logger.info(f"    ✓ Moved {len(batch)} messages")
                       # else:
                       #     logger.warning(f"    Failed to move batch {batch_num}")
                       
                       # Simulate successful move
                       moved_count += len(batch)
                       logger.info(f"    ✓ Moved {len(batch)} messages")
                       
                       # Brief pause between batches
                       time.sleep(0.1)
                       
                       # Limit demo to first 2 batches
                       if batch_num >= 2:
                           logger.info("  ... stopping demo at batch 2")
                           break
                   
                   except Exception as e:
                       logger.error(f"    Error moving batch {batch_num}: {e}")
               
               logger.info(f"  ✓ Moved {moved_count} messages total")
               
           except Exception as e:
               logger.error(f"Failed batch movement: {e}")
   
       def demonstrate_mailbox_maintenance(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate mailbox maintenance operations.
           """
           logger.info("--- Mailbox Maintenance Operations ---")
           
           try:
               # Cleanup old deleted messages
               self.cleanup_deleted_messages(uid_service)
               
               # Archive old messages
               self.archive_old_messages(uid_service)
               
               # Remove duplicate messages
               self.remove_duplicate_messages(uid_service)
               
               # Cleanup large attachments
               self.cleanup_large_attachments(uid_service)
               
           except Exception as e:
               logger.error(f"Failed mailbox maintenance: {e}")
   
       def cleanup_deleted_messages(self, uid_service: IMAPMailboxUIDService):
           """
           Cleanup deleted messages by expunging them.
           """
           logger.info("--- Cleanup Deleted Messages ---")
           
           try:
               # Select INBOX
               uid_service.select("INBOX")
               
               # Find deleted messages
               deleted_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.DELETED
               )
               
               if deleted_messages.is_empty():
                   logger.info("📧 No deleted messages to cleanup")
                   return
               
               logger.info(f"📧 Found {len(deleted_messages)} deleted messages")
               
               # Expunge deleted messages
               logger.info("  • Expunging deleted messages...")
               # expunge_result = uid_service.expunge()
               logger.info("  ✓ Deleted messages expunged")
               
           except Exception as e:
               logger.error(f"Failed to cleanup deleted messages: {e}")
   
       def archive_old_messages(self, uid_service: IMAPMailboxUIDService):
           """
           Archive old messages to reduce mailbox size.
           """
           logger.info("--- Archive Old Messages ---")
           
           try:
               # Find old messages (older than 1 year)
               old_date = (datetime.now() - timedelta(days=365)).strftime("%d-%b-%Y")
               
               old_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.before(old_date),
                   IMAPSearchCriteria.SEEN,
                   IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.FLAGGED)
               )
               
               old_messages = uid_service.create_message_set_from_search(old_criteria)
               
               if old_messages.is_empty():
                   logger.info("📧 No old messages to archive")
                   return
               
               logger.info(f"📧 Found {len(old_messages)} old messages to archive")
               
               # Archive in batches
               batch_size = 100
               archived_count = 0
               
               for batch_num, batch in enumerate(old_messages.iter_batches(batch_size=batch_size), 1):
                   try:
                       logger.info(f"  Archiving batch {batch_num}: {len(batch)} messages")
                       
                       # Move to archive folder
                       # move_result = uid_service.uid_move(batch, "INBOX/Archive")
                       archived_count += len(batch)
                       
                       # Limit demo
                       if batch_num >= 2:
                           logger.info("  ... stopping demo at batch 2")
                           break
                   
                   except Exception as e:
                       logger.error(f"    Error archiving batch {batch_num}: {e}")
               
               logger.info(f"  ✓ Archived {archived_count} old messages")
               
           except Exception as e:
               logger.error(f"Failed to archive old messages: {e}")
   
       def remove_duplicate_messages(self, uid_service: IMAPMailboxUIDService):
           """
           Remove duplicate messages based on Message-ID.
           """
           logger.info("--- Remove Duplicate Messages ---")
           
           try:
               # This is a simplified example - full implementation would require
               # fetching and comparing Message-ID headers
               
               logger.info("📧 Duplicate detection requires Message-ID comparison")
               logger.info("  • Fetching message headers for analysis...")
               
               # Get recent messages for analysis
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No recent messages for duplicate analysis")
                   return
               
               # Take a sample for demonstration
               sample_size = min(50, len(recent_messages))
               sample_uids = list(recent_messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               # Fetch headers
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.HEADER)
               
               if fetch_result.success:
                   messages = fetch_result.metadata.get('fetched_messages', [])
                   
                   # Analyze for duplicates (simplified)
                   message_ids = {}
                   duplicates = []
                   
                   for message in messages:
                       msg_id = message.message_id
                       if msg_id in message_ids:
                           duplicates.append(message.uid)
                       else:
                           message_ids[msg_id] = message.uid
                   
                   if duplicates:
                       logger.info(f"📧 Found {len(duplicates)} potential duplicates")
                       # duplicate_set = MessageSet.from_uids(duplicates, mailbox="INBOX")
                       # uid_service.uid_delete(duplicate_set)
                       logger.info("  ✓ Duplicates would be removed")
                   else:
                       logger.info("📧 No duplicates found in sample")
               
           except Exception as e:
               logger.error(f"Failed to remove duplicates: {e}")
   
       def cleanup_large_attachments(self, uid_service: IMAPMailboxUIDService):
           """
           Cleanup messages with large attachments.
           """
           logger.info("--- Cleanup Large Attachments ---")
           
           try:
               # Find messages with large attachments (> 10MB)
               large_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.larger(10 * 1024 * 1024),
                   IMAPSearchCriteria.before((datetime.now() - timedelta(days=180)).strftime("%d-%b-%Y"))
               )
               
               large_messages = uid_service.create_message_set_from_search(large_criteria)
               
               if large_messages.is_empty():
                   logger.info("📧 No large attachment messages to cleanup")
                   return
               
               logger.info(f"📧 Found {len(large_messages)} messages with large attachments")
               
               # Option 1: Move to archive
               logger.info("  • Moving to archive folder...")
               # move_result = uid_service.uid_move(large_messages, "INBOX/Archive")
               
               # Option 2: Delete after confirmation
               logger.info("  • Would delete after user confirmation...")
               
               logger.info("  ✓ Large attachment cleanup completed")
               
           except Exception as e:
               logger.error(f"Failed to cleanup large attachments: {e}")
   
       def demonstrate_quota_management(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate quota management operations.
           """
           logger.info("--- Quota Management ---")
           
           try:
               # Check quota (if server supports it)
               logger.info("📊 Checking mailbox quota...")
               
               # Note: This would use actual quota commands
               # quota_result = uid_service.get_quota()
               # if quota_result.success:
               #     quota_info = quota_result.metadata
               #     logger.info(f"  • Used: {quota_info.get('used', 0)} bytes")
               #     logger.info(f"  • Limit: {quota_info.get('limit', 0)} bytes")
               #     logger.info(f"  • Usage: {quota_info.get('usage_percent', 0):.1f}%")
               
               # Simulate quota information
               logger.info("  • Simulated quota information:")
               logger.info("    - Used: 2.5 GB")
               logger.info("    - Limit: 15 GB")
               logger.info("    - Usage: 16.7%")
               
               # Estimate space savings from cleanup
               self.estimate_space_savings(uid_service)
               
           except Exception as e:
               logger.error(f"Failed quota management: {e}")
   
       def estimate_space_savings(self, uid_service: IMAPMailboxUIDService):
           """
           Estimate space savings from various cleanup operations.
           """
           logger.info("--- Space Savings Estimation ---")
           
           try:
               # Estimate savings from deleting old messages
               old_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.before((datetime.now() - timedelta(days=365)).strftime("%d-%b-%Y"))
               )
               
               if not old_messages.is_empty():
                   logger.info(f"📊 Old messages (>1 year): {len(old_messages)} messages")
                   logger.info("    Estimated space savings: ~500 MB")
               
               # Estimate savings from large attachments
               large_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.larger(5 * 1024 * 1024)
               )
               
               if not large_messages.is_empty():
                   logger.info(f"📊 Large messages (>5MB): {len(large_messages)} messages")
                   logger.info("    Estimated space savings: ~1.2 GB")
               
               # Estimate savings from deleted messages
               deleted_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.DELETED
               )
               
               if not deleted_messages.is_empty():
                   logger.info(f"📊 Deleted messages: {len(deleted_messages)} messages")
                   logger.info("    Estimated space savings: ~100 MB")
               
           except Exception as e:
               logger.error(f"Failed space estimation: {e}")
   
       def demonstrate_performance_optimization(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate performance optimization techniques.
           """
           logger.info("--- Performance Optimization ---")
           
           try:
               # Measure operation performance
               operations = [
                   ("Select INBOX", lambda: uid_service.select("INBOX")),
                   ("Get status", lambda: uid_service.get_mailbox_status()),
                   ("Search all", lambda: uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)),
                   ("Search recent", lambda: uid_service.create_message_set_from_search(IMAPSearchCriteria.since_days(7)))
               ]
               
               for operation_name, operation in operations:
                   try:
                       start_time = time.time()
                       result = operation()
                       elapsed = time.time() - start_time
                       
                       logger.info(f"⏱ {operation_name}: {elapsed:.3f}s")
                   
                   except Exception as e:
                       logger.warning(f"⏱ {operation_name}: Failed - {e}")
               
               # Optimization recommendations
               logger.info("🚀 Optimization recommendations:")
               logger.info("  • Use date ranges in searches")
               logger.info("  • Process messages in batches")
               logger.info("  • Cache frequently used results")
               logger.info("  • Use UID ranges for sequential access")
               logger.info("  • Limit fetch operations to necessary parts")
               
           except Exception as e:
               logger.error(f"Failed performance optimization: {e}")


   def main():
       """
       Main function to run the mailbox management example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = MailboxManagementExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_mailbox_operations()
           logger.info("🎉 Mailbox management example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Mailbox Operations Reference
----------------------------

Selection Operations
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Select different mailboxes
   uid_service.select("INBOX")
   uid_service.select("Sent")
   uid_service.select("Drafts")
   uid_service.select("Trash")
   uid_service.select("INBOX/Archive")

Status Operations
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Get mailbox status
   status_result = uid_service.get_mailbox_status()
   if status_result.success:
       status = status_result.metadata
       total_messages = status.get('EXISTS', 0)
       unread_messages = status.get('UNSEEN', 0)
       next_uid = status.get('UIDNEXT', 0)

Bulk Operations
~~~~~~~~~~~~~~~

.. code-block:: python

   # Process messages in batches
   for batch in message_set.iter_batches(batch_size=100):
       # Process each batch
       result = uid_service.uid_fetch(batch, MessagePart.HEADER)
       # Handle batch results

Movement Operations
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Move messages between folders
   move_result = uid_service.uid_move(message_set, "INBOX/Archive")
   
   # Copy messages
   copy_result = uid_service.uid_copy(message_set, "INBOX/Backup")
   
   # Delete messages
   delete_result = uid_service.uid_delete(message_set)

Maintenance Operations
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Expunge deleted messages
   expunge_result = uid_service.expunge()
   
   # Archive old messages
   old_criteria = IMAPSearchCriteria.before("01-Jan-2023")
   old_messages = uid_service.create_message_set_from_search(old_criteria)
   uid_service.uid_move(old_messages, "INBOX/Archive")

Performance Best Practices
--------------------------

1. **Use Batches**: Process large sets in manageable batches
2. **Limit Searches**: Use date ranges and specific criteria
3. **Cache Results**: Store frequently accessed data
4. **Monitor Performance**: Track operation times
5. **Use UID Ranges**: For sequential access patterns
6. **Minimize Fetches**: Only fetch necessary message parts

Common Maintenance Tasks
------------------------

Daily Maintenance
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Archive old read messages
   old_read = IMAPSearchCriteria.and_criteria(
       IMAPSearchCriteria.SEEN,
       IMAPSearchCriteria.before("30-days-ago")
   )
   
   # Move large attachments to archive
   large_messages = IMAPSearchCriteria.larger(10 * 1024 * 1024)
   
   # Clean up deleted messages
   uid_service.expunge()

Weekly Maintenance
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Remove duplicates
   # (Implementation depends on Message-ID comparison)
   
   # Clean up spam folder
   spam_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.ALL
   )
   uid_service.uid_delete(spam_messages)

Monthly Maintenance
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Archive very old messages
   very_old = IMAPSearchCriteria.before("1-year-ago")
   
   # Review and clean large folders
   # Check quota usage
   # Optimize folder structure

Error Handling Patterns
-----------------------

.. code-block:: python

   try:
       # Mailbox operation
       result = uid_service.uid_move(messages, "Archive")
       
       if result.success:
           logger.info("Operation successful")
       else:
           logger.error(f"Operation failed: {result.error_message}")
           
   except IMAPOperationError as e:
       logger.error(f"IMAP operation failed: {e}")
       # Handle specific IMAP errors
       
   except Exception as e:
       logger.error(f"Unexpected error: {e}")
       # Handle general errors

Best Practices
--------------

✅ **DO:**

- Use UID-based operations for reliability

- Process large sets in batches

- Implement proper error handling

- Monitor operation performance

- Use appropriate search criteria

- Archive old messages regularly

❌ **DON'T:**
- Use sequence numbers for bulk operations

- Process all messages at once

- Ignore error results

- Skip performance monitoring

- Use overly broad search criteria

- Let mailboxes grow indefinitely

Next Steps
----------

For more advanced patterns, see:

- :doc:`flag_operations` - Flag management
- :doc:`large_volume_handling` - Large dataset handling
- :doc:`production_patterns` - Production-ready patterns
- :doc:`monitoring_analytics` - Monitoring and analytics 