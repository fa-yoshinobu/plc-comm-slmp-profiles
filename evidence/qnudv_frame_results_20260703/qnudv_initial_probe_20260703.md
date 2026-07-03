# QnUDV Built-in CPU Initial SLMP Probe

- Date: 2026-07-03 13:10:13
- PLC: QnUDV built-in CPU / `192.168.250.100:1025` / TCP
- Model: `unknown`
- Frame/Profile: 3E / Q-L compatible / `melsec:qnudv`
- Policy: QnUDV built-in Ethernet is evaluated separately from R120P. Direct and random device commands are positive paths; block commands are checked as target/path non-support, not as library failures.
- Result: OK

## Results

| Item | Status | Detail |
|------|--------|--------|
| read_type_name | EXPECTED | end=0xC059, data=00 FF FF 03 00 01 01 00 00; QnUDV built-in path may not support 0101 |
| direct word read D9000 | OK | value=0x0000 |
| direct word write D9000 | OK | before=0x0000, write=0x3456, after=0x3456, restored=0x0000 |
| direct bit read Y1FFF | OK | value=False |
| direct bit write Y1FFF | OK | before=False, write=True, after=True, restored=False |
| random word write D9000 | OK | before=0x0000, write=0x2345, after=0x2345, restored=0x0000 |
| random bit write Y1FFF | OK | before=False, write=True, after=True, restored=False |
| named read | OK | {'D9000:U': 0, 'Y1FFF:BIT': False} |
| read-ext U0\G10 | NG | end=0xC070, data=00 FF FF 03 00 01 04 80 00 |
| read-ext U2\G1000 | NG | end=0xC070, data=00 FF FF 03 00 01 04 80 00 |
| high-level read_block guard | OK | ValueError: Read Block (0x0406) is not supported for plc_profile 'melsec:qnudv'. Use direct or random device commands. |
| raw read_block D9000=1 | OK | end=0xC059, data=00 FF FF 03 00 06 04 00 00 |
| raw write_block D9000=current | OK | end=0xC059, data=00 FF FF 03 00 06 14 00 00, after=0x0000 |

## Trace

| # | command/sub | end | request | response |
|---|-------------|-----|---------|----------|
| 1 | `0101/0000` | `C059` | `50 00 00 FF FF 03 00 06 00 10 00 01 01 00 00` | `D0 00 00 FF FF 03 00 0B 00 59 C0 00 FF FF 03 00 01 01 00 00` |
| 2 | `0401/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 3 | `1401/0000` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 01 14 00 00 28 23 00 A8 01 00 56 34` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 4 | `0401/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 56 34` |
| 5 | `1401/0000` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 01 14 00 00 28 23 00 A8 01 00 00 00` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 6 | `0401/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 7 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 00` |
| 8 | `1401/0001` | `0000` | `50 00 00 FF FF 03 00 0D 00 10 00 01 14 01 00 FF 1F 00 9D 01 00 10` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 9 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 10` |
| 10 | `1401/0001` | `0000` | `50 00 00 FF FF 03 00 0D 00 10 00 01 14 01 00 FF 1F 00 9D 01 00 00` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 11 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 00` |
| 12 | `0403/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 03 04 00 00 01 00 28 23 00 A8` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 13 | `1402/0000` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 02 14 00 00 01 00 28 23 00 A8 45 23` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 14 | `0403/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 03 04 00 00 01 00 28 23 00 A8` | `D0 00 00 FF FF 03 00 04 00 00 00 45 23` |
| 15 | `1402/0000` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 02 14 00 00 01 00 28 23 00 A8 00 00` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 16 | `0403/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 03 04 00 00 01 00 28 23 00 A8` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 17 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 00` |
| 18 | `1402/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 02 14 01 00 01 FF 1F 00 9D 01` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 19 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 10` |
| 20 | `1402/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 02 14 01 00 01 FF 1F 00 9D 00` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| 21 | `0401/0001` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 FF 1F 00 9D 01 00` | `D0 00 00 FF FF 03 00 03 00 00 00 00` |
| 22 | `0403/0000` | `0000` | `50 00 00 FF FF 03 00 10 00 10 00 03 04 00 00 02 00 28 23 00 A8 F0 1F 00 9D` | `D0 00 00 FF FF 03 00 06 00 00 00 00 00 00 00` |
| 23 | `0401/0080` | `C070` | `50 00 00 FF FF 03 00 13 00 10 00 01 04 80 00 00 00 0A 00 00 AB 00 00 00 00 F8 01 00` | `D0 00 00 FF FF 03 00 0B 00 70 C0 00 FF FF 03 00 01 04 80 00` |
| 24 | `0401/0080` | `C070` | `50 00 00 FF FF 03 00 13 00 10 00 01 04 80 00 00 00 E8 03 00 AB 00 00 02 00 F8 01 00` | `D0 00 00 FF FF 03 00 0B 00 70 C0 00 FF FF 03 00 01 04 80 00` |
| 25 | `0406/0000` | `C059` | `50 00 00 FF FF 03 00 0E 00 10 00 06 04 00 00 01 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 0B 00 59 C0 00 FF FF 03 00 06 04 00 00` |
| 26 | `0401/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 27 | `1406/0000` | `C059` | `50 00 00 FF FF 03 00 10 00 10 00 06 14 00 00 01 00 28 23 00 A8 01 00 00 00` | `D0 00 00 FF FF 03 00 0B 00 59 C0 00 FF FF 03 00 06 14 00 00` |
| 28 | `0401/0000` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 28 23 00 A8 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
