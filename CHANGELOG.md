# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
This repository publishes canonical profile data consumed by implementation repositories by fixed tags.

**Entry labels**

- `Data`: Capability profiles, device-range definitions, evidence, or generated JSON.
- `Docs`: README, comparison tables, or maintenance documentation.
- `Tooling`: Generators, validation scripts, or other maintainer utilities.
- `Release`: Tagging and publication preparation.

## [Unreleased]

### Changed

- Data: Renamed the public capability JSON from `slmp_builtin_ethernet_profiles.json` to `slmp_ethernet_profiles.json` because it now includes built-in and verified Ethernet-unit profiles.
- Tooling: Changed downstream import defaults from the moving `main` branch to immutable profile commit `e7e8f071ff1819a6b088b6a793e6f08029c54e38` and changed the Node-RED rollout audit to verify its runtime/admin profile API.

### Fixed

- Tooling: Reject duplicate JSON object keys during profile validation.

## [1.2.3] - 2026-07-06

### Changed

- Docs: Documented the shared generated profile-table style and regenerated the SLMP tables with explicit purpose and cell-reading sections.

## [1.2.2] - 2026-07-06

### Changed

- Data: Added inferred 0080/0081 extended random and monitor limit keys to the Q/L built-in/base profiles, while keeping iQ-F monitor support not adopted.
- Data: Recorded RJ71EN71 iQ-R live evidence for the 0082/0083 extended random routes used by API parity work.
- Tooling: Added validation that capability profiles keep a uniform limit-key set.
- Data: Pruned superseded evidence and corrected stale rollout references without changing the published profile decisions.

## [1.2.1] - 2026-07-05

### Changed

- Data: Shortened SLMP `display_name` values to the `<series> (<route>)` UI label form.
- Docs: Regenerated profile tables with the shortened display names and the RJ71EN71 row in table order.
- Tooling: Added a live verification draft generator and stable plan/result summary generation.
- Tooling: Added a profile field-collection tool with write probes enabled by default and documented collector hand-off usage.

## [1.2.0] - 2026-07-05

### Added

- Data: Added verified Ethernet-unit profiles for `melsec:qcpu:qj71e71-100`, `melsec:lcpu:lj71e71-100`, `melsec:qnu:qj71e71-100`, and `melsec:qnudv:qj71e71-100`.

## [1.1.2] - 2026-07-05

### Changed

- Data: Updated SLMP `display_name` values to match the approved profile naming table.
- Docs: Split the generated profile comparison into profile-parameter and device-range tables without changing canonical JSON data.

## [1.1.1] - 2026-07-05

### Added

- Data: Added `display_name` to each built-in Ethernet capability profile.

## [1.1.0] - 2026-07-04

### Added

- Data: Added iQ-R/iQ-L live evidence for extended random and monitor point limits and recorded route-specific `C070` results for Q/L families.
- Tooling: Added profile JSON validation, schemas, raw extended-random probes, and profile-level scope/base-profile support.
- Data: Marked `melsec:qcpu` as base-only and added device-range base-profile inheritance for Ethernet-unit profiles.

## [1.0.0] - 2026-07-04

### Added

- Data: Published the first canonical SLMP built-in Ethernet profile data set.
- Data: Added capability profiles for `melsec:iq-r`, `melsec:iq-l`, `melsec:iq-f`, `melsec:lcpu`, `melsec:qcpu`, `melsec:qnu`, `melsec:qnudv`, `melsec:mx-r`, and `melsec:mx-f`.
- Data: Added device-range rules generated from `device-ranges/slmp_device_range_rules.md`.
- Data: Added profile definition evidence under `evidence/profile-definitions`.
- Data: Added live verification evidence for R120P / iQ-R, iQ-L, iQ-F, LCPU, QnU, and QnUDV profile decisions.
- Data: Added `random_write_word.weighted_max` values and live evidence for every live profile that defines weighted random-write limits.
- Docs: Documented that profiles target CPU built-in Ethernet ports and are conservative when used with extension Ethernet modules.
- Docs: Added generated comparison tables for profile and device-rule maintenance.
- Docs: Added a live verification checklist template that separates random word-write count checks from weighted-limit checks.
- Tooling: Added generators for capability profiles, device-range rules, and comparison tables.
- Tooling: Added `.gitattributes` to keep generated JSON, Markdown, Python sources, and license text on LF line endings.

### Release

- Release: Prepared the first fixed-tag data release as `v1.0.0`.
