"""DataUpdateCoordinator for Meteonetwork integration with fallback support."""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    DEFAULT_STALE_THRESHOLD_MINUTES,
    DOMAIN,
    SENSOR_KEY_MAP,
)

_LOGGER = logging.getLogger(__name__)


def parse_observation_time(time_str: str) -> datetime | None:
    """Parse API observation time string into a timezone-aware datetime."""
    if not time_str or not isinstance(time_str, str):
        return None
    cleaned = time_str.strip()
    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S%z",
    ):
        try:
            dt = datetime.strptime(cleaned, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass
    return None


class MeteonetworkDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching data from the Meteonetwork API with fallback support."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        station_code: str,
        scan_interval: timedelta,
        fallback_station_code: str | None = None,
        stale_threshold_minutes: int = DEFAULT_STALE_THRESHOLD_MINUTES,
    ) -> None:
        """Initialize coordinator."""
        self.api_key = api_key
        self.station_code = station_code.strip().lower()
        self.fallback_station_code = (
            fallback_station_code.strip().lower() if fallback_station_code else None
        )
        self.stale_threshold_minutes = stale_threshold_minutes
        self.session = session

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )

    @property
    def is_fallback_active(self) -> bool:
        """Return whether fallback station is currently active."""
        if not self.data:
            return False
        return bool(self.data.get("is_fallback", False))

    async def _async_fetch_station_data(self, station_code: str) -> dict[str, Any] | None:
        """Fetch and parse data for a specific station from the API."""
        url = f"{API_BASE_URL}/{station_code}"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with asyncio.timeout(API_TIMEOUT):
            async with self.session.get(url, headers=headers) as response:
                if response.status == 401:
                    raise ConfigEntryAuthFailed("Invalid API key")

                if response.status != 200:
                    _LOGGER.warning(
                        "Meteonetwork station %s returned HTTP status %s",
                        station_code,
                        response.status,
                    )
                    return None

                data = await response.json()
                if not isinstance(data, list) or len(data) == 0:
                    _LOGGER.warning("Meteonetwork station %s returned empty data", station_code)
                    return None

                station_data = data[0]
                if not isinstance(station_data, dict):
                    _LOGGER.warning("Meteonetwork station %s returned malformed data", station_code)
                    return None

                return station_data

    def _is_station_data_valid_and_fresh(
        self, station_data: dict[str, Any] | None, station_code: str
    ) -> bool:
        """Check if station data is present, contains readings, and is not stale."""
        if not station_data or not isinstance(station_data, dict):
            return False

        # Staleness check based on observation timestamp
        obs_time_str = station_data.get("observation_time_utc") or station_data.get(
            "observation_time_local"
        )
        if obs_time_str:
            dt_obs = parse_observation_time(obs_time_str)
            if dt_obs:
                now_utc = datetime.now(timezone.utc)
                age_minutes = (now_utc - dt_obs).total_seconds() / 60
                if age_minutes > self.stale_threshold_minutes:
                    _LOGGER.warning(
                        "Station %s data is stale (last update: %s, age: %.1f min > threshold %d min)",
                        station_code,
                        obs_time_str,
                        age_minutes,
                        self.stale_threshold_minutes,
                    )
                    return False

        # Sensor readings presence check
        readings = [station_data.get(api_key) for api_key in SENSOR_KEY_MAP.values()]
        if all(v is None or v == "" or v == "--" for v in readings):
            _LOGGER.warning("Station %s has no active sensor readings", station_code)
            return False

        return True

    def _process_station_data(
        self, station_data: dict[str, Any], station_code: str, is_fallback: bool
    ) -> dict[str, Any]:
        """Format station data dictionary for entities."""
        processed: dict[str, Any] = {
            "place": station_data.get("place", ""),
            "altitude": station_data.get("altitude", ""),
            "latitude": station_data.get("latitude", 0),
            "longitude": station_data.get("longitude", 0),
            "observation_time_local": station_data.get("observation_time_local", ""),
            "observation_time_utc": station_data.get("observation_time_utc", ""),
            "active_station_code": station_code,
            "is_fallback": is_fallback,
        }

        for sensor_type, api_key in SENSOR_KEY_MAP.items():
            processed[sensor_type] = station_data.get(api_key)

        return processed

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from primary station with automatic fallback if offline or stale."""
        primary_data = None
        primary_error = None

        # 1. Attempt to fetch primary station
        try:
            primary_data = await self._async_fetch_station_data(self.station_code)
        except ConfigEntryAuthFailed:
            raise
        except (aiohttp.ClientError, asyncio.TimeoutError) as err:
            primary_error = err
            _LOGGER.warning("Communication error with primary station %s: %s", self.station_code, err)
        except Exception as err:
            primary_error = err
            _LOGGER.exception("Unexpected error fetching primary station %s: %s", self.station_code, err)

        if self._is_station_data_valid_and_fresh(primary_data, self.station_code):
            if self.is_fallback_active:
                _LOGGER.info(
                    "Primary station %s is back online. Restoring primary data.",
                    self.station_code,
                )
            return self._process_station_data(primary_data, self.station_code, is_fallback=False)

        # 2. Primary is offline, stale, or errored -> try fallback station if configured
        if self.fallback_station_code:
            _LOGGER.warning(
                "Primary station %s is offline or stale. Switching to fallback station %s",
                self.station_code,
                self.fallback_station_code,
            )
            fallback_data = None
            try:
                fallback_data = await self._async_fetch_station_data(self.fallback_station_code)
            except ConfigEntryAuthFailed:
                raise
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.error(
                    "Communication error with fallback station %s: %s",
                    self.fallback_station_code,
                    err,
                )
            except Exception as err:
                _LOGGER.exception(
                    "Unexpected error fetching fallback station %s: %s",
                    self.fallback_station_code,
                    err,
                )

            if self._is_station_data_valid_and_fresh(fallback_data, self.fallback_station_code):
                return self._process_station_data(
                    fallback_data, self.fallback_station_code, is_fallback=True
                )

        # 3. Neither station provided valid data
        if primary_error:
            raise UpdateFailed(f"Primary station {self.station_code} failed ({primary_error}) and fallback unavailable")

        raise UpdateFailed(
            f"Primary station {self.station_code} is offline or stale and no valid fallback data available"
        )
