# <PLC/Profile> SLMP Live Verification Checklist

Use this template to decide whether the canonical JSON is correct for one connected PLC/profile.
This is a decision checklist, not a communication log. Do not record raw frames, per-send history, or old attempts unless they explain the current decision.

Untested items are never failure results. Every row must end as `pass`, `fail`, `config`, `address`, `family`, `route`, `limit`, `policy`, `spec`, or `unverified`.

Common rules:

- `G` and `HG` are not standalone device routes. Use routed forms only.
- `S` write behavior is profile-specific. Verify it per PLC/profile; do not assume read-only.
- Device writes are allowed for verification unless explicitly disabled.
- Numeric write probes use random test values. Do not require restoring the old numeric value.
- Bit write probes must reset the tested bits to OFF after the write check.

## Session

| Item | Value |
|------|-------|
| Date | YYYY-MM-DD |
| PLC model |  |
| PLC profile | `melsec:...` |
| Endpoint | `192.168.250.100:1025` TCP |
| Source JSON | `capability/slmp_builtin_ethernet_profiles.json` |
| Device range JSON | `device-ranges/slmp_device_range_rules.json` |
| Notes |  |

## Feature Checklist

Use the profile JSON settings as-is. Do not duplicate frame, compatibility, or subcommand details here.

| Feature | JSON expectation | Target used | Status | Decision note |
|---------|------------------|-------------|--------|---------------|
| Type name |  | - |  |  |
| Direct read/write |  |  |  |  |
| Random read/write |  |  |  |  |
| Block read/write |  |  |  |  |
| Monitor |  |  |  |  |
| Long timer/counter route | dedicated long route |  |  |  |
| LZ 32-bit route | dword route, not 16-bit direct |  |  |  |

## Qualified Access Checklist

Use this table for access routes and qualifiers, not ordinary device-family existence.

| Route | JSON feature / rule | Target used | Status | Decision note |
|-------|---------------------|-------------|--------|---------------|
| `J...\...` link direct | `ext_link_direct` |  |  | Configuration-dependent when link hardware is absent |
| `U...\G...` module buffer | `ext_module_access` |  |  | Unit/address availability is configuration-dependent |
| `U3E0\HG...` CPU buffer | `hg_cpu_buffer` |  |  | iQ-R-only route |
| Standalone `G` | common rule | - | spec | Not a standalone device route |
| Standalone `HG` | common rule | - | spec | Not a standalone device route |

## Limit Checklist

Only run these when limit testing is intended. A point-limit failure is `limit`, not a feature failure.
For random word write, verify the count limit and the weighted limit separately when `weighted max` is defined.
The weighted-limit probe must keep the total point count within `max` and exceed only `weighted max`; do not treat `81 word` or `161 word` count-over probes as weighted-limit evidence.
Typical weighted-only probes are `40 word + 40 dword` for `max 80 / weighted max 960`, and `138 dword` for `max 160 / weighted max 1920`.
For extended random routes, verify the ext-specific limit rows separately from the plain random rows.

| Limit item | JSON value | Status | Decision note |
|------------|------------|--------|---------------|
| Direct word read |  |  |  |
| Direct word write |  |  |  |
| Direct bit read |  |  |  |
| Direct bit write |  |  |  |
| Random word read |  |  |  |
| Random word write count | max, over end code |  | Record pass at max and fail at max+1 |
| Random word write weighted | weighted max, over end code |  | Required when weighted max exists; total point count must remain within max |
| Random bit write |  |  |  |
| Monitor word register |  |  |  |
| Extended random word read | ext max, over end code |  | Record pass at ext max and fail at ext max+1 |
| Extended random word write count | ext max, over end code |  | Record pass at ext max and fail at ext max+1 |
| Extended random word write weighted | ext weighted max, over end code |  | Required when ext weighted max exists; total point count must remain within ext max |
| Extended random bit write | ext max, over end code |  | Bit probes must reset tested bits OFF |
| Extended monitor word register | ext max, over end code or not adopted |  | Record whether the ext monitor path is adopted as a limit source |

## Write Policy Checklist

`S` write behavior is profile-specific. Verify it per PLC/profile.
Do not keep noise such as "not written to a nonexistent address". If a write result is needed, use an address that exists for the connected PLC.

| Device family | JSON policy | Status | Decision note |
|---------------|-------------|--------|---------------|
| `S` |  |  |  |

## Device Family Access Checklist

Use the device-range JSON. This table is for whether each device family exists and is reachable on the PLC, not for command feature support.

| Family | Devices | JSON rule | Status | Decision note |
|--------|---------|-----------|--------|---------------|
| X | X |  |  |  |
| Y | Y |  |  |  |
| M | M |  |  |  |
| B | B |  |  |  |
| SB | SB |  |  |  |
| F | F |  |  |  |
| V | V |  |  |  |
| L | L |  |  |  |
| S | S |  |  | Existence/access only; write policy is separate |
| D | D |  |  |  |
| W | W |  |  |  |
| SW | SW |  |  |  |
| R | R |  |  |  |
| T | TS / TC / TN |  |  |  |
| ST | STS / STC / STN |  |  |  |
| C | CS / CC / CN |  |  |  |
| LT | LTS / LTC / LTN |  |  |  |
| LST | LSTS / LSTC / LSTN |  |  |  |
| LC | LCS / LCC / LCN |  |  |  |
| Z | Z |  |  |  |
| LZ | LZ |  |  | 32-bit route only |
| ZR | ZR |  |  |  |
| RD | RD |  |  |  |
| SM | SM |  |  |  |
| SD | SD |  |  |  |

## Final Decision

| Area | Decision | Remaining unverified items |
|------|----------|----------------------------|
| Features |  |  |
| Limits |  |  |
| Write policy |  |  |
| Device families |  |  |
