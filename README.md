# Vactidy para Home Assistant

Integración local para robots aspiradores **Vactidy** (y modelos compatibles basados en Tuya)
que hablan el protocolo LAN de Tuya 3.3. Sin nube, sin cuenta, sin dependencias del
fabricante: Home Assistant se conecta directamente al robot por TCP en el puerto 6668.

[English](README.en.md) · [Galego](README.gl.md)

> **Estado:** v0.1.0. Probado sobre un **Vactidy Cleanova W15** (`productId`
> `ut96oplbcckfxwwu`, firmware `40.00`, protocolo `2.2`), cuyo mapa de data points
> coincide casi por completo con el Proscenic M9.

---

## Qué aporta

- Entidad `vacuum` completa: iniciar, pausar, detener, volver a la base, localizar y
  cambiar la potencia de succión.
- 12 sensores: batería, superficie y tiempo de la limpieza actual, acumulados,
  vida útil de cepillos, sensores y mopa, y código de avería traducido.
- 5 sensores binarios: cargando, en la base, problema, no molestar y mopa instalada.
- 2 selectores: caudal de agua de la mopa y modo de limpieza (barrer / fregar / ambas).
- 2 interruptores: modo no molestar y luz del panel.
- 6 botones: localizar, vaciar depósito y reiniciar los cuatro contadores de mantenimiento.
- Diagnóstico descargable desde la propia entrada, sin exponer la clave local.

## Requisitos

- Home Assistant 2024.11 o superior.
- El robot y Home Assistant en la misma red local.
- La **clave local** del dispositivo. Es un valor de 16 caracteres que el fabricante
  entrega al vincular el robot y que no caduca. Se puede obtener de dos formas:
  1. Con `tinytuya wizard`, que la descarga de la API de Tuya Cloud pidiendo las claves
     de tu cuenta de desarrollador.
  2. Extrayéndola del propio teléfono si ya tienes la app Tuya vinculada
     (`shared_prefs/spUtils.xml`, campo `localKey`).
- La **IP fija** del robot en la red local. Se recomienda reservarla en el router por MAC.

## Instalación

### HACS (recomendado)

1. HACS → Integraciones → menú de tres puntos → **Repositorios personalizados**.
2. Añade `https://github.com/PainceirasTech/vactidy-ha` con categoría **Integration**.
3. Busca **Vactidy**, instala y reinicia Home Assistant.

### Manual

Copia la carpeta `custom_components/vactidy` dentro de `config/custom_components/` de tu
instalación de Home Assistant y reinicia.

## Configuración

1. Ajustes → Dispositivos y servicios → **Añadir integración** → *Vactidy*.
2. Rellena los cuatro campos:

| Campo | Ejemplo | Dónde se obtiene |
| --- | --- | --- |
| Dirección IP | `192.168.5.210` | Reserva DHCP del router |
| ID del dispositivo | `bf3e20ee26fbdcffd8e8kl` | `tinytuya wizard` o la app |
| Clave local | 16 caracteres | `tinytuya wizard` o `spUtils.xml` |
| Nombre | `Robot salón` | El que quieras |

La integración valida la conexión antes de guardar: si la clave es incorrecta verás
**«La clave local ha sido rechazada»**, y si la IP no responde, **«No se puede alcanzar
el robot»**. Si más adelante cambia la IP o rotas la clave, usa **Reconfigurar** en la
entrada; no hace falta borrarla.

## Entidades

| Plataforma | Entidades |
| --- | --- |
| `vacuum` | Robot (estado, batería, potencia, iniciar / pausar / detener / base / localizar) |
| `sensor` | Batería, superficie limpiada, tiempo de limpieza, estado, superficie total, limpiezas totales, tiempo total, vida de cepillo lateral, cepillo principal, sensores, mopa, avería |
| `binary_sensor` | Cargando, en la base, problema, no molestar, mopa instalada |
| `select` | Caudal de agua, modo de limpieza |
| `switch` | No molestar, luz del panel |
| `button` | Localizar, vaciar depósito, reiniciar cepillo lateral, principal, sensores y mopa |

La entidad `vacuum` expone además como atributos el estado en crudo, la superficie y el
tiempo de la limpieza, el modo, el caudal, si la mopa está puesta, el número de limpiezas
y el código de avería con su descripción.

## Cómo funciona

El cliente (`tuya_local.py`) implementa el protocolo local de Tuya 3.3 en asyncio puro:

- Tramas `55AA`: cabecera de 16 bytes, cuerpo cifrado y pie con CRC32 + sufijo.
- Cifrado **AES-128-ECB** con la clave local tal cual, sin hash.
- Consulta con `DP_QUERY (0x0A)` y escritura con `CONTROL (0x07)`.
- El robot responde repitiendo el comando recibido, no con `STATUS (0x08)`; el cliente
  acepta cualquier mensaje que traiga `dps`.

No se usa la nube en ningún momento. El único requisito externo es `cryptography`, que
ya viene con Home Assistant.

## Limitaciones y hoja de ruta

- **Mapas y limpieza por zonas**: los data points `14` (traza) y `16` (petición de mapa)
  están identificados pero su formato binario no está documentado; no se implementan aún.
- **Control manual por dirección** (`12`): no expuesto, para no competir con la app.
- **Frecuencia de vaciado** (`37`) y **volumen** (`26`): pendientes de exponer.
- La integración sondea cada 30 s; el estado se refresca al instante tras cada comando.

## Capturas

Las imágenes viven en `docs/images/` y se referencian desde aquí:

| Fichero | Contenido |
| --- | --- |
| `docs/images/integracion.png` | La integración añadida en Ajustes → Dispositivos y servicios |
| `docs/images/tarjeta.png` | Tarjeta del robot con sus entidades en el panel |
| `docs/images/configuracion.png` | Formulario de alta con los cuatro campos |

## Licencia

MIT. Consulta [LICENSE](LICENSE).

## Aviso

Proyecto no oficial, sin relación con Vactidy ni con Tuya. Usa el protocolo local por
ingeniería inversa del tráfico de tu propio dispositivo. Si actualizas el firmware del
robot, el mapa de data points podría cambiar.
