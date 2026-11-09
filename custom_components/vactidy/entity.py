"""Entidad base compartida por todas las plataformas de Vactidy."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import VactidyCoordinator


class VactidyEntity(CoordinatorEntity[VactidyCoordinator]):
    """Entidad ligada al coordinador y al dispositivo físico."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: VactidyCoordinator, key: str) -> None:
        super().__init__(coordinator)
        device = coordinator.device
        self._attr_unique_id = f"{device.device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.device_id)},
            manufacturer=MANUFACTURER,
            name=coordinator.config_entry.title,
            model="W15",
            configuration_url="https://github.com/PainceirasTech/vactidy-ha",
        )

    @property
    def dp(self) -> dict[int, Any]:
        """Último volcado de data points."""
        return self.coordinator.data or {}

    @property
    def available(self) -> bool:
        return super().available and bool(self.coordinator.data)
