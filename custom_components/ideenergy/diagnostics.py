# Copyright (C) 2021-2026 Luis López <luis@cuarentaydos.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.

"""Diagnostics support for i-DE Energy Monitor."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import CONF_CONTRACT
from .data import IntegrationIDeEnergyConfigEntry

TO_REDACT = {CONF_USERNAME, CONF_PASSWORD, CONF_CONTRACT}
REDACTED = "**REDACTED**"


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: IntegrationIDeEnergyConfigEntry
) -> dict[str, Any]:
    """Return diagnostics without exposing household energy data or identifiers."""
    coordinator = entry.runtime_data.coordinator

    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "unique_id": REDACTED if entry.unique_id else None,
        },
        "coordinator": {
            "last_update_success": coordinator.last_update_success,
            "active_datasets": sorted(
                name for name, count in coordinator.dataset_counter.items() if count > 0
            ),
            "available_datasets": sorted(
                dataset.name
                for dataset, value in coordinator.data.items()
                if value is not None
            ),
        },
    }
