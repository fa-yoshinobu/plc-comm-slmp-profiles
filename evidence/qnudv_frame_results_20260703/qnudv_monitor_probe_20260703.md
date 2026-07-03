# QnUDV Monitor Probe

- Date: 2026-07-03
- PLC: QnUDV built-in CPU / `192.168.250.100:1025` / TCP
- Frame/Profile: 3E / Q-L compatible / `melsec:qnudv`
- Scope: `0801/0802` monitor registration and execution
- Result: OK

## Results

| Item | Status | Detail |
|------|--------|--------|
| monitor `D9000` | OK | `0801/0000` end=`0000`, `0802/0000` end=`0000`, value=`0x0000` |
| monitor `R10` | OK | `0801/0000` end=`0000`, `0802/0000` end=`0000`, value=`0x2BD1` |
| monitor `ZR10` | OK | `0801/0000` end=`0000`, `0802/0000` end=`0000`, value=`0x2BD1` |
| monitor `D9000 + R10 + ZR10` | OK | values=`0x0000, 0x2BD1, 0x2BD1` |
| monitor word 192 | OK | `0801/0000` end=`0000`, `0802/0000` end=`0000`, returned 192 words |
| monitor word 193 high-level | OK | send-before guard: `register_monitor_devices total access points out of range (1..192)` |
| monitor word 193 raw | OK | raw `0801/0000` end=`C054` |

## Trace Summary

| # | command/sub | end | note |
|---|-------------|-----|------|
| 1 | `0801/0000` | `0000` | register `D9000` |
| 2 | `0802/0000` | `0000` | execute, returns `00 00` |
| 3 | `0801/0000` | `0000` | register `R10` |
| 4 | `0802/0000` | `0000` | execute, returns `D1 2B` |
| 5 | `0801/0000` | `0000` | register `ZR10` |
| 6 | `0802/0000` | `0000` | execute, returns `D1 2B` |
| 7 | `0801/0000` | `0000` | register `D9000`, `R10`, `ZR10` |
| 8 | `0802/0000` | `0000` | execute, returns `00 00 D1 2B D1 2B` |
| 9 | `0801/0000` | `0000` | register 192 word devices |
| 10 | `0802/0000` | `0000` | execute, returns 192 words |
| 11 | `0801/0000` | `C054` | raw register 193 word devices |

## Conclusion

QnUDV built-in CPU supports monitor `0801/0802` on the 3E / Q-L compatible path. Treat monitor as a positive path with a 192-word registration limit; 193-word raw registration returns `C054`.
