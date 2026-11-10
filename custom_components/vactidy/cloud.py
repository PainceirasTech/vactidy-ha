"""Obtención de la clave local a través de la API de Tuya Cloud.

La clave local es un secreto de fábrica: no se puede derivar del identificador ni
viaja por la red local, así que la única forma de conseguirla sin tocar el móvil es
pedírsela a Tuya con unas credenciales de desarrollador.  Este módulo hace esa
petición desde Home Assistant para que el usuario no tenga que navegar por el panel
web ni ejecutar herramientas de línea de comandos.

Solo se usa durante el alta: la integración sigue funcionando después sin nube.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
import uuid
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

# Centros de datos de Tuya.  El proyecto tiene que estar creado en el mismo.
REGIONS: dict[str, str] = {
    "eu": "https://openapi.tuyaeu.com",
    "us": "https://openapi.tuyaus.com",
    "cn": "https://openapi.tuyacn.com",
    "in": "https://openapi.tuyain.com",
}

TIMEOUT = 15.0

# Códigos de error que conviene traducir a un mensaje entendible.
_ERR_BAD_CREDENTIALS = {1004, 1005, 1010, 1011, 1110, 1111}
_ERR_NO_PERMISSION = {1106, 1107, 28841104}
_ERR_NO_DEVICE = {1100, 1101, 28841005}


class CloudError(Exception):
    """Fallo al hablar con la API de Tuya Cloud."""


class CloudAuthError(CloudError):
    """Las credenciales del proyecto no son válidas."""


class CloudPermissionError(CloudError):
    """El proyecto no tiene permiso sobre el dispositivo (app sin vincular)."""


class CloudDeviceNotFound(CloudError):
    """El dispositivo no aparece en la cuenta de Tuya."""


def _sign(
    client_id: str,
    client_secret: str,
    timestamp: str,
    nonce: str,
    method: str,
    path: str,
    body: str = "",
) -> str:
    """Firma HMAC-SHA256 que exige la API de Tuya."""
    content_hash = hashlib.sha256(body.encode()).hexdigest()
    string_to_sign = f"{method}\n{content_hash}\n\n{path}"
    payload = f"{client_id}{timestamp}{nonce}{string_to_sign}"
    return hmac.new(
        client_secret.encode(), payload.encode(), hashlib.sha256
    ).hexdigest().upper()


async def _request(
    session: aiohttp.ClientSession,
    base: str,
    client_id: str,
    client_secret: str,
    method: str,
    path: str,
    access_token: str | None = None,
) -> dict[str, Any]:
    """Ejecuta una llamada firmada y devuelve el bloque ``result``."""
    timestamp = str(int(time.time() * 1000))
    nonce = uuid.uuid4().hex
    url = f"{base}{path}"
    headers = {
        "client_id": client_id,
        "sign": _sign(
            client_id, client_secret, timestamp, nonce, method, path
        ),
        "t": timestamp,
        "sign_method": "HMAC-SHA256",
        "nonce": nonce,
    }
    if access_token:
        headers["access_token"] = access_token

    try:
        async with session.request(
            method, url, headers=headers, timeout=aiohttp.ClientTimeout(total=TIMEOUT)
        ) as response:
            payload = await response.json(content_type=None)
    except aiohttp.ClientError as err:
        raise CloudError(f"No se pudo contactar con Tuya: {err}") from err
    except TimeoutError as err:
        raise CloudError("Tuya no respondió a tiempo") from err

    if not isinstance(payload, dict):
        raise CloudError("Respuesta inesperada de Tuya")

    if not payload.get("success"):
        code = payload.get("code")
        message = payload.get("msg", "error desconocido")
        _LOGGER.debug("Tuya Cloud devolvió %s: %s", code, message)
        if code in _ERR_BAD_CREDENTIALS:
            raise CloudAuthError(message)
        if code in _ERR_NO_PERMISSION:
            raise CloudPermissionError(message)
        if code in _ERR_NO_DEVICE:
            raise CloudDeviceNotFound(message)
        raise CloudError(f"{code}: {message}")

    result = payload.get("result")
    return result if isinstance(result, dict) else {}


async def _token(
    session: aiohttp.ClientSession,
    base: str,
    client_id: str,
    client_secret: str,
) -> dict[str, Any]:
    """Pide un token de acceso al proyecto."""
    token = await _request(
        session,
        base,
        client_id,
        client_secret,
        "GET",
        "/v1.0/token?grant_type=1",
    )
    if not token.get("access_token"):
        raise CloudAuthError("Tuya no devolvió un token de acceso")
    return token


async def async_list_devices(
    client_id: str,
    client_secret: str,
    region: str,
) -> list[dict[str, Any]]:
    """Devuelve todos los dispositivos de la cuenta vinculada al proyecto.

    Incluye la clave local cuando Tuya la entrega, que es lo habitual para un
    dispositivo con la app vinculada y permisos de lectura.
    """
    base = REGIONS.get(region.lower())
    if base is None:
        raise CloudError(f"Región desconocida: {region}")

    async with aiohttp.ClientSession() as session:
        token = await _token(session, base, client_id, client_secret)
        uid = token.get("uid")
        if not uid:
            raise CloudError("Tuya no devolvió el identificador de la cuenta")
        result = await _request(
            session,
            base,
            client_id,
            client_secret,
            "GET",
            f"/v1.0/users/{uid}/devices",
            access_token=token["access_token"],
        )

    devices = result.get("devices")
    if not isinstance(devices, list):
        return []
    return [dev for dev in devices if isinstance(dev, dict) and dev.get("id")]


async def async_detect_region(
    client_id: str,
    client_secret: str,
    preferred_region: str = "eu",
) -> str:
    """Averigua en qué centro de datos vive el proyecto.

    El usuario rara vez recuerda si creó el proyecto en EU, US, CN o IN, y elegir
    mal produce el mismo error que unas credenciales incorrectas.  Se prueba la
    región elegida primero y luego el resto; en cuanto una acepta el token, esa es.
    """
    order = [preferred_region.lower()]
    order += [code for code in REGIONS if code not in order]

    last_error: CloudError | None = None
    for region in order:
        base = REGIONS.get(region)
        if base is None:
            continue
        try:
            async with aiohttp.ClientSession() as session:
                await _token(session, base, client_id, client_secret)
        except CloudAuthError as err:
            last_error = err
            continue
        except CloudError:
            raise
        _LOGGER.debug("El proyecto de Tuya está en la región %s", region)
        return region

    raise last_error or CloudAuthError("Ninguna región aceptó las credenciales")


async def async_find_devices(
    client_id: str,
    client_secret: str,
    preferred_region: str = "eu",
) -> tuple[str, list[dict[str, Any]]]:
    """Detecta la región y devuelve los dispositivos de la cuenta."""
    region = await async_detect_region(
        client_id, client_secret, preferred_region
    )
    devices = await async_list_devices(client_id, client_secret, region)
    return region, devices


async def async_get_local_key(
    client_id: str,
    client_secret: str,
    region: str,
    device_id: str,
) -> str:
    """Devuelve la clave local de un dispositivo de la cuenta vinculada."""
    base = REGIONS.get(region.lower())
    if base is None:
        raise CloudError(f"Región desconocida: {region}")

    async with aiohttp.ClientSession() as session:
        token = await _token(session, base, client_id, client_secret)
        device = await _request(
            session,
            base,
            client_id,
            client_secret,
            "GET",
            f"/v1.0/devices/{device_id}",
            access_token=token["access_token"],
        )

    local_key = device.get("local_key")
    if not isinstance(local_key, str) or len(local_key) != 16:
        raise CloudDeviceNotFound(
            "El dispositivo no devolvió una clave local válida"
        )
    return local_key
