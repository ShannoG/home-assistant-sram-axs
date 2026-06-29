"""Coordinator for SRAM AXS passive BLE advertisements."""
from __future__ import annotations

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.components.bluetooth.passive_update_processor import (
    PassiveBluetoothProcessorCoordinator,
)
from homeassistant.core import HomeAssistant

from .const import LOGGER
from .parser import SramAxsAdvertisement, parse_advertisement


def _process_advertisement(
    service_info: BluetoothServiceInfoBleak,
) -> SramAxsAdvertisement | None:
    """Parse an incoming advertisement; return data or None to skip."""
    return parse_advertisement(service_info)


class SramAxsCoordinator(
    PassiveBluetoothProcessorCoordinator[SramAxsAdvertisement | None]
):
    """
    Coordinator that receives passive BLE advertisements for one AXS device.

    HA calls _process_advertisement every time an advertisement is seen.
    If it returns non-None the coordinator pushes the update to all registered
    PassiveBluetoothDataProcessor instances (i.e. our sensor platform).
    """

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        """Initialise the coordinator for the given device address."""
        super().__init__(
            hass,
            LOGGER,
            address=address,
            mode=BluetoothScanningMode.PASSIVE,
            update_method=_process_advertisement,
        )
        LOGGER.debug("SramAxsCoordinator created for %s", address)
