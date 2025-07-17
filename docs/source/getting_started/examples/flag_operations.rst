.. _flag_operations:

Flag Operations
===============

This example demonstrates comprehensive flag operations using Python Sage IMAP with **UID-based operations** for reliable flag management.

**⚠️ IMPORTANT: This example uses UIDs for all flag operations to ensure reliability!**

Overview
--------

You'll learn how to:

- Set and remove standard IMAP flags
- Work with custom flags and keywords
- Perform bulk flag operations efficiently
- Query messages by flag status
- Handle flag synchronization
- Implement flag-based message management
- Use flags for message organization

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of IMAP flag system

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   Flag Operations Example
   
   This example demonstrates comprehensive flag operations using
   UID-based operations for reliable flag management.
   """
   
   import logging
   import time
   from datetime import datetime, timedelta
   from typing import List, Dict, Optional, Set
   
   from sage_imap.services.client import IMAPClient
   from sage_imap.services import IMAPMailboxUIDService, IMAPFlagService
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
   
   
   class FlagOperationsExample:
       """
       Comprehensive flag operations example using UID-based operations.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the flag operations example.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
       def demonstrate_flag_operations(self):
           """
           Demonstrate comprehensive flag operations.
           """
           logger.info("=== Flag Operations Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   flag_service = IMAPFlagService(client)
                   
                   # Select INBOX for flag operations
                   uid_service.select("INBOX")
                   
                   # Standard flag operations
                   self.demonstrate_standard_flags(uid_service, flag_service)
                   
                   # Custom flag operations
                   self.demonstrate_custom_flags(uid_service, flag_service)
                   
                   # Bulk flag operations
                   self.demonstrate_bulk_flag_operations(uid_service, flag_service)
                   
                   # Flag queries and searches
                   self.demonstrate_flag_queries(uid_service)
                   
                   # Flag synchronization
                   self.demonstrate_flag_synchronization(uid_service, flag_service)
                   
                   # Flag-based organization
                   self.demonstrate_flag_organization(uid_service, flag_service)
                   
                   # Advanced flag patterns
                   self.demonstrate_advanced_patterns(uid_service, flag_service)
                   
                   logger.info("✓ Flag operations completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ Flag operations failed: {e}")
               raise
   
       def demonstrate_standard_flags(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate standard IMAP flag operations.
           """
           logger.info("--- Standard Flag Operations ---")
           
           try:
               # Get recent messages for flag operations
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No recent messages for flag operations")
                   return
               
               # Take a small sample for demonstration
               sample_uids = list(recent_messages.parsed_ids)[:5]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"📧 Working with {len(sample_set)} messages for flag operations")
               
               # Standard flags demonstration
               standard_flags = [
                   (Flag.SEEN, "\\Seen", "Mark as read"),
                   (Flag.FLAGGED, "\\Flagged", "Mark as important"),
                   (Flag.ANSWERED, "\\Answered", "Mark as answered"),
                   (Flag.DELETED, "\\Deleted", "Mark for deletion"),
                   (Flag.DRAFT, "\\Draft", "Mark as draft")
               ]
               
               for flag, flag_str, description in standard_flags:
                   try:
                       logger.info(f"  • {description}...")
                       
                       # Set flag
                       set_result = flag_service.set_flags(sample_set, [flag])
                       if set_result.success:
                           logger.info(f"    ✓ Set {flag_str} flag")
                       else:
                           logger.warning(f"    ⚠ Failed to set {flag_str}: {set_result.error_message}")
                       
                       # Brief pause
                       time.sleep(0.5)
                       
                       # Remove flag (except for DELETED to avoid issues)
                       if flag != Flag.DELETED:
                           remove_result = flag_service.remove_flags(sample_set, [flag])
                           if remove_result.success:
                               logger.info(f"    ✓ Removed {flag_str} flag")
                           else:
                               logger.warning(f"    ⚠ Failed to remove {flag_str}: {remove_result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Error with {flag_str}: {e}")
               
               logger.info("  ✓ Standard flag operations completed")
               
           except Exception as e:
               logger.error(f"Failed standard flag operations: {e}")
   
       def demonstrate_custom_flags(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate custom flag and keyword operations.
           """
           logger.info("--- Custom Flag Operations ---")
           
           try:
               # Get sample messages
               sample_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               
               if sample_messages.is_empty():
                   logger.info("📧 No messages for custom flag operations")
                   return
               
               # Take a small sample
               sample_uids = list(sample_messages.parsed_ids)[:3]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"📧 Working with {len(sample_set)} messages for custom flags")
               
               # Custom keywords to demonstrate
               custom_keywords = [
                   ("$Label1", "Priority: High"),
                   ("$Label2", "Category: Work"),
                   ("$Label3", "Project: Alpha"),
                   ("$MDNSent", "MDN Sent"),
                   ("$Forwarded", "Forwarded"),
                   ("NonJunk", "Not Junk"),
                   ("$Junk", "Junk/Spam")
               ]
               
               for keyword, description in custom_keywords:
                   try:
                       logger.info(f"  • {description} ({keyword})...")
                       
                       # Set custom keyword
                       set_result = flag_service.set_flags(sample_set, [keyword])
                       if set_result.success:
                           logger.info(f"    ✓ Set custom keyword: {keyword}")
                       else:
                           logger.warning(f"    ⚠ Failed to set {keyword}: {set_result.error_message}")
                       
                       # Brief pause
                       time.sleep(0.3)
                       
                       # Remove custom keyword
                       remove_result = flag_service.remove_flags(sample_set, [keyword])
                       if remove_result.success:
                           logger.info(f"    ✓ Removed custom keyword: {keyword}")
                       else:
                           logger.warning(f"    ⚠ Failed to remove {keyword}: {remove_result.error_message}")
                   
                   except Exception as e:
                       logger.error(f"    ❌ Error with {keyword}: {e}")
               
               # Demonstrate Gmail-specific labels
               self.demonstrate_gmail_labels(flag_service, sample_set)
               
               logger.info("  ✓ Custom flag operations completed")
               
           except Exception as e:
               logger.error(f"Failed custom flag operations: {e}")
   
       def demonstrate_gmail_labels(self, flag_service: IMAPFlagService, sample_set: MessageSet):
           """
           Demonstrate Gmail-specific label operations.
           """
           logger.info("--- Gmail Label Operations ---")
           
           try:
               # Gmail labels are represented as custom keywords
               gmail_labels = [
                   ("\\Important", "Important"),
                   ("\\Sent", "Sent"),
                   ("\\Starred", "Starred"),
                   ("\\Trash", "Trash"),
                   ("\\Draft", "Draft"),
                   ("\\Spam", "Spam"),
                   ("\\Inbox", "Inbox"),
                   ("\\All", "All Mail"),
                   ("\\Flagged", "Flagged")
               ]
               
               logger.info("  📧 Gmail-specific labels:")
               
               for label, description in gmail_labels:
                   try:
                       logger.info(f"    • {description} ({label})")
                       
                       # Note: In practice, you'd set/remove these labels
                       # set_result = flag_service.set_flags(sample_set, [label])
                       # remove_result = flag_service.remove_flags(sample_set, [label])
                       
                   except Exception as e:
                       logger.warning(f"    ⚠ Error with {label}: {e}")
               
               logger.info("  ✓ Gmail label operations demonstrated")
               
           except Exception as e:
               logger.error(f"Failed Gmail label operations: {e}")
   
       def demonstrate_bulk_flag_operations(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate bulk flag operations for efficiency.
           """
           logger.info("--- Bulk Flag Operations ---")
           
           try:
               # Get larger set of messages for bulk operations
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(30)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No messages for bulk flag operations")
                   return
               
               logger.info(f"📧 Performing bulk operations on {len(recent_messages)} messages")
               
               # Bulk mark as read
               self.bulk_mark_as_read(flag_service, recent_messages)
               
               # Bulk mark important messages
               self.bulk_mark_important(uid_service, flag_service)
               
               # Bulk cleanup operations
               self.bulk_cleanup_flags(uid_service, flag_service)
               
               # Batch processing for large sets
               self.batch_flag_processing(flag_service, recent_messages)
               
               logger.info("  ✓ Bulk flag operations completed")
               
           except Exception as e:
               logger.error(f"Failed bulk flag operations: {e}")
   
       def bulk_mark_as_read(self, flag_service: IMAPFlagService, messages: MessageSet):
           """
           Bulk mark messages as read.
           """
           logger.info("--- Bulk Mark as Read ---")
           
           try:
               # Take a sample for demonstration
               sample_size = min(10, len(messages))
               sample_uids = list(messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"  📧 Bulk marking {len(sample_set)} messages as read...")
               
               # Bulk set SEEN flag
               result = flag_service.set_flags(sample_set, [Flag.SEEN])
               
               if result.success:
                   logger.info(f"    ✓ Successfully marked {len(sample_set)} messages as read")
               else:
                   logger.warning(f"    ⚠ Failed to mark messages as read: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed bulk mark as read: {e}")
   
       def bulk_mark_important(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Bulk mark messages as important based on criteria.
           """
           logger.info("--- Bulk Mark Important ---")
           
           try:
               # Find messages from important senders
               important_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.from_address("boss@company.com"),
                   IMAPSearchCriteria.from_address("ceo@company.com"),
                   IMAPSearchCriteria.subject("urgent"),
                   IMAPSearchCriteria.subject("important")
               )
               
               important_messages = uid_service.create_message_set_from_search(important_criteria)
               
               if important_messages.is_empty():
                   logger.info("  📧 No messages match important criteria")
                   return
               
               logger.info(f"  📧 Bulk marking {len(important_messages)} important messages...")
               
               # Bulk set FLAGGED flag
               result = flag_service.set_flags(important_messages, [Flag.FLAGGED])
               
               if result.success:
                   logger.info(f"    ✓ Successfully marked {len(important_messages)} messages as important")
               else:
                   logger.warning(f"    ⚠ Failed to mark important messages: {result.error_message}")
               
           except Exception as e:
               logger.error(f"Failed bulk mark important: {e}")
   
       def bulk_cleanup_flags(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Bulk cleanup flag operations.
           """
           logger.info("--- Bulk Flag Cleanup ---")
           
           try:
               # Remove DELETED flag from messages (undelete)
               deleted_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.DELETED
               )
               
               if not deleted_messages.is_empty():
                   logger.info(f"  📧 Undeleting {len(deleted_messages)} messages...")
                   
                   result = flag_service.remove_flags(deleted_messages, [Flag.DELETED])
                   if result.success:
                       logger.info(f"    ✓ Undeleted {len(deleted_messages)} messages")
                   else:
                       logger.warning(f"    ⚠ Failed to undelete messages: {result.error_message}")
               else:
                   logger.info("  📧 No deleted messages to undelete")
               
               # Clear old answered flags
               old_answered_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.ANSWERED,
                   IMAPSearchCriteria.before((datetime.now() - timedelta(days=180)).strftime("%d-%b-%Y"))
               )
               
               old_answered = uid_service.create_message_set_from_search(old_answered_criteria)
               
               if not old_answered.is_empty():
                   logger.info(f"  📧 Clearing old answered flags from {len(old_answered)} messages...")
                   
                   result = flag_service.remove_flags(old_answered, [Flag.ANSWERED])
                   if result.success:
                       logger.info(f"    ✓ Cleared answered flags from {len(old_answered)} messages")
                   else:
                       logger.warning(f"    ⚠ Failed to clear answered flags: {result.error_message}")
               else:
                   logger.info("  📧 No old answered messages to clean")
               
           except Exception as e:
               logger.error(f"Failed bulk flag cleanup: {e}")
   
       def batch_flag_processing(self, flag_service: IMAPFlagService, messages: MessageSet):
           """
           Process flags in batches for large message sets.
           """
           logger.info("--- Batch Flag Processing ---")
           
           try:
               batch_size = 50
               processed_count = 0
               
               logger.info(f"  📧 Processing {len(messages)} messages in batches of {batch_size}")
               
               for batch_num, batch in enumerate(messages.iter_batches(batch_size=batch_size), 1):
                   try:
                       logger.info(f"    Processing batch {batch_num}: {len(batch)} messages")
                       
                       # Example: Mark batch as read
                       result = flag_service.set_flags(batch, [Flag.SEEN])
                       
                       if result.success:
                           processed_count += len(batch)
                           logger.info(f"      ✓ Processed {len(batch)} messages")
                       else:
                           logger.warning(f"      ⚠ Failed to process batch {batch_num}: {result.error_message}")
                       
                       # Brief pause between batches
                       time.sleep(0.1)
                       
                       # Limit demo to first 3 batches
                       if batch_num >= 3:
                           logger.info("      ... stopping demo at batch 3")
                           break
                   
                   except Exception as e:
                       logger.error(f"      ❌ Error processing batch {batch_num}: {e}")
               
               logger.info(f"    ✓ Processed {processed_count} messages in batches")
               
           except Exception as e:
               logger.error(f"Failed batch flag processing: {e}")
   
       def demonstrate_flag_queries(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate querying messages by flag status.
           """
           logger.info("--- Flag Query Operations ---")
           
           try:
               # Query messages by different flag combinations
               flag_queries = [
                   (IMAPSearchCriteria.SEEN, "Read messages"),
                   (IMAPSearchCriteria.UNSEEN, "Unread messages"),
                   (IMAPSearchCriteria.FLAGGED, "Flagged messages"),
                   (IMAPSearchCriteria.UNFLAGGED, "Unflagged messages"),
                   (IMAPSearchCriteria.ANSWERED, "Answered messages"),
                   (IMAPSearchCriteria.UNANSWERED, "Unanswered messages"),
                   (IMAPSearchCriteria.DELETED, "Deleted messages"),
                   (IMAPSearchCriteria.UNDELETED, "Undeleted messages"),
                   (IMAPSearchCriteria.DRAFT, "Draft messages"),
                   (IMAPSearchCriteria.UNDRAFT, "Non-draft messages"),
                   (IMAPSearchCriteria.RECENT, "Recent messages"),
                   (IMAPSearchCriteria.OLD, "Old messages")
               ]
               
               for criteria, description in flag_queries:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       logger.info(f"  📧 {description}: {len(messages)}")
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ Could not query {description}: {e}")
               
               # Complex flag queries
               self.demonstrate_complex_flag_queries(uid_service)
               
               logger.info("  ✓ Flag query operations completed")
               
           except Exception as e:
               logger.error(f"Failed flag query operations: {e}")
   
       def demonstrate_complex_flag_queries(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate complex flag query combinations.
           """
           logger.info("--- Complex Flag Queries ---")
           
           try:
               # Unread important messages
               unread_important = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.FLAGGED
               )
               messages = uid_service.create_message_set_from_search(unread_important)
               logger.info(f"  📧 Unread important messages: {len(messages)}")
               
               # Read but unanswered messages
               read_unanswered = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.SEEN,
                   IMAPSearchCriteria.UNANSWERED
               )
               messages = uid_service.create_message_set_from_search(read_unanswered)
               logger.info(f"  📧 Read but unanswered messages: {len(messages)}")
               
               # Not deleted and not draft
               active_messages = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNDELETED,
                   IMAPSearchCriteria.UNDRAFT
               )
               messages = uid_service.create_message_set_from_search(active_messages)
               logger.info(f"  📧 Active messages (not deleted, not draft): {len(messages)}")
               
               # Flagged OR recent
               priority_messages = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.FLAGGED,
                   IMAPSearchCriteria.RECENT
               )
               messages = uid_service.create_message_set_from_search(priority_messages)
               logger.info(f"  📧 Priority messages (flagged OR recent): {len(messages)}")
               
               # Custom keyword queries
               custom_keyword_queries = [
                   ("$Label1", "Label1 messages"),
                   ("$Forwarded", "Forwarded messages"),
                   ("NonJunk", "Non-junk messages"),
                   ("$MDNSent", "MDN sent messages")
               ]
               
               for keyword, description in custom_keyword_queries:
                   try:
                       keyword_criteria = IMAPSearchCriteria.keyword(keyword)
                       messages = uid_service.create_message_set_from_search(keyword_criteria)
                       logger.info(f"  📧 {description}: {len(messages)}")
                   
                   except Exception as e:
                       logger.warning(f"  ⚠ Could not query {description}: {e}")
               
           except Exception as e:
               logger.error(f"Failed complex flag queries: {e}")
   
       def demonstrate_flag_synchronization(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate flag synchronization between sessions.
           """
           logger.info("--- Flag Synchronization ---")
           
           try:
               # Get current flag state
               recent_messages = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               
               if recent_messages.is_empty():
                   logger.info("📧 No messages for flag synchronization demo")
                   return
               
               logger.info(f"📧 Demonstrating flag synchronization with {len(recent_messages)} messages")
               
               # Simulate flag changes that might happen in another client
               self.simulate_external_flag_changes(flag_service, recent_messages)
               
               # Check flag consistency
               self.check_flag_consistency(uid_service, recent_messages)
               
               # Synchronize flags
               self.synchronize_flags(uid_service, flag_service, recent_messages)
               
               logger.info("  ✓ Flag synchronization completed")
               
           except Exception as e:
               logger.error(f"Failed flag synchronization: {e}")
   
       def simulate_external_flag_changes(self, flag_service: IMAPFlagService, messages: MessageSet):
           """
           Simulate flag changes from external clients.
           """
           logger.info("--- Simulating External Flag Changes ---")
           
           try:
               # Take a small sample
               sample_size = min(3, len(messages))
               sample_uids = list(messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               logger.info(f"  📧 Simulating external changes on {len(sample_set)} messages")
               
               # Simulate marking as read
               logger.info("    • Simulating mark as read...")
               result = flag_service.set_flags(sample_set, [Flag.SEEN])
               if result.success:
                   logger.info("      ✓ Marked as read")
               
               # Simulate flagging
               logger.info("    • Simulating flag as important...")
               result = flag_service.set_flags(sample_set, [Flag.FLAGGED])
               if result.success:
                   logger.info("      ✓ Flagged as important")
               
               logger.info("  ✓ External flag changes simulated")
               
           except Exception as e:
               logger.error(f"Failed to simulate external flag changes: {e}")
   
       def check_flag_consistency(self, uid_service: IMAPMailboxUIDService, messages: MessageSet):
           """
           Check flag consistency across messages.
           """
           logger.info("--- Checking Flag Consistency ---")
           
           try:
               # Take a sample for checking
               sample_size = min(5, len(messages))
               sample_uids = list(messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               # Fetch messages to check their flags
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.FLAGS)
               
               if fetch_result.success:
                   messages_data = fetch_result.metadata.get('fetched_messages', [])
                   
                   logger.info(f"  📧 Checking flags for {len(messages_data)} messages:")
                   
                   for message in messages_data:
                       flags = message.flags if hasattr(message, 'flags') else []
                       logger.info(f"    • UID {message.uid}: {flags}")
                       
                       # Check for common flag inconsistencies
                       if Flag.SEEN in flags and Flag.UNSEEN in flags:
                           logger.warning(f"      ⚠ Inconsistent read state for UID {message.uid}")
                       
                       if Flag.DELETED in flags and Flag.FLAGGED in flags:
                           logger.warning(f"      ⚠ Deleted message still flagged: UID {message.uid}")
               
               logger.info("  ✓ Flag consistency check completed")
               
           except Exception as e:
               logger.error(f"Failed flag consistency check: {e}")
   
       def synchronize_flags(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService, messages: MessageSet):
           """
           Synchronize flags with server state.
           """
           logger.info("--- Synchronizing Flags ---")
           
           try:
               # In a real application, this would sync with a local cache
               # Here we demonstrate the pattern
               
               logger.info("  📧 Synchronizing flags with server...")
               
               # Refresh mailbox status
               status_result = uid_service.get_mailbox_status()
               if status_result.success:
                   logger.info("    ✓ Mailbox status refreshed")
               
               # Re-fetch message flags
               sample_size = min(5, len(messages))
               sample_uids = list(messages.parsed_ids)[:sample_size]
               sample_set = MessageSet.from_uids(sample_uids, mailbox="INBOX")
               
               fetch_result = uid_service.uid_fetch(sample_set, MessagePart.FLAGS)
               if fetch_result.success:
                   logger.info("    ✓ Message flags synchronized")
               
               logger.info("  ✓ Flag synchronization completed")
               
           except Exception as e:
               logger.error(f"Failed flag synchronization: {e}")
   
       def demonstrate_flag_organization(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate using flags for message organization.
           """
           logger.info("--- Flag-Based Message Organization ---")
           
           try:
               # Organize messages by priority using flags
               self.organize_by_priority(uid_service, flag_service)
               
               # Organize by category using custom flags
               self.organize_by_category(uid_service, flag_service)
               
               # Organize by status using flags
               self.organize_by_status(uid_service, flag_service)
               
               logger.info("  ✓ Flag-based organization completed")
               
           except Exception as e:
               logger.error(f"Failed flag-based organization: {e}")
   
       def organize_by_priority(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Organize messages by priority using flags.
           """
           logger.info("--- Organize by Priority ---")
           
           try:
               # High priority: messages from important senders
               high_priority_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.from_address("boss@company.com"),
                   IMAPSearchCriteria.subject("urgent"),
                   IMAPSearchCriteria.subject("critical")
               )
               
               high_priority_messages = uid_service.create_message_set_from_search(high_priority_criteria)
               
               if not high_priority_messages.is_empty():
                   logger.info(f"  📧 Flagging {len(high_priority_messages)} high priority messages")
                   result = flag_service.set_flags(high_priority_messages, [Flag.FLAGGED])
                   if result.success:
                       logger.info("    ✓ High priority messages flagged")
               
               # Medium priority: messages from colleagues
               medium_priority_criteria = IMAPSearchCriteria.from_address("@company.com")
               medium_priority_messages = uid_service.create_message_set_from_search(medium_priority_criteria)
               
               if not medium_priority_messages.is_empty():
                   logger.info(f"  📧 Marking {len(medium_priority_messages)} medium priority messages")
                   result = flag_service.set_flags(medium_priority_messages, ["$Label1"])
                   if result.success:
                       logger.info("    ✓ Medium priority messages marked")
               
               logger.info("  ✓ Priority organization completed")
               
           except Exception as e:
               logger.error(f"Failed priority organization: {e}")
   
       def organize_by_category(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Organize messages by category using custom flags.
           """
           logger.info("--- Organize by Category ---")
           
           try:
               # Category mapping
               categories = [
                   (IMAPSearchCriteria.subject("meeting"), "$Category_Meeting", "Meetings"),
                   (IMAPSearchCriteria.subject("invoice"), "$Category_Finance", "Finance"),
                   (IMAPSearchCriteria.subject("report"), "$Category_Reports", "Reports"),
                   (IMAPSearchCriteria.body("newsletter"), "$Category_Newsletter", "Newsletters")
               ]
               
               for criteria, flag, description in categories:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       
                       if not messages.is_empty():
                           logger.info(f"  📧 Categorizing {len(messages)} {description.lower()}")
                           result = flag_service.set_flags(messages, [flag])
                           if result.success:
                               logger.info(f"    ✓ {description} categorized")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Failed to categorize {description}: {e}")
               
               logger.info("  ✓ Category organization completed")
               
           except Exception as e:
               logger.error(f"Failed category organization: {e}")
   
       def organize_by_status(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Organize messages by status using flags.
           """
           logger.info("--- Organize by Status ---")
           
           try:
               # Status-based organization
               status_flags = [
                   (IMAPSearchCriteria.UNANSWERED, "$Status_NeedsReply", "Needs Reply"),
                   (IMAPSearchCriteria.UNSEEN, "$Status_New", "New Messages"),
                   (IMAPSearchCriteria.larger(1024*1024), "$Status_LargeAttachment", "Large Files")
               ]
               
               for criteria, flag, description in status_flags:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       
                       if not messages.is_empty():
                           logger.info(f"  📧 Marking {len(messages)} messages as '{description}'")
                           result = flag_service.set_flags(messages, [flag])
                           if result.success:
                               logger.info(f"    ✓ {description} status set")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Failed to set {description} status: {e}")
               
               logger.info("  ✓ Status organization completed")
               
           except Exception as e:
               logger.error(f"Failed status organization: {e}")
   
       def demonstrate_advanced_patterns(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate advanced flag usage patterns.
           """
           logger.info("--- Advanced Flag Patterns ---")
           
           try:
               # Conditional flag setting
               self.conditional_flag_setting(uid_service, flag_service)
               
               # Flag-based workflows
               self.flag_based_workflows(uid_service, flag_service)
               
               # Flag statistics and analysis
               self.flag_statistics(uid_service)
               
               logger.info("  ✓ Advanced flag patterns completed")
               
           except Exception as e:
               logger.error(f"Failed advanced flag patterns: {e}")
   
       def conditional_flag_setting(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate conditional flag setting based on message content.
           """
           logger.info("--- Conditional Flag Setting ---")
           
           try:
               # Auto-flag based on conditions
               conditions = [
                   {
                       'criteria': IMAPSearchCriteria.and_criteria(
                           IMAPSearchCriteria.from_address("@important-client.com"),
                           IMAPSearchCriteria.since_days(1)
                       ),
                       'flag': Flag.FLAGGED,
                       'description': 'Recent messages from important client'
                   },
                   {
                       'criteria': IMAPSearchCriteria.and_criteria(
                           IMAPSearchCriteria.subject("out of office"),
                           IMAPSearchCriteria.since_days(7)
                       ),
                       'flag': "$AutoReply",
                       'description': 'Out of office messages'
                   }
               ]
               
               for condition in conditions:
                   try:
                       messages = uid_service.create_message_set_from_search(condition['criteria'])
                       
                       if not messages.is_empty():
                           logger.info(f"  📧 {condition['description']}: {len(messages)} messages")
                           result = flag_service.set_flags(messages, [condition['flag']])
                           if result.success:
                               logger.info(f"    ✓ Conditional flag set")
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Failed conditional flag: {e}")
               
               logger.info("  ✓ Conditional flag setting completed")
               
           except Exception as e:
               logger.error(f"Failed conditional flag setting: {e}")
   
       def flag_based_workflows(self, uid_service: IMAPMailboxUIDService, flag_service: IMAPFlagService):
           """
           Demonstrate flag-based workflow patterns.
           """
           logger.info("--- Flag-Based Workflows ---")
           
           try:
               # Workflow: New → In Progress → Completed
               workflow_stages = [
                   ("$Workflow_New", "New items"),
                   ("$Workflow_InProgress", "In progress"),
                   ("$Workflow_Completed", "Completed")
               ]
               
               # Simulate workflow progression
               for stage_flag, stage_name in workflow_stages:
                   logger.info(f"  📧 {stage_name} workflow stage")
                   
                   # In a real application, this would move messages through stages
                   # based on actions taken
                   
               # Cleanup completed workflow items
               completed_criteria = IMAPSearchCriteria.keyword("$Workflow_Completed")
               completed_messages = uid_service.create_message_set_from_search(completed_criteria)
               
               if not completed_messages.is_empty():
                   logger.info(f"  📧 Archiving {len(completed_messages)} completed workflow items")
                   # In practice: move to archive folder
               
               logger.info("  ✓ Flag-based workflows demonstrated")
               
           except Exception as e:
               logger.error(f"Failed flag-based workflows: {e}")
   
       def flag_statistics(self, uid_service: IMAPMailboxUIDService):
           """
           Generate statistics about flag usage.
           """
           logger.info("--- Flag Statistics ---")
           
           try:
               # Count messages by flag type
               flag_stats = []
               
               flag_queries = [
                   (IMAPSearchCriteria.SEEN, "Read"),
                   (IMAPSearchCriteria.UNSEEN, "Unread"),
                   (IMAPSearchCriteria.FLAGGED, "Flagged"),
                   (IMAPSearchCriteria.ANSWERED, "Answered"),
                   (IMAPSearchCriteria.DELETED, "Deleted"),
                   (IMAPSearchCriteria.DRAFT, "Draft"),
                   (IMAPSearchCriteria.RECENT, "Recent")
               ]
               
               total_messages = len(uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL))
               
               logger.info(f"  📊 Flag Statistics (Total: {total_messages} messages):")
               
               for criteria, flag_name in flag_queries:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       count = len(messages)
                       percentage = (count / total_messages * 100) if total_messages > 0 else 0
                       
                       logger.info(f"    • {flag_name}: {count} ({percentage:.1f}%)")
                       flag_stats.append((flag_name, count, percentage))
                   
                   except Exception as e:
                       logger.warning(f"    ⚠ Could not count {flag_name}: {e}")
               
               # Find most common flag
               if flag_stats:
                   most_common = max(flag_stats, key=lambda x: x[1])
                   logger.info(f"  📊 Most common flag: {most_common[0]} ({most_common[1]} messages)")
               
               logger.info("  ✓ Flag statistics completed")
               
           except Exception as e:
               logger.error(f"Failed flag statistics: {e}")


   def main():
       """
       Main function to run the flag operations example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = FlagOperationsExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_flag_operations()
           logger.info("🎉 Flag operations example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Flag Operations Reference
-------------------------

Standard IMAP Flags
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # System flags
   Flag.SEEN         # \\Seen - Message has been read
   Flag.ANSWERED     # \\Answered - Message has been answered
   Flag.FLAGGED      # \\Flagged - Message is flagged for urgent/special attention
   Flag.DELETED      # \\Deleted - Message is marked for removal
   Flag.DRAFT        # \\Draft - Message is a draft
   Flag.RECENT       # \\Recent - Message is new (first session seeing it)

Setting Flags
~~~~~~~~~~~~~

.. code-block:: python

   # Set single flag
   result = flag_service.set_flags(message_set, [Flag.SEEN])
   
   # Set multiple flags
   result = flag_service.set_flags(message_set, [Flag.SEEN, Flag.FLAGGED])
   
   # Set custom flags
   result = flag_service.set_flags(message_set, ["$Label1", "$Important"])

Removing Flags
~~~~~~~~~~~~~~

.. code-block:: python

   # Remove single flag
   result = flag_service.remove_flags(message_set, [Flag.FLAGGED])
   
   # Remove multiple flags
   result = flag_service.remove_flags(message_set, [Flag.FLAGGED, Flag.ANSWERED])

Querying by Flags
~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Query messages with specific flags
   flagged_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.FLAGGED
   )
   
   # Query messages without specific flags
   unflagged_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.UNFLAGGED
   )

Custom Flags and Keywords
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Gmail labels
   "\\Important", "\\Starred", "\\Sent", "\\Trash"
   
   # Custom keywords
   "$Label1", "$Label2", "$Label3"
   "$Priority", "$Category", "$Status"
   "$Forwarded", "$MDNSent", "NonJunk"

Bulk Operations
~~~~~~~~~~~~~~~

.. code-block:: python

   # Bulk mark as read
   result = flag_service.set_flags(large_message_set, [Flag.SEEN])
   
   # Batch processing
   for batch in large_message_set.iter_batches(batch_size=100):
       result = flag_service.set_flags(batch, [Flag.SEEN])

Flag Patterns
-------------

Priority Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # High priority
   high_priority = IMAPSearchCriteria.or_criteria(
       IMAPSearchCriteria.FLAGGED,
       IMAPSearchCriteria.subject("urgent")
   )
   
   # Mark as high priority
   flag_service.set_flags(high_priority_messages, [Flag.FLAGGED])

Category Organization
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Categorize by content
   meeting_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.subject("meeting")
   )
   flag_service.set_flags(meeting_messages, ["$Category_Meeting"])

Status Tracking
~~~~~~~~~~~~~~~

.. code-block:: python

   # Track message status
   needs_reply = IMAPSearchCriteria.UNANSWERED
   flag_service.set_flags(needs_reply_messages, ["$Status_NeedsReply"])

Workflow Management
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Workflow stages
   new_items = "$Workflow_New"
   in_progress = "$Workflow_InProgress"
   completed = "$Workflow_Completed"
   
   # Move through workflow
   flag_service.remove_flags(message_set, [new_items])
   flag_service.set_flags(message_set, [in_progress])

Best Practices
--------------

✅ **DO:**

- Use UID-based flag operations for reliability

- Process large sets in batches

- Use meaningful custom flag names

- Implement proper error handling

- Check server flag support

- Use flags for organization and workflow

❌ **DON'T:**

- Use sequence numbers for flag operations

- Set conflicting flags simultaneously

- Use flags for data storage

- Ignore flag operation results

- Exceed server flag limits

- Use non-standard flag names

Server Compatibility
--------------------

Different IMAP servers have varying flag support:

- **Gmail**: Supports labels as custom flags

- **Outlook**: Limited custom flag support

- **Dovecot**: Full custom flag support

- **Courier**: Basic flag support

Always test flag operations with your specific server.

Common Use Cases
----------------

Email Client Features
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Mark as read/unread
   flag_service.set_flags(messages, [Flag.SEEN])
   flag_service.remove_flags(messages, [Flag.SEEN])
   
   # Star/unstar messages
   flag_service.set_flags(messages, [Flag.FLAGGED])
   flag_service.remove_flags(messages, [Flag.FLAGGED])

Automated Processing
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Auto-categorize
   newsletter_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.body("unsubscribe")
   )
   flag_service.set_flags(newsletter_messages, ["$Category_Newsletter"])

Project Management
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Track project emails
   project_messages = uid_service.create_message_set_from_search(
       IMAPSearchCriteria.subject("Project Alpha")
   )
   flag_service.set_flags(project_messages, ["$Project_Alpha"])

Next Steps
----------

For more advanced patterns, see:

- :doc:`folder_management` - Folder operations
- :doc:`message_set_usage` - Advanced MessageSet usage
- :doc:`large_volume_handling` - Large dataset handling
- :doc:`production_patterns` - Production-ready patterns 