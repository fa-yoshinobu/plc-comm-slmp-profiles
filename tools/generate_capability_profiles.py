#!/usr/bin/env python3
"""Generate canonical SLMP capability profiles from profile definition Markdown."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFINITION_DIR = ROOT / "evidence" / "profile-definitions"
OUTPUT = ROOT / "capability" / "slmp_builtin_ethernet_profiles.json"

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

STATE_SEMANTICS = {
    "supported": "Adopted as supported for this profile. Send normally.",
    "blocked": "Not adopted for this profile. In strict mode, fail before transport.",
    "config-dependent": (
        "Depends on the PLC configuration, such as whether the target unit exists. "
        "Do not guard; send and let the PLC respond."
    ),
    "unverified": "Unverified. In strict mode, guard as blocked; with strict disabled, allow sending.",
    "delegated": (
        "Delegated to existing runtime mechanisms, such as SD-derived device range lookup and global rules. "
        "The profile does not decide or guard this feature."
    ),
}

SUBCOMMAND_KEYS = {
    "word": "word_subcommand",
    "bit": "bit_subcommand",
    "ext_word": "ext_word_subcommand",
    "ext_bit": "ext_bit_subcommand",
}


def strip_cell(value: str) -> str:
    text = value.strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        return text[1:-1]
    return text


def parse_markdown_tables(text: str) -> dict[str, list[dict[str, str]]]:
    current_section = "Item"
    tables: dict[str, list[dict[str, str]]] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if line.startswith("## "):
            current_section = line[3:].strip()
            index += 1
            continue
        if not line.startswith("|"):
            index += 1
            continue

        table_lines: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            table_lines.append(lines[index].strip())
            index += 1
        if len(table_lines) < 2:
            continue
        headers = [strip_cell(cell) for cell in table_lines[0].strip("|").split("|")]
        rows: list[dict[str, str]] = []
        for row_line in table_lines[2:]:
            cells = [strip_cell(cell) for cell in row_line.strip("|").split("|")]
            if len(cells) != len(headers):
                raise ValueError(f"table row/header mismatch in {current_section}: {row_line}")
            rows.append(dict(zip(headers, cells, strict=True)))
        tables[current_section] = rows
    return tables


def rows_to_mapping(rows: list[dict[str, str]]) -> dict[str, str]:
    result: dict[str, str] = {}
    for row in rows:
        key = row.get("Item") or row.get("Key") or row.get("Device")
        value = row.get("Value") or row.get("Policy")
        if key is None or value is None:
            raise ValueError(f"cannot map table row: {row}")
        result[key] = value
    return result


def parse_definition(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    tables = parse_markdown_tables(text)
    item = rows_to_mapping(tables.get("Item", []))
    features = tables.get("Features", [])
    limits = tables.get("Limits", [])
    write_policy = rows_to_mapping(tables.get("Write Policy", [])) if "Write Policy" in tables else {}
    overrides = rows_to_mapping(tables.get("Overrides", [])) if "Overrides" in tables else {}
    if "profile" not in item:
        raise ValueError(f"missing profile in {path}")
    return {
        "path": path,
        "profile": item["profile"],
        "item": item,
        "features": features,
        "limits": limits,
        "write_policy": write_policy,
        "overrides": overrides,
    }


def parse_models(raw: str) -> list[str]:
    if not raw:
        return []
    if raw == "Unconfirmed":
        return ["Unconfirmed"]
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_optional_int(raw: str) -> int | None:
    text = raw.strip()
    if not text:
        return None
    return int(text, 10)


def live_profile(definition: dict[str, Any]) -> dict[str, Any]:
    item = definition["item"]
    subcommands = {json_key: item[md_key] for json_key, md_key in SUBCOMMAND_KEYS.items()}

    features: dict[str, dict[str, str]] = {}
    for row in definition["features"]:
        features[row["Key"]] = {"state": row["State"], "source": row["Source"]}

    limits: dict[str, dict[str, Any]] = {}
    for row in definition["limits"]:
        source = row["Source"]
        max_value = parse_optional_int(row["Max"])
        weighted = parse_optional_int(row["Weighted max"])
        over = row["Over end code"].strip()
        if source == "not-adopted" and max_value is None and weighted is None and not over:
            continue
        entry: dict[str, Any] = {"source": source}
        if max_value is not None:
            entry["max"] = max_value
        if weighted is not None:
            entry["weighted_max"] = weighted
        if over:
            entry["over_end_code"] = over
        limits[row["Key"]] = entry

    return {
        "frame": item["frame"],
        "compat": item["compat"],
        "subcommands": subcommands,
        "verified_models": parse_models(item.get("verified_models", "")),
        "features": features,
        "limits": limits,
        "write_policy": definition["write_policy"],
    }


def mark_derived(profile: dict[str, Any]) -> None:
    for feature in profile.get("features", {}).values():
        if feature.get("source") == "live":
            feature["source"] = "policy"
    for limit in profile.get("limits", {}).values():
        if limit.get("source") == "live":
            limit["source"] = "inferred"


def set_dotted(target: dict[str, Any], dotted_key: str, value: str) -> None:
    parts = dotted_key.split(".")
    current: dict[str, Any] = target
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    final = parts[-1]
    if final == "verified_models":
        current[final] = parse_models(value)
    else:
        current[final] = value


def build_profiles(definitions: dict[str, dict[str, Any]]) -> dict[str, Any]:
    built: dict[str, Any] = {}

    def build(profile_id: str) -> dict[str, Any]:
        if profile_id in built:
            return built[profile_id]
        definition = definitions[profile_id]
        dtype = definition["item"].get("definition_type")
        if dtype == "live":
            profile = live_profile(definition)
        elif dtype == "derived":
            base_id = definition["item"]["base_profile"]
            profile = copy.deepcopy(build(base_id))
            mark_derived(profile)
            for key, value in definition["overrides"].items():
                set_dotted(profile, key, value)
        else:
            raise ValueError(f"unsupported definition_type {dtype!r} for {profile_id}")
        built[profile_id] = profile
        return profile

    for profile_id in PROFILE_ORDER:
        build(profile_id)
    return {profile_id: built[profile_id] for profile_id in PROFILE_ORDER}


def definition_files() -> dict[str, dict[str, Any]]:
    definitions: dict[str, dict[str, Any]] = {}
    for path in sorted(DEFINITION_DIR.glob("*_profile_definition_*.md")):
        definition = parse_definition(path)
        profile = definition["profile"]
        if profile in definitions:
            raise ValueError(f"duplicate profile definition for {profile}: {path}")
        definitions[profile] = definition
    missing = [profile for profile in PROFILE_ORDER if profile not in definitions]
    if missing:
        raise ValueError(f"missing profile definitions: {missing}")
    return definitions


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def build_output() -> dict[str, Any]:
    definitions = definition_files()
    return {
        "schema_version": 1,
        "date": "2026-07-03",
        "scope": "builtin-ethernet-port",
        "description": (
            "Canonical PLC model profile definitions for the SLMP library family. "
            "Generated from evidence/profile-definitions."
        ),
        "policy": {
            "default_strict": True,
            "state_semantics": STATE_SEMANTICS,
        },
        "evidence_files": {
            profile_id: relative(definitions[profile_id]["path"]) for profile_id in PROFILE_ORDER
        },
        "profiles": build_profiles(definitions),
    }


def main() -> int:
    OUTPUT.write_text(
        json.dumps(build_output(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
