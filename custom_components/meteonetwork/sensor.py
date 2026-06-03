"""
Home Assistant Custom Component per Meteonetwork API
"""
import asyncio
import logging
from datetime import timedelta
from typing import Any, Dict, Optional

import aiohttp
import async_timeout
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_API_KEY,
    CONF_SCAN_INTERVAL,
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfLength,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

_LOGGER = logging.getLogger(__name__)

DOMAIN = "meteonetwork"
CONF_STATION_CODE = "station_code"

# Default values
DEFAULT_SCAN_INTERVAL = timedelta(minutes=5)
TIMEOUT = 10

# Sensor definitions
SENSOR_TYPES = {
    "temperature": {
        "name": "Temperatura",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
        "key": "temperature",
    },
    "pressure": {
        "name": "Pressione",
        "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPressure.HPA,
        "icon": "mdi:gauge",
        "key": "smlp",
    },
    "humidity": {
        "name": "Umidità",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:water-percent",
        "key": "rh",
    },
    "wind_speed": {
        "name": "Velocità Vento",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "icon": "mdi:weather-windy",
        "key": "wind_speed",
    },
    "wind_direction": {
        "name": "Direzione Vento",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:compass-outline",
        "key": "wind_direction",
    },
    "wind_gust": {
        "name": "Raffiche Vento",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "icon": "mdi:weather-windy-variant",
        "key": "wind_gust",
    },
    "temp_min": {
        "name": "Temperatura Minima",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer-chevron-down",
        "key": "current_tmin",
    },
    "temp_max": {
        "name": "Temperatura Massima",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer-chevron-up",
        "key": "current_tmax",
    },
    "daily_rain": {
        "name": "Pioggia Giornaliera",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfLength.MILLIMETERS,
        "icon": "mdi:weather-rainy",
        "key": "daily_rain",
    },
    "rain_rate": {
        "name": "Intensità Pioggia",
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": f"{UnitOfLength.MILLIMETERS}/h",
        "icon": "mdi:weather-pouring",
        "key": "rain_rate",
    },
    "dew_point": {
        "name": "Punto di Rugiada",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:water-outline",
        "key": "dew_point",
    },
}


class MeteonetworkDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Meteonetwork API."""

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession,
        api_key: str,
        station_code: str,
        scan_interval: timedelta,
    ) -> None:
        """Initialize."""
        self.api_key = api_key
        self.station_code = station_code
        self.session = session
        self.api_url = f"https://api.meteonetwork.it/v3/data-realtime/{station_code}"

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=scan_interval,
        )
        
    async def _async_update_data(self) -> Dict[str, Any]:
        """Update data via library."""
        try:
            async with async_timeout.timeout(TIMEOUT):
                headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                }
                
                async with self.session.get(self.api_url, headers=headers) as response:
                    if response.status == 401:
                        raise ConfigEntryAuthFailed("Invalid API key")
                    
                    if response.status != 200:
                        raise UpdateFailed(f"Error communicating with API: {response.status}")
                    
                    data = await response.json()
                    
                    if not data or len(data) == 0:
                        raise UpdateFailed("No data received from API")
                    
                    station_data = data[0]
                    
                    # Process and return the data
                    processed_data = {
                        "place": station_data.get("place", ""),
                        "altitude": station_data.get("altitude", ""),
                        "latitude": station_data.get("latitude", 0),
                        "longitude": station_data.get("longitude", 0),
                    }
                    
                    # Add sensor data
                    for sensor_type, config in SENSOR_TYPES.items():
                        processed_data[sensor_type] = station_data.get(config["key"], 0)
                    
                    return processed_data

        except asyncio.TimeoutError as exception:
            raise UpdateFailed(f"Timeout communicating with API: {exception}")
        except Exception as exception:
            raise UpdateFailed(f"Error communicating with API: {exception}")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Setup sensors from a config entry created in the integrations UI."""
    
    # Get the coordinator from the stored data
    coordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    
    sensors = []
    for sensor_type in SENSOR_TYPES:
        sensors.append(MeteonetworkSensor(coordinator, sensor_type, entry))
    
    async_add_entities(sensors, update_before_add=True)


class MeteonetworkSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Meteonetwork sensor."""

    def __init__(
        self,
        coordinator: MeteonetworkDataUpdateCoordinator,
        sensor_type: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        
        self._sensor_type = sensor_type
        self._sensor_config = SENSOR_TYPES[sensor_type]
        self._entry = entry
        
        # --- FIX DENOMINAZIONE PULITA (sensor.meteonetwork_xxxx) ---
        self._attr_has_entity_name = True
        self._attr_name = self._sensor_config['name'] 
        
        self._attr_unique_id = f"{entry.data[CONF_STATION_CODE]}_{sensor_type}"
        self._attr_device_class = self._sensor_config.get("device_class")
        self._attr_state_class = self._sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = self._sensor_config.get("unit")
        self._attr_icon = self._sensor_config.get("icon")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data[CONF_STATION_CODE])},
            name=f"Stazione Meteonetwork {self.coordinator.data.get('place', 'Unknown')}",
            manufacturer="Meteonetwork",
            model="Weather Station",
            sw_version="1.0",
        )

    @property
    def native_value(self) -> Optional[float]:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None
        
        value = self.coordinator.data.get(self._sensor_type)
        
        # Handle special cases
        if value is None or value == "":
            return None
        
        if self._sensor_type == "wind_direction" and isinstance(value, str):
            return value
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.data:
            return {}
        
        attrs = {
            "stazione": self.coordinator.data.get("place", ""),
            "altitudine": self.coordinator.data.get("altitude", ""),
            "latitude": self.coordinator.data.get("latitude", 0),
            "longitude": self.coordinator.data.get("longitude", 0),
            "codice_stazione": self._entry.data[CONF_STATION_CODE],
        }
        
        return attrs

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
