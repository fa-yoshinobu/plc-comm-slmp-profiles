#!/usr/bin/env python3
"""Generate a live PLC verification checklist draft for one SLMP profile."""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_JSON = ROOT / "capability" / "slmp_builtin_ethernet_profiles.json"
DEVICE_RANGE_JSON = ROOT / "device-ranges" / "slmp_device_range_rules.json"

PROFILE_SLUGS = {
    "melsec:iq-r": "iq-r",
    "melsec:iq-l": "iq-l",
    "melsec:mx-r": "mx-r",
    "melsec:mx-f": "mx-f",
    "melsec:iq-f": "iq-f",
    "melsec:qcpu": "qcpu",
    "melsec:lcpu": "lcpu",
    "melsec:qnu": "qnu",
    "melsec:qnudv": "qnudv",
}

PROFILE_TITLES = {
    "melsec:iq-r": "iQ-R",
    "melsec:iq-l": "iQ-L",
    "melsec:mx-r": "MX-R",
    "melsec:mx-f": "MX-F",
    "melsec:iq-f": "iQ-F",
    "melsec:qcpu": "QCPU",
    "melsec:lcpu": "LCPU",
    "melsec:qnu": "QnU",
    "melsec:qnudv": "QnUDV",
}

FEATURE_ROWS = [
    ("Type name", "type_name", "-"),
    ("Direct read/write", "direct", ""),
    ("Random read/write", "random", ""),
    ("Block read/write", "block", ""),
    ("Monitor", "monitor", ""),
    ("Long timer/counter route", "long_device_path", ""),
    ("LZ 32-bit route", "lz_32bit_path", ""),
]

QUALIFIED_ROWS = [
    (
        "`J...\\...` link direct",
        "ext_link_direct",
        "",
        "Configuration-dependent when link hardware is absent",
    ),
    (
        "`U...\\G...` module buffer",
        "ext_module_access",
        "",
        "Unit/address availability is configuration-dependent",
    ),
    ("`U3E0\\HG...` CPU buffer", "hg_cpu_buffer", "", "iQ-R-only route"),
]

LIMIT_ROWS = [
    ("Direct word read", "direct_word_read"),
    ("Direct word write", "direct_word_write"),
    ("Direct bit read", "direct_bit_read"),
    ("Direct bit write", "direct_bit_write"),
    ("Random word read", "random_read_word"),
    ("Random word write count", "random_write_word"),
    ("Random word write weighted", "random_write_word"),
    ("Random bit write", "random_write_bit"),
    ("Monitor word register", "monitor_register_word"),
    ("Extended random word read", "random_read_word_ext"),
    ("Extended random word write count", "random_write_word_ext"),
    ("Extended random word write weighted", "random_write_word_ext"),
    ("Extended random bit write", "random_write_bit_ext"),
    ("Extended monitor word register", "monitor_register_word_ext"),
]

