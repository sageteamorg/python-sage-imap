.. _uid_search_operations:

UID Search Operations
=====================

This example demonstrates comprehensive UID-based search operations using Python Sage IMAP. Learn how to search emails reliably using UIDs and the enhanced MessageSet capabilities.

**⚠️ IMPORTANT: This example emphasizes UID-based searches for production reliability!**

Overview
--------

You'll learn how to:

- Perform basic UID searches with various criteria
- Build complex search queries with multiple conditions
- Use date-based searches efficiently
- Search by content, headers, and metadata
- Handle large search results with pagination
- Optimize search performance
- Use MessageSet for search result management

Prerequisites
-------------

- Python 3.7 or higher
- Python Sage IMAP installed
- Valid IMAP server credentials
- Understanding of IMAP search syntax

Complete Example
----------------

.. code-block:: python

   #!/usr/bin/env python3
   """
   UID Search Operations Example
   
   This example demonstrates comprehensive UID-based search operations
   using various criteria and optimization techniques.
   """
   
   import logging
   import time
   from datetime import datetime, timedelta
   from typing import List, Optional, Dict, Any
   
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
   
   
   class UIDSearchExample:
       """
       Comprehensive UID-based search operations example.
       """
       
       def __init__(self, host: str, username: str, password: str, port: int = 993):
           """
           Initialize the search example with connection parameters.
           """
           self.config = {
               'host': host,
               'username': username,
               'password': password,
               'port': port,
               'use_ssl': True,
               'timeout': 30.0
           }
           
       def demonstrate_uid_search_operations(self):
           """
           Demonstrate comprehensive UID search operations.
           """
           logger.info("=== UID Search Operations Example ===")
           
           try:
               with IMAPClient(config=self.config) as client:
                   uid_service = IMAPMailboxUIDService(client)
                   uid_service.select("INBOX")
                   
                   # Basic search operations
                   self.demonstrate_basic_searches(uid_service)
                   
                   # Date-based searches
                   self.demonstrate_date_searches(uid_service)
                   
                   # Content-based searches
                   self.demonstrate_content_searches(uid_service)
                   
                   # Flag-based searches
                   self.demonstrate_flag_searches(uid_service)
                   
                   # Complex compound searches
                   self.demonstrate_complex_searches(uid_service)
                   
                   # Performance optimization
                   self.demonstrate_search_optimization(uid_service)
                   
                   # Pagination and large results
                   self.demonstrate_search_pagination(uid_service)
                   
                   logger.info("✓ UID search operations completed successfully")
                   
           except Exception as e:
               logger.error(f"❌ UID search operations failed: {e}")
               raise
   
       def demonstrate_basic_searches(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate basic UID search operations.
           """
           logger.info("--- Basic UID Search Operations ---")
           
           try:
               # Search for all messages (useful for getting total count)
               all_criteria = IMAPSearchCriteria.ALL
               all_messages = uid_service.create_message_set_from_search(all_criteria)
               logger.info(f"📧 Total messages in INBOX: {len(all_messages)}")
               
               # Search for unread messages
               unread_criteria = IMAPSearchCriteria.UNSEEN
               unread_messages = uid_service.create_message_set_from_search(unread_criteria)
               logger.info(f"📧 Unread messages: {len(unread_messages)}")
               
               # Search for flagged (important) messages
               flagged_criteria = IMAPSearchCriteria.FLAGGED
               flagged_messages = uid_service.create_message_set_from_search(flagged_criteria)
               logger.info(f"📧 Flagged messages: {len(flagged_messages)}")
               
               # Search for answered messages
               answered_criteria = IMAPSearchCriteria.ANSWERED
               answered_messages = uid_service.create_message_set_from_search(answered_criteria)
               logger.info(f"📧 Answered messages: {len(answered_messages)}")
               
               # Search for draft messages
               draft_criteria = IMAPSearchCriteria.DRAFT
               draft_messages = uid_service.create_message_set_from_search(draft_criteria)
               logger.info(f"📧 Draft messages: {len(draft_messages)}")
               
               # Search for deleted messages
               deleted_criteria = IMAPSearchCriteria.DELETED
               deleted_messages = uid_service.create_message_set_from_search(deleted_criteria)
               logger.info(f"📧 Deleted messages: {len(deleted_messages)}")
               
               # Search for recent messages (arrived since last session)
               recent_criteria = IMAPSearchCriteria.RECENT
               recent_messages = uid_service.create_message_set_from_search(recent_criteria)
               logger.info(f"📧 Recent messages: {len(recent_messages)}")
               
           except Exception as e:
               logger.error(f"Failed basic searches: {e}")
   
       def demonstrate_date_searches(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate date-based UID search operations.
           """
           logger.info("--- Date-Based UID Search Operations ---")
           
           try:
               # Search for messages from today
               today = datetime.now()
               today_str = today.strftime("%d-%b-%Y")
               today_criteria = IMAPSearchCriteria.on(today_str)
               today_messages = uid_service.create_message_set_from_search(today_criteria)
               logger.info(f"📧 Messages from today: {len(today_messages)}")
               
               # Search for messages from last 7 days
               week_ago = today - timedelta(days=7)
               week_ago_str = week_ago.strftime("%d-%b-%Y")
               last_week_criteria = IMAPSearchCriteria.since(week_ago_str)
               last_week_messages = uid_service.create_message_set_from_search(last_week_criteria)
               logger.info(f"📧 Messages from last 7 days: {len(last_week_messages)}")
               
               # Search for messages from last 30 days
               month_ago = today - timedelta(days=30)
               month_ago_str = month_ago.strftime("%d-%b-%Y")
               last_month_criteria = IMAPSearchCriteria.since(month_ago_str)
               last_month_messages = uid_service.create_message_set_from_search(last_month_criteria)
               logger.info(f"📧 Messages from last 30 days: {len(last_month_messages)}")
               
               # Search for messages older than 30 days
               old_criteria = IMAPSearchCriteria.before(month_ago_str)
               old_messages = uid_service.create_message_set_from_search(old_criteria)
               logger.info(f"📧 Messages older than 30 days: {len(old_messages)}")
               
               # Search for messages within a specific date range
               range_start = today - timedelta(days=14)
               range_end = today - timedelta(days=7)
               range_start_str = range_start.strftime("%d-%b-%Y")
               range_end_str = range_end.strftime("%d-%b-%Y")
               
               range_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.since(range_start_str),
                   IMAPSearchCriteria.before(range_end_str)
               )
               range_messages = uid_service.create_message_set_from_search(range_criteria)
               logger.info(f"📧 Messages from {range_start_str} to {range_end_str}: {len(range_messages)}")
               
               # Search using convenience methods
               recent_7_days = uid_service.create_message_set_from_search(
                   IMAPSearchCriteria.since_days(7)
               )
               logger.info(f"📧 Recent 7 days (convenience method): {len(recent_7_days)}")
               
           except Exception as e:
               logger.error(f"Failed date searches: {e}")
   
       def demonstrate_content_searches(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate content-based UID search operations.
           """
           logger.info("--- Content-Based UID Search Operations ---")
           
           try:
               # Search by sender
               sender_criteria = IMAPSearchCriteria.from_address("@gmail.com")
               sender_messages = uid_service.create_message_set_from_search(sender_criteria)
               logger.info(f"📧 Messages from @gmail.com: {len(sender_messages)}")
               
               # Search by recipient
               to_criteria = IMAPSearchCriteria.to_address("me@example.com")
               to_messages = uid_service.create_message_set_from_search(to_criteria)
               logger.info(f"📧 Messages to me@example.com: {len(to_messages)}")
               
               # Search by CC recipient
               cc_criteria = IMAPSearchCriteria.cc_address("team@example.com")
               cc_messages = uid_service.create_message_set_from_search(cc_criteria)
               logger.info(f"📧 Messages CC'd to team@example.com: {len(cc_messages)}")
               
               # Search by subject keywords
               subject_criteria = IMAPSearchCriteria.subject("important")
               subject_messages = uid_service.create_message_set_from_search(subject_criteria)
               logger.info(f"📧 Messages with 'important' in subject: {len(subject_messages)}")
               
               # Search by body content
               body_criteria = IMAPSearchCriteria.body("meeting")
               body_messages = uid_service.create_message_set_from_search(body_criteria)
               logger.info(f"📧 Messages with 'meeting' in body: {len(body_messages)}")
               
               # Search by any text content
               text_criteria = IMAPSearchCriteria.text("project")
               text_messages = uid_service.create_message_set_from_search(text_criteria)
               logger.info(f"📧 Messages with 'project' anywhere: {len(text_messages)}")
               
               # Search by message size
               large_criteria = IMAPSearchCriteria.larger(1024 * 1024)  # > 1MB
               large_messages = uid_service.create_message_set_from_search(large_criteria)
               logger.info(f"📧 Messages larger than 1MB: {len(large_messages)}")
               
               small_criteria = IMAPSearchCriteria.smaller(1024)  # < 1KB
               small_messages = uid_service.create_message_set_from_search(small_criteria)
               logger.info(f"📧 Messages smaller than 1KB: {len(small_messages)}")
               
               # Search by header content
               header_criteria = IMAPSearchCriteria.header("X-Priority", "1")
               header_messages = uid_service.create_message_set_from_search(header_criteria)
               logger.info(f"📧 High priority messages: {len(header_messages)}")
               
           except Exception as e:
               logger.error(f"Failed content searches: {e}")
   
       def demonstrate_flag_searches(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate flag-based UID search operations.
           """
           logger.info("--- Flag-Based UID Search Operations ---")
           
           try:
               # Search for messages with specific flags
               flag_searches = [
                   (IMAPSearchCriteria.SEEN, "read"),
                   (IMAPSearchCriteria.UNSEEN, "unread"),
                   (IMAPSearchCriteria.FLAGGED, "flagged"),
                   (IMAPSearchCriteria.UNFLAGGED, "unflagged"),
                   (IMAPSearchCriteria.ANSWERED, "answered"),
                   (IMAPSearchCriteria.UNANSWERED, "unanswered"),
                   (IMAPSearchCriteria.DRAFT, "draft"),
                   (IMAPSearchCriteria.UNDRAFT, "non-draft"),
                   (IMAPSearchCriteria.DELETED, "deleted"),
                   (IMAPSearchCriteria.UNDELETED, "not deleted"),
                   (IMAPSearchCriteria.RECENT, "recent"),
                   (IMAPSearchCriteria.OLD, "old")
               ]
               
               for criteria, description in flag_searches:
                   try:
                       messages = uid_service.create_message_set_from_search(criteria)
                       logger.info(f"📧 {description.capitalize()} messages: {len(messages)}")
                   except Exception as e:
                       logger.warning(f"Could not search for {description} messages: {e}")
               
               # Search for messages with custom keywords
               keyword_criteria = IMAPSearchCriteria.keyword("\\Junk")
               keyword_messages = uid_service.create_message_set_from_search(keyword_criteria)
               logger.info(f"📧 Messages with \\Junk keyword: {len(keyword_messages)}")
               
               # Search for messages without custom keywords
               unkeyword_criteria = IMAPSearchCriteria.unkeyword("\\Junk")
               unkeyword_messages = uid_service.create_message_set_from_search(unkeyword_criteria)
               logger.info(f"📧 Messages without \\Junk keyword: {len(unkeyword_messages)}")
               
           except Exception as e:
               logger.error(f"Failed flag searches: {e}")
   
       def demonstrate_complex_searches(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate complex compound UID search operations.
           """
           logger.info("--- Complex Compound UID Search Operations ---")
           
           try:
               # AND operation: Unread messages from last 7 days
               unread_recent_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.since_days(7)
               )
               unread_recent_messages = uid_service.create_message_set_from_search(unread_recent_criteria)
               logger.info(f"📧 Unread messages from last 7 days: {len(unread_recent_messages)}")
               
               # OR operation: Flagged OR from important sender
               important_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.FLAGGED,
                   IMAPSearchCriteria.from_address("boss@company.com")
               )
               important_messages = uid_service.create_message_set_from_search(important_criteria)
               logger.info(f"📧 Important messages (flagged OR from boss): {len(important_messages)}")
               
               # NOT operation: Not read and not deleted
               active_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.SEEN),
                   IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.DELETED)
               )
               active_messages = uid_service.create_message_set_from_search(active_criteria)
               logger.info(f"📧 Active unread messages: {len(active_messages)}")
               
               # Complex multi-condition search
               complex_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.since_days(30),
                   IMAPSearchCriteria.or_criteria(
                       IMAPSearchCriteria.subject("urgent"),
                       IMAPSearchCriteria.subject("important")
                   ),
                   IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.DELETED),
                   IMAPSearchCriteria.larger(1024)  # > 1KB
               )
               complex_messages = uid_service.create_message_set_from_search(complex_criteria)
               logger.info(f"📧 Complex search results: {len(complex_messages)}")
               
               # Search with multiple senders
               multiple_senders_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.from_address("@company.com"),
                   IMAPSearchCriteria.from_address("@partner.com"),
                   IMAPSearchCriteria.from_address("@client.com")
               )
               multiple_senders_messages = uid_service.create_message_set_from_search(multiple_senders_criteria)
               logger.info(f"📧 Messages from multiple domains: {len(multiple_senders_messages)}")
               
               # Search for potential spam
               spam_criteria = IMAPSearchCriteria.or_criteria(
                   IMAPSearchCriteria.subject("URGENT"),
                   IMAPSearchCriteria.subject("FREE"),
                   IMAPSearchCriteria.subject("WINNER"),
                   IMAPSearchCriteria.and_criteria(
                       IMAPSearchCriteria.body("click here"),
                       IMAPSearchCriteria.body("limited time")
                   )
               )
               spam_messages = uid_service.create_message_set_from_search(spam_criteria)
               logger.info(f"📧 Potential spam messages: {len(spam_messages)}")
               
           except Exception as e:
               logger.error(f"Failed complex searches: {e}")
   
       def demonstrate_search_optimization(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate search optimization techniques.
           """
           logger.info("--- Search Optimization Techniques ---")
           
           try:
               # Measure search performance
               start_time = time.time()
               
               # Simple search
               simple_criteria = IMAPSearchCriteria.UNSEEN
               simple_messages = uid_service.create_message_set_from_search(simple_criteria)
               simple_time = time.time() - start_time
               
               logger.info(f"📊 Simple search: {len(simple_messages)} messages in {simple_time:.3f}s")
               
               # Complex search timing
               start_time = time.time()
               complex_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.since_days(30),
                   IMAPSearchCriteria.or_criteria(
                       IMAPSearchCriteria.from_address("@company.com"),
                       IMAPSearchCriteria.subject("important")
                   )
               )
               complex_messages = uid_service.create_message_set_from_search(complex_criteria)
               complex_time = time.time() - start_time
               
               logger.info(f"📊 Complex search: {len(complex_messages)} messages in {complex_time:.3f}s")
               
               # UID range search (often faster for sequential access)
               start_time = time.time()
               
               # Get last 1000 messages by UID
               all_messages = uid_service.create_message_set_from_search(IMAPSearchCriteria.ALL)
               if not all_messages.is_empty():
                   all_uids = sorted(all_messages.parsed_ids)
                   if len(all_uids) > 1000:
                       recent_uids = all_uids[-1000:]  # Last 1000 UIDs
                       recent_range = MessageSet.from_uids(recent_uids, mailbox="INBOX")
                       range_time = time.time() - start_time
                       logger.info(f"📊 UID range selection: {len(recent_range)} messages in {range_time:.3f}s")
               
               # Demonstrate search result caching
               self.demonstrate_search_caching(uid_service)
               
           except Exception as e:
               logger.error(f"Failed search optimization: {e}")
   
       def demonstrate_search_caching(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate search result caching for performance.
           """
           logger.info("--- Search Result Caching ---")
           
           try:
               # Cache frequently used searches
               search_cache = {}
               
               def cached_search(criteria_key: str, criteria: IMAPSearchCriteria) -> MessageSet:
                   """
                   Perform search with caching.
                   """
                   if criteria_key not in search_cache:
                       start_time = time.time()
                       search_cache[criteria_key] = uid_service.create_message_set_from_search(criteria)
                       search_time = time.time() - start_time
                       logger.info(f"📊 Cached search '{criteria_key}': {search_time:.3f}s")
                   else:
                       logger.info(f"📊 Using cached result for '{criteria_key}'")
                   
                   return search_cache[criteria_key]
               
               # First search - will cache
               unread_messages = cached_search("unread", IMAPSearchCriteria.UNSEEN)
               logger.info(f"📧 Unread messages (first call): {len(unread_messages)}")
               
               # Second search - from cache
               unread_messages_2 = cached_search("unread", IMAPSearchCriteria.UNSEEN)
               logger.info(f"📧 Unread messages (cached): {len(unread_messages_2)}")
               
               # Cache recent searches
               recent_messages = cached_search("recent", IMAPSearchCriteria.since_days(7))
               logger.info(f"📧 Recent messages: {len(recent_messages)}")
               
               # Use cached results for compound operations
               if not unread_messages.is_empty() and not recent_messages.is_empty():
                   # Intersection of cached results
                   unread_recent = unread_messages.intersection(recent_messages)
                   logger.info(f"📧 Unread recent messages (from cache): {len(unread_recent)}")
               
           except Exception as e:
               logger.error(f"Failed search caching: {e}")
   
       def demonstrate_search_pagination(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate handling large search results with pagination.
           """
           logger.info("--- Search Result Pagination ---")
           
           try:
               # Get all messages
               all_criteria = IMAPSearchCriteria.ALL
               all_messages = uid_service.create_message_set_from_search(all_criteria)
               
               if all_messages.is_empty():
                   logger.info("📧 No messages found for pagination demo")
                   return
               
               logger.info(f"📧 Total messages for pagination: {len(all_messages)}")
               
               # Paginate through results
               page_size = 50
               page_count = 0
               
               for batch in all_messages.iter_batches(batch_size=page_size):
                   page_count += 1
                   logger.info(f"📄 Page {page_count}: {len(batch)} messages")
                   
                   # Fetch headers for this page
                   try:
                       fetch_result = uid_service.uid_fetch(batch, MessagePart.HEADER)
                       if fetch_result.success:
                           messages = fetch_result.metadata.get('fetched_messages', [])
                           logger.info(f"  ✓ Fetched {len(messages)} message headers")
                           
                           # Show first few subjects
                           for i, message in enumerate(messages[:3]):
                               logger.info(f"    {i+1}. {message.subject}")
                           
                           if len(messages) > 3:
                               logger.info(f"    ... and {len(messages) - 3} more")
                       else:
                           logger.warning(f"  ⚠ Failed to fetch page {page_count}")
                   
                   except Exception as e:
                       logger.error(f"  ❌ Error fetching page {page_count}: {e}")
                   
                   # Limit demo to first 5 pages
                   if page_count >= 5:
                       logger.info(f"  ... stopping demo at page {page_count}")
                       break
               
               logger.info(f"📊 Pagination complete: {page_count} pages processed")
               
           except Exception as e:
               logger.error(f"Failed search pagination: {e}")
   
       def demonstrate_advanced_search_patterns(self, uid_service: IMAPMailboxUIDService):
           """
           Demonstrate advanced search patterns and techniques.
           """
           logger.info("--- Advanced Search Patterns ---")
           
           try:
               # Pattern 1: Find emails that need attention
               needs_attention_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.UNSEEN,
                   IMAPSearchCriteria.or_criteria(
                       IMAPSearchCriteria.FLAGGED,
                       IMAPSearchCriteria.subject("urgent"),
                       IMAPSearchCriteria.subject("important"),
                       IMAPSearchCriteria.from_address("boss@company.com")
                   ),
                   IMAPSearchCriteria.since_days(30)
               )
               attention_messages = uid_service.create_message_set_from_search(needs_attention_criteria)
               logger.info(f"📧 Messages needing attention: {len(attention_messages)}")
               
               # Pattern 2: Find potential newsletters
               newsletter_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.or_criteria(
                       IMAPSearchCriteria.subject("newsletter"),
                       IMAPSearchCriteria.subject("unsubscribe"),
                       IMAPSearchCriteria.body("unsubscribe"),
                       IMAPSearchCriteria.from_address("noreply@"),
                       IMAPSearchCriteria.from_address("no-reply@")
                   ),
                   IMAPSearchCriteria.since_days(7)
               )
               newsletter_messages = uid_service.create_message_set_from_search(newsletter_criteria)
               logger.info(f"📧 Potential newsletters: {len(newsletter_messages)}")
               
               # Pattern 3: Find large attachments
               large_attachment_criteria = IMAPSearchCriteria.and_criteria(
                   IMAPSearchCriteria.larger(5 * 1024 * 1024),  # > 5MB
                   IMAPSearchCriteria.since_days(30)
               )
               large_attachment_messages = uid_service.create_message_set_from_search(large_attachment_criteria)
               logger.info(f"📧 Messages with large attachments: {len(large_attachment_messages)}")
               
               # Pattern 4: Find conversation threads
               # This would require fetching message IDs and In-Reply-To headers
               logger.info("📧 Conversation thread detection would require header analysis")
               
           except Exception as e:
               logger.error(f"Failed advanced search patterns: {e}")


   def main():
       """
       Main function to run the UID search example.
       """
       # Configuration - Replace with your actual credentials
       HOST = "imap.gmail.com"
       USERNAME = "your_email@gmail.com"
       PASSWORD = "your_app_password"
       PORT = 993
       
       # Create and run the example
       example = UIDSearchExample(HOST, USERNAME, PASSWORD, PORT)
       
       try:
           example.demonstrate_uid_search_operations()
           logger.info("🎉 UID search operations example completed successfully!")
           
       except Exception as e:
           logger.error(f"❌ Example failed: {e}")
           return 1
       
       return 0


   if __name__ == "__main__":
       exit(main())


