#!/usr/bin/env python3
"""Generate Markdown comparison tables from the canonical SLMP profile JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_JSON = ROOT / "capability" / "slmp_builtin_ethernet_profiles.json"
DEVICE_RANGES_JSON = ROOT / "device-ranges" / "slmp_device_range_rules.json"
OUTPUT = ROOT / "tables" / "slmp_profile_comparison.md"

FEATURE_LABELS = {
    "type_name": "Type name",
    "direct": "Direct read/write",
    "random": "Random read/write",
    "block": "Block read/write",
    "monitor": "Monitor",
    "ext_module_access": "U\\G module access",
    "ext_link_direct": "Link direct",
    "hg_cpu_buffer": "HG CPU buffer",
    "long_device_path": "Long-device route",
    "lz_32bit_path": "LZ 32-bit route",
}

LIMIT_LABELS = {
    "direct_word_read": "Direct word read",
    "direct_word_write": "Direct word write",
    "direct_bit_read": "Direct bit read",
    "direct_bit_write": "Direct bit write",
    "random_read_word": "Random word read",
    "random_write_word": "Random word write",
    "random_write_bit": "Random bit write",
    "monitor_register_word": "Monitor word register",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def md_escape(value: Any) -> str:
    if value is None:
        return "-"
    text = str(value)
    if text == "":
        return "-"
    return text.replace("|", "\\|").replace("\n", "<br>")


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(md_escape(header) for header in headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(md_escape(cell) for cell in row) + " |")
    return "\n".join(lines)


def state_cell(feature: dict[str, Any] | None) -> str:
    if not feature:
        return "-"
    state = feature.get("state", "-")
    source = feature.get("source")
    if source:
        return f"{state}/{source}"
    return state


def limit_cell(limit: dict[str, Any] | None) -> str:
    if not limit:
        return "-"
    parts: list[str] = []
    if "max" in limit:
        parts.append(f"max {limit['max']}")
    if "weighted_max" in limit:
        parts.append(f"weighted {limit['weighted_max']}")
    if "over_end_code" in limit:
        parts.append(f"over {limit['over_end_code']}")
    if "source" in limit:
        parts.append(f"[{limit['source']}]")
    return ", ".join(parts) if parts else "-"


def write_policy_cell(policy: dict[str, Any] | None) -> str:
    if not policy:
        return "-"
    return ", ".join(f"{key}={value}" for key, value in sorted(policy.items()))


def range_rule_cell(rule: dict[str, Any] | None) -> str:
    if not rule:
        return "-"

    kind = rule.get("kind", "-")
    if kind == "fixed":
        return f"fixed {rule.get('fixed_value', '-')}"
    if kind == "unsupported":
        return "unsupported"
    if kind == "undefined":
        return "undefined"

    source = rule.get("source", "")
    parts = [kind]
    if source:
        parts.append(source)
    if "clip_value" in rule:
        parts.append(f"clip {rule['clip_value']}")
    return " ".join(parts)


def build_capability_section(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = capability["profiles"]
    profile_ids = list(profiles)

    summary_rows = []
    for profile_id in profile_ids:
        profile = profiles[profile_id]
        subcommands = profile.get("subcommands", {})
        summary_rows.append(
            [
                profile_id,
                profile.get("frame", "-"),
                profile.get("compat", "-"),
                subcommands.get("word", "-"),
                subcommands.get("bit", "-"),
                subcommands.get("ext_word", "-"),
                subcommands.get("ext_bit", "-"),
                profile.get("derived_from", "-"),
                "<br>".join(profile.get("verified_models", [])) or "-",
            ]
        )

    feature_ids = [
        feature_id
        for feature_id in FEATURE_LABELS
        if any(feature_id in profiles[profile_id].get("features", {}) for profile_id in profile_ids)
    ]
    feature_rows = []
    for feature_id in feature_ids:
        feature_rows.append(
            [FEATURE_LABELS.get(feature_id, feature_id)]
            + [
                state_cell(profiles[profile_id].get("features", {}).get(feature_id))
                for profile_id in profile_ids
            ]
        )

    limit_ids = [
        limit_id
        for limit_id in LIMIT_LABELS
        if any(limit_id in profiles[profile_id].get("limits", {}) for profile_id in profile_ids)
    ]
    limit_rows = []
    for limit_id in limit_ids:
        limit_rows.append(
            [LIMIT_LABELS.get(limit_id, limit_id)]
            + [
                limit_cell(profiles[profile_id].get("limits", {}).get(limit_id))
                for profile_id in profile_ids
            ]
        )

    write_policy_rows = [
        [profile_id, write_policy_cell(profiles[profile_id].get("write_policy"))]
        for profile_id in profile_ids
    ]

    return "\n\n".join(
        [
            "## Capability Profiles",
            "### Profile Summary",
            md_table(
                [
                    "Profile",
                    "Frame",
                    "Compat",
                    "Word subcmd",
                    "Bit subcmd",
                    "Ext word",
                    "Ext bit",
                    "Derived from",
                    "Verified models",
                ],
                summary_rows,
            ),
            "### Feature State Matrix",
            "Cell format: `state/source`.",
            md_table(["Feature"] + profile_ids, feature_rows),
            "### Point Limit Matrix",
            md_table(["Limit"] + profile_ids, limit_rows),
            "### Write Policy",
            md_table(["Profile", "Policy"], write_policy_rows),
        ]
    )


def build_device_range_section(device_ranges: dict[str, Any]) -> str:
    profiles: dict[str, Any] = device_ranges["profiles"]
    profile_ids = list(profiles)
    ordered_items = device_ranges["ordered_items"]

    summary_rows = [
        [
            profile_id,
            profiles[profile_id].get("register_start", "-"),
            profiles[profile_id].get("register_count", "-"),
        ]
        for profile_id in profile_ids
    ]

    rule_rows = []
    for item in ordered_items:
        rule_rows.append(
            [item]
            + [
                range_rule_cell(profiles[profile_id].get("rules", {}).get(item))
                for profile_id in profile_ids
            ]
        )

    return "\n\n".join(
        [
            "## Device Range Rules",
            "### SD Register Blocks",
            md_table(["Profile", "Register start", "Register count"], summary_rows),
            "### Device Family Rule Matrix",
            md_table(["Device family"] + profile_ids, rule_rows),
        ]
    )


def main() -> None:
    capability = load_json(CAPABILITY_JSON)
    device_ranges = load_json(DEVICE_RANGES_JSON)

    content = "\n\n".join(
        [
            "# SLMP Profile Comparison Tables",
            "<!-- Generated by tools/generate_profile_tables.py. Do not edit manually. -->",
            f"Generated from `{CAPABILITY_JSON.relative_to(ROOT).as_posix()}` and `{DEVICE_RANGES_JSON.relative_to(ROOT).as_posix()}`.",
            "The JSON files remain the canonical source of truth; this file is only a maintenance view.",
            build_capability_section(capability),
            build_device_range_section(device_ranges),
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
