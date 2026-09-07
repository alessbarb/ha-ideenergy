"""Tests for historical statistic aggregation."""

from types import SimpleNamespace

import pytest

from custom_components.ideenergy import sensor

pytestmark = pytest.mark.asyncio


def make_subject(hass):
    """Create the minimal object needed by the statistic calculator."""
    return SimpleNamespace(
        hass=hass,
        entity_id="sensor.test_historical_consumption",
        get_statistic_metadata=lambda: {"statistic_id": "sensor.test"},
    )


def historical_state(*, timestamp: float, state: float | None):
    """Create a minimal historical state value."""
    return SimpleNamespace(timestamp=timestamp, state=state)


async def test_zero_energy_period_is_preserved(hass):
    subject = make_subject(hass)

    result = await sensor.IDeEnergySensor.async_calculate_statistic_data(
        subject,
        [historical_state(timestamp=3601, state=0)],
    )

    assert len(result) == 1
    assert result[0]["state"] == 0
    assert result[0]["sum"] == 0


async def test_unsorted_periods_are_aggregated_chronologically(hass):
    subject = make_subject(hass)

    result = await sensor.IDeEnergySensor.async_calculate_statistic_data(
        subject,
        [
            historical_state(timestamp=7201, state=2),
            historical_state(timestamp=3601, state=1),
        ],
    )

    assert [item["state"] for item in result] == [1, 2]
    assert [item["sum"] for item in result] == [1, 3]


async def test_none_period_is_discarded_without_dropping_zero(hass):
    subject = make_subject(hass)

    result = await sensor.IDeEnergySensor.async_calculate_statistic_data(
        subject,
        [
            historical_state(timestamp=3601, state=None),
            historical_state(timestamp=7201, state=0),
        ],
    )

    assert len(result) == 1
    assert result[0]["state"] == 0
    assert result[0]["sum"] == 0


async def test_latest_sum_is_reused_without_second_recorder_lookup(hass):
    subject = make_subject(hass)

    result = await sensor.IDeEnergySensor.async_calculate_statistic_data(
        subject,
        [historical_state(timestamp=3601, state=2.5)],
        latest={"start": 0, "sum": 10},
    )

    assert len(result) == 1
    assert result[0]["state"] == 2.5
    assert result[0]["sum"] == 12.5
