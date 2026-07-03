# iQ-R / melsec:iq-r Profile Definition

| Item | Value |
|------|-------|
| profile | `melsec:iq-r` |
| definition_type | `live` |
| source_evidence | `evidence/iq-r_slmp_live_verify_20260703.md` |
| live_verified | `true` |
| verified_models | `R120PCPU(built-in Ethernet)` |
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
| hg_cpu_buffer | supported | live |
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

## Write Policy

| Device | Policy |
|--------|--------|
| S | read-only |
