"""SRAM AXS sensor platform — battery level."""
from __future__ import annotations

from homeassistant.components.bluetooth import (
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
    async_register_callback,
)
from homeassistant.components.bluetooth.models import BluetoothChange
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, LOGGER, SERVICE_UUID
from .parser import SramAxsAdvertisement, parse_advertisement


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SRAM AXS battery sensor from a config entry."""
    address: str = entry.data["address"]
    device_type: str = entry.data["device_type"]

    entity = SramAxsBatterySensor(address, device_type, entry.entry_id)
    async_add_entities([entity])

    @callback
    def _on_advertisement(
        service_info: BluetoothServiceInfoBleak,
        change: BluetoothChange,
    ) -> None:
        parsed = parse_advertisement(service_info)
        if parsed is not None:
            entity.update_from_advertisement(parsed)

    entry.async_on_unload(
        async_register_callback(
            hass,
            _on_advertisement,
            {"address": address, "service_uuids": {SERVICE_UUID}},
            BluetoothScanningMode.PASSIVE,
        )
    )

    LOGGER.debug("Sensor platform set up for %s", address)


class SramAxsBatterySensor(RestoreEntity, SensorEntity):
    """Battery level sensor for a SRAM AXS component."""

    entity_description = SensorEntityDescription(
        key="battery",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    )

    _attr_has_entity_name = True
    _attr_name = "Battery"

    def __init__(self, address: str, device_type: str, entry_id: str) -> None:
        """Initialise the sensor."""
        self._address = address
        self._device_type = device_type
        self._attr_unique_id = f"{entry_id}_battery"
        self._attr_native_value: int | None = None
        self._attr_available = False

        short = address.replace(":", "")[-6:].upper()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, address)},
            name=f"{device_type} {short}",
            manufacturer="SRAM",
            model=device_type,
        )

    async def async_added_to_hass(self) -> None:
        """Restore last known state on startup."""
        await super().async_added_to_hass()
        if (last_state := await self.async_get_last_state()) is not None:
            try:
                self._attr_native_value = int(last_state.state)
                self._attr_available = True
            except (ValueError, TypeError):
                pass

    @callback
    def update_from_advertisement(self, advertisement: SramAxsAdvertisement) -> None:
        """Push new data from an incoming advertisement."""
        self._attr_native_value = advertisement.battery_level
        self._attr_available = True
        self.async_write_ha_state()
        LOGGER.debug(
            "%s: battery updated to %d%%", self._address, advertisement.battery_level
        )