Search Criteria Reference
-------------------------

Basic Criteria
~~~~~~~~~~~~~~

.. code-block:: python

   # Flag-based searches
   IMAPSearchCriteria.ALL           # All messages
   IMAPSearchCriteria.SEEN          # Read messages
   IMAPSearchCriteria.UNSEEN        # Unread messages
   IMAPSearchCriteria.FLAGGED       # Flagged messages
   IMAPSearchCriteria.UNFLAGGED     # Unflagged messages
   IMAPSearchCriteria.ANSWERED      # Answered messages
   IMAPSearchCriteria.UNANSWERED    # Unanswered messages
   IMAPSearchCriteria.DRAFT         # Draft messages
   IMAPSearchCriteria.UNDRAFT       # Non-draft messages
   IMAPSearchCriteria.DELETED       # Deleted messages
   IMAPSearchCriteria.UNDELETED     # Non-deleted messages
   IMAPSearchCriteria.RECENT        # Recent messages
   IMAPSearchCriteria.OLD           # Old messages

Date-Based Criteria
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Date searches
   IMAPSearchCriteria.before("01-Jan-2024")
   IMAPSearchCriteria.since("01-Jan-2024")
   IMAPSearchCriteria.on("01-Jan-2024")
   IMAPSearchCriteria.since_days(7)     # Last 7 days
   
   # Sent date searches
   IMAPSearchCriteria.sent_before("01-Jan-2024")
   IMAPSearchCriteria.sent_since("01-Jan-2024")
   IMAPSearchCriteria.sent_on("01-Jan-2024")

