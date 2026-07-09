#!/usr/bin/env python3
"""Audit saved live evidence for the Ethernet-unit profile decisions.

This reads existing evidence files only. It never opens a PLC connection.
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RESULTS = REPO / "evidence/unit-investigations/plans/results"
DEFINITIONS = REPO / "evidence/profile-definitions"
CAPABILITY_JSON = REPO / "capability/slmp_ethernet_profiles.json"


@dataclass(frozen=True)
class UnitEvidence:
    canonical_profile: str
    base_profile: str
    result_file: str
    definition_file: str
    expected_model: str
    expect_qj_link_direct: bool = False
    expect_lj_link_direct_partial: bool = False


UNIT_EVIDENCE = [
    UnitEvidence(
        canonical_profile="melsec:qcpu:qj71e71-100",
        base_profile="melsec:qcpu",
        result_file="qj71e71-100_q12hcpu.json",
        definition_file="qcpu_qj71e71-100_profile_definition.md",
        expected_model="Q12HCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:qnu:qj71e71-100",
        base_profile="melsec:qnu",
        result_file="qj71e71-100_q26udehcpu.json",
        definition_file="qnu_qj71e71-100_profile_definition.md",
        expected_model="Q26UDEHCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:qnudv:qj71e71-100",
        base_profile="melsec:qnudv",
        result_file="qj71e71-100_q06udvcpu.json",
        definition_file="qnudv_qj71e71-100_profile_definition.md",
        expected_model="Q06UDVCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:lcpu:lj71e71-100",
        base_profile="melsec:lcpu",
        result_file="lj71e71-100_l02scpu.json",
        definition_file="lcpu_lj71e71-100_profile_definition.md",
        expected_model="L02SCPU via LJ71E71-100",
        expect_lj_link_direct_partial=True,
    ),
]

RJ_PROFILE = UnitEvidence(
    canonical_profile="melsec:iq-r:rj71en71",
    base_profile="melsec:iq-r",
    result_file="rj71en71_r120pcpu.json",
    definition_file="iq-r_rj71en71_profile_definition.md",
    expected_model="R120PCPU via RJ71EN71",
)


@dataclass
class Audit:
    checks: int = 0
    failures: list[str] = field(default_factory=list)

    def check(self, condition: bool, message: str) -> None:
        self.checks += 1
        if not condition:
            self.failures.append(message)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_result(result_file: str) -> dict[str, Any]:
    return read_json(RESULTS / result_file)


def check_profile_definition_source_links(audit: Audit) -> None:
    for path in sorted(DEFINITIONS.glob("*_profile_definition*.md")):
        text = path.read_text(encoding="utf-8")
        dtype = re.search(r"\|\s*definition_type\s*\|\s*`?([^`|]+)`?\s*\|", text)
        source = re.search(r"\|\s*source_evidence\s*\|\s*`([^`]+)`\s*\|", text)
        if dtype and dtype.group(1).strip() == "live":
            audit.check(source is not None, f"{path.name}: live definition must have source_evidence")
        if source is None:
            continue
        source_path = source.group(1)
        audit.check(
            source_path.startswith("evidence/unit-investigations/plans/results/"),
            f"{path.name}: source_evidence must point to plans/results",
        )
        audit.check(source_path.endswith(".json"), f"{path.name}: source_evidence must point to result JSON")
        audit.check(not re.search(r"20\d{6}", Path(source_path).name), f"{path.name}: source_evidence filename must not contain a date")
        json_path = REPO / source_path
        audit.check(json_path.is_file(), f"{path.name}: missing source_evidence JSON {source_path}")
        audit.check(json_path.with_suffix(".md").is_file(), f"{path.name}: missing generated summary MD for {source_path}")


def result_by_id(result: dict[str, Any], item_id: str) -> dict[str, Any]:
    for item in result.get("results", []):
        if item.get("id") == item_id:
            return item
    raise KeyError(item_id)


def check_common_result_health(audit: Audit, result: dict[str, Any], label: str) -> None:
    audit.check(result.get("errors") == [], f"{label}: results.json must have no errors")
    audit.check(result.get("waived") == [], f"{label}: results.json must have no waived required items")
    audit.check(
        result.get("started_items") == result.get("recorded_items"),
        f"{label}: recorded_items must match started_items",
    )


def check_boundary(
    audit: Audit,
    result: dict[str, Any],
    item_id: str,
    expected_max: int,
    expected_over: str,
    label: str,
) -> None:
    item = result_by_id(result, item_id)
    audit.check(item.get("status") == "limit", f"{label}: {item_id} must be a measured limit")
    audit.check(item.get("largest_pass") == expected_max, f"{label}: {item_id} largest_pass mismatch")
    audit.check(item.get("fail_end") == expected_over, f"{label}: {item_id} fail_end mismatch")


def check_limit_against_profile(
    audit: Audit,
    result: dict[str, Any],
    profile: dict[str, Any],
    limit_name: str,
    result_id: str,
    label: str,
) -> None:
    limit = profile["limits"][limit_name]
    if limit.get("source") != "live":
        audit.check(limit.get("source") == "inferred", f"{label}: {limit_name} must be live or inferred")
        return
    check_boundary(audit, result, result_id, limit["max"], limit["over_end_code"], label)


def check_unit_profile(audit: Audit, canonical: dict[str, Any], unit: UnitEvidence) -> None:
    label = unit.canonical_profile
    result = load_result(unit.result_file)
    profile = canonical["profiles"][unit.canonical_profile]

    check_common_result_health(audit, result, label)
    result_profile = result["profile"]
    audit.check(result_profile.get("profile") == unit.base_profile, f"{label}: result base profile mismatch")
    audit.check(result_profile.get("frame") == "4E", f"{label}: saved result must use 4E")
    audit.check(result_profile.get("compat") == "Q/L", f"{label}: saved result must use Q/L compatibility")
    audit.check(
        result_profile.get("subcommands") == {"word": "0000", "bit": "0001", "ext_word": "0080", "ext_bit": "0081"},
        f"{label}: saved result must use Q/L 4E subcommands",
    )

    audit.check(profile.get("base_profile") == unit.base_profile, f"{label}: canonical base_profile mismatch")
    audit.check(profile.get("frame") == "4E", f"{label}: canonical frame mismatch")
    audit.check(profile.get("compat") == "Q/L", f"{label}: canonical compat mismatch")
    audit.check(profile.get("scope") == "ethernet-unit", f"{label}: canonical scope mismatch")
    audit.check(unit.expected_model in profile.get("verified_models", []), f"{label}: verified_models missing model")

    definition_path = DEFINITIONS / unit.definition_file
    audit.check(definition_path.is_file(), f"{label}: missing definition file")
    if definition_path.is_file():
        definition = definition_path.read_text(encoding="utf-8")
        audit.check(unit.canonical_profile in definition, f"{label}: definition missing canonical profile")
        audit.check(unit.expected_model in definition, f"{label}: definition missing verified model")
        audit.check("4E + Q/L works" in definition, f"{label}: definition missing frame decision")
        audit.check(
            f"evidence/unit-investigations/plans/results/{unit.result_file}" in definition,
            f"{label}: source_evidence must point to the canonical result JSON",
        )
        if unit.expect_lj_link_direct_partial:
            audit.check("J2\\W100" in definition, f"{label}: definition must mention latest J\\W target")
            audit.check("J2\\B10" in definition and "4031" in definition, f"{label}: definition must record J\\B NG")

    audit.check(result_by_id(result, "type_name").get("end_code") == "0000", f"{label}: type_name must pass")
    audit.check(result_by_id(result, "block_read").get("end_code") == "0000", f"{label}: block_read must pass")
    audit.check(result_by_id(result, "block_write").get("end_code") == "0000", f"{label}: block_write must pass")

    check_limit_against_profile(audit, result, profile, "direct_word_read", "boundary_direct_read_word", label)
    check_limit_against_profile(audit, result, profile, "direct_word_write", "boundary_direct_write_word", label)
    check_limit_against_profile(audit, result, profile, "direct_bit_read", "boundary_direct_read_bit", label)
    check_limit_against_profile(audit, result, profile, "direct_bit_write", "boundary_direct_write_bit", label)
    check_limit_against_profile(audit, result, profile, "random_read_word", "boundary_random_read_word", label)
    check_limit_against_profile(audit, result, profile, "random_write_word", "boundary_random_write_word", label)
    check_limit_against_profile(audit, result, profile, "random_write_bit", "boundary_random_write_bit", label)
    check_limit_against_profile(audit, result, profile, "random_read_word_ext", "boundary_random_read_word_ext", label)
    check_limit_against_profile(audit, result, profile, "random_write_word_ext", "boundary_random_write_word_ext", label)
    check_limit_against_profile(audit, result, profile, "monitor_register_word_ext", "boundary_monitor_register_ext", label)
    if "random_write_bit_ext" in profile["limits"]:
        check_limit_against_profile(audit, result, profile, "random_write_bit_ext", "boundary_random_write_bit_ext", label)

    routes = result_by_id(result, "ext_read_routes").get("routes", {})
    audit.check(routes.get("U\\G") == "0000", f"{label}: U\\G route must pass on measured unit configuration")
    if unit.expect_qj_link_direct:
        for route in ["J\\X", "J\\Y", "J\\B", "J\\W", "J\\SB", "J\\SW"]:
            audit.check(routes.get(route) == "0000", f"{label}: {route} route must pass on measured QJ setup")
    if unit.expect_lj_link_direct_partial:
        for route in ["J\\X", "J\\Y", "J\\W", "J\\SB", "J\\SW"]:
            audit.check(routes.get(route) == "0000", f"{label}: {route} route must pass on measured LJ setup")
        audit.check(routes.get("J\\B") not in (None, "0000"), f"{label}: J\\B route must remain non-positive")
        jw_read = result_by_id(result, "boundary_random_read_word_ext_jw")
        jw_write = result_by_id(result, "boundary_random_write_word_ext_jw")
        jw_weighted = result_by_id(result, "boundary_random_write_word_weighted_ext_jw")
        audit.check(jw_read.get("status") == "limit" and jw_read.get("largest_pass") == 192, f"{label}: J\\W read ext limit mismatch")
        audit.check(jw_write.get("status") == "limit" and jw_write.get("largest_pass") == 160, f"{label}: J\\W write ext limit mismatch")
        audit.check(
            jw_weighted.get("status") == "limit" and jw_weighted.get("largest_pass") == 137,
            f"{label}: J\\W weighted ext limit mismatch",
        )


def check_rj_unit_profile(audit: Audit, canonical: dict[str, Any]) -> None:
    label = RJ_PROFILE.canonical_profile
    result = load_result(RJ_PROFILE.result_file)
    iqr = canonical["profiles"]["melsec:iq-r"]
    profile = canonical["profiles"][RJ_PROFILE.canonical_profile]

    check_common_result_health(audit, result, label)
    result_profile = result["profile"]
    audit.check(result_profile.get("profile") == "melsec:iq-r", f"{label}: result profile mismatch")
    audit.check(result_profile.get("frame") == "4E", f"{label}: frame mismatch")
    audit.check(result_profile.get("compat") == "iQ-R", f"{label}: compat mismatch")
    audit.check(profile.get("base_profile") == "melsec:iq-r", f"{label}: canonical base_profile mismatch")
    audit.check(profile.get("frame") == "4E", f"{label}: canonical frame mismatch")
    audit.check(profile.get("compat") == "iQ-R", f"{label}: canonical compat mismatch")
    audit.check(profile.get("scope") == "ethernet-unit", f"{label}: canonical scope mismatch")
    audit.check("R120PCPU via RJ71EN71" in profile.get("verified_models", []), f"{label}: verified model missing")

    definition_path = DEFINITIONS / RJ_PROFILE.definition_file
    audit.check(definition_path.is_file(), f"{label}: missing definition file")
    if definition_path.is_file():
        definition = definition_path.read_text(encoding="utf-8")
        audit.check(RJ_PROFILE.canonical_profile in definition, f"{label}: definition missing canonical profile")
        audit.check(RJ_PROFILE.expected_model in definition, f"{label}: definition missing verified model")
        audit.check("Add alias unit profile" in definition, f"{label}: definition missing alias decision")
        audit.check(
            f"evidence/unit-investigations/plans/results/{RJ_PROFILE.result_file}" in definition,
            f"{label}: source_evidence must point to the canonical result JSON",
        )

    type_name = result_by_id(result, "type_name")
    audit.check(type_name.get("end_code") == "0000", f"{label}: type_name must pass")
    audit.check(type_name.get("text") == "R120PCPU", f"{label}: type_name must identify R120PCPU")
    audit.check(result_by_id(result, "write_policy_s").get("end_codes") == ["4030"], f"{label}: S write policy evidence mismatch")

    for limit_name, result_id in [
        ("direct_word_read", "boundary_direct_read_word"),
        ("direct_word_write", "boundary_direct_write_word"),
        ("direct_bit_read", "boundary_direct_read_bit"),
        ("direct_bit_write", "boundary_direct_write_bit"),
        ("random_read_word", "boundary_random_read_word"),
        ("random_write_word", "boundary_random_write_word"),
        ("random_write_bit", "boundary_random_write_bit"),
        ("random_read_word_ext", "boundary_random_read_word_ext"),
        ("random_write_word_ext", "boundary_random_write_word_ext"),
        ("random_write_bit_ext", "boundary_random_write_bit_ext"),
        ("monitor_register_word_ext", "boundary_monitor_register_ext"),
    ]:
        check_limit_against_profile(audit, result, iqr, limit_name, result_id, label)
        audit.check(
            profile["limits"][limit_name]["max"] == iqr["limits"][limit_name]["max"],
            f"{label}: {limit_name} max must inherit iQ-R value",
        )


def main() -> int:
    canonical = read_json(CAPABILITY_JSON)
    audit = Audit()

    check_profile_definition_source_links(audit)
    for unit in UNIT_EVIDENCE:
        check_unit_profile(audit, canonical, unit)
    check_rj_unit_profile(audit, canonical)

    if audit.failures:
        for failure in audit.failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        print(f"unit-profile-source-evidence-audit-failed checks={audit.checks} failures={len(audit.failures)}", file=sys.stderr)
        return 1

    print(f"unit-profile-source-evidence-audit-ok checks={audit.checks}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
