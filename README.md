# plc-comm-slmp-profiles

This repository is the canonical source for PLC model profile data shared by the SLMP communication libraries (dotnet / python / rust / node-red / cpp-minimal). The JSON files in this repository are the source of truth; implementation repositories import them by fixed tags.

## Layout

| Path | Contents |
|------|----------|
| `capability/slmp_builtin_ethernet_profiles.json` | Per-profile capability definitions for seven profiles. These policies are scoped to built-in Ethernet ports only and include frame/subcommand groups, feature states, point limits, write policy, and route selection. |
| `device-ranges/slmp_device_range_rules.json` | Canonical device-range rules for nine profiles. Defines the SD register block location, family resolution rules (`fixed`, `word-register`, `dword-register`, clipped variants, `unsupported`, `undefined`), and runtime probe behavior. |
| `instructions/slmp_profile_restriction_instructions_20260703.md` | Implementation instructions for rolling out the capability profiles to the libraries, including guard behavior, `strict_profile`, and conformance tests. |
| `evidence/` | Live-device verification records from 2026-07-03 for R120P / iQ-L / iQ-F / LCPU / QnUDV. |

## Role Of The Two JSON Files

- **capability** answers "which features may be sent to the built-in Ethernet port for this profile." It is policy data that cannot be reliably discovered at runtime. It does not describe device existence or ranges.
- **device-ranges** answers "how to discover whether device families exist and what their ranges are." It includes runtime probe algorithms for PLCs where some Q-series device ranges are not written into SD registers.

## Profile IDs

Canonical IDs match each implementation's `SlmpPlcProfile` equivalent:
`melsec:iq-r` / `melsec:iq-l` / `melsec:mx-r` / `melsec:mx-f` / `melsec:iq-f` / `melsec:qcpu` / `melsec:lcpu` / `melsec:qnu` / `melsec:qnudv`

The capability table includes only the seven profiles backed by live verification or explicit user policy decisions. `qcpu` and `qnu` exist only in device-ranges; they intentionally have no capability profile.

## Editing Rules

1. **Do not add unsupported entries.** Every change must carry a `source` value (`live` / `manual` / `spec` / `policy` / `inferred`) and either evidence or a note. Add live verification records under `evidence/` when the source is live testing.
2. If live behavior differs from the current canonical data, record the result in evidence first and then update the JSON.
3. Publish changes with a commit and a tag. Implementation repositories must state the imported tag and verify conformance with fixture tests.
4. If the schema changes, increment `schema_version` and keep the old tag available until every implementation has migrated.

## Background

The initial data set was created from live verification of five PLC families on 2026-07-03. Tests used built-in Ethernet ports over TCP 1025. Extension Ethernet unit configurations are out of scope; see `instructions/` for the policy details.
