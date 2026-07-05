# Unit Profile Goal Acceptance Matrix

Date: 2026-07-05

Scope: acceptance audit for `D:\APP\unit_profiles_goal_20260704.md`.
This matrix separates completed non-live work from live PLC and publication
items that still require explicit user approval.

## Current Status

Overall state: non-live implementation, documentation, generated artifacts, and
CI gates are complete in the local worktrees. All four new Ethernet-unit
downstream live patterns, QCPU + QJ71E71-100, QnU + QJ71E71-100,
QnUDV + QJ71E71-100, and LCPU + LJ71E71-100, have passed across all five
implementations. The goal is not complete only because publication steps are
still pending.

An iQ-R built-in Ethernet read-only connectivity smoke was run later on
2026-07-05 and passed, but it is not QJ71E71-100/LJ71E71-100 unit-profile
acceptance evidence.

An LCPU built-in Ethernet read-only 5-implementation smoke was also run later
on 2026-07-05 and passed, but it is not LJ71E71-100 unit-profile acceptance
evidence.

An RJ71EN71 iQ-R read-only 5-implementation smoke was also run later on
2026-07-05 and passed. It supports the no-new-profile decision for RJ71EN71,
but it is not QJ71E71-100/LJ71E71-100 unit-profile acceptance evidence.

A QnUDV + QJ71E71-100 read-only 5-implementation acceptance run was then
completed with `melsec:qnudv:qj71e71-100`. It satisfies the Q-series E71
downstream 4E evidence item for a new unit profile.

An LCPU + LJ71E71-100 read-only 5-implementation acceptance run was also
completed with `melsec:lcpu:lj71e71-100`. It satisfies the LJ71E71-100
downstream acceptance pattern.

A QCPU + QJ71E71-100 read-only 5-implementation acceptance run was also
completed with `melsec:qcpu:qj71e71-100`.

A QnU + QJ71E71-100 read-only 5-implementation acceptance run was also
completed with `melsec:qnu:qj71e71-100`.

All per-profile live implementation patterns are now complete.

## GOAL-0 Invariants

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Do not create profiles without measured evidence. | PASS | QJ/LJ unit profiles are backed by `evidence/unit-investigations/plans/runs/*/results.json` and definition files in `evidence/profile-definitions/`. RJ71EN71 has a no-new-profile decision file. `python tools\audit_unit_profile_source_evidence.py` passed with `unit-profile-source-evidence-audit-ok checks=283`. |
| Do not retag an existing release; use v1.2.0 for the new wave. | PARTIAL | The five downstream `scripts/update_slmp_profile_jsons.ps1` files default to `v1.2.0`. The actual tag/push is not performed yet. |
| Live checks default to read-only unless explicitly approved. | PASS | `downstream_unit_profile_read_checks_20260705.md` contains a read-only downstream plan. `tools/run_downstream_read_checks.py` defaults to dry-run, requires `--execute --approved-live-ok` for live execution, and does not create `--record-json` output unless the live gate is approved. `tools/audit_downstream_read_records.py --require-complete` reports `downstream-read-records-ok records=5 valid=5 implementations=5 q_series_4e=pass` after the approved QJ71E71-100/LJ71E71-100 runs. |
| Device ranges and point limits stay shared with the base profile unless evidence requires otherwise. | PASS | `python tools\validate_profiles.py` passed after regenerating capability/device-range artifacts. `python tools\audit_unit_profile_rollout.py` passed with `checks=211`. |

## GOAL-1 Difference Evidence

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Evidence JSON and definition/decision records exist for RJ71EN71, QJ71E71-100, and LJ71E71-100. | PASS | `rj71en71_r120pcpu_20260705_022520/results.json`, `qj71e71-100_q12hcpu_20260705_012948/results.json`, `qj71e71-100_q26udehcpu_20260705_013641/results.json`, `qj71e71-100_q06udvcpu_20260705_012302/results.json`, and `lj71e71-100_l02scpu_20260705_015031/results.json`; definition/decision files in `evidence/profile-definitions/`; source-evidence audit passed. |
| Each unit has a difference/no-difference decision record. | PASS | `rj71en71_slmp_unit_profile_decision_20260705.md`, `qcpu_qj71e71-100_slmp_profile_definition_20260705.md`, `qnu_qj71e71-100_slmp_profile_definition_20260705.md`, `qnudv_qj71e71-100_slmp_profile_definition_20260705.md`, and `lcpu_lj71e71-100_slmp_profile_definition_20260705.md`. |
| Q/L Ethernet units include 4E communication evidence. | PASS | QJ71E71-100 and LJ71E71-100 plan-run evidence records are represented in the profile-definition files and canonical JSON as `frame=4E`, `compat=Q/L`. `audit_unit_profile_source_evidence.py` confirms the saved results used 4E + Q/L subcommands. |

## GOAL-2 Canonical Profiles

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Difference-bearing units are present in capability JSON. | PASS | `capability/slmp_builtin_ethernet_profiles.json` contains `melsec:qcpu:qj71e71-100`, `melsec:qnu:qj71e71-100`, `melsec:qnudv:qj71e71-100`, and `melsec:lcpu:lj71e71-100`. |
| RJ71EN71 stays on the base iQ-R profile with verified model evidence. | PASS | `melsec:iq-r` includes `R120PCPU via RJ71EN71` in `verified_models`; `rj71en71_slmp_unit_profile_decision_20260705.md` records the no-new-profile decision; `rj71en71_iq-r_downstream_5impl_smoke_20260705.md` shows all five downstream implementations can read through RJ71EN71 with `melsec:iq-r`. |
| `melsec:qcpu` is base-only while `melsec:qcpu:qj71e71-100` remains selectable. | PASS | Canonical JSON has `melsec:qcpu` as `role=base`, `scope=base-profile`; audit confirms the successor profile is selectable and inherits address behavior from `melsec:qcpu`. |
| Profile scope expression matches the mixed built-in/unit reality. | PASS | Canonical JSON uses per-profile `scope` values: built-in profiles use `builtin-ethernet-port`, unit profiles use `ethernet-unit`, and `melsec:qcpu` uses `base-profile`. |
| Generated comparison tables and device-range rules are current. | PASS | Ran `generate_capability_profiles.py`, `generate_device_range_rules.py`, `generate_profile_tables.py`, and `validate_profiles.py` successfully. |

