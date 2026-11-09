# v0.1.0 — primera versión

Integración local para robots aspiradores Vactidy basados en Tuya 3.3, probada sobre un
**Cleanova W15**.

## Incluye

- Entidad `vacuum` completa: iniciar, pausar, detener, volver a la base, localizar y
  cambiar la potencia de succión.
- 12 sensores, 5 binarios, 2 selectores, 2 interruptores y 6 botones.
- **Descubrimiento automático**: la integración localiza el robot en la red local y
  rellena la IP y el identificador; solo hay que aportar la clave local.
- **Alta con Tuya Cloud**: si prefieres no buscar la clave, se pide a la API con las
  credenciales de un proyecto de desarrollador. No se almacenan.
- Diagnóstico descargable desde la entrada, sin exponer la clave.

## Instalación

HACS → menú de tres puntos → **Repositorios personalizados** →
`https://github.com/PainceirasTech/vactidy-ha` con categoría **Integration**.

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
