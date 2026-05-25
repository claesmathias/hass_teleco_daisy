import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .hub import DaisyHub

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["light", "cover", "climate"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("async_setup_entry: setting up entry '%s'", entry.title)

    daisy_hub = DaisyHub(hass, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])

    _LOGGER.debug("async_setup_entry: logging in as %s", entry.data[CONF_USERNAME])
    await hass.async_add_executor_job(daisy_hub.login)
    _LOGGER.debug("async_setup_entry: login successful, fetching entities")

    await hass.async_add_executor_job(daisy_hub.fetch_entities)
    _LOGGER.debug("async_setup_entry: entities fetched, forwarding to platforms")

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = daisy_hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("async_setup_entry: platforms set up successfully")
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    _LOGGER.debug("async_unload_entry: unloading entry '%s'", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.debug("async_unload_entry: entry '%s' unloaded", entry.title)
    else:
        _LOGGER.warning("async_unload_entry: failed to unload entry '%s'", entry.title)
    return unload_ok
