# Unit Probe Plan Runner Usage

Use `run_unit_probe_plan.py` for unit investigations (extension Ethernet units such as QJ71E71-100). It executes a reviewed plan file end to end and removes operator discretion:

- The plan JSON is the only instruction. Skipping an item at runtime is not possible.
- Every required item in `unit_probe_plan_required.json` must exist in the plan, or the run is refused before any communication.
- Writes go only to devices listed in the plan's `write_allow`, within the declared span. A write item with a non-allowlisted target is a validation error, never a silent skip.
- Limits are found by automatic boundary search (exponential growth, then binary search). Fixed guess counts cannot be substituted for evidence.

Do not run this tool against a production machine or a PLC that controls live equipment. It writes to the allowlisted devices.

## Basic Run

Open a command prompt at the repository root. Always dry-run first and review
the printed write targets:

```bat
python tools\run_unit_probe_plan.py --plan evidence\unit-investigations\plans\qj71e71-100_q12hcpu.json --dry-run
```

`dry-run OK` means the plan is complete (all required items present) and every write target is allowlisted. Then run for real:

```bat
python tools\run_unit_probe_plan.py --plan evidence\unit-investigations\plans\qj71e71-100_q12hcpu.json
```

## Outputs

One run writes two stable files under `evidence/unit-investigations/plans/results/`.

| File | Content |
| --- | --- |
| `{plan_name}.json` | Per-item outcome: boundary values with end codes, route/family tables, errors, waivers |
| `{plan_name}.md` | Generated human-readable summary of the JSON. Do not edit by hand |

Console shows `[n/total] item_id` progress and each boundary attempt (`count=N -> end_code`), so a stall is always visible without retaining a separate attempt log.

To refresh summaries from existing JSON files without PLC communication:

```bat
python tools\generate_unit_probe_summaries.py
```

## Raw Probe Escalation

`live_profile_probe.py` is for discovery when the plan runner does not yet know how to ask a question. It writes no evidence files; treat its stdout JSON as temporary.

If that result affects a maintained profile, do not save a standalone MD/log. Add or adjust a structured item in `run_unit_probe_plan.py`, put the item in the reviewed plan JSON, rerun the plan, and keep the updated `plans/results/{plan_name}.json` plus generated `{plan_name}.md`. Point the profile definition's `source_evidence` row at the JSON. If the result does not affect the profile, discard it.

## Exit Codes

| Code | Meaning |
| --- | --- |
| 0 | All items recorded, no errors |
| 2 | Plan validation failed (missing required item, disallowed write target, cap over field limit). Fix the plan file |
| 3 | Run finished but some items recorded errors (see `results.json` `errors` list). Re-run after fixing the cause |

## Boundary Search Results

Each `boundary_*` item ends in one of:

- `{"status": "limit", "largest_pass": N, "first_fail": N+1, "fail_end": "XXXX"}` — the measured boundary with the over end code.
- `{"status": "limit", "largest_pass": cap, "no_fail_up_to_cap": cap}` — no failure up to the cap; raise `cap` in the plan if a boundary is expected.
- `{"status": "fail", "first_fail": 1, "fail_end": "XXXX"}` — the feature/route failed at 1 point (family/route evidence, not a limit).
- `{"status": "error", "at_count": N}` — communication error even after one retry.

Bit write probes reset the tested bits OFF after each successful attempt. Numeric write values are test values and are not restored.

## Writing A Plan For A New Unit

1. Copy an existing plan from `evidence/unit-investigations/plans/`.
2. Update `profile.base` (the built-in profile of the connected CPU), `frame`, `compat`, and the connection block.
3. Update `write_allow` to the devices the user has designated as writable, with spans at least `cap + 1` for boundary items. Input-like routes (`J..\X`, `J..\Y`) must not be added.
4. Update item params: configured `J`/`U\G` targets, working word/bit areas, caps.
5. `--dry-run` until validation passes. Validation errors list exactly what is missing.

Required coverage lives in `unit_probe_plan_required.json` (25 items: type name, direct/random/block/monitor features, all boundary rows including the ext write rows, qualified routes, all device families, `S` write policy). Extra items beyond the manifest are allowed and run as-is (for example, probing both `U\G` and `J\W` targets for the same ext row).

## Waivers

If an item is genuinely impossible on a given rig (for example, no `J` route is configured), replace its body with an explicit reviewed reason **in the plan file**:

```json
{"id": "boundary_random_write_bit_ext", "waiver": "No J link route is configured on this test rig (user decision 2026-07-05)."}
```

Waived items appear in `results.json` under `waived`. A waiver is a user decision recorded in a reviewed file; deciding at runtime is not supported on purpose.

## Standalone Executables

To hand the sweep to someone who does not have Python or this repository:

```bat
tools\build_unit_probe_exe.bat
```

This builds two single-file executables in `dist\` (canonical JSON and the required-items manifest are bundled inside):

| Executable | Purpose |
| --- | --- |
| `slmp-unit-probe-plan.exe` | Same as `run_unit_probe_plan.py`: `slmp-unit-probe-plan.exe --plan <plan.json> [--dry-run]` |
| `slmp-live-probe.exe` | Same as `live_profile_probe.py` for single ad-hoc requests |

Hand off the executable together with a **reviewed plan JSON** and this document. The bundled JSON matches the repository state at build time; rebuild after canonical JSON changes.

## Notes

- Long timer/counter families are probed by their **intended library routes**: `LTN`/`LSTN` as one 4-word unit (contact/coil bits decode from it), `LCN` and `LZ` by random dword read, `LCS`/`LCC` by direct bit read. `LTS`/`LTC`/`LSTS`/`LSTC` raw device codes are also probed but marked `raw_device_code_probe: true` in results — the library never sends those codes, so raw results are record-only and must not drive family reachability or unit-difference decisions.
- Caps for random/monitor items must be 255 or less (the count field is one byte).
- The runner reuses `live_profile_probe.py` for framing and payloads; on abnormal ends it retries once, records the item error in the result file, and moves on — it never goes silent and never drops an item.
- Feed the saved result JSON boundary values into the profile definition. The profile definition is the maintained decision summary; the result JSON is the machine-checkable evidence.
