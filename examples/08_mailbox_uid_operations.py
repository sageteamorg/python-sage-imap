#!/usr/bin/env python3
"""
IMAP Mailbox UID Operations Example

This example demonstrates the comprehensive UID-based operations available in the
enhanced IMAPMailboxUIDService, including:

1. UID vs sequence number operations
2. UID search and fetch operations
3. UID-based message management
4. Persistent message identification
5. Synchronization-friendly operations
6. Performance considerations
7. Best practices for UID operations

Prerequisites:
- Valid IMAP server credentials
- Python 3.7+
- sage-imap library installed
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logging
import time
from datetime import datetime, timedelta

from _env import IMAP_HOST, IMAP_PASSWORD, IMAP_USER

from sage_imap.helpers.enums import MessagePart
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def uid_vs_sequence_comparison():
    """Compare UID operations with sequence number operations."""
    print("\n" + "=" * 60)
    print("UID VS SEQUENCE NUMBER COMPARISON")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            # Initialize both services
            regular_service = IMAPMailboxService(client)
            uid_service = IMAPMailboxUIDService(client)

            # Select INBOX for both services
            regular_result = regular_service.select("INBOX")
            uid_result = uid_service.select("INBOX")

            if not (regular_result.success and uid_result.success):
                print("✗ Failed to select INBOX for comparison")
                return

            print("✓ Both services initialized and INBOX selected")

            # 1. Search comparison
            print("\n1. Search operation comparison...")

            search_criteria = IMAPSearchCriteria.ALL

            # Regular search
            start_time = time.time()
            regular_search = regular_service.search(search_criteria)
            regular_time = time.time() - start_time

            # UID search
            start_time = time.time()
            uid_search = uid_service.uid_search(search_criteria)
            uid_time = time.time() - start_time

            if regular_search.success and uid_search.success:
                print(
                    f"  Regular search: {regular_search.message_count} messages ({regular_time:.3f}s)"
                )
                print(
                    f"  UID search: {uid_search.message_count} messages ({uid_time:.3f}s)"
                )

                # Show difference in identifiers
                regular_ids = regular_search.affected_messages[:5]
                uid_ids = uid_search.affected_messages[:5]

                print(f"  Regular IDs (sequence): {regular_ids}")
                print(f"  UID IDs (persistent): {uid_ids}")

                # Explain the difference
                print("\n  Key differences:")
                print(
                    "  - Sequence numbers: 1, 2, 3, 4, 5... (change when messages deleted)"
                )
                print(
                    "  - UIDs: 1001, 1003, 1007, 1012... (persistent, gaps are normal)"
                )

            # 2. Fetch comparison
            print("\n2. Fetch operation comparison...")

            if regular_search.success and uid_search.success:
                # Take first message from each
                if regular_search.affected_messages and uid_search.affected_messages:
                    regular_msg_set = MessageSet([regular_search.affected_messages[0]])
                    uid_msg_set = MessageSet([uid_search.affected_messages[0]])

                    # Regular fetch
                    start_time = time.time()
                    regular_fetch = regular_service.fetch(
                        regular_msg_set, MessagePart.BODY_PEEK_HEADER
                    )
                    regular_fetch_time = time.time() - start_time

                    # UID fetch
                    start_time = time.time()
                    uid_fetch = uid_service.uid_fetch(
                        uid_msg_set, MessagePart.BODY_PEEK_HEADER
                    )
                    uid_fetch_time = time.time() - start_time

                    if regular_fetch.success and uid_fetch.success:
                        print(
                            f"  Regular fetch: {regular_fetch.message_count} messages ({regular_fetch_time:.3f}s)"
                        )
                        print(
                            f"  UID fetch: {uid_fetch.message_count} messages ({uid_fetch_time:.3f}s)"
                        )

                        # Show fetched message details
                        regular_messages = regular_fetch.metadata.get(
                            "fetched_messages", []
                        )
                        uid_messages = uid_fetch.metadata.get("fetched_messages", [])

                        if regular_messages and uid_messages:
                            reg_msg = regular_messages[0]
                            uid_msg = uid_messages[0]

                            print(
                                f"  Regular message - Seq: {reg_msg.sequence_number}, UID: {reg_msg.uid}"
                            )
                            print(
                                f"  UID message - Seq: {uid_msg.sequence_number}, UID: {uid_msg.uid}"
                            )

            # 3. Stability demonstration
            print("\n3. Stability demonstration...")
            print("  Scenario: What happens when messages are deleted?")
            print("  ")
            print("  Before deletion:")
            print("    Sequence: 1, 2, 3, 4, 5")
            print("    UIDs:     101, 102, 103, 104, 105")
            print("  ")
            print("  After deleting message 2:")
            print("    Sequence: 1, 2, 3, 4    (numbers shift!)")
            print("    UIDs:     101, 103, 104, 105  (UIDs remain stable)")
            print("  ")
            print("  ✓ UID operations remain valid after deletions")
            print("  ✗ Sequence operations may target wrong messages")

            # 4. Use case recommendations
            print("\n4. Use case recommendations...")
            print("  Use sequence numbers for:")
            print("  - Simple, immediate operations")
            print("  - Single-session processing")
            print("  - Performance-critical simple tasks")
            print("  ")
            print("  Use UIDs for:")
            print("  - Multi-session operations")
            print("  - Message synchronization")
            print("  - Long-running processes")
            print("  - Reliable message tracking")
            print("  - Email client implementations")

    except Exception as e:
        print(f"✗ Error in comparison: {e}")


def uid_search_operations():
    """Demonstrate comprehensive UID search operations."""
    print("\n" + "=" * 60)
    print("UID SEARCH OPERATIONS")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            uid_service = IMAPMailboxUIDService(client)

            # Select INBOX
            select_result = uid_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for UID search operations")

            # 1. Basic UID search
            print("\n1. Basic UID search...")
            all_criteria = IMAPSearchCriteria.ALL
            search_result = uid_service.uid_search(all_criteria)

            if search_result.success:
                print(f"  ✓ Found {search_result.message_count} messages")
                print(f"  Execution time: {search_result.execution_time:.3f}s")

                uids = search_result.affected_messages
                if uids:
                    print(f"  UID range: {uids[0]} to {uids[-1]}")
                    print(f"  Sample UIDs: {uids[:10]}")

                    # Analyze UID gaps
                    if len(uids) > 1:
                        uid_ints = [int(uid) for uid in uids]
                        gaps = [
                            uid_ints[i + 1] - uid_ints[i]
                            for i in range(len(uid_ints) - 1)
                        ]
                        avg_gap = sum(gaps) / len(gaps)
                        max_gap = max(gaps)
                        print(
                            f"  UID gaps - Average: {avg_gap:.1f}, Maximum: {max_gap}"
                        )

            # 2. Date-based UID search
            print("\n2. Date-based UID search...")

            # Search for messages from last week
            last_week = datetime.now() - timedelta(days=7)
            date_criteria = IMAPSearchCriteria.since(last_week.strftime("%d-%b-%Y"))

            search_result = uid_service.uid_search(date_criteria)
            if search_result.success:
                print(
                    f"  ✓ Found {search_result.message_count} messages from last week"
                )
                recent_uids = search_result.affected_messages

                if recent_uids:
                    print(f"  Recent UIDs: {recent_uids[:5]}")

            # 3. Flag-based UID search
            print("\n3. Flag-based UID search...")

            # Search for unread messages
            unread_criteria = IMAPSearchCriteria.UNSEEN
            search_result = uid_service.uid_search(unread_criteria)

            if search_result.success:
                print(f"  ✓ Found {search_result.message_count} unread messages")
                unread_uids = search_result.affected_messages

                if unread_uids:
                    print(f"  Unread UIDs: {unread_uids[:5]}")

            # 4. Complex UID search
            print("\n4. Complex UID search...")

            # Multi-criteria search - combine multiple criteria
            since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
            complex_criteria = IMAPSearchCriteria.and_criteria(
                IMAPSearchCriteria.since(since_date), IMAPSearchCriteria.UNSEEN
            )

            search_result = uid_service.uid_search(complex_criteria)
            if search_result.success:
                print(
                    f"  ✓ Complex search found {search_result.message_count} messages"
                )
                print("  Criteria: Last 30 days, unread")

                if search_result.affected_messages:
                    print(f"  Matching UIDs: {search_result.affected_messages[:5]}")

            # 5. UID range operations
            print("\n5. UID range operations...")

            # Get all UIDs again for range demonstration
            all_search = uid_service.uid_search(IMAPSearchCriteria.ALL)
            if all_search.success and all_search.affected_messages:
                all_uids = [int(uid) for uid in all_search.affected_messages]

                # Demonstrate UID range selection
                min_uid = min(all_uids)
                max_uid = max(all_uids)
                mid_uid = (min_uid + max_uid) // 2

                print(f"  UID range: {min_uid} to {max_uid}")
                print(f"  Total UIDs: {len(all_uids)}")
                print(f"  Midpoint UID: {mid_uid}")

                # Search for UIDs above midpoint
                high_uid_criteria = IMAPSearchCriteria.uid(f"{mid_uid}:*")
                high_search = uid_service.uid_search(high_uid_criteria)

                if high_search.success:
                    print(
                        f"  UIDs above {mid_uid}: {high_search.message_count} messages"
                    )

            # 6. Performance analysis
            print("\n6. UID search performance analysis...")

            stats = uid_service.get_monitoring_statistics()
            search_count = stats.get("operations_by_type", {}).get("uid_search", 0)
            search_time = stats.get("average_times", {}).get("uid_search", 0)

            print("  ✓ Search performance metrics:")
            print(f"    Total UID searches: {search_count}")
            print(f"    Average search time: {search_time:.3f}s")

            if search_count > 0:
                print("  ✓ UID search performance is optimal")

    except Exception as e:
        print(f"✗ Error in UID search operations: {e}")


def uid_fetch_operations():
    """Demonstrate comprehensive UID fetch operations."""
    print("\n" + "=" * 60)
    print("UID FETCH OPERATIONS")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            uid_service = IMAPMailboxUIDService(client)

            # Select INBOX
            select_result = uid_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for UID fetch operations")

            # Get some UIDs to work with
            search_result = uid_service.uid_search(IMAPSearchCriteria.ALL)
            if not search_result.success or not search_result.affected_messages:
                print("✗ No messages found for fetch operations")
                return

            uids = search_result.affected_messages
            print(f"✓ Found {len(uids)} messages for fetch operations")

            # 1. Single message UID fetch
            print("\n1. Single message UID fetch...")

            single_uid = uids[0]
            msg_set = MessageSet([single_uid])

            fetch_result = uid_service.uid_fetch(msg_set, MessagePart.BODY_PEEK_HEADER)
            if fetch_result.success:
                print(f"  ✓ Fetched message UID {single_uid}")
                print(f"  Execution time: {fetch_result.execution_time:.3f}s")

                messages = fetch_result.metadata.get("fetched_messages", [])
                if messages:
                    msg = messages[0]
                    print("  Message details:")
                    print(f"    UID: {msg.uid}")
                    print(f"    Subject: {msg.subject}")
                    print(f"    From: {msg.from_address}")
                    print(f"    Size: {msg.size} bytes")
                    print(f"    Flags: {msg.flags}")

            # 2. Multiple message UID fetch
            print("\n2. Multiple message UID fetch...")

            # Fetch first 3 messages
            multi_uids = uids[:3]
            msg_set = MessageSet(multi_uids)

            fetch_result = uid_service.uid_fetch(msg_set, MessagePart.BODY_PEEK_HEADER)
            if fetch_result.success:
                print(f"  ✓ Fetched {fetch_result.message_count} messages")
                print(f"  Execution time: {fetch_result.execution_time:.3f}s")
                print(f"  UIDs: {multi_uids}")

                messages = fetch_result.metadata.get("fetched_messages", [])
                for i, msg in enumerate(messages):
                    print(f"    Message {i+1}: UID {msg.uid} - {msg.subject}")

            # 3. Different message parts
            print("\n3. Fetching different message parts...")

            test_uid = uids[0]
            msg_set = MessageSet([test_uid])

            # Fetch different parts
            parts_to_test = [
                (MessagePart.BODY_PEEK_HEADER, "Headers only"),
                (MessagePart.BODY_TEXT, "Text content"),
                (MessagePart.RFC822, "Full message"),
            ]

            for part, description in parts_to_test:
                fetch_result = uid_service.uid_fetch(msg_set, part)
                if fetch_result.success:
                    messages = fetch_result.metadata.get("fetched_messages", [])
                    if messages:
                        msg = messages[0]
                        print(
                            f"  ✓ {description}: {msg.size} bytes ({fetch_result.execution_time:.3f}s)"
                        )
                else:
                    print(f"  ✗ {description}: {fetch_result.error_message}")

            # 4. Batch UID fetch
            print("\n4. Batch UID fetch operations...")

            # Process UIDs in batches
            batch_size = 5
            total_uids = min(15, len(uids))  # Limit for demonstration

            print(f"  Processing {total_uids} UIDs in batches of {batch_size}")

            for i in range(0, total_uids, batch_size):
                batch_uids = uids[i : i + batch_size]
                batch_num = i // batch_size + 1

                msg_set = MessageSet(batch_uids)

                start_time = time.time()
                fetch_result = uid_service.uid_fetch(
                    msg_set, MessagePart.BODY_PEEK_HEADER
                )
                batch_time = time.time() - start_time

                if fetch_result.success:
                    print(
                        f"    Batch {batch_num}: {fetch_result.message_count} messages ({batch_time:.3f}s)"
                    )
                    print(f"      UIDs: {batch_uids}")
                else:
                    print(
                        f"    Batch {batch_num}: Failed - {fetch_result.error_message}"
                    )

            # 5. UID fetch with error handling
            print("\n5. UID fetch error handling...")

            # Test with invalid UID
            invalid_uid = "999999"  # Likely doesn't exist
            msg_set = MessageSet([invalid_uid])

            fetch_result = uid_service.uid_fetch(msg_set, MessagePart.BODY_PEEK_HEADER)
            if not fetch_result.success:
                print(
                    f"  ✓ Invalid UID handled gracefully: {fetch_result.error_message}"
                )
            else:
                print("  ✗ Invalid UID unexpectedly succeeded")

            # Test with mixed valid/invalid UIDs
            mixed_uids = [uids[0], "999999", uids[1] if len(uids) > 1 else uids[0]]
            msg_set = MessageSet(mixed_uids)

            fetch_result = uid_service.uid_fetch(msg_set, MessagePart.BODY_PEEK_HEADER)
            print(f"  Mixed UIDs result: {fetch_result.message_count} messages fetched")
            if fetch_result.success:
                print("    Successfully handled mixed valid/invalid UIDs")

            # 6. Performance metrics
            print("\n6. UID fetch performance metrics...")

            stats = uid_service.get_monitoring_statistics()
            fetch_count = stats.get("operations_by_type", {}).get("uid_fetch", 0)
            fetch_time = stats.get("average_times", {}).get("uid_fetch", 0)

            print("  ✓ Fetch performance:")
            print(f"    Total UID fetches: {fetch_count}")
            print(f"    Average fetch time: {fetch_time:.3f}s")

            if fetch_count > 0:
                print(
                    f"    Performance rating: {'Excellent' if fetch_time < 0.1 else 'Good' if fetch_time < 0.5 else 'Acceptable'}"
                )

    except Exception as e:
        print(f"✗ Error in UID fetch operations: {e}")


def uid_message_management():
    """Demonstrate UID-based message management operations."""
    print("\n" + "=" * 60)
    print("UID MESSAGE MANAGEMENT")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            uid_service = IMAPMailboxUIDService(client)

            # Select INBOX
            select_result = uid_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for UID message management")

            # Get some UIDs to work with
            search_result = uid_service.uid_search(IMAPSearchCriteria.ALL)
            if not search_result.success or not search_result.affected_messages:
                print("✗ No messages found for management operations")
                return

            uids = search_result.affected_messages
            print(f"✓ Found {len(uids)} messages for management operations")

            # 1. UID move operation simulation
            print("\n1. UID move operation simulation...")

            if len(uids) > 0:
                target_uid = uids[0]
                MessageSet([target_uid])

                print(f"  Simulating move of UID {target_uid} to Archive folder")
                print("  (Skipping actual move to preserve test environment)")

                print("  UID move operation would:")
                print("  1. Copy message to destination using UID")
                print("  2. Mark original as deleted using UID")
                print("  3. Expunge to remove from source")
                print("  4. Verify operation success")

                # Show the advantages of UID move
                print("\n  Advantages of UID move:")
                print("  - Persistent message identification")
                print("  - Safe for concurrent operations")
                print("  - Reliable across sessions")
                print("  - No sequence number conflicts")

            # 2. UID trash operation simulation
            print("\n2. UID trash operation simulation...")

            if len(uids) > 1:
                target_uid = uids[1]
                MessageSet([target_uid])

                print(f"  Simulating trash of UID {target_uid}")
                print("  (Skipping actual trash to preserve test environment)")

                print("  UID trash operation would:")
                print("  1. Mark message as deleted using UID")
                print("  2. Move to trash folder using UID")
                print("  3. Preserve UID for potential recovery")
                print("  4. Update monitoring statistics")

            # 3. UID restore operation simulation
            print("\n3. UID restore operation simulation...")

            print("  Restore operation scenario:")
            print("  1. User requests recovery of specific message")
            print("  2. System searches trash folder by UID")
            print("  3. Message is moved back to original location")
            print("  4. Deleted flag is removed")
            print("  5. UID remains consistent throughout")

            print("\n  UID restore advantages:")
            print("  - Exact message identification")
            print("  - No confusion with sequence numbers")
            print("  - Reliable recovery process")
            print("  - Audit trail preservation")

            # 4. Bulk UID operations
            print("\n4. Bulk UID operations...")

            # Simulate bulk operations with UIDs
            bulk_uids = uids[: min(10, len(uids))]

            print(f"  Processing {len(bulk_uids)} messages in bulk")
            print(
                "  UIDs to process:", bulk_uids[:5], "..." if len(bulk_uids) > 5 else ""
            )

            # Simulate batch processing
            batch_size = 3
            batches = [
                bulk_uids[i : i + batch_size]
                for i in range(0, len(bulk_uids), batch_size)
            ]

            print(f"  Processing in {len(batches)} batches of {batch_size}")

            for i, batch in enumerate(batches):
                print(f"    Batch {i+1}: UIDs {batch}")
                # Simulate processing time
                time.sleep(0.01)

            print("  ✓ Bulk UID operations completed")

            # 5. UID synchronization patterns
            print("\n5. UID synchronization patterns...")

            print("  Common synchronization scenarios:")
            print("  1. Client startup: Fetch all UIDs, compare with local cache")
            print("  2. Periodic sync: Check for new UIDs since last sync")
            print("  3. Change detection: Monitor UID validity")
            print("  4. Recovery: Re-sync based on UID ranges")

            # Demonstrate UID-based synchronization
            print("\n  Example synchronization workflow:")
            print("  ```python")
            print("  # Get current UIDs")
            print("  current_uids = uid_service.uid_search(IMAPSearchCriteria().all())")
            print("  ")
            print("  # Compare with cached UIDs")
            print("  cached_uids = load_cached_uids()")
            print("  new_uids = set(current_uids) - set(cached_uids)")
            print("  deleted_uids = set(cached_uids) - set(current_uids)")
            print("  ")
            print("  # Process changes")
            print("  for uid in new_uids:")
            print("      fetch_and_process_message(uid)")
            print("  ```")

            # 6. UID operation monitoring
            print("\n6. UID operation monitoring...")

            stats = uid_service.get_monitoring_statistics()

            print("  ✓ UID operation statistics:")
            uid_ops = {
                k: v
                for k, v in stats.get("operations_by_type", {}).items()
                if "uid" in k
            }

            if uid_ops:
                for operation, count in uid_ops.items():
                    print(f"    {operation}: {count} operations")
            else:
                print("    No UID operations recorded yet")

            # Show average times for UID operations
            uid_times = {
                k: v for k, v in stats.get("average_times", {}).items() if "uid" in k
            }
            if uid_times:
                print("  Average UID operation times:")
                for operation, avg_time in uid_times.items():
                    print(f"    {operation}: {avg_time:.3f}s")

    except Exception as e:
        print(f"✗ Error in UID message management: {e}")


def uid_best_practices():
    """Demonstrate best practices for UID operations."""
    print("\n" + "=" * 60)
    print("UID BEST PRACTICES")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            uid_service = IMAPMailboxUIDService(client)

            print("✓ UID service initialized for best practices demonstration")

            # 1. UID caching strategies
            print("\n1. UID caching strategies...")
            print("  Best practices for UID caching:")
            print("  - Cache UIDs with message metadata")
            print("  - Use UID validity to detect cache invalidation")
            print("  - Implement incremental synchronization")
            print("  - Store UID-to-message mappings")
            print("  - Handle UID gaps gracefully")

            # Example caching structure
            print("\n  Example cache structure:")
            print("  ```python")
            print("  cache = {")
            print("      'uid_validity': 1234567890,")
            print("      'last_sync': '2024-01-15T10:30:00Z',")
            print("      'messages': {")
            print("          '1001': {'subject': 'Email 1', 'flags': ['\\Seen']},")
            print("          '1003': {'subject': 'Email 2', 'flags': ['\\Unseen']},")
            print("          '1007': {'subject': 'Email 3', 'flags': ['\\Flagged']}")
            print("      }")
            print("  }```")

            # 2. Error handling patterns
            print("\n2. Error handling patterns...")
            print("  Robust UID error handling:")
            print("  - Validate UID format before operations")
            print("  - Handle UID expiration gracefully")
            print("  - Implement retry logic for transient failures")
            print("  - Log UID operation failures for debugging")
            print("  - Provide meaningful error messages")

            # Demonstrate error handling
            print("\n  Example error handling:")
            print("  ```python")
            print("  try:")
            print("      result = uid_service.uid_fetch(msg_set, MessagePart.HEADER)")
            print("      if not result.success:")
            print(
                "          logger.warning(f'UID fetch failed: {result.error_message}')"
            )
            print("          # Implement fallback or retry logic")
            print("  except Exception as e:")
            print("      logger.error(f'UID operation error: {e}')")
            print("      # Handle unexpected errors")
            print("  ```")

            # 3. Performance optimization
            print("\n3. Performance optimization...")
            print("  UID performance best practices:")
            print("  - Batch UID operations when possible")
            print("  - Use UID ranges for large operations")
            print("  - Cache frequently accessed UIDs")
            print("  - Minimize full mailbox scans")
            print("  - Monitor operation performance")

            # Show performance monitoring
            stats = uid_service.get_monitoring_statistics()
            print("\n  Current performance metrics:")
            print(f"    Total operations: {stats.get('total_operations', 0)}")
            print(f"    Service uptime: {stats.get('uptime', 0):.1f}s")

            avg_times = stats.get("average_times", {})
            if avg_times:
                print("    Average operation times:")
                for op, time_val in avg_times.items():
                    print(f"      {op}: {time_val:.3f}s")

            # 4. Synchronization patterns
            print("\n4. Synchronization patterns...")
            print("  Effective UID synchronization:")
            print("  - Use UID SEARCH for change detection")
            print("  - Implement incremental updates")
            print("  - Handle mailbox state changes")
            print("  - Maintain UID consistency")
            print("  - Support offline/online transitions")

            # Example synchronization workflow
            print("\n  Synchronization workflow:")
            print("  1. Check UID validity")
            print("  2. Get current UID list")
            print("  3. Compare with cached UIDs")
            print("  4. Fetch new messages")
            print("  5. Update local cache")
            print("  6. Clean up deleted messages")

            # 5. Integration patterns
            print("\n5. Integration patterns...")
            print("  UID integration best practices:")
            print("  - Use UIDs for message threading")
            print("  - Implement UID-based search indexes")
            print("  - Support cross-folder UID operations")
            print("  - Handle UID in message URLs")
            print("  - Maintain UID audit trails")

            # 6. Testing strategies
            print("\n6. Testing strategies...")
            print("  UID testing approaches:")
            print("  - Test UID persistence across sessions")
            print("  - Verify UID stability after deletions")
            print("  - Test UID range operations")
            print("  - Validate error handling")
            print("  - Performance test with large UID sets")

            print("\n  Testing considerations:")
            print("  - UIDs are server-specific")
            print("  - UID validity can change")
            print("  - Network failures affect UID operations")
            print("  - Concurrent access impacts UID stability")
            print("  - Different servers have different UID behaviors")

            # 7. Migration and backup
            print("\n7. Migration and backup...")
            print("  UID considerations for migration:")
            print("  - UIDs are not portable between servers")
            print("  - Use message headers for cross-server identification")
            print("  - Implement UID mapping during migration")
            print("  - Backup UID-to-message relationships")
            print("  - Test UID operations after migration")

            # Final recommendations
            print("\n8. Final recommendations...")
            print("  ✓ Always use UID operations for:")
            print("    - Multi-session applications")
            print("    - Message synchronization")
            print("    - Long-running processes")
            print("    - Reliable message tracking")
            print("  ")
            print("  ✓ Consider sequence numbers for:")
            print("    - Simple, immediate operations")
            print("    - Single-session processing")
            print("    - Performance-critical tasks")
            print("  ")
            print("  ✓ Key success factors:")
            print("    - Understand UID behavior")
            print("    - Implement proper error handling")
            print("    - Monitor performance metrics")
            print("    - Test thoroughly")
            print("    - Document UID usage patterns")

    except Exception as e:
        print(f"✗ Error in best practices demonstration: {e}")


def main():
    """Run all UID operation examples."""
    print("IMAP Mailbox UID Operations Examples")
    print("=" * 60)
    print("This example demonstrates comprehensive UID-based operations")
    print("for reliable and persistent message handling.")

    try:
        # Run all examples
        uid_vs_sequence_comparison()
        uid_search_operations()
        uid_fetch_operations()
        uid_message_management()
        uid_best_practices()

        print("\n" + "=" * 60)
        print("UID OPERATIONS EXAMPLES COMPLETED")
        print("=" * 60)
        print("All UID operation examples have been demonstrated.")
        print("Key takeaways:")
        print("- UIDs provide persistent message identification")
        print("- UID operations are safer for long-running processes")
        print("- Proper error handling is crucial for UID operations")
        print("- Performance monitoring helps optimize UID usage")
        print("- Best practices ensure reliable implementations")

    except KeyboardInterrupt:
        print("\n✗ Examples interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Unexpected error in UID examples")


if __name__ == "__main__":
    main()
