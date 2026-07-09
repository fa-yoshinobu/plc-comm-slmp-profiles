# QCPU / melsec:qcpu Profile Definition

This is a definition record, not live verification. QCPU CPUs do not provide a built-in Ethernet port in this profile scope. This profile is a base-only Q-series range and address baseline; use `melsec:qcpu:qj71e71-100` for the verified QJ71E71-100 Ethernet-unit route.

| Item | Value |
|------|-------|
| profile | `melsec:qcpu` |
| definition_type | `derived` |
| base_profile | `melsec:qnu` |
| scope | `base-profile` |
| role | `base` |
| inherit | feature states, limits, write policy |
| live_verified | `false` |

## Overrides

| Key | Value |
|-----|-------|
| verified_models | `No built-in Ethernet CPU target (QnU-derived conservative baseline)` |
| limits.random_read_word_ext.source | inferred |
| limits.random_read_word_ext.max | 185 |
| limits.random_read_word_ext.over_end_code | 4080 |
| limits.random_write_word_ext.source | inferred |
| limits.random_write_word_ext.max | 160 |
| limits.random_write_word_ext.weighted_max | 1920 |
| limits.random_write_word_ext.over_end_code | 4080 |
| limits.random_write_bit_ext.source | inferred |
| limits.random_write_bit_ext.max | 188 |
| limits.random_write_bit_ext.over_end_code | C053 |
| limits.monitor_register_word_ext.source | inferred |
| limits.monitor_register_word_ext.max | 192 |
| limits.monitor_register_word_ext.over_end_code | C054 |
