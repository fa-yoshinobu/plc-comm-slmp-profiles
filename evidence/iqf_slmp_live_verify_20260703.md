# MELSEC iQ-F / FX5 SLMP仕様判断資料

## 採用するプロファイル

| 項目 | 採用内容 |
|------|----------|
| PLC profile | `melsec:iq-f` |
| Frame | 3E |
| Compatibility | Q/L互換 |
| Standard subcommand | word=`0000`, bit=`0001` |
| Extended subcommand | word=`0080`, bit=`0081` |
| X/Y表記 | 8進表記 |

R120P の 4E / iQ-R 前提、QnUDV / LCPU のデバイス範囲、R120P の `U\G` positive path は iQ-F へ持ち込まない。

## 採用する機能

iQ-F / FX5 では、以下を positive path として扱う。

| 機能 | 採用判断 |
|------|----------|
| Type Name `0101/0000` | 使用可 |
| Direct read/write `0401/1401` | 使用可 |
| Random read/write `0403/1402` | 使用可 |
| Block read/write `0406/1406` | 使用可 |
| Named通常デバイス | 使用可 |
| `LC` ロングカウンタ | `LC0..LC63` を使用可 |
| `LZ` | `LZ0/LZ1` を32-bit経路で使用可 |
| `U1\G...` | 特殊ユニットが存在する構成では使用可 |

`U1\G...` はユニット構成依存である。iQ-F全体で常に使える機能ではなく、対象PLC構成で実在確認できた場合だけ positive path とする。

## 採用しない機能

| 機能 | 判断 | 根拠 |
|------|------|------|
| Monitor `0801/0802` | positive pathにしない | `D10` 単独でも `C059` |
| `U0\G0` | positive pathにしない | `C060` |
| `U2\G1000` | positive pathにしない | `C060` |
| `ZR` | positive pathにしない | `C05C` |
| `RD` | positive pathにしない | `C05C` |
| `V` | positive pathにしない | `C05C` |
| `LT` / `LST` | positive pathにしない | `C05C` |
| HGのCPU-buffer経路 | positive pathにしない | iQ-R専用。iQ-Fには定義しない |

## 今回扱わない機能

| 機能 | 判断 | 理由 |
|------|------|------|
| UDP経路 | この資料では判定しない | TCP `1025` の仕様判断資料。UDPは既存確認済みとして今回含めない |
| UDF | この資料では判定しない | ユーザー指定により今回の確認範囲から除外 |

## デバイス範囲

SD範囲から得た iQ-F / FX5 の範囲は以下として扱う。

```text
X=1024, Y=1024, M=7680, B=256, SB=512, F=128, L=7680,
D=8000, W=512, SW=512, T=512, ST=16, C=256,
LC=64, Z=20, LZ=2, R=32768
```

| デバイス | 採用範囲 | 範囲外応答 | 備考 |
|----------|----------|------------|------|
| `X` | `X0..X1777` | `X2000` = `C056` | 8進表記、入力なのでread-only |
| `Y` | `Y0..Y1777` | `Y2000` = `C056` | 8進表記、write/read/restore可 |
| `Z` | `Z0..Z19` | `Z20` = `C056` | 使用可 |
| `R` | `R0..R32767` | `R32768` = `C056` | 使用可 |
| `LC` | `LC0..LC63` | `LC64` = `C056` | long counterとして扱う |
| `LZ` | `LZ0..LZ1` | `LZ2` = `C056` | 32-bit経路のみ positive path |

## 点数上限

| コマンド | 採用上限 | 上限超過 |
|----------|----------|----------|
| direct word read `0401/0000` | 960点 | 961点 = `C052` |
| direct word write `1401/0000` | 960点 | 961点 = `C052` |
| direct bit read `0401/0001` | 3584点 | 3585点 = `C051` |
| direct bit write `1401/0001` | 3584点 | 3585点 = `C051` |
| random read `0403/0000` | 192 word | 193 word = `C054` |
| random word write `1402/0000` | 160 word | 161 word = `C054` |
| random bit write `1402/0001` | 188 bit | 189 bit = `C053` |

## `U\G` の扱い

`Un\Gn` は iQ-F でもユニット構成に依存する。ライブラリ仕様としては、構文とフレームはサポートするが、対象PLCに該当ユニットが存在しない場合の `C060` はPLC構成由来として扱う。

HGのCPU-buffer経路はiQ-R専用であり、iQ-Fには定義しない。iQ-Fで確認対象にするのは `U1\G...` のようなG系ユニットバッファアクセスである。

| 対象 | 判断 |
|------|------|
| `U0\G0` | `C060` のため、この構成では positive pathにしない |
| `U1\G0` | 特殊ユニットあり構成で read/write/restore成功 |
| `U1\G1` | 特殊ユニットあり構成で read/write/restore成功 |
| `U1\G10` | 特殊ユニットあり構成で read/write/restore成功 |
| `U2\G1000` | `C060` のため、この構成では positive pathにしない |

`U1\G...` の確認値:

| 対象 | 確認結果 |
|------|----------|
| `U1\G0` | `0x0000 -> 0x1234 -> 0x0000`、再確認 `0x0000 -> 0x1357 -> 0x0000` |
| `U1\G1` | `0x0000 -> 0x2345 -> 0x0000`、再確認 `0x0000 -> 0x2468 -> 0x0000` |
| `U1\G10` | `0x0000 -> 0x3456 -> 0x0000`、再確認 `0x0000 -> 0x3579 -> 0x0000` |

結論: `U1\G...` は、特殊ユニットが存在するFX5U構成では direct extended word `0401/0080` / `1401/0080` の positive path とする。ただし、すべての `Un\Gn` に一般化しない。

## FX5UC と FX5U の差分

| 項目 | FX5UC-32MT/D | FX5U-32MR/DS 特殊ユニットあり | 仕様判断 |
|------|--------------|-------------------------------|----------|
| Type Name | `FX5UC-32MT/D`, model `0x4A91` | `FX5U-32MR/DS`, model `0x4A41` | 型名差分のみ |
| 通常direct/random/named | 成功 | 成功 | 同一扱い |
| block `0406/1406` | 成功 | 成功 | positive path |
| monitor `0801/0802` | `C059` | `C059` | positive pathにしない |
| SD範囲 | 同じ | 同じ | 同一扱い |
| `LC` / `LZ` | 成功 | 成功 | positive path |
| `ZR/RD/V/LT/LST` | `C05C` | `C05C` | positive pathにしない |
| `U1\G...` | `C060` または未確認 | 成功 | 構成依存として扱う |

FX5UC と FX5U で、通常機能・境界・範囲は同一判断にする。差分は特殊ユニット構成による `U1\G...` の成立可否であり、PLCシリーズ差ではなく構成差として扱う。

## 仕様結論

`melsec:iq-f` は 3E / Q-L互換プロファイルとして扱う。通常 direct/random/block/named、`LC`、`LZ` は positive path。monitor、`ZR/RD/V/LT/LST`、iQ-R専用のHG CPU-buffer経路は positive pathにしない。`U\G` は構文・経路としてはサポートし、実在ユニットがある場合のみ positive path とする。
