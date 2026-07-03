# MELSEC iQ-L / L16HCPU SLMP Specification Decision Record

## Adopted Profile

| Item | Decision |
|------|----------|
| PLC profile | `melsec:iq-l` |
| Live model | `L16HCPU`, model code `0x48C2` |
| Frame | 4E |
| Compatibility | iQ-R-compatible |
| Standard subcommand | word=`0002`, bit=`0003` |
| Extended subcommand | word=`0082`, bit=`0083` |
| X/Y notation | hexadecimal |

Treat iQ-L separately from `melsec:lcpu`. Do not carry LCPU 3E / Q-L-compatible results into iQ-L.

## Errata

Rows below that describe `LCS` as "do not write" are not canonical write-policy evidence. The canonical write policy is maintained in `capability/slmp_builtin_ethernet_profiles.json`; as of the 2026-07-03 correction, `S=read-only` is the only write-policy restriction and it applies to every profile.

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
| `U1\G10` | Supported in this configuration |

`U1\G10` is configuration-dependent. The syntax and route are supported, but treat it as a positive path only when the target PLC configuration confirms that the unit exists.

## Features Not Adopted

| Feature | Decision | Evidence |
|---------|----------|----------|
| `S` write | Not a positive path | `S10` read succeeds; writes are stopped as read-only |
| `LZ2` | Not a positive path | named `LZ2:D` read returns `4031` |
| standalone `G/HG` | Not a positive path | Use U-qualified extended access |
| HG CPU-buffer route | Not a positive path | iQ-R only; not defined for iQ-L |

## Out Of Scope Or Undecided

| Feature | Decision | Reason |
|---------|----------|--------|
| link-direct | No positive/negative decision | No required hardware was available; it is likely usable by specification |
| UDP route | Not decided here | This record covers TCP `1025` |
| UDF | Not tested here | Excluded by user request |

## Device Ranges

Treat the `melsec:iq-l` range catalog as follows.

| Device | Adopted range | Notation |
|--------|---------------|----------|
| `X` | `X0000..X2FFF` | hexadecimal |
| `Y` | `Y0000..Y2FFF` | hexadecimal |
| `M` | `M0..M12287` | decimal |
| `B` | `B0000..B1FFF` | hexadecimal |
| `SB` | `SB000..SB7FF` | hexadecimal |
| `F` | `F0..F2047` | decimal |
| `V` | `V0..V2047` | decimal |
| `L` | `L0..L8191` | decimal |
| `S` | `S0..S1023` | decimal, read-only |
| `D` | `D0..D10239` | decimal |
| `W` | `W0000..W1FFF` | hexadecimal |
| `SW` | `SW000..SW7FF` | hexadecimal |
| `R` | `R0..R32767` | decimal |
| `TS/TC/TN` | `0..1023` | decimal |
| `STS/STC/STN` | `0..511` | decimal |
| `CS/CC/CN` | `0..511` | decimal |
| `LTS/LTC/LTN` | `0..1023` | decimal |
| `LSTS/LSTC/LSTN` | `0..511` | decimal |
| `LCS/LCC/LCN` | `0..511` | decimal |
| `Z` | `Z0..Z19` | decimal |
| `LZ` | `LZ0..LZ1` | decimal; positive path only through 32-bit routes |
| `ZR` | `ZR0..ZR716799` | decimal |
| `RD` | `RD0..RD524287` | decimal |
| `SM` | `SM0..SM4095` | decimal |
| `SD` | `SD0..SD4095` | decimal |

## Point Limits

| Command | Adopted limit | Over-limit response |
|---------|---------------|---------------------|
| direct word read `0401/0002` | 960 points | 961 points = `C051` |
| direct word write `1401/0002` | 960 points | 961 points = `C051` |
| direct bit read `0401/0003` | 7168 points | 7169 points = `C052` |
| direct bit write `1401/0003` | 7168 points | 7169 points = `C052` |
| random read `0403/0002` | 96 words | 97 words = `C054` |
| random word write `1402/0002` | 80 words | 81 words = `C054` |
| random bit write `1402/0003` | 94 bits | 95 bits = `C053` |

## Long-Device Handling

iQ-L treats long timers, long retentive timers, and long counters as positive paths. For users, route them through dedicated long-device helpers instead of exposing direct/random/block details.

| Target | Decision |
|--------|----------|
| `LTN10` | `read_long_timer` can read state and current value |
| `LSTN10` | `read_long_retentive_timer` can read state and current value |
| `LTS10:BIT` / `LTC10:BIT` | named state read succeeds |
| `LSTS10:BIT` / `LSTC10:BIT` | named state read succeeds |
| `LTN10:D` | write/read/restore succeeds |
| `LSTN10:D` | write/read/restore succeeds |
| `LCN10:D` | write/read/restore succeeds |
| `LCC10:BIT` | write/read/restore succeeds |
| `LCS` | Contact device used for reads; do not write |

Verification values:

```text
LTN10:D   0 -> 0x00001234 -> 0
LSTN10:D  0 -> 0x00002345 -> 0
LCN10:D   0 -> 0x00003456 -> 0
LCC10:BIT False -> True -> False
```

## `LZ` Handling

`LZ` is treated as a long-only device with only `LZ0/LZ1`. Do not use 16-bit direct/block routes; use named/random dword routes.

| Target | Decision |
|--------|----------|
| `LZ0/LZ1` | Positive path through 32-bit routes |
| `LZ1:D` | `0 -> 0x00004567 -> 0` write/read/restore succeeds |
| `LZ2:D` | Not a positive path because it returns `4031` |

## `U\G` Handling

`Un\Gn` is configuration-dependent. In this iQ-L / L16HCPU configuration, `U1\G10` succeeded with direct extended word `0401/0082` / `1401/0082` write/read/restore.

```text
U1\G10 0x0000 -> 0x4567 -> 0x0000
```

This result is used for the positive-path decision for `U1\G10`; do not generalize it to every `Un\Gn`.

## Specification Conclusion

Treat `melsec:iq-l` separately from `melsec:lcpu` and use a 4E / iQ-R-compatible profile. Normal direct/random/block/monitor/named routes, long-device routes, `LZ0/LZ1`, and verified `U1\G10` are positive paths. `S` write, `LZ2`, standalone `G/HG`, and the iQ-R-only HG CPU-buffer route are not positive paths. Link-direct is unverified because hardware was not available, but remains a likely-supported undecided item.
