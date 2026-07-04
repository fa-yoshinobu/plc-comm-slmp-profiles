#!/usr/bin/env python3
"""Collect SLMP profile evidence from a connected PLC.

This tool is intended for remote investigations where another person runs a
single command on a PLC that the maintainer does not have.
"""

from __future__ import annotations

import argparse
import json
import random
import socket
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from live_profile_probe import (
    COMMAND_DEVICE_READ,
    COMMAND_DEVICE_WRITE,
    COMMAND_TYPE_NAME,
    Profile,
    device_payload,
    pack_bits,
    pack_words,
    request_frame,
    send_request,
    unpack_bits,
    unpack_words,
)


DEFAULT_HOST = "192.168.250.100"
DEFAULT_PORT = 1025
DEFAULT_WORD_WRITE_DEVICE = "D1000"
DEFAULT_BIT_WRITE_DEVICE = "M1000"
DEFAULT_S_WRITE_DEVICE = "S2"


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def load_profile(root: Path, profile_id: str) -> tuple[dict[str, Any], Profile]:
    capability = load_json(root / "capability" / "slmp_builtin_ethernet_profiles.json")
    raw = capability["profiles"][profile_id]
    return capability, Profile(
        name=profile_id,
        frame=str(raw["frame"]),
        compat=str(raw["compat"]),
        subcommands={key: int(value, 16) for key, value in raw["subcommands"].items()},
    )


def open_socket(host: str, port: int, timeout: float) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((host, port))
    return sock


def request(
    *,
    host: str,
    port: int,
    timeout: float,
    profile: Profile,
    command: int,
    subcommand: int,
    data: bytes,
    serial: int,
    network: int,
    station: int,
    module_io: int,
    multidrop: int,
    monitoring_timer: int,
) -> dict[str, Any]:
    try:
        with open_socket(host, port, timeout) as sock:
            frame = request_frame(
                profile,
                command,
                subcommand,
                data,
                serial=serial,
                monitoring_timer=monitoring_timer,
                network=network,
                station=station,
                module_io=module_io,
                multidrop=multidrop,
            )
            response = send_request(sock, profile, frame)
        return {
            "ok": True,
            "end_code": f"{response.end_code:04X}",
            "data_hex": response.data.hex(),
        }
    except Exception as exc:  # noqa: BLE001 - field collector must keep going.
        return {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
        }


def collect_type_name(args: argparse.Namespace, profile: Profile) -> dict[str, Any]:
    result = request(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        profile=profile,
        command=COMMAND_TYPE_NAME,
        subcommand=0x0000,
        data=b"",
        serial=1,
        network=args.network,
        station=args.station,
        module_io=args.module_io,
        multidrop=args.multidrop,
        monitoring_timer=args.monitoring_timer,
    )
    if result.get("ok") and result.get("end_code") == "0000":
        raw = bytes.fromhex(result["data_hex"])
        name = raw[:16].rstrip(b"\x00 ").decode("ascii", errors="replace")
        result["text"] = name
        result["type_name"] = name
        if len(raw) >= 18:
            type_code = raw[16:18]
            result["type_code"] = f"{int.from_bytes(type_code, 'little'):04X}"
            result["type_code_raw_hex"] = type_code.hex()
        if len(raw) > 18:
            result["extra_hex"] = raw[18:].hex()
    return result


