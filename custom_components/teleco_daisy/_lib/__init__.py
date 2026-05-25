"""
teleco_daisy
~~~~~~~~~~~~
Python library for the Teleco / TMate cloud API.

Quick start::

    from teleco_daisy import TelecoDaisy

    api = TelecoDaisy("user@example.com", "secret")
    api.login()

    for inst in api.get_installations():
        online = api.is_installation_online(inst)
        print(inst, "online:", online)

        for room in api.get_rooms(inst):
            print(" ", room)
            for device in room.deviceList:
                print("   ", device)
"""

from .client import TelecoDaisy
from .devices import (
    DaisyAwningCover,
    DaisyCover,
    DaisyDevice,
    DaisyDeviceWithCommands,
    DaisyHeater4CH,
    DaisyLight,
    DaisyRGBLight,
    DaisyRoom,
    DaisyRoomWithCommands,
    DaisyRetractableSlatsCover,
    DaisyShadeCover,
    DaisySlatsCover,
    DaisyWhite4LevelLight,
)
from .exceptions import AckError, ApiError, AuthError, CommandError, TelecoError
from .models import (
    ConfirmationUser,
    DaisyInstallation,
    FeedCommandResult,
    InstallationCloud,
    ScenarioCloud,
    StatusItem,
    TimerCloud,
    TimerSetup,
)

__all__ = [
    # Client
    "TelecoDaisy",
    # Devices
    "DaisyDevice",
    "DaisyDeviceWithCommands",
    "DaisyRoom",
    "DaisyRoomWithCommands",
    "DaisyLight",
    "DaisyRGBLight",
    "DaisyWhite4LevelLight",
    "DaisyCover",
    "DaisySlatsCover",
    "DaisyRetractableSlatsCover",
    "DaisyShadeCover",
    "DaisyAwningCover",
    "DaisyHeater4CH",
    # Models
    "DaisyInstallation",
    "InstallationCloud",
    "ScenarioCloud",
    "StatusItem",
    "TimerCloud",
    "TimerSetup",
    "ConfirmationUser",
    "FeedCommandResult",
    # Exceptions
    "TelecoError",
    "AuthError",
    "ApiError",
    "CommandError",
    "AckError",
]

__version__ = "0.2.2"
