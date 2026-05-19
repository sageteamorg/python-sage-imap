"""Contract parity between sync _ops and async mailbox search/fetch shapes."""

from sage_imap.aio._response import search_data_from_lines
from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.services.mailbox._ops import uid_search_via_transport


class _MockTransport:
    def search(self, criteria, charset=None, use_uid=False):
        return "OK", [b"1 2 3"]


class TestParity:
    def test_uid_search_result_shape(self):
        result = uid_search_via_transport(
            _MockTransport(), IMAPSearchCriteria.UNSEEN, charset="UTF-8"
        )
        assert result.success
        assert result.operation == "uid_search"
        assert result.affected_messages == ["1", "2", "3"]

    def test_async_search_line_parsing_matches(self):
        data = search_data_from_lines([b"* SEARCH 1 2 3"])
        assert data[0].split() == [b"1", b"2", b"3"]
