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
- The robot and Home Assistant on the same local network.
- The **local key** of the device: 16 characters assigned by the manufacturer when the
  robot is linked and which never expire. It is the only value needed, and the integration
  can ask Tuya for it if you provide developer credentials.

  That key is a factory secret: it is not derived from the device ID and it never travels
  over the local network, so no program can guess it. What can be avoided is the manual
  work of hunting it down, which is what the two routes below are for.

## Installation

### HACS (recommended)

1. HACS → Integrations → three dot menu → **Custom repositories**.
2. Add `https://github.com/PainceirasTech/vactidy-ha` with category **Integration**.
3. Search for **Vactidy**, install and restart Home Assistant.

### Manual

Copy the `custom_components/vactidy` folder into `config/custom_components/` and restart.

## Configuration

1. Settings → Devices & services → **Add integration** → *Vactidy*.
2. The integration looks for the robot on the local network and **fills in the IP address
   and the device ID by itself**. Then choose one of the two routes:

   - **I already have the local key**: paste it and give the robot a name. That is all.
   - **Get it from Tuya Cloud**: enter the *Access ID* and *Access Secret* of a free project
     at <https://iot.tuya.com> with your Tuya app account linked
     (*Devices → Link Tuya App account*). The integration asks Tuya for the key, fills in
     the form and creates the entry. The credentials are not stored: they are used only at
     that moment.

3. Press **Submit**. A test connection is opened with the robot and, if it answers, the
   entry is created.

If discovery does not find the robot (because it sits on another subnet or the router
blocks broadcasts), both fields appear empty and you can type them by hand. The device ID
is shown in the Tuya app under *Device settings → Device information*.

The integration validates the connection before saving: a wrong key shows **"The local key
was rejected"**, an unreachable IP shows **"Cannot reach the robot"**, and a device that
answers but belongs to another family shows **"The device answered, but it does not report
the expected data points"**. If the IP changes later or the key is rotated, use
**Reconfigure** on the entry; there is no need to delete it.

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
| `docs/images/configuracion.png` | Setup form with the robot already detected and the local key as the only manual field |

## License

MIT. See [LICENSE](LICENSE).

## Disclaimer

Unofficial project, not affiliated with Vactidy or Tuya. It uses the local protocol by
reverse engineering your own device traffic. A firmware update could change the data
point map.
