# MX-R / melsec:mx-r Profile Definition

This is a definition record, not live verification.

| Item | Value |
|------|-------|
| profile | `melsec:mx-r` |
| definition_type | `derived` |
| base_profile | `melsec:iq-r` |
| inherit | feature states, limits, write policy, device-range model |
| live_verified | `false` |

## Overrides

| Key | Value |
|-----|-------|
| verified_models | `Unconfirmed` |
| features.hg_cpu_buffer.state | `blocked` |
| features.hg_cpu_buffer.source | `spec` |
