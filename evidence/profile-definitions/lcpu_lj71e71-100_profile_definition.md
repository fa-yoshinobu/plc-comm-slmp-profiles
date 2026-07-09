# LCPU via LJ71E71-100 / melsec:lcpu:lj71e71-100 Profile Definition

This is a unit-profile definition backed by live L02SCPU + LJ71E71-100 evidence.
The profile keeps `melsec:lcpu` as its base profile for device range and address-resolution behavior, but uses the Ethernet-unit communication shape measured through LJ71E71-100.

Schema note: `schema_version` remains 1. Profile-level `scope`, optional `base_profile`, and `role=base` metadata are additive for the v1.2.0 unit-profile wave.

## Difference Decision

| Area | Base `melsec:lcpu` | Unit result | Decision |
|------|--------------------|-------------|----------|
| Frame | 3E/Q-L built-in | 4E + Q/L works | Add unit profile |
| Type name / block | blocked on built-in | live pass | Unit feature differs |
| Extended routes | not adopted on built-in | configured `U\G` passes; `J2\X`, `J2\Y`, `J2\W`, `J2\SB`, and `J2\SW` pass; `J2\B` returned `4031` | Unit feature differs; keep route config-dependent |
| Limits | built-in plain limits only | unit plain, `U5\G100` ext, and `J2\W100` ext word limits measured | Use live unit limits |
| Device ranges | LCPU baseline | same family/range model | Inherit base range data |

## Item

| Item | Value |
|------|-------|
| profile | `melsec:lcpu:lj71e71-100` |
| definition_type | `live` |
| base_profile | `melsec:lcpu` |
| source_evidence | `evidence/unit-investigations/plans/results/lj71e71-100_l02scpu.json` |
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
| random_write_bit_ext | 188 |  | C053 | inferred |
| monitor_register_word_ext | 192 |  | C054 | live |

## Route Notes

| Route | Latest target | Result | Decision note |
|-------|---------------|--------|---------------|
| `U\G` | `U5\G100` | read/write/monitor ext word limits measured | Positive configured module-buffer route for this rig |
| `J\W` | `J2\W100` | read/write ext word limits measured | Positive link-direct word route for this rig |
| `J\X` | `J2\X0` | read returned `0000` | Positive read route only |
| `J\Y` | `J2\Y0` | read returned `0000` | Positive read route only |
| `J\SB` | `J2\SB0` | read returned `0000` | Positive read route only |
| `J\SW` | `J2\SW0` | read returned `0000` | Positive read route only |
| `J\B` | `J2\B10` | read/write-bit-ext returned `4031` | Not positive evidence for ext bit write; keep `random_write_bit_ext` inferred, not live |

## Write Policy

| Device | Policy |
|--------|--------|
| S | read-write |
