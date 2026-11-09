"""Flujo de configuración de Vactidy."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .cloud import (
    REGIONS,
    CloudAuthError,
    CloudDeviceNotFound,
    CloudError,
    CloudPermissionError,
    async_find_devices,
    async_get_local_key,
)
from .const import (
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONNECT_TIMEOUT,
    DEFAULT_NAME,
    DOMAIN,
    LOCAL_PORT,
)
from .discovery import DiscoveredDevice, discover_devices_blocking
from .tuya_local import TuyaAuthError, TuyaConnectionError, TuyaDevice, TuyaError

_LOGGER = logging.getLogger(__name__)

# Sin estos dos puntos de datos el robot no es de esta familia.
CORE_DPS = {5, 8}

# Validación de la clave local: 16 caracteres imprimibles.
LOCAL_KEY_LENGTH = 16


class VactidyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Alta del robot: detectarlo, conseguir la clave y comprobarlo."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered: DiscoveredDevice | None = None
        self._discovery_done = False
        self._cloud_key: str | None = None
        self._cloud_device_id: str | None = None
        self._cloud_devices: list[dict[str, Any]] = []
        self._cloud_region = "eu"
        self._cloud_client_id = ""
        self._cloud_client_secret = ""

    # -- utilidades ---------------------------------------------------------

    async def _async_discover(self) -> None:
        """Busca el robot una sola vez por ejecución del flujo."""
        if self._discovery_done:
            return
        self._discovery_done = True
        try:
            devices = await self.hass.async_add_executor_job(
                discover_devices_blocking, 6.0
            )
        except OSError as err:
            _LOGGER.debug("El descubrimiento falló: %s", err)
            return
        if not devices:
            _LOGGER.debug("No se encontraron robots Tuya en la red local")
            return
        # Se prefiere un robot que anuncie su product key.
        self._discovered = next(
            (dev for dev in devices if dev.product_key), devices[0]
        )
        _LOGGER.debug(
            "Robot detectado: %s en %s (%s)",
            self._discovered.device_id,
            self._discovered.host,
            self._discovered.product_key,
        )

    def _detected_text(self) -> str:
        if self._discovered is None:
            return "no"
        return f"{self._discovered.host} · {self._discovered.device_id}"

    def _local_schema(self) -> vol.Schema:
        """Formulario con lo que ya sepamos relleno."""
        device = self._discovered
        fields: dict[Any, Any] = {}

        default_host = device.host if device else None
        default_id = (
            self._cloud_device_id
            or (device.device_id if device else None)
        )

        if default_host:
            fields[vol.Required(CONF_HOST, default=default_host)] = str
        else:
            fields[vol.Required(CONF_HOST)] = str

        if default_id:
            fields[vol.Required(CONF_DEVICE_ID, default=default_id)] = str
        else:
            fields[vol.Required(CONF_DEVICE_ID)] = str

        if self._cloud_key is not None:
            fields[vol.Required(CONF_LOCAL_KEY, default=self._cloud_key)] = str
        else:
            fields[vol.Required(CONF_LOCAL_KEY)] = str
        fields[vol.Optional(CONF_NAME, default=DEFAULT_NAME)] = str
        return vol.Schema(fields)

    def _select_cloud_device(self, device: dict[str, Any]) -> None:
        """Guarda los datos del dispositivo elegido en el listado de Tuya."""
        self._cloud_device_id = str(device["id"])
        key = device.get("local_key")
        if isinstance(key, str) and len(key) == LOCAL_KEY_LENGTH:
            self._cloud_key = key

    # -- pasos --------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Menú inicial: clave a mano o pedida a Tuya Cloud."""
        await self._async_discover()
        return self.async_show_menu(
            step_id="user",
            menu_options=["local", "cloud"],
            description_placeholders={"detected": self._detected_text()},
        )

    async def async_step_local(
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
                await device.async_close()
                if status and not CORE_DPS <= status.keys():
                    errors["base"] = "unsupported_device"
                else:
                    await self.async_set_unique_id(device.device_id)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                        data={
                            CONF_HOST: device.host,
                            CONF_DEVICE_ID: device.device_id,
                            CONF_LOCAL_KEY: device.local_key,
                        },
                    )

        schema = self._local_schema()
        if user_input is not None:
            schema = self.add_suggested_values_to_schema(schema, user_input)

        return self.async_show_form(
            step_id="local",
            data_schema=schema,
            errors=errors,
            description_placeholders={"detected": self._detected_text()},
        )

    async def async_step_cloud(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Autentica con Tuya y lista los robots de la cuenta.

        Solo se piden las credenciales del proyecto.  La región se detecta sola,
        porque elegir mal el centro de datos produce el mismo error que una
        contraseña incorrecta y es un tropiezo muy habitual.
        """
        errors: dict[str, str] = {}
        schema = vol.Schema(
            {
                vol.Required("client_id"): str,
                vol.Required("client_secret"): str,
                vol.Required("region", default="eu"): SelectSelector(
                    SelectSelectorConfig(
                        options=[
                            SelectOptionDict(value=code, label=code.upper())
                            for code in REGIONS
                        ],
                        mode=SelectSelectorMode.DROPDOWN,
                    )
                ),
            }
        )

        if user_input is not None:
            try:
                region, devices = await async_find_devices(
                    client_id=user_input["client_id"].strip(),
                    client_secret=user_input["client_secret"].strip(),
                    preferred_region=user_input["region"],
                )
            except CloudAuthError:
                errors["base"] = "invalid_cloud_auth"
            except CloudPermissionError:
                errors["base"] = "cloud_not_linked"
            except CloudDeviceNotFound:
                errors["base"] = "cloud_device_not_found"
            except CloudError:
                errors["base"] = "cloud_error"
            else:
                if not devices:
                    errors["base"] = "cloud_device_not_found"
                else:
                    self._cloud_region = region
                    self._cloud_devices = devices
                    self._cloud_client_id = user_input["client_id"].strip()
                    self._cloud_client_secret = user_input["client_secret"].strip()
                    if len(devices) == 1:
                        self._select_cloud_device(devices[0])
                        return await self.async_step_local()
                    return await self.async_step_cloud_device()

        return self.async_show_form(
            step_id="cloud",
            data_schema=schema,
            errors=errors,
            description_placeholders={
                "detected": self._detected_text(),
                "device_id": (
                    self._discovered.device_id if self._discovered else ""
                ),
            },
        )

    async def async_step_cloud_device(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Deja elegir el robot cuando la cuenta tiene varios dispositivos."""
        errors: dict[str, str] = {}
        if user_input is not None:
            chosen = next(
                (
                    dev
                    for dev in self._cloud_devices
                    if str(dev.get("id")) == user_input["device"]
                ),
                None,
            )
            if chosen is None:
                errors["base"] = "cloud_device_not_found"
            else:
                self._select_cloud_device(chosen)
                if self._cloud_key is None:
                    # Tuya no entregó la clave en el listado: se pide aparte.
                    try:
                        self._cloud_key = await async_get_local_key(
                            client_id=self._cloud_client_id,
                            client_secret=self._cloud_client_secret,
                            region=self._cloud_region,
                            device_id=self._cloud_device_id or "",
                        )
                    except CloudError:
                        errors["base"] = "cloud_error"
                if not errors:
                    return await self.async_step_local()

        options = [
            SelectOptionDict(
                value=str(dev["id"]),
                label=" · ".join(
                    part
                    for part in (
                        str(dev.get("name") or dev["id"]),
                        "sin conexión" if dev.get("online") is False else None,
                    )
                    if part
                ),
            )
            for dev in self._cloud_devices
        ]

        return self.async_show_form(
            step_id="cloud_device",
            data_schema=vol.Schema(
                {
                    vol.Required("device"): SelectSelector(
                        SelectSelectorConfig(
                            options=options,
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            errors=errors,
            description_placeholders={"region": self._cloud_region.upper()},
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
                vol.Schema(
                    {
                        vol.Required(CONF_HOST): str,
                        vol.Required(CONF_LOCAL_KEY): str,
                    }
                ),
                entry.data,
            ),
            errors=errors,
        )
