# Vactidy para Home Assistant

Integración local para robots aspiradores **Vactidy** (y modelos compatibles basados en Tuya)
que hablan el protocolo LAN de Tuya 3.3. Sin nube, sin cuenta y sin depender del fabricante:
Home Assistant se conecta directamente al robot por tu red wifi.

[English](README.en.md) · [Galego](README.gl.md)

> **Estado:** v0.1.3. Probado sobre un **Vactidy Cleanova W15** (`productId`
> `ut96oplbcckfxwwu`, firmware `40.00`, protocolo `2.2`), cuyo mapa de data points
> coincide casi por completo con el Proscenic M9.

---

## Qué vas a conseguir

Un robot integrado en Home Assistant con:

- **Entidad `vacuum`**: iniciar, pausar, detener, volver a la base, localizar y cambiar la
  potencia de succión.
- **12 sensores**: batería, superficie y tiempo de la limpieza, acumulados, vida útil de
  cepillos, sensores y mopa, y el código de avería traducido.
- **5 sensores binarios**: cargando, en la base, problema, no molestar y mopa instalada.
- **2 selectores**: caudal de agua de la mopa y modo de limpieza (barrer / fregar / ambas).
- **2 interruptores**: modo no molestar y luz del panel.
- **6 botones**: localizar, vaciar el depósito y reiniciar los contadores de mantenimiento.

Todo funciona en local: si se cae internet, el robot sigue respondiendo.

## Antes de empezar

Necesitas cuatro cosas:

1. Home Assistant **2024.11 o superior**.
2. Acceso al **Marketplace** de integraciones. Si tienes Home Assistant **2026.11 o
   posterior**, el Marketplace viene incluido: está en *Ajustes → Marketplace*. En
   versiones anteriores se llama **HACS** y hay que instalarlo (paso 1).
3. El robot **encendido y conectado a la misma red** que Home Assistant.
4. Diez minutos y la **clave local** del robot. Si no la tienes, el paso 5 explica cómo
   conseguirla sin usar la terminal.

---

## Paso 1 · Abrir el Marketplace

**Home Assistant 2026.11 o posterior:** el Marketplace ya viene dentro de Home Assistant.
Entra en *Ajustes → Marketplace* y salta al paso 2. No hay que instalar nada.

**Versiones anteriores:** el mismo catálogo se llama **HACS** y se instala aparte.

1. Instala el add-on **Terminal & SSH** desde *Ajustes → Complementos → Tienda de
   complementos*, o entra por SSH a tu instalación.
2. Ejecuta:

   ```bash
   wget -O - https://get.hacs.xyz | bash -
   ```

3. Reinicia Home Assistant.
4. Ve a *Ajustes → Dispositivos y servicios → Añadir integración* y busca **HACS**.
   Acéptalo todo y, cuando te pida autorizar en GitHub, introduce el código que te muestra.

## Paso 2 · Instalar Vactidy

**Si Vactidy ya aparece en el catálogo** (búscalo en *Marketplace → Integraciones*), abre
la ficha y pulsa **Descargar**. Salta al paso 3.

**Si todavía no aparece**, la inclusión en el catálogo sigue en revisión y hay que añadir
el repositorio a mano:

1. Abre **Marketplace** (o **HACS**) en la barra lateral.
2. Entra en **Integraciones**.
3. Arriba a la derecha, menú de tres puntos → **Repositorios personalizados**
   (*Custom repositories*).
4. Pega la dirección y elige la categoría:

   | Campo | Valor |
   | --- | --- |
   | Repositorio | `https://github.com/PainceirasTech/vactidy-ha` |
   | Categoría | **Integration** |

5. Pulsa **Añadir**, busca **Vactidy**, abre la ficha y pulsa **Descargar**.

## Paso 3 · Reiniciar Home Assistant

Reinicia desde *Ajustes → Sistema → Reiniciar*.

El reinicio no es opcional: hasta que no reinicies, Home Assistant no ve la integración.

## Paso 4 · Añadir la integración

1. Ve a *Ajustes → Dispositivos y servicios*.
2. Pulsa **Añadir integración** (abajo a la derecha).
3. Busca **Vactidy** y ábrelo.
4. Aparece un menú con dos opciones:

   ```
   ¿Cómo quieres configurar el robot?
     ▸ Ya tengo la clave local
     ▸ Obtenerla de Tuya Cloud
   ```

   Elige la que corresponda a tu caso. La segunda es la fácil si nunca has oído hablar de
   una «clave local».

La integración busca el robot en tu red mientras muestras ese menú. Si lo encuentra, verás
su IP y su identificador en el texto de arriba; si no, no pasa nada, se escriben a mano.

## Paso 5 · Conseguir la clave local

La **clave local** es un texto de 16 caracteres que el robot usa para cifrar la
comunicación. La asigna el fabricante y no cambia nunca. Hay dos maneras de obtenerla.

### Opción A · Pedírsela a Tuya (recomendado, sin terminal)

Solo hace falta una cuenta gratuita de desarrollador y vincular la app del móvil.

1. Entra en <https://iot.tuya.com> y crea una cuenta (es gratis; no hace falta tarjeta).
2. En el menú lateral, **Cloud → Project Management**, y pulsa **Create Cloud Project**.
   - Nombre: el que quieras.
   - *Industry*: Smart Home.
   - *Development Method*: Smart Home.
   - *Data Center*: **Central Europe** si estás en España.
3. Abre el proyecto recién creado y apunta el **Access ID** y el **Access Secret** de la
   pestaña *Overview*. Son las credenciales que te pedirá la integración.
4. Dentro del proyecto, ve a **Devices → Link Tuya App account → Add App Account**.
   **Ojo: esto se hace en la web**, en el panel de Tuya, no en la app del móvil. Aparece un
   código QR.
