[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

# MELSEC SLMP Profiles

Canonical MELSEC SLMP profile data shared by the `plc-comm-slmp-*` libraries.

Markdown files are the editable source. JSON files and comparison tables are generated artifacts. Downstream libraries should import a fixed tag from this repository.

## Profile data

The maintained capability definitions are in [profile definitions](evidence/profile-definitions/).

Generated capability data is published as [slmp_builtin_ethernet_profiles.json](capability/slmp_builtin_ethernet_profiles.json). It defines frame defaults, compatibility mode, feature states, point limits, write policy, and route policy for CPU built-in Ethernet profiles.

In a profile definition limit row, `Weighted max` is an additional weighted-count guard for commands that use weighted point accounting. A blank `Weighted max` means no weighted guard is defined for that limit row; it does not mean an unknown value.

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
| [Profile comparison](tables/slmp_profile_comparison.md) | Compare capability and device-range data across profiles. |
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
