# QnUDV Long-Family Probe

- Date: 2026-07-03 13:23:08 +09:00
- PLC: QnUDV built-in CPU / `192.168.250.100:1025` / TCP
- Frame/Profile: 3E / Q-L compatible / `melsec:qnudv`
- Policy: R120Pのロング系結果を持ち込まず、QnUDV内蔵CPUで使えるかを実機で確認する。ユーザー確認により、このQnUDVではロング系は「なし」と扱う。
- Result: not supported on this target/path

## Conclusion

今回のQnUDV内蔵CPU / 3E Q-L compatible path では、ロングタイマ、ロング積算タイマ、ロングカウンタを positive path にしない。

- `LTN/LSTN` 4-word long route: `C05B`
- `LTS/LTC/LSTS/LSTC` named state route: underlying `LTN/LSTN` read が `C05B`
- `LCN` dword route: random dword read が `C05B`
- `LCS/LCC` state route: direct bit read が `C05B`
- write/read/restore は事前readで失敗したため、write要求には到達していない

## Results

| Item | Result |
|------|--------|
| `read_long_timer LTN10` | `C05B` / error info `00 FF FF 03 00 01 04 00 00` |
| `read_long_retentive_timer LSTN10` | `C05B` / error info `00 FF FF 03 00 01 04 00 00` |
| named state read `LTS10:BIT`, `LTC10:BIT`, `LSTS10:BIT`, `LSTC10:BIT` | `C05B` via `LTN10` read |
| named current write `LTN10:D` | before-read `C05B`; write not sent |
| named current write `LSTN10:D` | before-read `C05B`; write not sent |
| named coil write `LTC10:BIT` | before-read `C05B`; write not sent |
| named coil write `LSTC10:BIT` | before-read `C05B`; write not sent |
| named snapshot `LCN10:D`, `LCN10:L`, `LCS10:BIT`, `LCC10:BIT` | `C05B` via `LCN10` random dword read |
| named current write `LCN10:D` | before-read `C05B`; write not sent |
| named current write `LCN10:L` | before-read `C05B`; write not sent |
| named coil write `LCC10:BIT` | before-read `C05B`; write not sent |
| `read_long_timer LTN0` | `C05B` / error info `00 FF FF 03 00 01 04 00 00` |
| `read_long_retentive_timer LSTN0` | `C05B` / error info `00 FF FF 03 00 01 04 00 00` |
| named `LCN0:D` | `C05B` / error info `00 FF FF 03 00 03 04 00 00` |
| named `LCC0:BIT` | `C05B` / error info `00 FF FF 03 00 01 04 01 00` |

## Trace

| # | command/sub | target | end | request | response |
|---|-------------|--------|-----|---------|----------|
| 1 | `0401/0000` | `LTN10` 4 words | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 0A 00 00 52 04 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 00 00` |
| 2 | `0401/0000` | `LSTN10` 4 words | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 0A 00 00 5A 04 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 00 00` |
| 3 | `0403/0000` | `LCN10` dword | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 03 04 00 00 00 01 0A 00 00 56` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 03 04 00 00` |
| 4 | `0401/0001` | `LCC10` bit | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 0A 00 00 54 01 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 01 00` |
| 5 | `0401/0000` | `LTN0` 4 words | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 00 00 00 52 04 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 00 00` |
| 6 | `0401/0000` | `LSTN0` 4 words | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 00 00 00 5A 04 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 00 00` |
| 7 | `0403/0000` | `LCN0` dword | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 03 04 00 00 00 01 00 00 00 56` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 03 04 00 00` |
| 8 | `0401/0001` | `LCC0` bit | `C05B` | `50 00 00 FF FF 03 00 0C 00 10 00 01 04 01 00 00 00 00 54 01 00` | `D0 00 00 FF FF 03 00 0B 00 5B C0 00 FF FF 03 00 01 04 01 00` |
