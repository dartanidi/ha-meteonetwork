"""The Meteonetwork integration."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_SCAN_INTERVAL, CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .sensor import MeteonetworkDataUpdateCoordinator

DOMAIN = "meteonetwork"
CONF_STATION_CODE = "station_code"
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Meteonetwork from a config entry."""
    
    api_key = entry.data[CONF_API_KEY]
    station_code = entry.data[CONF_STATION_CODE]
    
    # Get scan interval from options first, then from data, with fallback to default
    scan_interval_minutes = entry.options.get(
        CONF_SCAN_INTERVAL, 
        entry.data.get(CONF_SCAN_INTERVAL, 5)
    )
    scan_interval = timedelta(minutes=scan_interval_minutes)
    
    session = async_get_clientsession(hass)
    coordinator = MeteonetworkDataUpdateCoordinator(hass, session, api_key, station_code, scan_interval)
    
    # Fetch initial data so we have data when entities subscribe
    # If this fails, raise ConfigEntryNotReady
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as err:
        raise ConfigEntryNotReady(f"Unable to connect to Meteonetwork API: {err}") from err
    
    # Store coordinator in hass data
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
    }
    
    # Set up options update listener
    unsub_options_update_listener = entry.add_update_listener(options_update_listener)
    hass.data[DOMAIN][entry.entry_id]["unsub_options_update_listener"] = unsub_options_update_listener
    
    # Forward the setup to the sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel the options update listener
    if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        unsub_options_update_listener = hass.data[DOMAIN][entry.entry_id].get(
            "unsub_options_update_listener"
        )
        if unsub_options_update_listener:
            unsub_options_update_listener()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN, None)
    
    return unload_ok


async def options_update_listener(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle options update."""
    # Reload the integration when options change
    await hass.config_entries.async_reload(config_entry.entry_id)
