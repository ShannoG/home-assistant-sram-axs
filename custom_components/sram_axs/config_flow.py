"""Config flow for SRAM AXS integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.selector import (
    SelectOptionDict,
    SelectSelector,
    SelectSelectorConfig,
)

from .const import DEVICE_VARIANTS, DOMAIN, LOGGER, UNKNOWN_DEVICE_TYPE
from .parser import SramAxsAdvertisement, parse_advertisement

# Presented in the UI for the user to pick from
DEVICE_TYPE_OPTIONS = [
    SelectOptionDict(value="Rear Derailleur", label="Rear Derailleur"),
    SelectOptionDict(value="Front Derailleur", label="Front Derailleur"),
    SelectOptionDict(value="Dropper Post", label="Dropper Post"),
    SelectOptionDict(value="Left Shifter Pod", label="Left Shifter Pod"),
    SelectOptionDict(value="Right Shifter Pod", label="Right Shifter Pod"),
    SelectOptionDict(value="Brake Lever", label="Brake Lever"),
    SelectOptionDict(value="AXS Component", label="Other / Unknown"),
]


class SramAxsConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SRAM AXS."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialise the config flow."""
        self._discovery: SramAxsAdvertisement | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a device discovered via Bluetooth."""
        LOGGER.debug("Bluetooth discovery: %s", discovery_info.address)

        parsed = parse_advertisement(discovery_info)
        if parsed is None:
            return self.async_abort(reason="not_supported")

        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        self._discovery = parsed
        self.context["title_placeholders"] = {"name": parsed.friendly_name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user to confirm and identify the discovered device."""
        assert self._discovery is not None

        if user_input is not None:
            device_type = user_input.get("device_type", self._discovery.device_type)
            short = self._discovery.address.replace(":", "")[-6:].upper()
            return self.async_create_entry(
                title=f"{device_type} {short}",
                data={
                    "address": self._discovery.address,
                    "variant": self._discovery.variant,
                    "device_type": device_type,
                },
            )

        # Pre-select the parsed type if we recognise it, else leave blank
        guessed = self._discovery.device_type
        suggested = guessed if guessed != UNKNOWN_DEVICE_TYPE else None

        return self.async_show_form(
            step_id="bluetooth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required("device_type", default=suggested): SelectSelector(
                        SelectSelectorConfig(options=DEVICE_TYPE_OPTIONS)
                    ),
                }
            ),
            description_placeholders={
                "address": self._discovery.address,
            },
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle manual setup."""
        if user_input is not None:
            address = user_input["address"]
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()

            for svc_info in async_discovered_service_info(self.hass, connectable=False):
                if svc_info.address == address:
                    parsed = parse_advertisement(svc_info)
                    if parsed:
                        return self.async_create_entry(
                            title=parsed.friendly_name,
                            data={
                                "address": parsed.address,
                                "device_type_byte": parsed.device_type_byte,
                                "device_type": parsed.device_type,
                            },
                        )
            return self.async_abort(reason="not_supported")

        current = self._async_current_ids(include_ignore=False)
        devices: dict[str, str] = {}
        for svc_info in async_discovered_service_info(self.hass, connectable=False):
            if svc_info.address in current or svc_info.address in devices:
                continue
            parsed = parse_advertisement(svc_info)
            if parsed:
                devices[svc_info.address] = parsed.friendly_name

        if not devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                SelectOptionDict(value=addr, label=name)
                                for addr, name in devices.items()
                            ]
                        )
                    )
                }
            ),
        )
