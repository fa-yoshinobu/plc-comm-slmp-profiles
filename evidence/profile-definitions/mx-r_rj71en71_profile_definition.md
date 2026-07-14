# MX-R via RJ71EN71 / melsec:mx-r:rj71en71 Profile Definition

This is a derived Ethernet-unit alias backed by live MXR300-32 + RJ71EN71
evidence. The unit route matched the MX-R built-in Ethernet request shape,
feature decisions, limits, device-range model, route results, and `S` write
policy across all 29 reviewed probe items. This profile therefore inherits
`melsec:mx-r` and gives RJ71EN71 users a distinct selectable connection name.

## Difference Decision

| Area | Base `melsec:mx-r` | RJ71EN71 result | Decision |
|------|--------------------|-----------------|----------|
| Frame / compat / subcommands | 4E/iQ-R with `0002`, `0003`, `0082`, `0083` | Exact match | Add alias unit profile |
| Feature states and routes | Live MX-R contract | Exact match, including `U3E0\HG=4030` | Inherit base profile |
| Limits | Live MX-R plain and extended limits | Exact match at every pass/fail boundary | Inherit base limits |
| Device ranges | MX-R range model | No connection-path difference observed | Inherit base range data |
| Write policy | `S=read-only` | `S2` write returned `4031`, matching built-in | Inherit base write policy |

## Item

| Item | Value |
|------|-------|
| profile | `melsec:mx-r:rj71en71` |
| definition_type | `derived` |
| base_profile | `melsec:mx-r` |
| source_evidence | `evidence/unit-investigations/plans/results/mx-r_rj71en71_mxr300-32.json` |
| live_verified | `true` |
| verified_models | `MXR300-32 via RJ71EN71` |
| scope | `ethernet-unit` |

## Overrides

| Key | Value |
|-----|-------|
| verified_models | `MXR300-32 via RJ71EN71` |
| features.type_name.source | `live` |
| features.direct.source | `live` |
| features.random.source | `live` |
| features.block.source | `live` |
| features.monitor.source | `live` |
| features.ext_module_access.source | `live` |
| features.ext_link_direct.source | `live` |
| features.long_device_path.source | `live` |
| features.lz_32bit_path.source | `live` |
| limits.direct_word_read.source | `live` |
| limits.direct_word_write.source | `live` |
| limits.direct_bit_read.source | `live` |
| limits.direct_bit_write.source | `live` |
| limits.random_read_word.source | `live` |
| limits.random_write_word.source | `live` |
| limits.random_write_bit.source | `live` |
| limits.monitor_register_word.source | `live` |
| limits.random_read_word_ext.source | `live` |
| limits.random_write_word_ext.source | `live` |
| limits.random_write_bit_ext.source | `live` |
| limits.monitor_register_word_ext.source | `live` |
