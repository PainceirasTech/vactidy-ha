"""Selectores: caudal de la mopa y modo de limpieza."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import (
    CLEAN_MODES,
    DP_CLEAN_MODE,
    DP_WATER_LEVEL,
    DOMAIN,
    WATER_LEVELS,
)
from .entity import VactidyEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> "None":
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            VactidySelect(
                coordinator,
                "water_level",
                DP_WATER_LEVEL,
                WATER_LEVELS,
            ),
            VactidySelect(
                coordinator,
                "clean_mode",
                DP_CLEAN_MODE,
                CLEAN_MODES,
            ),
        ]
    )


class VactidySelect(VactidyEntity, SelectEntity):
    """Selector respaldado por un data point de tipo texto."""

    def __init__(self, coordinator, key: str, dp: int, options: list[str]) -> None:
        super().__init__(coordinator, key)
        self._dp = dp
        self._attr_translation_key = key
        self._attr_options = list(options)

    @property
    def current_option(self) -> str | None:
        value = self.dp.get(self._dp)
        return value if value in self._attr_options else None

    async def async_select_option(self, option: str) -> None:
        if option not in self._attr_options:
            raise ValueError(f"Opción no válida: {option}")
        await self.coordinator.async_send({self._dp: option})
