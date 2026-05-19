"""Tests for shared transport_ops helpers."""

from sage_imap.services.transport_ops import expand_uid_set, parse_copyuid


class TestTransportOps:
    def test_parse_copyuid(self):
        response = ("OK", [b"[COPYUID 1 1:2 3:4]"])
        parsed = parse_copyuid(response)
        assert parsed["uidvalidity"] == 1
        assert parsed["dest_uids"] == "3:4"

    def test_expand_uid_set(self):
        assert expand_uid_set("1,3:5") == [1, 3, 4, 5]
