"""Parse SRAM AXS BLE advertisement data."""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak

from .const import (
    DEVICE_VARIANTS,
    LOGGER,
    MANUFACTURER_ID,
    MFR_MIN_LENGTH,
    MFR_OFFSET_BATTERY,
    MFR_OFFSET_STATUS,
    MFR_OFFSET_VARIANT,
    UNKNOWN_DEVICE_TYPE,
)


@dataclass
class SramAxsAdvertisement:
    """Parsed data from a single SRAM AXS advertisement."""

    address: str
    name: str
    variant: int
    device_type: str
    status_flags: int
    battery_level: int
    rssi: int

    @property
    def friendly_name(self) -> str:
        """Human-readable name combining device type and short address."""
        short = self.address.replace(":", "")[-6:].upper()
        return f"{self.device_type} {short}"


def parse_advertisement(
    service_info: BluetoothServiceInfoBleak,
) -> SramAxsAdvertisement | None:
    """
    Parse a BluetoothServiceInfoBleak into a SramAxsAdvertisement.

    Returns None if the advertisement does not carry valid AXS data.

    Manufacturer data layout (12 bytes, ID 2355 / 0x0933):
      [9]    variant — stable identifier for component type
      [10]   status flags
      [11]   battery level (0-100 %)
    """
    mfr_data: bytes | None = service_info.manufacturer_data.get(MANUFACTURER_ID)

    if mfr_data is None:
        LOGGER.debug(
            "%s: no manufacturer data for ID %d", service_info.address, MANUFACTURER_ID
        )
        return None

    if len(mfr_data) < MFR_MIN_LENGTH:
        LOGGER.debug(
            "%s: manufacturer data too short (%d bytes, need %d)",
            service_info.address,
            len(mfr_data),
            MFR_MIN_LENGTH,
        )
        return None

    variant = mfr_data[MFR_OFFSET_VARIANT]
    device_type = DEVICE_VARIANTS.get(variant, UNKNOWN_DEVICE_TYPE)
    status_flags = mfr_data[MFR_OFFSET_STATUS]
    battery_level = mfr_data[MFR_OFFSET_BATTERY]

    if not (0 <= battery_level <= 100):
        LOGGER.debug(
            "%s: battery value %d out of range, discarding",
            service_info.address,
            battery_level,
        )
        return None

    LOGGER.debug(
        "%s: parsed — variant=0x%02X (%s) battery=%d%% status=0x%02X",
        service_info.address,
        variant,
        device_type,
        battery_level,
        status_flags,
    )

    return SramAxsAdvertisement(
        address=service_info.address,
        name=service_info.name,
        variant=variant,
        device_type=device_type,
        status_flags=status_flags,
        battery_level=battery_level,
        rssi=service_info.rssi,
    )
