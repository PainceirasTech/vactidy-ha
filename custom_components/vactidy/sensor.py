"""Sensores de estado y mantenimiento del robot."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, UnitOfArea, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import (
    DP_BATTERY,
    DP_CLEAN_AREA,
    DP_CLEAN_TIME,
    DP_FAULT,
    DP_MAIN_BRUSH_LIFE,
    DP_MOP_LIFE,
    DP_SENSOR_LIFE,
    DP_SIDE_BRUSH_LIFE,
    DP_STATUS,
    DP_TOTAL_AREA,
    DP_TOTAL_COUNT,
    DP_TOTAL_TIME,
    DOMAIN,
    FAULT_CODES,
)
from .entity import VactidyEntity


def _segundos_a_horas(value: Any) -> float | None:
    """Convierte los segundos que informa el robot a horas con un decimal."""
    if value is None:
        return None
    try:
        return round(float(value) / 3600, 1)
    except (TypeError, ValueError):
        return None


def _fault_text(value: Any) -> str | None:
    """Traduce el código de avería a una clave legible."""
    if not value:
        return "sin_averia"
    return FAULT_CODES.get(int(value), f"codigo_{value}")


@dataclass(frozen=True, kw_only=True)
class VactidySensorDescription(SensorEntityDescription):
    """Descripción de un sensor con su función de conversión."""

    value_fn: Callable[[dict[int, Any]], Any]


SENSORS: tuple[VactidySensorDescription, ...] = (
    VactidySensorDescription(
        key="battery",
        translation_key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: dp.get(DP_BATTERY),
    ),
    VactidySensorDescription(
        key="clean_area",
        translation_key="clean_area",
        device_class=SensorDeviceClass.AREA,
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: dp.get(DP_CLEAN_AREA),
    ),
    VactidySensorDescription(
        key="clean_time",
        translation_key="clean_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: dp.get(DP_CLEAN_TIME),
    ),
    VactidySensorDescription(
        key="status",
        translation_key="status",
        icon="mdi:robot-vacuum",
        value_fn=lambda dp: dp.get(DP_STATUS),
    ),
    VactidySensorDescription(
        key="total_area",
        translation_key="total_area",
        device_class=SensorDeviceClass.AREA,
        native_unit_of_measurement=UnitOfArea.SQUARE_METERS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda dp: dp.get(DP_TOTAL_AREA),
    ),
    VactidySensorDescription(
        key="total_clean_count",
        translation_key="total_clean_count",
        icon="mdi:counter",
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda dp: dp.get(DP_TOTAL_COUNT),
    ),
    VactidySensorDescription(
        key="total_clean_time",
        translation_key="total_clean_time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        value_fn=lambda dp: dp.get(DP_TOTAL_TIME),
    ),
    VactidySensorDescription(
        key="side_brush_life",
        translation_key="side_brush_life",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: _segundos_a_horas(dp.get(DP_SIDE_BRUSH_LIFE)),
    ),
    VactidySensorDescription(
        key="main_brush_life",
        translation_key="main_brush_life",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: _segundos_a_horas(dp.get(DP_MAIN_BRUSH_LIFE)),
    ),
    VactidySensorDescription(
        key="sensor_life",
        translation_key="sensor_life",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: _segundos_a_horas(dp.get(DP_SENSOR_LIFE)),
    ),
    VactidySensorDescription(
        key="mop_life",
        translation_key="mop_life",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda dp: _segundos_a_horas(dp.get(DP_MOP_LIFE)),
    ),
    VactidySensorDescription(
        key="fault",
        translation_key="fault",
        icon="mdi:alert-circle-outline",
        entity_registry_enabled_default=True,
        value_fn=lambda dp: _fault_text(dp.get(DP_FAULT)),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VactidySensor(coordinator, description) for description in SENSORS
    )


class VactidySensor(VactidyEntity, SensorEntity):
    """Sensor genérico alimentado por un data point."""

    entity_description: VactidySensorDescription

    def __init__(self, coordinator, description: VactidySensorDescription) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> Any:
        return self.entity_description.value_fn(self.dp)
