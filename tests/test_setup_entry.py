"""Tests for i-DE config entry setup failures and identity migration."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import ideenergy
import pytest
from homeassistant.config_entries import ConfigEntryNotReady
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.exceptions import ConfigEntryAuthFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ideenergy import async_setup_entry
from custom_components.ideenergy.const import CONF_CONTRACT, DOMAIN

pytestmark = pytest.mark.asyncio

CUPS = "ES0000000000000000AB"
CONTRACT_ID = "123456789"


def make_entry(*, unique_id=None):
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=unique_id,
        data={
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "secret",
            CONF_CONTRACT: CONTRACT_ID,
        },
    )


def make_contract_details():
    return {
        "cups": CUPS,
        "listContador": [{"tipMarca": "TEST"}],
    }


async def test_setup_rejected_credentials_raise_auth_failed(hass, monkeypatch):
    entry = make_entry(unique_id=CUPS)
    entry.add_to_hass(hass)
    client = SimpleNamespace(
        get_contract_details=AsyncMock(
            side_effect=ideenergy.CommandError({"success": "false"})
        )
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.get_i_de_energy_api",
        lambda hass, entry: client,
    )

    with pytest.raises(ConfigEntryAuthFailed):
        await async_setup_entry(hass, entry)


async def test_setup_transient_failure_is_retryable(hass, monkeypatch):
    entry = make_entry(unique_id=CUPS)
    entry.add_to_hass(hass)
    response = Mock(status=503, reason="Service Unavailable")
    client = SimpleNamespace(
        get_contract_details=AsyncMock(side_effect=ideenergy.RequestFailedError(response))
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.get_i_de_energy_api",
        lambda hass, entry: client,
    )

    with pytest.raises(ConfigEntryNotReady):
        await async_setup_entry(hass, entry)


async def test_setup_migrates_missing_unique_id_to_cups(hass, monkeypatch):
    entry = make_entry(unique_id=None)
    entry.add_to_hass(hass)
    client = SimpleNamespace(
        get_contract_details=AsyncMock(return_value=make_contract_details())
    )

    coordinator = SimpleNamespace(
        async_config_entry_first_refresh=AsyncMock(),
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.get_i_de_energy_api",
        lambda hass, entry: client,
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.IDeEnergyConfigEntryState",
        lambda hass, entry: SimpleNamespace(async_load=AsyncMock()),
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.IDeEnergyDataCoordinator",
        lambda **kwargs: coordinator,
    )
    monkeypatch.setattr(
        "custom_components.ideenergy.async_get_loaded_integration",
        AsyncMock(return_value=SimpleNamespace()),
    )
    monkeypatch.setattr(
        hass.config_entries,
        "async_forward_entry_setups",
        AsyncMock(),
    )

    assert await async_setup_entry(hass, entry) is True
    assert entry.unique_id == CUPS
    coordinator.async_config_entry_first_refresh.assert_awaited_once_with()
