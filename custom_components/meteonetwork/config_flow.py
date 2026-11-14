"""Config flow for Meteonetwork integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import (
    API_BASE_URL,
    API_TIMEOUT,
    CONF_FALLBACK_STATION_CODE,
    CONF_STALE_THRESHOLD,
    CONF_STATION_CODE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_STALE_THRESHOLD_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL,
    MAX_STALE_THRESHOLD_MINUTES,
    MIN_SCAN_INTERVAL,
    MIN_STALE_THRESHOLD_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_CODE): str,
        vol.Required(CONF_API_KEY): TextSelector(
            TextSelectorConfig(type=TextSelectorType.PASSWORD)
        ),
        vol.Optional(CONF_FALLBACK_STATION_CODE, default=""): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): NumberSelector(
            NumberSelectorConfig(
                min=MIN_SCAN_INTERVAL,
                max=MAX_SCAN_INTERVAL,
                step=1,
                unit_of_measurement="min",
                mode=NumberSelectorMode.BOX,
            )
        ),
        vol.Optional(
            CONF_STALE_THRESHOLD, default=DEFAULT_STALE_THRESHOLD_MINUTES
        ): NumberSelector(
            NumberSelectorConfig(
                min=MIN_STALE_THRESHOLD_MINUTES,
                max=MAX_STALE_THRESHOLD_MINUTES,
                step=5,
                unit_of_measurement="min",
                mode=NumberSelectorMode.BOX,
            )
        ),
    }
)


class MeteonetworkHub:
    """Client helper for verifying connection during config flow."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        self.hass = hass

    async def authenticate(
        self, api_key: str, station_code: str, retry_on_429: bool = True
    ) -> dict[str, Any]:
        """Test authentication with the Meteonetwork API with automatic 429 throttling."""
        try:
            session = async_get_clientsession(self.hass)
            url = f"{API_BASE_URL}/{station_code}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }

            async with asyncio.timeout(API_TIMEOUT):
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                            station_data = data[0]
                            return {
                                "success": True,
                                "station_name": station_data.get(
                                    "place", f"Stazione {station_code.upper()}"
                                ),
                                "latitude": station_data.get("latitude", 0),
                                "longitude": station_data.get("longitude", 0),
                                "altitude": station_data.get("altitude", ""),
                            }
                        _LOGGER.warning("API returned empty or invalid data: %s", data)
                        return {"success": False, "error": "no_data"}

                    if response.status == 401:
                        return {"success": False, "error": "invalid_auth"}

                    if response.status == 404:
                        return {"success": False, "error": "station_not_found"}

                    if response.status == 429:
                        if retry_on_429:
                            retry_after = 2
                            try:
                                retry_after = max(int(response.headers.get("Retry-After", 2)), 2)
                            except (ValueError, TypeError):
                                retry_after = 2
                            _LOGGER.warning(
                                "Rate limit Meteonetwork raggiunto (HTTP 429). Attesa di %s secondi prima di ritentare...",
                                retry_after,
                            )
                            await asyncio.sleep(retry_after)
                            return await self.authenticate(api_key, station_code, retry_on_429=False)

                        _LOGGER.warning("Rate limit Meteonetwork (HTTP 429) persistente.")
                        return {"success": False, "error": "rate_limited"}

                    _LOGGER.warning("API returned status %s", response.status)
                    return {"success": False, "error": "cannot_connect"}

        except asyncio.TimeoutError:
            _LOGGER.warning("Timeout connecting to Meteonetwork API")
            return {"success": False, "error": "timeout"}
        except aiohttp.ClientError as err:
            _LOGGER.warning("Client error connecting to Meteonetwork API: %s", err)
            return {"success": False, "error": "cannot_connect"}
        except Exception as err:
            _LOGGER.exception("Unexpected exception during Meteonetwork authentication: %s", err)
            return {"success": False, "error": "unknown"}


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by authenticating against the API."""
    hub = MeteonetworkHub(hass)
    station_code = data[CONF_STATION_CODE].strip().lower()
    api_key = data[CONF_API_KEY].strip()
    fallback_station_code = data.get(CONF_FALLBACK_STATION_CODE, "").strip().lower()

    if fallback_station_code and fallback_station_code == station_code:
        raise SameStation

    result = await hub.authenticate(api_key, station_code)

    if not result["success"]:
        if result["error"] == "invalid_auth":
            raise InvalidAuth
        if result["error"] == "station_not_found":
            raise StationNotFound
        if result["error"] == "timeout":
            raise TimeoutConnect
        if result["error"] == "no_data":
            raise NoData
        if result["error"] == "rate_limited":
            raise RateLimited
        raise CannotConnect("Impossibile connettersi all'API Meteonetwork")

    # If fallback station was specified, pause 1.5s to respect the 1 req/sec rate limit
    if fallback_station_code:
        await asyncio.sleep(1.5)
        fallback_res = await hub.authenticate(api_key, fallback_station_code)
        if not fallback_res["success"]:
            if fallback_res.get("error") == "rate_limited":
                raise RateLimited
            raise FallbackStationNotFound

    return {
        "title": f"{result['station_name']} ({station_code.upper()})",
        "station_info": result,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteonetwork."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial user step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=STEP_USER_DATA_SCHEMA,
            )

        errors = {}

        station_code = user_input[CONF_STATION_CODE].strip().lower()
        api_key = user_input[CONF_API_KEY].strip()
        fallback_station_code = user_input.get(CONF_FALLBACK_STATION_CODE, "").strip().lower()
        scan_interval = user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        stale_threshold = user_input.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD_MINUTES)

        try:
            # Check if primary station is already configured
            await self.async_set_unique_id(station_code)
            self._abort_if_unique_id_configured()

            info = await validate_input(
                self.hass,
                {
                    CONF_STATION_CODE: station_code,
                    CONF_API_KEY: api_key,
                    CONF_FALLBACK_STATION_CODE: fallback_station_code,
                },
            )
        except SameStation:
            errors["fallback_station_code"] = "same_station"
        except FallbackStationNotFound:
            errors["fallback_station_code"] = "fallback_station_not_found"
        except StationNotFound:
            errors["station_code"] = "station_not_found"
        except InvalidAuth:
            errors["api_key"] = "invalid_auth"
        except TimeoutConnect:
            errors["base"] = "timeout"
        except NoData:
            errors["base"] = "no_data"
        except RateLimited:
            errors["base"] = "rate_limited"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception in config flow")
            errors["base"] = "unknown"
        else:
            clean_data = {
                CONF_STATION_CODE: station_code,
                CONF_API_KEY: api_key,
            }
            options = {
                CONF_SCAN_INTERVAL: scan_interval,
                CONF_FALLBACK_STATION_CODE: fallback_station_code,
                CONF_STALE_THRESHOLD: stale_threshold,
            }
            return self.async_create_entry(
                title=info["title"],
                data=clean_data,
                options=options,
            )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Meteonetwork."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            fallback_station_code = user_input.get(CONF_FALLBACK_STATION_CODE, "").strip().lower()
            primary_station = self.config_entry.data.get(CONF_STATION_CODE, "").strip().lower()
            api_key = self.config_entry.data.get(CONF_API_KEY, "").strip()

            if fallback_station_code:
                if fallback_station_code == primary_station:
                    errors["fallback_station_code"] = "same_station"
                else:
                    hub = MeteonetworkHub(self.hass)
                    res = await hub.authenticate(api_key, fallback_station_code)
                    if not res["success"]:
                        if res.get("error") == "rate_limited":
                            errors["base"] = "rate_limited"
                        else:
                            errors["fallback_station_code"] = "fallback_station_not_found"

            if not errors:
                clean_options = {
                    CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    CONF_FALLBACK_STATION_CODE: fallback_station_code,
                    CONF_STALE_THRESHOLD: user_input.get(
                        CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD_MINUTES
                    ),
                }
                return self.async_create_entry(title="", data=clean_options)

        current_scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
        )
        current_fallback = self.config_entry.options.get(
            CONF_FALLBACK_STATION_CODE,
            self.config_entry.data.get(CONF_FALLBACK_STATION_CODE, ""),
        )
        current_stale_threshold = self.config_entry.options.get(
            CONF_STALE_THRESHOLD,
            self.config_entry.data.get(CONF_STALE_THRESHOLD, DEFAULT_STALE_THRESHOLD_MINUTES),
        )

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_FALLBACK_STATION_CODE,
                    default=current_fallback,
                ): str,
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=current_scan_interval,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL,
                        max=MAX_SCAN_INTERVAL,
                        step=1,
                        unit_of_measurement="min",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
                vol.Optional(
                    CONF_STALE_THRESHOLD,
                    default=current_stale_threshold,
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_STALE_THRESHOLD_MINUTES,
                        max=MAX_STALE_THRESHOLD_MINUTES,
                        step=5,
                        unit_of_measurement="min",
                        mode=NumberSelectorMode.BOX,
                    )
                ),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
            errors=errors,
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class TimeoutConnect(HomeAssistantError):
    """Error to indicate connection timed out."""


class NoData(HomeAssistantError):
    """Error to indicate API returned no data."""


class RateLimited(HomeAssistantError):
    """Error to indicate API rate limit (HTTP 429) was reached."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class StationNotFound(HomeAssistantError):
    """Error to indicate the station was not found."""


class FallbackStationNotFound(HomeAssistantError):
    """Error to indicate the fallback station was not found."""


class SameStation(HomeAssistantError):
    """Error to indicate fallback station is identical to primary station."""
