"""DataUpdateCoordinator for Meteonetwork integration."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import API_BASE_URL, API_TIMEOUT, DOMAIN, SENSOR_KEY_MAP

_LOGGER = logging.getLogger(__name__)


class MeteonetworkDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Meteonetwork API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        station_code: str,
        scan_interval: timedelta,
    ) -> None:
        """Initialize coordinator."""
        self.api_key = api_key
        self.station_code = station_code
        self.session = session
        self.api_url = f"{API_BASE_URL}/{station_code}"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Meteonetwork API."""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with asyncio.timeout(API_TIMEOUT):
                async with self.session.get(self.api_url, headers=headers) as response:
                    if response.status == 401:
                        raise ConfigEntryAuthFailed("Invalid API key")

                    if response.status != 200:
                        raise UpdateFailed(
                            f"Error communicating with API: status {response.status}"
                        )

                    data = await response.json()

                    if not isinstance(data, list) or len(data) == 0:
                        raise UpdateFailed("No valid data received from Meteonetwork API")

                    station_data = data[0]
                    if not isinstance(station_data, dict):
                        raise UpdateFailed("Malformed station data received from API")

                    processed_data: dict[str, Any] = {
                        "place": station_data.get("place", ""),
                        "altitude": station_data.get("altitude", ""),
                        "latitude": station_data.get("latitude", 0),
                        "longitude": station_data.get("longitude", 0),
                    }

                    for sensor_type, api_key in SENSOR_KEY_MAP.items():
                        processed_data[sensor_type] = station_data.get(api_key)

                    return processed_data

        except ConfigEntryAuthFailed:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error fetching Meteonetwork data: %s", err)
            raise UpdateFailed(f"Unexpected error: {err}") from err
