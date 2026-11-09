"""Coordinador de datos: sondea el robot por la red local."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, SCAN_INTERVAL
from .tuya_local import TuyaConnectionError, TuyaDevice, TuyaError

_LOGGER = logging.getLogger(__name__)


class VactidyCoordinator(DataUpdateCoordinator[dict[int, Any]]):
    """Mantiene el último volcado de data points del robot."""

    def __init__(self, hass: HomeAssistant, device: TuyaDevice) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{device.device_id}",
            update_interval=SCAN_INTERVAL,
        )
        self.device = device

    async def _async_update_data(self) -> dict[int, Any]:
        try:
            return await self.device.async_status()
        except TuyaConnectionError as err:
            raise UpdateFailed(f"Robot inalcanzable: {err}") from err
        except TuyaError as err:
            raise UpdateFailed(f"Error del robot: {err}") from err

    async def async_send(self, dps: dict[int, Any]) -> None:
        """Envía data points y refresca el estado inmediatamente."""
        await self.device.async_set_dps(dps)
        await self.async_request_refresh()
