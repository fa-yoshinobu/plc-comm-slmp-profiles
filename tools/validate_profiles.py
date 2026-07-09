#!/usr/bin/env python3
"""Validate canonical SLMP profile JSON files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_JSON = ROOT / "capability" / "slmp_ethernet_profiles.json"
DEVICE_RANGES_JSON = ROOT / "device-ranges" / "slmp_device_range_rules.json"
PROFILE_ORDER = [
    "melsec:iq-r",
    "melsec:iq-r:rj71en71",
    "melsec:iq-l",
    "melsec:mx-r",
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

BASE_LIMIT_KEYS = {
    "direct_word_read",
    "direct_word_write",
    "direct_bit_read",
    "direct_bit_write",
    "random_read_word",
    "random_write_word",
    "random_write_bit",
    "random_read_word_ext",
    "random_write_word_ext",
    "random_write_bit_ext",
}
MONITOR_LIMIT_KEYS = {
    "monitor_register_word",
    "monitor_register_word_ext",
}


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_keys)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def validate_capability(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == 1, "capability schema_version must be 1")
    require(payload.get("scope") == "slmp-ethernet-port", "unexpected capability scope")
    profiles = payload.get("profiles")
    require(isinstance(profiles, dict), "profiles must be an object")
    require(list(profiles) == PROFILE_ORDER, "profile order changed unexpectedly")

    evidence_files = payload.get("evidence_files")
    require(isinstance(evidence_files, dict), "evidence_files must be an object")
    require(set(evidence_files) == set(PROFILE_ORDER), "evidence_files must match profile IDs")

    for profile_id, profile in profiles.items():
        require(profile.get("display_name"), f"{profile_id}: display_name is required")
        require(
            profile.get("scope") in {"builtin-ethernet-port", "ethernet-unit", "base-profile"},
            f"{profile_id}: invalid profile scope",
        )
        base = profile.get("base_profile")
        if base is not None:
            require(base in profiles, f"{profile_id}: base_profile must reference an existing profile")
            require(base != profile_id, f"{profile_id}: base_profile cannot reference itself")
        role = profile.get("role")
        if role is not None:
            require(role == "base", f"{profile_id}: invalid role")
            require(profile.get("scope") == "base-profile", f"{profile_id}: base role requires base-profile scope")
        require(profile.get("frame") in {"3E", "4E"}, f"{profile_id}: invalid frame")
        require(isinstance(profile.get("compat"), str) and profile["compat"], f"{profile_id}: compat required")
        subcommands = profile.get("subcommands")
        require(isinstance(subcommands, dict), f"{profile_id}: subcommands required")
        require(set(subcommands) == {"word", "bit", "ext_word", "ext_bit"}, f"{profile_id}: bad subcommands")
        require(isinstance(profile.get("verified_models"), list), f"{profile_id}: verified_models must be list")
        features = profile.get("features")
        require(isinstance(features, dict), f"{profile_id}: features required")
        for key, feature in features.items():
            require(feature.get("state") in payload["policy"]["state_semantics"], f"{profile_id}/{key}: bad state")
            require(isinstance(feature.get("source"), str) and feature["source"], f"{profile_id}/{key}: source")
        limits = profile.get("limits")
        require(isinstance(limits, dict), f"{profile_id}: limits required")
        expected_limit_keys = set(BASE_LIMIT_KEYS)
        expected_limit_keys.update(MONITOR_LIMIT_KEYS)
        require(
            set(limits) == expected_limit_keys,
            f"{profile_id}: limits keys must match expected set; "
            f"missing={sorted(expected_limit_keys - set(limits))}, "
            f"extra={sorted(set(limits) - expected_limit_keys)}",
        )
        for key, limit in limits.items():
            require(isinstance(limit.get("source"), str) and limit["source"], f"{profile_id}/{key}: limit source")
            if "max" in limit:
                require(isinstance(limit["max"], int), f"{profile_id}/{key}: max must be int")
            if "weighted_max" in limit:
                require(isinstance(limit["weighted_max"], int), f"{profile_id}/{key}: weighted_max must be int")
        require(isinstance(profile.get("write_policy"), dict), f"{profile_id}: write_policy required")


def validate_device_ranges(payload: dict[str, Any]) -> None:
    require(payload.get("schema_version") == 1, "device range schema_version must be 1")
    profiles = payload.get("profiles")
    require(isinstance(profiles, dict), "device range profiles must be an object")
    require(set(profiles) == set(PROFILE_ORDER), "device range profiles must match capability IDs")


def main() -> int:
    validate_capability(load_json(CAPABILITY_JSON))
    validate_device_ranges(load_json(DEVICE_RANGES_JSON))
    print(f"validated {CAPABILITY_JSON.relative_to(ROOT)}")
    print(f"validated {DEVICE_RANGES_JSON.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
