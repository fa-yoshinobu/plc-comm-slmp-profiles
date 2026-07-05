# QCPU QJ71E71-100 Downstream 5-Implementation Read

Date: 2026-07-05

This is a read-only downstream implementation acceptance check for the new
Ethernet-unit profile `melsec:qcpu:qj71e71-100`.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: QCPU + QJ71E71-100 / `melsec:qcpu:qj71e71-100`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: downstream read acceptance for the new QJ71E71-100 unit profile

No writes were part of this batch.

## Results

| Implementation | Command/API | Status | Result note |
|----------------|-------------|--------|-------------|
| .NET | `dotnet run --project samples/PlcComm.Slmp.Cli -- read-soak ... --plc-profile melsec:qcpu:qj71e71-100 --device D1000 --points 1 --iterations 1 --quiet` | pass | 1 iteration, 0 failures, latency 91 ms |
| Python | `python samples\02_device_reads.py ... --plc-profile melsec:qcpu:qj71e71-100 --word-device D1000 --word-points 1 --bit-points 0` | pass | `D1000 words: [0]` |
| Rust | `cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile melsec:qcpu:qj71e71-100` | pass | `{"status":"success","values":[0]}` |
| Node-RED | `SlmpClient.readDevices("D1000", 1, {bitUnit:false})` with `plcProfile:"melsec:qcpu:qj71e71-100"` | pass | `{"status":"success","values":[0],"plcProfile":"melsec:qcpu:qj71e71-100","frameType":"4e","plcSeries":"ql"}` |
| C++ minimal | `slmp_live_read_once 192.168.250.100 1025 melsec:qcpu:qj71e71-100 D1000` | pass | `{"status":"success","profile":"melsec:qcpu:qj71e71-100","frame":"4E","compat":"Q/L","device":"D1000","values":[0]}` |

Result record:
`evidence/unit-investigations/downstream-runs/qcpu_qj71e71-100_20260705.json`.

## Acceptance Impact

This completes the QCPU + QJ71E71-100 live implementation pattern. The profile
used 4E frame behavior with Q/L compatibility through QJ71E71-100, and all five
downstream implementations completed a read-only `D1000` read.

The remaining per-profile live implementation pattern is
`melsec:qnu:qj71e71-100`.
