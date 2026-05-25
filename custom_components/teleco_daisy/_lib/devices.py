"""
teleco_daisy.devices
~~~~~~~~~~~~~~~~~~~~
Device classes and factory. No third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Literal

from .models import DaisyInstallation, StatusItem

if TYPE_CHECKING:
    from .client import TelecoDaisy


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

@dataclass
class DaisyBaseDevice:
    activetimer: str
    deviceCode: str
    deviceIndex: int
    deviceOrder: int
    favorite: str
    feedback: str
    idDevicemodel: int
    idDevicetype: int
    idInstallationDevice: int
    label: str
    remoteControlCode: str
    directOnly: str | None = None


@dataclass
class DaisyDevice(DaisyBaseDevice):
    client: "TelecoDaisy" = field(repr=False, default=None)
    installation: DaisyInstallation = field(repr=False, default=None)

    def __str__(self) -> str:
        return f'{self.__class__.__name__}("{self.label}")'

    def __repr__(self) -> str:
        return (
            f'<{self.__class__.__name__} label="{self.label}" '
            f'id={self.idInstallationDevice} '
            f'type={self.idDevicetype} model={self.idDevicemodel}>'
        )

    def command(self, params: dict) -> dict:
        return self.client.feed_the_commands(
            installation=self.installation,
            commandsList=[
                {
                    "deviceCode": str(self.deviceIndex),
                    "idInstallationDevice": self.idInstallationDevice,
                }
                | params
            ],
        )

    def update_state(self) -> list[StatusItem]:
        return self.client.status_device_list(self.installation, self)


# ---------------------------------------------------------------------------
# Device with command definitions
# ---------------------------------------------------------------------------

@dataclass
class DeviceCommand:
    commandAction: str | None = None
    commandCode: str | None = None
    commandParam: str | None = None
    deviceIndex: int | None = None
    idDevicetypeCommandModel: int | None = None
    idInstallationDeviceCommand: int | None = None
    lowlevelCommand: str | None = None


@dataclass
class DaisyDeviceWithCommands(DaisyBaseDevice):
    deviceCommandList: list[DeviceCommand] = field(default_factory=list)

    def __str__(self) -> str:
        return f'DaisyDeviceWithCommands("{self.label}")'


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------

@dataclass
class DaisyRoom:
    idInstallationRoom: int
    idRoomtype: int
    roomDescription: str
    roomOrder: int
    deviceList: list[DaisyDevice] = field(default_factory=list)

    def __str__(self) -> str:
        return f'DaisyRoom("{self.roomDescription}" [{len(self.deviceList)} devices])'


@dataclass
class DaisyRoomWithCommands:
    idInstallationRoom: int
    idRoomtype: int
    roomDescription: str
    roomOrder: int
    deviceList: list[DaisyDeviceWithCommands] = field(default_factory=list)

    def __str__(self) -> str:
        return f'DaisyRoomWithCommands("{self.roomDescription}")'


# ---------------------------------------------------------------------------
# Covers
# ---------------------------------------------------------------------------

@dataclass
class DaisyCover(DaisyDevice):
    is_closed: bool | None = None
    osc_map: dict = field(default_factory=dict)

    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "OPEN_CLOSE":
                if s.statusValue == "CLOSE":
                    self.is_closed = True
                elif s.statusValue == "OPEN":
                    self.is_closed = False
                else:
                    self.is_closed = None
        return stati

    def open_cover(self) -> dict:
        return self._osc("open")

    def stop_cover(self) -> dict:
        return self._osc("stop")

    def close_cover(self) -> dict:
        return self._osc("close")

    def _osc(self, action: str) -> dict:
        return self.command({"commandAction": "OPEN_STOP_CLOSE"} | self.osc_map[action])


@dataclass
class DaisySlatsCover(DaisyCover):
    position: int | None = None

    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "LEVEL":
                self.position = int(s.statusValue)
        return stati

    def open_cover(self, percent: str | None = None) -> dict:
        if percent is None or percent == "100":
            return self._osc("open")
        level_map = {
            "33":  {"commandParam": "LEV2", "commandId": 97, "lowlevelCommand": "CH2"},
            "66":  {"commandParam": "LEV3", "commandId": 98, "lowlevelCommand": "CH3"},
            "100": {"commandParam": "LEV4", "commandId": 99, "lowlevelCommand": "CH4"},
        }
        return self.command({"commandAction": "LEVEL"} | level_map[percent])


@dataclass
class DaisyShadeCover(DaisyCover):
    # For shades/screens, Teleco's "OPEN" means deployed (blocking sun) and
    # "CLOSE" means retracted — the inverse of HA cover semantics where
    # is_closed=True means the cover is blocking. Override both state reading
    # and the osc_map keys so that HA "open" retracts and "close" deploys.
    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "OPEN_CLOSE":
                if s.statusValue == "OPEN":
                    self.is_closed = True   # deployed = HA closed
                elif s.statusValue == "CLOSE":
                    self.is_closed = False  # retracted = HA open
        return stati


@dataclass
class DaisyAwningCover(DaisyCover):
    pass


# ---------------------------------------------------------------------------
# Lights
# ---------------------------------------------------------------------------

@dataclass
class DaisyLight(DaisyDevice):
    is_on: bool | None = None
    brightness: int | None = None

    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "POWER":
                self.is_on = s.statusValue == "ON"
        return stati

    def _turn_on(self, extra: dict) -> dict:
        return self.command({"commandAction": "POWER", "commandParam": "ON"} | extra)

    def _turn_off(self, extra: dict) -> dict:
        return self.command({"commandAction": "POWER", "commandParam": "OFF"} | extra)


@dataclass
class DaisyRGBLight(DaisyLight):
    rgb: tuple | None = None

    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "COLOR":
                v = s.statusValue
                self.brightness = int(v[1:4])
                self.rgb = (int(v[5:8]), int(v[9:12]), int(v[13:16]))
        return stati

    def set_rgb_and_brightness(self, rgb=None, brightness=None) -> dict:
        brightness = brightness if brightness is not None else (self.brightness or 0)
        if not 0 <= brightness <= 100:
            raise ValueError("brightness must be 0–100")
        rgb = rgb if rgb is not None else (self.rgb or (255, 255, 255))
        if any(not 0 <= c <= 255 for c in rgb):
            raise ValueError("RGB channels must be 0–255")
        v = f"A{brightness:03d}R{rgb[0]:03d}G{rgb[1]:03d}B{rgb[2]:03d}"
        return self.command({"commandAction": "COLOR", "commandId": 137,
                             "commandParam": v, "lowlevelCommand": None})

    def turn_on(self) -> dict:
        return self._turn_on({"commandId": 138, "lowlevelCommand": None})

    def turn_off(self) -> dict:
        return self._turn_off({"commandId": 138, "lowlevelCommand": None})


@dataclass
class DaisyWhite4LevelLight(DaisyLight):
    brightness_map: dict = field(default_factory=dict)

    def update_state(self) -> list[StatusItem]:
        stati = super().update_state()
        for s in stati:
            if s.statusitemCode == "POWER":
                self.is_on = s.statusValue == "ON"
            elif s.statusitemCode == "LEVEL":
                self.brightness = {"25": 25, "50": 50, "75": 75, "100": 100}.get(
                    s.statusValue, 50
                )
        return stati

    def set_brightness(self, brightness: int) -> dict:
        if not 0 <= brightness <= 100:
            raise ValueError("brightness must be 0–100")
        if brightness == 0:
            return self.turn_off()
        level = (25 if brightness <= 37 else
                 50 if brightness <= 62 else
                 75 if brightness <= 87 else 100)
        return self.command({"commandAction": "LEVEL"} | self.brightness_map[level])

    def turn_on(self) -> dict:
        if self.idDevicetype == 21 and self.idDevicemodel == 17:
            return self._turn_on({"commandId": 40, "lowlevelCommand": "CH1"})
        return self._turn_on({"commandId": 146, "lowlevelCommand": "CH1"})

    def turn_off(self) -> dict:
        if self.idDevicetype == 21 and self.idDevicemodel == 17:
            return self._turn_off({"commandId": 41, "lowlevelCommand": "CH8"})
        return self._turn_off({"commandId": 147, "lowlevelCommand": "CH8"})


# ---------------------------------------------------------------------------
# Retractable slats (model 44, subId 1 — "RAS")
# Command IDs are server-assigned and differ per device model, so they are
# fetched from command-device-list on first use instead of being hardcoded.
# ---------------------------------------------------------------------------

@dataclass
class DaisyRetractableSlatsCover(DaisySlatsCover):
    _cmd_map: dict = field(default_factory=dict, init=False, repr=False)

    def _load_commands(self) -> None:
        result = self.client.get_command_device_list(
            self.installation, self.idInstallationDevice
        )
        for c in result.get("commandList", []):
            key = (c.get("commandAction", ""), c.get("commandParam", ""))
            self._cmd_map[key] = {
                "commandId": c.get("idDevicetypeCommandModel", 0),
                "lowlevelCommand": c.get("lowlevelCommand", ""),
            }

    def _c(self, action: str, param: str) -> dict:
        if not self._cmd_map:
            self._load_commands()
        return {"commandParam": param} | self._cmd_map.get((action, param), {})

    def open_cover(self, percent: str | None = None) -> dict:
        if percent is None or percent == "100":
            return self.command({"commandAction": "OPEN_STOP_CLOSE"} | self._c("OPEN_STOP_CLOSE", "OPEN"))
        lev = {"33": "LEV2", "66": "LEV3", "100": "LEV4"}[percent]
        return self.command({"commandAction": "LEVEL"} | self._c("LEVEL", lev))

    def stop_cover(self) -> dict:
        return self.command({"commandAction": "OPEN_STOP_CLOSE"} | self._c("OPEN_STOP_CLOSE", "STOP"))

    def close_cover(self) -> dict:
        return self.command({"commandAction": "OPEN_STOP_CLOSE"} | self._c("OPEN_STOP_CLOSE", "CLOSE"))


# ---------------------------------------------------------------------------
# Heater
# ---------------------------------------------------------------------------

@dataclass
class DaisyHeater4CH(DaisyDevice):
    def turn_on(self) -> dict:
        return self.command({"commandAction": "POWER", "commandParam": "ON",
                             "lowlevelCommand": "CH1", "commandId": 58})

    def turn_off(self) -> dict:
        return self.command({"commandAction": "POWER", "commandParam": "OFF",
                             "lowlevelCommand": "CH4", "commandId": 59})

    def set_level(self, level: str) -> dict:
        cmd = {
            "50":  {"commandId": 60, "commandParam": "LEV2", "lowlevelCommand": "CH3"},
            "75":  {"commandId": 61, "commandParam": "LEV3", "lowlevelCommand": "CH2"},
            "100": {"commandId": 62, "commandParam": "LEV4", "lowlevelCommand": "CH1"},
        }[level]
        return self.command({"commandAction": "LEVEL"} | cmd)


# ---------------------------------------------------------------------------
# Shared base fields for create_device
# ---------------------------------------------------------------------------

_BASE_FIELDS = {
    "activetimer", "deviceCode", "deviceIndex", "deviceOrder",
    "favorite", "feedback", "idDevicemodel", "idDevicetype",
    "idInstallationDevice", "label", "remoteControlCode", "directOnly",
    "client", "installation",
}

def _base(raw: dict) -> dict:
    return {k: v for k, v in raw.items() if k in _BASE_FIELDS}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_device(raw: dict) -> DaisyDevice:
    dt = raw.get("idDevicetype")
    dm = raw.get("idDevicemodel")

    if dt == 23 and dm == 32:
        return DaisyRGBLight(**_base(raw))

    if dt == 24 and dm == 27:
        return DaisySlatsCover(**_base(raw), osc_map={
            "open":  {"commandId": 94, "commandParam": "OPEN",  "lowlevelCommand": "CH4"},
            "stop":  {"commandId": 95, "commandParam": "STOP",  "lowlevelCommand": "CH7"},
            "close": {"commandId": 96, "commandParam": "CLOSE", "lowlevelCommand": "CH1"},
        })

    if dt == 24 and dm == 44:
        return DaisyRetractableSlatsCover(**_base(raw))

    if dt == 21 and dm == 34:
        return DaisyWhite4LevelLight(**_base(raw), brightness_map={
            25:  {"commandParam": "LEV1", "commandId": 141, "lowlevelCommand": "CH4"},
            50:  {"commandParam": "LEV2", "commandId": 142, "lowlevelCommand": "CH3"},
            75:  {"commandParam": "LEV3", "commandId": 143, "lowlevelCommand": "CH2"},
            100: {"commandParam": "LEV4", "commandId": 144, "lowlevelCommand": "CH1"},
        })

    if dt == 21 and dm == 17:
        return DaisyWhite4LevelLight(**_base(raw), brightness_map={
            25:  {"commandParam": "LEV1", "commandId": 42,  "lowlevelCommand": "CH4"},
            50:  {"commandParam": "LEV2", "commandId": 43,  "lowlevelCommand": "CH3"},
            75:  {"commandParam": "LEV3", "commandId": 44,  "lowlevelCommand": "CH2"},
            100: {"commandParam": "LEV4", "commandId": 45,  "lowlevelCommand": "CH1"},
        })

    if dt == 21 and dm == 20:
        return DaisyHeater4CH(**_base(raw))

    if dt == 22 and dm == 31:
        return DaisyShadeCover(**_base(raw), osc_map={
            "open":  {"commandId": 113, "commandParam": "CLOSE", "lowlevelCommand": "CH8"},
            "stop":  {"commandId": 112, "commandParam": "STOP",  "lowlevelCommand": "CH7"},
            "close": {"commandId": 111, "commandParam": "OPEN",  "lowlevelCommand": "CH5"},
        })

    if dt == 22 and dm == 25:
        return DaisyShadeCover(**_base(raw), osc_map={
            "open":  {"commandId": 77, "commandParam": "CLOSE", "lowlevelCommand": "CH8"},
            "stop":  {"commandId": 76, "commandParam": "STOP",  "lowlevelCommand": "CH7"},
            "close": {"commandId": 75, "commandParam": "OPEN",  "lowlevelCommand": "CH5"},
        })

    if dt == 22 and dm == 21:
        return DaisyAwningCover(**_base(raw), osc_map={
            "open":  {"commandId": 63, "commandParam": "OPEN",  "lowlevelCommand": "CH5"},
            "stop":  {"commandId": 64, "commandParam": "STOP",  "lowlevelCommand": "CH7"},
            "close": {"commandId": 65, "commandParam": "CLOSE", "lowlevelCommand": "CH8"},
        })

    return DaisyDevice(**_base(raw))
