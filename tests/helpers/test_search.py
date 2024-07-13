from datetime import datetime, timedelta

import pytest

from sage_imap.helpers.search import IMAPSearchCriteria


def test_enum_values():
    assert IMAPSearchCriteria.ALL == "ALL"
    assert IMAPSearchCriteria.SEEN == "SEEN"
    assert IMAPSearchCriteria.UNSEEN == "UNSEEN"
    assert IMAPSearchCriteria.FLAGGED == "FLAGGED"
    assert IMAPSearchCriteria.UNFLAGGED == "UNFLAGGED"
    assert IMAPSearchCriteria.ANSWERED == "ANSWERED"
    assert IMAPSearchCriteria.UNANSWERED == "UNANSWERED"
    assert IMAPSearchCriteria.DELETED == "DELETED"
    assert IMAPSearchCriteria.UNDELETED == "UNDELETED"
    assert IMAPSearchCriteria.DRAFT == "DRAFT"


def test_before():
    assert IMAPSearchCriteria.before("01-Jan-2023") == "BEFORE 01-Jan-2023"


def test_on():
    assert IMAPSearchCriteria.on("01-Jan-2023") == "ON 01-Jan-2023"


def test_since():
    assert IMAPSearchCriteria.since("01-Jan-2023") == "SINCE 01-Jan-2023"


def test_from_address():
    assert (
        IMAPSearchCriteria.from_address("example@example.com")
        == 'FROM "example@example.com"'
    )


def test_to_address():
    assert (
        IMAPSearchCriteria.to_address("example@example.com")
        == 'TO "example@example.com"'
    )


def test_subject():
    assert IMAPSearchCriteria.subject("Meeting") == 'SUBJECT "Meeting"'


def test_body():
    assert IMAPSearchCriteria.body("Project update") == 'BODY "Project update"'


def test_text():
    assert IMAPSearchCriteria.text("Important") == 'TEXT "Important"'


def test_header():
    assert IMAPSearchCriteria.header("X-Priority", "1") == 'HEADER "X-Priority" "1"'


def test_and_criteria():
    criteria = IMAPSearchCriteria.and_criteria(
        IMAPSearchCriteria.SEEN, IMAPSearchCriteria.from_address("example@example.com")
    )
    assert criteria == '(SEEN FROM "example@example.com")'


def test_or_criteria():
    criteria = IMAPSearchCriteria.or_criteria(
        IMAPSearchCriteria.SEEN, IMAPSearchCriteria.UNSEEN
    )
    assert criteria == "(OR SEEN UNSEEN)"


def test_not_criteria():
    criteria = IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.SEEN)
    assert criteria == "NOT (SEEN)"


def test_recent():
    recent_days = 7
    recent_date = (datetime.now() - timedelta(days=recent_days)).strftime("%d-%b-%Y")
    criteria = IMAPSearchCriteria.recent(recent_days)
    assert criteria == f"SINCE {recent_date}"

def test_message_id():
    # Test for a specific Message-ID
    message_id = "<unique-id@example.com>"
    expected_criteria = 'HEADER "Message-ID" "<unique-id@example.com>"'
    assert IMAPSearchCriteria.message_id(message_id) == expected_criteria

    # Test for a different Message-ID
    message_id = "<another-id@example.com>"
    expected_criteria = 'HEADER "Message-ID" "<another-id@example.com>"'
    assert IMAPSearchCriteria.message_id(message_id) == expected_criteria
