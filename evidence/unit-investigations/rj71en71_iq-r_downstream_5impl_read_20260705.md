# RJ71EN71 iQ-R Downstream 5-Implementation Read

Date: 2026-07-05

This is a read-only downstream implementation acceptance check for the new
Ethernet-unit alias profile `melsec:iq-r:rj71en71`.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: R120PCPU + RJ71EN71 / `melsec:iq-r:rj71en71`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: downstream read acceptance for the RJ71EN71 alias profile

No writes were part of this batch.

## Results

| Implementation | Command/API | Status | Result note |
|----------------|-------------|--------|-------------|
| .NET | `dotnet run --project samples/PlcComm.Slmp.Cli -- read-soak ... --plc-profile melsec:iq-r:rj71en71 --device D1000 --points 1 --iterations 1 --quiet` | pass | 1 iteration, 0 failures, latency 21 ms |
| Python | `python samples\02_device_reads.py ... --plc-profile melsec:iq-r:rj71en71 --word-device D1000 --word-points 1 --bit-points 0` | pass | `D1000 words: [0]` |
| Rust | `cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile melsec:iq-r:rj71en71` | pass | `{"status":"success","values":[0]}` |
| Node-RED | `SlmpClient.readDevices("D1000", 1, {bitUnit:false})` with `plcProfile:"melsec:iq-r:rj71en71"` | pass | `{"status":"success","values":[0],"plcProfile":"melsec:iq-r:rj71en71","frameType":"4e","plcSeries":"iqr"}` |
| C++ minimal | `slmp_live_read_once 192.168.250.100 1025 melsec:iq-r:rj71en71 D1000` | pass | `{"status":"success","profile":"melsec:iq-r:rj71en71","frame":"4E","compat":"iQ-R","device":"D1000","values":[0]}` |

Result record:
`evidence/unit-investigations/downstream-runs/rj71en71_iq-r_20260705.json`.

## Acceptance Impact

This completes the RJ71EN71 live implementation pattern. The alias profile used
4E frame behavior with iQ-R compatibility through RJ71EN71, and all five
downstream implementations completed a read-only `D1000` read.

All per-profile live implementation patterns for this goal are now complete.
