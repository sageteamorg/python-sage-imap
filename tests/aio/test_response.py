"""Tests for aioimaplib response normalization helpers."""

from sage_imap.aio._response import (
    fetch_lines_to_imaplib_data,
    response_to_imap,
    search_data_from_lines,
)


class TestResponseToImap:
    def test_none_response(self):
        assert response_to_imap(None) == ("NO", [])

    def test_tuple_passthrough(self):
        assert response_to_imap(("OK", [b"x"])) == ("OK", [b"x"])

    def test_aio_response_object(self):
        class Resp:
            result = "OK"
            lines = [b"line"]

        assert response_to_imap(Resp()) == ("OK", [b"line"])


class TestSearchDataFromLines:
    def test_empty_lines(self):
        assert search_data_from_lines([]) == [b""]

    def test_non_bytes_skipped(self):
        assert search_data_from_lines(["text"]) == [b""]

    def test_search_prefix(self):
        assert search_data_from_lines([b"* SEARCH 7 8"]) == [b"7 8"]


class TestFetchLinesToImaplibData:
    def test_pairs_header_and_body(self):
        lines = [
            b"* 1 FETCH (UID 1 FLAGS (\\Seen) RFC822 {4}",
            b"body",
        ]
        data = fetch_lines_to_imaplib_data(lines)
        assert len(data) == 1
        assert data[0][1] == b"body"

    def test_skips_non_fetch_lines(self):
        assert fetch_lines_to_imaplib_data([b"OK completed"]) == []
