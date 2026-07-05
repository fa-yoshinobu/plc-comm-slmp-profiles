# iQ-R Built-in Downstream Connectivity Smoke

Date: 2026-07-05

This is a read-only connectivity smoke for the currently connected iQ-R
built-in Ethernet port. It is not a QJ71E71-100 Ethernet-unit acceptance
record and does not satisfy the downstream unit-profile read requirement.

## Approved Live Check

User-confirmed target:

- Target PLC/profile: iQ-R built-in Ethernet / `melsec:iq-r`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: connection/read smoke only; not QJ71E71-100 unit-profile acceptance

Command:

```powershell
python samples\02_device_reads.py --host 192.168.250.100 --port 1025 --transport tcp --plc-profile melsec:iq-r --word-device D1000 --word-points 1 --bit-points 0
```

Result:

```text
D1000 words: [0]
```

Status: pass.

## Acceptance Impact

The GOAL-3 downstream acceptance item remains pending because the connected
PLC was iQ-R built-in Ethernet, not QJ71E71-100 or LJ71E71-100.
