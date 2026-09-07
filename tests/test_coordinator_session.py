"""Tests for passive coordinator session handling."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import ideenergy
import pytest
from homeassistant.core import dt_util
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.ideenergy.coordinator import (
    DIRECT_READING_LAST_ATTEMPT_STORED_STATE_KEY,
    DIRECT_READING_LAST_SUCCESS_STORED_STATE_KEY,
    MEASURE_ACCUMULATED_KEY,
    MEASURE_INSTANT_KEY,
    IDeEnergyCoordinatorDataSet,
    IDeEnergyDataCoordinator,
)

pytestmark = pytest.mark.asyncio


def make_client(*, is_logged: bool = False):
    """Create a minimal client double for coordinator tests."""
    return SimpleNamespace(
        is_logged=is_logged,
        login=AsyncMock(),
        renew_session=AsyncMock(),
        get_measure=AsyncMock(),
        get_historical_consumption=AsyncMock(),
        get_historical_generation=AsyncMock(),
        get_historical_power_demand=AsyncMock(),
    )


def make_state(data=None):
    """Create an in-memory persisted-state double."""
    return SimpleNamespace(data=data or {}, async_save=AsyncMock())


def make_coordinator(hass, client, state):
    return IDeEnergyDataCoordinator(
        hass=hass,
        client=client,
        config_entry_state=state,
    )


async def test_idle_coordinator_makes_no_client_calls(hass):
    client = make_client()
    coordinator = make_coordinator(hass, client, make_state())

    await coordinator._async_update_data()

    client.login.assert_not_awaited()
    client.renew_session.assert_not_awaited()
    client.get_measure.assert_not_awaited()
    client.get_historical_consumption.assert_not_awaited()
    client.get_historical_generation.assert_not_awaited()
    client.get_historical_power_demand.assert_not_awaited()


async def test_throttled_dataset_does_not_authenticate(hass):
    client = make_client()
    state = make_state(
        {
            DIRECT_READING_LAST_SUCCESS_STORED_STATE_KEY: dt_util.as_timestamp(
                dt_util.now()
            )
        }
    )
    coordinator = make_coordinator(hass, client, state)
    coordinator.dataset_counter[IDeEnergyCoordinatorDataSet.DIRECT_READING.name] = 1

    await coordinator._async_update_data()

    client.login.assert_not_awaited()
    client.renew_session.assert_not_awaited()
    client.get_measure.assert_not_awaited()


async def test_due_dataset_logs_in_only_for_real_request(hass):
    client = make_client(is_logged=False)
    client.get_measure.return_value = ideenergy.Measure(accumulate=123, instant=4.5)
    state = make_state()
    coordinator = make_coordinator(hass, client, state)
    coordinator.dataset_counter[IDeEnergyCoordinatorDataSet.DIRECT_READING.name] = 1

    data = await coordinator._async_update_data()

    client.login.assert_awaited_once_with()
    client.renew_session.assert_not_awaited()
    client.get_measure.assert_awaited_once_with()
    assert data[IDeEnergyCoordinatorDataSet.DIRECT_READING] == {
        MEASURE_ACCUMULATED_KEY: 123,
        MEASURE_INSTANT_KEY: 4.5,
    }
    assert DIRECT_READING_LAST_SUCCESS_STORED_STATE_KEY in state.data


async def test_403_reauthenticates_once_and_retries_once(hass):
    response = Mock(status=403, reason="Forbidden")
    client = make_client(is_logged=True)
    client.get_measure.side_effect = [
        ideenergy.RequestFailedError(response),
        ideenergy.Measure(accumulate=321, instant=1.25),
    ]
    state = make_state()
    coordinator = make_coordinator(hass, client, state)
    coordinator.dataset_counter[IDeEnergyCoordinatorDataSet.DIRECT_READING.name] = 1

    data = await coordinator._async_update_data()

    client.login.assert_awaited_once_with()
    assert client.get_measure.await_count == 2
    assert (
        data[IDeEnergyCoordinatorDataSet.DIRECT_READING][MEASURE_ACCUMULATED_KEY] == 321
    )


async def test_503_becomes_update_failed_and_records_attempt(hass):
    response = Mock(status=503, reason="Service Unavailable")
    client = make_client(is_logged=True)
    client.get_measure.side_effect = ideenergy.RequestFailedError(response)
    state = make_state()
    coordinator = make_coordinator(hass, client, state)
    coordinator.dataset_counter[IDeEnergyCoordinatorDataSet.DIRECT_READING.name] = 1

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()

    client.login.assert_not_awaited()
    client.renew_session.assert_not_awaited()
    client.get_measure.assert_awaited_once_with()
    assert DIRECT_READING_LAST_ATTEMPT_STORED_STATE_KEY in state.data
    assert DIRECT_READING_LAST_SUCCESS_STORED_STATE_KEY not in state.data


async def test_unchanged_data_does_not_notify_listeners(hass):
    client = make_client()
    coordinator = make_coordinator(hass, client, make_state())
    listener = Mock()
    remove_listener = coordinator.async_add_listener(listener)

    await coordinator.async_refresh()
    listener.reset_mock()
    await coordinator.async_refresh()

    listener.assert_not_called()
    client.login.assert_not_awaited()
    client.renew_session.assert_not_awaited()
    remove_listener()
