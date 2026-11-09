# Vactidy for Home Assistant

Local integration for **Vactidy** robot vacuums (and compatible Tuya-based models) that
speak the Tuya 3.3 LAN protocol. No cloud, no account, no vendor dependency: Home
Assistant talks to the robot directly over TCP port 6668.

[Español](README.md) · [Galego](README.gl.md)

> **Status:** v0.1.0. Tested on a **Vactidy Cleanova W15** (`productId`
> `ut96oplbcckfxwwu`, firmware `40.00`, protocol `2.2`), whose data point map matches the
> Proscenic M9 almost one to one.

---

## What you get

- A full `vacuum` entity: start, pause, stop, return to dock, locate and change suction
  power.
- 12 sensors: battery, current clean area and time, lifetime totals, remaining life of
  brushes, sensors and mop, and a translated fault code.
- 5 binary sensors: charging, docked, problem, do not disturb and mop installed.
- 2 selects: mop water level and cleaning mode (sweep / mop / both).
- 2 switches: do not disturb mode and panel light.
- 6 buttons: locate, empty dustbin and reset the four maintenance counters.
- Downloadable diagnostics from the config entry, without exposing the local key.

## Requirements

- Home Assistant 2024.11 or newer.
- Robot and Home Assistant on the same local network.
- The device **local key**: a 16 character value handed out when the robot is paired. It
  never expires. You can get it in two ways:
  1. `tinytuya wizard`, which pulls it from the Tuya Cloud API using your developer
     account keys.
  2. Extracting it from the phone where the Tuya app is already paired
     (`shared_prefs/spUtils.xml`, `localKey` field).
- A **fixed IP** for the robot. Reserving the lease by MAC on your router is recommended.

## Installation

### HACS (recommended)

1. HACS → Integrations → three dot menu → **Custom repositories**.
2. Add `https://github.com/PainceirasTech/vactidy-ha` with category **Integration**.
3. Search for **Vactidy**, install and restart Home Assistant.

### Manual

Copy the `custom_components/vactidy` folder into `config/custom_components/` and restart.

## Configuration

1. Settings → Devices & services → **Add integration** → *Vactidy*.
2. Fill in the four fields:

| Field | Example | Where to get it |
| --- | --- | --- |
| IP address | `192.168.5.210` | Router DHCP reservation |
| Device ID | `bf3e20ee26fbdcffd8e8kl` | `tinytuya wizard` or the app |
| Local key | 16 characters | `tinytuya wizard` or `spUtils.xml` |
| Name | `Living room robot` | Anything you like |

The integration validates the connection before saving: a wrong key shows **“The local
key was rejected”**, an unreachable IP shows **“Cannot reach the robot”**. If the IP
changes or you rotate the key later, use **Reconfigure** on the entry; no need to delete
it.

## Entities

| Platform | Entities |
| --- | --- |
| `vacuum` | Robot (state, battery, fan speed, start / pause / stop / dock / locate) |
| `sensor` | Battery, cleaned area, cleaning time, status, total area, total cleanings, total time, side brush life, main brush life, sensor life, mop life, fault |
| `binary_sensor` | Charging, docked, problem, do not disturb, mop installed |
| `select` | Water level, cleaning mode |
| `switch` | Do not disturb, panel light |
| `button` | Locate, empty dustbin, reset side brush, main brush, sensors and mop |

The `vacuum` entity also exposes attributes with the raw status, clean area and time,
mode, water level, mop presence, cleaning count and the fault code with its description.

## How it works

`tuya_local.py` implements the Tuya 3.3 LAN protocol in pure asyncio:

- `55AA` frames: 16 byte header, encrypted body, CRC32 + suffix footer.
- **AES-128-ECB** using the local key as-is, with no hashing.
- `DP_QUERY (0x0A)` to read and `CONTROL (0x07)` to write.
- The robot replies echoing the command it received instead of using `STATUS (0x08)`, so
  the client accepts any message carrying `dps`.

The cloud is never involved. The only external requirement is `cryptography`, already
shipped with Home Assistant.

## Limitations and roadmap

- **Maps and zone cleaning**: data points `14` (path) and `16` (map request) are
  identified but their binary format is undocumented; not implemented yet.
- **Manual direction control** (`12`): intentionally not exposed.
- **Dust collection frequency** (`37`) and **volume** (`26`): pending.
- The integration polls every 30 s; state refreshes instantly after each command.

## Screenshots

| File | Content |
| --- | --- |
| `docs/images/integracion.png` | The integration listed under Settings → Devices & services |
| `docs/images/tarjeta.png` | Robot card with its entities on the dashboard |
| `docs/images/configuracion.png` | Setup form with the four fields |

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

Unofficial project, not affiliated with Vactidy or Tuya. It uses the local protocol by
reverse engineering your own device traffic. A firmware update could change the data
point map.
