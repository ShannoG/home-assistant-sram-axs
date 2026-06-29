"""
Decode SRAM AXS BLE advertisement data from captured JSON files.
Usage: python decode.py advertised-data/rd.json advertised-data/dropper.json
"""

import json
import sys
import struct

MANUFACTURER_ID = 2355  # 0x0933 - SRAM

# Known device type bytes (mfr_data[7])
DEVICE_TYPES = {
    0x63: "Rear Derailleur",
    0x37: "Dropper Post",
    # Add more as discovered
}


def decode_manufacturer_data(data: bytes) -> dict:
    """
    Manufacturer data layout (12 bytes):
      [0:7]  00 00 01 01 00 04 05  - constant preamble
      [7]    device type byte
      [8]    firmware / product family
      [9]    variant / channel
      [10]   status flags
      [11]   battery level (%)
    """
    if len(data) < 12:
        return {"error": f"too short: {len(data)} bytes"}

    device_type_byte = data[7]
    device_type = DEVICE_TYPES.get(device_type_byte, f"Unknown (0x{device_type_byte:02X})")

    return {
        "preamble": data[0:7].hex(),
        "device_type_byte": f"0x{device_type_byte:02X}",
        "device_type": device_type,
        "byte_8": f"0x{data[8]:02X} ({data[8]})",
        "byte_9": f"0x{data[9]:02X} ({data[9]})",
        "status_flags": f"0x{data[10]:02X} ({data[10]:08b})",
        "battery_level": data[11],
    }


def decode_service_data(data: bytes) -> dict:
    """
    Service data layout (9 bytes, service 0000fe51-...):
      [0]    0x0d - constant
      [1]    0x03 - constant
      [2:8]  6 bytes - possibly device serial / MAC-derived
      [8]    status / flags
    """
    if len(data) < 9:
        return {"error": f"too short: {len(data)} bytes"}

    return {
        "header": data[0:2].hex(),
        "device_id_bytes": data[2:8].hex(),
        "last_byte": f"0x{data[8]:02X} ({data[8]:08b})",
    }


def decode_raw_adv(raw: bytes) -> list[dict]:
    """Walk the raw advertisement LTV structures."""
    structures = []
    i = 0
    ad_types = {
        0x01: "Flags",
        0x02: "Incomplete 16-bit UUIDs",
        0x03: "Complete 16-bit UUIDs",
        0x07: "Complete 128-bit UUIDs",
        0x09: "Complete Local Name",
        0x0A: "TX Power Level",
        0x16: "Service Data (16-bit UUID)",
        0xFF: "Manufacturer Specific Data",
    }
    while i < len(raw):
        length = raw[i]
        if length == 0:
            break
        ad_type = raw[i + 1]
        payload = raw[i + 2: i + 1 + length]
        structures.append({
            "type": f"0x{ad_type:02X} ({ad_types.get(ad_type, 'Unknown')})",
            "length": length,
            "payload_hex": payload.hex(),
        })
        i += 1 + length
    return structures


def analyse(path: str) -> None:
    with open(path) as f:
        adv = json.load(f)

    print(f"\n{'=' * 60}")
    print(f"Device:  {adv['name']}")
    print(f"Address: {adv['address']}")
    print(f"RSSI:    {adv['rssi']} dBm")
    print(f"Connectable: {adv['connectable']}")

    # Manufacturer data
    print(f"\n--- Manufacturer Data (ID {MANUFACTURER_ID} / 0x{MANUFACTURER_ID:04X}) ---")
    mfr_hex = adv["manufacturer_data"].get(str(MANUFACTURER_ID))
    if mfr_hex:
        mfr_bytes = bytes.fromhex(mfr_hex)
        print(f"Raw: {' '.join(f'{b:02X}' for b in mfr_bytes)}")
        decoded = decode_manufacturer_data(mfr_bytes)
        for k, v in decoded.items():
            print(f"  {k:20s}: {v}")
    else:
        print("  Not present")

    # Service data
    print(f"\n--- Service Data (0000fe51-...) ---")
    svc_hex = adv["service_data"].get("0000fe51-0000-1000-8000-00805f9b34fb")
    if svc_hex:
        svc_bytes = bytes.fromhex(svc_hex)
        print(f"Raw: {' '.join(f'{b:02X}' for b in svc_bytes)}")
        decoded = decode_service_data(svc_bytes)
        for k, v in decoded.items():
            print(f"  {k:20s}: {v}")
    else:
        print("  Not present")

    # Raw LTV walk
    print(f"\n--- Raw Advertisement LTV Structures ---")
    raw_bytes = bytes.fromhex(adv["raw"])
    for s in decode_raw_adv(raw_bytes):
        print(f"  {s['type']}")
        print(f"    len={s['length']}  payload={s['payload_hex']}")


def compare(paths: list[str]) -> None:
    devices = []
    for path in paths:
        with open(path) as f:
            adv = json.load(f)
        mfr_hex = adv["manufacturer_data"].get(str(MANUFACTURER_ID), "")
        mfr = bytes.fromhex(mfr_hex) if mfr_hex else b""
        devices.append((adv["name"], adv["address"], mfr))

    if len(devices) < 2:
        return

    print(f"\n{'=' * 60}")
    print("MANUFACTURER DATA BYTE COMPARISON")
    print(f"{'Byte':<6}", end="")
    for name, addr, _ in devices:
        label = name.split()[-1]  # use the number part
        print(f"  {label:>14}", end="")
    print("  same?")

    max_len = max(len(m) for _, _, m in devices)
    for i in range(max_len):
        vals = [m[i] if i < len(m) else None for _, _, m in devices]
        same = "==" if len(set(v for v in vals if v is not None)) == 1 else "!!"
        print(f"  [{i:2d}]", end="")
        for v in vals:
            cell = f"0x{v:02X}={v:3d}" if v is not None else "  ---  "
            print(f"  {cell:>14}", end="")
        print(f"  {same}")

    print(f"\nBattery levels:")
    for name, addr, mfr in devices:
        if len(mfr) >= 12:
            print(f"  {name} ({addr}): {mfr[11]}%")


if __name__ == "__main__":
    paths = sys.argv[1:] if len(sys.argv) > 1 else [
        "advertised-data/rd.json",
        "advertised-data/dropper.json",
    ]

    for path in paths:
        analyse(path)

    if len(paths) > 1:
        compare(paths)
