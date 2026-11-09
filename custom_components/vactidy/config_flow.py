"""Flujo de configuración de Vactidy."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME

from .const import CONF_DEVICE_ID, CONF_LOCAL_KEY, CONNECT_TIMEOUT, DOMAIN, LOCAL_PORT
from .tuya_local import TuyaAuthError, TuyaConnectionError, TuyaDevice, TuyaError

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_DEVICE_ID): str,
        vol.Required(CONF_LOCAL_KEY): str,
        vol.Optional(CONF_NAME, default="Robot aspirador"): str,
    }
)

STEP_RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_LOCAL_KEY): str,
    }
)


class VactidyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta del robot pidiendo IP, identificador y clave local."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            device = TuyaDevice(
                host=user_input[CONF_HOST].strip(),
                device_id=user_input[CONF_DEVICE_ID].strip(),
                local_key=user_input[CONF_LOCAL_KEY].strip(),
                port=LOCAL_PORT,
                timeout=CONNECT_TIMEOUT,
            )
            try:
                status = await device.async_status()
            except TuyaAuthError:
                errors["base"] = "invalid_auth"
            except TuyaConnectionError:
                errors["base"] = "cannot_connect"
            except TuyaError:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(device.device_id)
                self._abort_if_unique_id_configured()
                await device.async_close()
                _LOGGER.debug("Robot validado con %d data points", len(status))
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip() or "Robot aspirador",
                    data={
                        CONF_HOST: device.host,
                        CONF_DEVICE_ID: device.device_id,
                        CONF_LOCAL_KEY: device.local_key,
                    },
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Permite cambiar IP o clave sin borrar la entrada."""
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            device = TuyaDevice(
                host=user_input[CONF_HOST].strip(),
                device_id=entry.data[CONF_DEVICE_ID],
                local_key=user_input[CONF_LOCAL_KEY].strip(),
                port=LOCAL_PORT,
                timeout=CONNECT_TIMEOUT,
            )
            try:
                await device.async_status()
            except TuyaAuthError:
                errors["base"] = "invalid_auth"
            except TuyaConnectionError:
                errors["base"] = "cannot_connect"
            except TuyaError:
                errors["base"] = "unknown"
            else:
                await device.async_close()
                return self.async_update_reload_and_abort(
                    entry,
                    data_updates={
                        CONF_HOST: device.host,
                        CONF_LOCAL_KEY: device.local_key,
                    },
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self.add_suggested_values_to_schema(
                STEP_RECONFIGURE_SCHEMA, entry.data
            ),
            errors=errors,
        )
