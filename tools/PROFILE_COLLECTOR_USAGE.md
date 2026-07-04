# SLMP Profile Collector Usage

Use `slmp-profile-collector.exe` on a prepared test PLC to collect profile evidence for a PLC that maintainers do not have.

Do not run this tool against a production machine or a PLC that controls live equipment.

## What The Tool Does

- Connects to the PLC over SLMP TCP.
- Reads the PLC type name.
- Reads the SD range block used by the selected profile.
- Reads the first address of each device family.
- Writes test values to configured test devices and reads them back.
- Saves one JSON result file in the current folder.

By default, the tool writes to these devices:

| Purpose | Default device |
| --- | --- |
| Word write test | `D1000` |
| Bit write test | `M1000` |
| `S` write policy test | `S2` |

Numeric write values are random and are not restored. Bit write tests reset the tested bit to OFF after the check.

## Basic Run

```bat
slmp-profile-collector.exe --profile melsec:iq-f --host 192.168.250.100 --plc-model FX5U-32MR/DS
```

The tool creates a file like:

```text
slmp_profile_collect_iq-f_20260704_130000.json
```

Send that JSON file back to the maintainer.

## List Profiles

```bat
slmp-profile-collector.exe --list-profiles
```

## Common Examples

### iQ-F / FX5

```bat
slmp-profile-collector.exe --profile melsec:iq-f --host 192.168.250.100 --plc-model FX5U-32MR/DS
```

### iQ-R

```bat
slmp-profile-collector.exe --profile melsec:iq-r --host 192.168.250.100 --plc-model R120PCPU
```

### QnUDV

```bat
slmp-profile-collector.exe --profile melsec:qnudv --host 192.168.250.100 --plc-model Q06UDVCPU
```

## Change Test Devices

Use this when the default devices are not available on the prepared test PLC.

```bat
slmp-profile-collector.exe --profile melsec:iq-f --host 192.168.250.100 --word-write-device D2000 --bit-write-device M2000 --s-write-device S2
```

## Read-Only Run

Use this only when writes are intentionally not allowed. This is less useful for profile maintenance because write policy cannot be confirmed.

```bat
slmp-profile-collector.exe --profile melsec:iq-f --host 192.168.250.100 --skip-writes
```

## Other Connection Options

```bat
slmp-profile-collector.exe --profile melsec:iq-r --host 192.168.250.100 --port 1025 --timeout 5
```

For routed access targets, the normal SLMP target fields are available:

```bat
slmp-profile-collector.exe --profile melsec:iq-r --host 192.168.250.100 --network 0 --station 255 --module-io 0x03FF --multidrop 0
```

## Build The EXE

From the repository root:

```bat
tools\build_profile_collector_exe.bat
```

The executable is created at:

```text
dist\slmp-profile-collector.exe
```

Rebuild the executable whenever the bundled profile JSON or device-range JSON changes.
