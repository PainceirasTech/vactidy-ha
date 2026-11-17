# Limpiar por mapa desde Home Assistant y Alexa

El robot guarda los mapas en la nube de Tuya y la app solo los aplica con el
comando `0x2e`, que necesita la URL del fichero del mapa. Este paquete hace lo
mismo **sin nube**: Home Assistant sirve el fichero del mapa y se lo manda al
robot por la red local.

Resultado: «Alexa, activa Limpiar salón» aplica el mapa del salón, arranca la
limpieza y el robot vuelve solo a su base al terminar.

## Que hace falta

| Pieza | Donde va |
|---|---|
| `tools/vactidy_room.py` | `/config/scripts/vactidy_room.py` |
| `tools/maps/salon.txt` | `/config/www/vactidy/salon.txt` |
| `ha/vactidy_maps.yaml` | paquete de Home Assistant |

El fichero del mapa se sirve desde `http://<ip-de-ha>:8123/local/vactidy/salon.txt`,
que es la ruta que usa el propio Home Assistant para su carpeta `www`.

## Instalacion

### 1. Copiar los ficheros al contenedor

Con el contenedor `homeassistant` en el Pi:

```bash
docker exec -i homeassistant mkdir -p /config/scripts /config/www/vactidy
docker cp vactidy_room.py homeassistant:/config/scripts/vactidy_room.py
docker cp salon.txt homeassistant:/config/www/vactidy/salon.txt
docker cp cocina.txt homeassistant:/config/www/vactidy/cocina.txt
```

Si no tienes terminal a mano, vale cualquier editor de ficheros de Home
Assistant (add-on *File editor*, Samba o la consola de Portainer): crea
`config/scripts/vactidy_room.py` y `config/www/vactidy/salon.txt` y pega el
contenido.

### 2. Guardar las credenciales

En `secrets.yaml`:

```yaml
vactidy_device_id: bf3e20ee26fbdcffd8e8kl
vactidy_local_key: "TU_CLAVE_LOCAL"
```

La clave local es la misma que usa la integracion `tuya-local` (16 caracteres,
se lee en *Cloud → API Explorer → Query device details*).

### 3. Activar el paquete

En `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

y guarda `vactidy_maps.yaml` en `config/packages/`. Reinicia Home Assistant.

Comprueba que aparecen dos acciones nuevas: `shell_command.vactidy_limpiar_salon`
y `script.limpiar_salon`.

### 4. Alexa

Las acciones de tipo `script` se exponen a Alexa como escenas. Exponlas en la
integracion de Alexa que uses (Nabu Casa o Alexa Smart Home) y en la app de
Alexa apareceran como escenas:

- «Alexa, activa Limpiar salón» → aplica el mapa del salón y limpia.
- «Alexa, activa Parar el robot y mandarlo a la base» → pausa y vuelve a cargar.

Si prefieres una rutina con nombre natural, crea la rutina en la app de Alexa
y que ejecute la escena.

## Mapas capturados

| Planta | Fichero | mapId | Tamaño |
|---|---|---|---|
| Salón (arriba) | `salon.txt` | 64542 | 58.824 B |
| Cocina (abajo) | `cocina.txt` | 58757 | 107.418 B |

Ambos se han probado contra el robot: responde `0x2f` con `ret=1` y se ve la
descarga en el log del servidor (`192.168.5.210 "GET /cocina.txt" 200`).

## Capturar otro mapa

Cada mapa tiene su propio `mapId` y su propio fichero. Para un tercer mapa:

1. Arranca la captura en el PC:

   ```powershell
   cd $env:TEMP\opencode
   python -u frida_spawn.py hook_v5.js 900 2>&1 | Tee-Object -FilePath hook_nuevo.log
   ```

2. En LDPlayer, abre el robot y pulsa **Mapa → <nombre> → Aplicar**.
3. Extrae la URL y descarga el fichero:

   ```powershell
   cd $env:TEMP\opencode
   python -u parse_map.py hook_nuevo.log nuevo
   ```

   Deja `nuevo.txt` en `tools/maps/` e imprime el `mapId`.
4. Copia el fichero a `/config/www/vactidy/nuevo.txt` y añade el bloque
   correspondiente en `vactidy_maps.yaml` con el `mapId` real.

## Detalles que conviene saber

- **Una sola sesion local**: el robot solo admite una conexion a la vez. Si
  `tuya-local` esta consultando en ese momento, el script espera y reintenta
  (`--retries 8`, un intento cada 4 s). Aun asi puedes ver un aviso de conexion
  en el log de `tuya-local`; es inocuo.
- **Parar**: `DP4="standby"` no detiene una limpieza en marcha, por eso el
  comando de parada pausa primero y luego ordena volver a la base.
- **La URL es obligatoria**: sin fichero, el robot responde `ret=0` y no cambia
  de mapa. Por eso el mapa se sirve desde Home Assistant y no desde la nube.
- **Si el robot no tiene el mapa aplicado** pero le mandas limpiar, limpia con
  el que tenga en memoria; el script siempre aplica antes de arrancar.
- **Bateria baja**: si esta por debajo del 15 %, el robot puede rechazar el
  arranque. Espera a que cargue.
