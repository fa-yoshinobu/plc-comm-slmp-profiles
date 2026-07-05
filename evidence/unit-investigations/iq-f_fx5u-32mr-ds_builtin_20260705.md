# FX5U-32MR/DS Built-in Ethernet SLMP Live Verification

Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.
This is a decision record, not a communication log.

Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- On this iQ-F profile, `S` is read/write-capable; other PLC profiles keep their own evidence.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check.

## Session

| Item | Value |
|------|-------|
| Date | 2026-07-05 |
| PLC model | FX5U-32MR/DS built-in Ethernet |
| PLC profile | `melsec:iq-f` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification. Plan run `evidence/unit-investigations/plans/runs/iq-f_fx5u-32mr-ds_builtin_20260705_033024/results.json` recorded 25/25 items, waived 0, errors 0. JSON was not changed. |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | supported / live | `0101/0000` | pass | 3E returned `0000`, text `FX5U-32MR/DS`, raw type-code bytes `414A` |
| Direct read/write | supported / live | `D0`, `M0`, `D1000`, `M1000` | pass | Read and write returned `0000`; bit write was reset OFF and verified |
| Random read/write | supported / live | `D1000`, `M1000` | pass | Plain random read/write returned `0000`; bit write was reset OFF |
| Block read/write | supported / live | `D1000`, `M1000` | pass | Read block and write block returned `0000`; tested bit block was reset OFF |
| Monitor | blocked / live | `D0`, `D1000`, `U1\G100` | spec | Monitor registration returned `C059`; monitor execute row returned `C059`; keep monitor not adopted for iQ-F |
| Long timer/counter route | supported LC route; LT/LST unsupported | `LCN0`, `LCS0`, `LCC0`, `LTN0`, `LSTN0`, raw `LTS0`, raw `LTC0`, raw `LSTS0`, raw `LSTC0` | pass | `LCN0`, `LCS0`, and `LCC0` returned `0000`; `LTN0`, `LSTN0`, and raw LT/LST probes returned `C05C` |
| LZ 32-bit route | supported dword route | `LZ0` | pass | `LZ0` random dword route returned `0000` |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` | `J1\X100`, `J1\Y100`, `J1\B100`, `J1\W100`, `J1\SB100`, `J1\SW100` | route | Read-only supplemental probes all returned `C05B`; do not adopt link direct as an iQ-F positive path |
| `U...\G...` module buffer | `ext_module_access` | `U1\G100` | config | Configured target returned `C060` in this run; no positive `U\G` module-buffer path was observed for the current configuration |
| `U3E0\HG...` CPU buffer | iQ-R-only route | `U3E0\HG0` | spec | Read-only probe returned `C05C`; keep `HG` blocked/not adopted for iQ-F |
| Standalone `G` | common rule | - | spec | Not a standalone device route |
| Standalone `HG` | common rule | - | spec | Not a standalone device route |

## Limit Checklist

Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.
For random word write, verify the count limit and the weighted limit separately when `weighted max` is defined.
The weighted-limit probe must keep the total point count within `max` and exceed only `weighted max`; do not treat `81 word` or `161 word` count-over probes as weighted-limit evidence.
For extended random routes, verify the ext-specific limit rows separately from the plain random rows.

| Limit item | JSON value | Status | Decision note |
|------------|------------|--------|---------------|
| Direct word read | max 960, over `C052` | limit | 960 pass; 961 returned `C052` |
| Direct word write | max 960, over `C052` | limit | 960 pass; 961 returned `C052` |
| Direct bit read | max 3584, over `C051` | limit | 3584 pass; 3585 returned `C051` |
| Direct bit write | max 3584, over `C051` | limit | 3584 pass and reset OFF; 3585 returned `C051` |
| Random word read | max 192, over `C054` | limit | 192 word pass; 193 word returned `C054` |
| Random word write count | max 160, over `C054` | limit | 160 word pass; 161 word returned `C054` |
| Random word write weighted | weighted max 1920, over `C054` | limit | 137 dword pass; 138 dword returned `C054` |
| Random bit write | max 188, over `C053` | limit | 188 pass and reset OFF; 189 returned `C053` |
| Monitor word register | not adopted | spec | 1 point returned `C059`; monitor is blocked for iQ-F |
| Extended random word read (`U1\G`) | ext max 96, over `C054` | config | `U1\G100` returned `C060` at 1 point; ext word-read limit was not reached in this run |
| Extended random word write count (`U1\G`) | ext max 80, over `C054` | config | `U1\G100` returned `C060` at 1 point; ext word-write count limit was not reached in this run |
| Extended random word write weighted (`U1\G`) | ext weighted max 960, over `C054` | config | `U1\G100` dword test returned `C060` at 1 point; ext weighted limit was not reached in this run |
| Extended random bit write (`M` via 0081) | ext max 94, over `C053` | limit | `M1000` passed at 94, reset OFF, and returned `C053` at 95 |
| Extended monitor word register (`U1\G`) | not adopted | spec | `U1\G100` monitor registration returned `C059`; ext monitor is blocked for iQ-F |

## Write Policy Checklist

For this iQ-F profile, `S` is read/write-capable.
Do not keep noise such as "not written to a nonexistent address". If a write result is needed, use an address that exists for the connected PLC.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` | read/write | pass | Raw SLMP write/read/reset/read to `S2` returned `0000`, `0000`, `0000`, `0000`; adopt `S` as write-capable for this target |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X | iq-f baseline dword-register | pass | `X0` returned `0000` |
| Y | Y | iq-f baseline dword-register | pass | `Y0` returned `0000` |
| M | M | iq-f baseline dword-register | pass | `M0` returned `0000` |
| B | B | iq-f baseline dword-register | pass | `B0` returned `0000` |
| SB | SB | iq-f baseline dword-register | pass | `SB0` returned `0000` |
| F | F | iq-f baseline dword-register | pass | `F0` returned `0000` |
| V | V | unsupported | family | `V0` returned `C05C` |
| L | L | iq-f baseline dword-register | pass | `L0` returned `0000` |
| S | S | supported | pass | `S0` returned `0000`; write policy is separate |
| D | D | iq-f baseline dword-register | pass | `D0` returned `0000` |
| W | W | iq-f baseline dword-register | pass | `W0` returned `0000` |
| SW | SW | iq-f baseline dword-register | pass | `SW0` returned `0000` |
| R | R | iq-f baseline dword-register-clipped | pass | `R0` returned `0000` |
| T | TS / TC / TN | iq-f baseline dword-register | pass | `TS0`, `TC0`, and `TN0` returned `0000` |
| ST | STS / STC / STN | iq-f baseline dword-register | pass | `STS0`, `STC0`, and `STN0` returned `0000` |
| C | CS / CC / CN | iq-f baseline dword-register | pass | `CS0`, `CC0`, and `CN0` returned `0000` |
| LT | LTS / LTC / LTN | unsupported | family | Intended `LTN0` word4 returned `C05C`; raw-device-code probes `LTS0` and `LTC0` returned `C05C` |
| LST | LSTS / LSTC / LSTN | unsupported | family | Intended `LSTN0` word4 returned `C05C`; raw-device-code probes `LSTS0` and `LSTC0` returned `C05C` |
| LC | LCS / LCC / LCN | iq-f baseline dword-register | pass | `LCS0`, `LCC0`, and intended `LCN0` dword random route returned `0000` |
| Z | Z | iq-f baseline word-register | pass | `Z0` returned `0000` |
| LZ | LZ | iq-f baseline word-register | pass | `LZ0` returned `0000` |
| ZR | ZR | unsupported | family | `ZR0` returned `C05C` |
| RD | RD | unsupported | family | `RD0` returned `C05C` |
| SM | SM | iq-f baseline fixed 4096 | pass | `SM0` returned `0000` |
| SD | SD | iq-f baseline fixed 4096 | pass | `SD0` returned `0000` |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | `melsec:iq-f` built-in profile type-name, direct, plain random, block, LC long route, and `LZ` routes passed over 3E/Q-L; monitor remains blocked; `J`, `HG`, and current `U1\G100` module-buffer ext word route are not positive routes in this run | None |
| Limits | Plain limits match the iQ-F shape: random read 192/193 `C054`, random word write 160/161 `C054`, weighted dword 137/138 `C054`, random bit write 188/189 `C053`, direct word 960/961 `C052`, direct bit 3584/3585 `C051`; `M1000` ext bit limit is 94/95 `C053`; `U1\G100` ext word rows returned `C060` at 1 point, so no ext word boundary was obtained in this run | None |
| Write policy | Raw `S` write/read/reset/read returned all `0000`; keep `S` read/write-capable | None |
| Device families | Adopt observed iQ-F family results including unsupported `V`, `LT`, `LST`, `ZR`, and `RD`; `LC` and `LZ` are reachable | None |
