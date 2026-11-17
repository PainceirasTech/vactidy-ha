#!/usr/bin/env python3
"""Control local del robot Vactidy Cleanova W15 desde Home Assistant.

Habla el protocolo Tuya 3.3 directamente con el robot (puerto 6668) y usa el
canal de comandos del mapa (DP15 con tramas base64) para lanzar la limpieza de
una habitacion concreta.

Ejemplos:
    python3 vactidy_room.py --list
    python3 vactidy_room.py --clean 3
    python3 vactidy_room.py --clean 3 --host 192.168.5.210

Variables de entorno equivalentes a los argumentos:
    VACTIDY_HOST, VACTIDY_DEVICE_ID, VACTIDY_LOCAL_KEY
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import binascii
import hashlib
import json
import os
import struct
import sys
import time
import urllib.parse
from typing import Any

# --- protocolo Tuya 3.3 ----------------------------------------------------

PREFIX = 0x000055AA
SUFFIX = 0x0000AA55
HEADER_FMT = ">4I"
END_FMT = ">2I"
PROTOCOL_33_HEADER = b"3.3" + b"\x00" * 12
CMD_CONTROL = 0x07
CMD_DP_QUERY = 0x0A
DP_QUERY_COMMANDS = {CMD_DP_QUERY, 0x09, 0x10}

DEFAULT_HOST = "192.168.5.210"
DEFAULT_DEVICE_ID = "bf3e20ee26fbdcffd8e8kl"


class RobotError(Exception):
    """Fallo hablando con el robot."""


def _aes(local_key: str):
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    raw = local_key.encode("latin1")
    key = raw if len(raw) == 16 else hashlib.md5(raw).digest()
    return Cipher(algorithms.AES(key), modes.ECB())


def _encrypt(cipher, raw: bytes) -> bytes:
    pad = 16 - len(raw) % 16
    encryptor = cipher.encryptor()
    return encryptor.update(raw + bytes([pad]) * pad) + encryptor.finalize()


def _decrypt(cipher, raw: bytes) -> bytes:
    decryptor = cipher.decryptor()
    data = decryptor.update(raw) + decryptor.finalize()
    pad = data[-1]
    if not 1 <= pad <= 16:
        raise ValueError("relleno invalido")
    return data[:-pad]


# --- tramas del protocolo de mapa -----------------------------------------

def frame_std(cmd: str, data: str = "") -> str:
    """Trama estandar v1: aa 01 + longitud (8 hex) + cmd + datos + checksum."""
    body = cmd + data
    total = sum(int(body[i : i + 2], 16) for i in range(0, len(body), 2)) % 256
    return f"aa01{len(body) // 2:08x}{body}{total:02x}"


def frame_ext(cmd: str, data: str = "") -> str:
    """Trama extendida: ab 00 + longitud (8 hex) + cmd + datos + checksum."""
    body = cmd + data
    total = sum(int(body[i : i + 2], 16) for i in range(0, len(body), 2)) % 256
    return f"ab00{len(body) // 2:08x}{body}{total:02x}"


def to_b64(hexstr: str) -> str:
    return base64.b64encode(bytes.fromhex(hexstr)).decode()


def frame_room_clean(room_ids: list[int], times: int = 1) -> str:
    """cmd 0x14: veces | numero de habitaciones | ids."""
    data = f"{times:02x}{len(room_ids):02x}" + "".join(f"{i:02x}" for i in room_ids)
    return frame_std("14", data)


def frame_use_map(map_id: int, url: str) -> str:
    """Comando extendido 0x2e: pedir al robot que cargue un mapa de la nube."""
    url_bytes = url.encode("utf-8")
    data = f"{map_id & 0xFFFFFFFF:08x}{len(url_bytes):08x}{url_bytes.hex()}"
    return frame_ext("2e", data)


def parse_room_names(payload: bytes) -> list[dict[str, Any]]:
    """cmd 0x25: un byte de recuento y bloques de 21 bytes por habitacion."""
    if len(payload) < 9 or payload[0] != 0xAA or payload[6] != 0x25:
        return []
    body = payload[8:-1].hex()
    rooms = []
    for chunk in [body[i : i + 42] for i in range(0, len(body), 42)]:
        if len(chunk) < 42:
            break
        try:
            name = urllib.parse.unquote(
                bytes.fromhex(chunk[4:]).decode("latin1")
            ).strip()
        except (ValueError, UnicodeDecodeError):
            name = ""
        rooms.append({"roomId": int(chunk[0:2], 16), "name": name})
    return rooms


# --- cliente ---------------------------------------------------------------

class Robot:
    def __init__(
        self,
        host: str,
        device_id: str,
        local_key: str,
        timeout: float = 6.0,
        retries: int = 1,
        retry_delay: float = 4.0,
    ):
        self.host = host
        self.device_id = device_id
        self.timeout = timeout
        self.retries = max(1, retries)
        self.retry_delay = retry_delay
        self._cipher = _aes(local_key)
        self._seq = 1
        self._reader = None
        self._writer = None

    async def __aenter__(self) -> "Robot":
        last: Exception | None = None
        for attempt in range(self.retries):
            try:
                self._reader, self._writer = await asyncio.wait_for(
                    asyncio.open_connection(self.host, 6668), self.timeout
                )
                return self
            except OSError as err:
                last = err
                if attempt + 1 < self.retries:
                    await asyncio.sleep(self.retry_delay)
        raise RobotError(f"no se pudo conectar a {self.host}: {last}") from last

    async def __aexit__(self, *_exc) -> None:
        writer, self._writer = self._writer, None
        self._reader = None
        if writer is None:
            return
        try:
            writer.close()
            await asyncio.wait_for(writer.wait_closed(), 2)
        except (OSError, asyncio.TimeoutError):
            pass

    def _pack(self, command: int, payload: dict[str, Any]) -> bytes:
        body = _encrypt(self._cipher, json.dumps(payload, separators=(",", ":")).encode())
        if command not in DP_QUERY_COMMANDS:
            body = PROTOCOL_33_HEADER + body
        header = struct.pack(HEADER_FMT, PREFIX, self._seq, command, len(body) + 8)
        self._seq = self._seq % 0xFFFFFFFF + 1
        crc = binascii.crc32(header + body) & 0xFFFFFFFF
        return header + body + struct.pack(END_FMT, crc, SUFFIX)

    def _decode_body(self, raw: bytes) -> dict[str, Any]:
        if len(raw) <= 4:
            return {}
        for offset in range(0, max(1, len(raw) - 15)):
            candidate = raw[offset:]
            if len(candidate) % 16:
                continue
            try:
                data = json.loads(_decrypt(self._cipher, candidate))
            except (ValueError, UnicodeDecodeError, binascii.Error):
                continue
            if isinstance(data, dict):
                return data
        raise RobotError("respuesta ilegible: comprueba la clave local")

    async def _read_frame(self) -> tuple[int, bytes]:
        head = await self._reader.readexactly(16)
        _prefix, _seq, command, length = struct.unpack(HEADER_FMT, head)
        body = await self._reader.readexactly(length)
        return command, body[:-8]

    async def send_dps(self, dps: dict[int, Any]) -> dict[int, Any]:
        """Envia data points y devuelve los que conteste el robot."""
        self._writer.write(
            self._pack(
                CMD_CONTROL,
                {
                    "devId": self.device_id,
                    "uid": self.device_id,
                    "t": str(int(time.time())),
                    "dps": {str(k): v for k, v in dps.items()},
                },
            )
        )
        await self._writer.drain()
        data = self._decode_body((await self._read_frame())[1])
        return {int(k): v for k, v in (data.get("dps") or {}).items()}

    async def status(self) -> dict[int, Any]:
        self._writer.write(
            self._pack(
                CMD_DP_QUERY,
                {
                    "gwId": self.device_id,
                    "devId": self.device_id,
                    "uid": self.device_id,
                    "t": str(int(time.time())),
                },
            )
        )
        await self._writer.drain()
        data = self._decode_body((await self._read_frame())[1])
        return {int(k): v for k, v in (data.get("dps") or {}).items()}

    async def command_frames(self, hexstr: str, seconds: float = 8.0) -> list[bytes]:
        """Manda una trama por DP15 y recoge las tramas que devuelva el robot."""
        await self.send_dps({15: to_b64(hexstr)})
        frames: list[bytes] = []
        deadline = time.time() + seconds
        while time.time() < deadline:
            try:
                raw = await asyncio.wait_for(self._read_frame(), 1.0)
            except asyncio.TimeoutError:
                continue
            except (asyncio.IncompleteReadError, OSError):
                break
            data = self._decode_body(raw[1])
            value = (data.get("dps") or {}).get("15")
            if isinstance(value, str):
                try:
                    frames.append(base64.b64decode(value))
                except (ValueError, binascii.Error):
                    pass
        return frames

    async def rooms(self) -> list[dict[str, Any]]:
        for payload in await self.command_frames(frame_std("24", "00")):
            found = parse_room_names(payload)
            if found:
                return found
        return []

    async def clean_room(self, room_id: int, times: int = 1) -> dict[str, Any]:
        await self.send_dps({4: "select_room"})
        await asyncio.sleep(1)
        await self.command_frames(frame_room_clean([room_id], times), seconds=4)
        await asyncio.sleep(1)
        state = await self.status()
        if state.get(4) != "select_room":
            raise RobotError(
                f"el robot no acepto la habitacion {room_id} (dp4={state.get(4)})"
            )
        await self.send_dps({1: True})
        await asyncio.sleep(3)
        return await self.status()

    async def use_map(self, map_id: int, url: str) -> list[bytes]:
        """Carga en el robot un mapa guardado en la nube (comando 0x2e)."""
        return await self.command_frames(frame_use_map(map_id, url), seconds=12)

    async def start_clean(self, speed: str | None = None) -> dict[str, Any]:
        dps: dict[int, Any] = {}
        if speed:
            dps[9] = speed
        if dps:
            await self.send_dps(dps)
            await asyncio.sleep(1)
        await self.send_dps({1: True})
        await asyncio.sleep(3)
        return await self.status()

    async def pause(self) -> dict[str, Any]:
        await self.send_dps({2: True})
        await asyncio.sleep(2)
        return await self.status()

    async def go_home(self) -> dict[str, Any]:
        await self.send_dps({3: True})
        await asyncio.sleep(3)
        return await self.status()

    async def stop_clean(self) -> dict[str, Any]:
        """Para la limpieza y manda el robot a la base.

        ``DP4="standby"`` no detiene una limpieza en marcha, asi que se pausa
        primero y despues se ordena volver a la base.
        """
        await self.send_dps({2: True})
        await asyncio.sleep(2)
        await self.send_dps({4: "goto_charge"})
        await asyncio.sleep(3)
        state = await self.status()
        if state.get(5) not in ("goto_charge", "charging", "charge_done"):
            await self.send_dps({3: True})
            await asyncio.sleep(3)
            state = await self.status()
        return state


async def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--list", action="store_true", help="lista las habitaciones")
    parser.add_argument("--clean", type=int, metavar="ID", help="limpia esa habitacion")
    parser.add_argument("--times", type=int, default=1, help="pasadas (por defecto 1)")
    parser.add_argument("--auto", action="store_true", help="limpieza completa")
    parser.add_argument(
        "--speed",
        choices=["closed", "gentle", "normal", "strong", "max"],
        help="potencia de succion al arrancar",
    )
    parser.add_argument("--pause", action="store_true", help="pausar")
    parser.add_argument("--resume", action="store_true", help="continuar tras pausa")
    parser.add_argument("--dock", action="store_true", help="volver a la base")
    parser.add_argument("--stop", action="store_true", help="detener")
    parser.add_argument(
        "--stop-dock",
        action="store_true",
        help="parar la limpieza y volver a la base (pausa + recarga)",
    )
    parser.add_argument("--map", dest="map_id", type=int, help="id del mapa de la nube")
    parser.add_argument("--url", help="URL del mapa (con --map)")
    parser.add_argument("--host", default=os.environ.get("VACTIDY_HOST", DEFAULT_HOST))
    parser.add_argument(
        "--device-id", default=os.environ.get("VACTIDY_DEVICE_ID", DEFAULT_DEVICE_ID)
    )
    parser.add_argument("--local-key", default=os.environ.get("VACTIDY_LOCAL_KEY", ""))
    parser.add_argument(
        "--retries",
        type=int,
        default=1,
        help="intentos de conexion (util si Home Assistant ocupa la sesion)",
    )
    args = parser.parse_args()

    if not args.local_key:
        print("Falta la clave local (--local-key o VACTIDY_LOCAL_KEY)", file=sys.stderr)
        return 2
    if len(args.local_key) != 16:
        print(
            f"La clave local debe tener 16 caracteres (tiene {len(args.local_key)}): "
            "revisa comillas o espacios en el fichero de entorno",
            file=sys.stderr,
        )
        return 2

    async with Robot(
        args.host, args.device_id, args.local_key, retries=args.retries
    ) as robot:
        if args.map_id is not None:
            if not args.url:
                print("Falta --url junto a --map", file=sys.stderr)
                return 2
            replies = await robot.use_map(args.map_id, args.url)
            if not replies:
                print("el robot no contesto al comando de mapa")
                return 1
            for raw in replies:
                print(f"respuesta: {binascii.hexlify(raw).decode()}")
            if not (args.auto or args.speed):
                return 0
        if args.auto or args.speed:
            state = await robot.start_clean(args.speed)
            print(f"limpieza lanzada: dp4={state.get(4)} dp5={state.get(5)}")
            return 0
        if args.pause:
            state = await robot.pause()
            print(f"pausado: dp5={state.get(5)}")
            return 0
        if args.resume:
            state = await robot.start_clean()
            print(f"continuado: dp5={state.get(5)}")
            return 0
        if args.dock:
            state = await robot.go_home()
            print(f"volviendo a la base: dp5={state.get(5)}")
            return 0
        if args.stop_dock:
            state = await robot.stop_clean()
            print(f"parando y volviendo a la base: dp4={state.get(4)} dp5={state.get(5)}")
            return 0
        if args.stop:
            await robot.send_dps({4: "standby"})
            print("detenido")
            return 0
        if args.clean is not None:
            state = await robot.clean_room(args.clean, args.times)
            print(f"limpieza lanzada: dp4={state.get(4)} dp5={state.get(5)}")
            return 0
        rooms = await robot.rooms()
        if not rooms:
            print("sin habitaciones: aplica un mapa guardado en la app de Tuya")
            return 1
        for room in rooms:
            print(f"{room['roomId']}\t{room['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
