# MELSEC iQ-F / FX5 SLMP Specification Decision Record

## Adopted Profile

| Item | Decision |
|------|----------|
| PLC profile | `melsec:iq-f` |
| Frame | 3E |
| Compatibility | Q/L-compatible |
| Standard subcommand | word=`0000`, bit=`0001` |
| Extended subcommand | word=`0080`, bit=`0081` |
| X/Y notation | octal |

Do not carry over R120P 4E / iQ-R assumptions, QnUDV / LCPU device ranges, or the R120P `U\G` positive path to iQ-F.

## Adopted Features

For iQ-F / FX5, adopt the following positive paths.

| Feature | Decision |
|---------|----------|
| Type Name `0101/0000` | Supported |
| Direct read/write `0401/1401` | Supported |
| Random read/write `0403/1402` | Supported |
| Block read/write `0406/1406` | Supported |
| Named normal devices | Supported |
| `LC` long counter | `LC0..LC63` supported |
| `LZ` | `LZ0/LZ1` supported through 32-bit routes |
| `U1\G...` | Supported when the special unit exists in the PLC configuration |

`U1\G...` is configuration-dependent. It is not always available on every iQ-F target; treat it as a positive path only when the target PLC configuration confirms the unit exists.

## Features Not Adopted

| Feature | Decision | Evidence |
|---------|----------|----------|
| Monitor `0801/0802` | Not a positive path | Not listed for FX5 in the target manual; `0801/0000` single `D10` registration is also rejected on hardware |
| `U0\G0` | Not a positive path | `C060` |
| `U2\G1000` | Not a positive path | `C060` |
| `ZR` | Not a positive path | `C05C` |
| `RD` | Not a positive path | `C05C` |
| `V` | Not a positive path | `C05C` |
| `LT` / `LST` | Not a positive path | `C05C` |
| HG CPU-buffer route | Not a positive path | iQ-R only; not defined for iQ-F |

## Out Of Scope For This Record

| Feature | Decision | Reason |
|---------|----------|--------|
| UDP route | Not decided here | This record covers TCP `1025`; UDP had already been checked separately and is not included here |
| UDF | Not tested here | Excluded by user request |

## Device Ranges

Treat the iQ-F / FX5 ranges resolved from SD registers as follows.

```text
X=1024, Y=1024, M=7680, B=256, SB=512, F=128, L=7680,
D=8000, W=512, SW=512, T=512, ST=16, C=256,
LC=64, Z=20, LZ=2, R=32768
```

| Device | Adopted range | Out-of-range response | Notes |
|--------|---------------|-----------------------|-------|
| `X` | `X0..X1777` | `X2000` = `C056` | Octal notation; input device, therefore read-only |
| `Y` | `Y0..Y1777` | `Y2000` = `C056` | Octal notation; write/read/restore succeeds |
| `Z` | `Z0..Z19` | `Z20` = `C056` | Supported |
| `R` | `R0..R32767` | `R32768` = `C056` | Supported |
| `LC` | `LC0..LC63` | `LC64` = `C056` | Treat as long counter |
| `LZ` | `LZ0..LZ1` | `LZ2` = `C056` | Positive path only through 32-bit routes |

## Point Limits

| Command | Adopted limit | Over-limit response |
|---------|---------------|---------------------|
| direct word read `0401/0000` | 960 points | 961 points = `C052` |
| direct word write `1401/0000` | 960 points | 961 points = `C052` |
| direct bit read `0401/0001` | 3584 points | 3585 points = `C051` |
| direct bit write `1401/0001` | 3584 points | 3585 points = `C051` |
| random read `0403/0000` | 192 words | 193 words = `C054` |
| random word write `1402/0000` | 160 words | 161 words = `C054` |
| random bit write `1402/0001` | 188 bits | 189 bits = `C053` |

## `U\G` Handling

`Un\Gn` is configuration-dependent on iQ-F as well. The library supports the syntax and frame route, but `C060` from a target without the corresponding unit is treated as a PLC configuration result.

The HG CPU-buffer route is iQ-R only and is not defined for iQ-F. On iQ-F, the verified target is G-type unit buffer access such as `U1\G...`.

| Target | Decision |
|--------|----------|
| `U0\G0` | Not a positive path in this configuration because it returns `C060` |
| `U1\G0` | read/write/restore succeeds with the special-unit configuration |
| `U1\G1` | read/write/restore succeeds with the special-unit configuration |
| `U1\G10` | read/write/restore succeeds with the special-unit configuration |
| `U2\G1000` | Not a positive path in this configuration because it returns `C060` |

Observed `U1\G...` values:

| Target | Verification result |
|--------|---------------------|
| `U1\G0` | `0x0000 -> 0x1234 -> 0x0000`, recheck `0x0000 -> 0x1357 -> 0x0000` |
| `U1\G1` | `0x0000 -> 0x2345 -> 0x0000`, recheck `0x0000 -> 0x2468 -> 0x0000` |
| `U1\G10` | `0x0000 -> 0x3456 -> 0x0000`, recheck `0x0000 -> 0x3579 -> 0x0000` |

Conclusion: `U1\G...` is a positive path for direct extended word `0401/0080` / `1401/0080` when the FX5U configuration includes the special unit. Do not generalize this to every `Un\Gn`.

## FX5UC / FX5U Differences

| Item | FX5UC-32MT/D | FX5U-32MR/DS with special unit | Specification decision |
|------|--------------|--------------------------------|------------------------|
| Type Name | `FX5UC-32MT/D`, model `0x4A91` | `FX5U-32MR/DS`, model `0x4A41` | Model name only |
| Normal direct/random/named | Succeeds | Succeeds | Treat the same |
| block `0406/1406` | Succeeds | Succeeds | Positive path |
| monitor `0801/0802` | Not adopted | Not adopted | Not listed for FX5 in the target manual; hardware also rejects registration |
| SD ranges | Same | Same | Treat the same |
| `LC` / `LZ` | Succeeds | Succeeds | Positive path |
| `ZR/RD/V/LT/LST` | `C05C` | `C05C` | Not a positive path |
| `U1\G...` | `C060` or not checked | Succeeds | Configuration-dependent |

FX5UC and FX5U use the same decisions for normal features, boundaries, and ranges. The only difference is whether `U1\G...` is available through a special-unit configuration; that is a configuration difference, not a PLC-series difference.

## Specification Conclusion

Treat `melsec:iq-f` as a 3E / Q-L-compatible profile. Normal direct/random/block/named routes, `LC`, and `LZ` are positive paths. Monitor, `ZR/RD/V/LT/LST`, and the iQ-R-only HG CPU-buffer route are not positive paths. `U\G` syntax and routing are supported, but it is a positive path only when the target unit exists.
