#!/usr/bin/env python3
"""Generate device range JSON from the Markdown definition file."""

from __future__ import annotations

import json
import copy
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_MD = ROOT / "device-ranges" / "slmp_device_range_rules.md"
OUTPUT_JSON = ROOT / "device-ranges" / "slmp_device_range_rules.json"


def split_md_row(line: str) -> list[str]:
    text = line.strip()
    if text.startswith("|"):
        text = text[1:]
    if text.endswith("|"):
        text = text[:-1]

    cells: list[str] = []
    current: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] == "|":
            current.append("|")
            index += 2
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    cells.append("".join(current).strip())
    return cells


def parse_table(lines: list[str]) -> list[dict[str, str]]:
    rows = [split_md_row(line) for line in lines if line.strip().startswith("|")]
    if len(rows) < 2:
        return []
    headers = rows[0]
    data_rows = rows[2:]
    return [
        {header: row[index] if index < len(row) else "" for index, header in enumerate(headers)}
        for row in data_rows
        if any(cell.strip() for cell in row)
    ]


def table_after_heading(lines: list[str], heading: str) -> list[dict[str, str]]:
    heading_line = f"## {heading}"
    subheading_line = f"### {heading}"
    start = None
    for index, line in enumerate(lines):
        if line.strip() in {heading_line, subheading_line}:
            start = index + 1
            break
    if start is None:
        raise ValueError(f"Missing heading: {heading}")

    table_lines: list[str] = []
    in_table = False
    for line in lines[start:]:
        if line.startswith("#") and not in_table:
            break
        if line.strip().startswith("|"):
            table_lines.append(line)
            in_table = True
            continue
        if in_table:
            break
    if not table_lines:
        raise ValueError(f"Missing table after heading: {heading}")
    return parse_table(table_lines)


def parse_int(value: str) -> int:
    return int(value.strip())


def parse_profile_list(value: str) -> list[str]:
    if not value or value == "-":
        return []
    return [part.strip() for part in value.split(",") if part.strip()]


def parse_parameter_value(value: str) -> int | str:
    return parse_int(value) if re.fullmatch(r"\d+", value) else value


def parse_parameters(value: str) -> dict[str, int | str]:
    if not value or value == "-":
        return {}
    parameters: dict[str, int | str] = {}
    for part in [part.strip() for part in value.split(";") if part.strip()]:
        key, separator, raw_value = part.partition("=")
        if not separator:
            raise ValueError(f"Invalid parameter field: {part}")
        parameters[key.strip()] = parse_parameter_value(raw_value.strip())
    return parameters


def parse_device_type(kind: str) -> str:
    device_type = kind.strip()
    if device_type not in {"bit", "word", "dword"}:
        raise ValueError(f"Invalid device type: {kind}")
    return device_type


def parse_devices(symbol: str, value: str) -> list[dict[str, Any]]:
    devices: list[dict[str, Any]] = []
    if ":" not in value:
        device_type = parse_device_type(value)
        return [{"device": symbol, "type": device_type, "is_bit": device_type == "bit"}]

    for part in parse_profile_list(value):
        name, _, kind = part.partition(":")
        device_type = parse_device_type(kind)
        if not name:
            raise ValueError(f"Invalid device descriptor: {part}")
        devices.append({"device": name, "type": device_type, "is_bit": device_type == "bit"})
    return devices


def parse_rule_cell(value: str) -> dict[str, Any]:
    parts = [part.strip() for part in value.split(";") if part.strip()]
    if not parts:
        raise ValueError("Empty rule cell")

    kind_aliases = {
        "word": "word-register",
        "dword": "dword-register",
        "word-clipped": "word-register-clipped",
        "dword-clipped": "dword-register-clipped",
    }
    fixed_match = re.fullmatch(r"fixed=(\d+)", parts[0])
    if fixed_match:
        rule: dict[str, Any] = {
            "kind": "fixed",
            "fixed_value": parse_int(fixed_match.group(1)),
        }
    else:
        clipped_match = re.fullmatch(r"(word-clipped|dword-clipped)=(\d+)", parts[0])
        if clipped_match:
            rule = {
                "kind": kind_aliases[clipped_match.group(1)],
                "clip_value": parse_int(clipped_match.group(2)),
            }
        else:
            rule = {"kind": kind_aliases.get(parts[0], parts[0])}

    fields: dict[str, str] = {}
    for part in parts[1:]:
        key, separator, raw_value = part.partition("=")
        if not separator:
            if part == "probe":
                rule["probe"] = True
                continue
            raise ValueError(f"Invalid rule flag: {part}")
        fields[key.strip()] = raw_value.strip()

    if "register" in fields:
        rule["register"] = parse_int(fields["register"])
    elif "source" in fields:
        register_match = re.fullmatch(r"SD(\d+)", fields["source"])
        if register_match:
            rule["register"] = parse_int(register_match.group(1))
    if "fixed_value" in fields:
        rule["fixed_value"] = parse_int(fields["fixed_value"])
    if "clip_value" in fields:
        rule["clip_value"] = parse_int(fields["clip_value"])
    return rule


