# test_enums.py
import pytest

from sage_imap.helpers.flags import FlagCommand, Flags


def test_flags_enum():
    assert Flags.SEEN == "\\Seen"
    assert Flags.ANSWERED == "\\Answered"
    assert Flags.FLAGGED == "\\Flagged"
    assert Flags.DELETED == "\\Deleted"
    assert Flags.DRAFT == "\\Draft"
    assert Flags.RECENT == "\\Recent"


def test_flag_command_enum():
    assert FlagCommand.ADD == "+FLAGS"
    assert FlagCommand.REMOVE == "-FLAGS"
