# L16HCPU Built-in Ethernet SLMP Live Verification

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
| Date | 2026-07-05 |
| PLC model | L16HCPU built-in Ethernet |
| PLC profile | `melsec:iq-l` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification. Plan run `evidence/unit-investigations/plans/runs/iq-l_l16hcpu_builtin_20260705_024832/results.json` recorded 29/29 items, waived 0, errors 0. JSON was not changed. |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | supported / live | `0101/0000` | pass | 4E returned `0000`, text `L16HCPU`, raw type-code bytes `C248` |
| Direct read/write | supported / live | `D0`, `M0`, `D1000`, `M1000` | pass | Read and write returned `0000`; bit write was reset OFF and verified |
| Random read/write | supported / live | `D1000`, `M1000` | pass | Plain random read/write returned `0000`; bit write was reset OFF |
| Block read/write | supported / live | `D1000`, `M1000` | pass | Read block and write block returned `0000`; tested bit block was reset OFF |
| Monitor | supported / live | `D1000` | pass | Register and monitor execute returned `0000` |
| Long timer/counter route | supported intended long routes | `LTN0`, `LSTN0`, `LCS0`, `LCC0`, `LCN0`, raw `LTS0`, raw `LTC0`, raw `LSTS0`, raw `LSTC0` | pass | Intended routes `LTN0` word4, `LSTN0` word4, `LCN0` dword random, `LCS0`, and `LCC0` returned `0000`; raw-device-code probes `LTS0`, `LTC0`, `LSTS0`, and `LSTC0` returned `4030` |
| LZ 32-bit route | supported dword route | `LZ0` | pass | `LZ0` random dword route returned `0000` |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` | `J2\X100`, `J2\Y100`, `J2\B100`, `J2\W100`, `J2\SB100`, `J2\SW100` | config | Read-only supplemental probes all returned `4031`; no reachable J target is configured in this session, so this is not positive route evidence |
| `U...\G...` module buffer | `ext_module_access` | `U1\G100` | config | Configured target returned `0000`; unit number and buffer address are configuration-dependent by design |
| `U3E0\G...` CPU/module buffer | routed module access | `U3E0\G0` | config | Configured target returned `0000`; use routed form only |
| `U3E0\HG...` CPU buffer | iQ-R-only route | `U3E0\HG0` | spec | Read-only probe returned `4031`; keep `HG` blocked/not adopted for iQ-L |
| Standalone `G` | common rule | - | spec | Not a standalone device route |
| Standalone `HG` | common rule | - | spec | Not a standalone device route |

## Limit Checklist

Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.
For random word write, verify the count limit and the weighted limit separately when `weighted max` is defined.
The weighted-limit probe must keep the total point count within `max` and exceed only `weighted max`; do not treat `81 word` or `161 word` count-over probes as weighted-limit evidence.
For extended random routes, verify the ext-specific limit rows separately from the plain random rows.

| Limit item | JSON value | Status | Decision note |
|------------|------------|--------|---------------|
| Direct word read | max 960, over `C051` | limit | 960 pass; 961 returned `C051` |
| Direct word write | max 960, over `C051` | limit | 960 pass; 961 returned `C051` |
| Direct bit read | max 7168, over `C052` | limit | 7168 pass; 7169 returned `C052` |
| Direct bit write | max 7168, over `C052` | limit | 7168 pass and reset OFF; 7169 returned `C052` |
| Random word read | max 96, over `C054` | limit | 96 word pass; 97 word returned `C054` |
| Random word write count | max 80, over `C054` | limit | 80 word pass; 81 word returned `C054` |
| Random word write weighted | weighted max 960, over `C054` | limit | 68 dword pass; 69 dword returned `C054` |
| Random bit write | max 94, over `C053` | limit | 94 pass and reset OFF; 95 returned `C053` |
| Monitor word register | max 96, over `C054` | limit | 96 pass; 97 returned `C054` |
| Extended random word read (`U1\G`) | ext max 96, over `C054` | limit | `U1\G100` passed at 96 and returned `C054` at 97 |
| Extended random word read (`U3E0\G`) | ext max 96, over `C054` | limit | `U3E0\G0` passed at 96 and returned `C054` at 97 |
| Extended random word write count (`U1\G`) | ext max 80, over `C054` | limit | `U1\G100` passed at 80 and returned `C054` at 81 |
| Extended random word write count (`U3E0\G`) | ext max 80, over `C054` | limit | `U3E0\G0` passed at 80 and returned `C054` at 81 |
| Extended random word write weighted (`U1\G`) | ext weighted max 960, over `C054` | limit | `U1\G100` dword test passed at 68 and returned `C054` at 69 |
| Extended random word write weighted (`U3E0\G`) | ext weighted max 960, over `C054` | limit | `U3E0\G0` dword test passed at 68 and returned `C054` at 69 |
| Extended random bit write (`M` via 0083) | ext max 94, over `C053` | limit | `M1000` passed at 94, reset OFF, and returned `C053` at 95 |
| Extended monitor word register (`U1\G`) | ext max 96, over `C054` | limit | `U1\G100` register passed at 96 and returned `C054` at 97 |
| Extended monitor word register (`U3E0\G`) | ext max 96, over `C054` | limit | `U3E0\G0` register passed at 96 and returned `C054` at 97 |

## Write Policy Checklist

For this iQ-L profile, the canonical policy is expected to be `S=read-only` unless the JSON changes.
Do not keep noise such as "not written to a nonexistent address". If a write result is needed, use an address that exists for the connected PLC.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` | read-only | policy | Raw SLMP write to `S2` returned `4030`; keep `S` write-prohibited for this target |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X | iq-l baseline dword-register | pass | `X0` returned `0000` |
| Y | Y | iq-l baseline dword-register | pass | `Y0` returned `0000` |
| M | M | iq-l baseline dword-register | pass | `M0` returned `0000` |
| B | B | iq-l baseline dword-register | pass | `B0` returned `0000` |
| SB | SB | iq-l baseline dword-register | pass | `SB0` returned `0000` |
| F | F | iq-l baseline dword-register | pass | `F0` returned `0000` |
| V | V | iq-l baseline dword-register | pass | `V0` returned `0000` |
| L | L | iq-l baseline dword-register | pass | `L0` returned `0000` |
| S | S | iq-l baseline dword-register | pass | `S0` returned `0000`; write policy is separate |
| D | D | iq-l baseline dword-register | pass | `D0` returned `0000` |
| W | W | iq-l baseline dword-register | pass | `W0` returned `0000` |
| SW | SW | iq-l baseline dword-register | pass | `SW0` returned `0000` |
| R | R | iq-l baseline dword-register-clipped | pass | `R0` returned `0000` |
| T | TS / TC / TN | iq-l baseline dword-register | pass | `TS0`, `TC0`, and `TN0` returned `0000` |
| ST | STS / STC / STN | iq-l baseline dword-register | pass | `STS0`, `STC0`, and `STN0` returned `0000` |
| C | CS / CC / CN | iq-l baseline dword-register | pass | `CS0`, `CC0`, and `CN0` returned `0000` |
| LT | LTS / LTC / LTN | iq-l baseline dword-register | pass | Intended `LTN0` word4 route returned `0000`; raw-device-code probes `LTS0` and `LTC0` returned `4030` |
| LST | LSTS / LSTC / LSTN | iq-l baseline dword-register | pass | Intended `LSTN0` word4 route returned `0000`; raw-device-code probes `LSTS0` and `LSTC0` returned `4030` |
| LC | LCS / LCC / LCN | iq-l baseline dword-register | pass | `LCS0`, `LCC0`, and intended `LCN0` dword random route returned `0000` |
| Z | Z | iq-l baseline word-register | pass | `Z0` returned `0000` |
| LZ | LZ | iq-l baseline word-register | pass | `LZ0` returned `0000` |
| ZR | ZR | iq-l baseline dword-register | pass | `ZR0` returned `0000` |
| RD | RD | iq-l baseline dword-register | pass | `RD0` returned `0000` |
| SM | SM | iq-l baseline fixed 4096 | pass | `SM0` returned `0000` |
| SD | SD | iq-l baseline fixed 4096 | pass | `SD0` returned `0000` |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | Existing `melsec:iq-l` built-in profile expectations match this L16HCPU target: type-name, direct, random, block, monitor, configured `U\G`, configured `U3E0\G`, intended long timer/counter, and `LZ` routes passed over 4E/iQ-R; `J` returned `4031` in this configuration and is not positive route evidence | None |
| Limits | Plain and extended limits match the iQ-L shape: random read/register 96/97 `C054`, random word write 80/81 `C054`, weighted dword 68/69 `C054`, random bit write 94/95 `C053`, direct word 960/961 `C051`, and direct bit 7168/7169 `C052`; both `U1\G100` and `U3E0\G0` match the same ext word limits | None |
| Write policy | Raw `S` write returned `4030`; keep `S` read-only/write-prohibited | None |
| Device families | All observed iQ-L families are reachable for this L16HCPU built-in target; treat `LTN0`/`LSTN0` word4 routes as intended long routes and keep raw `LTS`/`LTC`/`LSTS`/`LSTC` `4030` results as raw-probe evidence only | None |
