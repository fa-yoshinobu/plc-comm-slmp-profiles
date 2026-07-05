# Unit Profile Rollout Non-Live Audit

Date: 2026-07-05

Scope: non-live rollout checks for the Ethernet-unit profile wave. This record
does not contain PLC communication evidence and does not satisfy the downstream
live-read acceptance item.

## Commands

```powershell
python tools\audit_unit_profile_rollout.py
```

Result:

```text
unit-profile-rollout-audit-ok checks=211
```

Source-evidence replay audit:

```powershell
python tools\audit_unit_profile_source_evidence.py
```

Result:

```text
unit-profile-source-evidence-audit-ok checks=283
```

This audit reads the saved `results.json` files and checks that the adopted
unit-profile decisions are backed by the recorded frame/compatibility,
subcommand, feature, route, limit, and no-new-profile evidence. It does not
perform new PLC communication.

Downstream live-result record audit before live execution:

```powershell
python tools\audit_downstream_read_records.py
python tools\audit_downstream_read_records.py --require-complete
```

Result:

```text
downstream-read-records-pending records=0 valid=0 missing=.NET,Python,Rust,Node-RED,C++ minimal q_series_4e=pending
require-complete pending gate ok
```

The default audit reports pending without failing before live evidence exists.
The `--require-complete` mode fails while live acceptance records are absent.

Additional planner dry-run check:

```powershell
$profiles = @(
  'melsec:qcpu:qj71e71-100',
  'melsec:qnu:qj71e71-100',
  'melsec:qnudv:qj71e71-100',
  'melsec:lcpu:lj71e71-100'
)
foreach ($profile in $profiles) {
  python tools\run_downstream_read_checks.py --profile $profile --host 192.168.250.100 --port 1025 --device D1000 *> $null
  if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}
```

Result:

```text
all downstream dry-runs passed
```

Result-record gate checks:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --host 192.168.250.100 --port 1025 --device D1000 --record-json $env:TEMP\downstream_read_dryrun_should_not_exist.json
python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --execute --record-json $env:TEMP\downstream_read_unapproved_should_not_exist.json
```

Result:

```text
dry-run record-json gate ok
unapproved record-json gate ok
```

No result record was created in dry-run mode or unapproved execute mode.

docs-site refresh after the profile-doc wording update:

```powershell
$env:PYTHONPATH='D:\APP\plc-comm-hostlink-python\src;D:\APP\plc-comm-slmp-python;D:\APP\plc-comm-computerlink-python'
python scripts\collect_docs.py --source-root D:\APP --docs-root docs
python -m mkdocs build --strict
```

Result:

```text
collect_docs.py completed for the configured source repositories.
Documentation built in strict mode.
```

## What The Audit Covers

- Canonical JSON contains the four selectable Ethernet-unit profiles:
  `melsec:qcpu:qj71e71-100`, `melsec:qnu:qj71e71-100`,
  `melsec:qnudv:qj71e71-100`, and `melsec:lcpu:lj71e71-100`.
- Saved source evidence for QJ71E71-100, LJ71E71-100, and RJ71EN71 still
  matches the adopted canonical decisions.
- Each Ethernet-unit profile has `scope=ethernet-unit`, `frame=4E`,
  `compat=Q/L`, and the expected `base_profile`.
- `melsec:qcpu` is `role=base` and `scope=base-profile`.
- `melsec:iq-r` keeps the RJ71EN71 no-new-profile decision through
  `verified_models`.
- The five downstream repositories carry v1.2.0 profile fixtures and
  update-script default refs.
- User profile docs include the new profile IDs and do not list `melsec:qcpu`
  as a selectable table row.
- Node-RED editor option HTML does not expose `melsec:qcpu` as a profile
  option and does expose the new unit profiles.
- docs-site QJ71E71-100 and LJ71E71-100 setup pages reference the new
  canonical profiles and mention 4E with Q/L compatibility.
- The downstream live-read template and planner exist, and the planner's live
  path requires the explicit approval flag.
- The planner can write a JSON result record during approved live execution,
  while dry-run and unapproved execute modes do not create result files.
- The downstream result-record audit tool reports pending before live records
  exist and can be used with `--require-complete` after the approved batch.

## Remaining Acceptance Items

- Run the downstream read-only live check for all five implementations after
  the user confirms the connected PLC and replies `OK` for the exact batch.
- Record those pass/fail results in
  `downstream_unit_profile_read_checks_20260705.md`.
- Publish/tag/commit only after explicit user instruction.
