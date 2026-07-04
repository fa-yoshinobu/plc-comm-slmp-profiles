[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# MELSEC SLMP Profiles

Canonical MELSEC SLMP profile data shared by the `plc-comm-slmp-*` libraries.

Markdown files are the editable source. JSON files and comparison tables are generated artifacts. Downstream libraries should import a fixed tag from this repository.

## Profile data

The maintained capability definitions are in [profile definitions](evidence/profile-definitions/).

Generated capability data is published as [slmp_builtin_ethernet_profiles.json](capability/slmp_builtin_ethernet_profiles.json). It defines frame defaults, compatibility mode, feature states, point limits, write policy, and route policy for CPU built-in Ethernet profiles.

In a profile definition limit row, `Weighted max` is an additional weighted-count guard for commands that use weighted point accounting. A blank `Weighted max` means no weighted guard is defined for that limit row; it does not mean an unknown value.

Extended random and monitor routes use their own `*_ext` limit rows. Implementations should read those rows directly when building 0080/0081 or 0082/0083 requests, instead of deriving extended limits from the plain random or monitor rows.

## Device range data

The maintained device-range source is [slmp_device_range_rules.md](device-ranges/slmp_device_range_rules.md).

Generated device-range data is published as [slmp_device_range_rules.json](device-ranges/slmp_device_range_rules.json). It defines SD register windows, fixed ranges, register-derived ranges, unsupported families, undefined families, and runtime probe markers.

Communication libraries may use device-range data to reject unsupported device families. They should not use device-range upper bounds as transport send guards; applications or live probe tools should decide address-range validity.

## Supported PLC profiles

- `melsec:iq-r`
- `melsec:iq-l`
- `melsec:mx-r`
- `melsec:mx-f`
- `melsec:iq-f`
- `melsec:qcpu`
- `melsec:lcpu`
- `melsec:qnu`
- `melsec:qnudv`

## Port scope

These profiles target CPU built-in Ethernet ports.

Extension Ethernet modules may support additional commands. A built-in Ethernet profile is the conservative baseline: using it against an extension Ethernet module should not enable commands beyond the stricter CPU built-in Ethernet profile, but it may leave module-specific capabilities unused.

## Documentation

| Page | Use it for |
| --- | --- |
| [Full documentation site](https://fa-yoshinobu.github.io/plc-comm-docs-site/) | Unified docs for all PLC communication libraries. |
| [Profile parameters](tables/slmp_profile_parameters.md) | Compare frame defaults, feature decisions, point limits, write policy, and device availability across profiles. |
| [Device ranges](tables/slmp_device_ranges.md) | Check SD-derived range rules, fixed ranges, probe markers, and unsupported device families. |
| [Profile definitions](evidence/profile-definitions/) | Edit capability profile source data. |
| [Device range source](device-ranges/slmp_device_range_rules.md) | Edit device-range source data. |
| [Live evidence](evidence/) | Check live verification decisions used by the profile definitions. |

## Generate

Do not edit generated JSON or table files by hand.

```powershell
python tools/generate_capability_profiles.py
python tools/generate_device_range_rules.py
python tools/generate_profile_tables.py
```

Run the relevant generator after changing its Markdown source. Run the table generator after either JSON file changes.

To start a live PLC verification record from the canonical JSON values:

```powershell
python tools/generate_live_verification_draft.py --profile melsec:iq-f --plc-model FX5U-32MR/DS
```

The generated file is only a checklist draft. Keep untested rows as `unverified` until a live probe is run.

To collect field evidence from a PLC that the maintainer does not have:

```powershell
python tools/collect_live_plc_profile.py --profile melsec:iq-f --host 192.168.250.100 --plc-model FX5U-32MR/DS
```

This collector writes to the configured test devices by default so that write policy and basic write behavior are recorded. Numeric write probes use random values and are not restored. Bit probes are reset to OFF after the check. Use `--skip-writes` only when a read-only collection is intentionally required.

For a single-file Windows executable, bundle this collector together with `capability/slmp_builtin_ethernet_profiles.json` and `device-ranges/slmp_device_range_rules.json`; the executable must use the same JSON data version as this repository tag.

```bat
tools\build_profile_collector_exe.bat
```

Hand off [PROFILE_COLLECTOR_USAGE.md](tools/PROFILE_COLLECTOR_USAGE.md) with the executable when asking someone else to run the collector.

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
