"""Captura el payload que envía la app Tuya al limpiar una habitación.

Sirve para descubrir el formato del DP 16 (`request`), que es el que lleva el
identificador del mapa y de las habitaciones. Una vez conocido, se puede
replicar desde Home Assistant para lanzar la limpieza de una zona concreta.

Uso:
    1. Pon abajo el device_id, la IP y la clave local del robot.
    2. Ejecuta:  python capture_room_payload.py
    3. En el móvil, abre la app Tuya y lanza "limpiar habitación" eligiendo el salón.
    4. Copia lo que aparezca como PAYLOAD DP16.
"""

import json
import os
import time

import tinytuya

DEVICE_ID = "bf3e20ee26fbdcffd8e8kl"
IP = "192.168.5.210"
LOCAL_KEY = os.environ.get("VACTIDY_LOCAL_KEY", "")
VERSION = 3.3

INTERESANTES = ("4", "5", "16", "198")


def main() -> None:
    device = tinytuya.Device(DEVICE_ID, IP, LOCAL_KEY, version=VERSION)
    device.set_socketPersistent(True)
    device.set_socketTimeout(10)

    print("Conectando con el robot...")
    estado = device.status()
    if not estado or "dps" not in estado:
        print("No se pudo leer el estado. Revisa la clave local y la IP.")
        return
    print("Conectado. Estado actual:", json.dumps(estado["dps"], ensure_ascii=False))
    print()
    print("Escuchando cambios. Lanza ahora la limpieza de una habitación desde la app Tuya.")
    print("Pulsa Ctrl+C para terminar.")
    print()

    anteriores: dict[str, str] = {}
    while True:
        try:
            mensaje = device.receive()
        except KeyboardInterrupt:
            break
        if not isinstance(mensaje, dict):
            time.sleep(0.2)
            continue

        dps = mensaje.get("dps") or {}
        for clave in INTERESANTES:
            if clave not in dps:
                continue
            valor = str(dps[clave])
            if valor == anteriores.get(clave):
                continue
            anteriores[clave] = valor
            if clave == "16":
                print("PAYLOAD DP16:", valor)
                print("  longitud:", len(valor))
            else:
                print(f"DP{clave} = {valor}")
        time.sleep(0.2)


if __name__ == "__main__":
    main()
