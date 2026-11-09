# Vactidy for Home Assistant

Local integration for **Vactidy** robot vacuums (and compatible Tuya-based models) that speak
the Tuya 3.3 LAN protocol. No cloud, no account and no vendor dependency: Home Assistant
talks to the robot directly over your own wifi.

[Español](README.md) · [Galego](README.gl.md)

> **Status:** v0.1.0. Tested on a **Vactidy Cleanova W15** (`productId` `ut96oplbcckfxwwu`,
> firmware `40.00`, protocol `2.2`), whose data point map almost matches the Proscenic M9.

---

## What you get

A robot vacuum inside Home Assistant with:

- **`vacuum` entity**: start, pause, stop, return to base, locate and change suction power.
- **12 sensors**: battery, cleaned area and cleaning time, totals, remaining life of the
  brushes, sensors and mop, and the translated fault code.
- **5 binary sensors**: charging, on dock, problem, do not disturb and mop installed.
- **2 selects**: mop water level and cleaning mode (sweep / mop / both).
- **2 switches**: do not disturb and panel light.
- **6 buttons**: locate, empty the dustbin and reset the maintenance counters.

Everything runs locally: if your internet goes down, the robot still responds.

## Before you start

You need four things:

1. Home Assistant **2024.11 or newer**.
2. **HACS** installed. Step 1 covers it if you don't.
3. The robot **powered on and on the same network** as Home Assistant.
4. Ten minutes and the robot's **local key**. Step 5 explains how to get it without a
   terminal.

---

## Step 1 · Install HACS (skip if you already have it)

If you already see **HACS** in the sidebar, go to step 2.

1. Install the **Terminal & SSH** add-on from *Settings → Add-ons → Add-on store*, or open
   an SSH session to your installation.
2. Run:

   ```bash
   wget -O - https://get.hacs.xyz | bash -
   ```

3. Restart Home Assistant.
4. Go to *Settings → Devices & services → Add integration* and search for **HACS**.
   Accept everything and, when it asks you to authorise on GitHub, enter the code it shows.
5. HACS appears in the sidebar.

> In some versions the menu is called **Marketplace**. It is the same place.

## Step 2 · Add this repository to HACS

1. Open **HACS** in the sidebar.
2. Go to **Integrations**.
3. Top right, three-dot menu → **Custom repositories**.
4. Paste the address and pick the category:

   | Field | Value |
   | --- | --- |
   | Repository | `https://github.com/PainceirasTech/vactidy-ha` |
   | Category | **Integration** |

5. Press **Add**.

## Step 3 · Install the integration

1. Still in **HACS → Integrations**.
2. Search for **Vactidy**.
3. Open it and press **Download**.
4. When it finishes, **restart Home Assistant** from *Settings → System → Restart*.

The restart is not optional: until you restart, Home Assistant cannot see the integration.

## Step 4 · Add the integration

1. Go to *Settings → Devices & services*.
2. Press **Add integration** (bottom right).
3. Search for **Vactidy** and open it.
4. A menu appears with two options:

   ```
   How do you want to set up the robot?
     ▸ I already have the local key
     ▸ Get it from Tuya Cloud
   ```

   Pick the one that fits you. The second is the easy one if you have never heard of a
   "local key".

The integration scans your network while that menu is on screen. If it finds the robot you
will see its IP and identifier in the text above; if not, that is fine, you can type them.

## Step 5 · Get the local key

The **local key** is a 16-character string the robot uses to encrypt its traffic. The
factory assigns it and it never changes. There are two ways to get it.

### Option A · Ask Tuya (recommended, no terminal)

You only need a free developer account and to link the phone app.

1. Go to <https://iot.tuya.com> and create an account (free, no card needed).
2. In the side menu, **Cloud → Development**, then **Create Cloud Project**.
   - Name: whatever you like.
   - *Industry*: Smart Home.
   - *Development Method*: Smart Home.
   - *Data Center*: **Central Europe** if you are in Europe.
3. Open the new project and note the **Access ID** and **Access Secret** from the *Overview*
   tab. These are the credentials the integration will ask for.
4. In the project menu, **Devices → Link Tuya App account → Add App Account**. A QR code
   appears.
5. On your phone, open the **Tuya Smart** or **Smart Life** app (the one you use with the
   robot) → *Me* tab → scan icon (top right) → scan the QR → confirm.
6. Back in **Devices**, your robot is listed. It is linked.

Now, in Home Assistant:

1. Choose **Get it from Tuya Cloud** in the integration menu.
2. Fill in:

   | Field | What to enter |
   | --- | --- |
   | Access ID | From step 3 |
   | Access Secret | From step 3 |
   | Region | `EU` (Central Europe) |
   | Device ID | Leave empty unless you own several robots |

3. Press **Submit**. The integration asks Tuya for the key, fills the form and takes you to
   the final screen.