def unpack_dwords(data: bytes, count: int) -> list[int]:
    value_count = min(len(data) // 4, count)
    return [int.from_bytes(data[index * 4 : index * 4 + 4], "little") for index in range(value_count)]


def collect_read(
    args: argparse.Namespace,
    profile: Profile,
    *,
    device: str,
    points: int,
    bit: bool,
    serial: int,
    device_type: str | None = None,
) -> dict[str, Any]:
    subcommand = profile.subcommands["bit" if bit else "word"]
    result = request(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        profile=profile,
        command=COMMAND_DEVICE_READ,
        subcommand=subcommand,
        data=device_payload(profile, device, points),
        serial=serial,
        network=args.network,
        station=args.station,
        module_io=args.module_io,
        multidrop=args.multidrop,
        monitoring_timer=args.monitoring_timer,
    )
    result["device"] = device
    result["points"] = points
    result["kind"] = "bit" if bit else "word"
    if device_type:
        result["device_type"] = device_type
    if result.get("ok") and result.get("end_code") == "0000":
        raw = bytes.fromhex(result["data_hex"])
        result["value_bytes"] = len(raw)
        result["values"] = unpack_bits(raw, points) if bit else unpack_words(raw, points)
        if device_type == "dword":
            dword_values = unpack_dwords(raw, points)
            if dword_values:
                result["values_32bit"] = dword_values
    return result


def collect_write(
    args: argparse.Namespace,
    profile: Profile,
    *,
    device: str,
    value: int,
    bit: bool,
    serial: int,
    reset_bit: bool,
) -> dict[str, Any]:
    subcommand = profile.subcommands["bit" if bit else "word"]
    data = pack_bits([bool(value)]) if bit else pack_words([value])
    write_result = request(
        host=args.host,
        port=args.port,
        timeout=args.timeout,
        profile=profile,
        command=COMMAND_DEVICE_WRITE,
        subcommand=subcommand,
        data=device_payload(profile, device, 1, data),
        serial=serial,
        network=args.network,
        station=args.station,
        module_io=args.module_io,
        multidrop=args.multidrop,
        monitoring_timer=args.monitoring_timer,
    )
    read_result = collect_read(args, profile, device=device, points=1, bit=bit, serial=serial + 1)
    result: dict[str, Any] = {
        "device": device,
        "kind": "bit" if bit else "word",
        "value": bool(value) if bit else value,
        "write": write_result,
        "read_after_write": read_result,
    }
    if bit and reset_bit:
        reset_data = pack_bits([False])
        reset_result = request(
            host=args.host,
            port=args.port,
            timeout=args.timeout,
            profile=profile,
            command=COMMAND_DEVICE_WRITE,
            subcommand=subcommand,
            data=device_payload(profile, device, 1, reset_data),
            serial=serial + 2,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
            monitoring_timer=args.monitoring_timer,
        )
        result["reset_to_off"] = reset_result
        result["read_after_reset"] = collect_read(args, profile, device=device, points=1, bit=True, serial=serial + 3)
    return result


def collect_write_probes(args: argparse.Namespace, profile: Profile) -> dict[str, Any]:
    rng = random.SystemRandom()
    word_value = rng.randint(1, 0xFFFF)
    return {
        "enabled": True,
        "numeric_values_are_random": True,
        "numeric_values_are_not_restored": True,
        "bit_values_are_reset_to_off": True,
        "items": {
            "direct_word": collect_write(
                args,
                profile,
                device=args.word_write_device,
                value=word_value,
                bit=False,
                serial=10,
                reset_bit=False,
            ),
            "direct_bit": collect_write(
                args,
                profile,
                device=args.bit_write_device,
                value=1,
                bit=True,
                serial=20,
                reset_bit=True,
            ),
            "s_policy": collect_write(
                args,
                profile,
                device=args.s_write_device,
                value=1,
                bit=True,
                serial=30,
                reset_bit=True,
            ),
        },
    }


def family_probe_device(device_name: str) -> str:
    return f"{device_name}0"


def collect_device_family_reads(
    args: argparse.Namespace,
    profile: Profile,
    device_ranges: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = device_ranges["rows"]
    results: list[dict[str, Any]] = []
    serial = 100
    for family in device_ranges["ordered_items"]:
        row = rows[family]
        for device in row.get("devices", []):
            device_name = device["device"]
            device_type = str(device.get("type", "bit" if device.get("is_bit") else "word"))
            is_bit = bool(device.get("is_bit"))
            probe = family_probe_device(device_name)
            result = collect_read(
                args,
                profile,
                device=probe,
                points=1,
                bit=is_bit,
                serial=serial,
                device_type=device_type,
            )
            result["family"] = family
            result["device_code"] = device_name
            result["expected_rule"] = (
                device_ranges.get("profiles", {})
                .get(args.profile, {})
                .get("rules", {})
                .get(family, {})
            )
            results.append(result)
            serial += 1
    return results


def collect_sd_range(args: argparse.Namespace, profile: Profile, device_ranges: dict[str, Any]) -> dict[str, Any]:
    range_profile = device_ranges.get("profiles", {}).get(args.profile)
    if not range_profile:
        return {"ok": False, "message": "no device-range profile block"}
    start = int(range_profile["register_start"])
    count = int(range_profile["register_count"])
    result = collect_read(args, profile, device=f"SD{start}", points=count, bit=False, serial=50)
    result["register_start"] = start
    result["register_count"] = count
    return result


def collect(args: argparse.Namespace) -> dict[str, Any]:
    root = app_root()
    capability, profile = load_profile(root, args.profile)
    device_ranges = load_json(root / "device-ranges" / "slmp_device_range_rules.json")
    profile_json = capability["profiles"][args.profile]
    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    return {
        "schema_version": 1,
        "collector": "collect_live_plc_profile.py",
        "timestamp": timestamp,
        "connection": {
            "host": args.host,
            "port": args.port,
            "timeout": args.timeout,
            "network": args.network,
            "station": args.station,
            "module_io": args.module_io,
            "multidrop": args.multidrop,
            "monitoring_timer": args.monitoring_timer,
        },
        "site_note": args.site_note,
        "plc_model": args.plc_model,
        "profile": args.profile,
        "profile_settings": {
            "frame": profile_json["frame"],
            "compat": profile_json["compat"],
            "subcommands": profile_json["subcommands"],
            "features": profile_json.get("features", {}),
            "limits": profile_json.get("limits", {}),
            "write_policy": profile_json.get("write_policy", {}),
        },
        "type_name": collect_type_name(args, profile),
        "write_probes": collect_write_probes(args, profile),
        "sd_range_block": collect_sd_range(args, profile, device_ranges),
        "device_family_reads": collect_device_family_reads(args, profile, device_ranges),
    }


def default_output(profile_id: str) -> Path:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = profile_id.replace("melsec:", "").replace(":", "-")
    return Path(f"slmp_profile_collect_{slug}_{stamp}.json")


def build_parser() -> argparse.ArgumentParser:
    root = app_root()
    capability = load_json(root / "capability" / "slmp_builtin_ethernet_profiles.json")
    parser = argparse.ArgumentParser(description="Collect SLMP profile evidence from a connected PLC.")
    parser.add_argument("--list-profiles", action="store_true", help="List bundled canonical profile IDs and exit.")
    parser.add_argument("--profile", choices=sorted(capability["profiles"]), help="Canonical profile ID.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--network", type=lambda value: int(value, 0), default=0x00)
    parser.add_argument("--station", type=lambda value: int(value, 0), default=0xFF)
    parser.add_argument("--module-io", type=lambda value: int(value, 0), default=0x03FF)
    parser.add_argument("--multidrop", type=lambda value: int(value, 0), default=0x00)
    parser.add_argument("--monitoring-timer", type=lambda value: int(value, 0), default=0x0010)
    parser.add_argument("--plc-model", default="")
    parser.add_argument("--site-note", default="", help="Free-form note, such as module/port setup.")
    parser.add_argument("--word-write-device", default=DEFAULT_WORD_WRITE_DEVICE)
    parser.add_argument("--bit-write-device", default=DEFAULT_BIT_WRITE_DEVICE)
    parser.add_argument("--s-write-device", default=DEFAULT_S_WRITE_DEVICE)
    parser.add_argument("--output", type=Path, help="Output JSON file. Defaults to the current directory.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    root = app_root()
    capability = load_json(root / "capability" / "slmp_builtin_ethernet_profiles.json")
    if args.list_profiles:
        for profile_id in sorted(capability["profiles"]):
            print(profile_id)
        return 0
    if not args.profile:
        parser.error("--profile is required unless --list-profiles is used")
    result = collect(args)
    output = args.output or default_output(args.profile)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(output.resolve())
    print("collection finished")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
