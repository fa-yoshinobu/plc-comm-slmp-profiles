# R120PCPU Built-in Ethernet SLMP Live Verification

Use this record to decide whether the canonical JSON is correct for this connected PLC/profile.
This is a decision record, not a communication log.

Untested items are never failure results. Status values are `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- On this iQ-R profile, `S` is read-only.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check.

## Session

| Item | Value |
|------|-------|
| Date | 2026-07-05 |
| PLC model | R120PCPU built-in Ethernet |
| PLC profile | `melsec:iq-r` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes | Built-in Ethernet profile verification. Plan run `evidence/unit-investigations/plans/runs/iq-r_r120pcpu_builtin_20260705_023411/results.json` recorded 37/37 items, waived 0, errors 0. JSON was not changed. |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name | supported / live | `0101/0000` | pass | 4E returned `0000`, text `R120PCPU`, raw type-code bytes `4448` |
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
| `J...\...` link direct | `ext_link_direct` | `J1\X10`, `J1\Y10`, `J1\B10`, `J1\W10`, `J1\SB40`, `J1\SW33` | config | Configured targets returned `0000`; availability is configuration-dependent by design |
| `U...\G...` module buffer | `ext_module_access` | `U5\G0` | config | Configured target returned `0000`; unit number and buffer address are configuration-dependent by design |
| `U3E0\G...` CPU/module buffer | routed module access | `U3E0\G0` | config | Configured target returned `0000`; use routed form only |
| `U3E0\HG...` CPU buffer | `hg_cpu_buffer` | `U3E0\HG0` | pass | iQ-R CPU buffer route returned `0000` |
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
| Extended random word read (`U5\G`) | ext max 96, over `C054` | limit | `U5\G0` passed at 96 and returned `C054` at 97 |
| Extended random word read (`J1\W`) | ext max 96, over `C054` | limit | `J1\W10` passed at 96 and returned `C054` at 97 |
| Extended random word read (`U3E0\G`) | ext max 96, over `C054` | limit | `U3E0\G0` passed at 96 and returned `C054` at 97 |
| Extended random word read (`U3E0\HG`) | ext max 96, over `C054` | limit | `U3E0\HG0` passed at 96 and returned `C054` at 97 |
| Extended random word write count (`U5\G`) | ext max 80, over `C054` | limit | `U5\G0` passed at 80 and returned `C054` at 81 |
| Extended random word write count (`J1\W`) | ext max 80, over `C054` | limit | `J1\W10` passed at 80 and returned `C054` at 81 |
| Extended random word write count (`U3E0\G`) | ext max 80, over `C054` | limit | `U3E0\G0` passed at 80 and returned `C054` at 81 |
| Extended random word write count (`U3E0\HG`) | ext max 80, over `C054` | limit | `U3E0\HG0` passed at 80 and returned `C054` at 81 |
| Extended random word write weighted (`U5\G`) | ext weighted max 960, over `C054` | limit | `U5\G0` dword test passed at 68 and returned `C054` at 69 |
| Extended random word write weighted (`J1\W`) | ext weighted max 960, over `C054` | limit | `J1\W10` dword test passed at 68 and returned `C054` at 69 |
| Extended random word write weighted (`U3E0\G`) | ext weighted max 960, over `C054` | limit | `U3E0\G0` dword test passed at 68 and returned `C054` at 69 |
| Extended random word write weighted (`U3E0\HG`) | ext weighted max 960, over `C054` | limit | `U3E0\HG0` dword test passed at 68 and returned `C054` at 69 |
| Extended random bit write (`J1\B`) | ext max 94, over `C053` | limit | `J1\B10` passed at 94, reset OFF, and returned `C053` at 95 |
| Extended monitor word register (`U5\G`) | ext max 96, over `C054` | limit | `U5\G0` register passed at 96 and returned `C054` at 97 |
| Extended monitor word register (`J1\W`) | ext max 96, over `C054` | limit | `J1\W10` register passed at 96 and returned `C054` at 97 |
| Extended monitor word register (`U3E0\G`) | ext max 96, over `C054` | limit | `U3E0\G0` register passed at 96 and returned `C054` at 97 |
| Extended monitor word register (`U3E0\HG`) | ext max 96, over `C054` | limit | `U3E0\HG0` register passed at 96 and returned `C054` at 97 |

## Write Policy Checklist

For this iQ-R profile, the canonical policy is expected to be `S=read-only` unless the JSON changes.
Do not keep noise such as "not written to a nonexistent address". If a write result is needed, use an address that exists for the connected PLC.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` | read-only | policy | Raw SLMP write to `S2` returned `4030`; keep `S` write-prohibited for this target |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X | iq-r baseline dword-register | pass | `X0` returned `0000` |
| Y | Y | iq-r baseline dword-register | pass | `Y0` returned `0000` |
| M | M | iq-r baseline dword-register | pass | `M0` returned `0000` |
| B | B | iq-r baseline dword-register | pass | `B0` returned `0000` |
| SB | SB | iq-r baseline dword-register | pass | `SB0` returned `0000` |
| F | F | iq-r baseline dword-register | pass | `F0` returned `0000` |
| V | V | iq-r baseline dword-register | pass | `V0` returned `0000` |
| L | L | iq-r baseline dword-register | pass | `L0` returned `0000` |
| S | S | iq-r baseline dword-register | pass | `S0` returned `0000`; write policy is separate |
| D | D | iq-r baseline dword-register | pass | `D0` returned `0000` |
| W | W | iq-r baseline dword-register | pass | `W0` returned `0000` |
| SW | SW | iq-r baseline dword-register | pass | `SW0` returned `0000` |
| R | R | iq-r baseline dword-register-clipped | pass | `R0` returned `0000` |
| T | TS / TC / TN | iq-r baseline dword-register | pass | `TS0`, `TC0`, and `TN0` returned `0000` |
| ST | STS / STC / STN | iq-r baseline dword-register | pass | `STS0`, `STC0`, and `STN0` returned `0000` |
| C | CS / CC / CN | iq-r baseline dword-register | pass | `CS0`, `CC0`, and `CN0` returned `0000` |
| LT | LTS / LTC / LTN | iq-r baseline dword-register | pass | Intended `LTN0` word4 route returned `0000`; raw-device-code probes `LTS0` and `LTC0` returned `4030` |
| LST | LSTS / LSTC / LSTN | iq-r baseline dword-register | pass | Intended `LSTN0` word4 route returned `0000`; raw-device-code probes `LSTS0` and `LSTC0` returned `4030` |
| LC | LCS / LCC / LCN | iq-r baseline dword-register | pass | `LCS0`, `LCC0`, and intended `LCN0` dword random route returned `0000` |
| Z | Z | iq-r baseline word-register | pass | `Z0` returned `0000` |
| LZ | LZ | iq-r baseline word-register | pass | `LZ0` returned `0000` |
| ZR | ZR | iq-r baseline dword-register | pass | `ZR0` returned `0000` |
| RD | RD | iq-r baseline dword-register | pass | `RD0` returned `0000` |
| SM | SM | iq-r baseline fixed 4096 | pass | `SM0` returned `0000` |
| SD | SD | iq-r baseline fixed 4096 | pass | `SD0` returned `0000` |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features | Existing `melsec:iq-r` built-in profile expectations match this R120PCPU target: type-name, direct, random, block, monitor, configured `J`, configured `U\G`, `U3E0\G`, iQ-R `U3E0\HG`, intended long timer/counter, and `LZ` routes passed over 4E/iQ-R | None |
| Limits | Plain and extended limits match the iQ-R shape: random read/register 96/97 `C054`, random word write 80/81 `C054`, weighted dword 68/69 `C054`, random bit write 94/95 `C053`, direct word 960/961 `C051`, and direct bit 7168/7169 `C052` | None |
| Write policy | Raw `S` write returned `4030`; keep `S` read-only/write-prohibited | None |
| Device families | All observed iQ-R families are reachable for this R120PCPU built-in target; treat `LTN0`/`LSTN0` word4 routes as intended long routes and keep raw `LTS`/`LTC`/`LSTS`/`LSTC` `4030` results as raw-probe evidence only | None |
