"""Tests for i-DE config-entry identity and recovery flows."""

from typing import Any
from unittest.mock import AsyncMock, Mock

import ideenergy
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ideenergy import config_flow
from custom_components.ideenergy.const import CONF_CONTRACT, DOMAIN

pytestmark = pytest.mark.asyncio

CUPS = "ES0000000000000000AB"
CONTRACT_ID = "123456789"
CONTRACT = {
    "cups": CUPS,
    "direccion": "Test address",
    "codContrato": CONTRACT_ID,
}


class FakeAPI:
    """Minimal authenticated API used by lifecycle tests."""

    def __init__(self, contracts: list[dict[str, Any]] | None = None):
        self._contracts = contracts if contracts is not None else [CONTRACT]

    async def get_contracts(self) -> list[dict[str, Any]]:
        return self._contracts


async def start_user_flow(hass):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def submit_credentials(
    hass, result, username="user@example.com", password="secret"
):
    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_USERNAME: username, CONF_PASSWORD: password},
    )


async def test_duplicate_cups_is_rejected(hass, monkeypatch):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUPS,
        data={
            CONF_USERNAME: "existing@example.com",
            CONF_PASSWORD: "old-secret",
            CONF_CONTRACT: CONTRACT_ID,
        },
    )
    entry.add_to_hass(hass)

    async def fake_create_api(hass, username, password):
        return FakeAPI()

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await start_user_flow(hass)
    result = await submit_credentials(hass, result)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "contract"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_CONTRACT: f"{CUPS} (Test address)"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_transient_client_failure_is_cannot_connect(hass, monkeypatch):
    response = Mock(status=503, reason="Service Unavailable")

    async def fake_create_api(hass, username, password):
        raise ideenergy.RequestFailedError(response)

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await start_user_flow(hass)
    result = await submit_credentials(hass, result)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}


async def test_http_403_is_invalid_auth(hass, monkeypatch):
    response = Mock(status=403, reason="Forbidden")

    async def fake_create_api(hass, username, password):
        raise ideenergy.RequestFailedError(response)

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await start_user_flow(hass)
    result = await submit_credentials(hass, result)

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_auth"}


async def test_reauth_updates_credentials_and_preserves_cups(hass, monkeypatch):
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=CUPS,
        data={
            CONF_USERNAME: "old@example.com",
            CONF_PASSWORD: "old-secret",
            CONF_CONTRACT: CONTRACT_ID,
        },
    )
    entry.add_to_hass(hass)

    async def fake_create_api(hass, username, password):
        return FakeAPI()

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)
    monkeypatch.setattr(
        hass.config_entries, "async_reload", AsyncMock(return_value=True)
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
        data=entry.data,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "new@example.com",
            CONF_PASSWORD: "new-secret",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.unique_id == CUPS
    assert entry.data == {
        CONF_USERNAME: "new@example.com",
        CONF_PASSWORD: "new-secret",
        CONF_CONTRACT: CONTRACT_ID,
    }


async def test_reauth_missing_contract_does_not_mutate_entry(hass, monkeypatch):
    original_data = {
        CONF_USERNAME: "old@example.com",
        CONF_PASSWORD: "old-secret",
        CONF_CONTRACT: CONTRACT_ID,
    }
    entry = MockConfigEntry(domain=DOMAIN, unique_id=CUPS, data=original_data)
    entry.add_to_hass(hass)

    async def fake_create_api(hass, username, password):
        return FakeAPI(contracts=[])

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={
            "source": config_entries.SOURCE_REAUTH,
            "entry_id": entry.entry_id,
        },
        data=entry.data,
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "new@example.com",
            CONF_PASSWORD: "new-secret",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "contract_not_found"}
    assert entry.unique_id == CUPS
    assert entry.data == original_data
