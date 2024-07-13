from datetime import datetime, timezone

from sage_imap.utils import convert_to_local_time


def test_convert_to_local_time():
    # Test UTC datetime conversion
    dt_utc = datetime(2023, 7, 13, 12, 0, 0, tzinfo=timezone.utc)
    local_time = convert_to_local_time(dt_utc)
    assert local_time.tzinfo is not None
    assert local_time.utcoffset() == local_time.astimezone().utcoffset()

    # Test naive datetime conversion (assumed to be UTC)
    dt_naive = datetime(2023, 7, 13, 12, 0, 0)
    local_time = convert_to_local_time(dt_naive)
    assert local_time.tzinfo is not None
    assert local_time.utcoffset() == local_time.astimezone().utcoffset()

    # Test datetime already in local time zone
    local_tz = datetime.now().astimezone().tzinfo
    dt_local = datetime(2023, 7, 13, 12, 0, 0, tzinfo=local_tz)
    local_time = convert_to_local_time(dt_local)
    assert local_time.tzinfo == local_tz
