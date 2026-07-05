# LCPU Built-in Downstream 5-Implementation Smoke

Date: 2026-07-05

This is a read-only downstream implementation smoke for the currently
connected LCPU built-in Ethernet port. It is not LJ71E71-100 Ethernet-unit
acceptance evidence.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: LCPU built-in Ethernet / `melsec:lcpu`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: complete all downstream checks possible without switching PLC

No writes were part of this batch.

## Results

| Implementation | Command/API | Status | Result note |
|----------------|-------------|--------|-------------|
| .NET | `dotnet run --project samples/PlcComm.Slmp.Cli -- read-soak ... --plc-profile melsec:lcpu --device D1000 --points 1 --iterations 1` | pass | 1 iteration, 0 failures, latency 15 ms |
| Python | `python samples\02_device_reads.py ... --plc-profile melsec:lcpu --word-device D1000 --word-points 1 --bit-points 0` | pass | `D1000 words: [0]` |
| Rust | `cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile melsec:lcpu` | pass | `{"status":"success","values":[0]}` |
| Node-RED | `SlmpClient.readDevices("D1000", 1, {bitUnit:false})` with `plcProfile:"melsec:lcpu"` | pass | `{"status":"success","values":[0],"plcProfile":"melsec:lcpu","frameType":"3e","plcSeries":"ql"}` |
| C++ minimal | `slmp_live_read_once 192.168.250.100 1025 melsec:lcpu D1000` | pass | `{"status":"success","profile":"melsec:lcpu","frame":"3E","compat":"Q/L","device":"D1000","values":[0]}` |

.NET note: the first `read-soak` attempt returned `[NG] The operation was
canceled.` A second attempt with the same endpoint/profile/read target
succeeded and produced the result above. The failed attempt is not treated as
PLC evidence for unsupported behavior because the same read passed immediately
afterward.

Rust note: the CLI binary requires `--features cli`.

## Acceptance Impact

This confirms that all five downstream implementations can read from the
currently connected LCPU built-in Ethernet PLC using `melsec:lcpu`.

The GOAL-3 Ethernet-unit acceptance item remains pending because the connected
PLC was not LJ71E71-100.
