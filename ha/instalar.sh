#!/bin/sh
# Instala los comandos de limpieza por mapa del Vactidy en Home Assistant.
# Se ejecuta DENTRO del contenedor:  sh /config/instalar.sh
set -eu

BASE="http://192.168.5.100:8002"
CFG="/config"
ENTORNO="$CFG/scripts/vactidy.env"

echo "== 1. Carpetas =="
mkdir -p "$CFG/scripts" "$CFG/www/vactidy" "$CFG/packages"
echo "   ok: $CFG/scripts $CFG/www/vactidy $CFG/packages"

echo "== 2. Descargando ficheros =="
wget -q -O "$CFG/scripts/vactidy_room.py" "$BASE/tools/vactidy_room.py"
wget -q -O "$CFG/www/vactidy/salon.txt" "$BASE/tools/maps/salon.txt"
wget -q -O "$CFG/www/vactidy/cocina.txt" "$BASE/tools/maps/cocina.txt"
wget -q -O "$CFG/packages/vactidy_maps.yaml" "$BASE/ha/vactidy_maps.yaml"
ls -l "$CFG/scripts/vactidy_room.py" "$CFG/www/vactidy" "$CFG/packages/vactidy_maps.yaml"

echo "== 3. Leyendo la clave local de tuya-local =="
python3 - <<'PY'
import json
import pathlib
import shlex

almacen = pathlib.Path("/config/.storage/core.config_entries")
datos = json.loads(almacen.read_text(encoding="utf-8"))
clave = None
dispositivo = None
for entrada in datos["data"]["entries"]:
    if entrada.get("domain") != "tuya_local":
        continue
    secretos = entrada.get("data") or {}
    if secretos.get("local_key"):
        clave = secretos["local_key"]
        dispositivo = secretos.get("device_id") or secretos.get("device_id_str")
        break

if not clave:
    raise SystemExit("ERROR: no encuentro la clave local en la integracion tuya_local")

destino = pathlib.Path("/config/scripts/vactidy.env")
destino.write_text(
    "# Credenciales del robot. No compartir este fichero.\n"
    f"VACTIDY_HOST=192.168.5.210\n"
    f"VACTIDY_DEVICE_ID={shlex.quote(str(dispositivo))}\n"
    f"VACTIDY_LOCAL_KEY={shlex.quote(clave)}\n",
    encoding="utf-8",
)
destino.chmod(0o600)
print(f"   ok: {destino} (dispositivo {dispositivo}, clave de {len(clave)} caracteres)")
PY

echo "== 4. Activando el paquete en configuration.yaml =="
if grep -q 'packages:' "$CFG/configuration.yaml"; then
    echo "   ya estaba activado, no toco configuration.yaml"
else
    cp "$CFG/configuration.yaml" "$CFG/configuration.yaml.bak-vactidy"
    printf '\n# Limpieza por mapa del Vactidy (anadido por instalar.sh)\nhomeassistant:\n  packages: !include_dir_named packages\n' >> "$CFG/configuration.yaml"
    echo "   ok: configuration.yaml actualizado (copia en configuration.yaml.bak-vactidy)"
fi

echo "== 5. Comprobando la configuracion =="
python3 -m homeassistant --script check_config -c "$CFG" >/tmp/check.log 2>&1 && \
    echo "   ok: configuracion valida" || {
        echo "   FALLO en la validacion, ultimas lineas:"
        tail -n 25 /tmp/check.log
        exit 1
    }

echo
echo "Listo. Reinicia Home Assistant y prueba la accion script.limpiar_salon."