5. En el móvil, abre la app con la que controlas el robot (**Vactidy**, **Tuya Smart** o
   **Smart Life**) → pestaña *Yo* → icono de escaneo (arriba a la derecha) → escanea el QR
   → confirma.
6. Vuelve a **Devices** en la web: tu robot aparece en la lista. Ya está vinculado.

Ahora, en Home Assistant:

1. Elige **Obtenerla de Tuya Cloud** en el menú de la integración.
2. Rellena:

   | Campo | Qué poner |
   | --- | --- |
   | Access ID | El del paso 3 |
   | Access Secret | El del paso 3 |
   | Región | `EU` (Central Europe) |
   | Identificador | Déjalo vacío salvo que tengas varios robots |

3. Pulsa **Enviar**. La integración pide la clave a Tuya, la rellena y te lleva al
   formulario final.

Las credenciales **no se guardan**: se usan una vez y se descartan.

### Opción B · Ya tengo la clave local

Si la tienes (porque la guardaste al instalarla, o porque la sacaste de la app), elige
**Ya tengo la clave local** y pégala. Fin.

### Opción C · A mano, para quien quiera el dato físico

Si prefieres no dar credenciales a nadie y tienes acceso al móvil donde está vinculado el
robot, la clave se puede extraer de los datos de la propia app. Requiere un móvil Android
con depuración USB y un programa de terminal: es la vía de la documentación antigua y solo
la recomendamos si las otras dos fallan.

## Paso 6 · Terminar y comprobar

1. En el formulario final, elige el **nombre** del robot. Es opcional: si lo dejas vacío se
   llamará *Robot aspirador*.
2. Pulsa **Enviar**. La integración abre una conexión de prueba:
   - Si el robot responde, la entrada queda creada y las entidades aparecen solas.
   - Si algo falla, verás el error explicado en el apartado siguiente.
3. Comprueba en *Ajustes → Dispositivos y servicios → Vactidy* que el estado es **En base**
   o **Cargando**, con la batería al nivel real.

Prueba rápida: abre la tarjeta del robot y pulsa **Localizar**. El robot debería decir algo.
Después, **Volver a la base** lo devuelve a su sitio.

## Si algo va mal

| Lo que ves | Qué significa | Qué hacer |
| --- | --- | --- |
| «No se puede alcanzar el robot» | La IP no responde en el puerto 6668 | Comprueba que el robot está encendido y en la misma red; revisa que la IP no haya cambiado (ponle IP fija en el router) |
| «La clave local ha sido rechazada» | La clave tiene 16 caracteres pero no es la del robot | Vuelve a copiarla completa, sin espacios; si la regeneraste en la app, usa la nueva |
| «El dispositivo respondió, pero no informa los puntos de datos esperados» | Es un aparato Tuya, pero no de esta familia | Este modelo no es compatible; abre una incidencia con el modelo exacto |
| No aparece Vactidy al añadir la integración | No se reinició tras instalar | Reinicia Home Assistant y vuelve a *Ajustes → Dispositivos y servicios* |
| La integración no encuentra el robot | Difusión bloqueada o el robot está en otra subred | Escribe la IP y el identificador a mano; están en la app Tuya, en *Ajustes del dispositivo → Información del dispositivo* |
| «Autenticación de Tuya Cloud rechazada» | Access ID o Secret incorrectos | Cópialos otra vez de *Overview*; ojo, no son los de la app sino los del proyecto |
| «La cuenta de Tuya no tiene dispositivos vinculados» | Falta el paso del QR | Repite *Devices → Link Tuya App account* |

El registro completo está en *Ajustes → Sistema → Registros*, filtrando por `vactidy`.

## Entidades que aparecen

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

## Compatibilidad

El mapa de data points que usa esta integración **no es de Vactidy**: es el que Tuya
comparte entre varias marcas blancas. El W15 coincide casi al 100 % con el Proscenic M9, y
por eso es muy probable que funcione en otros robots con el mismo `productId` o similar.

Si tu robot usa otro mapa, la integración lo detecta al configurarla y te lo dice con el
error «no informa los puntos de datos esperados» en vez de crear entidades rotas.

Modelos confirmados:

| Modelo | Estado |
| --- | --- |
| Vactidy Cleanova W15 | Probado |
| Otros Vactidy con Tuya 3.3 | Sin probar; prueba y cuéntalo en una incidencia |

## Cómo funciona (para curiosos)

El cliente (`tuya_local.py`) implementa el protocolo local de Tuya 3.3 en asyncio puro:

- Tramas `55AA`: cabecera de 16 bytes, cuerpo cifrado y pie con CRC32 + sufijo.
- Cifrado **AES-128-ECB** con la clave local tal cual, sin hash.
- Consulta con `DP_QUERY (0x0A)` y escritura con `CONTROL (0x07)`.
- El robot responde repitiendo el comando recibido, no con `STATUS (0x08)`; el cliente
  acepta cualquier mensaje que traiga `dps`.

No se usa la nube en ningún momento. El único requisito externo es `cryptography`, que ya
viene con Home Assistant.

## Limitaciones y hoja de ruta

- **Mapas y limpieza por zonas**: los data points `14` (traza) y `16` (petición de mapa)
  están identificados pero su formato binario no está documentado; no se implementan aún.
- **Control manual por dirección** (`12`): no expuesto, para no competir con la app.
- **Frecuencia de vaciado** (`37`) y **volumen** (`26`): pendientes de exponer.
- La integración sondea cada 30 s; el estado se refresca al instante tras cada comando.

## Capturas

Las imágenes viven en `docs/images/`:

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
