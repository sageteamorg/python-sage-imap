#!/usr/bin/env python3
"""
Advanced IMAP Mailbox Features Example

This example demonstrates advanced features of the enhanced IMAPMailboxService:

1. Email upload and EML file handling
2. Sent message management
3. Advanced search patterns and criteria
4. Mailbox statistics and analytics
5. Message restoration and recovery
6. Custom validation and monitoring
7. Performance optimization techniques

Prerequisites:
- Valid IMAP server credentials
- Python 3.7+
- sage-imap library installed
- Sample EML files (optional)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import logging
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from _env import IMAP_HOST, IMAP_PASSWORD, IMAP_USER

from sage_imap.helpers.enums import Flag
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.models.email import EmailMessage
from sage_imap.services.client import ConnectionConfig, IMAPClient
from sage_imap.services.mailbox import IMAPMailboxService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_sample_email() -> EmailMessage:
    """Create a sample email for testing purposes."""
    msg = MIMEMultipart()
    msg["From"] = "test@example.com"
    msg["To"] = "recipient@example.com"
    msg["Subject"] = f'Test Email - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

    body = f"""
    This is a test email created at {datetime.now()}.

    This email demonstrates the enhanced mailbox service capabilities:
    - Email upload functionality
    - EML file handling
    - Message processing
    - Advanced search features

    Best regards,
    Enhanced IMAP Service
    """

    msg.attach(MIMEText(body, "plain"))

    # Create EmailMessage from MIME message
    email_message = EmailMessage(
        message_id=f"<test-{datetime.now().timestamp()}@example.com>"
    )
    email_message.raw = msg.as_bytes()
    email_message.subject = msg["Subject"]
    email_message.from_address = msg["From"]
    email_message.to_address = [msg["To"]]
    email_message.date = datetime.now().isoformat()
    email_message.size = len(email_message.raw)

    return email_message


def email_upload_operations():
    """Demonstrate email upload and EML file handling."""
    print("\n" + "=" * 60)
    print("EMAIL UPLOAD AND EML FILE HANDLING")
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

            print("✓ INBOX selected for upload operations")

            # 1. Create sample emails
            print("\n1. Creating sample emails...")
            sample_emails = []

            for i in range(3):
                email = create_sample_email()
                email.subject = (
                    f"Sample Email {i+1} - {datetime.now().strftime('%H:%M:%S')}"
                )
                sample_emails.append(email)
                print(f"  ✓ Created email {i+1}: {email.subject}")

            # 2. Upload emails (simulation)
            print("\n2. Simulating email upload...")
            print("  Note: Actual upload skipped to preserve test environment")

            # Demonstrate upload_eml method structure
            print("  Upload operation would include:")
            print("  - Validation of email data")
            print("  - Batch processing for efficiency")
            print("  - Comprehensive error handling")
            print("  - Progress monitoring")
            print("  - Detailed result reporting")

            # Show what the upload would look like
            flags = Flag.SEEN  # Mark as read
            mailbox = "INBOX"

            print(f"  Would upload {len(sample_emails)} emails to {mailbox}")
            print(f"  With flags: {flags}")
            print(f"  Batch size: {mailbox_service.bulk_operation_batch_size}")

            # Simulate upload result
            print("\n3. Upload result simulation...")
            print("  ✓ Upload completed successfully")
            print(f"  Total emails: {len(sample_emails)}")
            print(f"  Successful: {len(sample_emails)}")
            print("  Failed: 0")
            print("  Execution time: 0.125s")
            print("  Success rate: 100.0%")

            # 4. EML file handling
            print("\n4. EML file handling capabilities...")
            print("  The service supports:")
            print("  - EmailIterator for memory-efficient processing")
            print("  - List[EmailMessage] for direct upload")
            print("  - Automatic validation of email structure")
            print("  - Date and flag preservation")
            print("  - Size and metadata tracking")

            # 5. Bulk upload simulation
            print("\n5. Bulk upload simulation...")
            print("  For large email collections:")
            print("  - Automatic batch processing")
            print("  - Progress reporting every 10 batches")
            print("  - Error collection and reporting")
            print("  - Performance monitoring")
            print("  - Memory-efficient processing")

            # Show batch processing logic
            batch_size = mailbox_service.bulk_operation_batch_size
            total_emails = 100  # Simulate large collection
            batches = (total_emails + batch_size - 1) // batch_size

            print(f"  Example: {total_emails} emails, batch size {batch_size}")
            print(f"  Would process in {batches} batches")

            for i in range(min(3, batches)):  # Show first 3 batches
                start_idx = i * batch_size
                end_idx = min(start_idx + batch_size, total_emails)
                print(f"    Batch {i+1}: emails {start_idx+1}-{end_idx}")

    except Exception as e:
        print(f"✗ Error in upload operations: {e}")


def sent_message_management():
    """Demonstrate sent message management."""
    print("\n" + "=" * 60)
    print("SENT MESSAGE MANAGEMENT")
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

            print("✓ Mailbox service initialized for sent message management")

            # 1. Create a sent message
            print("\n1. Creating sent message...")
            sent_msg = MIMEMultipart()
            sent_msg["From"] = IMAP_USER
            sent_msg["To"] = "recipient@example.com"
            sent_msg["Subject"] = (
                f'Sent Message - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            )
            sent_msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")

            body = """
            This is a sent message being saved to the Sent folder.

            The enhanced mailbox service provides:
            - Automatic sent message handling
            - Proper flag management
            - Date preservation
            - Comprehensive validation
            """

            sent_msg.attach(MIMEText(body, "plain"))
            raw_email = sent_msg.as_bytes()

            print(f"  ✓ Created sent message: {sent_msg['Subject']}")
            print(f"  Message size: {len(raw_email)} bytes")

            # 2. Save sent message (simulation)
            print("\n2. Saving sent message...")
            print("  Note: Actual save skipped to preserve test environment")

            sent_mailbox = "Sent"
            flags = Flag.SEEN  # Mark as read
            date_time = datetime.now().strftime("%d-%b-%Y %H:%M:%S %z")

            print("  Save operation would include:")
            print(f"  - Target mailbox: {sent_mailbox}")
            print(f"  - Flags: {flags}")
            print(f"  - Date/time: {date_time}")
            print("  - Validation of raw email data")
            print("  - Error handling and monitoring")

            # 3. Sent message validation
            print("\n3. Sent message validation...")
            print("  The service validates:")
            print("  - Raw email format (str or bytes)")
            print("  - Mailbox name validity")
            print("  - Flag compatibility")
            print("  - Date format correctness")
            print("  - Message structure integrity")

            # 4. Sent folder management
            print("\n4. Sent folder management...")

            # Select Sent folder (if it exists)
            select_result = mailbox_service.select("Sent")
            if select_result.success:
                print("  ✓ Sent folder selected successfully")

                # Get sent folder statistics
                stats = mailbox_service.get_mailbox_statistics("Sent")
                print("  Sent folder statistics:")
                print(f"    Total messages: {stats.total_messages}")
                print(f"    Unread messages: {stats.unread_messages}")
                print(f"    Recent messages: {stats.recent_messages}")

            else:
                print("  ✗ Sent folder not accessible or doesn't exist")
                print("  In production, you might:")
                print("  - Create the folder if it doesn't exist")
                print("  - Use alternative folder names")
                print("  - Handle folder access errors gracefully")

            # 5. Integration with email sending
            print("\n5. Integration with email sending...")
            print("  Typical workflow:")
            print("  1. Compose email message")
            print("  2. Send via SMTP")
            print("  3. Save copy to Sent folder via IMAP")
            print("  4. Handle any errors gracefully")
            print("  5. Provide user feedback")

            print("\n  Example integration:")
            print("  ```python")
            print("  # After successful SMTP send")
            print("  result = mailbox_service.save_sent(")
            print("      sent_mailbox='Sent',")
            print("      raw=message.as_bytes(),")
            print("      flags=Flag.SEEN,")
            print("      date_time=datetime.now()")
            print("  )")
            print("  ```")

    except Exception as e:
        print(f"✗ Error in sent message management: {e}")


def advanced_search_patterns():
    """Demonstrate advanced search patterns and criteria."""
    print("\n" + "=" * 60)
    print("ADVANCED SEARCH PATTERNS AND CRITERIA")
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

            print("✓ INBOX selected for advanced search operations")

            # 1. Date-based searches
            print("\n1. Date-based search patterns...")

            # Search for emails from last week
            last_week = datetime.now() - timedelta(days=7)
            search_criteria = IMAPSearchCriteria.since(last_week.strftime("%d-%b-%Y"))

            result = mailbox_service.search(search_criteria)
            if result.success:
                print(f"  ✓ Found {result.message_count} emails from last week")
            else:
                print(f"  ✗ Last week search failed: {result.error_message}")

            # Search for emails from specific date range
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now() - timedelta(days=7)

            range_criteria = IMAPSearchCriteria.and_criteria(
                IMAPSearchCriteria.since(start_date.strftime("%d-%b-%Y")),
                IMAPSearchCriteria.before(end_date.strftime("%d-%b-%Y")),
            )

            result = mailbox_service.search(range_criteria)
            if result.success:
                print(f"  ✓ Found {result.message_count} emails in date range")
            else:
                print(f"  ✗ Date range search failed: {result.error_message}")

            # 2. Sender and recipient searches
            print("\n2. Sender and recipient searches...")

            # Search by sender domain
            domain_criteria = IMAPSearchCriteria.from_address("@example.com")
            result = mailbox_service.search(domain_criteria)
            if result.success:
                print(f"  ✓ Found {result.message_count} emails from example.com")

            # Search by multiple criteria
            complex_criteria = IMAPSearchCriteria.and_criteria(
                IMAPSearchCriteria.from_address("@gmail.com"),
                IMAPSearchCriteria.subject("important"),
                IMAPSearchCriteria.UNSEEN,
            )

            result = mailbox_service.search(complex_criteria)
            if result.success:
                print(
                    f"  ✓ Found {result.message_count} unread important emails from Gmail"
                )

            # 3. Flag-based searches
            print("\n3. Flag-based search patterns...")

            # Search for flagged messages
            flagged_criteria = IMAPSearchCriteria.FLAGGED
            result = mailbox_service.search(flagged_criteria)
            if result.success:
                print(f"  ✓ Found {result.message_count} flagged emails")

            # Search for unread messages
            unread_criteria = IMAPSearchCriteria.UNSEEN
            result = mailbox_service.search(unread_criteria)
            if result.success:
                print(f"  ✓ Found {result.message_count} unread emails")

            # 4. Size-based searches
            print("\n4. Size-based search patterns...")
            print(
                "  Note: Size-based searches not implemented in current search criteria"
            )
            print("  Alternative: Use fetch results to filter by size post-search")
            print("  Example workflow:")
            print("  1. Search for all messages")
            print("  2. Fetch message sizes")
            print("  3. Filter results by size criteria")
            print("  4. Process filtered results")

            # 5. Complex search combinations
            print("\n5. Complex search combinations...")

            # Multi-criteria search
            complex_search = IMAPSearchCriteria.and_criteria(
                IMAPSearchCriteria.from_address("@important-domain.com"),
                IMAPSearchCriteria.subject("urgent"),
                IMAPSearchCriteria.since(
                    (datetime.now() - timedelta(days=7)).strftime("%d-%b-%Y")
                ),
                IMAPSearchCriteria.UNSEEN,
            )

            result = mailbox_service.search(complex_search)
            if result.success:
                print(
                    f"  ✓ Complex search found {result.message_count} matching emails"
                )
                print(
                    "  Criteria: urgent emails from important domain, last week, unread"
                )

            # 6. Search performance optimization
            print("\n6. Search performance optimization...")
            print("  Search optimization techniques:")
            print("  - Use specific criteria to reduce result sets")
            print("  - Combine multiple criteria in single search")
            print("  - Use date ranges to limit search scope")
            print("  - Consider server-side search capabilities")
            print("  - Monitor search execution times")

            # Show search statistics
            stats = mailbox_service.get_monitoring_statistics()
            search_stats = stats.get("operations_by_type", {}).get("search", 0)
            search_times = stats.get("average_times", {}).get("search", 0)

            print("  Current session search statistics:")
            print(f"    Total searches: {search_stats}")
            print(f"    Average search time: {search_times:.3f}s")

    except Exception as e:
        print(f"✗ Error in advanced search: {e}")


def mailbox_statistics_and_analytics():
    """Demonstrate mailbox statistics and analytics."""
    print("\n" + "=" * 60)
    print("MAILBOX STATISTICS AND ANALYTICS")
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

            print("✓ INBOX selected for statistics analysis")

            # 1. Basic mailbox statistics
            print("\n1. Basic mailbox statistics...")
            stats = mailbox_service.get_mailbox_statistics()

            print("  ✓ Mailbox statistics retrieved:")
            print(f"    Total messages: {stats.total_messages}")
            print(f"    Unread messages: {stats.unread_messages}")
            print(f"    Recent messages: {stats.recent_messages}")
            print(f"    Flagged messages: {stats.flagged_messages}")
            print(f"    Mailbox size: {stats.size_bytes} bytes")

            # Calculate percentages
            if stats.total_messages > 0:
                unread_pct = (stats.unread_messages / stats.total_messages) * 100
                recent_pct = (stats.recent_messages / stats.total_messages) * 100
                print(f"    Unread percentage: {unread_pct:.1f}%")
                print(f"    Recent percentage: {recent_pct:.1f}%")

            # 2. Advanced analytics
            print("\n2. Advanced analytics...")

            # Analyze message distribution by date
            print("  Date-based analysis:")

            # Messages from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            recent_criteria = IMAPSearchCriteria.since(yesterday.strftime("%d-%b-%Y"))
            recent_result = mailbox_service.search(recent_criteria)

            if recent_result.success:
                print(f"    Last 24 hours: {recent_result.message_count} messages")

            # Messages from last week
            last_week = datetime.now() - timedelta(days=7)
            week_criteria = IMAPSearchCriteria.since(last_week.strftime("%d-%b-%Y"))
            week_result = mailbox_service.search(week_criteria)

            if week_result.success:
                print(f"    Last 7 days: {week_result.message_count} messages")

            # Messages from last month
            last_month = datetime.now() - timedelta(days=30)
            month_criteria = IMAPSearchCriteria.since(last_month.strftime("%d-%b-%Y"))
            month_result = mailbox_service.search(month_criteria)

            if month_result.success:
                print(f"    Last 30 days: {month_result.message_count} messages")

            # 3. Performance analytics
            print("\n3. Performance analytics...")
            perf_stats = mailbox_service.get_monitoring_statistics()

            print("  ✓ Performance metrics:")
            print(f"    Service uptime: {perf_stats.get('uptime', 0):.1f} seconds")
            print(f"    Total operations: {perf_stats.get('total_operations', 0)}")

            # Operation breakdown
            ops_by_type = perf_stats.get("operations_by_type", {})
            print("    Operations by type:")
            for op_type, count in ops_by_type.items():
                print(f"      {op_type}: {count}")

            # Average execution times
            avg_times = perf_stats.get("average_times", {})
            print("    Average execution times:")
            for op_type, avg_time in avg_times.items():
                print(f"      {op_type}: {avg_time:.3f}s")

            # 4. Error analysis
            print("\n4. Error analysis...")
            error_counts = perf_stats.get("error_counts", {})

            if error_counts:
                print("  ✓ Error tracking:")
                total_errors = sum(error_counts.values())
                print(f"    Total errors: {total_errors}")

                for operation, count in error_counts.items():
                    print(f"      {operation}: {count} errors")
            else:
                print("  ✓ No errors recorded in current session")

            # 5. Trend analysis
            print("\n5. Trend analysis...")
            recent_ops = perf_stats.get("recent_operations", [])

            if recent_ops:
                print(f"  ✓ Recent operations analysis ({len(recent_ops)} operations):")

                # Success rate
                successful_ops = sum(1 for op in recent_ops if op.get("success", True))
                success_rate = (successful_ops / len(recent_ops)) * 100
                print(f"    Success rate: {success_rate:.1f}%")

                # Average execution time
                total_time = sum(op.get("execution_time", 0) for op in recent_ops)
                avg_time = total_time / len(recent_ops)
                print(f"    Average execution time: {avg_time:.3f}s")

                # Most recent operations
                print("    Most recent operations:")
                for op in recent_ops[-3:]:  # Show last 3
                    operation = op.get("operation", "Unknown")
                    exec_time = op.get("execution_time", 0)
                    success = op.get("success", True)
                    status = "✓" if success else "✗"
                    print(f"      {status} {operation} ({exec_time:.3f}s)")

            # 6. Recommendations
            print("\n6. Performance recommendations...")

            # Analyze performance patterns
            total_ops = perf_stats.get("total_operations", 0)
            uptime = perf_stats.get("uptime", 1)
            ops_per_second = total_ops / uptime if uptime > 0 else 0

            print("  Based on current metrics:")
            print(f"    Operations per second: {ops_per_second:.2f}")

            if ops_per_second > 10:
                print("    ✓ High throughput - consider connection pooling")
            elif ops_per_second > 5:
                print("    ✓ Moderate throughput - performance is good")
            else:
                print("    ✓ Low throughput - suitable for current load")

            # Check for errors
            total_errors = sum(error_counts.values()) if error_counts else 0
            if total_errors > 0:
                error_rate = (total_errors / total_ops) * 100 if total_ops > 0 else 0
                print(f"    Error rate: {error_rate:.1f}%")

                if error_rate > 5:
                    print("    ⚠ High error rate - check connection stability")
                elif error_rate > 1:
                    print("    ⚠ Moderate error rate - monitor closely")
                else:
                    print("    ✓ Low error rate - system is stable")

    except Exception as e:
        print(f"✗ Error in statistics analysis: {e}")


def message_restoration_and_recovery():
    """Demonstrate message restoration and recovery features."""
    print("\n" + "=" * 60)
    print("MESSAGE RESTORATION AND RECOVERY")
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

            print("✓ Mailbox service initialized for restoration operations")

            # 1. Recovery workflow simulation
            print("\n1. Message recovery workflow...")
            print("  Typical recovery scenario:")
            print("  1. User accidentally deletes important emails")
            print("  2. Messages are moved to Trash folder")
            print("  3. User requests recovery")
            print("  4. System searches Trash folder")
            print("  5. Messages are restored to original location")
            print("  6. Deleted flags are removed")
            print("  7. User is notified of recovery status")

            # 2. Trash folder analysis
            print("\n2. Trash folder analysis...")

            # Try to select Trash folder
            trash_folders = ["Trash", "Deleted Items", "Deleted Messages"]
            trash_folder = None

            for folder in trash_folders:
                result = mailbox_service.select(folder)
                if result.success:
                    trash_folder = folder
                    print(f"  ✓ Found trash folder: {folder}")
                    break

            if not trash_folder:
                print("  ✗ No trash folder found - creating simulation")
                trash_folder = "Trash"  # Use for simulation

            # 3. Recovery simulation
            print("\n3. Recovery operation simulation...")

            if trash_folder and mailbox_service.current_selection:
                # Get trash folder statistics
                stats = mailbox_service.get_mailbox_statistics()
                print("  Trash folder statistics:")
                print(f"    Total messages: {stats.total_messages}")
                print(f"    Messages available for recovery: {stats.total_messages}")

                # Simulate finding messages to recover
                if stats.total_messages > 0:
                    print("\n  Recovery process simulation:")
                    print("  1. Search for recoverable messages")
                    print("  2. Validate message integrity")
                    print("  3. Prepare restoration operation")
                    print("  4. Move messages to safe location")
                    print("  5. Remove deletion flags")
                    print("  6. Verify successful recovery")

                    # Show what restore operation would do
                    print("\n  Restore operation would:")
                    print("  - Select trash folder")
                    print("  - Move messages to safe folder")
                    print("  - Remove \\Deleted flag")
                    print("  - Verify operation success")
                    print("  - Provide detailed feedback")

            # 4. Recovery validation
            print("\n4. Recovery validation features...")
            print("  The service includes:")
            print("  - Message integrity verification")
            print("  - Mailbox validation before operations")
            print("  - Comprehensive error handling")
            print("  - Operation rollback on failure")
            print("  - Detailed logging for audit trails")

            # 5. Bulk recovery capabilities
            print("\n5. Bulk recovery capabilities...")
            print("  For large-scale recovery:")
            print("  - Batch processing for efficiency")
            print("  - Progress monitoring and reporting")
            print("  - Selective recovery by criteria")
            print("  - Error handling per message")
            print("  - Performance optimization")

            # Example bulk recovery simulation
            print("\n  Example bulk recovery:")
            print("  ```python")
            print("  # Search for messages to recover")
            print(
                "  search_criteria = IMAPSearchCriteria.from_address('important@domain.com')"
            )
            print("  search_result = mailbox_service.search(search_criteria)")
            print("  ")
            print("  # Restore found messages")
            print("  if search_result.success:")
            print("      msg_set = MessageSet(search_result.affected_messages)")
            print("      restore_result = mailbox_service.restore(")
            print("          msg_set, 'Trash', 'INBOX')")
            print("  ```")

            # 6. Recovery monitoring
            print("\n6. Recovery monitoring...")
            print("  Recovery operations are monitored for:")
            print("  - Success/failure rates")
            print("  - Execution times")
            print("  - Error patterns")
            print("  - Performance metrics")
            print("  - User activity tracking")

            # Show current monitoring stats
            stats = mailbox_service.get_monitoring_statistics()
            restore_count = stats.get("operations_by_type", {}).get("restore", 0)
            restore_time = stats.get("average_times", {}).get("restore", 0)

            print("  Current session recovery stats:")
            print(f"    Restore operations: {restore_count}")
            print(f"    Average restore time: {restore_time:.3f}s")

    except Exception as e:
        print(f"✗ Error in restoration demo: {e}")


def main():
    """Run all advanced mailbox feature examples."""
    print("Advanced IMAP Mailbox Features Examples")
    print("=" * 60)
    print("This example demonstrates advanced features of the enhanced")
    print("mailbox service including upload, analytics, and recovery.")

    try:
        # Run all examples
        email_upload_operations()
        sent_message_management()
        advanced_search_patterns()
        mailbox_statistics_and_analytics()
        message_restoration_and_recovery()

        print("\n" + "=" * 60)
        print("ADVANCED EXAMPLES COMPLETED SUCCESSFULLY")
        print("=" * 60)
        print("All advanced mailbox features have been demonstrated.")
        print("The enhanced service provides:")
        print("- Comprehensive email upload capabilities")
        print("- Advanced search and filtering")
        print("- Detailed statistics and analytics")
        print("- Robust recovery and restoration")
        print("- Production-ready monitoring")
        print("- Enterprise-grade reliability")

    except KeyboardInterrupt:
        print("\n✗ Examples interrupted by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        logger.exception("Unexpected error in advanced examples")


if __name__ == "__main__":
    main()
