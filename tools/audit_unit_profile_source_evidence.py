#!/usr/bin/env python3
"""Audit saved live evidence for the Ethernet-unit profile decisions.

This reads existing evidence files only. It never opens a PLC connection.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
RUNS = REPO / "evidence/unit-investigations/plans/runs"
DEFINITIONS = REPO / "evidence/profile-definitions"
CAPABILITY_JSON = REPO / "capability/slmp_builtin_ethernet_profiles.json"


@dataclass(frozen=True)
class UnitEvidence:
    canonical_profile: str
    base_profile: str
    run_dir: str
    definition_file: str
    expected_model: str
    expect_qj_link_direct: bool = False
    expect_lj_link_direct_config_absent: bool = False


UNIT_EVIDENCE = [
    UnitEvidence(
        canonical_profile="melsec:qcpu:qj71e71-100",
        base_profile="melsec:qcpu",
        run_dir="qj71e71-100_q12hcpu_20260705_012948",
        definition_file="qcpu_qj71e71-100_slmp_profile_definition_20260705.md",
        expected_model="Q12HCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:qnu:qj71e71-100",
        base_profile="melsec:qnu",
        run_dir="qj71e71-100_q26udehcpu_20260705_013641",
        definition_file="qnu_qj71e71-100_slmp_profile_definition_20260705.md",
        expected_model="Q26UDEHCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:qnudv:qj71e71-100",
        base_profile="melsec:qnudv",
        run_dir="qj71e71-100_q06udvcpu_20260705_012302",
        definition_file="qnudv_qj71e71-100_slmp_profile_definition_20260705.md",
        expected_model="Q06UDVCPU via QJ71E71-100",
        expect_qj_link_direct=True,
    ),
    UnitEvidence(
        canonical_profile="melsec:lcpu:lj71e71-100",
        base_profile="melsec:lcpu",
        run_dir="lj71e71-100_l02scpu_20260705_015031",
        definition_file="lcpu_lj71e71-100_slmp_profile_definition_20260705.md",
        expected_model="L02SCPU via LJ71E71-100",
        expect_lj_link_direct_config_absent=True,
    ),
]

RJ_PROFILE = UnitEvidence(
    canonical_profile="melsec:iq-r:rj71en71",
    base_profile="melsec:iq-r",
    run_dir="rj71en71_r120pcpu_20260705_022520",
    definition_file="iq-r_rj71en71_slmp_profile_definition_20260705.md",
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


def load_result(run_dir: str) -> dict[str, Any]:
    return read_json(RUNS / run_dir / "results.json")


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
    result = load_result(unit.run_dir)
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
        audit.check("source_evidence" in definition, f"{label}: definition missing source_evidence")

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
    if unit.expect_lj_link_direct_config_absent:
        for route in ["J\\X", "J\\Y", "J\\B", "J\\W", "J\\SB", "J\\SW"]:
            audit.check(routes.get(route) not in (None, "0000"), f"{label}: {route} route must remain config-dependent")


def check_rj_unit_profile(audit: Audit, canonical: dict[str, Any]) -> None:
    label = RJ_PROFILE.canonical_profile
    result = load_result("rj71en71_r120pcpu_20260705_022520")
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
        audit.check("source_evidence" in definition, f"{label}: definition missing source_evidence")

    decision_path = DEFINITIONS / "rj71en71_slmp_unit_profile_decision_20260705.md"
    audit.check(decision_path.is_file(), f"{label}: missing superseded decision file")
    if decision_path.is_file():
        decision = decision_path.read_text(encoding="utf-8")
        audit.check("superseded" in decision.lower(), f"{label}: decision must be marked superseded")
        audit.check("melsec:iq-r:rj71en71" in decision, f"{label}: decision missing new canonical profile")

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
