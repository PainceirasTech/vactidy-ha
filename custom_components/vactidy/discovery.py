"""Descubrimiento de robots Tuya en la red local.

El robot escucha en el puerto UDP 7000 y responde a una difusión con un JSON
en claro: identificador, IP, producto y versión de firmware. La petición va en
formato de trama ``0x00006699`` con el cuerpo cifrado en AES-GCM, pero la
respuesta llega sin cifrar. La clave local nunca viaja en ese intercambio, así
que el usuario solo tiene que aportarla a mano.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import struct
import time
from dataclasses import dataclass
from hashlib import md5

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_LOGGER = logging.getLogger(__name__)

# Clave fija que comparten todos los dispositivos Tuya para el descubrimiento.
_UDP_KEY = md5(b"yGAdlopoPVldABfn").digest()
_PREFIX = 0x00006699
_SUFFIX = b"\x00\x00\x99\x66"
_CMD_REQ_DEVINFO = 37
_HEADER_FMT = ">IHIII"
_HEADER_SIZE = struct.calcsize(_HEADER_FMT)  # 18
_IV_SIZE = 12
_TAG_SIZE = 16
_DISCOVERY_PORTS = (7000, 6666, 6667)
_BROADCAST_INTERVAL = 0.6


@dataclass(frozen=True, slots=True)
class DiscoveredDevice:
    """Robot encontrado en la red local."""

    device_id: str
    host: str
    product_key: str | None = None
    version: str | None = None


def _pack_request(ip: str, seqno: int = 0) -> bytes:
    """Construye la petición de descubrimiento en formato 6699."""
    payload = json.dumps({"from": "app", "ip": ip}).encode()
    body_len = _IV_SIZE + len(payload) + _TAG_SIZE
    header = struct.pack(_HEADER_FMT, _PREFIX, 0, seqno, _CMD_REQ_DEVINFO, body_len)
    iv = os.urandom(_IV_SIZE)
    # El encabezado (menos el prefijo) autentica la trama. AESGCM devuelve
    # solo ciphertext+tag, así que el IV se antepone a mano.
    sealed = AESGCM(_UDP_KEY).encrypt(iv, payload, header[4:])
    return header + iv + sealed + _SUFFIX


def _device_from_mapping(data: dict, source_ip: str) -> DiscoveredDevice | None:
    """Extrae los datos del robot de un diccionario ya decodificado."""
    device_id = data.get("gwId") or data.get("devId") or data.get("id")
    if not device_id or not isinstance(device_id, str):
        return None
    return DiscoveredDevice(
        device_id=device_id,
        host=data.get("ip") or source_ip,
        product_key=data.get("productKey"),
        version=data.get("version"),
    )


def _decrypt_55aa(raw: bytes) -> dict | None:
    """Descifra una respuesta con el formato clásico 55AA y AES-ECB."""
    if len(raw) < 24 or raw[:4] != b"\x00\x00U\xaa":
        return None
    length = struct.unpack(">I", raw[12:16])[0]
    body = raw[16 : 16 + length - 8]
    if not body:
        return None
    for offset in (4, 0):
        chunk = body[offset:]
        if not chunk or len(chunk) % 16:
            continue
        try:
            decryptor = Cipher(algorithms.AES(_UDP_KEY), modes.ECB()).decryptor()
            plain = decryptor.update(chunk) + decryptor.finalize()
            padding = plain[-1]
            if 1 <= padding <= 16:
                plain = plain[:-padding]
            data = json.loads(plain)
        except (ValueError, UnicodeDecodeError):
            continue
        if isinstance(data, dict):
            return data
    return None


def _parse_response(raw: bytes, source_ip: str) -> DiscoveredDevice | None:
    """Interpreta una respuesta de descubrimiento.

    Según el firmware, el robot contesta con un JSON en claro, con la trama
    clásica 55AA cifrada en AES-ECB o con la trama 6699 cifrada en AES-GCM.
    """
    try:
        plain = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        plain = None
    if isinstance(plain, dict):
        return _device_from_mapping(plain, source_ip)

    data = _decrypt_55aa(raw)
    if data is not None:
        return _device_from_mapping(data, source_ip)

    if len(raw) < _HEADER_SIZE + _IV_SIZE + _TAG_SIZE + 4:
        return None
    prefix, _zero, _seq, _cmd, length = struct.unpack(
        _HEADER_FMT, raw[:_HEADER_SIZE]
    )
    if prefix != _PREFIX:
        return None

    body = raw[_HEADER_SIZE : _HEADER_SIZE + length]
    if len(body) < _IV_SIZE + _TAG_SIZE + 4 or body[-4:] != _SUFFIX:
        return None
    iv = body[:_IV_SIZE]
    ciphertext = body[_IV_SIZE:-_TAG_SIZE - 4]
    tag = body[-_TAG_SIZE - 4 : -4]
    try:
        decoded = AESGCM(_UDP_KEY).decrypt(iv, ciphertext + tag, raw[4:_HEADER_SIZE])
        data = json.loads(decoded)
    except Exception:  # noqa: BLE001 - cualquier fallo es una trama ajena
        return None
    return _device_from_mapping(data, source_ip) if isinstance(data, dict) else None


def _local_ip() -> str | None:
    """IP de la interfaz que sale a Internet, sin enviar tráfico real."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def _local_ips() -> list[str]:
    """Direcciones IPv4 de todas las interfaces del equipo."""
    addresses: set[str] = set()
    probe_ip = _local_ip()
    if probe_ip:
        addresses.add(probe_ip)
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(info[4][0])
    except OSError:
        pass
    return sorted(ip for ip in addresses if not ip.startswith("127."))


