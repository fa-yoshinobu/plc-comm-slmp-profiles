# R120P / RCPU SLMP Specification Decision Record

## Adopted Profile

| Item | Decision |
|------|----------|
| PLC profile | `melsec:iq-r` |
| Live model | `R120PCPU` |
| Frame | 4E |
| Compatibility | iQ-R |
| Standard subcommand | word=`0002`, bit=`0003` |
| Extended subcommand | word=`0082`, bit=`0083` |
| X/Y notation | hexadecimal |

R120P / RCPU capability decisions use 4E / iQ-R profile as the standard condition. 3E / Q-L compatible frames are comparison paths only and are not used as negative evidence for R120P.

## Adopted Features

| Feature | Decision |
|---------|----------|
| Type Name `0101/0000` | Supported |
| Direct read/write `0401/1401` | Supported |
| Random read/write `0403/1402` | Supported |
| Block read/write `0406/1406` | Supported |
| Monitor `0801/0802` | Supported |
| Named normal devices | Supported |
| Long timer / long retentive timer | Supported through dedicated long-device routes |
| Long counter | Supported through dedicated long-device routes |
| `LZ` | `LZ0/LZ1` supported through 32-bit routes |
| `U3E0\G...` | Supported in this configuration |
| `U3E0\HG...` | Supported as the iQ-R-only HG CPU-buffer route |
| `U2\G100` | Supported in this configuration |

## Features Not Adopted

| Feature | Decision | Evidence |
|---------|----------|----------|
| `S` write | Not a positive path | Read succeeds; write returns `4030` |
| `LTS/LTC/LSTS/LSTC` direct/block bit | Not a positive path | Read/write returns `4030`; use dedicated long-device routes |
| `LCN` 16-bit scalar/direct/block | Not a positive path | `LCN` is treated as a double-word current value |
| `LCS` write | Not a positive path | Contact devices are not write targets |
| `LZ` 16-bit direct/block | Not a positive path | `LZ` is a long-only device; use 32-bit routes |
| `Z20` and later | Not a positive path | `Z20` / `Z30` return `4031` |
| standalone `G/HG` | Not a positive path | Use U-qualified extended access |

## Out Of Scope For This Record

| Feature | Decision | Reason |
|---------|----------|--------|
| UDP route | Not decided here | This record covers TCP `1025` |
| UDF | Not tested here | Excluded by user request |

## Device Ranges

For this R120P / RCPU target, adopt the following behavior.

| Device | Adopted range / handling | Out-of-range response | Notes |
|--------|--------------------------|-----------------------|-------|
| `Z` | `Z0..Z19` | `Z20` / `Z30` = `4031` | Supported |
| `LZ` | `LZ0..LZ1` | `LZ2` / `LZ3` do not exist | Positive path only through 32-bit routes |
| `S` | read-only | write = `4030` | Do not use as a write target |
| `U3E0\G...` | Configuration-dependent supported route | - | Verified with direct/random/monitor |
| `U3E0\HG...` | iQ-R-only HG CPU-buffer route | - | Verified with direct/random/monitor |
| `U2\G100` | Configuration-dependent supported route | - | Verified with direct/random/monitor |

`Un\Gn` is not automatically supported just because it is U-qualified. It depends on the PLC configuration and must be confirmed for each target.

## Point Limits

| Command | Adopted limit | Over-limit response |
|---------|---------------|---------------------|
| direct word read `0401/0002` | 960 points | 961 points = `C051` |
| direct word write `1401/0002` | 960 points | 961 points = `C051` |
| direct bit read `0401/0003` | 7168 points | 7169 points = `C052` |
| direct bit write `1401/0003` | 7168 points | 7169 points = `C052` |
| random read `0403/0002` | 96 words | 97 words = `C054` |
| random word write `1402/0002` | 80 words / weighted 960 | 81 words / weighted 972 = `C054` |
| random bit write `1402/0003` | 94 bits | 95 bits = `C053` |
| monitor register `0801/0002` | 96 words | 97 words = `C054` |

## Block `0406/1406`

R120P 4E / iQ-R treats block read/write as a positive path. Mixed block access with `D + M` succeeded for mixed word/bit write, readback, and restore.

| Kind | Positive path | Not a positive path |
|------|---------------|---------------------|
| Word block | `D`, `SD`, `W`, `TN`, `STN`, `CN`, `SW`, `Z`, `R`, `RD`, `ZR`, `LTN`, `LSTN` | `LCN` uses dedicated long-device routes; `LZ` uses 32-bit routes |
| Bit block | `X`, `Y`, `M`, `L`, `SM`, `F`, `V`, `B`, `TS`, `TC`, `STS`, `STC`, `CS`, `CC`, `SB`, `DX`, `DY` | `S` write, `LTS/LTC/LSTS/LSTC`, `LCS/LCC` block |

## Long-Device Handling

Long timers, long retentive timers, and long counters are exposed to users through dedicated long-device routes. The library selects the correct route from the long-device address so users do not need to know the direct/random/block differences.

| Target | Decision |
|--------|----------|
| `LTN10` | `read_long_timer` can read state and current value. `LTN10:D` write/read/restore succeeds |
| `LSTN10` | `read_long_retentive_timer` can read state and current value. `LSTN10:D` write/read/restore succeeds |
| `LTS/LTC/LSTS/LSTC` | State is decoded from the `LTN/LSTN` 4-word area. `LTC10:BIT`, `LSTC10:BIT` write/read/restore succeeds |
| `LCN10` | `LCN10:D` / `LCN10:L` write/read/restore succeeds |
| `LCS10:BIT` / `LCC10:BIT` | State read succeeds. `LCC10:BIT` write/read/restore succeeds |
| `LCS` | Contact device; do not write |

## `LZ` Handling

`LZ` is treated as a long-only device with only `LZ0/LZ1`. Do not use 16-bit direct/block routes; use named/random dword routes.

| Target | Decision |
|--------|----------|
| `LZ0` | random dword, named `:D`, and named `:L` write/read/restore succeed |
| `LZ1` | random dword, named `:D`, and named `:L` write/read/restore succeed |
| 16-bit direct/block | Not a positive path |

## `U\G/HG` Handling

R120P / RCPU adopts U-qualified extended access. `G` is unit buffer memory. `HG` is the iQ-R-only HG CPU-buffer route. Standalone `G/HG` is not used.

| Target | Decision |
|--------|----------|
| `U3E0\G10` | Supported by direct/random/monitor |
| `U3E0\HG20` | Supported by direct/random/monitor as the iQ-R-only HG CPU-buffer route |
| `U2\G100` | Supported by direct/random/monitor |

These results are used for the positive-path decision for this R120P configuration. Do not generalize them to every `Un\Gn`.

## Specification Conclusion

Treat `melsec:iq-r` as the 4E / iQ-R profile. Normal direct/random/block/monitor/named routes, dedicated long-device routes, the `LZ0/LZ1` 32-bit route, verified `U3E0\G...`, iQ-R-only `U3E0\HG...`, and `U2\G100` are positive paths. `S` write, invalid long-device direct/block routes, `LZ` 16-bit direct/block routes, `Z20` and later, and standalone `G/HG` are not positive paths.
