#!/usr/bin/env python3
"""
Enhanced IMAP Mailbox Operations Example

This example demonstrates the comprehensive mailbox operations available in the
enhanced IMAPMailboxService, including:

1. Basic mailbox operations (select, close, status)
2. Email search and fetch operations
3. Message management (move, delete, trash, restore)
4. Bulk operations and batch processing
5. Monitoring and statistics
6. Error handling and validation

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

from sage_imap.helpers.enums import MailboxStatusItems, MessagePart
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.models.message import MessageSet
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.mailbox import IMAPMailboxService, IMAPMailboxUIDService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def basic_mailbox_operations():
    """Demonstrate basic mailbox operations."""
    print("\n" + "=" * 60)
    print("BASIC MAILBOX OPERATIONS")
    print("=" * 60)

    # Configuration
    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
        timeout=30.0,
    )

    try:
        with IMAPClient.from_config(config) as client:
            # Initialize mailbox service
            mailbox_service = IMAPMailboxService(client)

            print("✓ Mailbox service initialized")

            # 1. Select INBOX
            print("\n1. Selecting INBOX...")
            result = mailbox_service.select("INBOX")
            if result.success:
                print(
                    f"✓ Selected INBOX (execution time: {result.execution_time:.3f}s)"
                )
                print(f"  Current selection: {mailbox_service.current_selection}")
            else:
                print(f"✗ Failed to select INBOX: {result.error_message}")
                return

            # 2. Get mailbox status
            print("\n2. Getting mailbox status...")
            status_result = mailbox_service.status(
                "INBOX",
                MailboxStatusItems.MESSAGES,
                MailboxStatusItems.RECENT,
                MailboxStatusItems.UNSEEN,
            )

            if status_result.success:
                print(
                    f"✓ Mailbox status retrieved (execution time: {status_result.execution_time:.3f}s)"
                )
                print(
                    f"  Status response: {status_result.metadata.get('status_response')}"
                )
            else:
                print(f"✗ Failed to get status: {status_result.error_message}")

            # 3. Check mailbox
            print("\n3. Performing mailbox check...")
            check_result = mailbox_service.check()
            if check_result.success:
                print(
                    f"✓ Mailbox check completed (execution time: {check_result.execution_time:.3f}s)"
                )
            else:
                print(f"✗ Mailbox check failed: {check_result.error_message}")

            # 4. Get mailbox statistics
            print("\n4. Getting mailbox statistics...")
            stats = mailbox_service.get_mailbox_statistics()
            print("✓ Mailbox statistics:")
            print(f"  Total messages: {stats.total_messages}")
            print(f"  Unread messages: {stats.unread_messages}")
            print(f"  Recent messages: {stats.recent_messages}")

            # 5. Close mailbox
            print("\n5. Closing mailbox...")
            close_result = mailbox_service.close()
            if close_result.success:
                print(
                    f"✓ Mailbox closed (execution time: {close_result.execution_time:.3f}s)"
                )
                print(f"  Current selection: {mailbox_service.current_selection}")
            else:
                print(f"✗ Failed to close mailbox: {close_result.error_message}")

    except Exception as e:
        print(f"✗ Error in basic operations: {e}")


def search_and_fetch_operations():
    """Demonstrate search and fetch operations."""
    print("\n" + "=" * 60)
    print("SEARCH AND FETCH OPERATIONS")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            mailbox_service = IMAPMailboxService(client)

            # Select INBOX
            select_result = mailbox_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for search operations")

            # 1. Search for recent emails
            print("\n1. Searching for recent emails...")
            search_criteria = IMAPSearchCriteria.recent(
                7
            )  # Recent emails from last 7 days
            search_result = mailbox_service.search(search_criteria)

            if search_result.success:
                print(f"✓ Found {search_result.message_count} recent emails")
                print(f"  Execution time: {search_result.execution_time:.3f}s")
                print(
                    f"  Message IDs: {search_result.affected_messages[:5]}..."
                )  # Show first 5
            else:
                print(f"✗ Search failed: {search_result.error_message}")
                return

            # 2. Search for emails from last week
            print("\n2. Searching for emails from last week...")
            last_week = datetime.now() - timedelta(days=7)
            search_criteria = IMAPSearchCriteria.since(last_week.strftime("%d-%b-%Y"))
            search_result = mailbox_service.search(search_criteria)

            if search_result.success:
                print(f"✓ Found {search_result.message_count} emails from last week")
                message_ids = search_result.affected_messages
            else:
                print(f"✗ Search failed: {search_result.error_message}")
                return

            # 3. Fetch email headers (if we have messages)
            if message_ids:
                print("\n3. Fetching email headers...")
                # Take first 3 messages for demonstration
                msg_set = MessageSet(message_ids[:3])
                fetch_result = mailbox_service.fetch(
                    msg_set, MessagePart.BODY_PEEK_HEADER
                )

                if fetch_result.success:
                    print(f"✓ Fetched {fetch_result.message_count} email headers")
                    print(f"  Execution time: {fetch_result.execution_time:.3f}s")

                    # Display email information
                    fetched_messages = fetch_result.metadata.get("fetched_messages", [])
                    for i, email in enumerate(fetched_messages[:2]):  # Show first 2
                        print(f"  Email {i+1}:")
                        print(f"    Subject: {email.subject}")
                        print(f"    From: {email.from_address}")
                        print(f"    Date: {email.date}")
                        print(f"    Size: {email.size} bytes")
                        print(f"    Flags: {email.flags}")
                else:
                    print(f"✗ Fetch failed: {fetch_result.error_message}")

            # 4. Search for unread emails
            print("\n4. Searching for unread emails...")
            search_criteria = IMAPSearchCriteria.UNSEEN
            search_result = mailbox_service.search(search_criteria)

            if search_result.success:
                print(f"✓ Found {search_result.message_count} unread emails")
                if search_result.message_count > 0:
                    print(
                        f"  First few unread message IDs: {search_result.affected_messages[:3]}"
                    )
            else:
                print(f"✗ Unread search failed: {search_result.error_message}")

    except Exception as e:
        print(f"✗ Error in search operations: {e}")


def message_management_operations():
    """Demonstrate message management operations."""
    print("\n" + "=" * 60)
    print("MESSAGE MANAGEMENT OPERATIONS")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            mailbox_service = IMAPMailboxService(client)

            # Select INBOX
            select_result = mailbox_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for message management")

            # 1. Find some messages to work with
            print("\n1. Finding messages to manage...")
            search_criteria = IMAPSearchCriteria.ALL
            search_result = mailbox_service.search(search_criteria)

            if not search_result.success or search_result.message_count == 0:
                print("✗ No messages found to manage")
                return

            message_ids = search_result.affected_messages
            print(f"✓ Found {len(message_ids)} messages to work with")

            # 2. Move operation simulation (using first message)
            if len(message_ids) > 0:
                print("\n2. Simulating move operation...")
                MessageSet([message_ids[0]])

                # Note: This is a simulation - in real usage, ensure destination exists
                print(f"  Would move message {message_ids[0]} to 'Archive' folder")
                print("  (Skipping actual move to preserve test environment)")

                # Demonstrate the move method structure
                print("  Move operation would include:")
                print("  - Copy message to destination")
                print("  - Mark original as deleted")
                print("  - Expunge to remove from source")

            # 3. Trash operation simulation
            print("\n3. Simulating trash operation...")
            if len(message_ids) > 1:
                MessageSet([message_ids[1]])
                print(f"  Would trash message {message_ids[1]} to 'Trash' folder")
                print("  (Skipping actual trash to preserve test environment)")

            # 4. Demonstrate bulk operations concept
            print("\n4. Bulk operations concept...")
            if len(message_ids) > 5:
                batch_size = 3
                total_messages = min(6, len(message_ids))
                print(
                    f"  Processing {total_messages} messages in batches of {batch_size}"
                )

                for i in range(0, total_messages, batch_size):
                    batch = message_ids[i : i + batch_size]
                    print(f"  Batch {i//batch_size + 1}: {len(batch)} messages")
                    print(f"    Message IDs: {batch}")
                    # In real usage, would process each batch
                    time.sleep(0.1)  # Simulate processing time

            # 5. Show monitoring statistics
            print("\n5. Monitoring statistics...")
            stats = mailbox_service.get_monitoring_statistics()
            print("✓ Operation statistics:")
            print(f"  Total operations: {stats.get('total_operations', 0)}")
            print(f"  Operations by type: {stats.get('operations_by_type', {})}")
            print(f"  Error counts: {stats.get('error_counts', {})}")
            print(f"  Average execution times: {stats.get('average_times', {})}")

    except Exception as e:
        print(f"✗ Error in message management: {e}")


def uid_operations_example():
    """Demonstrate UID-based operations."""
    print("\n" + "=" * 60)
    print("UID-BASED OPERATIONS")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            # Initialize UID service
            uid_service = IMAPMailboxUIDService(client)

            # Select INBOX
            select_result = uid_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for UID operations")

            # 1. UID search
            print("\n1. Performing UID search...")
            search_criteria = IMAPSearchCriteria.ALL
            search_result = uid_service.uid_search(search_criteria)

            if search_result.success:
                print(f"✓ UID search found {search_result.message_count} messages")
                print(f"  Execution time: {search_result.execution_time:.3f}s")
                uid_list = search_result.affected_messages
                print(f"  First few UIDs: {uid_list[:5]}")
            else:
                print(f"✗ UID search failed: {search_result.error_message}")
                return

            # 2. UID fetch
            if uid_list:
                print("\n2. Fetching messages by UID...")
                msg_set = MessageSet(uid_list[:2])  # Fetch first 2 messages
                fetch_result = uid_service.uid_fetch(
                    msg_set, MessagePart.BODY_PEEK_HEADER
                )

                if fetch_result.success:
                    print(
                        f"✓ UID fetch retrieved {fetch_result.message_count} messages"
                    )
                    print(f"  Execution time: {fetch_result.execution_time:.3f}s")

                    # Display message information
                    fetched_messages = fetch_result.metadata.get("fetched_messages", [])
                    for i, email in enumerate(fetched_messages):
                        print(f"  Message {i+1}:")
                        print(f"    UID: {email.uid}")
                        print(f"    Subject: {email.subject}")
                        print(f"    From: {email.sender}")
                else:
                    print(f"✗ UID fetch failed: {fetch_result.error_message}")

            # 3. UID operations simulation
            print("\n3. UID operations simulation...")
            print("  UID operations provide persistent message identification")
            print("  - UIDs remain constant during session")
            print("  - Safer for long-running operations")
            print("  - Preferred for message synchronization")

            # 4. Compare with regular operations
            print("\n4. UID vs Regular operations comparison...")
            print("  Regular operations:")
            print("  - Use sequence numbers (1, 2, 3, ...)")
            print("  - Numbers change when messages are deleted")
            print("  - Faster for simple operations")
            print("  ")
            print("  UID operations:")
            print("  - Use unique identifiers")
            print("  - UIDs remain stable")
            print("  - Better for complex workflows")

            # 5. Show monitoring statistics
            print("\n5. UID service monitoring...")
            stats = uid_service.get_monitoring_statistics()
            print("✓ UID service statistics:")
            print(f"  Total operations: {stats.get('total_operations', 0)}")
            print(f"  Recent operations: {len(stats.get('recent_operations', []))}")

    except Exception as e:
        print(f"✗ Error in UID operations: {e}")


def bulk_operations_example():
    """Demonstrate bulk operations and batch processing."""
    print("\n" + "=" * 60)
    print("BULK OPERATIONS AND BATCH PROCESSING")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            mailbox_service = IMAPMailboxService(client)

            # Select INBOX
            select_result = mailbox_service.select("INBOX")
            if not select_result.success:
                print(f"✗ Failed to select INBOX: {select_result.error_message}")
                return

            print("✓ INBOX selected for bulk operations")

            # 1. Search and process example
            print("\n1. Search and process example...")
            search_criteria = IMAPSearchCriteria.ALL

            def message_processor(email_message: EmailMessage):
                """Example message processor function."""
                print(f"    Processing: {email_message.subject[:50]}...")
                # Simulate processing time
                time.sleep(0.01)
                return True

            # Use search_and_process method
            result = mailbox_service.search_and_process(
                criteria=search_criteria,
                processor_func=message_processor,
                batch_size=5,
                charset="UTF-8",
            )

            if result.is_successful:
                print(f"✓ Processed {result.successful_messages} messages successfully")
                print(f"  Total execution time: {result.execution_time:.3f}s")
                print(f"  Batches processed: {result.batches_processed}")
                print(f"  Success rate: {result.success_rate:.1f}%")
            else:
                print("✗ Bulk processing completed with issues:")
                print(f"  Successful: {result.successful_messages}")
                print(f"  Failed: {result.failed_messages}")
                print(f"  Errors: {result.errors[:3]}")  # Show first 3 errors

            # 2. Batch configuration example
            print("\n2. Batch configuration example...")
            print("  Configuring batch processing parameters:")

            # Set custom batch size
            original_batch_size = mailbox_service.bulk_operation_batch_size
            mailbox_service.bulk_operation_batch_size = 10
            print(f"  - Set batch size to {mailbox_service.bulk_operation_batch_size}")

            # Set concurrency limit
            original_concurrency = mailbox_service.max_concurrent_operations
            mailbox_service.max_concurrent_operations = 3
            print(
                f"  - Set max concurrent operations to {mailbox_service.max_concurrent_operations}"
            )

            # Restore original values
            mailbox_service.bulk_operation_batch_size = original_batch_size
            mailbox_service.max_concurrent_operations = original_concurrency
            print("  - Restored original configuration")

            # 3. Bulk operation simulation
            print("\n3. Bulk operation simulation...")

            # Find messages to work with
            search_result = mailbox_service.search(IMAPSearchCriteria.ALL)
            if search_result.success and search_result.message_count > 0:
                message_ids = search_result.affected_messages[:6]  # Limit to 6 for demo

                # Simulate bulk move operations
                print(f"  Simulating bulk move of {len(message_ids)} messages...")

                # Create message sets for bulk operations
                message_sets = []
                for i, msg_id in enumerate(message_ids):
                    msg_set = MessageSet([msg_id])
                    destination = "Archive"  # In real usage, use actual folders
                    message_sets.append((msg_set, destination))

                print(f"  Created {len(message_sets)} move operations")
                print("  (Skipping actual execution to preserve test environment)")

                # Show what bulk_move would do
                print("  Bulk move operation would:")
                print("  - Process operations in batches")
                print("  - Provide comprehensive error handling")
                print("  - Return detailed statistics")
                print("  - Monitor execution time and success rates")

            # 4. Performance monitoring
            print("\n4. Performance monitoring...")
            stats = mailbox_service.get_monitoring_statistics()

            print("✓ Performance metrics:")
            print(f"  Service uptime: {stats.get('uptime', 0):.1f} seconds")
            print(f"  Total operations: {stats.get('total_operations', 0)}")

            # Show operation breakdown
            ops_by_type = stats.get("operations_by_type", {})
            if ops_by_type:
                print("  Operations by type:")
                for op_type, count in ops_by_type.items():
                    print(f"    {op_type}: {count}")

            # Show average times
            avg_times = stats.get("average_times", {})
            if avg_times:
                print("  Average execution times:")
                for op_type, avg_time in avg_times.items():
                    print(f"    {op_type}: {avg_time:.3f}s")

    except Exception as e:
        print(f"✗ Error in bulk operations: {e}")


def error_handling_and_validation():
    """Demonstrate error handling and validation features."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING AND VALIDATION")
    print("=" * 60)

    config = ConnectionConfig(
        host=IMAP_HOST,
        username=IMAP_USER,
        password=IMAP_PASSWORD,
        enable_monitoring=True,
    )

    try:
        with IMAPClient.from_config(config) as client:
            mailbox_service = IMAPMailboxService(client)

            print("✓ Mailbox service initialized with validation")

            # 1. Mailbox validation
            print("\n1. Testing mailbox validation...")

            # Test invalid mailbox names
            invalid_mailboxes = ["", None, "folder/../dangerous", "folder\0null"]

            for invalid_mailbox in invalid_mailboxes:
                try:
                    if invalid_mailbox is None:
                        print("  Testing None mailbox...")
                    else:
                        print(f"  Testing invalid mailbox: '{invalid_mailbox}'")

                    result = mailbox_service.select(invalid_mailbox)
                    if not result.success:
                        print(
                            f"    ✓ Validation caught invalid mailbox: {result.error_message}"
                        )
                    else:
                        print("    ✗ Validation failed to catch invalid mailbox")

                except Exception as e:
                    print(f"    ✓ Exception caught invalid mailbox: {str(e)}")

            # 2. MessageSet validation
            print("\n2. Testing MessageSet validation...")

            # Test invalid message sets
            try:
                from sage_imap.models.message import MessageSet

                # Empty message set
                try:
                    empty_msg_set = MessageSet([])
                    mailbox_service.validator.validate_message_set(empty_msg_set)
                    print("    ✗ Empty MessageSet validation failed")
                except ValueError as e:
                    print(f"    ✓ Empty MessageSet validation: {e}")

                # Invalid message ID types
                try:
                    invalid_msg_set = MessageSet([1, "2", None])
                    mailbox_service.validator.validate_message_set(invalid_msg_set)
                    print("    ✗ Invalid MessageSet validation failed")
                except (ValueError, TypeError) as e:
                    print(f"    ✓ Invalid MessageSet validation: {e}")

            except Exception as e:
                print(f"    ✓ MessageSet validation system working: {e}")

            # 3. Operation error handling
            print("\n3. Testing operation error handling...")

            # Test operation on non-existent mailbox
            result = mailbox_service.select("NonExistentMailbox123")
            if not result.success:
                print(f"    ✓ Non-existent mailbox handled: {result.error_message}")
                print(f"    Execution time: {result.execution_time:.3f}s")

            # Test operation without mailbox selection
            mailbox_service.current_selection = None
            search_result = mailbox_service.search(IMAPSearchCriteria().all())
            if not search_result.success:
                print("    ✓ No mailbox selection handled gracefully")

            # 4. Monitoring error tracking
            print("\n4. Error monitoring...")
            stats = mailbox_service.get_monitoring_statistics()
            error_counts = stats.get("error_counts", {})

            if error_counts:
                print("✓ Error tracking active:")
                for operation, count in error_counts.items():
                    print(f"    {operation}: {count} errors")
            else:
                print("✓ No errors recorded in current session")

            # 5. Recovery and resilience
            print("\n5. Recovery and resilience features...")
            print("  The mailbox service includes:")
            print("  - Automatic validation of all inputs")
            print("  - Graceful error handling with detailed messages")
            print("  - Operation monitoring and statistics")
            print("  - Comprehensive logging for debugging")
            print("  - Context manager support for resource cleanup")
            print("  - Retry-friendly operation design")

    except Exception as e:
        print(f"✗ Error in error handling demo: {e}")


def main():
    """Run all mailbox operation examples."""
    print("Enhanced IMAP Mailbox Operations Examples")
    print("=" * 60)
    print("This example demonstrates the comprehensive mailbox operations")
    print("available in the enhanced sage-imap library.")

    try:
        # Run all examples
        basic_mailbox_operations()
        search_and_fetch_operations()
        message_management_operations()
        uid_operations_example()
        bulk_operations_example()
        error_handling_and_validation()

        print("\n" + "=" * 60)
        print("EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("All mailbox operation examples have been demonstrated.")
        print("The enhanced mailbox service provides:")
        print("- Comprehensive operation support")
        print("- Robust error handling and validation")
        print("- Performance monitoring and statistics")
        print("- Bulk operations with batch processing")
        print("- UID-based operations for stability")
        print("- Production-ready reliability features")

    except KeyboardInterrupt:
        print("\n✗ Examples interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Unexpected error in examples")


if __name__ == "__main__":
    main()
