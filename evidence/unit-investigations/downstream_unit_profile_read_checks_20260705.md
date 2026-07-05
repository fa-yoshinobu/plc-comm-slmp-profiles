# Downstream Unit Profile Read Checks

This record is for the GOAL-3 acceptance item: each downstream implementation must perform one read-only live read through a new Ethernet-unit profile.

This is not a profile-definition record and not a communication log. Keep it to the implementation, target profile, endpoint, read intent, command/API used, and pass/fail result.

## Live Safety Gate

Do not run any command from this page until the user has confirmed the currently connected PLC and replied `OK` for the specific batch.

Before each batch, state:

- target PLC/profile
- endpoint
- target device/address
- read-only intent
- test purpose

No writes are part of this downstream check.

## Candidate Targets

Use whichever PLC is physically connected and approved for the batch.

| Target PLC / unit | Canonical profile | Endpoint | Read target | Purpose |
|-------------------|-------------------|----------|-------------|---------|
| R120PCPU + RJ71EN71 | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | Verify RJ71EN71 alias profile uses 4E + iQ-R |
| Q12HCPU + QJ71E71-100 | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | Verify QCPU base-only successor profile through QJ71E71-100 |
| Q26UDEHCPU + QJ71E71-100 | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | Verify QnU unit profile uses 4E + Q/L |
| Q06UDVCPU + QJ71E71-100 | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | Verify QnUDV unit profile uses 4E + Q/L |
| L02SCPU + LJ71E71-100 | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | Verify LCPU unit profile uses 4E + Q/L |

## Implementation Checklist

Fill one row per implementation after the approved live read.

| Implementation | Repo | Profile used | Endpoint | Read target | Status | Result note |
|----------------|------|--------------|----------|-------------|--------|-------------|
| .NET | `plc-comm-slmp-dotnet` | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | Retry succeeded: 1 iteration, 0 failures, latency 20 ms |
| Python | `plc-comm-slmp-python` | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | Retry succeeded: `D1000 words: [17476]` |
| Rust | `plc-comm-slmp-rust` | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | Retry succeeded: `{"status":"success","values":[17476]}` |
| Node-RED | `node-red-contrib-plc-comm-slmp` | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frameType=4e`, `plcSeries=ql`, `values=[17476]` |
| C++ minimal | `plc-comm-slmp-cpp-minimal` | `melsec:qnudv:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frame=4E`, `compat=Q/L`, `values=[17476]` |

## Command Templates

Replace `<profile>` only with the approved connected target's canonical profile.
Do not use `melsec:qcpu`; it is base-only.

First print the complete command plan. This is dry-run only and does not talk to the PLC:

```powershell
python tools\run_downstream_read_checks.py --profile <profile> --host 192.168.250.100 --port 1025 --device D1000
```

After the user has confirmed the connected PLC and replied `OK` for the exact batch, run the same plan with the explicit live gate:

```powershell
python tools\run_downstream_read_checks.py --profile <profile> --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\<run-id>.json
```

Use a filesystem-safe `<run-id>`, for example `qcpu_qj71e71-100_20260705`.
The JSON record captures each implementation command, working directory,
exit code, stdout, and stderr. Use that record to fill the implementation
checklist above.

After a live run, validate the saved record set:

```powershell
python tools\audit_downstream_read_records.py --records-dir evidence\unit-investigations\downstream-runs --require-complete
```

The audit is complete only when all five implementation reads pass, at least
one passing record uses a QJ71E71-100 profile, and one passing record uses
`melsec:iq-r:rj71en71`.

The sections below show the individual commands emitted by the planner.

### .NET

Read intent: `D1000`, 1 word, read-only.

```powershell
dotnet run --project samples\PlcComm.Slmp.Cli -- read-soak --host 192.168.250.100 --port 1025 --transport tcp --plc-profile <profile> --device D1000 --points 1 --iterations 1 --quiet
```

### Python

Read intent: `D1000`, 1 word, read-only.

```powershell
python samples\02_device_reads.py --host 192.168.250.100 --port 1025 --transport tcp --plc-profile <profile> --word-device D1000 --word-points 1 --bit-points 0
```

### Rust

Read intent: `D1000`, 1 word, read-only.

```powershell
cargo run --features cli --bin slmp_verify_client -- 192.168.250.100 1025 read D1000 1 --plc-profile <profile>
```

### Node-RED

Read intent: `D1000`, 1 word, read-only.

```powershell
node -e "const {SlmpClient}=require('./lib/slmp'); (async()=>{const c=new SlmpClient({host:'192.168.250.100',port:1025,transport:'tcp',plcProfile:'<profile>'}); await c.connect(); try { const v=await c.readDevices('D1000',1,{bitUnit:false}); console.log(JSON.stringify({status:'success',values:v,plcProfile:c.plcProfile,frameType:c.frameType,plcSeries:c.plcSeries})); } finally { await c.close(); }})().catch(e=>{console.error(e); process.exit(1);});"
```

### C++ Minimal

Read intent: `D1000`, 1 word, read-only.

Build the host live-read smoke tool, then run it with the approved profile.

```powershell
g++ -std=c++17 -Wall -Wextra -Isrc tests\slmp_live_read_once.cpp src\slmp_minimal.cpp src\slmp_error_codes.cpp src\slmp_high_level.cpp -o "$env:TEMP\slmp_live_read_once.exe" -lws2_32
& "$env:TEMP\slmp_live_read_once.exe" 192.168.250.100 1025 <profile> D1000
```

`run_ci.bat` builds this tool and checks its usage output with no arguments, but does not run a live read. CI never talks to a live PLC.

## R120PCPU + RJ71EN71 Live Result

Approved read-only batch:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:iq-r:rj71en71 --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\rj71en71_iq-r_20260705.json
```