DEVICE_FAMILY_NOTES = {
    "S": "Existence/access only; write policy is separate",
    "LZ": "32-bit route only",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def md_escape(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", "<br>")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    return "\n".join(lines)


def profile_title(profile_id: str) -> str:
    return PROFILE_TITLES.get(profile_id, profile_id.replace("melsec:", ""))


def default_output(profile_id: str, run_date: str) -> Path:
    slug = PROFILE_SLUGS.get(profile_id, profile_id.replace("melsec:", "").replace(":", "-"))
    return ROOT / "evidence" / f"{slug}_slmp_live_verify_{run_date.replace('-', '')}.md"


def feature_expectation(feature: dict[str, Any] | None) -> str:
    if not feature:
        return ""
    state = feature.get("state", "")
    source = feature.get("source", "")
    return f"{state} / {source}" if source else str(state)


def limit_value(limit: dict[str, Any] | None, *, weighted_only: bool = False) -> str:
    if not limit:
        return ""
    parts: list[str] = []
    if weighted_only:
        if "weighted_max" in limit:
            parts.append(f"weighted max {limit['weighted_max']}")
        else:
            parts.append("weighted max not defined")
    elif "max" in limit:
        parts.append(f"max {limit['max']}")
    if "over_end_code" in limit:
        parts.append(f"over `{limit['over_end_code']}`")
    source = limit.get("source")
    if source:
        parts.append(f"source {source}")
    return ", ".join(parts)


def range_rule_cell(rule: dict[str, Any] | None) -> str:
    if not rule:
        return ""
    kind = rule.get("kind", "")
    display_kind = {
        "word-register": "word",
        "dword-register": "dword",
        "word-register-clipped": "word-clipped",
        "dword-register-clipped": "dword-clipped",
    }.get(kind, kind)
    if kind == "fixed":
        return f"fixed={rule.get('fixed_value', '')}"
    if kind in {"unsupported", "undefined"}:
        return display_kind
    register = rule.get("register")
    parts = [display_kind]
    if register is not None:
        parts.append(f"source=SD{register}")
    if "clip_value" in rule:
        parts.append(f"clip={rule['clip_value']}")
    if rule.get("probe"):
        parts.append("probe")
    return "; ".join(parts)


def devices_cell(row: dict[str, Any] | None) -> str:
    if not row:
        return ""
    return " / ".join(device.get("device", "") for device in row.get("devices", []))


def render(args: argparse.Namespace) -> str:
    capability = load_json(CAPABILITY_JSON)
    device_ranges = load_json(DEVICE_RANGE_JSON)
    profiles = capability["profiles"]
    if args.profile not in profiles:
        raise SystemExit(f"unknown profile: {args.profile}")
    profile = profiles[args.profile]
    range_profile = device_ranges["profiles"].get(args.profile, {})
    range_rules = range_profile.get("rules", {})

    session_rows = [
        ["Date", args.date],
        ["PLC model", args.plc_model],
        ["PLC profile", f"`{args.profile}`"],
        ["Endpoint", args.endpoint],
        ["Source JSON", "`capability/slmp_builtin_ethernet_profiles.json`"],
        ["Device range JSON", "`device-ranges/slmp_device_range_rules.json`"],
        ["Notes", args.notes],
    ]

    feature_rows: list[list[Any]] = []
    for label, key, target in FEATURE_ROWS:
        feature_rows.append(
            [
                label,
                feature_expectation(profile.get("features", {}).get(key)),
                target,
                "unverified",
                "",
            ]
        )

    qualified_rows: list[list[Any]] = []
    for route, key, target, note in QUALIFIED_ROWS:
        qualified_rows.append(
            [
                route,
                feature_expectation(profile.get("features", {}).get(key)),
                target,
                "unverified",
                note,
            ]
        )
    qualified_rows.extend(
        [
            ["Standalone `G`", "common rule", "-", "spec", "Not a standalone device route"],
            ["Standalone `HG`", "common rule", "-", "spec", "Not a standalone device route"],
        ]
    )

    limit_rows: list[list[Any]] = []
    for label, key in LIMIT_ROWS:
        weighted_only = label in {"Random word write weighted", "Extended random word write weighted"}
        note = ""
        if label in {"Random word write count", "Extended random word write count", "Extended random word read"}:
            note = "Record pass at max and fail at max+1"
        elif label == "Random word write weighted":
            note = "Required when weighted max exists; total point count must remain within max"
        elif label == "Extended random word write weighted":
            note = "Required when ext weighted max exists; total point count must remain within ext max"
        elif label == "Extended random bit write":
            note = "Bit probes must reset tested bits OFF"
        elif label == "Extended monitor word register":
            note = "Record whether the ext monitor path is adopted as a limit source"
        limit_rows.append(
            [
                label,
                limit_value(profile.get("limits", {}).get(key), weighted_only=weighted_only),
                "unverified",
                note,
            ]
        )

    policy = profile.get("write_policy", {})
    write_policy_rows = [["`S`", policy.get("S", ""), "unverified", ""]]

    family_rows: list[list[Any]] = []
    for family in device_ranges["ordered_items"]:
        row = device_ranges["rows"].get(family)
        rule = range_rules.get(family)
        note = DEVICE_FAMILY_NOTES.get(family, "")
        if rule and rule.get("kind") == "unsupported":
            note = note or "Expected unsupported by JSON; verify with a valid probe address"
        family_rows.append(
            [
                family,
                devices_cell(row),
                range_rule_cell(rule),
                "unverified",
                note,
            ]
        )

    final_rows = [
        ["Features", "Pending live verification", "All `unverified` feature rows"],
        ["Limits", "Pending live verification", "All intended limit rows"],
        ["Write policy", "Pending live verification", "`S`"],
        ["Device families", "Pending live verification", "All `unverified` device-family rows"],
    ]

    lines = [
        f"# {profile_title(args.profile)} / {args.profile} SLMP Live Verification",
        "",
        "Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.",
        "This is a decision record, not a communication log.",
        "",
        "This file is a generated draft. Replace `unverified` statuses with live decisions after probing.",
        "",
        "Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.",
        "",
        "Common rules:",
        "",
        "- `G` and `HG` are not standalone device routes. Use routed forms only.",
        "- `S` write behavior is profile-specific. Verify it per PLC/profile; do not assume read-only.",
        "- Device writes are allowed for verification unless explicitly disabled.",
        "- Numeric write probes use random test values. Do not require restoring the old numeric value.",
        "- Bit write probes must reset the tested bits to OFF after the write check.",
        "",
        "## Session",
        "",
        md_table(["Item", "Value"], session_rows),
        "",
        "## Feature Checklist",
        "",
        "Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.",
        "",
        md_table(["Feature", "JSON expectation", "Target used", "Status", "Decision note"], feature_rows),
        "",
        "## Qualified Access Checklist",
        "",
        "Use this table for access routes and qualifiers, not ordinary device-family existence.",
        "",
        md_table(["Route", "JSON feature / rule", "Target used", "Status", "Decision note"], qualified_rows),
        "",
        "## Limit Checklist",
        "",
        "Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.",
        "For random word write, verify the count limit and the weighted limit separately when `weighted max` is defined.",
        "The weighted-limit probe must keep the total point count within `max` and exceed only `weighted max`; do not treat `81 word` or `161 word` count-over probes as weighted-limit evidence.",
        "Typical weighted-only probes are `40 word + 40 dword` for `max 80 / weighted max 960`, and `138 dword` for `max 160 / weighted max 1920`.",
        "For extended random routes, verify the ext-specific limit rows separately from the plain random rows.",
        "",
        md_table(["Limit item", "JSON value", "Status", "Decision note"], limit_rows),
        "",
        "## Write Policy Checklist",
        "",
        "`S` write behavior is profile-specific. Verify it per PLC/profile.",
        "Do not keep noise such as \"not written to a nonexistent address\". If a write result is needed, use an address that exists for the connected PLC.",
        "",
        md_table(["Device family", "JSON policy", "Status", "Decision note"], write_policy_rows),
        "",
        "## Device Family Access Checklist",
        "",
        "Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.",
        "",
        md_table(["Family", "Devices", "JSON rule", "Status", "Decision note"], family_rows),
        "",
        "## Final Decision",
        "",
        md_table(["Area", "Decision", "Remaining unverified items"], final_rows),
        "",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a live PLC verification checklist draft.")
    parser.add_argument("--profile", required=True, help="Canonical profile id, for example melsec:iq-f.")
    parser.add_argument("--plc-model", default="", help="PLC model name to place in the Session table.")
    parser.add_argument("--endpoint", default="192.168.250.100:1025 TCP")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--notes", default="Built-in Ethernet profile verification draft")
    parser.add_argument("--output", type=Path, help="Output Markdown file. Defaults under evidence/.")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing output file.")
    parser.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing a file.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    text = render(args)
    if args.stdout:
        print(text, end="")
        return 0
    output = args.output or default_output(args.profile, args.date)
    if not output.is_absolute():
        output = ROOT / output
    if output.exists() and not args.force:
        raise SystemExit(f"output already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8", newline="\n")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
