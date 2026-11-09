"""Minimal asyncio client for the Tuya LAN protocol (3.3).

Only the subset needed to talk to robot vacuums is implemented: query the
current data points and push new ones.  No cloud connection is involved.
"""

from __future__ import annotations

import asyncio
import binascii
import hashlib
import json
import logging
import struct
import time
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

_LOGGER = logging.getLogger(__name__)

PREFIX = 0x000055AA
SUFFIX = 0x0000AA55
HEADER_FMT = ">4I"
END_FMT = ">2I"
HEADER_SIZE = struct.calcsize(HEADER_FMT)
FOOTER_SIZE = struct.calcsize(END_FMT)

CMD_CONTROL = 0x07
CMD_STATUS = 0x08
CMD_HEART_BEAT = 0x09
CMD_DP_QUERY = 0x0A
CMD_DP_QUERY_NEW = 0x10

PROTOCOL_33_HEADER = b"3.3" + b"\x00" * 12
MAX_PAYLOAD = 8192

DP_QUERY_COMMANDS = frozenset({CMD_DP_QUERY, CMD_DP_QUERY_NEW, CMD_HEART_BEAT})


class TuyaError(Exception):
    """Base error for the local Tuya protocol."""


class TuyaAuthError(TuyaError):
    """The device rejected the local key."""


class TuyaConnectionError(TuyaError):
    """The device could not be reached."""


def _aes(local_key: str) -> Cipher:
    """Construye el cifrador AES-128-ECB usado por el protocolo local.

    En Tuya 3.3 la clave es la propia ``localKey`` (16 caracteres ASCII), no un
    hash.  Solo si llega una clave de longitud inesperada se recurre al MD5.
    """
    raw = local_key.encode("latin1")
    key = raw if len(raw) == 16 else hashlib.md5(raw).digest()
    return Cipher(algorithms.AES(key), modes.ECB())


def _encrypt(cipher: Cipher, raw: bytes) -> bytes:
    pad = 16 - len(raw) % 16
    padded = raw + bytes([pad]) * pad
    encryptor = cipher.encryptor()
    return encryptor.update(padded) + encryptor.finalize()


def _decrypt(cipher: Cipher, raw: bytes) -> bytes:
    decryptor = cipher.decryptor()
    data = decryptor.update(raw) + decryptor.finalize()
    if not data:
        return data
    pad = data[-1]
    if pad < 1 or pad > 16 or data[-pad:] != bytes([pad]) * pad:
        raise TuyaError("Invalid PKCS#7 padding in device response")
    return data[:-pad]


