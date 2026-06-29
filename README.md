# SRAM AXS — Home Assistant Integration

Passive Bluetooth integration for SRAM AXS components (derailleurs, dropper posts, and more). Battery levels are read directly from BLE advertisements — no GATT connection required, so devices don't need to stay awake.

## Supported devices

| Device | Type byte |
|---|---|
| Rear Derailleur | `0x63` |
| Dropper Post | `0x37` |

More devices can be added to `const.py` as their type bytes are discovered.

## How it works

AXS components wake and advertise when shaken. Each advertisement contains manufacturer data (ID `0x0933`) where byte 11 is the battery percentage. This integration registers a passive BLE callback with Home Assistant — no polling, no connection, no impact on device battery life.

Works with any Bluetooth source HA supports: built-in adapter, or ESPHome BT proxies running `bluetooth_proxy: active: true`.

## Installation

### HACS (recommended)

1. Add this repo as a custom HACS repository (type: Integration)
2. Install "SRAM AXS"
3. Restart Home Assistant

### Manual

Copy `custom_components/sram_axs/` into your HA `config/custom_components/` directory and restart.

## Setup

Wake an AXS component (shake it). Within a few seconds it will appear in **Settings → Devices & Services → Discovered**. Click Configure and confirm.

If auto-discovery doesn't trigger, go to **Add Integration**, search for "SRAM AXS", and pick from the list of currently visible devices.

## ESPHome proxy configuration

Your ESPHome BT proxy needs active mode enabled so HA can route through it:

```yaml
bluetooth_proxy:
  active: true
```

Passive-only proxies will still forward advertisements (enough for battery updates) but won't support GATT connections if those are added later.

## Entities

Each device gets one entity:

| Entity | Class | Notes |
|---|---|---|
| Battery | `battery` | Updates each time the device advertises |