The credentials are **not stored**: they are used once and discarded.

### Option B · You already have the local key

If you have it, choose **I already have the local key**, paste it and you are done.

### Option C · By hand, for the curious

If you would rather not hand over any credentials and you have the phone the robot is linked
to, the key can be extracted from the app's own data. It needs an Android phone with USB
debugging and a terminal program: this is the old documentation route and we only recommend
it if the other two fail.

## Step 6 · Finish and check

1. On the final form, choose the robot's **name**. It is optional: leave it empty and it will
   be called *Robot vacuum*.
2. Press **Submit**. The integration opens a test connection:
   - If the robot answers, the entry is created and the entities appear by themselves.
   - If something fails, you will see the error explained in the next section.
3. Check *Settings → Devices & services → Vactidy*: the state should be **Docked** or
   **Charging**, with the real battery level.

Quick test: open the robot card and press **Locate**. The robot should say something. Then
**Return to base** sends it home.

## Troubleshooting

| What you see | What it means | What to do |
| --- | --- | --- |
| "Cannot reach the robot" | The IP does not answer on port 6668 | Check the robot is on and on the same network; make sure its IP did not change (set a DHCP reservation on your router) |
| "The local key was rejected" | The key has 16 characters but is not this robot's | Copy it again in full, no spaces; if you regenerated it in the app, use the new one |
| "The device answered but does not report the expected data points" | It is a Tuya device, but not this family | This model is not supported; open an issue with the exact model |
| Vactidy does not appear when adding the integration | You did not restart after installing | Restart Home Assistant and go back to *Settings → Devices & services* |
| The integration cannot find the robot | Broadcast blocked or the robot is on another subnet | Type the IP and identifier by hand; both are in the Tuya app under *Device settings → Device information* |
| "Tuya Cloud authentication rejected" | Wrong Access ID or Secret | Copy them again from *Overview*; these are the project ones, not the app ones |
| "The Tuya account has no linked devices" | The QR step is missing | Repeat *Devices → Link Tuya App account* |

The full log is in *Settings → System → Logs*, filtered by `vactidy`.

## Entities

| Platform | Entities |
| --- | --- |
| `vacuum` | Robot (state, battery, fan speed, start / pause / stop / dock / locate) |
| `sensor` | Battery, cleaned area, cleaning time, status, total area, total cleanings, total time, side brush life, main brush life, sensors, mop, fault |
| `binary_sensor` | Charging, on dock, problem, do not disturb, mop installed |
| `select` | Water level, cleaning mode |
| `switch` | Do not disturb, panel light |
| `button` | Locate, empty dustbin, reset side brush, main brush, sensors and mop |

The `vacuum` entity also exposes raw state, cleaned area and time, mode, water level, whether
the mop is fitted, the number of cleanings and the fault code with its description.

## Compatibility

The data point map used here **is not Vactidy's**: it is the one Tuya shares across several
white-label brands. The W15 matches the Proscenic M9 almost completely, so it will very
likely work on other robots with the same or a similar `productId`.

If your robot uses a different map, the integration detects it during setup and tells you
with the "does not report the expected data points" error instead of creating broken
entities.

Known models:

| Model | Status |
| --- | --- |
| Vactidy Cleanova W15 | Tested |
| Other Vactidy with Tuya 3.3 | Untested; try it and report back in an issue |

## How it works (for the curious)

The client (`tuya_local.py`) implements the Tuya 3.3 LAN protocol in pure asyncio:

- `55AA` frames: 16-byte header, encrypted body and CRC32 + suffix footer.
- **AES-128-ECB** with the local key as-is, no hashing.
- Reads with `DP_QUERY (0x0A)` and writes with `CONTROL (0x07)`.
- The robot replies by repeating the command it received, not with `STATUS (0x08)`; the
  client accepts any message carrying `dps`.

The cloud is never used. The only external requirement is `cryptography`, which ships with
Home Assistant.

## Limitations and roadmap

- **Maps and zone cleaning**: data points `14` (trace) and `16` (map request) are identified
  but their binary format is undocumented; not implemented yet.
- **Manual directional control** (`12`): not exposed, to avoid fighting the app.
- **Dust collection frequency** (`37`) and **volume** (`26`): not exposed yet.
- The integration polls every 30 s; state refreshes immediately after each command.

## Screenshots

Images live in `docs/images/`:

| File | Content |
| --- | --- |
| `docs/images/integracion.png` | The integration added in Settings → Devices & services |
| `docs/images/tarjeta.png` | The robot card with its entities on the dashboard |
| `docs/images/configuracion.png` | Setup form with the robot already detected and the local key as the only manual field |

## License

MIT. See [LICENSE](LICENSE).

## Notice

Unofficial project, not affiliated with Vactidy or Tuya. It uses the local protocol through
reverse engineering of your own device's traffic. If you update the robot firmware, the data
point map may change.
