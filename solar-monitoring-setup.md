# Solar & Battery Monitoring — Setup Summary

## Goal

Integrate the home solar panel and battery system into Home Assistant for ongoing
local monitoring, using the ECHONET Lite protocol over the local LAN.  No cloud
portal or CSV download is required — all data comes directly from the on-site
gateway.

---

## Hardware

| Device | Role |
|---|---|
| CB-P63M06A | 6.3 kWh battery package (Choshu Sangyo / Sharp SmartPV Multi OEM) |
| PCS-RP2A | Multi battery power conditioner (inverter) |
| RC-307A | LAN gateway — speaks ECHONET Lite on the local network |

The RC-307A is the key piece.  It exposes all solar and battery data via
**ECHONET Lite** (UDP multicast, port 3610) on the same LAN as the Raspberry Pi 5.

---

## What Was Added / Changed

### `tools/discover_echonet.py` — NEW

A standalone Python script to run on the Pi before setting up the HA integration.
It sends an ECHONET Lite multicast discovery query and prints the IP address and
supported object classes (solar, battery, etc.) of every responding device.

Run it with:
```bash
python3 tools/discover_echonet.py
```

Use the IP it reports when adding the ECHONET Lite integration in HA.

---

### `packages/solar.yaml` — NEW

Home Assistant package file for the solar/battery system.  Contains:

- **`utility_meter`** — daily and monthly totals for solar generation, grid import,
  and grid export
- **`template` sensors** — derived values:
  - Solar Power kW
  - Battery SOC %
  - Battery Power kW (positive = charging, negative = discharging)
  - Grid Import kW (買電)
  - Grid Export kW (売電)
  - Home Consumption kW (derived: Solar + Import − Export − Battery charging)
  - Self-Consumption Rate % — share of solar used at home rather than exported
  - Self-Sufficiency Rate % — share of home load covered by solar + battery

> **Important:** The ECHONET Lite integration itself is configured through the HA UI
> (Settings → Integrations → Add Integration → "ECHONET Lite").  After HA discovers
> the RC-307A, check the entity IDs it assigns and update the `sensor.rc_307a_*`
> placeholders in this file to match.

---

### `ui-lovelace.yaml` — NEW (replaces `dashboards/main.yaml`)

The main Lovelace dashboard in YAML mode.  HA reads this file automatically when
`lovelace: mode: yaml` is set in `configuration.yaml`.

Contains four views:

| View | Contents |
|---|---|
| Overview | Security (Ring), Cleaning (Eufy), Alexa media control |
| Switches | SwitchBot devices |
| Solar & Battery | Battery SOC gauge, live power flow, efficiency rates, 24 h history graph, daily/monthly generation totals, raw system detail |
| Scenes | Evening, Away |

If `dashboards/main.yaml` exists in the target repo, delete it — it is superseded
by `ui-lovelace.yaml`.

---

### `configuration.yaml` — MODIFIED

Two changes:

1. **Fixed duplicate `homeassistant:` key** — the original file had two separate
   `homeassistant:` blocks (one for location/locale settings, one for `packages:`).
   This is invalid YAML and silently prevented all packages from loading.  They are
   merged into a single block.

2. **Added `lovelace: mode: yaml`** — tells HA to read the default dashboard from
   `ui-lovelace.yaml` instead of its internal storage.  Built-in panels (Map, Energy,
   History, Logbook) are unaffected by this setting.

The final `configuration.yaml` should look like this:

```yaml
homeassistant:
  name: Hiropaccio Home
  latitude: !secret home_latitude
  longitude: !secret home_longitude
  elevation: !secret home_elevation
  unit_system: metric
  currency: JPY
  country: JP
  time_zone: Asia/Tokyo
  packages: !include_dir_named packages/

# Split automations into directory
automation: !include_dir_merge_list automations/

# Split scripts into directory
script: !include_dir_merge_named scripts/

# Split scenes into directory
scene: !include_dir_merge_list scenes/

# Enable the frontend (Lovelace)
frontend:
  themes: !include_dir_merge_named www/themes/

# Lovelace in YAML mode — reads from ui-lovelace.yaml in this directory
lovelace:
  mode: yaml

# Enable configuration UI
config:

# Enable Home Assistant API
api:

# Enable HTTP
http:

# Logbook and history
logbook:
history:

# Enable sun sensor
sun:

# Enable system health
system_health:
```

---

## Steps to Apply in the Target Repo (`honome-iot`, branch `stage`)

1. Copy `tools/discover_echonet.py` into the repo
2. Copy `packages/solar.yaml` into the repo
3. Copy `ui-lovelace.yaml` into the repo root; delete `dashboards/main.yaml` if present
4. Apply the two changes to `configuration.yaml` described above
5. Commit to `stage`
6. On the Pi: `git pull`, then **Developer Tools → Check Configuration** in HA
7. Restart HA
8. Run `python3 tools/discover_echonet.py` on the Pi to find the RC-307A IP
9. **Settings → Integrations → Add Integration → ECHONET Lite** — HA should
   auto-discover the RC-307A, or enter the IP from step 8 manually
10. After discovery, note the actual entity IDs HA assigns and update the
    `sensor.rc_307a_*` placeholders in `packages/solar.yaml`

---

## Source of These Files

The files live on branch `claude/solar-panel-csv-download-XJJEW` of
`https://github.com/hiropaccio/hiropaccio`.  They can be cherry-picked into
the target repo with:

```bash
git remote add tmp https://github.com/hiropaccio/hiropaccio.git
git fetch tmp claude/solar-panel-csv-download-XJJEW
git cherry-pick a946217 a30d07e c594167 ca3c79a
git remote remove tmp
```
