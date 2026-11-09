# v0.1.1

Integración local para robots aspiradores Vactidy basados en Tuya 3.3, probada sobre un
**Cleanova W15**.

Esta versión no añade funciones nuevas: corrige todo lo que impedía publicar la integración
en el catálogo de Home Assistant y actualiza la documentación.

## Correcciones

- **Imágenes de marca**: se añaden `brand/icon.png` y `brand/logo.png`, que el catálogo
  exige para mostrar la integración.
- **Manifiesto**: se retira `requirements: cryptography`, porque ya es dependencia del
  propio Home Assistant y declararla puede provocar conflictos de versión.
- **Traducciones**: la potencia de succión se declara ahora con la estructura que valida
  Home Assistant (`entity.vacuum.vacuum.state_attributes.fan_speed.state`), y la entidad
  declara su `translation_key`.
- **Validación continua**: los flujos de trabajo solo se ejecutan en `push` a `main`,
  `pull_request` y una vez al día, en lugar de dos veces por cada commit.

## Documentación

- Los tres README (español, inglés y gallego) explican el **Marketplace** como vía
  principal, disponible de serie desde Home Assistant 2026.11, y reservan el nombre HACS
  para versiones anteriores.
- Guía paso a paso pensada para quien nunca ha instalado una integración: sin terminal,
  sin conocimientos previos, con una tabla de problemas frecuentes.

## Requisitos

- Home Assistant 2024.11 o superior.
- El robot y Home Assistant en la misma red local.
- La clave local del dispositivo (16 caracteres).

## Limitaciones conocidas

- Mapas y limpieza por zonas sin implementar: los data points 14 y 16 están identificados
  pero su formato binario no está documentado.
- El descubrimiento depende de la difusión UDP; en redes que la bloquean hay que escribir
  la IP y el identificador a mano.
- Solo probado con el mapa de data points del W15, que coincide con el del Proscenic M9.
  Otros modelos pueden no funcionar; la integración lo detecta y lo avisa.
