"""Constantes de la integración Vactidy (robots aspiradores Tuya 3.3)."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "vactidy"
MANUFACTURER: Final = "Vactidy"
DEFAULT_NAME: Final = "Robot aspirador"

# Claves de la entrada de configuración.
CONF_DEVICE_ID: Final = "device_id"
CONF_LOCAL_KEY: Final = "local_key"

# El robot informa cada pocos segundos, pero no hace falta más resolución que
# esta para la interfaz.  El estado también se refresca tras cada comando.
SCAN_INTERVAL: Final = timedelta(seconds=30)
CONNECT_TIMEOUT: Final = 6.0
LOCAL_PORT: Final = 6668

# -- Data points ------------------------------------------------------------

DP_ACTIVATE: Final = 1  # boolean: empezar a limpiar
DP_PAUSE: Final = 2  # boolean: pausar
DP_RETURN: Final = 3  # boolean: volver a la base
DP_COMMAND: Final = 4  # string: orden de alto nivel
DP_STATUS: Final = 5  # string: estado actual
DP_CLEAN_TIME: Final = 6  # int: minutos de la limpieza en curso
DP_CLEAN_AREA: Final = 7  # int: m² de la limpieza en curso
DP_BATTERY: Final = 8  # int: porcentaje
DP_FAN_SPEED: Final = 9  # string: potencia de succión
DP_WATER_LEVEL: Final = 10  # string: caudal de la mopa
DP_LOCATE: Final = 11  # boolean: hacer sonar el robot
DP_DIRECTION: Final = 12  # string: control manual
DP_MAP_RESET: Final = 13  # boolean: borrar el mapa
DP_PATH_DATA: Final = 14  # raw: traza de la ruta
DP_REQUEST: Final = 16  # string: petición del mapa
DP_SIDE_BRUSH_LIFE: Final = 17  # int: segundos restantes
DP_SIDE_BRUSH_RESET: Final = 18  # boolean: reiniciar contador
DP_MAIN_BRUSH_LIFE: Final = 19  # int: segundos restantes
DP_MAIN_BRUSH_RESET: Final = 20  # boolean: reiniciar contador
DP_SENSOR_LIFE: Final = 21  # int: segundos restantes
DP_SENSOR_RESET: Final = 22  # boolean: reiniciar contador
DP_MOP_LIFE: Final = 23  # int: segundos restantes
DP_MOP_RESET: Final = 24  # boolean: reiniciar contador
DP_DO_NOT_DISTURB: Final = 25  # boolean: modo silencioso
DP_VOLUME: Final = 26  # int: volumen de los avisos
DP_RESUME: Final = 27  # boolean: reanudar tras pausa
DP_ERROR_FLAGS: Final = 28  # int: máscara de errores
DP_TOTAL_AREA: Final = 29  # int: m² acumulados
DP_TOTAL_COUNT: Final = 30  # int: limpiezas acumuladas
DP_TOTAL_TIME: Final = 31  # int: minutos acumulados
DP_DUST_COLLECT: Final = 37  # int: frecuencia de vaciado
DP_EMPTY_DUSTBIN: Final = 38  # boolean: vaciar el depósito
DP_CUSTOMIZE: Final = 39  # boolean: modo personalizado
DP_MOP_INSTALLED: Final = 40  # string: mopa puesta o no
DP_CLEAN_MODE: Final = 41  # string: barrer / fregar / ambas
DP_LED: Final = 130  # boolean: luz del panel
DP_DOCK_TYPE: Final = 132  # string: tipo de base
DP_FAULT: Final = 199  # int: código de avería

# -- Valores de estado ------------------------------------------------------

STATUS_CLEANING: Final = frozenset(
    {
        "smart",
        "zone_clean",
        "part_clean",
        "cleaning",
        "wall_follow",
        "select_room",
        "seek_dust_bucket",
        "collecting_dust",
        "repositing",
        "goto_pos",
        "pos_arrived",
    }
)
STATUS_PAUSED: Final = frozenset({"paused", "pos_unarrive", "direction_control"})
STATUS_RETURNING: Final = frozenset({"goto_charge"})
STATUS_DOCKED: Final = frozenset({"standby", "charging", "charge_done", "sleep"})
STATUS_ERROR: Final = frozenset({"fault"})

FAN_SPEEDS: Final = ["closed", "gentle", "normal", "strong", "max"]
FAN_SPEED_DEFAULT: Final = "normal"

WATER_LEVELS: Final = ["closed", "low", "middle", "high"]
WATER_LEVEL_NAMES: Final = {
    "closed": "closed",
    "installed": "installed",
    "low": "low",
    "middle": "middle",
    "high": "high",
}

CLEAN_MODES: Final = ["only_sweep", "only_mop", "both_work"]

COMMAND_SMART: Final = "smart"
COMMAND_STANDBY: Final = "standby"
COMMAND_GOTO_CHARGE: Final = "goto_charge"

# -- Averías ----------------------------------------------------------------

FAULT_CODES: Final = {
    21003: "dustbin_missing",
    21005: "mop_missing",
    21008: "robot_lifted",
    21012: "dustbag_full",
    21013: "dustbag_missing",
    22001: "bumper_stuck",
    22006: "robot_stuck",
    23011: "low_suction",
}

# DPs que representan un contador de vida útil, en segundos.
LIFE_DPS: Final = {
    DP_SIDE_BRUSH_LIFE: "side_brush_life",
    DP_MAIN_BRUSH_LIFE: "main_brush_life",
    DP_SENSOR_LIFE: "sensor_life",
    DP_MOP_LIFE: "mop_life",
}
