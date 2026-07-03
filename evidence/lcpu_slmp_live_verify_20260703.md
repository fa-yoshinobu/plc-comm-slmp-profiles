# MELSEC-L / LCPU SLMP Specification Decision Record

## Adopted Profile

| Item | Decision |
|------|----------|
| PLC profile | `melsec:lcpu` |
| Live model | Do not treat `0101/0000` as a positive path because it returns `C059` |
| Frame | 3E |
| Compatibility | Q/L-compatible |
| Standard subcommand | word=`0000`, bit=`0001` |
| Extended subcommand | word=`0080`, bit=`0081` |
| X/Y notation | Q/L-compatible notation |

Treat LCPU separately from `melsec:iq-l`. Do not carry R120P 4E / iQ-R assumptions, QnUDV `ZR` ranges, or R120P long-device positive paths into LCPU.

## Adopted Features

| Feature | Decision |
|---------|----------|
| Direct read/write `0401/1401` | Supported |
| Random read/write `0403/1402` | Supported |
| Monitor `0801/0802` | Supported |
| Named normal devices | Supported |
| `Z` | `Z0..Z19` supported |
| `R` | `R0..R32767` supported |
| `ZR` | `ZR0..ZR131071` supported |

`D10` / `M10` succeeded with direct and random write/read/restore. `D10`, `R10`, and `ZR10` succeeded with monitor. `Z10`, `R10`, and `ZR10` succeeded with direct/random/named `:U` write/read/restore.

## Features Not Adopted

| Feature | Decision | Evidence |
|---------|----------|----------|
| Type Name `0101/0000` | Not a positive path | `C059` |
| Block read/write `0406/1406` | Not a positive path | Raw send also returns `C059` |
| `U\G` extended access | Not a positive path | `U0\G10`, `U2\G1000` return `C070` |
| Long timer / long retentive timer | Not a positive path | Representative `LTN/LSTN` reads return `C05B` |
| Long counter | Not a positive path | Representative `LCN/LCC` reads return `C05B` |
| `LZ` | Not a positive path | `LZ0` raw/named read returns `C05B` |
| HG CPU-buffer route | Not a positive path | iQ-R only; not defined for LCPU |

## Out Of Scope For This Record

| Feature | Decision | Reason |
|---------|----------|--------|
| UDP route | Not decided here | This record covers TCP `1025` |
| UDF | Not tested here | Excluded by user request |

## Device Ranges

For this LCPU target, adopt the following ranges.

| Device | Adopted range | Out-of-range response | Notes |
|--------|---------------|-----------------------|-------|
| `Z` | `Z0..Z19` | `Z20` = `4031` | Supported |
| `R` | `R0..R32767` | `R32768` = `4031` | Supported |
| `ZR` | `ZR0..ZR131071` | `ZR131072` = `4031` | Do not carry over QnUDV `ZR0..ZR393215` |
| `D9000` | Out of range | `4031` | Do not use it as a base point for limit tests |

## Point Limits

| Command | Adopted limit | Over-limit response |
|---------|---------------|---------------------|
| direct word read `0401/0000` | 960 points | 961 points = `C051` |
| direct word write `1401/0000` | 960 points | 961 points = `C051` |
| direct bit read `0401/0001` | 7168 points | 7169 points = `C052` |
| direct bit write `1401/0001` | 7168 points | 7169 points = `C052` |
| random read `0403/0000` | 192 words | 193 words = `C054` |
| random word write `1402/0000` | 160 words / weighted 1920 | 161 words / weighted 1932 = `C054` |
| random bit write `1402/0001` | 188 bits | 189 bits = `C053` |

## Long Devices And `LZ`

On this LCPU, long-device families and `LZ` do not work. Do not carry over R120P dedicated long-device positive paths or `LZ0/LZ1` positive paths into LCPU.

| Target | Decision |
|--------|----------|
| `LTN0` / `LSTN0` | 4-word read returns `C05B` |
| `LCN0` | raw direct word read and named `LCN0:D` return `C05B` |
| `LCC0` | bit read and named `LCC0:BIT` return `C05B` |
| `LZ0` | raw direct word read and named `LZ0:D` / `LZ0:L` return `C05B` |

## Specification Conclusion

Treat `melsec:lcpu` as a 3E / Q-L-compatible profile. Normal direct/random/monitor/named routes, `Z0..Z19`, `R0..R32767`, and `ZR0..ZR131071` are positive paths. Type Name, block, `U\G` extended access, long-device families, `LZ`, and the iQ-R-only HG CPU-buffer route are not positive paths.
