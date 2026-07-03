# R120P / RCPU SLMP仕様判断資料

## 採用するプロファイル

| 項目 | 採用内容 |
|------|----------|
| PLC profile | `melsec:iq-r` |
| 実機型名 | `R120PCPU` |
| Frame | 4E |
| Compatibility | iQ-R |
| Standard subcommand | word=`0002`, bit=`0003` |
| Extended subcommand | word=`0082`, bit=`0083` |
| X/Y表記 | 16進表記 |

R120P / RCPU の機能可否は 4E / iQ-R profile を標準条件として判定する。3E / Q-L互換フレームは比較用であり、R120P の不可判定根拠にはしない。

## 採用する機能

| 機能 | 採用判断 |
|------|----------|
| Type Name `0101/0000` | 使用可 |
| Direct read/write `0401/1401` | 使用可 |
| Random read/write `0403/1402` | 使用可 |
| Block read/write `0406/1406` | 使用可 |
| Monitor `0801/0802` | 使用可 |
| Named通常デバイス | 使用可 |
| Long timer / retentive long timer | 専用ロング系経路で使用可 |
| Long counter | 専用ロング系経路で使用可 |
| `LZ` | `LZ0/LZ1` を32-bit経路で使用可 |
| `U3E0\G...` | この構成では使用可 |
| `U3E0\HG...` | iQ-R専用HG CPU-buffer経路として使用可 |
| `U2\G100` | この構成では使用可 |

## 採用しない機能

| 機能 | 判断 | 根拠 |
|------|------|------|
| `S` write | positive pathにしない | read は可、write は `4030` |
| `LTS/LTC/LSTS/LSTC` direct/block bit | positive pathにしない | read/write が `4030`。専用ロング系経路を使う |
| `LCN` 16-bit scalar/direct/block | positive pathにしない | `LCN` はダブルワード現在値として扱う |
| `LCS` write | positive pathにしない | 接点なので書込み対象にしない |
| `LZ` 16-bit direct/block | positive pathにしない | `LZ` はロング固定デバイス。32-bit経路を使う |
| `Z20` 以降 | positive pathにしない | `Z20` / `Z30` が `4031` |
| standalone `G/HG` | positive pathにしない | `U` 修飾付き extended access を使う |

## 今回扱わない機能

| 機能 | 判断 | 理由 |
|------|------|------|
| UDP経路 | この資料では判定しない | TCP `1025` の仕様判断資料 |
| UDF | この資料では判定しない | ユーザー指定により今回の確認範囲から除外 |

## デバイス範囲

今回の R120P / RCPU では、以下の扱いを採用する。

| デバイス | 採用範囲 / 扱い | 範囲外応答 | 備考 |
|----------|------------------|------------|------|
| `Z` | `Z0..Z19` | `Z20` / `Z30` = `4031` | 使用可 |
| `LZ` | `LZ0..LZ1` | `LZ2` / `LZ3` は存在しない | 32-bit経路のみ positive path |
| `S` | read-only | write = `4030` | write対象にしない |
| `U3E0\G...` | 構成依存で使用可 | - | direct/random/monitorで確認 |
| `U3E0\HG...` | iQ-R専用HG CPU-bufferとして使用可 | - | direct/random/monitorで確認 |
| `U2\G100` | 構成依存で使用可 | - | direct/random/monitorで確認 |

`Un\Gn` は「U付きなら何でも可」ではなくPLC構成依存である。対象PLCごとに毎回実在確認する。

## 点数上限

| コマンド | 採用上限 | 上限超過 |
|----------|----------|----------|
| direct word read `0401/0002` | 960点 | 961点 = `C051` |
| direct word write `1401/0002` | 960点 | 961点 = `C051` |
| direct bit read `0401/0003` | 7168点 | 7169点 = `C052` |
| direct bit write `1401/0003` | 7168点 | 7169点 = `C052` |
| random read `0403/0002` | 96 word | 97 word = `C054` |
| random word write `1402/0002` | 80 word / weighted 960 | 81 word / weighted 972 = `C054` |
| random bit write `1402/0003` | 94 bit | 95 bit = `C053` |
| monitor register `0801/0002` | 96 word | 97 word = `C054` |

## Block `0406/1406` の扱い

R120P 4E / iQ-R では block read/write を positive path とする。mixed block は `D + M` で word/bit 混在書込み・読戻し・復元成功。

| 種別 | positive path | positive pathにしないもの |
|------|---------------|---------------------------|
| Word block | `D`, `SD`, `W`, `TN`, `STN`, `CN`, `SW`, `Z`, `R`, `RD`, `ZR`, `LTN`, `LSTN` | `LCN` は専用ロング系経路、`LZ` は32-bit経路 |
| Bit block | `X`, `Y`, `M`, `L`, `SM`, `F`, `V`, `B`, `TS`, `TC`, `STS`, `STC`, `CS`, `CC`, `SB`, `DX`, `DY` | `S` write、`LTS/LTC/LSTS/LSTC`、`LCS/LCC` block |

## ロング系の扱い

ロングタイマ、ロング積算タイマ、ロングカウンタは、ユーザー向けには専用ロング系経路に集約する。利用者が direct/random/block の仕様差を意識しなくても、ロング系デバイス指定からライブラリ側が正しい経路へ振り分ける。

| 対象 | 採用判断 |
|------|----------|
| `LTN10` | `read_long_timer` で状態・現在値読出し可。`LTN10:D` write/read/restore可 |
| `LSTN10` | `read_long_retentive_timer` で状態・現在値読出し可。`LSTN10:D` write/read/restore可 |
| `LTS/LTC/LSTS/LSTC` | 状態は `LTN/LSTN` 4-wordからdecode。`LTC10:BIT`, `LSTC10:BIT` は write/read/restore可 |
| `LCN10` | `LCN10:D` / `LCN10:L` write/read/restore可 |
| `LCS10:BIT` / `LCC10:BIT` | 状態読出し可。`LCC10:BIT` は write/read/restore可 |
| `LCS` | 接点なので書込み対象にしない |

## `LZ` の扱い

`LZ` は `LZ0/LZ1` だけのロング固定デバイスとして扱う。16-bit direct/block を positive path にせず、32-bit の named/random dword 経路を使う。

| 対象 | 判断 |
|------|------|
| `LZ0` | random dword、named `:D`、named `:L` で write/read/restore可 |
| `LZ1` | random dword、named `:D`、named `:L` で write/read/restore可 |
| 16-bit direct/block | positive pathにしない |

## `U\G/HG` の扱い

R120P / RCPU では `U` 修飾付き extended access を採用する。`G` はユニットバッファ、`HG` は iQ-R専用HG CPU-buffer経路として扱う。standalone `G/HG` は使用しない。

| 対象 | 採用判断 |
|------|----------|
| `U3E0\G10` | direct/random/monitorで使用可 |
| `U3E0\HG20` | iQ-R専用HG CPU-buffer経路として direct/random/monitorで使用可 |
| `U2\G100` | direct/random/monitorで使用可 |

この結果は今回のR120P構成での positive path 判断に使うが、すべての `Un\Gn` に一般化しない。

## 仕様結論

`melsec:iq-r` は 4E / iQ-Rプロファイルとして扱う。通常 direct/random/block/monitor/named、専用ロング系、`LZ0/LZ1` の32-bit経路、実在確認済みの `U3E0\G...`、iQ-R専用 `U3E0\HG...`、`U2\G100` は positive path。`S` write、ロング系の不適切な direct/block、`LZ` の16-bit direct/block、`Z20` 以降、standalone `G/HG` は positive path にしない。
