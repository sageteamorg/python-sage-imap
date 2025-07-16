import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import os

from sage_imap.models.email import EmailMessage, EmailIterator, Attachment
from sage_imap.helpers.enums import Flag
from sage_imap.helpers.typings import EmailAddress


class TestEnhancedEmailMessage:
    """Test the enhanced EmailMessage class."""
    
    def test_attachment_validation(self):
        """Test attachment validation and sanitization."""
        # Test valid attachment
        attachment = Attachment(
            filename="test.pdf",
            content_type="application/pdf",
            payload=b"test content"
        )
        assert attachment.filename == "test.pdf"
        assert attachment.size == 12
        assert not attachment.is_image
        assert not attachment.is_text
        
        # Test filename sanitization
        attachment = Attachment(
            filename="../../../etc/passwd",
            content_type="text/plain",
            payload=b"malicious content"
        )
        assert attachment.filename == "passwd"
        
        # Test dangerous characters removal
        attachment = Attachment(
            filename="file<>:\"/\\|?*.txt",
            content_type="text/plain",
            payload=b"content"
        )
        assert attachment.filename == "file_________.txt"
    
    def test_attachment_save_to_file(self):
        """Test attachment save functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            attachment = Attachment(
                filename="test.txt",
                content_type="text/plain",
                payload=b"test content"
            )
            
            saved_path = attachment.save_to_file(temp_dir)
            assert saved_path.exists()
            assert saved_path.read_bytes() == b"test content"
            
            # Test filename conflict handling
            saved_path2 = attachment.save_to_file(temp_dir)
            assert saved_path2.name == "test_1.txt"
    
    def test_email_validation(self):
        """Test email validation and error handling."""
        # Test empty bytes
        with pytest.raises(ValueError, match="Email bytes cannot be empty"):
            EmailMessage.read_from_eml_bytes(b"")
        
        # Test file not found
        with pytest.raises(FileNotFoundError):
            EmailMessage.read_from_eml_file("nonexistent.eml")
    
    def test_safe_header_decode(self):
        """Test safe header decoding."""
        email = EmailMessage(message_id="test")
        
        # Test normal header
        result = email._safe_header_decode("Normal Subject")
        assert result == "Normal Subject"
        
        # Test encoded header
        result = email._safe_header_decode("=?utf-8?B?VGVzdCBTdWJqZWN0?=")
        assert result == "Test Subject"
        
        # Test invalid encoding
        result = email._safe_header_decode("Invalid\x80Header")
        assert "Invalid" in result
    
    def test_email_address_parsing(self):
        """Test email address parsing with validation."""
        email = EmailMessage(message_id="test")
        
        # Test valid address
        addr = email._parse_email_address("test@example.com")
        assert addr is not None
        
        # Test empty address
        addr = email._parse_email_address("")
        assert addr is None
    
    def test_message_id_sanitization(self):
        """Test message ID sanitization."""
        email = EmailMessage(message_id="test")
        
        # Test normal message ID
        result = email.sanitize_message_id("<test@example.com>")
        assert result == "<test@example.com>"
        
        # Test message ID without brackets
        result = email.sanitize_message_id("test@example.com")
        assert result == "<test@example.com>"
        
        # Test invalid message ID
        result = email.sanitize_message_id("invalid")
        assert result is None
    
    def test_cached_properties(self):
        """Test cached properties for performance."""
        email = EmailMessage(
            message_id="test",
            raw=b"test email content",
            to_address=[EmailAddress("to@example.com")],
            cc_address=[EmailAddress("cc@example.com")],
            attachments=[
                Attachment("test.txt", "text/plain", b"content1"),
                Attachment("test2.txt", "text/plain", b"content2")
            ]
        )
        
        # Test content hash
        hash1 = email.content_hash
        hash2 = email.content_hash
        assert hash1 == hash2  # Should be cached
        
        # Test all recipients
        recipients = email.all_recipients
        assert len(recipients) == 2
        
        # Test total attachment size
        total_size = email.total_attachment_size
        assert total_size == 16  # 8 + 8
    
    def test_utility_methods(self):
        """Test utility methods."""
        email = EmailMessage(
            message_id="test",
            subject="Re: Test Subject",
            plain_body="This is a test email",
            html_body="<p>This is a test email</p>",
            attachments=[
                Attachment("image.jpg", "image/jpeg", b"image data"),
                Attachment("doc.pdf", "application/pdf", b"pdf data")
            ]
        )
        
        # Test reply detection
        assert email.is_reply()
        assert not email.is_forward()
        
        # Test body checks
        assert email.has_plain_body()
        assert email.has_html_body()
        
        # Test body preview
        preview = email.get_body_preview(10)
        assert len(preview) <= 13  # 10 + "..."
        
        # Test attachment methods
        assert email.has_attachments()
        assert len(email.get_attachment_filenames()) == 2
        
        image_attachments = email.get_image_attachments()
        assert len(image_attachments) == 1
        assert image_attachments[0].filename == "image.jpg"
    
    def test_to_dict_conversion(self):
        """Test dictionary conversion."""
        email = EmailMessage(
            message_id="<test@example.com>",
            subject="Test Subject",
            from_address=EmailAddress("from@example.com"),
            size=1024
        )
        
        result = email.to_dict()
        assert result['message_id'] == "<test@example.com>"
        assert result['subject'] == "Test Subject"
        assert result['from_address'] == "from@example.com"
        assert result['size'] == 1024
        assert 'content_hash' in result


class TestEnhancedEmailIterator:
    """Test the enhanced EmailIterator class."""
    
    @pytest.fixture
    def sample_emails(self):
        """Create sample emails for testing."""
        return [
            EmailMessage(
                message_id="<1@example.com>",
                subject="First Email",
                from_address=EmailAddress("sender1@example.com"),
                to_address=[EmailAddress("recipient@example.com")],
                size=100,
                date="2023-01-01T10:00:00",
                plain_body="First email content",
                attachments=[Attachment("file1.txt", "text/plain", b"content1")]
            ),
            EmailMessage(
                message_id="<2@example.com>",
                subject="Second Email",
                from_address=EmailAddress("sender2@example.com"),
                to_address=[EmailAddress("recipient@example.com")],
                size=200,
                date="2023-01-02T10:00:00",
                plain_body="Second email content",
                attachments=[]
            ),
            EmailMessage(
                message_id="<3@example.com>",
                subject="Re: First Email",
                from_address=EmailAddress("sender1@example.com"),
                to_address=[EmailAddress("recipient@example.com")],
                size=150,
                date="2023-01-03T10:00:00",
                plain_body="Reply to first email",
                attachments=[
                    Attachment("image.jpg", "image/jpeg", b"image data"),
                    Attachment("doc.pdf", "application/pdf", b"pdf data")
                ]
            )
        ]
    
    def test_basic_functionality(self, sample_emails):
        """Test basic iterator functionality."""
        iterator = EmailIterator(sample_emails)
        
        # Test length
        assert len(iterator) == 3
        
        # Test boolean conversion
        assert bool(iterator)
        
        # Test iteration
        emails = list(iterator)
        assert len(emails) == 3
        
        # Test indexing
        assert iterator[0].subject == "First Email"
        assert iterator[1].subject == "Second Email"
        
        # Test slicing
        sliced = iterator[1:3]
        assert len(sliced) == 2
        assert sliced[0].subject == "Second Email"
    
    def test_filtering_methods(self, sample_emails):
        """Test various filtering methods."""
        iterator = EmailIterator(sample_emails)
        
        # Test filter by sender
        sender1_emails = iterator.filter_by_sender("sender1@example.com")
        assert len(sender1_emails) == 2
        
        # Test filter by subject part
        first_emails = iterator.filter_by_subject_part("First")
        assert len(first_emails) == 2  # "First Email" and "Re: First Email"
        
        # Test filter by date range
        start_date = datetime(2023, 1, 2)
        end_date = datetime(2023, 1, 3)
        date_filtered = iterator.filter_by_date_range(start_date, end_date)
        assert len(date_filtered) == 1
        
        # Test filter by size range
        size_filtered = iterator.filter_by_size_range(min_size=150)
        assert len(size_filtered) == 2
        
        # Test filter by attachments
        with_attachments = iterator.filter_by_attachment()
        assert len(with_attachments) == 2
        
        without_attachments = iterator.filter_without_attachment()
        assert len(without_attachments) == 1
        
        # Test filter by attachment count
        multiple_attachments = iterator.filter_by_attachment_count(min_count=2)
        assert len(multiple_attachments) == 1
        
        # Test filter by content type
        image_emails = iterator.filter_by_content_type("image/")
        assert len(image_emails) == 1
        
        # Test filter by body content
        content_filtered = iterator.filter_by_body_content("first", case_sensitive=False)
        assert len(content_filtered) == 2
    
    def test_sorting_methods(self, sample_emails):
        """Test sorting methods."""
        iterator = EmailIterator(sample_emails)
        
        # Test sort by date
        sorted_by_date = iterator.sort_by_date()
        dates = [email.date for email in sorted_by_date]
        assert dates == sorted(dates)
        
        # Test sort by size
        sorted_by_size = iterator.sort_by_size()
        sizes = [email.size for email in sorted_by_size]
        assert sizes == sorted(sizes)
        
        # Test sort by subject
        sorted_by_subject = iterator.sort_by_subject()
        subjects = [email.subject for email in sorted_by_subject]
        assert subjects == sorted(subjects, key=str.lower)
        
        # Test sort by attachment count
        sorted_by_attachments = iterator.sort_by_attachment_count()
        attachment_counts = [len(email.attachments) for email in sorted_by_attachments]
        assert attachment_counts == sorted(attachment_counts)
    
    def test_grouping_methods(self, sample_emails):
        """Test grouping methods."""
        iterator = EmailIterator(sample_emails)
        
        # Test group by sender
        grouped_by_sender = iterator.group_by_sender()
        assert len(grouped_by_sender) == 2
        assert len(grouped_by_sender["sender1@example.com"]) == 2
        assert len(grouped_by_sender["sender2@example.com"]) == 1
        
        # Test group by date
        grouped_by_date = iterator.group_by_date()
        assert len(grouped_by_date) == 3
        assert len(grouped_by_date["2023-01-01"]) == 1
        assert len(grouped_by_date["2023-01-02"]) == 1
        assert len(grouped_by_date["2023-01-03"]) == 1
    
    def test_utility_methods(self, sample_emails):
        """Test utility methods."""
        iterator = EmailIterator(sample_emails)
        
        # Test get unique senders
        senders = iterator.get_unique_senders()
        assert len(senders) == 2
        assert "sender1@example.com" in senders
        assert "sender2@example.com" in senders
        
        # Test get unique recipients
        recipients = iterator.get_unique_recipients()
        assert len(recipients) == 1
        assert "recipient@example.com" in recipients
        
        # Test get date range
        date_range = iterator.get_date_range()
        assert date_range[0] == "2023-01-01T10:00:00"
        assert date_range[1] == "2023-01-03T10:00:00"
        
        # Test get total size
        total_size = iterator.get_total_size()
        assert total_size == 450  # 100 + 200 + 150
        
        # Test pagination
        page1 = iterator.page(1, 2)
        assert len(page1) == 2
        
        page2 = iterator.page(2, 2)
        assert len(page2) == 1
        
        # Test take and skip
        first_two = iterator.take(2)
        assert len(first_two) == 2
        
        last_two = iterator.skip(1)
        assert len(last_two) == 2
    
    def test_statistics(self, sample_emails):
        """Test statistics generation."""
        iterator = EmailIterator(sample_emails)
        stats = iterator.get_statistics()
        
        assert stats['total_emails'] == 3
        assert stats['total_size'] == 450
        assert stats['unique_senders'] == 2
        assert stats['unique_recipients'] == 1
        assert stats['emails_with_attachments'] == 2
        assert stats['average_size'] == 150
        assert stats['date_range'] == ("2023-01-01T10:00:00", "2023-01-03T10:00:00")
    
    def test_chaining_and_deduplication(self, sample_emails):
        """Test chaining and deduplication."""
        iterator1 = EmailIterator(sample_emails[:2])
        iterator2 = EmailIterator(sample_emails[1:])
        
        # Test chaining
        chained = iterator1.chain(iterator2)
        assert len(chained) == 4  # 2 + 3 with one duplicate
        
        # Test deduplication
        deduplicated = chained.deduplicate(lambda email: email.message_id)
        assert len(deduplicated) == 3  # Duplicates removed
    
    def test_save_to_directory(self, sample_emails):
        """Test saving emails to directory."""
        iterator = EmailIterator(sample_emails)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock the raw content for emails
            for email in sample_emails:
                email.raw = f"Mock email content for {email.subject}".encode()
            
            saved_files = iterator.save_all_to_directory(temp_dir)
            assert len(saved_files) == 3
            
            # Check files exist
            for file_path in saved_files:
                assert file_path.exists()
                assert file_path.suffix == '.eml'
    
    def test_conversion_methods(self, sample_emails):
        """Test conversion methods."""
        iterator = EmailIterator(sample_emails)
        
        # Test to_list
        email_list = iterator.to_list()
        assert len(email_list) == 3
        assert all(isinstance(email, EmailMessage) for email in email_list)
        
        # Test to_dict_list
        dict_list = iterator.to_dict_list()
        assert len(dict_list) == 3
        assert all(isinstance(item, dict) for item in dict_list)
        assert all('message_id' in item for item in dict_list) 