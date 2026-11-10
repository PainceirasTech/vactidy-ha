# v0.1.4 — la vía Tuya Cloud, arreglada y explicada

## Corrección importante

**La firma de las peticiones a Tuya Cloud estaba mal.** Se incluía el `nonce` dentro del
texto firmado, y Tuya exige `client_id + t + método + hash del cuerpo + ruta`. Consecuencia:
cualquier credencial correcta era rechazada con `sign invalid` (código 1004). Corregido y
verificado contra el algoritmo de referencia.

## Mensajes de error honestos

Antes, un fallo de autenticación acababa mostrando «el dispositivo no aparece en esa
cuenta de Tuya», que era falso y despistaba. Ahora cada caso tiene su mensaje:

- `sign invalid` → credenciales o reloj del sistema.
- listado sin permiso → error de Tuya con su texto real.
- dispositivo inexistente → solo cuando de verdad no aparece.

## La verdad sobre las apps de marca blanca

El robot es Tuya por dentro, pero **la app de Vactidy no se puede vincular a un proyecto de
Tuya**: el único código QR que ofrece es para añadir miembros al hogar. Solo las apps
oficiales de Tuya (Tuya Smart y Smart Life) entienden el QR de *Devices → Link Tuya App
account*.

Por eso la vía Cloud ahora lo dice en la primera línea del formulario y remite a la vía
manual. Se documentan los tres caminos reales para conseguir la clave local:

1. **Ya tenerla.**
2. **Mover el robot a Tuya Smart o Smart Life** y vincular la cuenta al proyecto. Es el
   camino que funciona sin root, a cambio de dejar de usar la app de Vactidy.
3. **Extraerla del móvil** (`shared_prefs/spUtils.xml`), con root o copia de seguridad.

## Instalación

Actualiza desde el Marketplace (o HACS) y reinicia Home Assistant.

## Limitaciones conocidas

- Mapas y limpieza por zonas sin implementar: los data points 14 y 16 están identificados
  pero su formato binario no está documentado.
- El descubrimiento depende de la difusión UDP; donde esté bloqueada hay que escribir la IP
  y el identificador a mano.
- Solo probado con el mapa de data points del W15, que coincide con el del Proscenic M9.
