"""
teleco_daisy.exceptions
~~~~~~~~~~~~~~~~~~~~~~~
Exception hierarchy for the Teleco Daisy library.
"""


class TelecoError(Exception):
    """Base exception for all library errors."""


class AuthError(TelecoError):
    """Raised when login / credential errors occur."""


class ApiError(TelecoError):
    """Raised when the API returns codEsito != 'S'."""

    def __init__(self, response: dict):
        self.cod_esito = response.get("codEsito")
        self.msg_esito = response.get("msgEsito", "")
        super().__init__(f"[{self.cod_esito}] {self.msg_esito}")


class CommandError(TelecoError):
    """Raised when a device command fails (MessageID or ack error)."""


class AckError(CommandError):
    """Raised when the hub does not confirm command execution."""
