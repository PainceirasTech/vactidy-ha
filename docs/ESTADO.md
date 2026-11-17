# Estado del proyecto Vactidy — 15/11/2026

Documento de traspaso técnico. Recoge lo que está verificado contra el robot real,
lo que se ha descartado con pruebas y lo que queda pendiente.

## 1. Hardware y red

| Dato | Valor |
|---|---|
| Robot | Vactidy Cleanova W15 (Tuya/Proscenic por dentro) |
| `device_id` | `bf3e20ee26fbdcffd8e8kl` |
| IP | `192.168.5.210` |
| Puerto | `6668` (TCP) |
| Protocolo Tuya | **3.3** (con 3.4 y 3.5 responde `914 Check device key or version`) |
| `product_id` | `ut96oplbcckfxwwu` |
| App actual | Tuya Smart (migrado desde la app Vactidy) |
| Integración HA | `tuya-local`, perfil autodetectado `lubluelu_sl60d_vacuum` (75 %) |
| Mapas | 2 guardados en la app: «Salón» y «Cocina» (plantas distintas) |

La `local_key` se regenera cada vez que se re-empareja el robot. No se guarda en el
repositorio: se pasa por `--local-key` o por la variable `VACTIDY_LOCAL_KEY`.

## 2. Canales de control

### 2.1 Data points (Tuya estándar)

Los que usa la integración: `1` arrancar, `2` pausar, `3` volver a la base,
`4` comando (`smart`, `select_room`, `standby`, `goto_charge`…), `5` estado,
`8` batería, `9` potencia de succión, `10` nivel de agua, `41` modo de limpieza,
`199` código de avería.

Comandos verificados con el cliente propio:

| Acción | DP | Resultado |
|---|---|---|
| Empezar | `1 = true` | `dp5 = smart` |
| Pausar | `2 = true` | `dp5 = paused` |
| Reanudar | `1 = true` sobre pausa | `dp5 = smart` |
| Volver a la base | `3 = true` | `dp5 = goto_charge` |
| Detener | `4 = standby` | no saca al robot de `fault` |
| Velocidad | `9 = closed/gentle/normal/strong/max` | aplica al momento |

Aviso: `4 = goto_charge` **estando limpiando no hace nada** (el robot sigue en
`smart`). La secuencia que sí funciona es `4 = standby` y después `4 = goto_charge`,
o bien `3 = true` y esperar.

### 2.2 Protocolo de mapa por DP15

El robot publica en **DP15** (string base64) tramas del protocolo de mapa. Formato
(confirmado contra la librería `@ray-js/robot-protocol` que usa el panel de Tuya):

```
estándar:  aa | 01 (v1) | longitud 8 hex | cmd | datos | checksum (suma % 256)
extendida: ab | 00 | longitud 8 hex | cmd | datos | checksum
```

Tramas que emite el robot espontáneamente tras cualquier escritura:

| Trama | Significado |
|---|---|
| `aa01000000034901004a` | `0x49` muros virtuales |
| `aa010000002a39…` | `0x39` zonas prohibidas (contiene el nombre de la zona, p. ej. «Cables») |
| `aa01000000011717` | `0x17` limpieza puntual |
| `aa01000000033b03003e` | `0x3b` respuesta de limpieza por zona |

Las tramas se envían por **DP15**; escribir en DP16 (`get_map`, `get_both`,
`get_path`) no devuelve nada útil: solo provoca el trío de arriba.

### 2.3 Comandos de mapa (librería Tuya)

| Comando | Dirección | Función |
|---|---|---|
| `0x2a` / `0x2b` | app → robot | guardar mapa en una ranura (`saveSpace`, 1 byte) |
| `0x2c` / `0x2d` | app → robot | borrar mapa (`mapId`, 4 bytes) |
| `0x2e` / `0x2f` | app → robot | **usar mapa**: `mapId` (4 bytes) + longitud (4) + URL del mapa |
| `0x14` / `0x15` | app → robot | limpiar habitaciones (v1): veces + nº + ids |
| `0x56` / `0x57` | app → robot | limpiar habitaciones (v2): bloques de 10 hex por habitación |
| `0x24` / `0x25` | app → robot | nombres de habitación (bloques de 42 hex) |
| `0x1c` / `0x1d` | app → robot | dividir habitaciones |
| `0x3a` / `0x3b` | app → robot | limpieza por zona |

