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


def grouped_difference_cell(profile_ids: list[str], values: dict[str, str]) -> str:
    groups: dict[str, list[str]] = {}
    for profile_id in profile_ids:
        value = values.get(profile_id, "-")
        groups.setdefault(value, []).append(profile_id)
    return "<br>".join(
        f"`{value}`: {', '.join(grouped_profiles)}"
        for value, grouped_profiles in groups.items()
    )


def difference_rows(
    profile_ids: list[str],
    items: list[tuple[str, dict[str, str]]],
    *,
    include_same: bool = False,
) -> list[list[str]]:
    rows = []
    for label, values in items:
        distinct_values = {values.get(profile_id, "-") for profile_id in profile_ids}
        if not include_same and len(distinct_values) <= 1:
            continue
        rows.append([label, grouped_difference_cell(profile_ids, values)])
    return rows


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


def build_port_scope_section(capability: dict[str, Any]) -> str:
    notes = capability.get("policy", {}).get("notes", [])
    note_rows = [[note] for note in notes]

    return "\n\n".join(
        [
            "## Port Scope",
            md_table(
                ["Item", "Value"],
                [
                    ["Scope", capability.get("scope", "-")],
                    ["Description", capability.get("description", "-")],
                ],
            ),
            "### Policy Notes",
            md_table(["Note"], note_rows),
        ]
    )


def build_cell_legend_section(capability: dict[str, Any]) -> str:
    state_semantics = capability.get("policy", {}).get("state_semantics", {})

    state_rows = [[state, meaning] for state, meaning in state_semantics.items()]
    source_rows = [[source, meaning] for source, meaning in SOURCE_SEMANTICS.items()]
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


def build_difference_section(
    capability: dict[str, Any],
    device_ranges: dict[str, Any],
) -> str:
    capability_profiles: dict[str, Any] = capability["profiles"]
    capability_profile_ids = list(capability_profiles)
    range_profiles: dict[str, Any] = device_ranges["profiles"]
    range_profile_ids = list(range_profiles)

    profile_setting_items: list[tuple[str, dict[str, str]]] = []
    for label, getter in [
        ("Frame", lambda profile: profile.get("frame", "-")),
        ("Compatibility", lambda profile: profile.get("compat", "-")),
        ("Word subcommand", lambda profile: profile.get("subcommands", {}).get("word", "-")),
        ("Bit subcommand", lambda profile: profile.get("subcommands", {}).get("bit", "-")),
        ("Extended word subcommand", lambda profile: profile.get("subcommands", {}).get("ext_word", "-")),
        ("Extended bit subcommand", lambda profile: profile.get("subcommands", {}).get("ext_bit", "-")),
        ("Derived profile", lambda profile: profile.get("derived_from", "-")),
    ]:
        profile_setting_items.append(
            (
                label,
                {
                    profile_id: str(getter(capability_profiles[profile_id]))
                    for profile_id in capability_profile_ids
                },
            )
        )

    feature_ids = [
        feature_id
        for feature_id in FEATURE_LABELS
        if any(feature_id in capability_profiles[profile_id].get("features", {}) for profile_id in capability_profile_ids)
    ]
    feature_items = []
    for feature_id in feature_ids:
        feature_items.append(
            (
                FEATURE_LABELS.get(feature_id, feature_id),
                {
                    profile_id: state_cell(capability_profiles[profile_id].get("features", {}).get(feature_id))
                    for profile_id in capability_profile_ids
                },
            )
        )

    limit_ids = [
        limit_id
        for limit_id in LIMIT_LABELS
        if any(limit_id in capability_profiles[profile_id].get("limits", {}) for profile_id in capability_profile_ids)
    ]
    limit_items = []
    for limit_id in limit_ids:
        limit_items.append(
            (
                LIMIT_LABELS.get(limit_id, limit_id),
                {
                    profile_id: limit_cell(capability_profiles[profile_id].get("limits", {}).get(limit_id))
                    for profile_id in capability_profile_ids
                },
            )
        )

    write_policy_items = [
        (
            "Write policy",
            {
                profile_id: write_policy_cell(capability_profiles[profile_id].get("write_policy"))
                for profile_id in capability_profile_ids
            },
        )
    ]

    range_block_items = []
    for label, key in [
        ("SD register start", "register_start"),
        ("SD register count", "register_count"),
    ]:
        range_block_items.append(
            (
                label,
                {
                    profile_id: str(range_profiles[profile_id].get(key, "-"))
                    for profile_id in range_profile_ids
                },
            )
        )

    range_rule_items = []
    for item in device_ranges["ordered_items"]:
        range_rule_items.append(
            (
                item,
                {
                    profile_id: range_rule_cell(range_profiles[profile_id].get("rules", {}).get(item))
                    for profile_id in range_profile_ids
                },
            )
        )

    return "\n\n".join(
        [
            "## Difference Views",
            "These tables group profiles that have the same value. Rows where every profile has the same value are omitted.",
            "### Profile Setting Differences",
            md_table(["Item", "Value groups"], difference_rows(capability_profile_ids, profile_setting_items)),
            "### Feature State Differences",
            "Cell format inside each value group is `state/source`.",
            md_table(["Feature", "Value groups"], difference_rows(capability_profile_ids, feature_items)),
            "### Point Limit Differences",
            md_table(["Limit", "Value groups"], difference_rows(capability_profile_ids, limit_items)),
            "### Write Policy Differences",
            md_table(["Item", "Value groups"], difference_rows(capability_profile_ids, write_policy_items)),
            "### Device Range Block Differences",
            md_table(["Item", "Value groups"], difference_rows(range_profile_ids, range_block_items)),
            "### Device Family Rule Differences",
            md_table(["Device family", "Value groups"], difference_rows(range_profile_ids, range_rule_items)),
        ]
    )


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
            build_port_scope_section(capability),
            build_cell_legend_section(capability),
            build_difference_section(capability, device_ranges),
            build_capability_section(capability),
            build_device_range_section(device_ranges),
            "",
        ]
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(content, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
