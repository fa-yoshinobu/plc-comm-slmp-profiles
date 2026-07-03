# QnUDV内蔵CPU SLMP仕様判断資料

## 採用するプロファイル

| 項目 | 採用内容 |
|------|----------|
| PLC profile | `melsec:qnudv` |
| 実機型名 | `0101/0000` は `C059` のため型名読出しを positive path にしない |
| Frame | 3E |
| Compatibility | Q/L互換 |
| Standard subcommand | word=`0000`, bit=`0001` |
| Extended subcommand | word=`0080`, bit=`0081` |
| X/Y表記 | Q/L互換表記 |

QnUDV内蔵Ethernetは R120P の 4E / iQ-R path とは別ターゲットとして扱う。R120P の block / long / `U\G` positive path を QnUDV へ持ち込まない。

## 採用する機能

| 機能 | 採用判断 |
|------|----------|
| Direct read/write `0401/1401` | 使用可 |
| Random read/write `0403/1402` | 使用可 |
| Monitor `0801/0802` | 使用可 |
| Named通常デバイス | 使用可 |
| `Z` | `Z0..Z19` を使用可 |
| `R` | `R0..R32767` を使用可 |
| `ZR` | `ZR0..ZR393215` を使用可 |

`D9000` direct/random word、`Y1FFF` direct/random bit は write/read/restore 成功。`D9000:U` / `Y1FFF:BIT` は named read 成功。`Z10`, `R10`, `ZR10` は direct/random/named `:U` で write/read/restore 成功。monitor は `D9000`, `R10`, `ZR10` で登録・実行成功。

## 採用しない機能

| 機能 | 判断 | 根拠 |
|------|------|------|
| Type Name `0101/0000` | positive pathにしない | `C059` |
| Block read/write `0406/1406` | positive pathにしない | raw送信でも `C059`。high-level APIは送信前ガード対象 |
| `U\G` extended access | positive pathにしない | `U0\G10`, `U2\G1000` が `C070` |
| Long timer / retentive long timer | positive pathにしない | `LTN/LSTN` 代表readが `C05B` |
| Long counter | positive pathにしない | `LCN/LCC` 代表readが `C05B` |
| HGのCPU-buffer経路 | positive pathにしない | iQ-R専用。QnUDVには定義しない |

## 今回扱わない機能

| 機能 | 判断 | 理由 |
|------|------|------|
| UDP経路 | この資料では判定しない | TCP `1025` の仕様判断資料 |
| UDF | この資料では判定しない | ユーザー指定により今回の確認範囲から除外 |

## デバイス範囲

今回の QnUDV では、以下の範囲を採用する。

| デバイス | 採用範囲 | 範囲外応答 | 備考 |
|----------|----------|------------|------|
| `Z` | `Z0..Z19` | `Z20` = `4031` | 使用可 |
| `R` | `R0..R32767` | `R32768` = `4031` | 使用可 |
| `ZR` | `ZR0..ZR393215` | `ZR393216` = `4031` | 今回のQnUDV内蔵CPUで採用 |

## 点数上限

| コマンド | 採用上限 | 上限超過 |
|----------|----------|----------|
| direct word read `0401/0000` | 960点 | 961点 = `C051` |
| direct word write `1401/0000` | 960点 | 961点 = `C051` |
| direct bit read `0401/0001` | 7168点 | 7169点 = `C052` |
| direct bit write `1401/0001` | 7168点 | 7169点 = `C052` |
| random read `0403/0000` | 192 word | 193 word = `C054` |
| random word write `1402/0000` | 160 word / weighted 1920 | 161 word / weighted 1932 = `C054` |
| random bit write `1402/0001` | 188 bit | 189 bit = `C053` |
| monitor register `0801/0000` | 192 word | 193 word = `C054` |

## ロング系の扱い

この QnUDV ではロングタイマ、ロング積算タイマ、ロングカウンタは成立しない。R120P で使えた専用ロング系経路を QnUDV へ持ち込まない。

| 対象 | 判断 |
|------|------|
| `LTN10` / `LTN0` | 4-word read が `C05B` |
| `LSTN10` / `LSTN0` | 4-word read が `C05B` |
| `LTS/LTC/LSTS/LSTC` | named state read は元の `LTN/LSTN` read が `C05B` |
| `LCN10` / `LCN0` | dword read が `C05B` |
| `LCC10` / `LCC0` | bit read が `C05B` |

## 仕様結論

`melsec:qnudv` は 3E / Q/L互換プロファイルとして扱う。通常 direct/random/monitor/named、`Z0..Z19`、`R0..R32767`、`ZR0..ZR393215` は positive path。Type Name、block、`U\G` extended access、ロング系、iQ-R専用のHG CPU-buffer経路は positive path にしない。block は QnUDV実機で `C059` を確認済みのため、高レベルAPIでは送信前ガード対象にする。