El robot de este proyecto es **v3**, así que usa las variantes **v2** (`0x56`/`0x57`)
cuando la app trabaja con habitaciones.

## 3. El problema de las habitaciones (conclusión definitiva)

**Las habitaciones no existen dentro del robot.** Se comprobó:

- `0x25` (nombres) devuelve siempre **0 habitaciones**, con el robot en la base,
  limpiando, con `cloud_map` activado y con los dos mapas guardados en la app.
- `0x24`, `0x56`, `0x57`, `0x1c`, `0x15` no devuelven ninguna lista de habitaciones.
- Durante una limpieza real, el robot solo publica muros, zonas prohibidas y
  limpieza puntual: **ningún frame de mapa**.
- `0x2a` (guardar mapa en ranura) responde `ret=0` cuando no hay mapa estable.

El mapa y sus habitaciones los genera la **app** a partir del mapa que descarga de
la nube de Tuya, y se los pasa al robot con `0x2e` (mapId + URL). Sin ese comando
el robot no conoce ningún id de habitación, así que `0x14` con un id inventado
acaba en limpieza completa.

Consecuencia: **la limpieza por habitación no se puede montar solo con el canal
local**. Hace falta el mapa.

Lo que sí está en el robot (y por tanto sobrevive sin nube) son los **muros
virtuales** (`0x49`) y las **zonas prohibidas** (`0x39`), ligados al mapa activo.

## 4. Vías descartadas (no volver a intentarlas)

| Vía | Motivo del descarte |
|---|---|
| Escenas Tap-to-Run de la app Tuya | Solo exponen data points; no hay acción de habitación. El skill de Alexa tampoco. |
| `mitmproxy` con el móvil | La app rechaza el certificado de usuario (Android 7+) y no se captura tráfico útil. |
| Login en la API de la app (`a1.tuyaeu.com`) | Firma HMAC con `secret2`, derivable solo con ingeniería inversa del `.so`; no se obtuvo. |
| Extraer la `local_key` del móvil como producto | Requiere root o copia de seguridad completa; inviable para un usuario final. |
| Integración propia `vactidy-ha` como producto | El usuario final no puede obtener la clave sin root; PR de HACS cerrado. |
| `DP137` (`cloud map switch`) | Activa el interruptor, pero no descarga el mapa. |

## 5. Vía pendiente: API de nube de robot aspirador

Tuya publica endpoints específicos de aspirador:

```
GET /v1.0/users/sweepers/file/{device_id}/list
GET /v1.0/users/sweepers/file/{device_id}/download
GET /v1.0/users/sweepers/file/{device_id}/realtime-map?map_type=0
```

`map_type`: 0 layout, 1 ruta, 2 ruta incremental, 3 planificación.

Requieren suscribir **Robot Vacuum Open APIs** en el proyecto de `iot.tuya.com`,
además de IoT Core (la prueba caduca el 10/12/2026 y se puede renovar).

Si el fichero descargado es el mismo hex que decodifica la app, se pueden sacar los
`roomId` y los nombres, y a partir de ahí la limpieza por habitación se lanza en
local con `0x14`/`0x56` sin depender de la nube al usarla. La decodificación está
descrita en la librería: cabecera de 52 hex (versión 3) con `mapId`, tamaño,
origen, resolución y longitudes, seguida de datos LZ4 con la rejilla y la lista de
habitaciones.

## 6. Herramienta `tools/vactidy_room.py`

Cliente Tuya 3.3 autónomo (solo `cryptography`), pensado para invocarse desde HA:

```bash
python vactidy_room.py --list                     # habitaciones (vacío hoy)
python vactidy_room.py --clean 3                  # limpiar habitación por id
python vactidy_room.py --auto --speed normal      # limpieza completa
python vactidy_room.py --pause | --resume | --dock | --stop
python vactidy_room.py --map 1 --url https://...  # usar mapa (0x2e)
```

