"""Configuración de la integración Vactidy."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, CONNECT_TIMEOUT, DOMAIN, LOCAL_PORT
from .coordinator import VactidyCoordinator
from .tuya_local import TuyaDevice

_LOGGER = logging.getLogger(__name__)

VactidyConfigEntry = ConfigEntry

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.VACUUM,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Prepara el dispositivo a partir de la entrada de configuración."""
    device = TuyaDevice(
        host=entry.data[CONF_HOST],
        device_id=entry.data[CONF_DEVICE_ID],
        local_key=entry.data[CONF_LOCAL_KEY],
        port=LOCAL_PORT,
        timeout=CONNECT_TIMEOUT,
    )
    coordinator = VactidyCoordinator(hass, device)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Descarga las plataformas y cierra la conexión TCP."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        coordinator: VactidyCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.device.async_close()
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Recarga la entrada cuando cambian los datos de conexión."""
    await hass.config_entries.async_reload(entry.entry_id)
