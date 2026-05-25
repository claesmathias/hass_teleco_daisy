"""
teleco_daisy.models
~~~~~~~~~~~~~~~~~~~
Dataclass models mirroring the Java cloud model classes from the Teleco Daisy
Android app (reverse-engineered from classes3.dex via JADX).
Uses only stdlib dataclasses + requests — no third-party dependencies.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


def _from_dict(cls, d: dict):
    """Construct a dataclass from a dict, ignoring unknown keys."""
    import inspect
    known = {f.name for f in cls.__dataclass_fields__.values()}
    return cls(**{k: v for k, v in d.items() if k in known})


# ---------------------------------------------------------------------------
# Session / auth
# ---------------------------------------------------------------------------

@dataclass
class SessionCloud:
    idSession: str
    idAccount: int


@dataclass
class ConfirmationUser:
    idAccount: int
    email: str
    firstname: str
    lastname: str
    confirmationcode: str | None = None
    confirmationurl: str | None = None
    registrationdate: int | None = None


# ---------------------------------------------------------------------------
# Installations
# ---------------------------------------------------------------------------

@dataclass
class DaisyInstallation:
    activetimer: str
    firmwareVersion: str
    idInstallation: int
    idInstallationDevice: int
    instCode: str
    instDescription: str
    installationOrder: int
    latitude: float | None = None
    longitude: float | None = None
    weekend: str | None = None
    workdays: str | None = None

    def __str__(self) -> str:
        return f'DaisyInstallation("{self.instDescription}" fw{self.firmwareVersion})'

    @classmethod
    def from_dict(cls, d: dict) -> "DaisyInstallation":
        return _from_dict(cls, d)


@dataclass
class InstallationCloud:
    idInstallation: int
    idAccount: int
    instCode: str
    instDescription: str
    installationOrder: int
    idInstallationDevice: int | None = None
    idSession: str | None = None
    activetimer: str | None = None
    weekend: str | None = None
    workdays: str | None = None
    firmwareVersion: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "InstallationCloud":
        return _from_dict(cls, d)


# ---------------------------------------------------------------------------
# Devices / status
# ---------------------------------------------------------------------------

@dataclass
class StatusItem:
    idInstallationDeviceStatusitem: int
    idDevicetypeStatusitemModel: int
    statusitemCode: str
    statusItem: str
    statusValue: str
    lowlevelStatusitem: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "StatusItem":
        return _from_dict(cls, d)


# ---------------------------------------------------------------------------
# Timers
# ---------------------------------------------------------------------------

@dataclass
class TimerCloud:
    idInstallationDeviceTimer: int
    idInstallationDeviceCommand: int
    timerOrder: int
    commandParam: str | None = None
    timerActive: str | None = None
    timerDate: str | None = None
    timerDateExpire: str | None = None
    giorni: str | None = None
    albaTramonto: int | None = None
    crepuscolare: str | None = None
    crepuscolareOffset: int | None = None
    info: str | None = None

    @classmethod
    def from_dict(cls, d: dict) -> "TimerCloud":
        return _from_dict(cls, d)


@dataclass
class TimerSetup:
    idAccount: int
    idSession: str
    idInstallation: int
    idInstallationDevice: int
    timerList: list[TimerCloud] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "TimerSetup":
        timers = [TimerCloud.from_dict(t) for t in d.get("timerList", [])]
        return cls(
            idAccount=d["idAccount"],
            idSession=d["idSession"],
            idInstallation=d["idInstallation"],
            idInstallationDevice=d["idInstallationDevice"],
            timerList=timers,
        )


# ---------------------------------------------------------------------------
# Scenarios
# ---------------------------------------------------------------------------

@dataclass
class ScenarioCloud:
    idInstallationScenario: int
    idInstallation: int
    idAccount: int
    scenarioDescription: str
    scenarioOrder: int
    idInstallationRoom: int | None = None
    idInstallationDevice: int | None = None
    idSession: str | None = None
    icon: int | None = None
    commandList: list[dict] = field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict) -> "ScenarioCloud":
        return _from_dict(cls, d)


# ---------------------------------------------------------------------------
# Feed result
# ---------------------------------------------------------------------------

@dataclass
class FeedCommandResult:
    success: bool | None = None
    action_reference: str | None = None
    message: str | None = None
