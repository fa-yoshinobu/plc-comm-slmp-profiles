# LCPU via LJ71E71-100 / melsec:lcpu:lj71e71-100 Profile Definition

This is a unit-profile definition backed by live L02SCPU + LJ71E71-100 evidence.
The profile keeps `melsec:lcpu` as its base profile for device range and address-resolution behavior, but uses the Ethernet-unit communication shape measured through LJ71E71-100.

Schema note: `schema_version` remains 1. Profile-level `scope`, optional `base_profile`, and `role=base` metadata are additive for the v1.2.0 unit-profile wave.

## Difference Decision

| Area | Base `melsec:lcpu` | Unit result | Decision |
|------|--------------------|-------------|----------|
| Frame | 3E/Q-L built-in | 4E + Q/L works | Add unit profile |
| Type name / block | blocked on built-in | live pass | Unit feature differs |
| Extended routes | not adopted on built-in | configured `U\G` passes; `J` is config-dependent | Unit feature differs |
| Limits | built-in plain limits only | unit plain and `U\G` ext limits measured | Use live unit limits |
| Device ranges | LCPU baseline | same family/range model | Inherit base range data |

## Item

| Item | Value |
|------|-------|
| profile | `melsec:lcpu:lj71e71-100` |
| definition_type | `live` |
| base_profile | `melsec:lcpu` |
| source_evidence | `evidence/unit-investigations/lj71e71-100_l02scpu_20260705.md` |
| live_verified | `true` |
| verified_models | `L02SCPU via LJ71E71-100` |
| scope | `ethernet-unit` |
| frame | `4E` |
| compat | `Q/L` |
| word_subcommand | `0000` |
| bit_subcommand | `0001` |
| ext_word_subcommand | `0080` |
| ext_bit_subcommand | `0081` |

## Features

| Key | State | Source |
|-----|-------|--------|
| type_name | supported | live |
| direct | supported | live |
| random | supported | live |
| block | supported | live |
| monitor | supported | live |
| ext_module_access | config-dependent | live |
| ext_link_direct | config-dependent | live |
| hg_cpu_buffer | blocked | spec |
| long_device_path | blocked | live |
| lz_32bit_path | blocked | live |

## Limits

| Key | Max | Weighted max | Over end code | Source |
|-----|-----|--------------|---------------|--------|
| direct_word_read | 960 |  | C051 | live |
| direct_word_write | 960 |  | C051 | live |
| direct_bit_read | 7168 |  | C052 | live |
| direct_bit_write | 7168 |  | C052 | live |
| random_read_word | 192 |  | C054 | live |
| random_write_word | 160 | 1920 | 4080 | live |
| random_write_bit | 188 |  | C053 | live |
| monitor_register_word | 192 |  | C054 | live |
| random_read_word_ext | 192 |  | C054 | live |
| random_write_word_ext | 160 | 1920 | 4080 | live |
| random_write_bit_ext |  |  |  | not-adopted |
| monitor_register_word_ext | 192 |  | C054 | live |

## Write Policy

| Device | Policy |
|--------|--------|
| S | read-write |
