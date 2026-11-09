"""Sensores binarios: carga, averías y avisos."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import (
    DP_DO_NOT_DISTURB,
    DP_ERROR_FLAGS,
    DP_FAULT,
    DP_MOP_INSTALLED,
    DP_STATUS,
    DOMAIN,
    STATUS_DOCKED,
    STATUS_ERROR,
)
from .entity import VactidyEntity

_ESTADOS_CARGANDO = frozenset({"charging", "charge_done"})


@dataclass(frozen=True, kw_only=True)
class VactidyBinarySensorDescription(BinarySensorEntityDescription):
    """Descripción con la función que evalúa el data point."""

    value_fn: Callable[[dict[int, Any]], bool | None]


BINARY_SENSORS: tuple[VactidyBinarySensorDescription, ...] = (
    VactidyBinarySensorDescription(
        key="charging",
        translation_key="charging",
        device_class=BinarySensorDeviceClass.BATTERY_CHARGING,
        value_fn=lambda dp: dp.get(DP_STATUS) in _ESTADOS_CARGANDO,
    ),
    VactidyBinarySensorDescription(
        key="problem",
        translation_key="problem",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda dp: bool(dp.get(DP_FAULT))
        or bool(dp.get(DP_ERROR_FLAGS))
        or dp.get(DP_STATUS) in STATUS_ERROR,
    ),
    VactidyBinarySensorDescription(
        key="docked",
        translation_key="docked",
        device_class=BinarySensorDeviceClass.PLUG,
        value_fn=lambda dp: dp.get(DP_STATUS) in STATUS_DOCKED,
    ),
    VactidyBinarySensorDescription(
        key="do_not_disturb",
        translation_key="do_not_disturb",
        icon="mdi:bell-off",
        value_fn=lambda dp: bool(dp.get(DP_DO_NOT_DISTURB)),
    ),
    VactidyBinarySensorDescription(
        key="mop_installed",
        translation_key="mop_installed",
        icon="mdi:water",
        value_fn=lambda dp: dp.get(DP_MOP_INSTALLED) == "installed",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VactidyBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class VactidyBinarySensor(VactidyEntity, BinarySensorEntity):
    """Sensor binario genérico."""

    entity_description: VactidyBinarySensorDescription

    def __init__(
        self, coordinator, description: VactidyBinarySensorDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def is_on(self) -> bool | None:
        return self.entity_description.value_fn(self.dp)
