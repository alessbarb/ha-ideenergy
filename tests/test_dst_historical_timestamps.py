"""Tests for preserving Spanish DST-aware parser timestamps."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from custom_components.ideenergy.coordinator import _as_local_datetime

LOCAL_TZ = ZoneInfo("Europe/Madrid")


def test_legacy_naive_datetime_is_interpreted_as_madrid_local_time():
    value = _as_local_datetime(datetime(2026, 1, 15, 12, 0))

    assert value.tzinfo == LOCAL_TZ
    assert value.utcoffset() == timedelta(hours=1)


def test_autumn_fold_is_preserved_for_aware_parser_values():
    first_two = datetime(2026, 10, 25, 2, 0, tzinfo=LOCAL_TZ, fold=0)
    second_two = datetime(2026, 10, 25, 2, 0, tzinfo=LOCAL_TZ, fold=1)

    normalized_first = _as_local_datetime(first_two)
    normalized_second = _as_local_datetime(second_two)

    assert normalized_first.fold == 0
    assert normalized_second.fold == 1
    assert normalized_first.utcoffset() == timedelta(hours=2)
    assert normalized_second.utcoffset() == timedelta(hours=1)
    assert normalized_second.timestamp() - normalized_first.timestamp() == 3600
