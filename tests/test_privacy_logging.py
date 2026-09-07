"""Tests for privacy-safe integration logging."""

import logging
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from custom_components.ideenergy import coordinator, sensor

pytestmark = pytest.mark.asyncio

SECRET_ACCOUNT = "private-user@example.com/private-contract-123"
SECRET_CUPS = "sensor.es123456789012345678_historical_consumption"
SECRET_ENERGY = 987654.321


class SensitiveClient:
    """Client double whose string representation contains account identifiers."""

    is_logged = True

    def __str__(self) -> str:
        return SECRET_ACCOUNT


def make_state():
    return SimpleNamespace(data={}, async_save=AsyncMock())


async def test_coordinator_logs_do_not_render_client_identity(hass, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.ideenergy.coordinator")
    instance = coordinator.IDeEnergyDataCoordinator(
        hass=hass,
        client=SensitiveClient(),
        config_entry_state=make_state(),
    )

    instance._state_is_too_recent_with_debug(
        key="missing",
        max_age=timedelta(minutes=5),
        label="test timestamp",
    )

    assert SECRET_ACCOUNT not in instance.name
    assert SECRET_ACCOUNT not in caplog.text


async def test_statistic_logs_do_not_render_entity_id_or_energy_value(hass, caplog):
    caplog.set_level(logging.DEBUG, logger="custom_components.ideenergy.sensor")
    subject = SimpleNamespace(
        hass=hass,
        entity_id=SECRET_CUPS,
        I_DE_ENTITY_NAME="Historical Consumption",
    )

    await sensor.IDeEnergySensor.async_calculate_statistic_data(
        subject,
        [SimpleNamespace(timestamp=3601, state=1.0)],
        latest={"sum": SECRET_ENERGY, "start": 0},
    )

    assert SECRET_CUPS not in caplog.text
    assert str(SECRET_ENERGY) not in caplog.text
