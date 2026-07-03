# QnUDV Z/R/ZR Range Probe

- Date: 2026-07-03 13:17:21 +09:00
- PLC: QnUDV built-in CPU / `192.168.250.100:1025` / TCP
- Frame/Profile: 3E / Q-L compatible / `melsec:qnudv`
- Policy: range boundary checks use raw direct read for one-past-end so PLC response, not client guard, decides the result. Low-address write checks use read/write/read/restore/final-read.
- Result: OK

## Conclusion

| Family | Usable Range On This PLC | Boundary Result | Practical Routes |
|--------|--------------------------|-----------------|------------------|
| `Z` | `Z0..Z19` | `Z19` read `0000`; `Z20` raw read `4031` | `Z10` direct, random, named `:U` write/read/restore OK |
| `R` | `R0..R32767` | `R32767` read `0000`; `R32768` raw read `4031` | `R10` direct, random, named `:U` write/read/restore OK |
| `ZR` | `ZR0..ZR393215` | `ZR393215` read `0000`; `ZR393216` raw read `4031` | `ZR10` direct, random, named `:U` write/read/restore OK |

Final low-address values after restore:

| Device | Final Value |
|--------|-------------|
| `Z10` | `0x0000` |
| `R10` | `0x2BD1` |
| `ZR10` | `0x2BD1` |

## Boundary Read Results

| Item | Status | Detail |
|------|--------|--------|
| `Z19` direct read | OK | end=`0000`, value=`0x0000` |
| `Z20` direct read raw | OK | end=`4031`, data=`00 FF FF 03 00 01 04 00 00` |
| `R32767` direct read | OK | end=`0000`, value=`0x06BB` |
| `R32768` direct read raw | OK | end=`4031`, data=`00 FF FF 03 00 01 04 00 00` |
| `ZR393215` direct read | OK | end=`0000`, value=`0xB5EB` |
| `ZR393216` direct read raw | OK | end=`4031`, data=`00 FF FF 03 00 01 04 00 00` |

## Low-Address Write Results

| Route | Device | Detail |
|-------|--------|--------|
| direct `1401/0000` | `Z10` | before=`0x0000`, write=`0x0123`, after=`0x0123`, restored=`0x0000` |
| direct `1401/0000` | `R10` | before=`0x2BD1`, write=`0x2345`, after=`0x2345`, restored=`0x2BD1` |
| direct `1401/0000` | `ZR10` | before=`0x2BD1`, write=`0x3456`, after=`0x3456`, restored=`0x2BD1` |
| random `1402/0000` | `Z10` | before=`0x0000`, write=`0x0456`, after=`0x0456`, restored=`0x0000` |
| random `1402/0000` | `R10` | before=`0x2BD1`, write=`0x4567`, after=`0x4567`, restored=`0x2BD1` |
| random `1402/0000` | `ZR10` | before=`0x2BD1`, write=`0x5678`, after=`0x5678`, restored=`0x2BD1` |
| named `:U` | `Z10:U` | before=`0x0000`, write=`0x0789`, after=`0x0789`, restored=`0x0000` |
| named `:U` | `R10:U` | before=`0x2BD1`, write=`0x789A`, after=`0x789A`, restored=`0x2BD1` |
| named `:U` | `ZR10:U` | before=`0x2BD1`, write=`0x89AB`, after=`0x89AB`, restored=`0x2BD1` |

## Boundary Trace

| # | command/sub | target | end | request | response |
|---|-------------|--------|-----|---------|----------|
| 1 | `0401/0000` | `Z19` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 13 00 00 CC 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 00 00` |
| 2 | `0401/0000` | `Z20` | `4031` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 14 00 00 CC 01 00` | `D0 00 00 FF FF 03 00 0B 00 31 40 00 FF FF 03 00 01 04 00 00` |
| 3 | `0401/0000` | `R32767` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 FF 7F 00 AF 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 BB 06` |
| 4 | `0401/0000` | `R32768` | `4031` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 00 80 00 AF 01 00` | `D0 00 00 FF FF 03 00 0B 00 31 40 00 FF FF 03 00 01 04 00 00` |
| 5 | `0401/0000` | `ZR393215` | `0000` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 FF FF 05 B0 01 00` | `D0 00 00 FF FF 03 00 04 00 00 00 EB B5` |
| 6 | `0401/0000` | `ZR393216` | `4031` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 00 00 06 B0 01 00` | `D0 00 00 FF FF 03 00 0B 00 31 40 00 FF FF 03 00 01 04 00 00` |

## Representative Random Write Trace

| command/sub | target | end | request | response |
|-------------|--------|-----|---------|----------|
| `1402/0000` | `Z10=0x0456` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 02 14 00 00 01 00 0A 00 00 CC 56 04` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| `1402/0000` | `R10=0x4567` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 02 14 00 00 01 00 0A 00 00 AF 67 45` | `D0 00 00 FF FF 03 00 02 00 00 00` |
| `1402/0000` | `ZR10=0x5678` | `0000` | `50 00 00 FF FF 03 00 0E 00 10 00 02 14 00 00 01 00 0A 00 00 B0 78 56` | `D0 00 00 FF FF 03 00 02 00 00 00` |
