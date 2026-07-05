# RJ71EN71 Unit Profile Decision

This record is superseded by
`iq-r_rj71en71_slmp_profile_definition_20260705.md`, which adds the selectable
`melsec:iq-r:rj71en71` alias profile. The original no-new-profile decision was
reversed by user decision on 2026-07-05 so RJ71EN71 users can choose their own
unit configuration name, matching the QJ71E71-100/LJ71E71-100 profile pattern.

| Area | Base `melsec:iq-r` | RJ71EN71 result | Decision |
|------|--------------------|-----------------|----------|
| Frame / compat | 4E/iQ-R | 4E/iQ-R | Add alias unit profile |
| Feature states | supported/config-dependent iQ-R shape | same adopted feature shape | Inherit base profile |
| Limits | iQ-R live limits | same plain and extended limit shape | Inherit base limits |
| Device ranges | iQ-R range model | same family/range model | Inherit base range data |
| Write policy | `S=read-only` | raw `S` write returned `4030` | Inherit base write policy |

`melsec:iq-r:rj71en71` records `R120PCPU via RJ71EN71` in
`verified_models` while `melsec:iq-r` remains the built-in Ethernet profile.
