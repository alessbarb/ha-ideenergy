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

import logging
import os

import ideenergy
from homeassistant.config_entries import ConfigEntry, ConfigEntryNotReady
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.loader import async_get_loaded_integration

from .const import CONF_CONTRACT, DOMAIN, UPDATE_INTERVAL
from .coordinator import IDeEnergyDataCoordinator
from .data import IntegrationIDeEnergyConfigEntry, IntegrationIDeEnergyRunTimeData
from .store import IDeEnergyConfigEntryState

PLATFORMS: list[str] = ["sensor"]

LOGGER = logging.getLogger(__name__)


def setup_domain_data(hass: HomeAssistant) -> None:
    """Set up shared data for all config entries."""
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: IntegrationIDeEnergyConfigEntry,
) -> bool:
    """Set up this integration using UI."""
    setup_domain_data(hass)

    client = get_i_de_energy_api(hass, entry)

    try:
        contract_details = await client.get_contract_details()
    except (ideenergy.CommandError, ideenergy.UserExpiredError) as exc:
        raise ConfigEntryAuthFailed("i-DE rejected the configured credentials") from exc
    except ideenergy.ClientError as exc:
        raise ConfigEntryNotReady("Unable to connect to i-DE") from exc

    cups = str(contract_details["cups"])
    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=cups)

    device_info = get_i_de_energy_device_info(contract_details)

    config_entry_state = IDeEnergyConfigEntryState(hass, entry)
    await config_entry_state.async_load()

    coordinator = IDeEnergyDataCoordinator(
        hass=hass,
        client=client,
        config_entry_state=config_entry_state,
        update_interval=UPDATE_INTERVAL,
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = IntegrationIDeEnergyRunTimeData(
        coordinator=coordinator,
        integration=async_get_loaded_integration(hass, entry.domain),
        device_info=device_info,
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: IntegrationIDeEnergyConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


def get_i_de_energy_api(hass: HomeAssistant, entry: ConfigEntry):
    """Build the i-DE API client for a config entry."""
    if bool(os.environ.get("HASS_I_DE_MOCK", "")):
        client_cls = ideenergy.MockClient
    else:
        client_cls = ideenergy.Client

    return client_cls(
        session=async_create_clientsession(hass),
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        contract=entry.data[CONF_CONTRACT],
    )


def get_i_de_energy_device_info(contract_details):
    """Build Home Assistant device information for an i-DE contract."""
    return DeviceInfo(
        identifiers={
            ("cups", contract_details["cups"]),
        },
        name=contract_details["cups"],
        manufacturer=contract_details["listContador"][0]["tipMarca"],
    )
