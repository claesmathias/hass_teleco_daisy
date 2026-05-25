from __future__ import annotations

import logging

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from ._lib import DaisyHeater4CH

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    hub = hass.data[DOMAIN][config_entry.entry_id]
    async_add_entities([TelecoDaisyClimateEntity(heater) for heater in hub.heaters])


class TelecoDaisyClimateEntity(ClimateEntity):
    _attr_hvac_modes = [HVACMode.HEAT, HVACMode.OFF]
    _attr_supported_features = (
        ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = ["50", "75", "100"]
    _attr_temperature_unit = UnitOfTemperature.CELSIUS

    def __init__(self, heater: DaisyHeater4CH) -> None:
        self._heater = heater
        self._attr_unique_id = str(heater.idInstallationDevice)
        self._attr_name = heater.label
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_preset_mode: str | None = None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self._attr_name,
            manufacturer="Teleco Automation",
        )

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        if hvac_mode == HVACMode.HEAT:
            self._heater.turn_on()
        else:
            self._heater.turn_off()
        self._attr_hvac_mode = hvac_mode

    def turn_on(self) -> None:
        self.set_hvac_mode(HVACMode.HEAT)

    def turn_off(self) -> None:
        self.set_hvac_mode(HVACMode.OFF)

    def set_preset_mode(self, preset_mode: str) -> None:
        self._heater.set_level(preset_mode)
        self._attr_preset_mode = preset_mode
