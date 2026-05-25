from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

import teleco_daisy as _lib
from teleco_daisy import DaisyCover, DaisyHeater4CH, DaisyLight, TelecoDaisy

_LOGGER = logging.getLogger(__name__)


class DaisyHub(TelecoDaisy):
    manufacturer = "Teleco Automation"
    lights: list[DaisyLight]
    covers: list[DaisyCover]
    heaters: list[DaisyHeater4CH]

    def __init__(self, hass: HomeAssistant, email: str, password: str) -> None:
        super().__init__(email, password)

        self._hass = hass
        self._name = "Teleco DaisyHub"
        self._id = "Teleco DaisyHub".lower()

        self.online = True

        _LOGGER.debug(
            "DaisyHub created, teleco_daisy library version: %s",
            getattr(_lib, "__version__", "unknown"),
        )

    def fetch_entities(self):
        self.lights = []
        self.covers = []
        self.heaters = []

        _LOGGER.debug("fetch_entities: starting installation discovery")
        installations = self.get_installations()
        _LOGGER.debug("fetch_entities: found %d installation(s)", len(installations))

        for installation in installations:
            _LOGGER.debug("fetch_entities: processing installation %s", installation)

            rooms = self.get_rooms(installation)
            _LOGGER.debug(
                "fetch_entities: installation %s has %d room(s)",
                installation.instCode,
                len(rooms),
            )

            for room in rooms:
                _LOGGER.debug(
                    "fetch_entities: room '%s' has %d device(s)",
                    room.roomDescription,
                    len(room.deviceList),
                )
                for device in room.deviceList:
                    _LOGGER.debug(
                        "fetch_entities: device '%s' type=%s model=%s -> %s",
                        device.label,
                        device.idDevicetype,
                        device.idDevicemodel,
                        type(device).__name__,
                    )
                    if isinstance(device, DaisyLight):
                        self.lights.append(device)
                    elif isinstance(device, DaisyCover):
                        self.covers.append(device)
                    elif isinstance(device, DaisyHeater4CH):
                        self.heaters.append(device)
                    else:
                        _LOGGER.warning(
                            "fetch_entities: unrecognised device '%s' "
                            "(type=%s model=%s) — not added to any platform",
                            device.label,
                            device.idDevicetype,
                            device.idDevicemodel,
                        )

        _LOGGER.debug(
            "fetch_entities: complete — %d light(s), %d cover(s), %d heater(s)",
            len(self.lights),
            len(self.covers),
            len(self.heaters),
        )

    @property
    def hub_id(self) -> str:
        return self._id

    async def test_connection(self) -> bool:
        # TODO
        return True
