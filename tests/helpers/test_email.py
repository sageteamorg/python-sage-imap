from datetime import datetime, timezone
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, parsedate_to_datetime

import pytest

from sage_imap.helpers.email import EmailIterator, EmailMessage


def convert_to_local_time(dt: datetime) -> datetime:
    """
    Converts a datetime object to the local time zone.

    Parameters
    ----------
    dt : datetime
        The datetime object to convert.

    Returns
    -------
    datetime
        The converted datetime object in the local time zone.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone()


def test_email_message_initialization():
    message = MIMEMultipart()
    message["subject"] = "Test Subject"
    message["from"] = "test@example.com"
    message["to"] = "recipient@example.com"
    message["cc"] = "cc@example.com"
    message["bcc"] = "bcc@example.com"
    message["date"] = formatdate(localtime=True)
    body = MIMEText("This is the body of the email", "plain")
    message.attach(body)

    email_message = EmailMessage(message, flags=["SEEN", "IMPORTANT"])

    assert email_message.subject == "Test Subject"
    assert email_message.from_address == "test@example.com"
    assert email_message.to_address == ["recipient@example.com"]
    assert email_message.cc_address == ["cc@example.com"]
    assert email_message.bcc_address == ["bcc@example.com"]

    parsed_date = parsedate_to_datetime(message["date"])
    expected_date = (
        convert_to_local_time(parsed_date).replace(microsecond=0).isoformat()
    )
    assert email_message.date == expected_date  # Ensure date format matches


def test_parse_date():
    message = MIMEMultipart()
    email_message = EmailMessage(message, flags=[])

    assert email_message.parse_date(None) is None
    date_str = formatdate(localtime=True)

    parsed_date = parsedate_to_datetime(date_str)
    expected_date = (
        convert_to_local_time(parsed_date).replace(microsecond=0).isoformat()
    )
    assert email_message.parse_date(date_str) == expected_date


def test_get_body_non_multipart():
    message = MIMEText("This is the body of the email", "plain")
    email_message = EmailMessage(message, flags=[])

    assert email_message.body == "This is the body of the email"


def test_get_body_multipart():
    message = MIMEMultipart()
    body = MIMEText("This is the body of the email", "plain")
    message.attach(body)

    email_message = EmailMessage(message, flags=[])

    assert email_message.body == "This is the body of the email"


def test_get_body_multipart_html():
    message = MIMEMultipart()
    body = MIMEText("<p>This is the body of the email</p>", "html")
    message.attach(body)

    email_message = EmailMessage(message, flags=[])

    assert email_message.body == "<p>This is the body of the email</p>"


def test_get_attachments():
    message = MIMEMultipart()
    part = MIMEBase("application", "octet-stream")
    part.set_payload(b"Test attachment content")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=test.txt")
    message.attach(part)

    email_message = EmailMessage(message, flags=[])

    assert len(email_message.attachments) == 1
    assert email_message.attachments[0]["filename"] == "test.txt"
    assert email_message.attachments[0]["content_type"] == "application/octet-stream"
    assert email_message.attachments[0]["payload"] == b"Test attachment content"


def test_decode_payload():
    message = MIMEText("This is the body of the email", "plain")
    email_message = EmailMessage(message, flags=[])

    part = MIMEText("This is the body of the email", "plain")
    assert email_message.decode_payload(part) == "This is the body of the email"

    part.set_payload(b"This is the body of the email")
    assert email_message.decode_payload(part) == "This is the body of the email"


def test_has_attachments():
    message = MIMEMultipart()
    email_message = EmailMessage(message, flags=[])

    assert not email_message.has_attachments()

    part = MIMEBase("application", "octet-stream")
    part.set_payload(b"Test attachment content")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=test.txt")
    message.attach(part)

    email_message = EmailMessage(message, flags=[])
    assert email_message.has_attachments()


def test_get_attachment_filenames():
    message = MIMEMultipart()
    part = MIMEBase("application", "octet-stream")
    part.set_payload(b"Test attachment content")
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment; filename=test.txt")
    message.attach(part)

    email_message = EmailMessage(message, flags=[])
    assert email_message.get_attachment_filenames() == ["test.txt"]


# def test_decode_payload_utf8():
#     part = MIMEText("This is the body of the email", "plain", "utf-8")
#     email_message = EmailMessage(MIMEMultipart(), flags=[])
#     part.set_payload("This is the body of the email".encode("utf-8"))
#     decoded_payload = email_message.decode_payload(part)
#     assert decoded_payload == "This is the body of the email"


def test_decode_payload_latin1():
    part = MIMEText("This is the body of the email", "plain", "latin-1")
    email_message = EmailMessage(MIMEMultipart(), flags=[])
    part.set_payload("This is the body of the email".encode("latin-1"))
    assert email_message.decode_payload(part) == "This is the body of the email"


def test_decode_payload_ascii():
    part = MIMEText("This is the body of the email", "plain", "ascii")
    email_message = EmailMessage(MIMEMultipart(), flags=[])
    part.set_payload("This is the body of the email".encode("ascii"))
    assert email_message.decode_payload(part) == "This is the body of the email"


# def test_decode_payload_ascii_error():
#     part = MIMEText("This is the body of the email", "plain", "us-ascii")
#     email_message = EmailMessage(MIMEMultipart(), flags=[])
#     part.set_payload(b'\x80abc')
#     decoded_payload = email_message.decode_payload(part)
#     assert decoded_payload == 'abc'  # "\x80" is not valid in ascii, ignored


def test_decode_payload_latin1_error():
    part = MIMEText("This is the body of the email", "plain", "latin-1")
    email_message = EmailMessage(MIMEMultipart(), flags=[])
    # Creating invalid Latin-1 sequence
    part.set_payload(b"\x80abc")
    assert (
        email_message.decode_payload(part) == "\x80abc"
    )  # "\x80" is valid in latin-1 but may not display correctly


def test_decode_payload_latin1_error():
    part = MIMEText("This is the body of the email", "plain", "latin-1")
    email_message = EmailMessage(MIMEMultipart(), flags=[])
    part.set_payload(b"\x80abc")
    assert (
        email_message.decode_payload(part) == "\x80abc"
    )  # "\x80" is valid in latin-1 but may not display correctly


def test_decode_payload_non_bytes():
    part = MIMEText("This is the body of the email", "plain")
    email_message = EmailMessage(MIMEMultipart(), flags=[])
    part.set_payload("This is the body of the email")
    assert email_message.decode_payload(part) == "This is the body of the email"


######################################################################################


def create_test_message(
    subject="Test",
    from_address="test@example.com",
    to_address="to@example.com",
    body="This is a test email",
    is_multipart=False,
    with_attachments=False,
):
    if is_multipart:
        message = MIMEMultipart()
        message.attach(MIMEText(body, "plain"))
        if with_attachments:
            attachment = MIMEText("This is an attachment", "plain")
            attachment.add_header(
                "Content-Disposition", "attachment", filename="test.txt"
            )
            message.attach(attachment)
    else:
        message = MIMEText(body, "plain")

    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to_address
    message["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")
    return message


def test_email_iterator():
    message1 = create_test_message(subject="Test 1")
    message2 = create_test_message(subject="Test 2")
    email_message1 = EmailMessage(message1, flags=["Seen"])
    email_message2 = EmailMessage(message2, flags=["Unseen"])
    email_iterator = EmailIterator([email_message1, email_message2])
    assert len(email_iterator) == 2
    assert email_iterator[0].subject == "Test 1"
    assert email_iterator[1].subject == "Test 2"


def test_email_iterator_out_of_range():
    message = create_test_message()
    email_message = EmailMessage(message, flags=["Seen"])
    email_iterator = EmailIterator([email_message])
    with pytest.raises(IndexError):
        email_iterator[1]


def test_email_iterator_slice():
    message1 = create_test_message(subject="Test 1")
    message2 = create_test_message(subject="Test 2")
    email_message1 = EmailMessage(message1, flags=["Seen"])
    email_message2 = EmailMessage(message2, flags=["Unseen"])
    email_iterator = EmailIterator([email_message1, email_message2])
    sliced_iterator = email_iterator[0:1]
    assert len(sliced_iterator) == 1
    assert sliced_iterator[0].subject == "Test 1"


def test_email_iterator_invalid_type():
    message = create_test_message(subject="Test 1")
    email_message = EmailMessage(message, flags=["Seen"])
    email_iterator = EmailIterator([email_message])
    with pytest.raises(TypeError):
        email_iterator["invalid_type"]


def test_email_iterator_repr():
    message1 = create_test_message(subject="Test 1")
    message2 = create_test_message(subject="Test 2")
    email_message1 = EmailMessage(message1, flags=["Seen"])
    email_message2 = EmailMessage(message2, flags=["Unseen"])
    email_iterator = EmailIterator([email_message1, email_message2])
    assert repr(email_iterator) == "EmailIterator(2 emails)"


def test_email_iterator_next():
    message1 = create_test_message(subject="Test 1")
    message2 = create_test_message(subject="Test 2")
    email_message1 = EmailMessage(message1, flags=["Seen"])
    email_message2 = EmailMessage(message2, flags=["Unseen"])
    email_iterator = EmailIterator([email_message1, email_message2])
    assert next(email_iterator).subject == "Test 1"
    assert next(email_iterator).subject == "Test 2"
    with pytest.raises(StopIteration):
        next(email_iterator)


def test_email_iterator_iter():
    message1 = create_test_message(subject="Test 1")
    message2 = create_test_message(subject="Test 2")
    email_message1 = EmailMessage(message1, flags=["Seen"])
    email_message2 = EmailMessage(message2, flags=["Unseen"])
    email_iterator = EmailIterator([email_message1, email_message2])

    subjects = [email_message.subject for email_message in email_iterator]
    assert subjects == ["Test 1", "Test 2"]
