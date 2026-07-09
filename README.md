[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# MELSEC SLMP Profiles

Canonical MELSEC SLMP profile data shared by the `plc-comm-slmp-*` libraries.

Profile definition Markdown files are the editable source. Capability JSON files, comparison tables, and unit-probe summary Markdown files are generated artifacts. Downstream libraries should import a fixed tag from this repository.

## Profile data

The maintained capability definitions are in [profile definitions](evidence/profile-definitions/).

Generated capability data is published as [slmp_ethernet_profiles.json](capability/slmp_ethernet_profiles.json). It defines frame defaults, compatibility mode, feature states, point limits, write policy, route policy, per-profile scope, base-profile links, and base-only roles for CPU built-in Ethernet profiles and verified Ethernet-unit profiles.

In a profile definition limit row, `Weighted max` is an additional weighted-count guard for commands that use weighted point accounting. A blank `Weighted max` means no weighted guard is defined for that limit row; it does not mean an unknown value.

Extended random and monitor routes use their own `*_ext` limit rows. Implementations should read those rows directly when building 0080/0081 or 0082/0083 requests, instead of deriving extended limits from the plain random or monitor rows.

## Device range data

The maintained device-range source is [slmp_device_range_rules.md](device-ranges/slmp_device_range_rules.md).

Generated device-range data is published as [slmp_device_range_rules.json](device-ranges/slmp_device_range_rules.json). It defines SD register windows, fixed ranges, register-derived ranges, unsupported families, undefined families, and runtime probe markers.

Communication libraries may use device-range data to reject unsupported device families. They should not use device-range upper bounds as transport send guards; applications or live probe tools should decide address-range validity.

## Supported connection profiles

- `melsec:iq-r`
- `melsec:iq-l`
- `melsec:mx-r`
- `melsec:mx-f`
- `melsec:iq-f`
- `melsec:qcpu:qj71e71-100`
- `melsec:lcpu`
- `melsec:lcpu:lj71e71-100`
- `melsec:qnu`
- `melsec:qnu:qj71e71-100`
- `melsec:qnudv`
- `melsec:qnudv:qj71e71-100`

## Base-only profiles

- `melsec:qcpu` exists only as a Q-series base profile for range and address-resolution data. Do not expose it as a connection profile; use `melsec:qcpu:qj71e71-100` for the verified QJ71E71-100 Ethernet-unit route.

## Port scope

Profile scope is recorded per profile. `builtin-ethernet-port` profiles target CPU built-in Ethernet ports, `ethernet-unit` profiles target verified extension Ethernet modules, and `base-profile` entries are not connection profiles.

Extension Ethernet modules may support additional commands. Use an `ethernet-unit` profile when live evidence exists for that unit/CPU family pair; otherwise the built-in Ethernet profile remains the conservative baseline.

## Documentation

| Page | Use it for |
| --- | --- |
| [Full documentation site](https://fa-yoshinobu.github.io/plc-comm-docs-site/) | Unified docs for all PLC communication libraries. |
| [Profile parameters](tables/slmp_profile_parameters.md) | Compare frame defaults, feature decisions, point limits, write policy, and device availability across profiles. |
| [Device ranges](tables/slmp_device_ranges.md) | Check SD-derived range rules, fixed ranges, probe markers, and unsupported device families. |
| [Profile definitions](evidence/profile-definitions/) | Edit capability profile source data. |
| [Device range source](device-ranges/slmp_device_range_rules.md) | Edit device-range source data. |
| [Unit probe results](evidence/unit-investigations/plans/results/) | Check the machine-readable JSON evidence and generated MD summaries named by profile definitions. |

## Generate

Do not edit generated JSON or table files by hand.

```powershell
python tools/generate_capability_profiles.py
python tools/generate_device_range_rules.py
python tools/generate_profile_tables.py
python tools/generate_unit_probe_summaries.py
```

Run the relevant generator after changing its Markdown source. Run the table generator after either JSON file changes.

To probe a live PLC directly (single raw SLMP requests, one JSON line per call):

```powershell
python tools/live_profile_probe.py --profile melsec:qnu --frame 4E --compat Q/L read-word --device D0
```

Use direct raw probes only to discover a missing check. If the result affects a maintained profile, add the check to `run_unit_probe_plan.py` and the reviewed plan JSON, rerun the plan, and keep only the generated `plans/results/{plan_name}.json` evidence plus its same-name MD summary.

To run a complete unit investigation sweep from a reviewed plan file (required coverage enforced, writes restricted to the plan's allowlist, limits found by automatic boundary search):

```powershell
python tools/run_unit_probe_plan.py --plan evidence/unit-investigations/plans/qj71e71-100_q12hcpu.json --dry-run
```

See [UNIT_PROBE_PLAN_USAGE.md](tools/UNIT_PROBE_PLAN_USAGE.md) for details.

## Downstream use

Implementation repositories should import a fixed tag and keep fixture tests that compare their embedded data against this repository.

If a JSON schema changes, increment `schema_version` and keep the old tag available until all downstream libraries have migrated.

## License

| Item | Value |
| --- | --- |
| License | [MIT](LICENSE) |
| Canonical data tag | `v1.0.0` or later |

## Commercial support

If you plan to embed these profiles in a paid or commercial product, please consider a separate support agreement or supporting the project as a sponsor.

Contact: <https://fa-labo.com/contact.html>
