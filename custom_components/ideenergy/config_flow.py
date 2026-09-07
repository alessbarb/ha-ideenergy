# Copyright (C) 2021-2026 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

import os
from collections.abc import Mapping
from logging import getLogger
from typing import Any

import ideenergy
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import CONF_CONTRACT, CONFIG_ENTRY_VERSION, DOMAIN

LOGGER = getLogger(__name__)


def _auth_schema(*, username: str | None = None) -> vol.Schema:
    """Build the credential form without exposing the stored password."""
    username_default = username or os.environ.get("I_DE_ENERGY_USERNAME")
    password_default = os.environ.get("I_DE_ENERGY_PASSWORD")

    schema: dict[Any, type] = {}
    if username_default:
        schema[vol.Required(CONF_USERNAME, default=username_default)] = str
    else:
        schema[vol.Required(CONF_USERNAME)] = str

    if password_default:
        schema[vol.Required(CONF_PASSWORD, default=password_default)] = str
    else:
        schema[vol.Required(CONF_PASSWORD)] = str

    return vol.Schema(schema)


def _is_authentication_error(exc: ideenergy.ClientError) -> bool:
    """Return whether an i-DE client error represents rejected credentials."""
    if isinstance(exc, (ideenergy.CommandError, ideenergy.UserExpiredError)):
        return True

    if isinstance(exc, ideenergy.RequestFailedError):
        return getattr(exc.response, "status", None) in (401, 403)

    return False


def _contract_map(contracts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Map human-readable contract labels to API contract records."""
    return {f"{item['cups']} ({item['direccion']})": item for item in contracts}


def _find_existing_contract(
    entry: ConfigEntry, contracts: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Find the contract that represents the existing config entry identity."""
    if entry.unique_id is not None:
        for contract in contracts:
            if str(contract["cups"]) == entry.unique_id:
                return contract

    current_contract = str(entry.data[CONF_CONTRACT])
    for contract in contracts:
        if str(contract["codContrato"]) == current_contract:
            return contract

    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Handle i-DE configuration flows."""

    VERSION = CONFIG_ENTRY_VERSION

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.info: dict[str, Any] = {}
        self.contracts: list[dict[str, Any]] = []

    async def _async_validate_credentials(
        self, username: str, password: str
    ) -> str | None:
        """Authenticate and load contracts, returning a config-flow error key."""
        try:
            api = await create_api(self.hass, username, password)
            contracts = await api.get_contracts()
        except ideenergy.ClientError as exc:
            if _is_authentication_error(exc):
                return "invalid_auth"
            return "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception while connecting to i-DE")
            return "unknown"

        self.info = {
            CONF_USERNAME: username,
            CONF_PASSWORD: password,
        }
        self.contracts = contracts
        return None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors = {}

        if user_input is not None:
            error = await self._async_validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if error is None:
                return await self.async_step_contract()
            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=_auth_schema(),
            errors=errors,
        )

    async def async_step_contract(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select the supply contract for a new config entry."""
        contracts = _contract_map(self.contracts)
        schema = vol.Schema({vol.Required(CONF_CONTRACT): vol.In(contracts.keys())})

        if user_input is None:
            return self.async_show_form(step_id="contract", data_schema=schema)

        contract = contracts[user_input[CONF_CONTRACT]]
        cups = str(contract["cups"])
        await self.async_set_unique_id(cups)
        self._abort_if_unique_id_configured()

        self.info[CONF_CONTRACT] = contract["codContrato"]
        return self.async_create_entry(title=f"CUPS {cups}", data=self.info)

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Start reauthentication for an existing entry."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Validate replacement credentials and reload the entry."""
        entry = self._get_reauth_entry()
        errors = {}

        if user_input is not None:
            error = await self._async_validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if error is None:
                contract = _find_existing_contract(entry, self.contracts)
                if contract is None:
                    errors["base"] = "contract_not_found"
                else:
                    cups = str(contract["cups"])
                    await self.async_set_unique_id(cups)
                    if entry.unique_id is None:
                        self.hass.config_entries.async_update_entry(
                            entry, unique_id=cups
                        )
                    else:
                        self._abort_if_unique_id_mismatch()

                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_USERNAME: self.info[CONF_USERNAME],
                            CONF_PASSWORD: self.info[CONF_PASSWORD],
                            CONF_CONTRACT: contract["codContrato"],
                        },
                    )
            else:
                errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_auth_schema(username=entry.data[CONF_USERNAME]),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Reconnect an existing entry while preserving its CUPS identity."""
        entry = self._get_reconfigure_entry()
        errors = {}

        if user_input is not None:
            error = await self._async_validate_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            if error is None:
                contract = _find_existing_contract(entry, self.contracts)
                if contract is None:
                    errors["base"] = "contract_not_found"
                else:
                    cups = str(contract["cups"])
                    await self.async_set_unique_id(cups)
                    if entry.unique_id is not None:
                        self._abort_if_unique_id_mismatch()

                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates={
                            CONF_USERNAME: self.info[CONF_USERNAME],
                            CONF_PASSWORD: self.info[CONF_PASSWORD],
                            CONF_CONTRACT: contract["codContrato"],
                        },
                    )
            else:
                errors["base"] = error

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_auth_schema(username=entry.data[CONF_USERNAME]),
            errors=errors,
        )


async def create_api(hass, username, password):
    """Create and authenticate an i-DE API client."""
    session = async_create_clientsession(hass)
    client = ideenergy.Client(session, username, password)
    await client.login()
    return client
