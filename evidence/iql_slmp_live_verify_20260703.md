# MELSEC iQ-L / L16HCPU SLMP仕様判断資料

## 採用するプロファイル

| 項目 | 採用内容 |
|------|----------|
| PLC profile | `melsec:iq-l` |
| 実機型名 | `L16HCPU`, model code `0x48C2` |
| Frame | 4E |
| Compatibility | iQ-R互換 |
| Standard subcommand | word=`0002`, bit=`0003` |
| Extended subcommand | word=`0082`, bit=`0083` |
| X/Y表記 | 16進表記 |

iQ-L は `melsec:lcpu` とは別プロファイルとして扱う。LCPU の 3E / Q-L互換結果を iQ-L へ持ち込まない。

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
| `U1\G10` | この構成では使用可 |

`U1\G10` はユニット構成依存である。構文と経路はサポートするが、対象PLC構成で実在確認できた場合だけ positive path とする。

## 採用しない機能

| 機能 | 判断 | 根拠 |
|------|------|------|
| `S` write | positive pathにしない | `S10` read は可、write は read-only として停止 |
| `LZ2` | positive pathにしない | named `LZ2:D` read が `4031` |
| standalone `G/HG` | positive pathにしない | `U` 修飾付き extended access を使う |
| HGのCPU-buffer経路 | positive pathにしない | iQ-R専用。iQ-Lには定義しない |

## 今回扱わない・未判定の機能

| 機能 | 判断 | 理由 |
|------|------|------|
| link-direct | positive/negative を確定しない | 必要な機材がなく未検証。仕様上は使える可能性が高い |
| UDP経路 | この資料では判定しない | TCP `1025` の仕様判断資料 |
| UDF | この資料では判定しない | ユーザー指定により今回の確認範囲から除外 |

## デバイス範囲

`melsec:iq-l` の範囲カタログは以下として扱う。

| デバイス | 採用範囲 | 表記 |
|----------|----------|------|
| `X` | `X0000..X2FFF` | 16進 |
| `Y` | `Y0000..Y2FFF` | 16進 |
| `M` | `M0..M12287` | 10進 |
| `B` | `B0000..B1FFF` | 16進 |
| `SB` | `SB000..SB7FF` | 16進 |
| `F` | `F0..F2047` | 10進 |
| `V` | `V0..V2047` | 10進 |
| `L` | `L0..L8191` | 10進 |
| `S` | `S0..S1023` | 10進、read-only扱い |
| `D` | `D0..D10239` | 10進 |
| `W` | `W0000..W1FFF` | 16進 |
| `SW` | `SW000..SW7FF` | 16進 |
| `R` | `R0..R32767` | 10進 |
| `TS/TC/TN` | `0..1023` | 10進 |
| `STS/STC/STN` | `0..511` | 10進 |
| `CS/CC/CN` | `0..511` | 10進 |
| `LTS/LTC/LTN` | `0..1023` | 10進 |
| `LSTS/LSTC/LSTN` | `0..511` | 10進 |
| `LCS/LCC/LCN` | `0..511` | 10進 |
| `Z` | `Z0..Z19` | 10進 |
| `LZ` | `LZ0..LZ1` | 10進、32-bit経路のみ positive path |
| `ZR` | `ZR0..ZR716799` | 10進 |
| `RD` | `RD0..RD524287` | 10進 |
| `SM` | `SM0..SM4095` | 10進 |
| `SD` | `SD0..SD4095` | 10進 |

## 点数上限

| コマンド | 採用上限 | 上限超過 |
|----------|----------|----------|
| direct word read `0401/0002` | 960点 | 961点 = `C051` |
| direct word write `1401/0002` | 960点 | 961点 = `C051` |
| direct bit read `0401/0003` | 7168点 | 7169点 = `C052` |
| direct bit write `1401/0003` | 7168点 | 7169点 = `C052` |
| random read `0403/0002` | 96 word | 97 word = `C054` |
| random word write `1402/0002` | 80 word | 81 word = `C054` |
| random bit write `1402/0003` | 94 bit | 95 bit = `C053` |

## ロング系の扱い

iQ-L ではロングタイマ、ロング積算タイマ、ロングカウンタを positive path とする。ただしユーザー向けには direct/random/block の細かな差を見せず、専用ロング系経路に集約する。

| 対象 | 採用判断 |
|------|----------|
| `LTN10` | `read_long_timer` で状態・現在値読出し可 |
| `LSTN10` | `read_long_retentive_timer` で状態・現在値読出し可 |
| `LTS10:BIT` / `LTC10:BIT` | named state read可 |
| `LSTS10:BIT` / `LSTC10:BIT` | named state read可 |
| `LTN10:D` | write/read/restore可 |
| `LSTN10:D` | write/read/restore可 |
| `LCN10:D` | write/read/restore可 |
| `LCC10:BIT` | write/read/restore可 |
| `LCS` | 接点として読出し対象。write対象にしない |

確認値:

```text
LTN10:D   0 -> 0x00001234 -> 0
LSTN10:D  0 -> 0x00002345 -> 0
LCN10:D   0 -> 0x00003456 -> 0
LCC10:BIT False -> True -> False
```

## `LZ` の扱い

`LZ` は `LZ0/LZ1` だけのロング固定デバイスとして扱う。16-bit direct/block を positive path にせず、32-bit の named/random dword 経路を使う。

| 対象 | 判断 |
|------|------|
| `LZ0/LZ1` | 32-bit経路で positive path |
| `LZ1:D` | `0 -> 0x00004567 -> 0` の write/read/restore可 |
| `LZ2:D` | `4031` のため positive pathにしない |

## `U\G` の扱い

`Un\Gn` はユニット構成依存である。今回の iQ-L / L16HCPU 構成では `U1\G10` が direct extended word `0401/0082` / `1401/0082` で read/write/restore成功した。

```text
U1\G10 0x0000 -> 0x4567 -> 0x0000
```

この結果は `U1\G10` の positive path 判断には使うが、すべての `Un\Gn` に一般化しない。

## 仕様結論

`melsec:iq-l` は `melsec:lcpu` とは分け、4E / iQ-R互換プロファイルとして扱う。通常 direct/random/block/monitor/named、ロング系、`LZ0/LZ1`、実在確認済みの `U1\G10` は positive path。`S` write、`LZ2`、standalone `G/HG`、iQ-R専用のHG CPU-buffer経路は positive path にしない。link-direct は機材なしで未検証のため、使える可能性が高い未判定項目として扱う。
