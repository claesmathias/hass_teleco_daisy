"""
teleco_daisy.client
~~~~~~~~~~~~~~~~~~~
Main API client for the Teleco / TMate cloud service.

Usage::

    from teleco_daisy import TelecoDaisy

    api = TelecoDaisy("user@example.com", "secret")
    api.login()

    for inst in api.get_installations():
        print(inst)
        for room in api.get_rooms(inst):
            for device in room.deviceList:
                print(" ", device)
"""

from __future__ import annotations

import logging
from time import sleep
from typing import Any

import requests

from .devices import DaisyDevice, DaisyRoom, DaisyRoomWithCommands, create_device
from .exceptions import AckError, ApiError, AuthError, CommandError
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

log = logging.getLogger(__name__)

BASE_URL = "https://tmate.telecoautomation.com/"
_BASIC_USER = "teleco"
_BASIC_PASS = "tmate20"


class TelecoDaisy:
    """
    Synchronous client for the Teleco / TMate cloud API.

    Parameters
    ----------
    email:    Account e-mail address.
    password: Account password.
    base_url: Override the default cloud endpoint (e.g. for staging).
    timeout:  HTTP request timeout in seconds (default 15).
    """

    def __init__(
        self,
        email: str,
        password: str,
        base_url: str = BASE_URL,
        timeout: int = 15,
    ):
        self.email = email
        self.password = password
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout

        self._session = requests.Session()
        self._session.auth = (_BASIC_USER, _BASIC_PASS)

        self.id_account: int | None = None
        self.id_session: str | None = None

    # ------------------------------------------------------------------
    # Internal HTTP helpers
    # ------------------------------------------------------------------

    def _post(
        self,
        path: str,
        body: dict | None = None,
        *,
        authenticated: bool = True,
    ) -> dict | None:
        """
        POST to ``path`` (relative to base_url).

        When *authenticated* is True the session/account tokens are merged
        into the body.  Raises :class:`ApiError` on non-"S" codEsito.
        Returns ``valRisultato`` (may be None for some endpoints).
        """
        payload: dict[str, Any] = {}
        if authenticated:
            payload["idSession"] = self.id_session
            payload["idAccount"] = self.id_account
        if body:
            payload |= body

        url = self.base_url + path
        log.debug("POST %s  body=%s", url, payload)
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        log.debug("     → %s", data)

        cod = data.get("codEsito")
        if cod is not None and cod != "S":
            raise ApiError(data)

        return data.get("valRisultato")

    def _tmate20_post(self, path: str, body: dict | None = None) -> dict:
        """
        POST to a tmate20 endpoint that returns raw JSON (no codEsito wrapper).
        Always injects idSession.
        """
        payload: dict[str, Any] = {"idSession": self.id_session}
        if body:
            payload |= body

        url = self.base_url + path
        log.debug("POST %s  body=%s", url, payload)
        resp = self._session.post(url, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        log.debug("     → %s", data)
        return data

    # ------------------------------------------------------------------
    # Account / auth
    # ------------------------------------------------------------------

    def login(self) -> None:
        """
        Authenticate and store session tokens.

        Raises :class:`AuthError` if credentials are rejected.
        """
        try:
            result = self._post(
                "teleco/services/account-login",
                {"email": self.email, "pwd": self.password},
                authenticated=False,
            )
        except ApiError as exc:
            raise AuthError("Login failed") from exc

        self.id_account = result["idAccount"]
        self.id_session = result["idSession"]
        log.info("Logged in as account %d", self.id_account)

    def logout(self) -> None:
        """Invalidate the session on the server and clear local tokens."""
        self._post("teleco/services/account-logout")
        log.info("Logged out account %d", self.id_account)
        self.id_account = None
        self.id_session = None

    def register(
        self,
        email: str,
        password: str,
        firstname: str,
        lastname: str,
        account_source: str = "daisy",
        flg_advert: str = "N",
    ) -> ConfirmationUser:
        """
        Create a new cloud account.

        Returns a :class:`~teleco_daisy.models.ConfirmationUser` with the
        new account id and e-mail confirmation details.
        """
        result = self._post(
            "teleco/services/account-registration",
            {
                "email": email,
                "pwd": password,
                "firstname": firstname,
                "lastname": lastname,
                "accountSource": account_source,
                "flgAdvert": flg_advert,
                "flgBanner": "S",
                "idApp": "DAISY",
            },
            authenticated=False,
        )
        return ConfirmationUser(**result)

    def change_password(
        self, pwd_old: str, pwd_new: str, id_account: int | None = None
    ) -> None:
        """Change the password for the currently logged-in account."""
        self._post(
            "teleco/services/change-password",
            {
                "idAccount": id_account or self.id_account,
                "pwdOld": pwd_old,
                "pwdNew": pwd_new,
            },
        )

    def reset_password(self, email: str) -> None:
        """Trigger a password-reset e-mail."""
        self._post(
            "teleco/services/reset-password",
            {"email": email},
            authenticated=False,
        )

    # ------------------------------------------------------------------
    # Installations
    # ------------------------------------------------------------------

    def get_installations(self) -> list[DaisyInstallation]:
        """Return all installations paired with this account."""
        result = self._post("teleco/services/account-installation-list")
        return [DaisyInstallation(**i) for i in result["installationList"]]

    def pair_installation(
        self,
        inst_code: str,
        inst_description: str,
        installation_order: int = 0,
        activetimer: str = "N",
        weekend: str | None = None,
        workdays: str | None = None,
        firmware_version: str | None = None,
    ) -> dict:
        """
        Pair a new installation (hub) with this account.

        ``inst_code`` is the unique code printed on the hub.
        Returns the raw ``valRisultato`` from the server.
        """
        return self._post(
            "teleco/services/account-installation-pair",
            {
                "instCode": inst_code,
                "instDescription": inst_description,
                "installationOrder": installation_order,
                "activetimer": activetimer,
                "weekend": weekend,
                "workdays": workdays,
                "firmwareVersion": firmware_version,
            },
        )

    def unpair_installation(self, installation: DaisyInstallation) -> None:
        """Remove the association between this account and an installation."""
        self._post(
            "teleco/services/account-installation-unpair",
            {"idInstallation": installation.idInstallation},
        )

    def setup_installation(
        self,
        installation: DaisyInstallation,
        inst_description: str | None = None,
        installation_order: int | None = None,
        activetimer: str | None = None,
        weekend: str | None = None,
        workdays: str | None = None,
        firmware_version: str | None = None,
    ) -> InstallationCloud:
        """
        Update installation metadata.

        Omitted parameters fall back to the values already on *installation*.
        Returns the server's updated :class:`~teleco_daisy.models.InstallationCloud`.
        """
        result = self._post(
            "teleco/services/installation-setup",
            {
                "idInstallation": installation.idInstallation,
                "instCode": installation.instCode,
                "instDescription": inst_description or installation.instDescription,
                "installationOrder": (
                    installation_order
                    if installation_order is not None
                    else installation.installationOrder
                ),
                "activetimer": activetimer or installation.activetimer,
                "weekend": weekend or installation.weekend,
                "workdays": workdays or installation.workdays,
                "firmwareVersion": firmware_version or installation.firmwareVersion,
            },
        )
        return InstallationCloud(**result)

    def is_installation_online(self, installation: DaisyInstallation) -> bool:
        """Return True if the hub is reachable (nodestatus endpoint)."""
        result = self._tmate20_post(
            "teleco/services/tmate20/nodestatus/",
            {"idInstallation": installation.instCode},
        )
        return bool(result.get("nodeActive"))

    # ------------------------------------------------------------------
    # Rooms
    # ------------------------------------------------------------------

    def get_rooms(self, installation: DaisyInstallation) -> list[DaisyRoom]:
        """
        Return all rooms (with live device objects) for an installation.

        Each device in the returned rooms has ``client`` and ``installation``
        already populated so you can call ``.command()``, ``.update_state()`` etc.
        """
        result = self._post(
            "teleco/services/room-list",
            {"idInstallation": installation.idInstallation},
        )
        rooms: list[DaisyRoom] = []
        for room in result["roomList"]:
            devices = []
            for raw_dev in room.get("deviceList", []):
                raw_dev["client"] = self
                raw_dev["installation"] = installation
                devices.append(create_device(raw_dev))
            rooms.append(DaisyRoom(**room | {"deviceList": devices}))
        return rooms

    def get_rooms_with_commands(
        self, installation: DaisyInstallation
    ) -> list[DaisyRoomWithCommands]:
        """
        Return rooms with command definitions (no live client references).
        Useful for inspecting available commands per device.
        """
        result = self._post(
            "teleco/services/room-configuration-list",
            {"idInstallation": installation.idInstallation},
        )
        return [DaisyRoomWithCommands(**r) for r in result["roomList"]]

    def setup_room(
        self,
        installation: DaisyInstallation,
        id_installation_room: int,
        room_description: str,
        id_roomtype: int,
        room_order: int,
        device_list: list[dict] | None = None,
    ) -> dict:
        """Create or update a room. Returns the raw ``valRisultato``."""
        return self._post(
            "teleco/services/room-setup",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationRoom": id_installation_room,
                "roomDescription": room_description,
                "idRoomtype": id_roomtype,
                "roomOrder": room_order,
                "deviceList": device_list or [],
            },
        )

    def delete_room(
        self,
        installation: DaisyInstallation,
        id_installation_room: int,
    ) -> None:
        """Delete a room from an installation."""
        self._post(
            "teleco/services/room-delete",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationRoom": id_installation_room,
            },
        )

    # ------------------------------------------------------------------
    # Device status
    # ------------------------------------------------------------------

    def status_device_list(
        self, installation: DaisyInstallation, device: DaisyDevice
    ) -> list[StatusItem]:
        """Return the current status items for *device*."""
        result = self._post(
            "teleco/services/status-device-list",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationDevice": device.idInstallationDevice,
            },
        )
        return [StatusItem(**x) for x in result.get("statusitemList", [])]

    def get_command_device_list(
        self,
        installation: DaisyInstallation,
        id_installation_device: int,
    ) -> dict:
        """Return the available commands for a specific device."""
        return self._post(
            "teleco/services/command-device-list",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationDevice": id_installation_device,
            },
        )

    def setup_command_device(
        self,
        installation: DaisyInstallation,
        id_installation_device: int,
    ) -> dict:
        """Trigger a command-device-setup (re-sync device commands)."""
        return self._post(
            "teleco/services/command-device-setup",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationDevice": id_installation_device,
            },
        )

    # ------------------------------------------------------------------
    # Scenarios
    # ------------------------------------------------------------------

    def get_scenarios(self, installation: DaisyInstallation) -> list[ScenarioCloud]:
        """Return all saved scenarios for an installation."""
        result = self._post(
            "teleco/services/scenario-list",
            {"idInstallation": installation.idInstallation},
        )
        return [ScenarioCloud(**s) for s in result.get("scenarioList", [])]

    def get_scenario_commands(
        self,
        installation: DaisyInstallation,
        id_installation_scenario: int,
    ) -> dict:
        """Return the command list for a specific scenario."""
        return self._post(
            "teleco/services/command-scenario-list",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationScenario": id_installation_scenario,
            },
        )

    def setup_scenario(
        self,
        installation: DaisyInstallation,
        id_installation_scenario: int,
        scenario_description: str,
        scenario_order: int,
        id_installation_room: int,
        icon: int = 0,
        command_list: list[dict] | None = None,
    ) -> dict:
        """
        Create or update a scenario.

        *command_list* is a list of dicts with keys
        ``idInstallationDeviceCommand``, ``commandIndex``, ``commandParam``.
        """
        return self._post(
            "teleco/services/scenario-setup",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationScenario": id_installation_scenario,
                "scenarioDescription": scenario_description,
                "scenarioOrder": scenario_order,
                "idInstallationRoom": id_installation_room,
                "icon": icon,
                "commandList": command_list or [],
            },
        )

    def delete_scenario(
        self,
        installation: DaisyInstallation,
        id_installation_scenario: int,
    ) -> None:
        """Delete a scenario."""
        self._post(
            "teleco/services/scenario-delete",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationScenario": id_installation_scenario,
            },
        )

    # ------------------------------------------------------------------
    # Timers
    # ------------------------------------------------------------------

    def get_timers(
        self,
        installation: DaisyInstallation,
        id_installation_device: int,
    ) -> TimerSetup:
        """Return the timer configuration for a device."""
        result = self._post(
            "teleco/services/timer-device-list/",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationDevice": id_installation_device,
            },
        )
        return TimerSetup(**result)

    def setup_timers(
        self,
        installation: DaisyInstallation,
        id_installation_device: int,
        timer_list: list[dict],
    ) -> TimerSetup:
        """
        Write a timer configuration for a device.

        *timer_list* is a list of dicts corresponding to
        :class:`~teleco_daisy.models.TimerCloud` fields.
        """
        result = self._post(
            "teleco/services/timer-device-setup/",
            {
                "idInstallation": installation.idInstallation,
                "idInstallationDevice": id_installation_device,
                "timerList": timer_list,
            },
        )
        return TimerSetup(**result)

    # ------------------------------------------------------------------
    # Feed commands / ack
    # ------------------------------------------------------------------

    def feed_the_commands(
        self,
        installation: DaisyInstallation,
        commandsList: list[dict],
        *,
        ignore_ack: bool = False,
    ) -> FeedCommandResult:
        """
        Send one or more raw commands to the hub.

        Returns a :class:`~teleco_daisy.models.FeedCommandResult`.
        Raises :class:`~teleco_daisy.exceptions.CommandError` on protocol errors.
        """
        res = self._tmate20_post(
            "teleco/services/tmate20/feedthecommands/",
            {
                "commandsList": commandsList,
                "idInstallation": installation.instCode,
                "idScenario": 0,
                "isScenario": False,
            },
        )
        if res.get("MessageID") != "WS-000":
            raise CommandError(f"Unexpected MessageID: {res}")

        action_ref = res.get("ActionReference")
        if ignore_ack:
            return FeedCommandResult(success=None, action_reference=action_ref)

        return self._poll_ack(installation, action_ref)

    def run_scenario(
        self,
        installation: DaisyInstallation,
        id_installation_scenario: int,
        *,
        ignore_ack: bool = False,
    ) -> FeedCommandResult:
        """Trigger a saved scenario on the hub."""
        res = self._tmate20_post(
            "teleco/services/tmate20/feedthecommands/",
            {
                "commandsList": [],
                "idInstallation": installation.instCode,
                "idScenario": id_installation_scenario,
                "isScenario": True,
            },
        )
        if res.get("MessageID") != "WS-000":
            raise CommandError(f"Unexpected MessageID: {res}")

        action_ref = res.get("ActionReference")
        if ignore_ack:
            return FeedCommandResult(success=None, action_reference=action_ref)

        return self._poll_ack(installation, action_ref)

    def _poll_ack(
        self,
        installation: DaisyInstallation,
        action_reference: str,
        *,
        max_retries: int = 10,
    ) -> FeedCommandResult:
        """Poll getackcommand until the hub confirms or rejects execution."""
        for _ in range(max_retries):
            res = self._tmate20_post(
                "teleco/services/tmate20/getackcommand/",
                {
                    "id": action_reference,
                    "idInstallation": installation.instCode,
                    "idSession": self.id_session,
                },
            )
            msg_id = res.get("MessageID")
            msg_text = res.get("MessageText")

            if msg_id != "WS-300":
                raise AckError(f"Unexpected MessageID in ack: {res}")

            if msg_text == "RCV":
                sleep(0.5)
                continue
            if msg_text == "PROC":
                return FeedCommandResult(success=True, action_reference=action_reference)
            return FeedCommandResult(
                success=False, action_reference=action_reference, message=msg_text
            )

        raise AckError(f"Hub did not confirm command after {max_retries} retries")
