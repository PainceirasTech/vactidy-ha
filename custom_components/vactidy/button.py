"""Botones de acción: localizar, vaciar y reiniciar contadores."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import (
    DP_EMPTY_DUSTBIN,
    DP_LOCATE,
    DP_MAIN_BRUSH_RESET,
    DP_MOP_RESET,
    DP_SENSOR_RESET,
    DP_SIDE_BRUSH_RESET,
    DOMAIN,
)
from .entity import VactidyEntity


@dataclass(frozen=True, kw_only=True)
class VactidyButtonDescription(ButtonEntityDescription):
    """Botón que escribe un data point concreto."""

    dp: int


BUTTONS: tuple[VactidyButtonDescription, ...] = (
    VactidyButtonDescription(
        key="locate",
        translation_key="locate",
        icon="mdi:map-marker-radius",
        dp=DP_LOCATE,
    ),
    VactidyButtonDescription(
        key="empty_dustbin",
        translation_key="empty_dustbin",
        icon="mdi:delete-variant",
        dp=DP_EMPTY_DUSTBIN,
    ),
    VactidyButtonDescription(
        key="reset_side_brush",
        translation_key="reset_side_brush",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        dp=DP_SIDE_BRUSH_RESET,
    ),
    VactidyButtonDescription(
        key="reset_main_brush",
        translation_key="reset_main_brush",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        dp=DP_MAIN_BRUSH_RESET,
    ),
    VactidyButtonDescription(
        key="reset_sensor",
        translation_key="reset_sensor",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        dp=DP_SENSOR_RESET,
    ),
    VactidyButtonDescription(
        key="reset_mop",
        translation_key="reset_mop",
        device_class=ButtonDeviceClass.RESTART,
        entity_category=EntityCategory.CONFIG,
        dp=DP_MOP_RESET,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VactidyButton(coordinator, description) for description in BUTTONS
    )


class VactidyButton(VactidyEntity, ButtonEntity):
    """Botón de un solo uso sobre un data point."""

    entity_description: VactidyButtonDescription

    def __init__(self, coordinator, description: VactidyButtonDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    async def async_press(self) -> None:
        await self.coordinator.async_send({self.entity_description.dp: True})
