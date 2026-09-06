"""Tests for privacy-safe config entry diagnostics."""

import json
from types import SimpleNamespace

import pytest
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ideenergy.const import CONF_CONTRACT, DOMAIN
from custom_components.ideenergy.coordinator import IDeEnergyCoordinatorDataSet
from custom_components.ideenergy.diagnostics import async_get_config_entry_diagnostics

pytestmark = pytest.mark.asyncio


async def test_diagnostics_redact_identifiers_and_energy_values(hass):
    username = "private-user@example.com"
    password = "private-password"
    contract = "private-contract-123"
    cups = "ES123456789012345678"
    sensitive_reading = 987654.321

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=cups,
        data={
            CONF_USERNAME: username,
            CONF_PASSWORD: password,
            CONF_CONTRACT: contract,
        },
    )
    coordinator = SimpleNamespace(
        last_update_success=True,
        dataset_counter={
            IDeEnergyCoordinatorDataSet.DIRECT_READING.name: 1,
            IDeEnergyCoordinatorDataSet.HISTORICAL_CONSUMPTION.name: 1,
            IDeEnergyCoordinatorDataSet.HISTORICAL_GENERATION.name: 0,
            IDeEnergyCoordinatorDataSet.POWER_DEMAND_PEAKS.name: 0,
        },
        data={
            IDeEnergyCoordinatorDataSet.DIRECT_READING: {
                "measure_accumulated": sensitive_reading,
                "measure_instant": 4321.123,
            },
            IDeEnergyCoordinatorDataSet.HISTORICAL_CONSUMPTION: [
                SimpleNamespace(state=sensitive_reading, timestamp=1234567890)
            ],
            IDeEnergyCoordinatorDataSet.HISTORICAL_GENERATION: None,
            IDeEnergyCoordinatorDataSet.POWER_DEMAND_PEAKS: None,
        },
    )
    entry.runtime_data = SimpleNamespace(coordinator=coordinator)

    result = await async_get_config_entry_diagnostics(hass, entry)
    rendered = json.dumps(result, sort_keys=True)

    assert username not in rendered
    assert password not in rendered
    assert contract not in rendered
    assert cups not in rendered
    assert str(sensitive_reading) not in rendered
    assert "4321.123" not in rendered

    assert result["entry"]["unique_id"] == "**REDACTED**"
    assert result["coordinator"]["last_update_success"] is True
    assert result["coordinator"]["active_datasets"] == [
        "DIRECT_READING",
        "HISTORICAL_CONSUMPTION",
    ]
    assert result["coordinator"]["available_datasets"] == [
        "DIRECT_READING",
        "HISTORICAL_CONSUMPTION",
    ]
