import pytest
import requests
import smtplib
from unittest.mock import patch, MagicMock
from sage_imap.exceptions import EmailException
from sage_imap.helpers.email import (
    AutoResponseSuppress,
    ContentTransferEncoding,
    ContentType,
    Priority,
    SpamResult,
)
from email.mime.multipart import MIMEMultipart
from sage_imap.services.email import SmartEmailMessage  # Correct import path

# Sample data for testing
sample_subject = "Test Subject"
sample_body = "Test Body"
sample_from_email = "test@example.com"
sample_to = ["recipient@example.com"]
sample_cc = ["cc@example.com"]
sample_bcc = ["bcc@example.com"]
sample_extra_headers = {"X-Test-Header": "HeaderValue"}
sample_attachments = ["tests/assets/test_attachment.txt"]

@pytest.fixture
def email_message():
    return SmartEmailMessage(
        subject=sample_subject,
        body=sample_body,
        from_email=sample_from_email,
        to=sample_to,
        cc=sample_cc,
        bcc=sample_bcc,
        extra_headers=sample_extra_headers,
        attachments=sample_attachments,
    )

def test_init(email_message):
    assert email_message.subject == sample_subject
    assert email_message.body == sample_body
    assert email_message.from_email == sample_from_email
    assert email_message.to == sample_to
    assert email_message.cc == sample_cc
    assert email_message.bcc == sample_bcc
    assert email_message.attachments == sample_attachments
    assert email_message.extra_headers["X-Test-Header"] == "HeaderValue"

@patch("sage_imap.services.email.requests.get")
def test_get_originating_ip(mock_get, email_message):
    mock_get.return_value.text = "8.8.8.8"
    ip = email_message._get_originating_ip()
    assert ip == "8.8.8.8"

@patch("sage_imap.services.email.requests.get")
def test_get_originating_ip_failure(mock_get, email_message):
    mock_get.side_effect = requests.RequestException()
    ip = email_message._get_originating_ip()
    assert ip == "127.0.0.1"

@patch("sage_imap.services.email.socket.getfqdn")
def test_generate_received_header(mock_getfqdn, email_message):
    mock_getfqdn.return_value = "localhost"
    header = email_message._generate_received_header()
    assert "localhost" in header

def test_update_attachment_status(email_message):
    email_message.update_attachment_status()
    assert email_message.has_attach == "yes"

def test_update_content_type_and_encoding_with_attachments(email_message):
    email_message.update_content_type_and_encoding()
    assert email_message.content_type == ContentType.MULTIPART.value
    assert email_message.content_transfer_encoding == ContentTransferEncoding.BASE64.value

def test_update_content_type_and_encoding_without_attachments():
    email_message = SmartEmailMessage(subject=sample_subject, body=sample_body)
    email_message.update_content_type_and_encoding()
    assert email_message.content_type == ContentType.PLAIN.value
    assert email_message.content_transfer_encoding == ContentTransferEncoding.SEVEN_BIT.value

def test_merge_headers(email_message):
    merged_headers = email_message.merge_headers({"X-New-Header": "NewValue"})
    assert merged_headers["X-New-Header"] == "NewValue"

def test_validate_headers(email_message):
    email_message.validate_headers()  # Should not raise an exception

def test_validate_headers_invalid_priority():
    with pytest.raises(EmailException):
        email_message = SmartEmailMessage(
            subject=sample_subject,
            body=sample_body,
            extra_headers={"X-Priority": "invalid"},  # Invalid priority value
        )
        email_message.validate_headers()

def test_validate_headers_invalid_spamd_result():
    with pytest.raises(EmailException):
        email_message = SmartEmailMessage(
            subject=sample_subject,
            body=sample_body,
            extra_headers={"X-Spamd-Result": "invalid"},
        )
        email_message.validate_headers()

def test_validate_headers_invalid_auto_response_suppress():
    with pytest.raises(EmailException):
        email_message = SmartEmailMessage(
            subject=sample_subject,
            body=sample_body,
            extra_headers={"X-Auto-Response-Suppress": "invalid"},
        )
        email_message.validate_headers()

def test_validate_headers_invalid_content_type():
    with pytest.raises(EmailException):
        email_message = SmartEmailMessage(
            subject=sample_subject,
            body=sample_body,
            extra_headers={"Content-Type": "invalid"},
        )
        email_message.validate_headers()

def test_validate_headers_invalid_content_transfer_encoding():
    with pytest.raises(EmailException):
        email_message = SmartEmailMessage(
            subject=sample_subject,
            body=sample_body,
            extra_headers={"Content-Transfer-Encoding": "invalid"},
        )
        email_message.validate_headers()

@patch("sage_imap.services.email.smtplib.SMTP")
def test_send_email(mock_smtp, email_message):
    email_message.send(
        smtp_server="smtp.example.com",
        smtp_port=587,
        smtp_user="user",
        smtp_password="password",
        use_tls=True,
    )
    mock_smtp.assert_called_once_with("smtp.example.com", 587)
    smtp_instance = mock_smtp.return_value
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("user", "password")
    smtp_instance.sendmail.assert_called_once()

@patch("sage_imap.services.email.smtplib.SMTP_SSL")
def test_send_email_ssl(mock_smtp_ssl, email_message):
    email_message.send(
        smtp_server="smtp.example.com",
        smtp_port=465,
        smtp_user="user",
        smtp_password="password",
        use_ssl=True,
    )
    mock_smtp_ssl.assert_called_once_with("smtp.example.com", 465)
    smtp_instance = mock_smtp_ssl.return_value
    smtp_instance.login.assert_called_once_with("user", "password")
    smtp_instance.sendmail.assert_called_once()

@patch("sage_imap.services.email.smtplib.SMTP")
def test_send_email_failure(mock_smtp, email_message):
    smtp_instance = mock_smtp.return_value
    smtp_instance.sendmail.side_effect = smtplib.SMTPException("SMTP error")
    with pytest.raises(EmailException):
        email_message.send(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            use_tls=True,
        )

@patch("sage_imap.services.email.smtplib.SMTP")
def test_send_email_unexpected_error(mock_smtp, email_message):
    smtp_instance = mock_smtp.return_value
    smtp_instance.sendmail.side_effect = Exception("Unexpected error")
    with pytest.raises(EmailException):
        email_message.send(
            smtp_server="smtp.example.com",
            smtp_port=587,
            smtp_user="user",
            smtp_password="password",
            use_tls=True,
        )
