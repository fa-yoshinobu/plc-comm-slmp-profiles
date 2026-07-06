# RJ71EN71 iQ-R Extended Random Live Probe

Date: 2026-07-06

This records the approved live PLC evidence for 008x extended random routes on
an iQ-R PLC reached through RJ71EN71. It is profile evidence collected with the
canonical raw probe, not a production-operation recommendation.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: R120PCPU + RJ71EN71 / `melsec:iq-r:rj71en71`
- Endpoint: `192.168.250.100:1025` TCP
- Read targets: `U3E0\G0`, 1 word; `U3E0\HG0`, 1 word
- Write targets: `U3E0\G0`, 1 word value `55065`; `U3E0\HG0`, 1 word value `2028`; `M1000`, 1 bit value `1` followed by OFF reset
- Intent: extended random read/write evidence collection
- Purpose: confirm RJ71EN71 alias profile acceptance for 008x extended random word and bit routes used by the cross-implementation API parity work

## Results

All probes used `tools/live_profile_probe.py` with the canonical profile JSON.

| Operation | Target | Value | Status | Result note |
| --- | --- | --- | --- | --- |
| `read-random-ext` | `U3E0\G0`, 1 word | - | pass | end code `0000`, data bytes `2` |
| `read-random-ext` | `U3E0\HG0`, 1 word | - | pass | end code `0000`, data bytes `2` |
| `write-random-words-ext` | `U3E0\G0`, 1 word | `55065` | pass | end code `0000` |
| `write-random-words-ext` | `U3E0\HG0`, 1 word | `2028` | pass | end code `0000` |
| `write-random-bits-ext` | `M1000`, 1 bit | `1`, then reset OFF | pass | write end code `0000`; reset end code `0000` |

## Acceptance Impact

The RJ71EN71 alias profile accepted the canonical 0082/0083 extended random
read/write paths for configured `U3E0\G`, iQ-R CPU-buffer `U3E0\HG`, and normal
bit `M` routes. These PLC results align with the Rust and Node-RED payload
parity tests for the newly added extended random APIs.