## GOAL-3 Downstream And Docs

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Five downstream implementations have the new profiles and v1.2.0 fixture refs. | PASS | `tools/audit_unit_profile_rollout.py` passed with `unit-profile-rollout-audit-ok checks=211`. |
| Five implementation CI gates pass. | PASS | `.NET cmd /c run_ci.bat` passed with 258 tests on net8.0/net9.0/net10.0; Python ruff/mypy/API-doc/pytest passed with 273 tests; Rust `cargo fmt --check` and `cargo test` passed; Node-RED `npm test` passed with 111 tests; C++ `cmd /c run_ci.bat` and `check_device_range_catalog_parity.py` passed. |
| New profile read-only live read passes once per implementation. | PASS | QCPU + QJ71E71-100 passed for all five implementations with `melsec:qcpu:qj71e71-100`: `qcpu_qj71e71-100_downstream_5impl_read_20260705.md` and `downstream-runs/qcpu_qj71e71-100_20260705.json`. QnU + QJ71E71-100 passed for all five implementations with `melsec:qnu:qj71e71-100`: `qnu_qj71e71-100_downstream_5impl_read_20260705.md` and `downstream-runs/qnu_qj71e71-100_20260705.json`. QnUDV + QJ71E71-100 passed for all five implementations with `melsec:qnudv:qj71e71-100`: `qnudv_qj71e71-100_downstream_5impl_read_20260705.md`. Initial transient failures are preserved in `downstream-runs/qnudv_qj71e71-100_20260705.json`; the successful retry consolidation is `downstream-runs/qnudv_qj71e71-100_20260705_retry_success.json`. LCPU + LJ71E71-100 passed for all five implementations with `melsec:lcpu:lj71e71-100`: `lcpu_lj71e71-100_downstream_5impl_read_20260705.md` and `downstream-runs/lcpu_lj71e71-100_20260705.json`. |
| Q-series E71 + new profile has downstream 4E live communication evidence. | PASS | `melsec:qcpu:qj71e71-100`, `melsec:qnu:qj71e71-100`, and `melsec:qnudv:qj71e71-100` via QJ71E71-100 passed in .NET, Python, Rust, Node-RED, and C++ minimal. Node-RED reported `frameType=4e`, `plcSeries=ql`; C++ reported `frame=4E`, `compat=Q/L`. `python tools\audit_downstream_read_records.py --records-dir evidence\unit-investigations\downstream-runs --require-complete` reports `downstream-read-records-ok records=5 valid=5 implementations=5 q_series_4e=pass`. |
| docs-site collect and strict build pass. | PASS | Ran `python scripts\collect_docs.py --source-root D:\APP --docs-root docs` and `python -m mkdocs build --strict` successfully. |
| Settings pages, PROFILES pages, and comparison tables agree on profile names. | PASS | `tools/audit_unit_profile_rollout.py` covers docs-site QJ/LJ pages and all five downstream `PROFILES.md` pages. |
| `melsec:qcpu` is hidden/rejected as a connection profile and still usable as an inherited range/address base. | PASS | Audit confirms user docs and Node-RED options. Unit tests in .NET, Python, Rust, and Node-RED cover rejection; C++ CI covers the minimal API behavior and fixture parity. |

## Publication

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Create/push `plc-comm-slmp-profiles` v1.2.0 tag. | PENDING | Not performed because publication requires explicit user instruction. |
| Commit/push five downstream repos and docs-site. | PENDING | Not performed because GitHub publication requires explicit user instruction. |

## Non-Live Verification Commands

Latest successful non-live verification set:

```powershell
python tools\generate_capability_profiles.py
python tools\generate_device_range_rules.py
python tools\generate_profile_tables.py
python tools\validate_profiles.py
python tools\audit_unit_profile_rollout.py
python tools\audit_unit_profile_source_evidence.py
python tools\audit_downstream_read_records.py
```

```powershell
cmd /c run_ci.bat
```

Run in `plc-comm-slmp-dotnet`.

```powershell
python -m ruff check .
python -m ruff format --check .
python -m mypy slmp
python scripts\check_public_api_docs.py
python -m pytest
```

Run in `plc-comm-slmp-python`.

```powershell
cargo fmt --check
cargo test
```

Run in `plc-comm-slmp-rust`.

```powershell
npm test
```

Run in `node-red-contrib-plc-comm-slmp`.

```powershell
cmd /c run_ci.bat
python scripts\check_device_range_catalog_parity.py
```

Run in `plc-comm-slmp-cpp-minimal`.

```powershell
$env:PYTHONPATH='D:\APP\plc-comm-hostlink-python\src;D:\APP\plc-comm-slmp-python;D:\APP\plc-comm-computerlink-python'
python scripts\collect_docs.py --source-root D:\APP --docs-root docs
python -m mkdocs build --strict
```

Run in `plc-comm-docs-site`.
