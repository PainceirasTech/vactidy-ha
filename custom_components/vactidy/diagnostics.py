"""Volcado de diagnóstico para incidencias."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import VactidyConfigEntry
from .const import DOMAIN


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: VactidyConfigEntry
) -> dict[str, Any]:
    """Devuelve el estado completo sin exponer la clave local."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    device = coordinator.device
    return {
        "entry": {
            "title": entry.title,
            "host": device.host,
            "port": device.port,
            "device_id": device.device_id,
        },
        "last_update_success": coordinator.last_update_success,
        "dps": {str(k): v for k, v in sorted((coordinator.data or {}).items())},
    }
