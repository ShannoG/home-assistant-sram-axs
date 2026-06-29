"""Constants for the SRAM AXS integration."""
from __future__ import annotations

import logging

DOMAIN = "sram_axs"
LOGGER = logging.getLogger(__package__)

# Manufacturer ID 2355 (0x0933) is SRAM LLC
MANUFACTURER_ID = 2355

# Service UUID advertised by all AXS components
SERVICE_UUID = "0000fe51-0000-1000-8000-00805f9b34fb"

# Manufacturer data byte offsets
MFR_OFFSET_VARIANT = 9   # stable device-type identifier
MFR_OFFSET_STATUS = 10
MFR_OFFSET_BATTERY = 11
MFR_MIN_LENGTH = 12

# Device variant byte (mfr_data[9]) — consistent across advertisements
# for a given physical component type.
# Add new values here as they are discovered from debug logs.
DEVICE_VARIANTS: dict[int, str] = {
    0x03: "Rear Derailleur",
    0x02: "Dropper Post",
    # 0x??:  "Front Derailleur",
    # 0x??:  "Shifter Pod",
    # 0x??:  "Brake Lever",
}

UNKNOWN_DEVICE_TYPE = "AXS Component"
