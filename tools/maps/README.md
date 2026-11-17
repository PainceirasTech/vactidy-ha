# Mapas del robot

En esta carpeta van los ficheros de mapa del robot, **uno por planta**:

```
salon.txt
cocina.txt
```

Son los ficheros `tar.gz` que la app de Tuya descarga de su nube. No se suben
al repositorio (estan en `.gitignore`) porque contienen el plano de la casa.

## Como se consiguen

Se capturan una sola vez desde la app, con `Frida` sobre un Android con root:

1. `python -u frida_spawn.py hook_v5.js 600` en el PC.
2. En la app, `Mapa → <nombre> → Aplicar`.
3. `python -u parse_map.py` descarga el fichero y lo deja aqui.

El proceso completo esta explicado en `ha/README.md`, seccion «Capturar otro
mapa (cocina)».

## Que hay dentro

El fichero es un `tar.gz` con:

| Fichero | Contenido |
|---|---|
| `area_info.json` | habitaciones con nombre, vertices y ajustes de limpieza |
| `area_user.json` | ajustes del usuario por zona |
| `charger_pose.json` | posicion de la base |
| `map.gridmap` | rejilla de ocupacion |
| `map.segmentmap` | segmentacion del mapa |
| `map_record.map`, `map_record.json` | registro del mapa |
| `navmap_bound.json` | limites de navegacion |
| `path_map`, `path_record` | rutas |

El robot descarga este mismo fichero cuando se le envia el comando `0x2e`.
