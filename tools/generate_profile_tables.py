#!/usr/bin/env python3
"""Generate user-facing Markdown tables from the SLMP profile JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_JSON = ROOT / "capability" / "slmp_ethernet_profiles.json"
DEVICE_RANGES_JSON = ROOT / "device-ranges" / "slmp_device_range_rules.json"
PARAMETERS_OUTPUT = ROOT / "tables" / "slmp_profile_parameters.md"
DEVICE_RANGES_OUTPUT = ROOT / "tables" / "slmp_device_ranges.md"

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
    "random_read_word_ext": "Extended random word read",
    "random_write_word_ext": "Extended random word write",
    "random_write_bit_ext": "Extended random bit write",
    "monitor_register_word_ext": "Extended monitor word register",
}

PROFILE_ORDER = [
    "melsec:iq-r",
    "melsec:iq-r:rj71en71",
    "melsec:iq-l",
    "melsec:mx-r",
    "melsec:mx-r:rj71en71",
    "melsec:mx-f",
    "melsec:iq-f",
    "melsec:qcpu",
    "melsec:qcpu:qj71e71-100",
    "melsec:lcpu",
    "melsec:lcpu:lj71e71-100",
    "melsec:qnu",
    "melsec:qnu:qj71e71-100",
    "melsec:qnudv",
    "melsec:qnudv:qj71e71-100",
]

SOURCE_SEMANTICS = {
    "live": "Directly verified on live PLC hardware.",
    "policy": "Adopted by explicit project/user policy; not necessarily live-verified for that exact profile.",
    "spec": "Derived from the specification or from a structural hardware constraint.",
    "inferred": "Inferred from another verified profile or an equivalent command group; not directly live-verified.",
    "manual": "Taken from manual documentation.",
    "not-adopted": "Recorded to keep the profile schema uniform even though the feature is not adopted for normal use.",
}

SUPPLEMENTAL_DEVICE_ROWS = {
    "DX": {
        "classification": "Direct access I/O",
        "device_name": "Direct input",
        "devices": [{"device": "DX", "type": "bit", "is_bit": True}],
        "notation": "base16",
    },
    "DY": {
        "classification": "Direct access I/O",
        "device_name": "Direct output",
        "devices": [{"device": "DY", "type": "bit", "is_bit": True}],
        "notation": "base16",
    },
}

SUPPLEMENTAL_UNSUPPORTED_BY_PROFILE = {
    "melsec:iq-f": {"DX", "DY"},
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


def ordered_profiles(profiles: dict[str, Any]) -> dict[str, Any]:
    ordered = {profile_id: profiles[profile_id] for profile_id in PROFILE_ORDER if profile_id in profiles}
    for profile_id, profile in profiles.items():
        if profile_id not in ordered:
            ordered[profile_id] = profile
    return ordered


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


def availability_cell(rule: dict[str, Any] | None) -> str:
    if not rule:
        return "?"
    kind = rule.get("kind")
    if kind == "unsupported":
        return "x"
    return "o"


def supplemental_availability_cell(device_family: str, profile_id: str) -> str:
    if device_family in SUPPLEMENTAL_UNSUPPORTED_BY_PROFILE.get(profile_id, set()):
        return "x"
    return "o"


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


def device_definition_items(device_ranges: dict[str, Any], include_supplemental: bool) -> list[tuple[str, dict[str, Any]]]:
    items: list[tuple[str, dict[str, Any]]] = []
    inserted = False
    for symbol, row in device_ranges.get("rows", {}).items():
        items.append((symbol, row))
        if include_supplemental and symbol == "SB":
            items.extend(SUPPLEMENTAL_DEVICE_ROWS.items())
            inserted = True
    if include_supplemental and not inserted:
        items.extend(SUPPLEMENTAL_DEVICE_ROWS.items())
    return items


def availability_items(device_ranges: dict[str, Any]) -> list[str]:
    items: list[str] = []
    inserted = False
    for item in device_ranges["ordered_items"]:
        items.append(item)
        if item == "SB":
            items.extend(SUPPLEMENTAL_DEVICE_ROWS)
            inserted = True
    if not inserted:
        items.extend(SUPPLEMENTAL_DEVICE_ROWS)
    return items


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


def build_profile_summary(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(capability["profiles"])
    rows = []
    for profile_id, profile in profiles.items():
        subcommands = profile.get("subcommands", {})
        rows.append(
            [
                profile_id,
                profile.get("display_name", "-"),
                profile.get("scope", "-"),
                profile.get("role", "connection"),
                profile.get("base_profile", "-"),
                profile.get("frame", "-"),
                profile.get("compat", "-"),
                subcommands.get("word", "-"),
                subcommands.get("bit", "-"),
                subcommands.get("ext_word", "-"),
                subcommands.get("ext_bit", "-"),
                "<br>".join(profile.get("verified_models", [])) or "-",
            ]
        )
    return "\n\n".join(
        [
            "## Profile Summary",
            md_table(
                [
                    "Profile",
                    "Display name",
                    "Scope",
                    "Role",
                    "Base profile",
                    "Frame",
                    "Compat",
                    "Word subcmd",
                    "Bit subcmd",
                    "Ext word",
                    "Ext bit",
                    "Verified models",
                ],
                rows,
            ),
        ]
    )


def build_device_definitions(device_ranges: dict[str, Any]) -> str:
    rows = [
        [
            row.get("classification", "-"),
            symbol,
            row.get("device_name", "-"),
            device_definition_type(row),
            row.get("notation", "-"),
        ]
        for symbol, row in device_definition_items(device_ranges, include_supplemental=True)
    ]
    return "\n\n".join(
        [
            "## Device Definitions",
            md_table(["Classification", "Symbol", "Device name", "Type", "Notation"], rows),
        ]
    )


def build_device_availability_matrix(device_ranges: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(device_ranges["profiles"])
    profile_ids = list(profiles)
    rows = []
    for item in availability_items(device_ranges):
        if item in SUPPLEMENTAL_DEVICE_ROWS:
            cells = [supplemental_availability_cell(item, profile_id) for profile_id in profile_ids]
        else:
            cells = [
                availability_cell(profiles[profile_id].get("rules", {}).get(item))
                for profile_id in profile_ids
            ]
        rows.append([item] + cells)
    return "\n\n".join(
        [
            "## Device Availability Matrix",
            "`o` means available for the profile. `x` means unsupported. Availability does not imply a static range upper bound.",
            "`DX` and `DY` are public parser families without range catalog rules; they are listed here only for profile availability.",
            md_table(["Device family"] + profile_ids, rows),
        ]
    )


def build_feature_matrix(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(capability["profiles"])
    profile_ids = list(profiles)
    feature_ids = [
        feature_id
        for feature_id in FEATURE_LABELS
        if any(feature_id in profiles[profile_id].get("features", {}) for profile_id in profile_ids)
    ]
    rows = []
    for feature_id in feature_ids:
        rows.append(
            [FEATURE_LABELS.get(feature_id, feature_id)]
            + [
                state_cell(profiles[profile_id].get("features", {}).get(feature_id))
                for profile_id in profile_ids
            ]
        )
    return "\n\n".join(
        [
            "## Feature Matrix",
            "Cell format is `state/source`.",
            md_table(["Feature"] + profile_ids, rows),
        ]
    )


def build_point_limit_matrix(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(capability["profiles"])
    profile_ids = list(profiles)
    limit_ids = [
        limit_id
        for limit_id in LIMIT_LABELS
        if any(limit_id in profiles[profile_id].get("limits", {}) for profile_id in profile_ids)
    ]
    rows = []
    for limit_id in limit_ids:
        rows.append(
            [LIMIT_LABELS.get(limit_id, limit_id)]
            + [
                limit_cell(profiles[profile_id].get("limits", {}).get(limit_id))
                for profile_id in profile_ids
            ]
        )
    return "\n\n".join(
        [
            "## Point Limit Matrix",
            md_table(["Limit"] + profile_ids, rows),
            "Note: `melsec:iq-f` uses live-verified over-limit end codes where word overrun returns `C052` and bit overrun returns `C051`.",
        ]
    )


def build_write_policy(capability: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(capability["profiles"])
    rows = [
        [profile_id, write_policy_cell(profile.get("write_policy"))]
        for profile_id, profile in profiles.items()
    ]
    return "\n\n".join(["## Write Policy", md_table(["Profile", "Policy"], rows)])


def build_cell_appendix(capability: dict[str, Any]) -> str:
    state_semantics = capability.get("policy", {}).get("state_semantics", {})
    state_rows = [[state, meaning] for state, meaning in state_semantics.items()]
    source_rows = [[source, SOURCE_SEMANTICS[source]] for source in collect_used_sources(capability)]
    return "\n\n".join(
        [
            "## Appendix: How To Read Cells",
            "`state/source` combines the capability decision with the evidence source. For example, `config-dependent/live` means `state=config-dependent` and `source=live`.",
            "### State Values",
            md_table(["State", "Meaning"], state_rows),
            "### Source Values",
            md_table(["Source", "Meaning"], source_rows),
        ]
    )


def build_parameters_page(capability: dict[str, Any], device_ranges: dict[str, Any]) -> str:
    source_label = (
        f"Generated user-facing reference. Source: `{CAPABILITY_JSON.relative_to(ROOT).as_posix()}` / "
        f"`{DEVICE_RANGES_JSON.relative_to(ROOT).as_posix()}`."
    )
    metadata = (
        f"Capability schema {capability.get('schema_version', '-')}, "
        f"capability date {capability.get('date', '-')}, "
        f"scope `{capability.get('scope', '-')}`, "
        f"default strict mode `{capability.get('policy', {}).get('default_strict', '-')}`. "
        f"Device-range schema {device_ranges.get('schema_version', '-')}, "
        f"device-range date {device_ranges.get('date', '-')}."
    )
    return "\n\n".join(
        [
            "# SLMP Profile Parameters",
            "<!-- Generated by tools/generate_profile_tables.py. Do not edit manually. -->",
            source_label,
            metadata,
            "## Purpose",
            "Profile parameters document selectable profile IDs, feature decisions, point limits, write policy, and device availability for user manuals and profile-selection tools.",
            "They do not guarantee that every address or configuration-dependent route will work on a particular PLC installation; use live PLC responses for runtime truth.",
            build_profile_summary(capability),
            build_device_definitions(device_ranges),
            build_device_availability_matrix(device_ranges),
            build_feature_matrix(capability),
            build_point_limit_matrix(capability),
            build_write_policy(capability),
            build_cell_appendix(capability),
            "",
        ]
    )


def build_device_value_kinds(device_ranges: dict[str, Any]) -> str:
    rows = [
        [kind, meaning]
        for kind, meaning in device_ranges.get("value_kinds", {}).items()
    ]
    if not rows:
        return ""
    return "\n\n".join(["## Device Value Kinds", md_table(["Kind", "Meaning"], rows)])


def build_device_range_blocks(device_ranges: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(device_ranges["profiles"])
    rows = [
        [
            profile_id,
            profile.get("register_start", "-"),
            profile.get("register_count", "-"),
            profile.get("base_profile", "-"),
        ]
        for profile_id, profile in profiles.items()
    ]
    return "\n\n".join(
        [
            "## Device Range Blocks",
            md_table(["Profile", "SD register start", "SD register count", "Base profile"], rows),
        ]
    )


def build_device_family_rule_comparison(device_ranges: dict[str, Any]) -> str:
    profiles: dict[str, Any] = ordered_profiles(device_ranges["profiles"])
    profile_ids = list(profiles)
    rows = []
    for item in device_ranges["ordered_items"]:
        row = device_ranges.get("rows", {}).get(item, {})
        rows.append(
            [item, device_definition_type(row)]
            + [
                range_rule_cell(profiles[profile_id].get("rules", {}).get(item))
                for profile_id in profile_ids
            ]
        )
    return "\n\n".join(
        [
            "## Device Family Rule Comparison",
            md_table(["Device family", "Type"] + profile_ids, rows),
        ]
    )


def build_device_ranges_page(device_ranges: dict[str, Any]) -> str:
    source_label = f"Generated user-facing reference. Source: `{DEVICE_RANGES_JSON.relative_to(ROOT).as_posix()}`."
    metadata = (
        f"Device-range schema {device_ranges.get('schema_version', '-')}, "
        f"device-range date {device_ranges.get('date', '-')}."
    )
    return "\n\n".join(
        [
            "# SLMP Device Ranges",
            "<!-- Generated by tools/generate_profile_tables.py. Do not edit manually. -->",
            source_label,
            metadata,
            "## Purpose",
            "Device range rules are not send/receive address guards for communication libraries.",
            "They are for device monitor, diagnostic, setup, and application-layer validation tools that need to discover or display valid ranges.",
            "When an exact range is configuration-dependent, prefer a live probe or the PLC response over a static upper-bound assumption.",
            build_device_value_kinds(device_ranges),
            build_device_range_blocks(device_ranges),
            build_device_family_rule_comparison(device_ranges),
            "## Appendix: How To Read Cells",
            "A `-` cell means no catalog rule is defined for that profile and device family.",
            "An `unsupported` cell means the profile explicitly records that the device family is not available.",
            "A `probe` suffix means the value is retained as probe-oriented catalog data rather than a guaranteed static range.",
            "",
        ]
    )


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def main() -> None:
    capability = load_json(CAPABILITY_JSON)
    device_ranges = load_json(DEVICE_RANGES_JSON)

    write_text(PARAMETERS_OUTPUT, build_parameters_page(capability, device_ranges))
    write_text(DEVICE_RANGES_OUTPUT, build_device_ranges_page(device_ranges))


if __name__ == "__main__":
    main()