def build_json(lines: list[str]) -> dict[str, Any]:
    metadata = {row["Item"]: row["Value"] for row in table_after_heading(lines, "Metadata")}

    row_metadata = table_after_heading(lines, "Device Families")
    rows = {
        row["Symbol"]: {
            "classification": row["Classification"],
            "device_name": row["Device name"],
            "devices": parse_devices(row["Symbol"], row["Type"]),
            "notation": row["Notation"],
        }
        for row in row_metadata
    }

    notation_overrides: dict[str, dict[str, str]] = {}
    for row in table_after_heading(lines, "Notation Overrides"):
        profile = row["Profile"]
        family = row["Device family"]
        notation = row["Notation"]
        if profile == "-" or family == "-" or notation == "-":
            continue
        notation_overrides.setdefault(profile, {})[family] = notation

    runtime_probe_meta = {
        row["Item"]: row["Value"]
        for row in table_after_heading(lines, "Runtime Probe Metadata")
    }
    runtime_probe_steps = []
    for row in table_after_heading(lines, "Runtime Probe Steps"):
        step: dict[str, Any] = {
            "order": parse_int(row["Order"]),
            "profiles": parse_profile_list(row["Profiles"]),
            "family": row["Family"],
            "method": row["Method"],
        }
        parameters = parse_parameters(row.get("Parameters", ""))
        if parameters:
            step["parameters"] = parameters
        runtime_probe_steps.append(step)

    profile_blocks: dict[str, dict[str, Any]] = {}
    for row in table_after_heading(lines, "Profile Blocks"):
        block: dict[str, Any] = {
            "register_start": parse_int(row["Register start"]),
            "register_count": parse_int(row["Register count"]),
            "rules": {},
        }
        base_profile = row.get("Base profile", "").strip()
        if base_profile and base_profile != "-":
            block["base_profile"] = base_profile
        profile_blocks[row["Profile"]] = block

    rule_rows = table_after_heading(lines, "Rule Matrix")
    ordered_items = [row["Device family"] for row in rule_rows]
    profile_ids = list(profile_blocks)
    matrix_profile_ids = [profile_id for profile_id in profile_ids if profile_id in rule_rows[0]]
    for row in rule_rows:
        family = row["Device family"]
        if family not in rows:
            raise ValueError(f"Rule Matrix family is missing from Device Families: {family}")
        for profile_id in matrix_profile_ids:
            profile_blocks[profile_id]["rules"][family] = parse_rule_cell(row[profile_id])
    for profile_id, block in profile_blocks.items():
        base_profile = block.get("base_profile")
        if not base_profile:
            continue
        if base_profile not in profile_blocks:
            raise ValueError(f"{profile_id}: unknown base profile {base_profile}")
        block["rules"] = copy.deepcopy(profile_blocks[base_profile]["rules"])

    return {
        "schema_version": parse_int(metadata["schema_version"]),
        "date": metadata["date"],
        "ordered_items": ordered_items,
        "rows": rows,
        "notation_overrides": notation_overrides,
        "runtime_probes": {
            "applies_to": parse_profile_list(runtime_probe_meta["applies_to"]),
            "max_probe_count": parse_int(runtime_probe_meta["max_probe_count"]),
            "steps": runtime_probe_steps,
        },
        "profiles": profile_blocks,
    }


def main() -> None:
    lines = SOURCE_MD.read_text(encoding="utf-8").splitlines()
    data = build_json(lines)
    OUTPUT_JSON.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