Content-Based Criteria
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Address searches
   IMAPSearchCriteria.from_address("user@domain.com")
   IMAPSearchCriteria.to_address("user@domain.com")
   IMAPSearchCriteria.cc_address("user@domain.com")
   IMAPSearchCriteria.bcc_address("user@domain.com")
   
   # Content searches
   IMAPSearchCriteria.subject("keyword")
   IMAPSearchCriteria.body("keyword")
   IMAPSearchCriteria.text("keyword")    # Subject OR body
   
   # Header searches
   IMAPSearchCriteria.header("Header-Name", "value")
   
   # Size searches
   IMAPSearchCriteria.larger(1024)      # > 1KB
   IMAPSearchCriteria.smaller(1024)     # < 1KB

Logical Operations
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # AND operation
   IMAPSearchCriteria.and_criteria(
       IMAPSearchCriteria.UNSEEN,
       IMAPSearchCriteria.since_days(7)
   )
   
   # OR operation
   IMAPSearchCriteria.or_criteria(
       IMAPSearchCriteria.FLAGGED,
       IMAPSearchCriteria.subject("urgent")
   )
   
   # NOT operation
   IMAPSearchCriteria.not_criteria(
       IMAPSearchCriteria.DELETED
   )

Performance Tips
----------------

1. **Use Date Ranges**: Limit searches to specific time periods

