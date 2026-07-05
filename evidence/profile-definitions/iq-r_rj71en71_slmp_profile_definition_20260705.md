# iQ-R via RJ71EN71 / melsec:iq-r:rj71en71 Profile Definition

This is a derived Ethernet-unit alias backed by live R120PCPU + RJ71EN71
evidence. The unit route matched the iQ-R 4E/iQ-R request shape, feature
decisions, limits, device-range model, and `S` write policy, so this profile
inherits `melsec:iq-r` and gives RJ71EN71 users a selectable configuration name.

Schema note: `schema_version` remains 1. Profile-level `scope`, optional
`base_profile`, and `role=base` metadata are additive for the v1.2.0
unit-profile wave.

## Difference Decision

| Area | Base `melsec:iq-r` | RJ71EN71 result | Decision |
|------|--------------------|-----------------|----------|
| Frame / compat | 4E/iQ-R | 4E/iQ-R | Add alias unit profile |
| Feature states | supported/config-dependent iQ-R shape | same adopted feature shape | Inherit base profile |
| Limits | iQ-R live limits | same plain and extended limit shape | Inherit base limits |
| Device ranges | iQ-R range model | same family/range model | Inherit base range data |
| Write policy | `S=read-only` | raw `S` write returned `4030` | Inherit base write policy |

## Item

| Item | Value |
|------|-------|
| profile | `melsec:iq-r:rj71en71` |
| definition_type | `derived` |
| base_profile | `melsec:iq-r` |
| source_evidence | `evidence/unit-investigations/rj71en71_r120pcpu_20260705.md` |
| live_verified | `true` |
| verified_models | `R120PCPU via RJ71EN71` |
| scope | `ethernet-unit` |

## Overrides

| Key | Value |
|-----|-------|
| verified_models | `R120PCPU via RJ71EN71` |