class TuyaDevice:
    """A single Tuya device reachable over the local network."""

    def __init__(
        self,
        host: str,
        device_id: str,
        local_key: str,
        *,
        port: int = 6668,
        timeout: float = 6.0,
    ) -> None:
        self.host = host
        self.device_id = device_id
        self.local_key = local_key
        self.port = port
        self.timeout = timeout

        self._cipher = _aes(local_key)
        self._seq = 1
        self._lock = asyncio.Lock()
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    # -- connection handling ------------------------------------------------

    async def async_connect(self) -> None:
        """Open the TCP connection to the device."""
        if self._writer is not None and not self._writer.is_closing():
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), self.timeout
            )
        except (OSError, asyncio.TimeoutError) as err:
            raise TuyaConnectionError(
                f"Cannot connect to {self.host}:{self.port}: {err}"
            ) from err

    async def async_close(self) -> None:
        """Close the TCP connection, ignoring errors."""
        writer, self._writer = self._writer, None
        self._reader = None
        if writer is None:
            return
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), 2)
        except (OSError, asyncio.TimeoutError):
            pass

    # -- low level framing --------------------------------------------------

    def _pack(self, command: int, payload: dict[str, Any]) -> bytes:
        raw = json.dumps(payload, separators=(",", ":")).encode()
        body = _encrypt(self._cipher, raw)
        if command not in DP_QUERY_COMMANDS:
            body = PROTOCOL_33_HEADER + body
        header = struct.pack(HEADER_FMT, PREFIX, self._seq, command, len(body) + 8)
        self._seq = self._seq % 0xFFFFFFFF + 1
        crc = binascii.crc32(header + body) & 0xFFFFFFFF
        return header + body + struct.pack(END_FMT, crc, SUFFIX)

    async def _read_frame(self) -> tuple[int, bytes]:
        """Lee una trama y devuelve ``(comando, cuerpo en bruto)``.

        El cuerpo llega con combinaciones distintas según el comando: solo el
        código de retorno, el retorno más la cabecera de versión, o el
        ciphertext a secas. El desempaquetado se resuelve en ``_decode_body``.
        """
        assert self._reader is not None
        head = await self._reader.readexactly(HEADER_SIZE)
        prefix, _seq, command, length = struct.unpack(HEADER_FMT, head)
        if prefix != PREFIX:
            raise TuyaError(f"Unexpected frame prefix 0x{prefix:08X}")
        if not FOOTER_SIZE < length <= MAX_PAYLOAD:
            raise TuyaError(f"Unexpected frame length {length}")
        body = await self._reader.readexactly(length)
        return command, body[:-FOOTER_SIZE]

    def _decode_body(self, raw: bytes) -> dict[str, Any]:
        """Descifra el cuerpo probando los desfases posibles de la cabecera.

        Un ACK de control son solo 4 bytes de código de retorno, sin nada que
        descifrar. En el resto de casos se prueban los desfases habituales
        (retorno, cabecera 3.3, ambos) y se acepta el primero que produzca un
        objeto JSON.
        """
        if len(raw) <= 4:
            return {}
        for offset in range(0, 25):
            candidate = raw[offset:]
            if not candidate or len(candidate) % 16:
                continue
            try:
                data = json.loads(_decrypt(self._cipher, candidate))
            except (ValueError, UnicodeDecodeError, TuyaError):
                continue
            if isinstance(data, dict):
                return data
        raise TuyaAuthError(
            "Device answered with undecryptable data, check the local key"
        )

    async def _drain_pending(self) -> None:
        """Descarta tramas huérfanas antes de enviar una petición nueva.

        El robot manda el estado espontáneamente tras cada control; si no se
        vacía el búfer, la siguiente consulta leería esa respuesta atrasada.
        """
        assert self._reader is not None
        while True:
            try:
                chunk = await asyncio.wait_for(self._reader.read(4096), 0.01)
            except asyncio.TimeoutError:
                return
            if not chunk:
                return

    async def _request(self, command: int, payload: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            await self.async_connect()
            assert self._writer is not None
            await self._drain_pending()
            self._writer.write(self._pack(command, payload))
            await self._writer.drain()

            deadline = asyncio.get_running_loop().time() + self.timeout
            while True:
                remaining = deadline - asyncio.get_running_loop().time()
                if remaining <= 0:
                    raise TuyaConnectionError(
                        f"{self.device_id} did not answer in {self.timeout:.0f}s"
                    )
                try:
                    reply_cmd, body = await asyncio.wait_for(
                        self._read_frame(), remaining
                    )
                except asyncio.TimeoutError as err:
                    raise TuyaConnectionError(
                        f"{self.device_id} did not answer in {self.timeout:.0f}s"
                    ) from err
                except (asyncio.IncompleteReadError, OSError) as err:
                    await self.async_close()
                    raise TuyaConnectionError(
                        f"Connection lost with {self.device_id}: {err}"
                    ) from err

                if reply_cmd == CMD_HEART_BEAT:
                    continue
                data = self._decode_body(body)
                if not data:
                    # ACK de control: sin cuerpo, el comando se ha aceptado.
                    return {"dps": {}}
                if data.get("Error") or data.get("error"):
                    raise TuyaError(
                        f"{self.device_id} reported: "
                        f"{data.get('Error') or data.get('error')}"
                    )
                if data.get("dps") is not None:
                    return data
                    return data

    # -- public API ---------------------------------------------------------

    async def async_status(self) -> dict[int, Any]:
        """Return the current ``{dp_id: value}`` mapping."""
        data = await self._request(
            CMD_DP_QUERY,
            {
                "gwId": self.device_id,
                "devId": self.device_id,
                "uid": self.device_id,
                # El SDK de Tuya espera el timestamp como cadena, no como entero.
                "t": str(int(time.time())),
            },
        )
        # JSON devuelve las claves como texto; el resto del código trabaja con int.
        return {int(dp): value for dp, value in data["dps"].items()}

    async def async_set_dps(self, dps: dict[int, Any]) -> dict[int, Any]:
        """Send new data point values and return what the device reports."""
        data = await self._request(
            CMD_CONTROL,
            {
                "devId": self.device_id,
                "uid": self.device_id,
                # Igual que en la consulta, el SDK espera "t" como cadena.
                "t": str(int(time.time())),
                "dps": {str(dp): value for dp, value in dps.items()},
            },
        )
        return {int(dp): value for dp, value in (data.get("dps") or {}).items()}
