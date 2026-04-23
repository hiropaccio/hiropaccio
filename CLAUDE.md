# CLAUDE.md — hiropaccio/hiropaccio

This file provides context for AI assistants (Claude, Copilot, etc.) working in this repository.

## Project Overview

This is the GitHub profile repository for **@hiropaccio**, which also serves as the home for a personal **home IoT automation project** built on [Home Assistant](https://www.home-assistant.io/). The primary goal is to unify a diverse set of smart home devices under a single Home Assistant instance running on a Raspberry Pi 5.

---

## Hardware Setup

### Server / Controller
| Device | Role |
|---|---|
| Raspberry Pi 5 | Home Assistant server, primary controller |
| HD touch monitor (connected to Pi) | Primary local dashboard |

### Room Display Clients
These devices run the Home Assistant frontend UI as per-room control panels:
| Device | Notes |
|---|---|
| Android tablet | Room touch client |
| Windows 8 tablet | Room touch client |
| Old iPad | Room touch client |

For these clients, use the **Home Assistant Companion app** (Android/iOS) or a browser pointed at `http://<pi-ip>:8123`. The Windows 8 tablet will need a modern browser (Chrome/Edge) since it cannot run the Companion app.

### Integrated Smart Devices
| Device | Integration | Protocol |
|---|---|---|
| SwitchBot hub + devices | [SwitchBot](https://www.home-assistant.io/integrations/switchbot/) | BLE / cloud |
| Ring camera | [Ring](https://www.home-assistant.io/integrations/ring/) | Cloud |
| Eufy robot cleaners | [Eufy Security](https://github.com/fuatakgun/eufy_security) | Cloud |
| Amazon Alexa Echo | [Alexa Media Player](https://github.com/custom-components/alexa_media_player) | Cloud |

---

## Software Stack

- **Home Assistant OS (HAOS)** — recommended install on Raspberry Pi 5
- **YAML** — all automations, scripts, scenes, and manual configuration
- **HACS** (Home Assistant Community Store) — for community integrations not yet in core

### Key Integrations

| Integration | Type | Purpose |
|---|---|---|
| SwitchBot | Built-in | Smart switches, plugs, sensors |
| Ring | Built-in | Doorbell/camera alerts |
| Eufy Security | HACS | Robot vacuum control |
| Alexa Media Player | HACS | Alexa TTS, play/pause, announcements |

---

## Repository Structure

```
hiropaccio/
├── README.md          # GitHub profile display page
├── CLAUDE.md          # This file — AI assistant context
└── (future)
    ├── automations/   # HA automation YAML files
    ├── scripts/       # HA script YAML files
    ├── dashboards/    # Lovelace dashboard config
    └── secrets.yaml.example  # Template for secrets (never commit real secrets)
```

---

## Development Workflow

1. **Edit** YAML configuration files locally (or directly on the Pi via SSH)
2. **Test** changes in the Home Assistant UI (`Settings → Automations / Scripts`)
3. **Validate** YAML with `yamllint` or the HA config checker (`Developer Tools → Check Configuration`)
4. **Commit** to a feature branch and open a PR into `main`
5. **Deploy** by syncing files to the Pi (e.g., `scp`, `rsync`, or the HA file editor add-on)

### Branch Strategy
- Feature branches: `feature/<description>` or `claude/<description>`
- Merge target: `main`
- Never commit secrets to any branch

---

## Conventions for AI Assistants

### YAML Style
- Indentation: **2 spaces** (no tabs)
- String quoting: use double quotes for values that contain special characters
- Keep automations atomic — one trigger/action purpose per automation

### Secrets Management
- All credentials, tokens, and passwords go in `secrets.yaml`
- Reference them with `!secret <key_name>` — never hardcode values
- `secrets.yaml` is in `.gitignore` — provide a `secrets.yaml.example` template instead

### Entity ID Naming
- Format: `<domain>.<location>_<device>_<attribute>` (snake_case)
- Example: `switch.living_room_tv_power`, `sensor.bedroom_temperature`
- Be consistent with location names across all configs

### Integration Preferences
- Prefer **built-in HA integrations** over HACS custom components when both exist
- When a local API exists (e.g., SwitchBot local API), prefer it over cloud polling to reduce latency and dependency on external services
- For Ring and Eufy (cloud-only), accept cloud dependency but handle failures gracefully in automations

### Automations
- Use `mode: single` unless concurrent runs are explicitly needed
- Add a `description:` field to every automation for clarity
- Group related automations with consistent `alias:` prefixes (e.g., `"Security: "`, `"Cleaning: "`, `"Morning: "`)

### No Build Step
This is a configuration-driven project. There is no compilation, no test suite to run, and no package manager. Validation is done through Home Assistant's built-in config checker.

---

## Useful References

- [Home Assistant Docs](https://www.home-assistant.io/docs/)
- [HA Automation Docs](https://www.home-assistant.io/docs/automation/)
- [SwitchBot Integration](https://www.home-assistant.io/integrations/switchbot/)
- [Ring Integration](https://www.home-assistant.io/integrations/ring/)
- [HACS](https://hacs.xyz/)
