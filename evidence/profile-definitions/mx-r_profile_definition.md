# MX-R / melsec:mx-r Profile Definition

| Item | Value |
|------|-------|
| profile | `melsec:mx-r` |
| definition_type | `live` |
| source_evidence | `evidence/unit-investigations/plans/results/mx-r_mxr300-32_builtin.json` |
| live_verified | `true` |
| verified_models | `MXR300-32(built-in Ethernet)` |
| base_profile | `melsec:iq-r` |
| frame | `4E` |
| compat | `iQ-R` |
| word_subcommand | `0002` |
| bit_subcommand | `0003` |
| ext_word_subcommand | `0082` |
| ext_bit_subcommand | `0083` |

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
| long_device_path | supported | live |
| lz_32bit_path | supported | live |

## Limits

| Key | Max | Weighted max | Over end code | Source |
|-----|-----|--------------|---------------|--------|
| direct_word_read | 960 |  | C051 | live |
| direct_word_write | 960 |  | C051 | live |
| direct_bit_read | 7168 |  | C052 | live |
| direct_bit_write | 7168 |  | C052 | live |
| random_read_word | 96 |  | C054 | live |
| random_write_word | 80 | 960 | C054 | live |
| random_write_bit | 94 |  | C053 | live |
| monitor_register_word | 96 |  | C054 | live |
| random_read_word_ext | 96 |  | C054 | live |
| random_write_word_ext | 80 | 960 | C054 | live |
| random_write_bit_ext | 94 |  | C053 | live |
| monitor_register_word_ext | 96 |  | C054 | live |

## Write Policy

| Device | Policy |
|--------|--------|
| S | read-only |

## Evidence Decisions

| Evidence | Result | NG classification | Contract decision |
|----------|--------|-------------------|-------------------|
| `U6\G1000` and `U3E0\G0` | `0000` | - | Keep `ext_module_access` config-dependent; this configuration is live-positive. |
| `J1\X10`, `J1\Y11`, `J1\B12`, `J1\W13`, `J1\SB1`, `J1\SW2` | `0000` | - | Keep `ext_link_direct` config-dependent; this configuration is live-positive. |
| `U3E0\HG0` | `4030` | spec | Keep `hg_cpu_buffer` blocked; MX-R does not adopt the iQ-R CPU-buffer route. |
| `S0` read and `S2` write | `4031` | address | Keep the S write policy read-only; one tested address does not establish family-wide absence. |
| Raw `LTS0`, `LTC0`, `LSTS0`, `LSTC0` | `4030` | route | Raw codes are record-only; the supported long-device contract uses the successful `LTN`/`LSTN` helper routes. |
