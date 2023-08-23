"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import DOMAIN


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    sensors = hass.data[DOMAIN]["sensors"]
    for sensor in sensors:
        add_entities(
            [LinkySensor(hass, sensor["name"], sensor["unit"])], update_before_add=True
        )
    return True


class LinkySensor(SensorEntity):
    """Representation of a sensor."""

    def __init__(self, hass: HomeAssistant, name, unit) -> None:
        """Initialize the sensor."""
        self._state = 0
        self._name = name
        self._unit = unit
        self.hass = hass
        self._attr = {}

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._name

    @property
    def unique_id(self) -> str:
        return self._name

    @property
    def device_class(self) -> str:
        if self._name == "Linky energy hours":
            return
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self) -> str:
        if self._name == "Linky energy hours":
            return
        return SensorStateClass.TOTAL_INCREASING

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self._unit

    @property
    def attribution(self) -> str | None:
        if self._name == "Linky energy hours":
            return self._attr
        return super().attribution

    def update(self) -> None:
        sensors_data = self.hass.data[DOMAIN]["sensors"]
        for sensor_data in sensors_data:
            if sensor_data["name"] == self._name:
                if self._name == "Linky energy hours":
                    self._state = "New value"
                    self._attr = sensor_data["value"]
                else:
                    self._state = sensor_data["value"]
                break