def _broadcast_targets() -> list[str]:
    """Difusiones útiles, una por interfaz, más la global."""
    targets = {"255.255.255.255"}
    for ip in _local_ips():
        if ip.count(".") == 3:
            targets.add(f"{ip.rsplit('.', 1)[0]}.255")
    return sorted(targets)


def discover_devices_blocking(timeout: float = 3.0) -> list[DiscoveredDevice]:
    """Busca robots en la red local. Bloquea, así que se llama en un executor.

    El robot no contesta al puerto de origen: emite su respuesta a los puertos
    fijos 6666, 6667 y 7000, así que hay que escuchar en ellos.
    """
    found: dict[str, DiscoveredDevice] = {}
    sockets: list[tuple[socket.socket, int]] = []

    for port in _DISCOVERY_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("", port))
        except OSError as err:
            _LOGGER.debug("No se pudo escuchar en el puerto %s: %s", port, err)
            sock.close()
            continue
        sock.setblocking(False)
        sockets.append((sock, port))

    targets = _broadcast_targets()
    local_ip = _local_ip() or "0.0.0.0"

    try:
        deadline = time.monotonic() + timeout
        next_broadcast = 0.0
        seqno = 0
        while time.monotonic() < deadline:
            now = time.monotonic()
            if now >= next_broadcast:
                payload = _pack_request(local_ip, seqno)
                seqno += 1
                for sock, _port in sockets:
                    for target in targets:
                        try:
                            # La petición se dirige al puerto de la aplicación.
                            sock.sendto(payload, (target, _DISCOVERY_PORTS[0]))
                        except OSError:
                            pass
                next_broadcast = now + _BROADCAST_INTERVAL

            for sock, _port in sockets:
                while True:
                    try:
                        raw, address = sock.recvfrom(4096)
                    except (BlockingIOError, InterruptedError, OSError):
                        break
                    device = _parse_response(raw, address[0])
                    if device is not None:
                        found[device.device_id] = device
            time.sleep(0.02)
    finally:
        for sock, _port in sockets:
            sock.close()

    _LOGGER.debug("Descubiertos %d dispositivos: %s", len(found), list(found))
    return list(found.values())
