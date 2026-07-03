#!/usr/bin/env python3
"""Raw SLMP live probe for profile evidence.

This tool is intentionally small and transport-level. It reads the canonical
profile JSON for frame/compat/subcommand choices, sends raw SLMP requests, and
prints concise JSON results. It does not apply client-library guards.
"""

from __future__ import annotations

import argparse
import json
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_JSON = ROOT / "capability" / "slmp_builtin_ethernet_profiles.json"


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


def load_profile(name: str) -> Profile:
    with CAPABILITY_JSON.open("r", encoding="utf-8") as fh:
        root = json.load(fh)
    raw = root["profiles"][name]
    return Profile(
        name=name,
        frame=str(raw["frame"]),
        compat=str(raw["compat"]),
        subcommands={key: int(value, 16) for key, value in raw["subcommands"].items()},
    )


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
    sock.sendall(frame)
    if profile.frame.strip().upper() == "3E":
        head = recv_exact(sock, 9)
        length = int.from_bytes(head[7:9], "little")
        payload = recv_exact(sock, length)
    else:
        head = recv_exact(sock, 13)
        length = int.from_bytes(head[11:13], "little")
        payload = recv_exact(sock, length)
    if len(payload) < 2:
        raise ValueError("response payload too short")
    return Response(end_code=int.from_bytes(payload[:2], "little"), data=payload[2:])


def open_socket(args: argparse.Namespace) -> socket.socket:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(args.timeout)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    sock.connect((args.host, args.port))
    return sock


def device_payload(profile: Profile, device: str, points: int, data: bytes = b"") -> bytes:
    return encode_device_spec(profile, device) + points.to_bytes(2, "little") + data


def emit(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


def run_read(args: argparse.Namespace, *, bit: bool) -> None:
    profile = load_profile(args.profile)
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
        "profile": profile.name,
        "operation": "read-bit" if bit else "read-word",
        "device": args.device,
        "points": args.points,
        "end_code": f"{response.end_code:04X}",
    }
    if response.end_code == 0:
        result["values"] = unpack_bits(response.data, args.points) if bit else unpack_words(response.data, args.points)
    emit(result)


def run_write(args: argparse.Namespace, *, bit: bool) -> None:
    profile = load_profile(args.profile)
    subcommand = profile.subcommands["bit" if bit else "word"]
    values = [bool(args.value)] if bit else [int(args.value)]
    data = pack_bits(values) if bit else pack_words(values)
    read_subcommand = profile.subcommands["bit" if bit else "word"]
    with open_socket(args) as sock:
        write_frame = request_frame(
            profile,
            COMMAND_DEVICE_WRITE,
            subcommand,
            device_payload(profile, args.device, 1, data),
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
            device_payload(profile, args.device, 1),
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
                device_payload(profile, args.device, 1, pack_bits([False])),
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
                device_payload(profile, args.device, 1),
                serial=4,
                monitoring_timer=args.monitoring_timer,
                network=args.network,
                station=args.station,
                module_io=args.module_io,
                multidrop=args.multidrop,
            )
            final_response = send_request(sock, profile, final_frame)
    result: dict[str, Any] = {
        "profile": profile.name,
        "operation": "write-bit" if bit else "write-word",
        "device": args.device,
        "value": bool(args.value) if bit else int(args.value),
        "write_end": f"{write_response.end_code:04X}",
        "read_end": f"{read_response.end_code:04X}",
    }
    if read_response.end_code == 0:
        result["read_value"] = unpack_bits(read_response.data, 1)[0] if bit else unpack_words(read_response.data, 1)[0]
    if reset_response is not None:
        result["reset_end"] = f"{reset_response.end_code:04X}"
    if final_response is not None:
        result["final_read_end"] = f"{final_response.end_code:04X}"
        if final_response.end_code == 0:
            result["final_value"] = unpack_bits(final_response.data, 1)[0]
    emit(result)


def run_type_name(args: argparse.Namespace) -> None:
    profile = load_profile(args.profile)
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
        "profile": profile.name,
        "operation": "type-name",
        "end_code": f"{response.end_code:04X}",
    }
    if response.end_code == 0:
        result["raw_hex"] = response.data.hex()
        result["text"] = response.data.rstrip(b"\x00 ").decode("ascii", errors="replace")
    emit(result)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Raw SLMP live probe for profile evidence.")
    parser.add_argument("--host", default="192.168.250.100")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--profile", required=True)
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

    for name, bit in (("write-bit", True), ("write-word", False)):
        sub = subparsers.add_parser(name)
        sub.add_argument("--device", required=True)
        sub.add_argument("--value", type=int, required=True)
        if bit:
            sub.add_argument("--reset", action="store_true", help="Reset the tested bit OFF and read it back.")
        sub.set_defaults(func=lambda args, bit=bit: run_write(args, bit=bit))

    sub = subparsers.add_parser("type-name")
    sub.set_defaults(func=run_type_name)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
