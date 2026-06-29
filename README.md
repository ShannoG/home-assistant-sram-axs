# SRAM AXS — Home Assistant Integration

Passive Bluetooth integration for SRAM AXS components. Battery levels are read directly from BLE advertisements — no GATT connection required, so devices don't need to stay awake long enough to pair.

## How it works

AXS components wake and advertise when shaken. Each advertisement contains manufacturer data (ID `0x0933` / 2355) where the last byte is the battery percentage. This integration registers a passive BLE callback — no polling, no connection, no impact on device battery life.

Works with any Bluetooth source HA supports: built-in adapter, or ESPHome BT proxies.

## Supported components

Any SRAM AXS component that advertises with service UUID `0000fe51-0000-1000-8000-00805f9b34fb`. You select the component type manually during setup. Known to work:

- Rear Derailleur (Eagle AXS, Red AXS)
- Dropper Post (Reverb AXS)

Others (front derailleur, shifter pods, brake levers) should work — the advertisement format is consistent across the AXS range.

## Installation

### HACS (recommended)

1. Add this repo as a custom HACS repository (type: Integration)
2. Install "SRAM AXS"
3. Restart Home Assistant

### Manual

Copy `custom_components/sram_axs/` into your HA `config/custom_components/` directory and restart.

## Setup

1. Wake an AXS component by shaking it
2. Within a few seconds it should appear in **Settings → Devices & Services → Discovered**
3. Click Configure, select the component type from the dropdown, and confirm

If auto-discovery doesn't trigger, go to **Add Integration → SRAM AXS** to pick from currently visible devices.

## ESPHome proxy

Any ESPHome BT proxy will work. Passive mode is sufficient since we only need to receive advertisements:

```yaml
bluetooth_proxy:
  active: false
```

Active mode (`true`) is also fine and gives you the option of adding GATT-based features later.

## Entities

Each device gets one entity:

| Entity | Class | Notes |
|---|---|---|
| Battery | `battery` | Updates each time the device wakes and advertises |

Battery state is restored across HA restarts from the last known value.

## Notes on device identification

The advertisement payload does not contain a stable device type field — bytes in the manufacturer data change between each wake cycle. Device type is therefore set manually during setup and stored in the config entry. If you configure a device incorrectly, delete the integration entry and re-add it.

## Contributing

If you have other AXS components (front derailleur, shifter pods, etc.) and can confirm they work, please open an issue or PR. The integration should work with any AXS component out of the box — the only thing that varies is the label shown in HA.
