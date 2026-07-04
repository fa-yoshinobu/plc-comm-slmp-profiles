# iQ-L / melsec:iq-l SLMP Live Verification

Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.
This is a decision record, not a communication log.

Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- On this iQ-L profile, `S` is read-only.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check.

## Session

| Item | Value |
|------|-------|
| Date | 2026-07-03 |
| PLC model | L16HCPU |
| PLC profile | `melsec:iq-l` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | supported / live | - | pass | `L16HCPU` |
| Direct read/write | supported / live | `D1000` / `M1000` | pass | Random word write verified; bit write verified and reset OFF |
| Random read/write | supported / live | `D1001`, `D1002`, `M1001`, `M1002` | pass | Random word write verified; bits reset OFF |
| Block read/write | supported / live | `D1100` / `M1100` | pass | Mixed block write verified; bits reset OFF |
| Monitor | supported / live | `D1000`, `D1001` | pass | Register and monitor cycle verified |
| Long timer/counter route | supported / live | `LT`, `LST`, `LC` all members | pass | `LTN/LTS/LTC`, `LSTN/LSTS/LSTC`, and `LCN/LCS/LCC` verified through intended long routes; bits reset OFF |
| LZ 32-bit route | supported / live | `LZ1:D` | pass | Random dword write verified through 32-bit route |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` | `J2\W100` | config | Returned `4031` in this configuration. Treat as link/network configuration-dependent, not a profile failure |
| `U...\G...` module buffer | `ext_module_access` | `U1\G10` | pass | Random word write verified. Unit/address availability remains configuration-dependent |
| `U3E0\HG...` CPU buffer | `hg_cpu_buffer` | - | spec | iQ-R-only route; not defined for iQ-L |
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
| Random word read | max 96, over `C054` | limit | 96 pass; 97 returned `C054` |
| Random word write | max 80, weighted max 960, over `C054` | limit | 80 word pass; 81 word returned `C054`; 40 word + 40 dword weighted over returned `C054` |
| Random bit write | max 94, over `C053` | limit | 94 pass and reset OFF; 95 returned `C053` |
| Monitor word register | max 96 | limit | 96 pass; 97 returned `C054` |
| Extended random word read | ext max 96, over `C054` | limit | 2026-07-04 `U1\G10` 0082 path: 96 pass; 97 returned `C054` |
| Extended random word write | ext max 80, weighted max 960, over `C054` | limit | 2026-07-04 `U1\G10` 0082 path: 80 word pass; 81 word returned `C054`; 68 dword pass; 69 dword returned `C054` |
| Extended random bit write | ext max 94, over `C053` | limit | 2026-07-04 0083 path: 94 `M1000...` reset writes pass; 95 returned `C053` |
| Extended monitor word register | ext max 96, over `C054` | limit | 2026-07-04 `U1\G10` 0082 path: 96 pass; 97 returned `C054` |

## Write Policy Checklist

For this iQ-L profile, the canonical policy is expected to be `S=read-only` unless the JSON changes.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` | read-only | policy | `S0` write rejected with `4030` |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X | dword-register | pass | `X0` reachable |
| Y | Y | dword-register | pass | `Y0` reachable |
| M | M | dword-register | pass | `M0` reachable |
| B | B | dword-register | pass | `B0` reachable |
| SB | SB | dword-register | pass | `SB0` reachable |
| F | F | dword-register | pass | `F0` reachable |
| V | V | dword-register | pass | `V0` reachable |
| L | L | dword-register | pass | `L0` reachable |
| S | S | dword-register | pass | `S0` reachable; write policy is separate |
| D | D | dword-register | pass | `D0` reachable |
| W | W | dword-register | pass | `W0` reachable |
| SW | SW | dword-register | pass | `SW0` reachable |
| R | R | dword-register-clipped | pass | `R0` reachable |
| T | TS / TC / TN | dword-register | pass | `TS0`, `TC0`, `TN0` reachable |
| ST | STS / STC / STN | dword-register | pass | `STS0`, `STC0`, `STN0` reachable |
| C | CS / CC / CN | dword-register | pass | `CS0`, `CC0`, `CN0` reachable |
| LT | LTS / LTC / LTN | dword-register | pass | Reachable by intended long routes |
| LST | LSTS / LSTC / LSTN | dword-register | pass | Reachable by intended long routes |
| LC | LCS / LCC / LCN | dword-register | pass | Reachable by intended long routes |
| Z | Z | word-register | pass | `Z0` reachable |
| LZ | LZ | word-register | pass | `LZ1` reachable through 32-bit route |
| ZR | ZR | dword-register | pass | `ZR0` reachable |
| RD | RD | dword-register | pass | `RD0` reachable |
| SM | SM | fixed | pass | `SM0` reachable |
| SD | SD | fixed | pass | `SD0` reachable |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | Adopt JSON expectations for `melsec:iq-l` | None |
| Qualified access | Adopt `U\G`; keep `J` link direct configuration-dependent; keep `HG` as iQ-R-only spec route | None |
| Limits | Adopt JSON limits for `melsec:iq-l`; 0082/0083 extended random and monitor routes have live evidence for ext-specific 96 / 80 weighted 960 / 94 limits | None |
| Write policy | Adopt `S=read-only` | None |
| Device families | All JSON-listed iQ-L device families are reachable | None |
