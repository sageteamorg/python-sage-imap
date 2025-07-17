"""
Pytest configuration and fixtures for models tests.
"""
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock
from sage_imap.models.email import EmailMessage, Attachment
from sage_imap.models.message import MessageSet
from sage_imap.helpers.enums import Flag
from sage_imap.helpers.typings import EmailAddress, EmailDate


@pytest.fixture
def sample_email_raw():
    """Sample raw email content for testing."""
    return b"""From: sender@example.com
To: recipient@example.com
Subject: Test Subject
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <test-message-id@example.com>
Content-Type: text/plain; charset=utf-8

This is a test email body.
"""


@pytest.fixture
def sample_multipart_email_raw():
    """Sample multipart email content for testing."""
    return b"""From: sender@example.com
To: recipient@example.com
Subject: Test Multipart Subject
Date: Wed, 12 Oct 2022 14:30:00 +0000
Message-ID: <test-multipart-id@example.com>
Content-Type: multipart/mixed; boundary="----=_NextPart_000_0000_01D7E4B4.12345678"

This is a multi-part message in MIME format.

------=_NextPart_000_0000_01D7E4B4.12345678
Content-Type: text/plain; charset=utf-8

This is the plain text body.

------=_NextPart_000_0000_01D7E4B4.12345678
Content-Type: text/html; charset=utf-8

<html><body><p>This is the HTML body.</p></body></html>

------=_NextPart_000_0000_01D7E4B4.12345678
Content-Type: text/plain; charset=utf-8
Content-Disposition: attachment; filename="test.txt"

This is attachment content.

------=_NextPart_000_0000_01D7E4B4.12345678--
"""


@pytest.fixture
def sample_email_message():
    """Sample EmailMessage instance for testing."""
    return EmailMessage(
        message_id="<test-message-id@example.com>",
        subject="Test Subject",
        from_address=EmailAddress("sender@example.com"),
        to_address=[EmailAddress("recipient@example.com")],
        cc_address=[EmailAddress("cc@example.com")],
        date=EmailDate("2022-10-12T14:30:00"),
        plain_body="This is a test email body.",
        html_body="<p>This is a test email body.</p>",
        size=1024,
        uid=1001,
        sequence_number=1,
        flags=[Flag.SEEN]
    )


@pytest.fixture
def sample_attachment():
    """Sample Attachment instance for testing."""
    return Attachment(
        filename="test.txt",
        content_type="text/plain",
        payload=b"This is test attachment content.",
        id="att-001",
        content_id="<content-id@example.com>",
        content_transfer_encoding="base64"
    )


@pytest.fixture
def sample_message_set():
    """Sample MessageSet instance for testing."""
    return MessageSet.from_uids([1001, 1002, 1003], mailbox="INBOX")


@pytest.fixture
def sample_email_list():
    """Sample list of EmailMessage instances for testing."""
    return [
        EmailMessage(
            message_id="<msg-1@example.com>",
            subject="First Email",
            from_address=EmailAddress("sender1@example.com"),
            to_address=[EmailAddress("recipient1@example.com")],
            plain_body="First email body",
            size=100,
            uid=1001,
            sequence_number=1,
            flags=[Flag.SEEN]
        ),
        EmailMessage(
            message_id="<msg-2@example.com>",
            subject="Second Email",
            from_address=EmailAddress("sender2@example.com"),
            to_address=[EmailAddress("recipient2@example.com")],
            plain_body="Second email body",
            size=200,
            uid=1002,
            sequence_number=2,
            flags=[Flag.FLAGGED]
        ),
        EmailMessage(
            message_id="<msg-3@example.com>",
            subject="Third Email",
            from_address=EmailAddress("sender1@example.com"),
            to_address=[EmailAddress("recipient3@example.com")],
            plain_body="Third email body",
            size=150,
            uid=1003,
            sequence_number=3,
            flags=[Flag.SEEN, Flag.FLAGGED]
        )
    ]


@pytest.fixture
def temp_directory():
    """Temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_eml_file(sample_email_raw):
    """Temporary .eml file for testing."""
    with tempfile.NamedTemporaryFile(suffix=".eml", delete=False) as temp_file:
        temp_file.write(sample_email_raw)
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup
    try:
        os.unlink(temp_file_path)
    except FileNotFoundError:
        pass


@pytest.fixture
def mock_imap_message():
    """Mock IMAP message for testing email parsing."""
    mock_message = Mock()
    mock_message.is_multipart.return_value = False
    mock_message.get_content_type.return_value = "text/plain"
    mock_message.get.return_value = "Test Subject"
    mock_message.get_all.return_value = ["test@example.com"]
    mock_message.items.return_value = [("Subject", "Test Subject")]
    mock_message.walk.return_value = [mock_message]
    
    return mock_message


@pytest.fixture
def mock_email_message():
    """Mock EmailMessage for testing MessageSet creation."""
    mock_message = Mock()
    mock_message.uid = 1001
    mock_message.sequence_number = 1
    mock_message.mailbox = "INBOX"
    
    return mock_message


# Helper functions for tests
def create_test_email_with_attachments(num_attachments=2):
    """Create a test email with specified number of attachments."""
    attachments = []
    for i in range(num_attachments):
        attachment = Attachment(
            filename=f"attachment_{i+1}.txt",
            content_type="text/plain",
            payload=f"Attachment {i+1} content".encode()
        )
        attachments.append(attachment)
    
    return EmailMessage(
        message_id=f"<test-with-attachments@example.com>",
        subject="Email with Attachments",
        from_address=EmailAddress("sender@example.com"),
        to_address=[EmailAddress("recipient@example.com")],
        plain_body="Email body with attachments",
        attachments=attachments,
        size=1024,
        uid=2001,
        sequence_number=1
    )


def create_test_message_set_with_ranges():
    """Create a test MessageSet with ranges for testing."""
    return MessageSet("1,2,3,10:15,20:*", is_uid=True, mailbox="INBOX")


def create_test_message_set_from_list(ids, is_uid=True, mailbox="INBOX"):
    """Create a test MessageSet from list of IDs."""
    if is_uid:
        return MessageSet.from_uids(ids, mailbox)
    else:
        return MessageSet.from_sequence_numbers(ids, mailbox)


# Test markers
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.slow = pytest.mark.slow
pytest.mark.email = pytest.mark.email
pytest.mark.message_set = pytest.mark.message_set
pytest.mark.attachment = pytest.mark.attachment


# Test configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "email: mark test as email-related"
    )
    config.addinivalue_line(
        "markers", "message_set: mark test as message set-related"
    )
    config.addinivalue_line(
        "markers", "attachment: mark test as attachment-related"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify test items during collection."""
    for item in items:
        # Add markers based on test names
        if "test_email" in item.name:
            item.add_marker(pytest.mark.email)
        elif "test_message" in item.name:
            item.add_marker(pytest.mark.message_set)
        elif "test_attachment" in item.name:
            item.add_marker(pytest.mark.attachment)
        
        # Mark all tests as unit tests by default
        if not any(marker.name in ["integration", "slow"] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)


# Test setup and teardown
@pytest.fixture(autouse=True)
def setup_and_teardown():
    """Setup and teardown for each test."""
    # Setup
    yield
    # Teardown - nothing needed for these tests 