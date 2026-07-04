# iQ-F / melsec:iq-f SLMP Live Verification

Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.
This is a decision record, not a communication log.

Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- On this iQ-F profile, `S` is read/write-capable; other PLC profiles keep their own evidence.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check unless the user explicitly requests leaving them ON.

## Session

| Item | Value |
|------|-------|
| Date | 2026-07-03 |
| PLC model | FX5U-32MR/DS |
| PLC profile | `melsec:iq-f` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | supported / live | - | pass | `FX5U-32MR/DS` |
| Direct read/write | supported / live | `D1000` / `M1000` | pass | Random word write verified; bit write verified and reset OFF |
| Random read/write | supported / live | `D1001`, `D1002`, `M1001`, `M1002` | pass | Random word write verified; bits reset OFF |
| Block read/write | supported / live | `D1100` / `M1100` | pass | Mixed block write verified; bits reset OFF |
| Monitor | blocked / live | `D10` | spec | Registration rejected with `C059`; not adopted for iQ-F |
| Long timer/counter route | supported / live | `LC` all members | pass | `LCN/LCS/LCC` verified through intended long routes; bits reset OFF. `LT/LST` families do not exist on iQ-F |
| LZ 32-bit route | supported / live | `LZ0:D` | pass | Random dword write verified through 32-bit route |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` | `J1\W100` | route | `J1\W100` read/write returned `C05B`; do not adopt link direct as an iQ-F positive path |
| `U...\G...` module buffer | `ext_module_access` | `U1\G10` | pass | Random word write verified. Unit/address availability remains configuration-dependent |
| `U3E0\HG...` CPU buffer | `hg_cpu_buffer` | - | spec | iQ-R-only route; not defined for iQ-F |
| Standalone `G` | common rule | - | spec | Not a standalone device route |
| Standalone `HG` | common rule | - | spec | Not a standalone device route |

## Limit Checklist

Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.

| Limit item | JSON value | Status | Decision note |
|------------|------------|--------|---------------|
| Direct word read | max 960, over `C052` | limit | 960 pass; 961 returned `C052` |
| Direct word write | max 960, over `C052` | limit | 960 pass; 961 returned `C052` |
| Direct bit read | max 3584, over `C051` | limit | 3584 pass; 3585 returned `C051` |
| Direct bit write | max 3584, over `C051` | limit | 3584 pass and reset OFF; 3585 returned `C051` |
| Random word read | max 192, over `C054` | limit | 192 pass; 193 returned `C054` |
| Random word write | max 160, weighted max 1920, over `C054` | limit | 160 word pass; 161 word returned `C054`; 138 dword weighted over returned `C054` |
| Random bit write | max 188, over `C053` | limit | 188 pass and reset OFF; 189 returned `C053` |
| Monitor word register | not adopted | spec | Monitor feature is not adopted for iQ-F |
| Extended random word read | implementation rule: `min(profile, 008x default)` | limit | `U1\G0` 0080 path: 96 pass; 97 returned `C054` |
| Extended random word write | implementation rule: `min(profile, 008x default)` weighted max 960 | limit | `U1\G0` 0080 path: 80 word pass; 81 word returned `C054`; 68 dword pass; 69 dword returned `C054`; readback is not used as a decision condition because the unit may overwrite buffer values |
| Extended random bit write | implementation rule: `min(profile, 008x default)` max 94 | limit | 0081 path: 94 M-bit reset writes pass; 95 returned `C053` |
| Extended monitor register | not adopted | spec | `U1\G0` 0080 monitor registration returned `C059` at both 96 and 97 points; not usable as a point-limit boundary for iQ-F |

## Write Policy Checklist

For this iQ-F profile, `S` is read/write-capable.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` | read/write | pass | Read/write access to `S` is adopted for this profile |

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
| V | V | unsupported | family | `V0` returned `C05C` |
| L | L | dword-register | pass | `L0` reachable |
| S | S | supported | pass | `S` is reachable; write policy is separate |
| D | D | dword-register | pass | `D0` reachable |
| W | W | dword-register | pass | `W0` reachable |
| SW | SW | dword-register | pass | `SW0` reachable |
| R | R | dword-register | pass | `R0` reachable |
| T | TS / TC / TN | dword-register | pass | `TS0`, `TC0`, `TN0` reachable |
| ST | STS / STC / STN | dword-register | pass | `STS0`, `STC0`, `STN0` reachable |
| C | CS / CC / CN | dword-register | pass | `CS0`, `CC0`, `CN0` reachable |
| LT | LTS / LTC / LTN | unsupported | family | `LTS0`, `LTC0`, `LTN0` returned `C05C` |
| LST | LSTS / LSTC / LSTN | unsupported | family | `LSTS0`, `LSTC0`, `LSTN0` returned `C05C` |
| LC | LCS / LCC / LCN | dword-register | pass | Reachable by intended long routes |
| Z | Z | word-register | pass | `Z0` reachable |
| LZ | LZ | word-register | pass | `LZ0` reachable through 32-bit route |
| ZR | ZR | unsupported | family | `ZR0` returned `C05C` |
| RD | RD | unsupported | family | `RD0` returned `C05C` |
| SM | SM | fixed | pass | `SM0` reachable |
| SD | SD | fixed | pass | `SD0` reachable |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | Adopt JSON expectations for `melsec:iq-f`; monitor remains not adopted | None |
| Qualified access | Adopt `U\G`; do not adopt `J` link direct; keep `HG` as iQ-R-only spec route | None |
| Limits | Adopt JSON limits for `melsec:iq-f`; for 008x extended random routes, use the implementation rule `min(profile limit, 008x default)` rather than adding separate profile keys | None |
| Write policy | Adopt `S` as read/write-capable for `melsec:iq-f` | None |
| Device families | Adopt observed iQ-F family results including `S` support | None |
