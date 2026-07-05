#!/usr/bin/env python3
"""Audit downstream live-read result records.

The default mode is safe before live testing: if no records exist, it reports
pending and exits successfully. Use --require-complete after approved live
checks to make pending or failed acceptance items fail the command.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[1]
DEFAULT_RECORDS_DIR = REPO / "evidence/unit-investigations/downstream-runs"
EXPECTED_SCHEMA = "downstream-unit-profile-read-checks/v1"

UNIT_PROFILES = {
    "melsec:iq-r:rj71en71": "R120PCPU + RJ71EN71",
    "melsec:qcpu:qj71e71-100": "Q12HCPU + QJ71E71-100",
    "melsec:qnu:qj71e71-100": "Q26UDEHCPU + QJ71E71-100",
    "melsec:qnudv:qj71e71-100": "Q06UDVCPU + QJ71E71-100",
    "melsec:lcpu:lj71e71-100": "L02SCPU + LJ71E71-100",
}

QJ_PROFILES = {
    "melsec:qcpu:qj71e71-100",
    "melsec:qnu:qj71e71-100",
    "melsec:qnudv:qj71e71-100",
}

RJ_PROFILES = {
    "melsec:iq-r:rj71en71",
}

IMPLEMENTATION_RESULTS = {
    ".NET": [".NET"],
    "Python": ["Python"],
    "Rust": ["Rust"],
    "Node-RED": ["Node-RED"],
    "C++ minimal": ["C++ minimal build", "C++ minimal read"],
}


@dataclass
class RecordAudit:
    records: int = 0
    valid_records: int = 0
    implementation_passes: dict[str, list[Path]] = field(default_factory=lambda: {name: [] for name in IMPLEMENTATION_RESULTS})
    qj_4e_records: list[Path] = field(default_factory=list)
    rj_4e_records: list[Path] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit downstream live-read JSON result records.")
    parser.add_argument("--records-dir", type=Path, default=DEFAULT_RECORDS_DIR)
    parser.add_argument(
        "--require-complete",
        action="store_true",
        help="Return non-zero unless all implementation and Q-series 4E acceptance items pass.",
    )
    return parser.parse_args()


def load_record(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"{path}: cannot read JSON: {exc}") from exc


def result_map(record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    results = record.get("results")
    if not isinstance(results, list):
        raise ValueError("results must be a list")
    mapped: dict[str, dict[str, Any]] = {}
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("each results item must be an object")
        name = item.get("name")
        if not isinstance(name, str):
            raise ValueError("each results item must have a string name")
        mapped[name] = item
    return mapped


def validate_record(path: Path, record: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if record.get("schema") != EXPECTED_SCHEMA:
        raise ValueError(f"{path}: schema must be {EXPECTED_SCHEMA}")
    profile = record.get("profile")
    if profile not in UNIT_PROFILES:
        raise ValueError(f"{path}: unknown unit profile {profile!r}")
    endpoint = record.get("endpoint")
    if not isinstance(endpoint, dict) or endpoint.get("transport") != "tcp":
        raise ValueError(f"{path}: endpoint must be TCP")
    read = record.get("read")
    if not isinstance(read, dict) or read.get("points") != 1 or read.get("unit") != "word":
        raise ValueError(f"{path}: read must be exactly one word")
    if record.get("approved_live_ok") is not True:
        raise ValueError(f"{path}: approved_live_ok must be true")
    if record.get("dry_run") is not False:
        raise ValueError(f"{path}: dry_run must be false")
    summary = record.get("summary")
    if not isinstance(summary, dict):
        raise ValueError(f"{path}: summary must be an object")
    if summary.get("commands") != 6:
        raise ValueError(f"{path}: summary.commands must be 6")
    return result_map(record)


def record_passes_all(results: dict[str, dict[str, Any]]) -> bool:
    for required in IMPLEMENTATION_RESULTS.values():
        for name in required:
            item = results.get(name)
            if item is None or not result_item_passes(item):
                return False
    return True


def result_item_passes(item: dict[str, Any]) -> bool:
    if item.get("exit_code") != 0 or item.get("status") != "pass":
        return False

    stdout = item.get("stdout")
    if not isinstance(stdout, str) or not stdout.strip():
        return True

    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return True

    if not isinstance(payload, dict):
        return True

    status = payload.get("status")
    if isinstance(status, str) and status.lower() not in {"ok", "pass", "success"}:
        return False
    return True


def audit_records(records_dir: Path) -> RecordAudit:
    audit = RecordAudit()
    paths = sorted(records_dir.glob("*.json")) if records_dir.is_dir() else []
    audit.records = len(paths)

    for path in paths:
        try:
            record = load_record(path)
            if record is None:
                continue
            results = validate_record(path, record)
        except ValueError as exc:
            audit.failures.append(str(exc))
            continue

        audit.valid_records += 1
        for implementation, required_names in IMPLEMENTATION_RESULTS.items():
            if all(result_item_passes(results.get(name, {})) for name in required_names):
                audit.implementation_passes[implementation].append(path)

        if record.get("profile") in QJ_PROFILES and record_passes_all(results):
            audit.qj_4e_records.append(path)
        if record.get("profile") in RJ_PROFILES and record_passes_all(results):
            audit.rj_4e_records.append(path)

    return audit


def print_summary(audit: RecordAudit, require_complete: bool) -> int:
    missing = [name for name, paths in audit.implementation_passes.items() if not paths]
    qj_status = "pass" if audit.qj_4e_records else "pending"
    rj_status = "pass" if audit.rj_4e_records else "pending"
    complete = not audit.failures and not missing and bool(audit.qj_4e_records) and bool(audit.rj_4e_records)

    if audit.failures:
        for failure in audit.failures:
            print(f"FAIL: {failure}", file=sys.stderr)

    if complete:
        print(
            "downstream-read-records-ok "
            f"records={audit.records} valid={audit.valid_records} implementations=5 q_series_4e=pass rj71en71_4e=pass"
        )
        return 0

    missing_text = ",".join(missing) if missing else "none"
    message = (
        "downstream-read-records-pending "
        f"records={audit.records} valid={audit.valid_records} "
        f"missing={missing_text} q_series_4e={qj_status} rj71en71_4e={rj_status}"
    )
    if require_complete or audit.failures:
        print(message, file=sys.stderr)
        return 1
    print(message)
    return 0


def main() -> int:
    args = parse_args()
    audit = audit_records(args.records_dir.resolve())
    return print_summary(audit, args.require_complete)


if __name__ == "__main__":
    raise SystemExit(main())
