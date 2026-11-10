# v0.1.3 — correcciones del alta con Tuya Cloud

## Correcciones

- **Las traducciones ya no contienen direcciones web.** Hassfest lo prohíbe en los
  textos de la interfaz; ahora las rutas del panel se explican en texto y los enlaces
  quedan en la documentación. Esto desbloquea la validación del repositorio.
- **Ruta correcta del panel de Tuya.** La sección se llama **Cloud → Project
  Management**, no «Development». Corregido en el formulario y en los tres README.
- **Se aclara dónde se vincula la app.** El vínculo se hace en el panel web, dentro del
  proyecto: *Devices → Link Tuya App account*. El código QR que aparece se escanea con
  la app Vactidy del móvil; esa opción no existe dentro de la app.
- **Diagnóstico visible.** Si Tuya devuelve un error, el formulario muestra el código y
  el mensaje exactos en lugar de un aviso genérico.
- **El listado de robots ya no es obligatorio.** Algunos proyectos no tienen permiso
  para listar dispositivos; en ese caso se puede escribir el identificador del robot y
  la clave se pide directamente.

## Instalación

Marketplace → Integraciones → Vactidy → **Actualizar** (o *Redownload*). Después,
reinicia Home Assistant.

## Requisitos

- Home Assistant 2024.11 o superior.
- El robot y Home Assistant en la misma red local.
- La clave local del dispositivo, o las credenciales de un proyecto de Tuya IoT con la
  cuenta de la app vinculada.

## Limitaciones conocidas

- Mapas y limpieza por zonas sin implementar: los data points 14 y 16 están identificados
  pero su formato binario no está documentado.
- El descubrimiento depende de la difusión UDP. En redes que la bloquean hay que escribir
  la IP y el identificador a mano.
- Tuya no permite leer las credenciales del proyecto sin iniciar sesión en su panel, así
  que el Access ID y el Access Secret hay que copiarlos una vez.