Configuración por `VACTIDY_HOST`, `VACTIDY_DEVICE_ID`, `VACTIDY_LOCAL_KEY`.

## 7. Notas operativas

- El robot admite **una sola sesión local**. Si Home Assistant (tuya-local) la tiene,
  el cliente falla con `901 Unable to Connect`: hay que reintentar.
- El robot **cierra la conexión** de vez en cuando (`IncompleteReadError`): los
  scripts deben reconectar y reintentar.
- Los push de estado llegan con cabeceras de **27 bytes**; el decodificador debe
  probar todos los offsets con longitud múltiplo de 16.
- Los scripts lanzados desde PowerShell bufferizan la salida: usar `python -u`.

## 8. Cambio de mapa 100 % local (RESUELTO)

La app aplica un mapa con el comando extendido `0x2e`, que lleva `mapId` + la URL
del fichero del mapa en la nube de Tuya. Capturado con Frida al pulsar «aplicar
mapa Salón»:

```
ab 00 | long 000001e9 | 2e | mapId 0000fc1e (64542) | lenURL 000001e0 (480) | URL
```

La URL es de S3 firmada (`ty-eu-storage-permanent.tuyaeu.com`, caduca en 24 h),
pero el fichero descargado **no caduca**: se sirve desde cualquier web.

### Prueba definitiva

1. `salon.txt` (58.824 B, `tar.gz`) servido con `python -m http.server 8000`.
2. `vactidy_room.py --map 64542 --url http://192.168.5.100:8000/salon.txt`
   → respuesta `0x2f` con `ret=1`.
3. En el log del servidor: `192.168.5.210 - "GET /salon.txt" 200` (el robot lo
   descargó).
4. `--auto` → `dp4=smart`, `dp5=smart`: limpió el salón y volvió solo a la base.

### Contenido del fichero

`tar.gz` con `area_info.json` (habitaciones con nombre y vértices),
`area_user.json`, `charger_pose.json`, `map.gridmap`, `map.segmentmap`,
`map_record.map`, `map_record.json`, `navmap_bound.json`, `path_map`,
`path_record`.

### Paquete de Home Assistant

`ha/vactidy_maps.yaml` + `ha/README.md`: `shell_command` que aplica el mapa
servido desde `/config/www/vactidy/` y arranca la limpieza, `script` para Alexa
y comando de parada fiable (`--stop-dock`: pausa y luego recarga).

### Como capturar otro mapa

`frida_spawn.py hook_v5.js 600` + aplicar el mapa en la app + `parse_map.py`.
El hook necesita fijar el classloader de la SDK
(`Java.classFactory.loader`) y engañar `AbsThingDevice.publishDps`.

## 9. Estado final (17 de noviembre de 2026)

Todo funciona en produccion sobre Home Assistant (`192.168.5.250:8123`,
HA 2026.11.2 en Docker):

| Pieza | Detalle |
|---|---|
| `script.limpiar_salon` | aplica mapa `64542` y limpia |
| `script.limpiar_cocina` | aplica mapa `58757` y limpia |
| `script.vactidy_parar` | pausa y vuelve a la base |
| Mapas | `/config/www/vactidy/{salon,cocina}.txt` (servidos por HA) |
| Credenciales | `/config/scripts/vactidy.env` (permisos 600, `shlex.quote`) |

### Alexa

No hace falta crear rutinas ni decir «activa»: **«Alexa, limpia salon»**
funciona directamente. HA entrega los `script` como escenas
(`Alexa.SceneController`) y el reconocimiento por voz las resuelve.

La app de Alexa en espanol no tiene pestana «Escenas»; solo aparecen en
*Rutinas → Anadir accion → Hogar inteligente → Escenas*.

### Lecciones de la instalacion

- `shell_command` exige **cadena**, no lista de argumentos. Si se define como
  lista, cae el dominio entero y desaparecen todos los comandos del sistema.
- La clave local puede contener caracteres de shell (`|`, `<`...): hay que
  citarla al escribir ficheros de entorno, o `source` la rompe.
- Los `script` se recargan sin reiniciar, pero Alexa necesita redescubrir.
