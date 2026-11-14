"""Binary sensor platform for Meteonetwork integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_STATION_CODE, DOMAIN
from .coordinator import MeteonetworkDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Meteonetwork binary sensors."""
    coordinator: MeteonetworkDataUpdateCoordinator = entry.runtime_data

    async_add_entities(
        [MeteonetworkFallbackBinarySensor(coordinator, entry)],
        update_before_add=False,
    )


class MeteonetworkFallbackBinarySensor(
    CoordinatorEntity[MeteonetworkDataUpdateCoordinator], BinarySensorEntity
):
    """Binary sensor indicating if Meteonetwork fallback station is in use."""

    def __init__(
        self,
        coordinator: MeteonetworkDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the fallback binary sensor."""
        super().__init__(coordinator)
        self._entry = entry

        self._attr_has_entity_name = True
        self._attr_name = "Fallback Attivo"
        self._attr_suggested_object_id = "meteonetwork_fallback_attivo"
        self._attr_unique_id = f"{entry.data[CONF_STATION_CODE]}_fallback_active"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_icon = "mdi:swap-horizontal"

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
    def is_on(self) -> bool:
        """Return true if the fallback station is currently active."""
        if not self.coordinator.data:
            return False
        return bool(self.coordinator.data.get("is_fallback", False))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            "stazione_principale": self.coordinator.station_code,
            "stazione_fallback": self.coordinator.fallback_station_code,
            "stazione_attiva": self.coordinator.data.get("active_station_code")
            if self.coordinator.data
            else None,
        }
