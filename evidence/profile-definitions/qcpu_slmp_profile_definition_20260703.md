# QCPU / melsec:qcpu Profile Definition

This is a definition record, not live verification. QCPU CPUs do not provide a built-in Ethernet port in this profile scope. This profile uses the QnU built-in Ethernet profile as the closest conservative Q-series baseline; extension Ethernet modules can support additional commands and are intentionally not expanded here.

| Item | Value |
|------|-------|
| profile | `melsec:qcpu` |
| definition_type | `derived` |
| base_profile | `melsec:qnu` |
| inherit | feature states, limits, write policy |
| live_verified | `false` |

## Overrides

| Key | Value |
|-----|-------|
| verified_models | `No built-in Ethernet CPU target (QnU-derived conservative baseline)` |