2. **Combine Criteria**: Use AND/OR to create efficient compound searches

3. **Cache Results**: Store frequently used search results

4. **Paginate Large Results**: Use MessageSet.iter_batches() for large result sets

5. **Use UID Ranges**: For sequential access, UID ranges can be faster

6. **Avoid Expensive Operations**: Body searches are slower than header searches

Common Search Patterns
----------------------

Unread Important Messages
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   urgent_unread = IMAPSearchCriteria.and_criteria(
       IMAPSearchCriteria.UNSEEN,
       IMAPSearchCriteria.or_criteria(
           IMAPSearchCriteria.FLAGGED,
           IMAPSearchCriteria.subject("urgent"),
           IMAPSearchCriteria.from_address("boss@company.com")
       )
   )

Recent Large Messages
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   recent_large = IMAPSearchCriteria.and_criteria(
       IMAPSearchCriteria.since_days(7),
       IMAPSearchCriteria.larger(5 * 1024 * 1024)  # > 5MB
   )

Cleanup Candidates
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   cleanup_candidates = IMAPSearchCriteria.and_criteria(
       IMAPSearchCriteria.before("01-Jan-2023"),
       IMAPSearchCriteria.SEEN,
       IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.FLAGGED)
   )

Best Practices
--------------

✅ **DO:**

- Use UID-based searches for reliability

- Combine criteria efficiently

- Cache frequent search results

- Use pagination for large result sets

- Test search performance with your data

❌ **DON'T:**

- Use sequence numbers for searches

- Perform expensive searches repeatedly

- Ignore search result sizes

- Use overly complex nested criteria

- Search without date limits in large mailboxes

Next Steps
----------

For more advanced patterns, see:

- :doc:`mailbox_management` - Mailbox operations
- :doc:`message_set_usage` - Advanced MessageSet usage
- :doc:`flag_operations` - Flag management
- :doc:`large_volume_handling` - Handling large datasets 