"""The Meteonetwork integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import CONF_STATION_CODE, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import MeteonetworkDataUpdateCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR]

type MeteonetworkConfigEntry = ConfigEntry[MeteonetworkDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: MeteonetworkConfigEntry) -> bool:
    """Set up Meteonetwork from a config entry."""
    api_key = entry.data[CONF_API_KEY]
    station_code = entry.data[CONF_STATION_CODE]

    # Get scan interval from options first, then data, with fallback to default
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL,
        entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
    )
    scan_interval = timedelta(minutes=scan_interval_minutes)

    session = async_get_clientsession(hass)
    coordinator = MeteonetworkDataUpdateCoordinator(
        hass, session, api_key, station_code, scan_interval
    )

    # Fetch initial data. HA natively manages ConfigEntryNotReady and ConfigEntryAuthFailed
    await coordinator.async_config_entry_first_refresh()

    # Store coordinator in runtime_data
    entry.runtime_data = coordinator

    # Set up options update listener (auto deregistered on unload)
    entry.async_on_unload(entry.add_update_listener(options_update_listener))

    # Forward the setup to the sensor platform
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
    entry.runtime_data.update_interval = timedelta(minutes=scan_interval_minutes)
