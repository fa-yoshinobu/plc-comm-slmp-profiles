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

- Docs: Split the generated SLMP profile comparison into user-facing profile parameter and device-range tables without changing the canonical JSON data.

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
