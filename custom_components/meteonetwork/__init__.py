"""The Meteonetwork integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_FALLBACK_STATION_CODE,
    CONF_STALE_THRESHOLD,
    CONF_STATION_CODE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STALE_THRESHOLD_MINUTES,
    DOMAIN,
)
from .coordinator import MeteonetworkDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]

type MeteonetworkConfigEntry = ConfigEntry[MeteonetworkDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MeteonetworkConfigEntry) -> bool:
    """Set up Meteonetwork from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    station_code = entry.data[CONF_STATION_CODE]

    # Get scan interval and fallback settings from options first, then data
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    scan_interval = timedelta(minutes=scan_interval_minutes)

    fallback_station_code = entry.options.get(
        CONF_FALLBACK_STATION_CODE,
        entry.data.get(CONF_FALLBACK_STATION_CODE),
    )
    stale_threshold_minutes = entry.options.get(
        CONF_STALE_THRESHOLD,
        entry.data.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD_MINUTES),
    )

    session = async_get_clientsession(hass)
    coordinator = MeteonetworkDataUpdateCoordinator(
        hass,
        session,
        api_key,
        station_code,
        scan_interval,
        fallback_station_code=fallback_station_code,
        stale_threshold_minutes=stale_threshold_minutes,
    )

    # Fetch initial data. HA natively manages ConfigEntryNotReady and ConfigEntryAuthFailed
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in runtime_data
    entry.runtime_data = coordinator

    # Set up options update listener (auto deregistered on unload)
    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    # Forward the setup to the platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MeteonetworkConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def options_update_listener(hass: HomeAssistant, entry: MeteonetworkConfigEntry) -> None:
    """Handle options update without full reload."""
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    fallback_station_code = entry.options.get(
        CONF_FALLBACK_STATION_CODE,
        entry.data.get(CONF_FALLBACK_STATION_CODE),
    )
    stale_threshold_minutes = entry.options.get(
        CONF_STALE_THRESHOLD,
        entry.data.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD_MINUTES),
    )

    coordinator = entry.runtime_data
    coordinator.update_interval = timedelta(minutes=scan_interval_minutes)
    coordinator.fallback_station_code = (
        fallback_station_code.strip().lower() if fallback_station_code else None
    )
    coordinator.stale_threshold_minutes = stale_threshold_minutes
