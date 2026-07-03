#!/usr/bin/env python3
"""Generate Markdown comparison tables from the SLMP profile JSON files."""

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

PROFILE_ORDER = [
    "melsec:iq-r",
    "melsec:iq-l",
    "melsec:mx-r",
    "melsec:mx-f",
    "melsec:iq-f",
    "melsec:qcpu",
    "melsec:lcpu",
    "melsec:qnu",
    "melsec:qnudv",
]

SOURCE_SEMANTICS = {
    "live": "Directly verified on live PLC hardware.",
    "policy": "Adopted by explicit project/user policy; not necessarily live-verified for that exact profile.",
    "spec": "Derived from the specification or from a structural hardware constraint.",
    "inferred": "Inferred from another verified profile or an equivalent command group; not directly live-verified.",
    "manual": "Taken from manual documentation.",
}

COMMON_CELL_MEANINGS = {
    "supported/live": "Works on live hardware. Send normally.",
    "supported/policy": "Allowed by policy, usually by profile equivalence or user decision. Not directly live-verified for that exact profile.",
    "blocked/live": "Verified unavailable on live hardware. In strict mode, fail before transport.",
    "blocked/policy": "Blocked by project policy. In strict mode, fail before transport.",
    "blocked/spec": "Blocked by specification or a structural hardware constraint. In strict mode, fail before transport.",
    "config-dependent/live": "Depends on PLC configuration and succeeded on a live configuration where the required unit/path exists. Do not profile-guard; send and let the PLC respond if the unit/path is absent.",
    "config-dependent/policy": "Treated as configuration-dependent by policy, without direct live verification for that exact profile. Do not profile-guard; send and let the PLC respond.",
    "unverified/policy": "Not verified. In strict mode, guard as blocked; with strict disabled, allow sending.",
    "delegated/live": "Live behavior shows the profile should not decide this feature. Delegate to existing runtime mechanisms such as range lookup or global route rules.",
    "delegated/policy": "Policy says the profile should not decide this feature. Delegate to existing runtime mechanisms such as range lookup or global route rules.",
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


def feature_cell(feature: dict[str, Any] | None) -> str:
    return state_cell(feature)


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

    def with_probe(text: str) -> str:
        return f"{text} probe" if rule.get("probe") else text

    kind = rule.get("kind", "-")
    display_kind = {
        "word-register": "word",
        "dword-register": "dword",
        "word-register-clipped": "word-clipped",
        "dword-register-clipped": "dword-clipped",
    }.get(kind, kind)
    if kind == "fixed":
        return with_probe(f"fixed {rule.get('fixed_value', '-')}")
    if kind == "unsupported":
        return "unsupported"
    if kind == "undefined":
        return with_probe("undefined")

    register = rule.get("register")
    location = f"SD{register}" if register is not None else ""
    parts = [f"{display_kind}: {location}"] if location else [display_kind]
    if "clip_value" in rule:
        parts.append(f"clip {rule['clip_value']}")
    if rule.get("probe"):
        parts.append("probe")
    return " ".join(parts)


def device_row_cell(row: dict[str, Any] | None) -> str:
    if not row:
        return "-"
    devices = []
    for device in row.get("devices", []):
        name = device.get("device", "-")
        device_type = device.get("type")
        if not device_type:
            device_type = "bit" if device.get("is_bit") else "word"
        devices.append(f"{name}:{device_type}")
    parts = [
        f"classification={row.get('classification', '-')}",
        f"name={row.get('device_name', '-')}",
        f"notation={row.get('notation', '-')}",
        "devices=" + ", ".join(devices) if devices else "devices=-",
    ]
    return "<br>".join(parts)


def device_definition_type(row: dict[str, Any]) -> str:
    devices = []
    for device in row.get("devices", []):
        name = device.get("device", "-")
        device_type = device.get("type")
        if not device_type:
            device_type = "bit" if device.get("is_bit") else "word"
        devices.append(f"{name}:{device_type}")
    if len(devices) == 1:
        return devices[0].split(":", 1)[1]
    return ", ".join(devices)


def ordered_profiles(profiles: dict[str, Any]) -> dict[str, Any]:
    ordered = {profile_id: profiles[profile_id] for profile_id in PROFILE_ORDER if profile_id in profiles}
    for profile_id, profile in profiles.items():
        if profile_id not in ordered:
            ordered[profile_id] = profile
    return ordered


def build_port_scope_section(capability: dict[str, Any], device_ranges: dict[str, Any]) -> str:
    rows = [
        ["Capability schema version", capability.get("schema_version", "-")],
        ["Capability date", capability.get("date", "-")],
        ["Scope", capability.get("scope", "-")],
        ["Description", capability.get("description", "-")],
        ["Default strict mode", capability.get("policy", {}).get("default_strict", "-")],
        ["Device range schema version", device_ranges.get("schema_version", "-")],
        ["Device range date", device_ranges.get("date", "-")],
    ]
    if "description" in device_ranges:
        rows.append(["Device range description", device_ranges["description"]])

    return "\n\n".join(
        [
        "## Port Scope",
        md_table(["Item", "Value"], rows),
        ]
    )


def collect_used_sources(capability: dict[str, Any]) -> list[str]:
    used: set[str] = set()
    for profile in capability["profiles"].values():
        for feature in profile.get("features", {}).values():
            if "source" in feature:
                used.add(feature["source"])
        for limit in profile.get("limits", {}).values():
            if "source" in limit:
                used.add(limit["source"])
    return [source for source in SOURCE_SEMANTICS if source in used]


def build_cell_legend_section(capability: dict[str, Any]) -> str:
    state_semantics = capability.get("policy", {}).get("state_semantics", {})

    state_rows = [[state, meaning] for state, meaning in state_semantics.items()]
    source_rows = [[source, SOURCE_SEMANTICS[source]] for source in collect_used_sources(capability)]
    combined_rows = [[cell, meaning] for cell, meaning in COMMON_CELL_MEANINGS.items()]

    return "\n\n".join(
        [
            "## How To Read Cells",
            "`state/source` combines the capability decision with the evidence source. For example, `config-dependent/live` means `state=config-dependent` and `source=live`.",
            "### State Values",
            md_table(["State", "Meaning"], state_rows),
            "### Source Values",
            md_table(["Source", "Meaning"], source_rows),
            "### Common Combined Values",
            md_table(["Cell", "Meaning"], combined_rows),
        ]
    )


def build_device_range_section(device_ranges: dict[str, Any]) -> str:
    range_profiles: dict[str, Any] = ordered_profiles(device_ranges["profiles"])
    range_profile_ids = list(range_profiles)

    value_kind_rows = [
        [kind, meaning]
        for kind, meaning in device_ranges.get("value_kinds", {}).items()
    ]

    range_block_rows = [
        [
            profile_id,
            range_profiles[profile_id].get("register_start", "-"),
            range_profiles[profile_id].get("register_count", "-"),
        ]
        for profile_id in range_profile_ids
    ]

    definition_rows = [
        [
            row.get("classification", "-"),
            symbol,
            row.get("device_name", "-"),
            device_definition_type(row),
            row.get("notation", "-"),
        ]
        for symbol, row in device_ranges.get("rows", {}).items()
    ]

    range_rule_rows = []
    for item in device_ranges["ordered_items"]:
        range_rule_rows.append(
            [
                item,
                device_row_cell(device_ranges.get("rows", {}).get(item)),
            ]
            + [
                range_rule_cell(range_profiles[profile_id].get("rules", {}).get(item))
                for profile_id in range_profile_ids
            ]
        )

    sections = [
        "## Device Range Rules",
        "These tables are generated from the device range JSON. They show the range metadata and every per-profile rule without omitting common values.",
    ]
    if value_kind_rows:
        sections.extend(["### Device Value Kinds", md_table(["Kind", "Meaning"], value_kind_rows)])
    sections.extend(
        [
            "### Device Definitions",
            md_table(["Classification", "Symbol", "Device name", "Type", "Notation"], definition_rows),
            "### Device Range Blocks",
            md_table(["Profile", "SD register start", "SD register count"], range_block_rows),
            "### Device Family Rule Comparison",
            md_table(["Device family", "Metadata"] + range_profile_ids, range_rule_rows),
        ]
    )
    return "\n\n".join(sections)


def build_capability_section(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(capability["profiles"])
    profile_ids = list(profiles)
    evidence_files = capability.get("evidence_files", {})

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
                "<br>".join(profile.get("verified_models", [])) or "-",
                evidence_files.get(profile_id, "-"),
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
                feature_cell(profiles[profile_id].get("features", {}).get(feature_id))
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
                    "Verified models",
                    "Evidence file",
                ],
                summary_rows,
            ),
            "### Feature Matrix",
            "Cell format is `state/source`.",
            md_table(["Feature"] + profile_ids, feature_rows),
            "### Point Limit Matrix",
            md_table(["Limit"] + profile_ids, limit_rows),
            "### Write Policy",
            md_table(["Profile", "Policy"], write_policy_rows),
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
            "This file is a maintenance view of the generated JSON and device range rules.",
            build_port_scope_section(capability, device_ranges),
            build_cell_legend_section(capability),
            build_capability_section(capability),
            build_device_range_section(device_ranges),
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