All five downstream implementation reads passed in the first batch.

| Implementation | Repo | Profile used | Endpoint | Read target | Status | Result note |
|----------------|------|--------------|----------|-------------|--------|-------------|
| .NET | `plc-comm-slmp-dotnet` | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | 1 iteration, 0 failures, latency 21 ms |
| Python | `plc-comm-slmp-python` | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `D1000 words: [0]` |
| Rust | `plc-comm-slmp-rust` | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `{"status":"success","values":[0]}` |
| Node-RED | `node-red-contrib-plc-comm-slmp` | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frameType=4e`, `plcSeries=iqr`, `values=[0]` |
| C++ minimal | `plc-comm-slmp-cpp-minimal` | `melsec:iq-r:rj71en71` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frame=4E`, `compat=iQ-R`, `values=[0]` |

Evidence:

- `rj71en71_iq-r_downstream_5impl_read_20260705.md`
- `downstream-runs/rj71en71_iq-r_20260705.json`

## QnUDV + QJ71E71-100 Live Result

Approved read-only batch:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:qnudv:qj71e71-100 --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\qnudv_qj71e71-100_20260705.json
```

The first batch preserved transient .NET/Python connection timeouts and a Rust
stdout `status:error` result despite process exit code 0. The retry results for
.NET, Python, and Rust all passed, and Node-RED/C++ minimal had already passed
in the approved batch.

Evidence:

- `qnudv_qj71e71-100_downstream_5impl_read_20260705.md`
- `downstream-runs/qnudv_qj71e71-100_20260705.json`
- `downstream-runs/qnudv_qj71e71-100_20260705_retry_success.json`

## LCPU + LJ71E71-100 Live Result

Approved read-only batch:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:lcpu:lj71e71-100 --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\lcpu_lj71e71-100_20260705.json
```

All five downstream implementation reads passed in the first batch.

| Implementation | Repo | Profile used | Endpoint | Read target | Status | Result note |
|----------------|------|--------------|----------|-------------|--------|-------------|
| .NET | `plc-comm-slmp-dotnet` | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | 1 iteration, 0 failures, latency 57 ms |
| Python | `plc-comm-slmp-python` | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `D1000 words: [0]` |
| Rust | `plc-comm-slmp-rust` | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `{"status":"success","values":[0]}` |
| Node-RED | `node-red-contrib-plc-comm-slmp` | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frameType=4e`, `plcSeries=ql`, `values=[0]` |
| C++ minimal | `plc-comm-slmp-cpp-minimal` | `melsec:lcpu:lj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frame=4E`, `compat=Q/L`, `values=[0]` |

Evidence:

- `lcpu_lj71e71-100_downstream_5impl_read_20260705.md`
- `downstream-runs/lcpu_lj71e71-100_20260705.json`

## QCPU + QJ71E71-100 Live Result

Approved read-only batch:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\qcpu_qj71e71-100_20260705.json
```

All five downstream implementation reads passed in the first batch.

