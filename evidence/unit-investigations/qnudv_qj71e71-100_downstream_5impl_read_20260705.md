# QnUDV QJ71E71-100 Downstream 5-Implementation Read

Date: 2026-07-05

This is a read-only downstream implementation acceptance check for the new
Ethernet-unit profile `melsec:qnudv:qj71e71-100`.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: QnUDV + QJ71E71-100 / `melsec:qnudv:qj71e71-100`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: downstream read acceptance for the new QJ71E71-100 unit profile

No writes were part of this batch.

## Results

| Implementation | Command/API | Status | Result note |
|----------------|-------------|--------|-------------|
| .NET | `dotnet run --project samples/PlcComm.Slmp.Cli -- read-soak ... --plc-profile melsec:qnudv:qj71e71-100 --device D1000 --points 1 --iterations 1` | pass | Retry succeeded: 1 iteration, 0 failures, latency 20 ms |
| Python | `python samples\02_device_reads.py ... --plc-profile melsec:qnudv:qj71e71-100 --word-device D1000 --word-points 1 --bit-points 0` | pass | Retry succeeded: `D1000 words: [17476]` |
| Rust | `cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile melsec:qnudv:qj71e71-100` | pass | Retry succeeded: `{"status":"success","values":[17476]}` |
| Node-RED | `SlmpClient.readDevices("D1000", 1, {bitUnit:false})` with `plcProfile:"melsec:qnudv:qj71e71-100"` | pass | `{"status":"success","values":[17476],"plcProfile":"melsec:qnudv:qj71e71-100","frameType":"4e","plcSeries":"ql"}` |
| C++ minimal | `slmp_live_read_once 192.168.250.100 1025 melsec:qnudv:qj71e71-100 D1000` | pass | `{"status":"success","profile":"melsec:qnudv:qj71e71-100","frame":"4E","compat":"Q/L","device":"D1000","values":[17476]}` |

Initial batch record:
`evidence/unit-investigations/downstream-runs/qnudv_qj71e71-100_20260705.json`.
It preserves transient .NET/Python connection timeouts and a Rust stdout
`status:error` result despite process exit code 0.

Successful retry consolidation:
`evidence/unit-investigations/downstream-runs/qnudv_qj71e71-100_20260705_retry_success.json`.

## Acceptance Impact

This satisfies the Q-series E71 downstream 4E evidence item for a new profile:
the profile used 4E frame behavior with Q/L compatibility through
QJ71E71-100, and all five downstream implementations completed a read-only
`D1000` read.

It completes the QnUDV + QJ71E71-100 live implementation pattern. The remaining
per-profile live implementation patterns are `melsec:qcpu:qj71e71-100`,
`melsec:qnu:qj71e71-100`, and `melsec:lcpu:lj71e71-100`.
