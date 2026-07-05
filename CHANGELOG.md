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

- Data: Updated SLMP `display_name` values to match the approved profile naming table for the `v1.1.2` data release.
- Docs: Split the generated SLMP profile comparison into user-facing profile parameter and device-range tables without changing the canonical JSON data.
- Tooling: Added a live verification draft generator that pre-fills checklist rows from the canonical capability and device-range JSON files.
- Tooling: Added a field collection tool for gathering profile evidence from PLCs that maintainers do not have, including write probes by default.
- Docs: Added hand-off usage instructions for the SLMP profile collector executable.
- Data: Added `display_name` to each built-in Ethernet capability profile.
- Tooling: Added JSON validation and schema files for profile maintenance.
- Data: Added iQ-R/iQ-L live evidence for 0082/0083 extended random and monitor point limits.
- Data: Recorded LCPU/QnU/QnUDV 0080 direct-device probes returning `C070` as route evidence, not point-limit evidence.
- Docs: Added extended random limit rows to the live verification checklist template.
- Tooling: Added raw extended random probes to `live_profile_probe.py`.
- Data: Added verified Ethernet-unit profiles for `melsec:qcpu:qj71e71-100`, `melsec:lcpu:lj71e71-100`, `melsec:qnu:qj71e71-100`, and `melsec:qnudv:qj71e71-100`.
- Data: Marked `melsec:qcpu` as a base-only profile and recorded `R120PCPU via RJ71EN71` as verified on `melsec:iq-r` instead of adding a separate RJ71EN71 profile.
- Data: Removed inferred 0080/0081 extended limit rows from Q/L built-in profiles after live baseline runs returned `C070`.
- Tooling: Added profile-level `scope`, optional `base_profile`, and `role=base` support to capability generation, validation, schema, and generated comparison tables.
- Tooling: Added device-range `base_profile` inheritance so Ethernet-unit profiles can reuse the existing CPU-family range models.

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
