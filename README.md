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
- La **clave local** del dispositivo: 16 caracteres que el fabricante asigna al vincular el
  robot y que no caducan. Es el único dato que hace falta, y la integración puede pedírsela
  sola a Tuya si le das credenciales de desarrollador.

  Esa clave es un secreto de fábrica: no se deriva del identificador ni viaja por la red
  local, así que ningún programa puede adivinarla. Lo que sí se puede evitar es el trabajo
  manual de buscarla, y para eso están las dos vías del apartado siguiente.

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
2. La integración busca el robot en la red local y **rellena sola la IP y el identificador**.
   Después elige una de las dos vías:

   - **Ya tengo la clave local**: pégala y ponle nombre al robot. Es todo.
   - **Obtenerla de Tuya Cloud**: introduce el *Access ID* y el *Access Secret* de un
     proyecto gratuito de <https://iot.tuya.com> con tu cuenta de la app Tuya vinculada
     (*Devices → Link Tuya App account*). La integración pide la clave a Tuya, rellena el
     formulario y guarda la entrada. Las credenciales no se almacenan: solo se usan en ese
     momento.

3. Pulsa **Enviar**. Se abre una conexión de prueba con el robot y, si responde, la entrada
   queda creada.

Si el descubrimiento no encuentra el robot (porque está en otra subred o el router bloquea
la difusión), los dos campos aparecen vacíos y puedes escribirlos a mano. El identificador
está en la app Tuya, en *Ajustes del dispositivo → Información del dispositivo*.

La integración valida la conexión antes de guardar: si la clave es incorrecta verás
**«La clave local ha sido rechazada»**, si la IP no responde **«No se puede alcanzar el
robot»** y si el aparato contesta pero no es de esta familia, **«El dispositivo respondió,
pero no informa los puntos de datos esperados»**. Si más adelante cambia la IP o rotas la
clave, usa **Reconfigurar** en la entrada; no hace falta borrarla.

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
| `docs/images/configuracion.png` | Formulario de alta con el robot ya detectado y la clave local como único campo manual |

## Licencia

MIT. Consulta [LICENSE](LICENSE).

## Aviso

Proyecto no oficial, sin relación con Vactidy ni con Tuya. Usa el protocolo local por
ingeniería inversa del tráfico de tu propio dispositivo. Si actualizas el firmware del
robot, el mapa de data points podría cambiar.
