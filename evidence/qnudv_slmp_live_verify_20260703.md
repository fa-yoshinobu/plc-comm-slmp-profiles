# QnUDV Built-In CPU SLMP Specification Decision Record

## Adopted Profile

| Item | Decision |
|------|----------|
| PLC profile | `melsec:qnudv` |
| Live model | Do not treat `0101/0000` as a positive path because it returns `C059` |
| Frame | 3E |
| Compatibility | Q/L-compatible |
| Standard subcommand | word=`0000`, bit=`0001` |
| Extended subcommand | word=`0080`, bit=`0081` |
| X/Y notation | Q/L-compatible notation |

Treat QnUDV built-in Ethernet as a different target from the R120P 4E / iQ-R path. Do not carry R120P block, long-device, or `U\G` positive paths into QnUDV.

## Adopted Features

| Feature | Decision |
|---------|----------|
| Direct read/write `0401/1401` | Supported |
| Random read/write `0403/1402` | Supported |
| Monitor `0801/0802` | Supported |
| Named normal devices | Supported |
| `Z` | `Z0..Z19` supported |
| `R` | `R0..R32767` supported |
| `ZR` | `ZR0..ZR393215` supported |

`D9000` direct/random word and `Y1FFF` direct/random bit write/read/restore succeeded. `D9000:U` / `Y1FFF:BIT` named read succeeded. `Z10`, `R10`, and `ZR10` direct/random/named `:U` write/read/restore succeeded. Monitor registration and execution succeeded with `D9000`, `R10`, and `ZR10`.

## Features Not Adopted

| Feature | Decision | Evidence |
|---------|----------|----------|
| Type Name `0101/0000` | Not a positive path | `C059` |
| Block read/write `0406/1406` | Not a positive path | Raw send also returns `C059`; high-level APIs should guard before transport |
| `U\G` extended access | Not a positive path | `U0\G10`, `U2\G1000` return `C070` |
| Long timer / long retentive timer | Not a positive path | Representative `LTN/LSTN` reads return `C05B` |
| Long counter | Not a positive path | Representative `LCN/LCC` reads return `C05B` |
| HG CPU-buffer route | Not a positive path | iQ-R only; not defined for QnUDV |

## Out Of Scope For This Record

| Feature | Decision | Reason |
|---------|----------|--------|
| UDP route | Not decided here | This record covers TCP `1025` |
| UDF | Not tested here | Excluded by user request |

## Device Ranges

For this QnUDV target, adopt the following ranges.

| Device | Adopted range | Out-of-range response | Notes |
|--------|---------------|-----------------------|-------|
| `Z` | `Z0..Z19` | `Z20` = `4031` | Supported |
| `R` | `R0..R32767` | `R32768` = `4031` | Supported |
| `ZR` | `ZR0..ZR393215` | `ZR393216` = `4031` | Adopted for this QnUDV built-in CPU |

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
| monitor register `0801/0000` | 192 words | 193 words = `C054` |

## Long-Device Handling

On this QnUDV target, long timers, long retentive timers, and long counters do not work. Do not carry over the dedicated long-device routes that work on R120P.

| Target | Decision |
|--------|----------|
| `LTN10` / `LTN0` | 4-word read returns `C05B` |
| `LSTN10` / `LSTN0` | 4-word read returns `C05B` |
| `LTS/LTC/LSTS/LSTC` | named state read depends on the underlying `LTN/LSTN` read, which returns `C05B` |
| `LCN10` / `LCN0` | dword read returns `C05B` |
| `LCC10` / `LCC0` | bit read returns `C05B` |

## Specification Conclusion

Treat `melsec:qnudv` as a 3E / Q/L-compatible profile. Normal direct/random/monitor/named routes, `Z0..Z19`, `R0..R32767`, and `ZR0..ZR393215` are positive paths. Type Name, block, `U\G` extended access, long-device families, and the iQ-R-only HG CPU-buffer route are not positive paths. Because QnUDV live hardware returned `C059` for block, high-level APIs should guard block before transport.
