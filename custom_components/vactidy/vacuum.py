"""Plataforma vacuum: el robot como entidad principal."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.vacuum import (
    StateVacuumEntity,
    VacuumActivity,
    VacuumEntityFeature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import VactidyConfigEntry
from .const import (
    CLEAN_MODES,
    DP_ACTIVATE,
    DP_BATTERY,
    DP_CLEAN_AREA,
    DP_CLEAN_MODE,
    DP_CLEAN_TIME,
    DP_COMMAND,
    DP_FAN_SPEED,
    DP_FAULT,
    DP_LOCATE,
    DP_MOP_INSTALLED,
    DP_PAUSE,
    DP_RESUME,
    DP_RETURN,
    DP_STATUS,
    DP_TOTAL_COUNT,
    DP_WATER_LEVEL,
    FAULT_CODES,
    FAN_SPEEDS,
    COMMAND_GOTO_CHARGE,
    COMMAND_SMART,
    COMMAND_STANDBY,
    STATUS_CLEANING,
    STATUS_DOCKED,
    STATUS_ERROR,
    STATUS_PAUSED,
    STATUS_RETURNING,
)
from .entity import VactidyEntity
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    VacuumEntityFeature.STATE
    | VacuumEntityFeature.BATTERY
    | VacuumEntityFeature.FAN_SPEED
    | VacuumEntityFeature.START
    | VacuumEntityFeature.PAUSE
    | VacuumEntityFeature.STOP
    | VacuumEntityFeature.RETURN_HOME
    | VacuumEntityFeature.LOCATE
    | VacuumEntityFeature.SEND_COMMAND
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: VactidyConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VactidyVacuum(coordinator)])


class VactidyVacuum(VactidyEntity, StateVacuumEntity):
    """Robot aspirador Vactidy."""

    _attr_name = None
    _attr_supported_features = SUPPORTED_FEATURES

    def __init__(self, coordinator) -> None:
        super().__init__(coordinator, "vacuum")

    # -- estado -------------------------------------------------------------

    @property
    def activity(self) -> VacuumActivity:
        status = self.dp.get(DP_STATUS)
        fault = self.dp.get(DP_FAULT) or 0
        if status in STATUS_ERROR or fault:
            return VacuumActivity.ERROR
        if status in STATUS_CLEANING:
            return VacuumActivity.CLEANING
        if status in STATUS_PAUSED:
            return VacuumActivity.PAUSED
        if status in STATUS_RETURNING:
            return VacuumActivity.RETURNING
        if status in STATUS_DOCKED:
            return VacuumActivity.DOCKED
        return VacuumActivity.IDLE

    @property
    def battery_level(self) -> int | None:
        value = self.dp.get(DP_BATTERY)
        return int(value) if value is not None else None

    @property
    def fan_speed(self) -> str | None:
        return self.dp.get(DP_FAN_SPEED)

    @property
    def fan_speed_list(self) -> list[str]:
        return list(FAN_SPEEDS)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        fault = self.dp.get(DP_FAULT) or 0
        return {
            "status": self.dp.get(DP_STATUS),
            "clean_area": self.dp.get(DP_CLEAN_AREA),
            "clean_time": self.dp.get(DP_CLEAN_TIME),
            "clean_mode": self.dp.get(DP_CLEAN_MODE),
            "water_level": self.dp.get(DP_WATER_LEVEL),
            "mop_installed": self.dp.get(DP_MOP_INSTALLED) == "installed",
            "total_clean_count": self.dp.get(DP_TOTAL_COUNT),
            "fault_code": fault,
            "fault": FAULT_CODES.get(fault) if fault else None,
        }

    # -- comandos -----------------------------------------------------------

    async def async_start(self) -> None:
        """Arranca una limpieza o reanuda la que estaba en pausa."""
        if self.activity is VacuumActivity.PAUSED:
            await self.coordinator.async_send({DP_RESUME: True})
            return
        await self.coordinator.async_send({DP_ACTIVATE: True})

    async def async_pause(self) -> None:
        await self.coordinator.async_send({DP_PAUSE: True})

    async def async_stop(self, **kwargs: Any) -> None:
        await self.coordinator.async_send({DP_COMMAND: COMMAND_STANDBY})

    async def async_return_to_base(self, **kwargs: Any) -> None:
        await self.coordinator.async_send({DP_RETURN: True})

    async def async_locate(self, **kwargs: Any) -> None:
        await self.coordinator.async_send({DP_LOCATE: True})

    async def async_set_fan_speed(self, fan_speed: str, **kwargs: Any) -> None:
        if fan_speed not in FAN_SPEEDS:
            raise ValueError(f"Potencia desconocida: {fan_speed}")
        await self.coordinator.async_send({DP_FAN_SPEED: fan_speed})

    async def async_send_command(
        self,
        command: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Comandos extra: ``smart``, ``goto_charge`` y los modos de limpieza."""
        params = params or {}
        if command in ("smart", "start") or command in CLEAN_MODES:
            await self.coordinator.async_send({DP_COMMAND: COMMAND_SMART})
            return
        if command in ("goto_charge", "charge"):
            await self.coordinator.async_send({DP_COMMAND: COMMAND_GOTO_CHARGE})
            return
        if command == "set_dp" and "dp" in params:
            await self.coordinator.async_send({int(params["dp"]): params.get("value")})
            return
        raise ValueError(f"Comando no soportado: {command}")
