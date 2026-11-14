"""Home Assistant Custom Component per Meteonetwork API."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_STATION_CODE, DOMAIN
from .coordinator import MeteonetworkDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# Definizioni sensori Meteonetwork
SENSOR_TYPES: dict[str, dict[str, Any]] = {
    "temperature": {
        "name": "Temperatura",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer",
    },
    "pressure": {
        "name": "Pressione",
        "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfPressure.HPA,
        "icon": "mdi:gauge",
    },
    "humidity": {
        "name": "Umidità",
        "device_class": SensorDeviceClass.HUMIDITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": PERCENTAGE,
        "icon": "mdi:water-percent",
    },
    "wind_speed": {
        "name": "Velocità Vento",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "icon": "mdi:weather-windy",
    },
    "wind_direction": {
        "name": "Direzione Vento",
        "device_class": None,
        "state_class": None,
        "unit": None,
        "icon": "mdi:compass-outline",
    },
    "wind_gust": {
        "name": "Raffiche Vento",
        "device_class": SensorDeviceClass.WIND_SPEED,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfSpeed.KILOMETERS_PER_HOUR,
        "icon": "mdi:weather-windy-variant",
    },
    "temp_min": {
        "name": "Temperatura Minima",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer-chevron-down",
    },
    "temp_max": {
        "name": "Temperatura Massima",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:thermometer-chevron-up",
    },
    "daily_rain": {
        "name": "Pioggia Giornaliera",
        "device_class": SensorDeviceClass.PRECIPITATION,
        "state_class": SensorStateClass.TOTAL_INCREASING,
        "unit": UnitOfPrecipitationDepth.MILLIMETERS,
        "icon": "mdi:weather-rainy",
    },
    "rain_rate": {
        "name": "Intensità Pioggia",
        "device_class": SensorDeviceClass.PRECIPITATION_INTENSITY,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        "icon": "mdi:weather-pouring",
    },
    "dew_point": {
        "name": "Punto di Rugiada",
        "device_class": SensorDeviceClass.TEMPERATURE,
        "state_class": SensorStateClass.MEASUREMENT,
        "unit": UnitOfTemperature.CELSIUS,
        "icon": "mdi:water-outline",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up sensors from a config entry created in the integrations UI."""
    coordinator: MeteonetworkDataUpdateCoordinator = entry.runtime_data

    sensors = [
        MeteonetworkSensor(coordinator, sensor_type, entry)
        for sensor_type in SENSOR_TYPES
    ]

    async_add_entities(sensors, update_before_add=False)


class MeteonetworkSensor(CoordinatorEntity[MeteonetworkDataUpdateCoordinator], SensorEntity):
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

        # Denominazione moderna: has_entity_name=True per UI pulita su scheda dispositivo,
        # e suggested_object_id per garantire entity_id tipo sensor.meteonetwork_temperatura
        self._attr_has_entity_name = True
        self._attr_name = self._sensor_config["name"]
        self._attr_suggested_object_id = f"meteonetwork_{slugify(self._sensor_config['name'])}"

        self._attr_unique_id = f"{entry.data[CONF_STATION_CODE]}_{sensor_type}"
        self._attr_device_class = self._sensor_config.get("device_class")
        self._attr_state_class = self._sensor_config.get("state_class")
        self._attr_native_unit_of_measurement = self._sensor_config.get("unit")
        self._attr_icon = self._sensor_config.get("icon")

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information."""
        station_name = "Unknown"
        if self.coordinator.data and isinstance(self.coordinator.data, dict):
            station_name = self.coordinator.data.get("place", "Unknown")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.data[CONF_STATION_CODE])},
            name=f"Stazione Meteonetwork {station_name}",
            manufacturer="Meteonetwork",
            model="Weather Station",
            configuration_url="https://www.meteonetwork.it/rete/livemap/",
        )

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return None

        value = self.coordinator.data.get(self._sensor_type)

        if value is None or value == "" or value == "--":
            return None

        if self._sensor_type == "wind_direction":
            return str(value)

        try:
            return float(value)
        except (ValueError, TypeError):
            return None
