"""Interruptores: modo silencioso y luz del panel."""

from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import DP_DO_NOT_DISTURB, DP_LED, DOMAIN
from .entity import VactidyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            VactidySwitch(coordinator, "do_not_disturb", DP_DO_NOT_DISTURB, "mdi:bell-off"),
            VactidySwitch(coordinator, "led", DP_LED, "mdi:lightbulb"),
        ]
    )


class VactidySwitch(VactidyEntity, SwitchEntity):
    """Interruptor respaldado por un data point booleano."""

    def __init__(self, coordinator, key: str, dp: int, icon: str) -> None:
        super().__init__(coordinator, key)
        self._dp = dp
        self._attr_translation_key = key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        value = self.dp.get(self._dp)
        return bool(value) if value is not None else None

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.async_send({self._dp: True})

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.async_send({self._dp: False})
