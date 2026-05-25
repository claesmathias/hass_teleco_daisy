# Home Assistant Teleco Daisy Integration

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=claesmathias&repository=hass_teleco_daisy&category=integration)

Home Assistant custom component for Teleco Automation / TMate Daisy smart home devices.

## Supported devices

| Device | HA platform | Type | Model |
|---|---|---|---|
| White light (4-level) | `light` | 21 | 17, 34 |
| RGB light | `light` | 23 | 32 |
| 4-channel heater | `climate` | 21 | 20 |
| Slats cover (venetian blind) | `cover` | 24 | 27 |
| Retractable slats cover | `cover` | 24 | 44 |
| Shade / screen cover | `cover` | 22 | 25, 31 |
| Awning cover | `cover` | 22 | 21 |

Any device that does not match a known type/model is loaded as a generic device and will not appear in Home Assistant. A warning is logged with its type and model numbers — please open an issue if you have an unsupported device.

## Installation

### Via HACS (recommended)

1. Add this repository to HACS as a custom repository (Integration category).
2. Install **Teleco Daisy** from HACS.
3. Restart Home Assistant.
4. Go to **Settings → Devices & Services → Add Integration**.
5. Search for `Teleco Daisy`, enter your credentials and click **Submit**.

### Manual

1. Copy the `custom_components/teleco_daisy` directory into your `<config>/custom_components/` folder.
2. Restart Home Assistant.
3. Follow steps 4–5 above.

## Notes

- The integration polls all devices every 15 seconds.
- The Teleco cloud API is required; local-only operation is not supported.
- The `teleco-daisy` library is bundled inside the component, so no extra pip install is needed.

## Changelog

### 0.2.3

- **Bundled library** — the `teleco-daisy` API client is now included directly in the component. No PyPI dependency required; the integration installs cleanly on any HA instance via HACS.
- **Retractable slats cover** (type 24, model 44) — new device class. Command IDs are fetched dynamically from the API on first use.
- **Shade/screen cover state fix** — shades now correctly report as *open* when retracted. Teleco's API uses inverted semantics (`OPEN` = deployed, `CLOSE` = retracted); the mapping to HA `is_closed` is now correct.
- **Climate platform** — heater (type 21, model 20) is now exposed as a `climate` entity with HEAT/OFF modes and 50/75/100 % power presets.
- **Config flow fix** — added missing `strings.json`; the setup dialog no longer returns a 500 error.

### 0.1.12

- Added `DaisyAwningCover` (type 22, model 21).

### 0.1.10

- Added `DaisyWhite4LevelLight` (replaces `DaisyWhiteLight`).
- Fixed LED on/off for type 21 model 17.
- Fixed light brightness status update.

### 0.1.5

- Added 4-channel heater (type 21, model 20).
