#!/usr/bin/env python3
"""
Enhanced Email Processing Example

This script demonstrates the improved capabilities of the sage_imap library,
including better email parsing, filtering, sorting, and processing.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from sage_imap.services import IMAPClient, IMAPMailboxService
from sage_imap.models.email import EmailMessage, EmailIterator, Attachment
from sage_imap.helpers.enums import DefaultMailboxes, Flag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EnhancedEmailProcessor:
    """Enhanced email processor with advanced filtering and analysis capabilities."""
    
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
    
    def process_emails(self, mailbox: str = DefaultMailboxes.INBOX) -> None:
        """Process emails with enhanced capabilities."""
        try:
            with IMAPClient(self.host, self.username, self.password) as client:
                with IMAPMailboxService(client) as mailbox_service:
                    # Select mailbox
                    mailbox_service.select(mailbox)
                    
                    # Get all emails (this would be replaced with actual email fetching)
                    emails = self._get_sample_emails()
                    email_iterator = EmailIterator(emails)
                    
                    # Demonstrate enhanced capabilities
                    self._demonstrate_filtering(email_iterator)
                    self._demonstrate_sorting(email_iterator)
                    self._demonstrate_grouping(email_iterator)
                    self._demonstrate_statistics(email_iterator)
                    self._demonstrate_attachment_processing(email_iterator)
                    self._demonstrate_advanced_features(email_iterator)
                    
        except Exception as e:
            logger.error(f"Error processing emails: {e}")
    
    def _get_sample_emails(self) -> List[EmailMessage]:
        """Create sample emails for demonstration."""
        return [
            EmailMessage(
                message_id="<1@example.com>",
                subject="Project Update - Q1 Results",
                from_address="manager@company.com",
                to_address=["team@company.com"],
                cc_address=["stakeholder@company.com"],
                date=(datetime.now() - timedelta(days=1)).isoformat(),
                plain_body="Please find the Q1 results attached.",
                html_body="<p>Please find the Q1 results attached.</p>",
                size=2048,
                attachments=[
                    Attachment("Q1_Report.pdf", "application/pdf", b"PDF content here"),
                    Attachment("data.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", b"Excel data")
                ],
                flags=[Flag.SEEN, Flag.FLAGGED]
            ),
            EmailMessage(
                message_id="<2@example.com>",
                subject="Re: Project Update - Q1 Results",
                from_address="team@company.com",
                to_address=["manager@company.com"],
                date=(datetime.now() - timedelta(hours=12)).isoformat(),
                plain_body="Thanks for the update. The results look great!",
                size=512,
                attachments=[],
                flags=[Flag.SEEN, Flag.ANSWERED]
            ),
            EmailMessage(
                message_id="<3@example.com>",
                subject="Meeting Invitation - Strategy Discussion",
                from_address="ceo@company.com",
                to_address=["manager@company.com", "team@company.com"],
                date=(datetime.now() - timedelta(hours=6)).isoformat(),
                plain_body="Let's discuss the strategy for Q2.",
                html_body="<p>Let's discuss the strategy for Q2.</p>",
                size=1024,
                attachments=[
                    Attachment("agenda.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", b"Word document")
                ],
                flags=[Flag.SEEN]
            ),
            EmailMessage(
                message_id="<4@example.com>",
                subject="Spam: Buy Now - Limited Time Offer!!!",
                from_address="spam@suspicious.com",
                to_address=["team@company.com"],
                date=(datetime.now() - timedelta(hours=2)).isoformat(),
                plain_body="Click here to buy our amazing product!",
                size=256,
                attachments=[],
                flags=[Flag.SEEN]
            ),
            EmailMessage(
                message_id="<5@example.com>",
                subject="System Alert - Server Maintenance",
                from_address="admin@company.com",
                to_address=["it@company.com"],
                cc_address=["manager@company.com"],
                date=datetime.now().isoformat(),
                plain_body="Scheduled maintenance tonight from 10 PM to 2 AM.",
                size=768,
                attachments=[
                    Attachment("maintenance_plan.pdf", "application/pdf", b"Maintenance plan PDF"),
                    Attachment("backup_log.txt", "text/plain", b"Backup log content")
                ],
                flags=[Flag.RECENT]
            )
        ]
    
    def _demonstrate_filtering(self, emails: EmailIterator) -> None:
        """Demonstrate advanced filtering capabilities."""
        print("\n" + "="*60)
        print("ADVANCED FILTERING DEMONSTRATION")
        print("="*60)
        
        # Filter by sender domain
        company_emails = emails.filter_by_sender("@company.com")
        print(f"Emails from company domain: {len(company_emails)}")
        
        # Filter by subject keywords
        project_emails = emails.filter_by_subject_part("Project", case_sensitive=False)
        print(f"Project-related emails: {len(project_emails)}")
        
        # Filter by date range (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_emails = emails.filter_by_date_range(start_date=yesterday)
        print(f"Emails from last 24 hours: {len(recent_emails)}")
        
        # Filter by size range
        large_emails = emails.filter_by_size_range(min_size=1000)
        print(f"Large emails (>1KB): {len(large_emails)}")
        
        # Filter emails with attachments
        emails_with_attachments = emails.filter_by_attachment()
        print(f"Emails with attachments: {len(emails_with_attachments)}")
        
        # Filter by attachment type
        pdf_emails = emails.filter_by_content_type("application/pdf")
        print(f"Emails with PDF attachments: {len(pdf_emails)}")
        
        # Filter by flags
        important_emails = emails.filter_by_flags([Flag.FLAGGED])
        print(f"Flagged emails: {len(important_emails)}")
        
        # Filter by body content
        meeting_emails = emails.filter_by_body_content("meeting", case_sensitive=False)
        print(f"Emails mentioning 'meeting': {len(meeting_emails)}")
        
        # Complex filtering - Recent important emails with attachments
        complex_filter = (emails
                         .filter_by_date_range(start_date=yesterday)
                         .filter_by_attachment()
                         .filter_by_flags([Flag.FLAGGED]))
        print(f"Recent important emails with attachments: {len(complex_filter)}")
    
    def _demonstrate_sorting(self, emails: EmailIterator) -> None:
        """Demonstrate sorting capabilities."""
        print("\n" + "="*60)
        print("SORTING DEMONSTRATION")
        print("="*60)
        
        # Sort by date (newest first)
        sorted_by_date = emails.sort_by_date(ascending=False)
        print("Emails sorted by date (newest first):")
        for email in sorted_by_date.take(3):
            print(f"  - {email.subject} ({email.date})")
        
        # Sort by size (largest first)
        sorted_by_size = emails.sort_by_size(ascending=False)
        print("\nEmails sorted by size (largest first):")
        for email in sorted_by_size.take(3):
            print(f"  - {email.subject} ({email.size} bytes)")
        
        # Sort by sender
        sorted_by_sender = emails.sort_by_sender()
        print("\nEmails sorted by sender:")
        for email in sorted_by_sender.take(3):
            print(f"  - {email.subject} (from: {email.from_address})")
        
        # Sort by attachment count
        sorted_by_attachments = emails.sort_by_attachment_count(ascending=False)
        print("\nEmails sorted by attachment count:")
        for email in sorted_by_attachments.take(3):
            print(f"  - {email.subject} ({len(email.attachments)} attachments)")
    
    def _demonstrate_grouping(self, emails: EmailIterator) -> None:
        """Demonstrate grouping capabilities."""
        print("\n" + "="*60)
        print("GROUPING DEMONSTRATION")
        print("="*60)
        
        # Group by sender
        grouped_by_sender = emails.group_by_sender()
        print("Emails grouped by sender:")
        for sender, sender_emails in grouped_by_sender.items():
            print(f"  - {sender}: {len(sender_emails)} emails")
        
        # Group by date
        grouped_by_date = emails.group_by_date("%Y-%m-%d")
        print("\nEmails grouped by date:")
        for date, date_emails in grouped_by_date.items():
            print(f"  - {date}: {len(date_emails)} emails")
    
    def _demonstrate_statistics(self, emails: EmailIterator) -> None:
        """Demonstrate statistics generation."""
        print("\n" + "="*60)
        print("STATISTICS DEMONSTRATION")
        print("="*60)
        
        stats = emails.get_statistics()
        print(f"Total emails: {stats['total_emails']}")
        print(f"Total size: {stats['total_size']} bytes")
        print(f"Average size: {stats['average_size']:.1f} bytes")
        print(f"Unique senders: {stats['unique_senders']}")
        print(f"Unique recipients: {stats['unique_recipients']}")
        print(f"Emails with attachments: {stats['emails_with_attachments']}")
        print(f"Total attachment size: {stats['total_attachment_size']} bytes")
        print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}")
        
        # Flag distribution
        print("\nFlag distribution:")
        for flag, count in stats['flag_distribution'].items():
            print(f"  - {flag}: {count}")
        
        # Content type distribution
        print("\nAttachment content types:")
        for content_type, count in stats['content_type_distribution'].items():
            print(f"  - {content_type}: {count}")
    
    def _demonstrate_attachment_processing(self, emails: EmailIterator) -> None:
        """Demonstrate enhanced attachment processing."""
        print("\n" + "="*60)
        print("ATTACHMENT PROCESSING DEMONSTRATION")
        print("="*60)
        
        # Find emails with attachments
        emails_with_attachments = emails.filter_by_attachment()
        print(f"Processing {len(emails_with_attachments)} emails with attachments:")
        
        for email in emails_with_attachments:
            print(f"\nEmail: {email.subject}")
            print(f"  Total attachment size: {email.total_attachment_size} bytes")
            
            for attachment in email.attachments:
                print(f"  - {attachment.filename} ({attachment.content_type}, {attachment.size} bytes)")
                print(f"    Is image: {attachment.is_image}")
                print(f"    Is text: {attachment.is_text}")
                
                # Demonstrate safe filename handling
                print(f"    Sanitized filename: {attachment.filename}")
        
        # Get all image attachments
        image_emails = emails.filter_by_content_type("image/")
        print(f"\nEmails with image attachments: {len(image_emails)}")
        
        # Get all PDF attachments
        pdf_emails = emails.filter_by_content_type("application/pdf")
        print(f"Emails with PDF attachments: {len(pdf_emails)}")
    
    def _demonstrate_advanced_features(self, emails: EmailIterator) -> None:
        """Demonstrate advanced features."""
        print("\n" + "="*60)
        print("ADVANCED FEATURES DEMONSTRATION")
        print("="*60)
        
        # Pagination
        print("Pagination example (page 1, 2 emails per page):")
        page1 = emails.page(1, 2)
        for email in page1:
            print(f"  - {email.subject}")
        
        # Chaining iterators
        important_emails = emails.filter_by_flags([Flag.FLAGGED])
        recent_emails = emails.filter_by_date_range(start_date=datetime.now() - timedelta(hours=24))
        combined = important_emails.chain(recent_emails)
        print(f"\nCombined important and recent emails: {len(combined)}")
        
        # Deduplication
        deduplicated = combined.deduplicate()
        print(f"After deduplication: {len(deduplicated)}")
        
        # Email analysis
        print("\nEmail analysis:")
        for email in emails.take(3):
            print(f"  - {email.subject}")
            print(f"    Reply: {email.is_reply()}")
            print(f"    Forward: {email.is_forward()}")
            print(f"    Has HTML: {email.has_html_body()}")
            print(f"    Has plain text: {email.has_plain_body()}")
            print(f"    Preview: {email.get_body_preview(50)}")
        
        # Unique senders and recipients
        print(f"\nUnique senders: {', '.join(emails.get_unique_senders())}")
        print(f"Unique recipients: {', '.join(emails.get_unique_recipients())}")
        
        # Date range analysis
        date_range = emails.get_date_range()
        print(f"Email date range: {date_range[0]} to {date_range[1]}")


def main():
    """Main function to demonstrate enhanced email processing."""
    print("Enhanced Email Processing Demo")
    print("=" * 60)
    
    # Note: Replace with actual IMAP credentials
    # processor = EnhancedEmailProcessor(
    #     host="imap.gmail.com",
    #     username="your_email@gmail.com",
    #     password="your_app_password"
    # )
    
    # For demo purposes, we'll use sample data
    processor = EnhancedEmailProcessor("demo.host", "demo_user", "demo_pass")
    
    # Create sample emails and demonstrate features
    emails = processor._get_sample_emails()
    email_iterator = EmailIterator(emails)
    
    print(f"Processing {len(email_iterator)} sample emails...")
    
    # Demonstrate all features
    processor._demonstrate_filtering(email_iterator)
    processor._demonstrate_sorting(email_iterator)
    processor._demonstrate_grouping(email_iterator)
    processor._demonstrate_statistics(email_iterator)
    processor._demonstrate_attachment_processing(email_iterator)
    processor._demonstrate_advanced_features(email_iterator)
    
    print("\n" + "="*60)
    print("Demo completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main() 