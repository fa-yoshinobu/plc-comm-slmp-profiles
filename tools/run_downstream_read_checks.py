#!/usr/bin/env python3
"""Plan or run downstream read-only unit-profile checks.

Default mode is dry-run and prints the commands only. Live PLC communication
requires both --execute and --approved-live-ok, after the user has confirmed
the connected PLC and approved the exact batch.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


TOOLS_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE_ROOT = TOOLS_DIR.parents[1]

UNIT_PROFILES = {
    "melsec:iq-r:rj71en71": "R120PCPU + RJ71EN71",
    "melsec:mx-r:rj71en71": "MXR300-32 + RJ71EN71",
    "melsec:qcpu:qj71e71-100": "Q12HCPU + QJ71E71-100",
    "melsec:qnu:qj71e71-100": "Q26UDEHCPU + QJ71E71-100",
    "melsec:qnudv:qj71e71-100": "Q06UDVCPU + QJ71E71-100",
    "melsec:lcpu:lj71e71-100": "L02SCPU + LJ71E71-100",
}


@dataclass(frozen=True)
class CheckCommand:
    name: str
    repo: str
    command: list[str]
    workdir: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan or run downstream unit-profile read-only checks.")
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--host", default="192.168.250.100")
    parser.add_argument("--port", type=int, default=1025)
    parser.add_argument("--profile", required=True, choices=sorted(UNIT_PROFILES))
    parser.add_argument("--device", default="D1000")
    parser.add_argument("--execute", action="store_true", help="Run the commands instead of printing them.")
    parser.add_argument(
        "--approved-live-ok",
        action="store_true",
        help="Required with --execute after the user has approved this live PLC batch.",
    )
    parser.add_argument("--cpp-compiler", default="g++")
    return parser.parse_args()


def quote_command(command: list[str]) -> str:
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    import shlex

    return " ".join(shlex.quote(part) for part in command)


def node_script(host: str, port: int, profile: str, device: str) -> str:
    return (
        "const {SlmpClient}=require('./lib/slmp'); "
        "(async()=>{"
        f"const c=new SlmpClient({{host:{json.dumps(host)},port:{port},transport:'tcp',plcProfile:{json.dumps(profile)}}}); "
        "await c.connect(); "
        "try { "
        f"const v=await c.readDevices({json.dumps(device)},1,{{bitUnit:false}}); "
        "console.log(JSON.stringify({status:'success',values:v,plcProfile:c.plcProfile,frameType:c.frameType,plcSeries:c.plcSeries})); "
        "} finally { await c.close(); }"
        "})().catch(e=>{console.error(e); process.exit(1);});"
    )


def build_commands(args: argparse.Namespace) -> list[CheckCommand]:
    root = args.source_root.resolve()
    port = str(args.port)
    cpp_exe = str(Path(tempfile.gettempdir()) / ("slmp_live_read_once.exe" if os.name == "nt" else "slmp_live_read_once"))

    cpp_build = [
        args.cpp_compiler,
        "-std=c++17",
        "-Wall",
        "-Wextra",
        "-Isrc",
        "tests/slmp_live_read_once.cpp",
        "src/slmp_minimal.cpp",
        "src/slmp_error_codes.cpp",
        "src/slmp_high_level.cpp",
        "-o",
        cpp_exe,
    ]
    if os.name == "nt":
        cpp_build.append("-lws2_32")

    return [
        CheckCommand(
            ".NET",
            "plc-comm-slmp-dotnet",
            [
                "dotnet",
                "run",
                "--project",
                "samples/PlcComm.Slmp.Cli",
                "--",
                "read-soak",
                "--host",
                args.host,
                "--port",
                port,
                "--transport",
                "tcp",
                "--plc-profile",
                args.profile,
                "--device",
                args.device,
                "--points",
                "1",
                "--iterations",
                "1",
                "--quiet",
            ],
            root / "plc-comm-slmp-dotnet",
        ),
        CheckCommand(
            "Python",
            "plc-comm-slmp-python",
            [
                "python",
                "samples/02_device_reads.py",
                "--host",
                args.host,
                "--port",
                port,
                "--transport",
                "tcp",
                "--plc-profile",
                args.profile,
                "--word-device",
                args.device,
                "--word-points",
                "1",
                "--bit-points",
                "0",
            ],
            root / "plc-comm-slmp-python",
        ),
        CheckCommand(
            "Rust",
            "plc-comm-slmp-rust",
            [
                "cargo",
                "run",
                "--features",
                "cli",
                "--bin",
                "slmp_verify_client",
                "--",
                args.host,
                port,
                "read",
                args.device,
                "1",
                "--plc-profile",
                args.profile,
            ],
            root / "plc-comm-slmp-rust",
        ),
        CheckCommand(
            "Node-RED",
            "node-red-contrib-plc-comm-slmp",
            ["node", "-e", node_script(args.host, args.port, args.profile, args.device)],
            root / "node-red-contrib-plc-comm-slmp",
        ),
        CheckCommand(
            "C++ minimal build",
            "plc-comm-slmp-cpp-minimal",
            cpp_build,
            root / "plc-comm-slmp-cpp-minimal",
        ),
        CheckCommand(
            "C++ minimal read",
            "plc-comm-slmp-cpp-minimal",
            [cpp_exe, args.host, port, args.profile, args.device],
            root / "plc-comm-slmp-cpp-minimal",
        ),
    ]


def validate_commands(commands: list[CheckCommand]) -> list[str]:
    problems: list[str] = []
    for item in commands:
        if not item.workdir.is_dir():
            problems.append(f"{item.name}: missing repo directory {item.workdir}")
    return problems


def print_plan(args: argparse.Namespace, commands: list[CheckCommand]) -> None:
    print("downstream read-only unit-profile check plan")
    print(f"target: {UNIT_PROFILES[args.profile]}")
    print(f"profile: {args.profile}")
    print(f"endpoint: {args.host}:{args.port} TCP")
    print(f"read: {args.device}, 1 word")
    print("intent: read-only downstream implementation acceptance")
    print("")
    for item in commands:
        print(f"[{item.name}] cwd={item.workdir}")
        print(quote_command(item.command))
        print("")


def run_commands(args: argparse.Namespace, commands: list[CheckCommand]) -> int:
    failures = 0
    for item in commands:
        print(f"== {item.name} ==")
        print(f"cwd: {item.workdir}")
        print(quote_command(item.command))
        completed = subprocess.run(item.command, cwd=item.workdir, check=False, capture_output=True, text=True)
        if completed.stdout:
            print(completed.stdout, end="" if completed.stdout.endswith("\n") else "\n")
        if completed.stderr:
            print(completed.stderr, end="" if completed.stderr.endswith("\n") else "\n", file=sys.stderr)
        if completed.returncode != 0:
            failures += 1
            print(f"{item.name}: FAIL exit={completed.returncode}", file=sys.stderr)
        else:
            print(f"{item.name}: PASS")
    return 0 if failures == 0 else 1


def main() -> int:
    args = parse_args()
    commands = build_commands(args)
    problems = validate_commands(commands)
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        return 2

    if not args.execute:
        print_plan(args, commands)
        print("dry-run only; no PLC communication was attempted.")
        return 0

    if not args.approved_live_ok:
        print("--execute requires --approved-live-ok after user approval for this live PLC batch.", file=sys.stderr)
        return 2

    return run_commands(args, commands)


if __name__ == "__main__":
    raise SystemExit(main())
