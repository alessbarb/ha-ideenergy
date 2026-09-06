"""Tests for the i-DE config flow."""

from typing import Any

import ideenergy
import pytest
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ideenergy import config_flow
from custom_components.ideenergy.const import CONF_CONTRACT, DOMAIN

pytestmark = pytest.mark.asyncio

CONTRACT = {
    "cups": "ES0000000000000000AB",
    "direccion": "Test address",
    "codContrato": "123456789",
}


class FakeAPI:
    """Minimal authenticated API used by config-flow tests."""

    async def get_contracts(self) -> list[dict[str, Any]]:
        return [CONTRACT]


async def test_user_flow_creates_entry(hass, monkeypatch) -> None:
    """A valid account and selected contract create a config entry."""

    async def fake_create_api(hass, username, password):
        return FakeAPI()

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "secret",
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "contract"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_CONTRACT: "ES0000000000000000AB (Test address)"},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "CUPS ES0000000000000000AB"
    assert result["data"] == {
        CONF_USERNAME: "user@example.com",
        CONF_PASSWORD: "secret",
        CONF_CONTRACT: "123456789",
    }


async def test_user_flow_rejects_invalid_auth(hass, monkeypatch) -> None:
    """Client authentication errors are shown in the form."""

    async def fake_create_api(hass, username, password):
        raise ideenergy.CommandError({"success": "false"})

    monkeypatch.setattr(config_flow, "create_api", fake_create_api)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "user@example.com",
            CONF_PASSWORD: "wrong",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}
