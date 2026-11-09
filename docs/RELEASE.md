# v0.1.2 — alta mucho más corta

Todo el trabajo de esta versión está en el momento de dar de alta el robot.

## Incluye

- **La región de Tuya se detecta sola.** Ya no hay que recordar si el proyecto se creó
  en EU, US, CN o IN: la integración prueba los cuatro centros de datos y usa el que
  responde. Elegir mal la región producía el mismo error que una contraseña incorrecta.
- **Selector de robot.** Después de autenticar, la integración lista los dispositivos de
  la cuenta y se elige el robot de un desplegable. La clave local se rellena sola, así
  que ya no hay que copiarla ni escribir el identificador.
- **Enlaces en el formulario.** La ayuda del paso de Tuya Cloud incluye enlaces directos
  a `iot.tuya.com`, con los cuatro pasos numerados.
- **Descubrimiento local con más margen.** El robot tarda en contestar a la difusión;
  antes se abandonaba a los 3 segundos y ahora se espera 6.
- **Mensaje de error más claro** cuando Tuya rechaza las credenciales: indica que el
  Access ID y el Access Secret deben ser del mismo proyecto y que la cuenta de la app
  tiene que estar vinculada.

## Instalación

Marketplace → Integraciones → Vactidy → **Actualizar** (o *Redownload* si aún usas el
repositorio personalizado). Después, reinicia Home Assistant.

## Requisitos

- Home Assistant 2024.11 o superior.
- El robot y Home Assistant en la misma red local.
- La clave local del dispositivo, o las credenciales de un proyecto de Tuya IoT.

## Limitaciones conocidas

- Mapas y limpieza por zonas sin implementar: los data points 14 y 16 están identificados
  pero su formato binario no está documentado.
- El descubrimiento depende de la difusión UDP. En redes que la bloquean hay que escribir
  la IP y el identificador a mano.
- Tuya no permite leer las credenciales del proyecto sin iniciar sesión en su panel, así
  que el Access ID y el Access Secret hay que copiarlos una vez.
