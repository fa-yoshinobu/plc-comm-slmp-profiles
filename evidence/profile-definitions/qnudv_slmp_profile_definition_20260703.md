# QnUDV / melsec:qnudv Profile Definition

| Item | Value |
|------|-------|
| profile | `melsec:qnudv` |
| definition_type | `live` |
| source_evidence | `evidence/qnudv_slmp_live_verify_20260703.md` |
| live_verified | `true` |
| verified_models | `Q06UDVCPU(built-in Ethernet)` |
| frame | `3E` |
| compat | `Q/L` |
| word_subcommand | `0000` |
| bit_subcommand | `0001` |
| ext_word_subcommand | `0080` |
| ext_bit_subcommand | `0081` |

## Features

| Key | State | Source |
|-----|-------|--------|
| type_name | blocked | live |
| direct | supported | live |
| random | supported | live |
| block | blocked | live |
| monitor | supported | live |
| ext_module_access | blocked | live |
| ext_link_direct | blocked | live |
| hg_cpu_buffer | blocked | spec |
| long_device_path | delegated | live |
| lz_32bit_path | delegated | live |

## Limits

| Key | Max | Weighted max | Over end code | Source |
|-----|-----|--------------|---------------|--------|
| direct_word_read | 960 |  | C051 | live |
| direct_word_write | 960 |  | C051 | live |
| direct_bit_read | 7168 |  | C052 | live |
| direct_bit_write | 7168 |  | C052 | live |
| random_read_word | 192 |  | C054 | live |
| random_write_word | 160 | 1920 | C054 | live |
| random_write_bit | 188 |  | C053 | live |
| monitor_register_word | 192 |  | C054 | live |
| random_read_word_ext |  |  |  | not-adopted |
| random_write_word_ext |  |  |  | not-adopted |
| random_write_bit_ext |  |  |  | not-adopted |
| monitor_register_word_ext |  |  |  | not-adopted |

## Write Policy

| Device | Policy |
|--------|--------|
| S | read-only |
