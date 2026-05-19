"""Tests for IMAP search criteria helpers."""

from sage_imap.helpers.search import IMAPSearchCriteria, escape_search_string


class TestEscapeSearchString:
    def test_escape_quotes(self):
        assert escape_search_string('say "hello"') == 'say \\"hello\\"'

    def test_escape_backslash(self):
        assert escape_search_string("a\\b") == "a\\\\b"


class TestIMAPSearchCriteria:
    def test_subject_escapes_quotes(self):
        criteria = IMAPSearchCriteria.subject('test "quote"')
        assert '\\"quote\\"' in criteria

    def test_from_address_escaped(self):
        criteria = IMAPSearchCriteria.from_address("user@example.com")
        assert criteria == 'FROM "user@example.com"'

    def test_date_criteria(self):
        assert IMAPSearchCriteria.before("01-Jan-2023") == "BEFORE 01-Jan-2023"
        assert IMAPSearchCriteria.on("01-Jan-2023") == "ON 01-Jan-2023"
        assert IMAPSearchCriteria.since("01-Jan-2023") == "SINCE 01-Jan-2023"

    def test_address_and_body_criteria(self):
        assert "TO " in IMAPSearchCriteria.to_address("a@b.com")
        assert "BODY " in IMAPSearchCriteria.body("text")
        assert "TEXT " in IMAPSearchCriteria.text("find")

    def test_header_and_combinators(self):
        assert "HEADER" in IMAPSearchCriteria.header("X-Test", "1")
        assert "SEEN" in IMAPSearchCriteria.and_criteria(
            IMAPSearchCriteria.SEEN, IMAPSearchCriteria.UNSEEN
        )
        assert "OR" in IMAPSearchCriteria.or_criteria(
            IMAPSearchCriteria.SEEN, IMAPSearchCriteria.UNSEEN
        )
        assert "NOT" in IMAPSearchCriteria.not_criteria(IMAPSearchCriteria.SEEN)

    def test_recent_message_id_uid(self):
        assert IMAPSearchCriteria.recent(1).startswith("SINCE")
        assert "Message-ID" in IMAPSearchCriteria.message_id("<id@x.com>")
        assert IMAPSearchCriteria.uid("1:5") == "UID 1:5"
