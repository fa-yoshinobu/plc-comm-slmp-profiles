#!/usr/bin/env python3
"""Raw SLMP live probe for profile evidence.

This tool is intentionally small and transport-level. It reads the canonical
profile JSON for frame/compat/subcommand choices, sends raw SLMP requests, and
prints concise JSON results. It does not apply client-library guards and
does not write evidence files. If a one-off result matters for a maintained
profile, add the check to run_unit_probe_plan.py and the reviewed plan JSON.
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _data_root() -> Path:
    if getattr(sys, "frozen", False):  # bundled single-file executable
        return Path(getattr(sys, "_MEIPASS"))
    return Path(__file__).resolve().parents[1]


ROOT = _data_root()
CAPABILITY_JSON = ROOT / "capability" / "slmp_ethernet_profiles.json"


DEVICE_CODES: dict[str, tuple[int, int]] = {
    "SM": (0x0091, 10),
    "SD": (0x00A9, 10),
    "X": (0x009C, 16),
    "Y": (0x009D, 16),
    "M": (0x0090, 10),
    "L": (0x0092, 10),
    "F": (0x0093, 10),
    "V": (0x0094, 10),
    "B": (0x00A0, 16),
    "S": (0x0098, 10),
    "D": (0x00A8, 10),
    "W": (0x00B4, 16),
    "TS": (0x00C1, 10),
    "TC": (0x00C0, 10),
    "TN": (0x00C2, 10),
    "STS": (0x00C7, 10),
    "STC": (0x00C6, 10),
    "STN": (0x00C8, 10),
    "CS": (0x00C4, 10),
    "CC": (0x00C3, 10),
    "CN": (0x00C5, 10),
    "SB": (0x00A1, 16),
    "SW": (0x00B5, 16),
    "Z": (0x00CC, 10),
    "LZ": (0x0062, 10),
    "R": (0x00AF, 10),
    "ZR": (0x00B0, 10),
    "RD": (0x002C, 10),
    "G": (0x00AB, 10),
    "HG": (0x002E, 10),
    "LTS": (0x0051, 10),
    "LTC": (0x0050, 10),
    "LTN": (0x0052, 10),
    "LSTS": (0x0059, 10),
    "LSTC": (0x0058, 10),
    "LSTN": (0x005A, 10),
    "LCS": (0x0055, 10),
    "LCC": (0x0054, 10),
    "LCN": (0x0056, 10),
}

COMMAND_DEVICE_READ = 0x0401
COMMAND_DEVICE_WRITE = 0x1401
COMMAND_DEVICE_READ_RANDOM = 0x0403
COMMAND_DEVICE_WRITE_RANDOM = 0x1402
COMMAND_DEVICE_READ_BLOCK = 0x0406
COMMAND_DEVICE_WRITE_BLOCK = 0x1406
COMMAND_DEVICE_ENTRY_MONITOR = 0x0801
COMMAND_DEVICE_EXECUTE_MONITOR = 0x0802
COMMAND_TYPE_NAME = 0x0101


@dataclass(frozen=True)
class Profile:
    name: str
    frame: str
    compat: str
    subcommands: dict[str, int]


@dataclass(frozen=True)
class Response:
    end_code: int
    data: bytes


def parse_u16_hex(value: str) -> int:
    text = value.strip()
    try:
        number = int(text[2:] if text.lower().startswith("0x") else text, 16)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected 16-bit hex value: {value!r}") from exc
    if not 0 <= number <= 0xFFFF:
        raise argparse.ArgumentTypeError(f"expected 16-bit value: {value!r}")
    return number


def load_profile(name: str) -> Profile:
    with CAPABILITY_JSON.open("r", encoding="utf-8") as fh:
        root = json.load(fh)
    raw = root["profiles"].get(name)
    if raw is None:
        supported = ", ".join(sorted(root["profiles"]))
        raise ValueError(f"unknown profile {name!r}; supported profiles: {supported}")
    return Profile(
        name=name,
        frame=str(raw["frame"]),
        compat=str(raw["compat"]),
        subcommands={key: int(value, 16) for key, value in raw["subcommands"].items()},
    )


def load_probe_profile(args: argparse.Namespace) -> Profile:
    profile = load_profile(args.profile)
    subcommands = dict(profile.subcommands)
    for key, arg_name in (
        ("word", "word_subcommand"),
        ("bit", "bit_subcommand"),
        ("ext_word", "ext_word_subcommand"),
        ("ext_bit", "ext_bit_subcommand"),
    ):
        value = getattr(args, arg_name)
        if value is not None:
            subcommands[key] = int(value)
    return Profile(
        name=profile.name,
        frame=args.frame or profile.frame,
        compat=args.compat or profile.compat,
        subcommands=subcommands,
    )


def profile_context(profile: Profile) -> dict[str, Any]:
    return {
        "profile": profile.name,
        "frame": profile.frame,
        "compat": profile.compat,
        "subcommands": {key: f"{value:04X}" for key, value in sorted(profile.subcommands.items())},
    }


def parse_device(device: str) -> tuple[str, int]:
    text = device.strip().upper()
    for code in sorted(DEVICE_CODES, key=lambda item: (-len(item), item)):
        if text.startswith(code):
            number_text = text[len(code) :]
            if not number_text:
                raise ValueError(f"missing device number: {device!r}")
            _, radix = DEVICE_CODES[code]
            return code, int(number_text, radix)
    raise ValueError(f"unsupported device: {device!r}")


def format_device(code: str, number: int) -> str:
    _, radix = DEVICE_CODES[code]
    if radix == 16:
        return f"{code}{number:X}"
    return f"{code}{number}"


def parse_extended_device(device: str) -> tuple[str, int, int, int]:
    text = device.strip().upper()
    extension_specification = 0
    direct_memory = 0x00
    if "\\" in text or "/" in text:
        sep = "\\" if "\\" in text else "/"
        prefix, raw_device = text.split(sep, 1)
        if prefix.startswith("U"):
            extension_specification = int(prefix[1:], 16)
            code, number = parse_device(raw_device)
            if code == "G":
                direct_memory = 0xF8
            elif code == "HG":
                direct_memory = 0xFA
            return code, number, extension_specification, direct_memory
        if prefix.startswith("J"):
            extension_specification = int(prefix[1:], 16)
            code, number = parse_device(raw_device)
            direct_memory = 0xF9
            return code, number, extension_specification, direct_memory
        raise ValueError(f"unsupported extended device qualifier: {device!r}")
    code, number = parse_device(text)
    return code, number, extension_specification, direct_memory


def format_extended_device(template: str, offset: int) -> str:
    code, number, _, _ = parse_extended_device(template)
    text = template.strip().upper()
    if "\\" in text or "/" in text:
        sep = "\\" if "\\" in text else "/"
        prefix, _ = text.split(sep, 1)
        return f"{prefix}\\{format_device(code, number + offset)}"
    return format_device(code, number + offset)


def uses_ql_device_format(profile: Profile) -> bool:
    return profile.compat.strip().lower() in {"q/l", "ql", "q"}


def encode_device_spec(profile: Profile, device: str) -> bytes:
    code, number = parse_device(device)
    device_code, _ = DEVICE_CODES[code]
    if uses_ql_device_format(profile):
        if not 0 <= number <= 0xFFFFFF:
            raise ValueError(f"device number out of Q/L range: {device}")
        return number.to_bytes(3, "little") + bytes([device_code & 0xFF])
    return number.to_bytes(4, "little") + device_code.to_bytes(2, "little")


def encode_extended_device_spec(profile: Profile, device: str) -> bytes:
    code, number, extension_specification, direct_memory = parse_extended_device(device)
    device_code, _ = DEVICE_CODES[code]
    device = format_device(code, number)
    payload = bytearray()
    payload += b"\x00"  # device modification index
    payload += b"\x00"  # device modification flags
    payload += encode_device_spec(profile, device)
    payload += b"\x00"  # extension specification modification
    payload += b"\x00"  # reserved
    payload += extension_specification.to_bytes(2, "little")
    payload += direct_memory.to_bytes(1, "little")
    return bytes(payload)


def pack_bits(values: list[bool]) -> bytes:
    out = bytearray()
    for index in range(0, len(values), 2):
        first = 1 if values[index] else 0
        second = 1 if index + 1 < len(values) and values[index + 1] else 0
        out.append((first << 4) | second)
    return bytes(out)


def unpack_bits(data: bytes, count: int) -> list[bool]:
    result: list[bool] = []
    for byte in data:
        result.append(bool((byte >> 4) & 0x01))
        if len(result) >= count:
            break
        result.append(bool(byte & 0x01))
        if len(result) >= count:
            break
    return result


def pack_words(values: list[int]) -> bytes:
    return b"".join((value & 0xFFFF).to_bytes(2, "little") for value in values)


def unpack_words(data: bytes, count: int) -> list[int]:
    return [int.from_bytes(data[index : index + 2], "little") for index in range(0, min(len(data), count * 2), 2)]


def request_frame(
    profile: Profile,
    command: int,
    subcommand: int,
    data: bytes,
    *,
    serial: int,
    monitoring_timer: int,
    network: int,
    station: int,
    module_io: int,
    multidrop: int,
) -> bytes:
    body = monitoring_timer.to_bytes(2, "little") + command.to_bytes(2, "little")
    body += subcommand.to_bytes(2, "little") + data
    target = bytes([network & 0xFF, station & 0xFF]) + module_io.to_bytes(2, "little") + bytes([multidrop & 0xFF])
    frame = profile.frame.strip().upper()
    if frame == "3E":
        return b"\x50\x00" + target + len(body).to_bytes(2, "little") + body
    if frame == "4E":
        return (
            b"\x54\x00"
            + (serial & 0xFFFF).to_bytes(2, "little")
            + b"\x00\x00"
            + target
            + len(body).to_bytes(2, "little")
            + body
        )
    raise ValueError(f"unsupported frame: {profile.frame}")


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < size:
        chunk = sock.recv(size - len(chunks))
        if not chunk:
            raise ConnectionError("socket closed before full response")
        chunks.extend(chunk)
    return bytes(chunks)


def send_request(sock: socket.socket, profile: Profile, frame: bytes) -> Response:
    note(f"request sent ({len(frame)} bytes); waiting for response (timeout {sock.gettimeout()}s)")
    sock.sendall(frame)
    if profile.frame.strip().upper() == "3E":
        head = recv_exact(sock, 9)
        if head[:2] != b"\xd0\x00":
            raise ValueError(f"unexpected 3E response subheader: {head[:2].hex()}")
        length = int.from_bytes(head[7:9], "little")
        payload = recv_exact(sock, length)
    else:
        head = recv_exact(sock, 13)
        if head[:2] != b"\xd4\x00":
            raise ValueError(f"unexpected 4E response subheader: {head[:2].hex()}")
        length = int.from_bytes(head[11:13], "little")
        payload = recv_exact(sock, length)
    if len(payload) < 2:
        raise ValueError("response payload too short")
    return Response(end_code=int.from_bytes(payload[:2], "little"), data=payload[2:])


def note(message: str) -> None:
    """Progress line on stderr so a timeout wait is never silent. Keeps stdout JSON-only."""
    print(f"[probe] {message}", file=sys.stderr, flush=True)


def open_socket(args: argparse.Namespace) -> socket.socket:
    note(f"connecting to {args.host}:{args.port} (timeout {args.timeout}s)")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((args.host, args.port))
    return sock


def device_payload(profile: Profile, device: str, points: int, data: bytes = b"") -> bytes:
    return encode_device_spec(profile, device) + points.to_bytes(2, "little") + data


def extended_device_payload(profile: Profile, device: str, points: int, data: bytes = b"") -> bytes:
    return encode_extended_device_spec(profile, device) + points.to_bytes(2, "little") + data


def emit(result: dict[str, Any]) -> None:
    # Keep the one-line JSON contract writable on Windows consoles using a
    # legacy code page such as CP932. Consumers still recover the original
    # Unicode value when they parse the JSON escape sequence.
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))


def type_name_fields(data: bytes) -> dict[str, str]:
    """Split a type-name response into its fixed-width name and type code."""
    fields = {
        "raw_hex": data.hex(),
        "text": data[:16].rstrip(b"\x00 ").decode("ascii", errors="replace"),
    }
    if len(data) >= 18:
        fields["type_code_hex"] = data[16:18].hex()
    return fields


def generated_devices(template: str, count: int) -> list[str]:
    if count < 0 or count > 255:
        raise ValueError("random device count must be in 0..255")
    return [format_extended_device(template, offset) for offset in range(count)]


def generated_plain_devices(template: str, count: int) -> list[str]:
    if count < 0 or count > 255:
        raise ValueError("random device count must be in 0..255")
    code, number = parse_device(template)
    return [format_device(code, number + offset) for offset in range(count)]


def random_read_payload(profile: Profile, word_devices: list[str], dword_devices: list[str]) -> bytes:
    payload = bytearray([len(word_devices), len(dword_devices)])
    for device in word_devices:
        payload += encode_device_spec(profile, device)
    for device in dword_devices:
        payload += encode_device_spec(profile, device)
    return bytes(payload)


def random_read_ext_payload(profile: Profile, word_devices: list[str], dword_devices: list[str]) -> bytes:
    payload = bytearray([len(word_devices), len(dword_devices)])
    for device in word_devices:
        payload += encode_extended_device_spec(profile, device)
    for device in dword_devices:
        payload += encode_extended_device_spec(profile, device)
    return bytes(payload)


def random_write_words_payload(
    profile: Profile,
    word_devices: list[str],
    dword_devices: list[str],
    *,
    word_value: int,
    dword_value: int,
) -> bytes:
    payload = bytearray([len(word_devices), len(dword_devices)])
    for device in word_devices:
        payload += encode_device_spec(profile, device)
        payload += int(word_value).to_bytes(2, "little", signed=False)
    for device in dword_devices:
        payload += encode_device_spec(profile, device)
        payload += int(dword_value).to_bytes(4, "little", signed=False)
    return bytes(payload)


def random_write_words_ext_payload(
    profile: Profile,
    word_devices: list[str],
    dword_devices: list[str],
    *,
    word_value: int,
    dword_value: int,
) -> bytes:
    payload = bytearray([len(word_devices), len(dword_devices)])
    for device in word_devices:
        payload += encode_extended_device_spec(profile, device)
        payload += int(word_value).to_bytes(2, "little", signed=False)
    for device in dword_devices:
        payload += encode_extended_device_spec(profile, device)
        payload += int(dword_value).to_bytes(4, "little", signed=False)
    return bytes(payload)


def random_write_bits_payload(profile: Profile, devices: list[str], value: bool) -> bytes:
    bit_data = b"\x01\x00" if value and not uses_ql_device_format(profile) else b"\x01" if value else b"\x00\x00" if not uses_ql_device_format(profile) else b"\x00"
    payload = bytearray([len(devices)])
    for device in devices:
        payload += encode_device_spec(profile, device)
        payload += bit_data
    return bytes(payload)


def random_write_bits_ext_payload(profile: Profile, devices: list[str], value: bool) -> bytes:
    bit_data = b"\x01\x00" if value and not uses_ql_device_format(profile) else b"\x01" if value else b"\x00\x00" if not uses_ql_device_format(profile) else b"\x00"
    payload = bytearray([len(devices)])
    for device in devices:
        payload += encode_extended_device_spec(profile, device)
        payload += bit_data
    return bytes(payload)


def block_access_payload(
    profile: Profile,
    *,
    word_device: str | None,
    word_points: int,
    bit_device: str | None,
    bit_points: int,
    word_data: bytes = b"",
    bit_data: bytes = b"",
) -> bytes:
    word_blocks = 1 if word_device else 0
    bit_blocks = 1 if bit_device else 0
    payload = bytearray([word_blocks, bit_blocks])
    if word_device:
        payload += encode_device_spec(profile, word_device)
        payload += word_points.to_bytes(2, "little")
        payload += word_data
    if bit_device:
        payload += encode_device_spec(profile, bit_device)
        payload += bit_points.to_bytes(2, "little")
        payload += bit_data
    return bytes(payload)


def run_read_random_ext(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_READ_RANDOM,
            profile.subcommands["ext_word"],
            random_read_ext_payload(profile, word_devices, dword_devices),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "read-random-ext",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    emit(result)


def run_read_random(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_plain_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_plain_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_READ_RANDOM,
            profile.subcommands["word"],
            random_read_payload(profile, word_devices, dword_devices),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "read-random",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    emit(result)


def run_write_random_words(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_plain_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_plain_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE_RANDOM,
            profile.subcommands["word"],
            random_write_words_payload(
                profile,
                word_devices,
                dword_devices,
                word_value=args.word_value,
                dword_value=args.dword_value,
            ),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result = {
        **profile_context(profile),
        "operation": "write-random-words",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "word_value": int(args.word_value),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "dword_value": int(args.dword_value),
        "end_code": f"{response.end_code:04X}",
    }
    emit(result)


def run_write_random_words_ext(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE_RANDOM,
            profile.subcommands["ext_word"],
            random_write_words_ext_payload(
                profile,
                word_devices,
                dword_devices,
                word_value=args.word_value,
                dword_value=args.dword_value,
            ),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result = {
        **profile_context(profile),
        "operation": "write-random-words-ext",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "word_value": int(args.word_value),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "dword_value": int(args.dword_value),
        "end_code": f"{response.end_code:04X}",
    }
    emit(result)


def run_write_random_bits_ext(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    devices = generated_devices(args.device, args.count)
    reset_response: Response | None = None
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE_RANDOM,
            profile.subcommands["ext_bit"],
            random_write_bits_ext_payload(profile, devices, bool(args.value)),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
        if args.reset and response.end_code == 0:
            reset_frame = request_frame(
                profile,
                COMMAND_DEVICE_WRITE_RANDOM,
                profile.subcommands["ext_bit"],
                random_write_bits_ext_payload(profile, devices, False),
                serial=2,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            reset_response = send_request(sock, profile, reset_frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "write-random-bits-ext",
        "device": args.device,
        "count": len(devices),
        "value": bool(args.value),
        "end_code": f"{response.end_code:04X}",
    }
    if reset_response is not None:
        result["reset_end"] = f"{reset_response.end_code:04X}"
    emit(result)


def run_write_random_bits(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    devices = generated_plain_devices(args.device, args.count)
    reset_response: Response | None = None
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE_RANDOM,
            profile.subcommands["bit"],
            random_write_bits_payload(profile, devices, bool(args.value)),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
        if args.reset and response.end_code == 0:
            reset_frame = request_frame(
                profile,
                COMMAND_DEVICE_WRITE_RANDOM,
                profile.subcommands["bit"],
                random_write_bits_payload(profile, devices, False),
                serial=2,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            reset_response = send_request(sock, profile, reset_frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "write-random-bits",
        "device": args.device,
        "count": len(devices),
        "value": bool(args.value),
        "end_code": f"{response.end_code:04X}",
    }
    if reset_response is not None:
        result["reset_end"] = f"{reset_response.end_code:04X}"
    emit(result)


def run_register_monitor_ext(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_ENTRY_MONITOR,
            profile.subcommands["ext_word"],
            random_read_ext_payload(profile, word_devices, dword_devices),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "register-monitor-ext",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    emit(result)


def run_register_monitor(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_plain_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_plain_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_ENTRY_MONITOR,
            profile.subcommands["word"],
            random_read_payload(profile, word_devices, dword_devices),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "register-monitor",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    emit(result)


def run_monitor(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_devices = generated_plain_devices(args.word_device, args.word_count) if args.word_device else []
    dword_devices = generated_plain_devices(args.dword_device, args.dword_count) if args.dword_device else []
    with open_socket(args) as sock:
        register_frame = request_frame(
            profile,
            COMMAND_DEVICE_ENTRY_MONITOR,
            profile.subcommands["word"],
            random_read_payload(profile, word_devices, dword_devices),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        register_response = send_request(sock, profile, register_frame)
        monitor_response: Response | None = None
        if register_response.end_code == 0:
            monitor_frame = request_frame(
                profile,
                COMMAND_DEVICE_EXECUTE_MONITOR,
                profile.subcommands["word"],
                b"",
                serial=2,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            monitor_response = send_request(sock, profile, monitor_frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "monitor",
        "word_device": args.word_device,
        "word_count": len(word_devices),
        "dword_device": args.dword_device,
        "dword_count": len(dword_devices),
        "register_end": f"{register_response.end_code:04X}",
    }
    if monitor_response is not None:
        result["monitor_end"] = f"{monitor_response.end_code:04X}"
        result["monitor_data_bytes"] = len(monitor_response.data)
    emit(result)


def run_read_block(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_READ_BLOCK,
            profile.subcommands["word"],
            block_access_payload(
                profile,
                word_device=args.word_device,
                word_points=args.word_points,
                bit_device=args.bit_device,
                bit_points=args.bit_points,
            ),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "read-block",
        "word_device": args.word_device,
        "word_points": args.word_points if args.word_device else 0,
        "bit_device": args.bit_device,
        "bit_points": args.bit_points if args.bit_device else 0,
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    emit(result)


def run_write_block(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    word_data = pack_words([args.word_value] * args.word_points) if args.word_device else b""
    bit_word_value = 0xFFFF if bool(args.bit_value) else 0x0000
    bit_data = pack_words([bit_word_value] * args.bit_points) if args.bit_device else b""
    reset_response: Response | None = None
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE_BLOCK,
            profile.subcommands["word"],
            block_access_payload(
                profile,
                word_device=args.word_device,
                word_points=args.word_points,
                bit_device=args.bit_device,
                bit_points=args.bit_points,
                word_data=word_data,
                bit_data=bit_data,
            ),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
        if args.reset_bits and args.bit_device and response.end_code == 0:
            reset_frame = request_frame(
                profile,
                COMMAND_DEVICE_WRITE_BLOCK,
                profile.subcommands["word"],
                block_access_payload(
                    profile,
                    word_device=None,
                    word_points=0,
                    bit_device=args.bit_device,
                    bit_points=args.bit_points,
                    bit_data=pack_words([0] * args.bit_points),
                ),
                serial=2,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            reset_response = send_request(sock, profile, reset_frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "write-block",
        "word_device": args.word_device,
        "word_points": args.word_points if args.word_device else 0,
        "word_value": args.word_value if args.word_device else None,
        "bit_device": args.bit_device,
        "bit_points": args.bit_points if args.bit_device else 0,
        "bit_value": bool(args.bit_value) if args.bit_device else None,
        "end_code": f"{response.end_code:04X}",
    }
    if reset_response is not None:
        result["reset_end"] = f"{reset_response.end_code:04X}"
    emit(result)


def run_read(args: argparse.Namespace, *, bit: bool) -> None:
    profile = load_probe_profile(args)
    subcommand = profile.subcommands["bit" if bit else "word"]
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_READ,
            subcommand,
            device_payload(profile, args.device, args.points),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "read-bit" if bit else "read-word",
        "device": args.device,
        "points": args.points,
        "end_code": f"{response.end_code:04X}",
    }
    if response.end_code == 0:
        result["values"] = unpack_bits(response.data, args.points) if bit else unpack_words(response.data, args.points)
    emit(result)


def run_read_ext(args: argparse.Namespace, *, bit: bool) -> None:
    profile = load_probe_profile(args)
    subcommand = profile.subcommands["ext_bit" if bit else "ext_word"]
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_DEVICE_READ,
            subcommand,
            extended_device_payload(profile, args.device, args.points),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "read-ext-bit" if bit else "read-ext-word",
        "device": args.device,
        "points": args.points,
        "end_code": f"{response.end_code:04X}",
        "data_bytes": len(response.data),
    }
    if response.end_code == 0:
        result["values"] = unpack_bits(response.data, args.points) if bit else unpack_words(response.data, args.points)
    emit(result)


def run_write(args: argparse.Namespace, *, bit: bool) -> None:
    profile = load_probe_profile(args)
    subcommand = profile.subcommands["bit" if bit else "word"]
    points = int(getattr(args, "points", 1))
    values = [bool(args.value)] * points if bit else [int(args.value)] * points
    data = pack_bits(values) if bit else pack_words(values)
    read_subcommand = profile.subcommands["bit" if bit else "word"]
    with open_socket(args) as sock:
        write_frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE,
            subcommand,
            device_payload(profile, args.device, points, data),
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        write_response = send_request(sock, profile, write_frame)
        read_frame = request_frame(
            profile,
            COMMAND_DEVICE_READ,
            read_subcommand,
            device_payload(profile, args.device, points),
            serial=2,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        read_response = send_request(sock, profile, read_frame)
        reset_response: Response | None = None
        final_response: Response | None = None
        if bit and args.reset:
            reset_frame = request_frame(
                profile,
                COMMAND_DEVICE_WRITE,
                subcommand,
                device_payload(profile, args.device, points, pack_bits([False] * points)),
                serial=3,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            reset_response = send_request(sock, profile, reset_frame)
            final_frame = request_frame(
                profile,
                COMMAND_DEVICE_READ,
                read_subcommand,
                device_payload(profile, args.device, points),
                serial=4,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            final_response = send_request(sock, profile, final_frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "write-bit" if bit else "write-word",
        "device": args.device,
        "points": points,
        "value": bool(args.value) if bit else int(args.value),
        "write_end": f"{write_response.end_code:04X}",
        "read_end": f"{read_response.end_code:04X}",
    }
    if read_response.end_code == 0:
        read_values = unpack_bits(read_response.data, points) if bit else unpack_words(read_response.data, points)
        result["read_count"] = len(read_values)
        if len(read_values) == 1:
            result["read_value"] = read_values[0]
    if reset_response is not None:
        result["reset_end"] = f"{reset_response.end_code:04X}"
    if final_response is not None:
        result["final_read_end"] = f"{final_response.end_code:04X}"
        if final_response.end_code == 0:
            final_values = unpack_bits(final_response.data, points)
            result["final_count"] = len(final_values)
            if len(final_values) == 1:
                result["final_value"] = final_values[0]
    emit(result)


def run_type_name(args: argparse.Namespace) -> None:
    profile = load_probe_profile(args)
    with open_socket(args) as sock:
        frame = request_frame(
            profile,
            COMMAND_TYPE_NAME,
            0x0000,
            b"",
            serial=1,
            monitoring_timer=args.monitoring_timer,
            network=args.network,
            station=args.station,
            module_io=args.module_io,
            multidrop=args.multidrop,
        )
        response = send_request(sock, profile, frame)
    result: dict[str, Any] = {
        **profile_context(profile),
        "operation": "type-name",
        "end_code": f"{response.end_code:04X}",
    }
    if response.end_code == 0:
        result.update(type_name_fields(response.data))
    emit(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Raw SLMP live probe for profile evidence.")
    parser.add_argument("--host", default="192.168.250.100")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--frame", choices=["3E", "4E"], help="Temporarily override the profile frame for probing.")
    parser.add_argument("--compat", help="Temporarily override the profile compatibility/device encoding mode.")
    parser.add_argument("--word-subcommand", type=parse_u16_hex, help="Temporarily override the word subcommand.")
    parser.add_argument("--bit-subcommand", type=parse_u16_hex, help="Temporarily override the bit subcommand.")
    parser.add_argument("--ext-word-subcommand", type=parse_u16_hex, help="Temporarily override the extended word subcommand.")
    parser.add_argument("--ext-bit-subcommand", type=parse_u16_hex, help="Temporarily override the extended bit subcommand.")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--network", type=lambda value: int(value, 0), default=0x00)
    parser.add_argument("--station", type=lambda value: int(value, 0), default=0xFF)
    parser.add_argument("--module-io", type=lambda value: int(value, 0), default=0x03FF)
    parser.add_argument("--multidrop", type=lambda value: int(value, 0), default=0x00)
    parser.add_argument("--monitoring-timer", type=lambda value: int(value, 0), default=0x0010)
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name, bit in (("read-bit", True), ("read-word", False)):
        sub = subparsers.add_parser(name)
        sub.add_argument("--device", required=True)
        sub.add_argument("--points", type=int, default=1)
        sub.set_defaults(func=lambda args, bit=bit: run_read(args, bit=bit))

    for name, bit in (("read-ext-bit", True), ("read-ext-word", False)):
        sub = subparsers.add_parser(name)
        sub.add_argument("--device", required=True)
        sub.add_argument("--points", type=int, default=1)
        sub.set_defaults(func=lambda args, bit=bit: run_read_ext(args, bit=bit))

    for name, bit in (("write-bit", True), ("write-word", False)):
        sub = subparsers.add_parser(name)
        sub.add_argument("--device", required=True)
        sub.add_argument("--points", type=int, default=1)
        sub.add_argument("--value", type=int, required=True)
        if bit:
            sub.add_argument("--reset", action="store_true", help="Reset the tested bit OFF and read it back.")
        sub.set_defaults(func=lambda args, bit=bit: run_write(args, bit=bit))

    sub = subparsers.add_parser("read-random")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.set_defaults(func=run_read_random)

    sub = subparsers.add_parser("write-random-words")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--word-value", type=lambda value: int(value, 0), default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.add_argument("--dword-value", type=lambda value: int(value, 0), default=0)
    sub.set_defaults(func=run_write_random_words)

    sub = subparsers.add_parser("write-random-bits")
    sub.add_argument("--device", required=True)
    sub.add_argument("--count", type=int, required=True)
    sub.add_argument("--value", type=lambda value: int(value, 0), required=True)
    sub.add_argument("--reset", action="store_true", help="Reset the tested bits OFF after a successful write.")
    sub.set_defaults(func=run_write_random_bits)

    sub = subparsers.add_parser("read-random-ext")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.set_defaults(func=run_read_random_ext)

    sub = subparsers.add_parser("write-random-words-ext")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--word-value", type=lambda value: int(value, 0), default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.add_argument("--dword-value", type=lambda value: int(value, 0), default=0)
    sub.set_defaults(func=run_write_random_words_ext)

    sub = subparsers.add_parser("write-random-bits-ext")
    sub.add_argument("--device", required=True)
    sub.add_argument("--count", type=int, required=True)
    sub.add_argument("--value", type=lambda value: int(value, 0), required=True)
    sub.add_argument("--reset", action="store_true", help="Reset the tested bits OFF after a successful write.")
    sub.set_defaults(func=run_write_random_bits_ext)

    sub = subparsers.add_parser("register-monitor-ext")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.set_defaults(func=run_register_monitor_ext)

    sub = subparsers.add_parser("register-monitor")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.set_defaults(func=run_register_monitor)

    sub = subparsers.add_parser("monitor")
    sub.add_argument("--word-device")
    sub.add_argument("--word-count", type=int, default=0)
    sub.add_argument("--dword-device")
    sub.add_argument("--dword-count", type=int, default=0)
    sub.set_defaults(func=run_monitor)

    sub = subparsers.add_parser("read-block")
    sub.add_argument("--word-device")
    sub.add_argument("--word-points", type=int, default=0)
    sub.add_argument("--bit-device")
    sub.add_argument("--bit-points", type=int, default=0)
    sub.set_defaults(func=run_read_block)

    sub = subparsers.add_parser("write-block")
    sub.add_argument("--word-device")
    sub.add_argument("--word-points", type=int, default=0)
    sub.add_argument("--word-value", type=lambda value: int(value, 0), default=0)
    sub.add_argument("--bit-device")
    sub.add_argument("--bit-points", type=int, default=0)
    sub.add_argument("--bit-value", type=lambda value: int(value, 0), default=0)
    sub.add_argument("--reset-bits", action="store_true", help="Reset the tested bit block OFF after a successful write.")
    sub.set_defaults(func=run_write_block)

    sub = subparsers.add_parser("type-name")
    sub.set_defaults(func=run_type_name)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001 -- probe contract: always emit one JSON line, even on failure
        emit(
            {
                "operation": args.command,
                "host": args.host,
                "port": args.port,
                "profile": args.profile,
                "error": type(exc).__name__,
                "detail": str(exc) or type(exc).__name__,
            }
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
