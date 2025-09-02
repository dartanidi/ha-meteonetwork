"""Config flow for Meteonetwork integration."""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "meteonetwork"
CONF_STATION_CODE = "station_code"

# Default scan interval in minutes
DEFAULT_SCAN_INTERVAL = 5
MIN_SCAN_INTERVAL = 1
MAX_SCAN_INTERVAL = 60

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_STATION_CODE): str,
        vol.Required(CONF_API_KEY): str,
        vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
        ),
    }
)


class PlaceholderHub:
    """Placeholder class to make tests pass."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize."""
        self.hass = hass

    async def authenticate(self, api_key: str, station_code: str) -> dict[str, Any]:
        """Test if we can authenticate with the host."""
        try:
            session = async_get_clientsession(self.hass)
            url = f"https://api.meteonetwork.it/v3/data-realtime/{station_code}"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            }
            
            async with async_timeout.timeout(10):
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        if isinstance(data, list) and len(data) > 0:
                            station_data = data[0]
                            return {
                                "success": True,
                                "station_name": station_data.get("place", f"Stazione {station_code}"),
                                "latitude": station_data.get("latitude", "N/A"),
                                "longitude": station_data.get("longitude", "N/A"),
                                "altitude": station_data.get("altitude", "N/A"),
                            }
                        else:
                            _LOGGER.warning(f"API returned empty or invalid data: {data}")
                            return {"success": False, "error": "no_data"}
                    elif response.status == 401:
                        return {"success": False, "error": "invalid_auth"}
                    elif response.status == 404:
                        return {"success": False, "error": "station_not_found"}
                    else:
                        _LOGGER.warning(f"API returned status {response.status}")
                        return {"success": False, "error": "cannot_connect"}
        except async_timeout.TimeoutError:
            _LOGGER.warning("Timeout connecting to Meteonetwork API")
            return {"success": False, "error": "timeout"}
        except aiohttp.ClientError as err:
            _LOGGER.warning(f"Client error: {err}")
            return {"success": False, "error": "cannot_connect"}
        except Exception as err:
            _LOGGER.exception(f"Unexpected exception during authentication: {err}")
            return {"success": False, "error": "unknown"}


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    hub = PlaceholderHub(hass)
    result = await hub.authenticate(data[CONF_API_KEY], data[CONF_STATION_CODE])
    
    if not result["success"]:
        if result["error"] == "invalid_auth":
            raise InvalidAuth
        elif result["error"] == "station_not_found":
            raise StationNotFound
        elif result["error"] == "timeout":
            raise CannotConnect("Timeout durante la connessione")
        elif result["error"] == "no_data":
            raise CannotConnect("La stazione non ha restituito dati")
        else:
            raise CannotConnect("Impossibile connettersi all'API")

    # Return info that you want to store in the config entry.
    return {
        "title": f"{result['station_name']} ({data[CONF_STATION_CODE]})",
        "station_info": result,
    }


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Meteonetwork."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", 
                data_schema=STEP_USER_DATA_SCHEMA,
                description_placeholders={
                    "scan_interval_range": f"{MIN_SCAN_INTERVAL}-{MAX_SCAN_INTERVAL} minuti"
                }
            )

        errors = {}

        try:
            # Check if the station is already configured
            await self.async_set_unique_id(user_input[CONF_STATION_CODE])
            self._abort_if_unique_id_configured()
            
            info = await validate_input(self.hass, user_input)
        except StationNotFound:
            errors["station_code"] = "station_not_found"
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["api_key"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", 
            data_schema=STEP_USER_DATA_SCHEMA, 
            errors=errors,
            description_placeholders={
                "scan_interval_range": f"{MIN_SCAN_INTERVAL}-{MAX_SCAN_INTERVAL} minuti"
            }
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Meteonetwork."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        # Don't store config_entry explicitly - it's deprecated
        pass

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SCAN_INTERVAL,
                    default=self.config_entry.options.get(
                        CONF_SCAN_INTERVAL,
                        self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
                    ),
                ): vol.All(
                    vol.Coerce(int), 
                    vol.Range(min=MIN_SCAN_INTERVAL, max=MAX_SCAN_INTERVAL)
                ),
            }
        )

        return self.async_show_form(
            step_id="init", 
            data_schema=options_schema,
            description_placeholders={
                "scan_interval_range": f"{MIN_SCAN_INTERVAL}-{MAX_SCAN_INTERVAL} minuti"
            }
        )


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class StationNotFound(HomeAssistantError):
    """Error to indicate the station was not found."""
