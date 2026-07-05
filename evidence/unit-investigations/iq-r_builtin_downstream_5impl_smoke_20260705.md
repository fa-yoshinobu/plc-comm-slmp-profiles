# iQ-R Built-in Downstream 5-Implementation Smoke

Date: 2026-07-05

This is a read-only downstream implementation smoke for the currently
connected iQ-R built-in Ethernet port. It is not QJ71E71-100/LJ71E71-100
Ethernet-unit acceptance evidence.

## Approved Live Batch

User-confirmed target:

- Target PLC/profile: iQ-R built-in Ethernet / `melsec:iq-r`
- Endpoint: `192.168.250.100:1025` TCP
- Read target: `D1000`, 1 word
- Intent: read-only
- Purpose: complete all downstream checks possible without switching PLC

No writes were part of this batch.

## Results

| Implementation | Command/API | Status | Result note |
|----------------|-------------|--------|-------------|
| .NET | `dotnet run --project samples/PlcComm.Slmp.Cli -- read-soak ... --plc-profile melsec:iq-r --device D1000 --points 1 --iterations 1 --quiet` | pass | 1 iteration, 0 failures, latency 17 ms |
| Python | `python samples\02_device_reads.py ... --plc-profile melsec:iq-r --word-device D1000 --word-points 1 --bit-points 0` | pass | `D1000 words: [0]` |
| Rust | `cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile melsec:iq-r` | pass | `{"status":"success","values":[0]}` |
| Node-RED | `SlmpClient.readDevices("D1000", 1, {bitUnit:false})` with `plcProfile:"melsec:iq-r"` | pass | `{"status":"success","values":[0],"plcProfile":"melsec:iq-r","frameType":"4e","plcSeries":"iqr"}` |
| C++ minimal | `slmp_live_read_once 192.168.250.100 1025 melsec:iq-r D1000` | pass | `{"status":"success","profile":"melsec:iq-r","frame":"4E","compat":"iQ-R","device":"D1000","values":[0]}` |

Rust note: the first attempt without `--features cli` failed before transport
because the binary is gated behind the `cli` feature. The command above is the
live read attempt and passed.

## Acceptance Impact

This confirms that all five downstream implementations can read from the
currently connected iQ-R built-in Ethernet PLC using `melsec:iq-r`.

The GOAL-3 Ethernet-unit acceptance item remains pending because the connected
PLC was not QJ71E71-100 or LJ71E71-100.
