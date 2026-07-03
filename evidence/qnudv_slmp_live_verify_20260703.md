# QnUDV / melsec:qnudv SLMP Live Verification

Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.
This is a decision record, not a communication log.

Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- `S` write behavior is profile-specific. On QnUDV, raw SLMP write succeeds, but library policy keeps `S` write-prohibited to match the official tool.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check unless the user explicitly requests leaving them ON.

## Session

| Item | Value |
|------|-------|
| Date | 2026-07-03 |
| PLC model | Q06UDVCPU |
| PLC profile | `melsec:qnudv` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | blocked / live | `0101/0000` | spec | Returned `C059`; do not adopt as a positive path |
| Direct read/write | supported / live | `D9000` / `M9000` | pass | Random word write verified; bit write verified and reset OFF |
| Random read/write | supported / live | `D9001` / `M9001` | pass | Random word write verified; bit write verified and reset OFF |
| Block read/write | blocked / live | `D9000` / `M9000`, `D9100` / `M9100` | spec | Raw read/write block returned `C059`; do not adopt as a positive path |
| Monitor | supported / live | `D9000`, `R10`, `ZR10` | pass | Register and monitor cycle verified |
| Long timer/counter route | delegated / live | `LT`, `LST`, `LC` representatives | family | `LT/LST/LC` families returned `C05B`; range lookup decides absence |
| LZ 32-bit route | delegated / live | `LZ0` random dword | family | `LZ0` returned `C05B`; range lookup decides absence |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` | `J1\W100` | route | Read/write returned `C070`; do not adopt link direct as a QnUDV positive path |
| `U...\G...` module buffer | `ext_module_access` | `U0\G10`, `U2\G1000` | route | Returned `C070`; do not adopt `U\G` as a QnUDV built-in Ethernet positive path |
| `U3E0\HG...` CPU buffer | `hg_cpu_buffer` | - | spec | iQ-R-only route; not defined for QnUDV |
| Standalone `G` | common rule | - | spec | Not a standalone device route |
| Standalone `HG` | common rule | - | spec | Not a standalone device route |

## Limit Checklist

Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.

| Limit item | JSON value | Status | Decision note |
|------------|------------|--------|---------------|
| Direct word read | max 960, over `C051` | limit | 960 pass; 961 returned `C051` |
| Direct word write | max 960, over `C051` | limit | 960 pass; 961 returned `C051` |
| Direct bit read | max 7168, over `C052` | limit | 7168 pass; 7169 returned `C052` |
| Direct bit write | max 7168, over `C052` | limit | 7168 pass and reset OFF; 7169 returned `C052` |
| Random word read | max 192, over `C054` | limit | 192 pass; 193 returned `C054` |
| Random word write | max 160, weighted max 1920, over `C054` | limit | 160 pass; 161 returned `C054` |
| Random bit write | max 188, over `C053` | limit | 188 pass and reset OFF; 189 returned `C053` |
| Monitor word register | max 192, over `C054` | limit | 192 pass; 193 returned `C054` |

## Write Policy Checklist

For QnUDV, `S` write is prohibited by library policy to match the official tool.

| Device family | Adopted policy | Status | Decision note |
|---------------|----------------|--------|---------------|
| `S` | read-only | policy | Raw SLMP write succeeds, but do not expose `S` write as a library positive path because the official tool does not allow it |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X | word-register | pass | `X0` reachable |
| Y | Y | word-register | pass | `Y0` reachable |
| M | M | dword-register | pass | `M0` reachable |
| B | B | dword-register | pass | `B0` reachable |
| SB | SB | word-register | pass | `SB0` reachable |
| F | F | word-register | pass | `F0` reachable |
| V | V | word-register | pass | `V0` reachable |
| L | L | word-register | pass | `L0` reachable |
| S | S | word-register | pass | `S0` reachable; write policy is separate |
| D | D | dword-register | pass | `D0` reachable |
| W | W | dword-register | pass | `W0` reachable |
| SW | SW | word-register | pass | `SW0` reachable |
| R | R | dword-register-clipped | pass | `R0` reachable |
| T | TS / TC / TN | word-register | pass | `TS0`, `TC0`, `TN0` reachable |
| ST | STS / STC / STN | word-register | pass | `STS0`, `STC0`, `STN0` reachable |
| C | CS / CC / CN | word-register | pass | `CS0`, `CC0`, `CN0` reachable |
| LT | LTS / LTC / LTN | unsupported | family | `LTS0`, `LTC0`, `LTN0` returned `C05B` |
| LST | LSTS / LSTC / LSTN | unsupported | family | `LSTS0`, `LSTC0`, `LSTN0` returned `C05B` |
| LC | LCS / LCC / LCN | unsupported | family | `LCS0`, `LCC0`, `LCN0` returned `C05B` |
| Z | Z | fixed | pass | `Z0` reachable |
| LZ | LZ | unsupported | family | `LZ0` returned `C05B` through random dword route |
| ZR | ZR | dword-register | pass | `ZR0` reachable |
| RD | RD | unsupported | family | `RD0` returned `C05B` |
| SM | SM | fixed | pass | `SM0` reachable |
| SD | SD | fixed | pass | `SD0` reachable |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | Adopt direct, random, and monitor. Do not adopt type name or block for QnUDV built-in Ethernet | None |
| Qualified access | Do not adopt `J` link direct, `U\G`, or `HG` for QnUDV built-in Ethernet | None |
| Limits | Adopt JSON limits for `melsec:qnudv` | None |
| Write policy | Adopt `S=read-only` on QnUDV by library policy | None |
| Device families | Adopt observed QnUDV family results | None |