| Implementation | Repo | Profile used | Endpoint | Read target | Status | Result note |
|----------------|------|--------------|----------|-------------|--------|-------------|
| .NET | `plc-comm-slmp-dotnet` | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | 1 iteration, 0 failures, latency 91 ms |
| Python | `plc-comm-slmp-python` | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `D1000 words: [0]` |
| Rust | `plc-comm-slmp-rust` | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `{"status":"success","values":[0]}` |
| Node-RED | `node-red-contrib-plc-comm-slmp` | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frameType=4e`, `plcSeries=ql`, `values=[0]` |
| C++ minimal | `plc-comm-slmp-cpp-minimal` | `melsec:qcpu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frame=4E`, `compat=Q/L`, `values=[0]` |

Evidence:

- `qcpu_qj71e71-100_downstream_5impl_read_20260705.md`
- `downstream-runs/qcpu_qj71e71-100_20260705.json`

## QnU + QJ71E71-100 Live Result

Approved read-only batch:

```powershell
python tools\run_downstream_read_checks.py --profile melsec:qnu:qj71e71-100 --host 192.168.250.100 --port 1025 --device D1000 --execute --approved-live-ok --record-json evidence\unit-investigations\downstream-runs\qnu_qj71e71-100_20260705.json
```

All five downstream implementation reads passed in the first batch.

| Implementation | Repo | Profile used | Endpoint | Read target | Status | Result note |
|----------------|------|--------------|----------|-------------|--------|-------------|
| .NET | `plc-comm-slmp-dotnet` | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | 1 iteration, 0 failures, latency 38 ms |
| Python | `plc-comm-slmp-python` | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `D1000 words: [0]` |
| Rust | `plc-comm-slmp-rust` | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `{"status":"success","values":[0]}` |
| Node-RED | `node-red-contrib-plc-comm-slmp` | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frameType=4e`, `plcSeries=ql`, `values=[0]` |
| C++ minimal | `plc-comm-slmp-cpp-minimal` | `melsec:qnu:qj71e71-100` | `192.168.250.100:1025` TCP | `D1000`, 1 word | pass | `frame=4E`, `compat=Q/L`, `values=[0]` |

Evidence:

- `qnu_qj71e71-100_downstream_5impl_read_20260705.md`
- `downstream-runs/qnu_qj71e71-100_20260705.json`

## Planner Verification

2026-07-05 non-live checks:

- `python tools\run_downstream_read_checks.py --profile melsec:iq-r:rj71en71 --host 192.168.250.100 --port 1025 --device D1000` printed the .NET, Python, Rust, Node-RED, and C++ build/read command plan and ended with `dry-run only; no PLC communication was attempted.`
- `python tools\run_downstream_read_checks.py --profile melsec:iq-r:rj71en71 --host 192.168.250.100 --port 1025 --device D1000 --execute --record-json <temp>` stopped before command execution because `--approved-live-ok` was not present, exited with code 2, and did not create the temp record file.
- `python tools\run_downstream_read_checks.py --profile melsec:iq-r:rj71en71 --host 192.168.250.100 --port 1025 --device D1000 --record-json <temp>` stayed in dry-run mode, printed the command plan, and did not create the temp record file.
- `python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --host 192.168.250.100 --port 1025 --device D1000` printed the .NET, Python, Rust, Node-RED, and C++ build/read command plan and ended with `dry-run only; no PLC communication was attempted.`
- `python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --execute` stopped before command execution because `--approved-live-ok` was not present.
- `python tools\run_downstream_read_checks.py --profile melsec:qcpu:qj71e71-100 --port not-a-number` failed during argument parsing, before any command plan or live action.
- `--record-json` was checked in dry-run and unapproved execute modes; neither mode created a record file.
- Before the RJ71EN71 live record existed, `python tools\audit_downstream_read_records.py --require-complete` returned non-zero and reported `rj71en71_4e=pending`.
- After `downstream-runs/rj71en71_iq-r_20260705.json` was recorded, `python tools\audit_downstream_read_records.py --records-dir evidence\unit-investigations\downstream-runs --require-complete` reported `downstream-read-records-ok records=6 valid=6 implementations=5 q_series_4e=pass rj71en71_4e=pass`.
- `python -m py_compile tools\run_downstream_read_checks.py tools\audit_unit_profile_rollout.py tools\audit_downstream_read_records.py` succeeded.

These checks validate the planner gate only. They are not live-read evidence and do not satisfy the implementation checklist above.

## Completion Rule

The GOAL-3 downstream read condition is satisfied only when all five implementation rows are `pass`.

The Q-series 4E condition is satisfied when at least one passing row uses a QJ71E71-100 profile (`melsec:qcpu:qj71e71-100`, `melsec:qnu:qj71e71-100`, or `melsec:qnudv:qj71e71-100`) and the implementation reports or is known by profile defaults to use 4E + Q/L.

The RJ71EN71 condition is satisfied when a passing row uses
`melsec:iq-r:rj71en71` and the implementation reports or is known by profile
defaults to use 4E + iQ-R.
