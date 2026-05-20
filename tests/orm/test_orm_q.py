"""Tests for sage_imap.orm.q (Q objects and filter compilation)."""

from __future__ import annotations

from sage_imap.helpers.search import IMAPSearchCriteria
from sage_imap.orm.q import Q, _filters_to_criteria, _single_filter


class TestQFilters:
    def test_empty_q_compiles_all(self):
        assert Q().compile() == str(IMAPSearchCriteria.ALL)

    def test_invert_negates(self):
        q = ~Q(unread=True)
        assert "NOT" in q.compile()

    def test_exclude_via_negated_filter(self):
        criteria = _filters_to_criteria({"unread": True})
        q = Q(criteria, _negated=True)
        assert "NOT" in q.compile()

    def test_all_keyword_filters(self):
        filters = {
            "unread": True,
            "seen": True,
            "flagged": True,
            "answered": True,
            "deleted": True,
            "draft": True,
            "from_address": "a@b.com",
            "to_address": "c@d.com",
            "subject": "hello",
            "body": "world",
            "text": "findme",
            "since": "01-Jan-2026",
            "before": "31-Dec-2026",
            "on": "15-May-2026",
            "recent_days": 7,
            "uid": "1:100",
        }
        compiled = _filters_to_criteria(filters)
        for token in (
            "UNSEEN",
            "SEEN",
            "FLAGGED",
            "ANSWERED",
            "DELETED",
            "DRAFT",
            "FROM",
            "TO",
            "SUBJECT",
            "BODY",
            "TEXT",
            "SINCE",
            "BEFORE",
            "ON",
            "UID",
        ):
            assert token in compiled

    def test_none_values_skipped(self):
        assert _filters_to_criteria({"unread": None, "seen": None}) == str(
            IMAPSearchCriteria.ALL
        )

    def test_false_boolean_filters_ignored(self):
        assert _single_filter("unread", False) is None
        assert _single_filter("unknown_key", "x") is None

    def test_raw_string_child(self):
        q = Q("ALL")
        assert q.compile() == "ALL"

    def test_three_way_or(self):
        q = Q(unread=True) | Q(flagged=True) | Q(answered=True)
        assert "OR" in q.compile()
