# SLMP実機検証指示書（監査F-1ほか）

- 作成日: 2026-07-03
- 背景資料: `D:\APP\review_slmp_spec_audit_20260703.md`（監査レポート）
- 目的: ライブラリ修正**前**に、実機でマニュアルとの不一致（F-1）の影響を確定させる
- 所要時間目安: F-1のみなら30分程度。オプション含め1〜2時間
- **読み書きするデバイスは D100 の読出しのみ（書込みなし）**。PLCの運転に影響しません。

---

## 検証したいこと（1行で）

「サブコマンド0080の一括読出し(0401)で、**現行ライブラリのバイト順（テストA）はPLCに拒否され、マニュアルのバイト順（テストB）は成功する**」ことを確認したい。

- マニュアル根拠: SH-080931 付1 p.204〜220 / SH-080003 付1 p.428〜432
  （図の画像: `D:\APP\MEL-PDF\extracted\SH-080931_p220_通常デバイス拡張レイアウト.png` ほか）

## 検証環境

- 対象PLC: これまでの検証実績がある **R120CPU/R08CPU（192.168.250.100）** を推奨。SLMPが有効ならどの iQ-R / Q / L / FX5 でも可
- 接続: Ethernet（TCP でも UDP でも可）
- フレーム: 下記バイト列は **3Eフレーム・バイナリコード** で記載（宛先は自局 00 FF FF 03 00）

## 送信フレーム（この3本を順に送る）

### ① ベースライン（通常読出し・必ず成功するはず）

D100を1ワード読出し（0401 / サブコマンド0000）:

```
50 00 00 FF FF 03 00 0C 00 10 00 01 04 00 00 64 00 00 A8 01 00
```

- 期待応答: `D0 00 00 FF FF 03 00 04 00 00 00 xx xx`（終了コード0000、xx xx = D100の値）
- ここで失敗する場合は接続・SLMP設定の問題なので以降は実施しない

### ② テストA: 現行ライブラリのレイアウト（不一致側・**拒否されるはず**）

同じD100読出しをサブコマンド0080で、現行ライブラリの標準ビルダーが生成する順序
（拡張指定が先頭: `拡張指定(2) 拡張指定修飾(1) 修飾idx(1) 修飾flags(1) デバイス番号(3) コード(1) DM(1)` = 10バイト）:

```
50 00 00 FF FF 03 00 12 00 10 00 01 04 80 00 00 00 00 00 00 64 00 00 A8 00 01 00
```

- 予想: 終了コード ≠ 0000（C051/C059/C05C系のエラーを想定）
- **もし0000で成功したら、その場合も応答データがベースラインのD100値と一致するか必ず記録**

### ③ テストB: マニュアルのレイアウト（**成功するはず**）

同じD100読出しをサブコマンド0080で、マニュアル付1の順序
（`デバイス修飾(2) デバイス番号(3) コード(1) 拡張指定修飾(2) 拡張指定(2) DM(1)` = 11バイト、全修飾ゼロ）:

```
50 00 00 FF FF 03 00 13 00 10 00 01 04 80 00 00 00 64 00 00 A8 00 00 00 00 00 01 00
```

- 期待応答: 終了コード0000、データ2バイトが①のD100値と一致

### （オプション）③' iQ-R系サブコマンド0082版

デバイス番号4バイト+コード2バイト、合計13バイト:

```
50 00 00 FF FF 03 00 15 00 10 00 01 04 82 00 00 00 64 00 00 00 A8 00 00 00 00 00 00 01 00
```

## 送信方法の例

手持ちのツールがあればそれで構いません（生バイトが送れれば何でもOK）。pythonライブラリがある環境なら改造不要でそのまま送れます:

```python
from slmp import SlmpClient  # plc-comm-slmp-python

cli = SlmpClient(host="192.168.250.100", transport="udp", frame_type="3e")
cli.connect()

# ①ベースライン:  devno(64 00 00) code(A8) points(01 00)
baseline = cli.raw_command(0x0401, subcommand=0x0000,
    payload=bytes.fromhex("640000A80100"), raise_on_error=False)

# ②テストA(現行ビルダー順): ext(00 00) extmod(00) idx(00) flags(00) devno(64 00 00) code(A8) DM(00) points(01 00)
test_a = cli.raw_command(0x0401, subcommand=0x0080,
    payload=bytes.fromhex("0000000000640000A8000100"), raise_on_error=False)

# ③テストB(マニュアル順): 修飾(00 00) devno(64 00 00) code(A8) 拡張指定修飾(00 00) 拡張指定(00 00) DM(00) points(01 00)
test_b = cli.raw_command(0x0401, subcommand=0x0080,
    payload=bytes.fromhex("0000640000A800000000000100"), raise_on_error=False)

for name, r in [("baseline", baseline), ("A(current)", test_a), ("B(manual)", test_b)]:
    print(name, f"end_code=0x{r.end_code:04X}", r.data.hex())
```

`raw_command` は payload をそのまま送るので、ライブラリの（疑いのある）ビルダーを経由しません。

## 判定基準

| 結果 | 判定 |
|------|------|
| ① OK / ② エラー / ③ OK（値一致） | **F-1確定**。ライブラリ標準ビルダーを③のレイアウトに修正する |
| ① OK / ② OK / ③ OK | PLCが両形式を受理（寛容）。それでもマニュアル準拠の③へ修正する方針は変えない。②の応答値がD100と一致するかで「誤解釈の有無」を判定 |
| ① OK / ③ エラー | 想定外。**終了コードとPLC型式・FWバージョンを記録して差し戻し**（マニュアル図の読み直しが必要） |

## 記録してほしいもの

1. PLC型式・ファームウェアバージョン、接続ユニット（CPU内蔵Ethernet / E71等）
2. ①②③それぞれの **終了コード（16進4桁）と応答データ全バイト**
3. 送信に使ったツール（pythonならバージョン）とTCP/UDPの別

結果は `D:\APP\review_slmp_spec_audit_20260703.md` のF-1欄に追記、または本ファイル末尾の「結果」欄に記入してください。

---

## オプション検証（時間があれば）

### F-3: 拡張サブコマンドの点数上限（読出しのみ・安全）

ランダム読出し(0403)をサブコマンド0080で**97点**指定 → マニュアル上限96点なのでエラーになるはず。96点なら成功するはず。
（現行ライブラリはLegacyモードで192点まで通してしまうため、その確認）

```python
devs = [(f"D{i}", None) for i in range(97)]  # 実際はライブラリのread_random_extで97点指定
```

ライブラリの`read_random_ext`（QL系列設定）で97点指定が**送信できてしまい**、PLCがエラーを返すことを確認。96点で成功すればマニュアル通り。

### F-4: FX5のビット上限（FX5があれば・読出しのみ）

FX5に対し 0401/0001 でM0から**3584点**読出し → 成功、**3600点** → エラー（マニュアル上限3584点。現行ライブラリは7168点まで送ってしまう）。

---

## 結果記入欄

| 項目 | 実施日 | PLC | 終了コード | 応答データ | 備考 |
|------|--------|-----|-----------|-----------|------|
| ① ベースライン | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | D100=0。通常0401/0000成功 |
| ② テストA | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | C05B | `00 FF FF 03 00 01 04 80 00` | 現行10バイト標準レイアウトはPLCが拒否 |
| ③ テストB | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | マニュアル11バイトレイアウト成功。D100値は①と一致 |
| ③' 0082版 | | | | | |
| F-3 96点 | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | 192バイト（D0〜D95、全0） | 0403/0080、マニュアル順11バイト指定、上限内成功 |
| F-3 97点 | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | C054 | `00 FF FF 03 00 03 04 80 00` | 0403/0080、マニュアル上限96点超過でPLCが拒否 |
| F-4 1点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | 0000 | 1バイト（`00`） | M0 1点、0401/0001、接続確認 |
| F-4 3584点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | 0000 | 1792バイト（先頭32バイト全0） | M0〜M3583、0401/0001、FX5上限内成功 |
| F-4 3600点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | C051 | `00 FF FF 03 00 01 04 01 00` | M0〜M3599、0401/0001、FX5上限3584点超過でPLCが拒否 |
| F-5 4E正常serial | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | D100 1ワード、4E/iQ-R形式、要求serial `1234` に対し応答serial `1234` |
| 修正後 4E通常読出し | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | 修正後python、4E/iQ-R 0401/0002、D100 1ワード、値`[0]` |
| 修正後 3E通常読出し | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | 修正後python、3E/Q-L 0401/0000、D100 1ワード、値`[0]` |
| 修正後 F-1 0080拡張読出し | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 0000 | `00 00` | 修正後pythonライブラリ経由。送信 `50 00 00 FF FF 03 00 13 00 10 00 01 04 80 00 00 00 64 00 00 A8 00 00 00 00 00 01 00`。マニュアル11バイトレイアウトで成功 |
| 修正後 F-3/F-8 raw 97点 | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | C054 | `00 FF FF 03 00 03 04 80 00` | raw 0403/0080、D0〜D96 97ワード。F-8構造化結果: network=00 station=FF module_io=03FF command=0403 subcommand=0080 |
| 修正後 F-3 APIガード 97点 | 2026-07-03 | R120P / 192.168.250.100:1025 TCP | 送信前拒否 | なし | 修正後python `read_random_ext` は97ワードを `1..96` 範囲外としてValueError。trace増分0で未送信確認 |
| 修正後 FX5U 1点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | 0000 | 1バイト（`00`） | 修正後python、3E/iQ-F 0401/0001、M0 1点、値`[False]` |
| 修正後 FX5U 3584点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | 0000 | 1792バイト | 修正後python、M0〜M3583、0401/0001、上限内成功。先頭16点すべてFalse |
| 修正後 F-4 APIガード 3585点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | 送信前拒否 | なし | 修正後python `read_devices("M0", 3585, bit_unit=True)` は `1..3584` 範囲外としてValueError。trace増分0で未送信確認 |
| 修正後 F-4/F-8 raw 3600点 | 2026-07-03 | FX5U / 192.168.250.100:1025 TCP | C051 | `00 FF FF 03 00 01 04 01 00` | raw 0401/0001、M0〜M3599。F-8構造化結果: network=00 station=FF module_io=03FF command=0401 subcommand=0001 |

## 追加結果: R120P実機検証（2026-07-03）

R120P実機検証の詳細は長くなったため、`r120p_slmp_live_verify_20260703.md` に分離した。

要点:
- R120P/RCPU の機能可否は **4Eフレーム + iQ-Rプロファイル + サブコマンド0002/0003/0082/0083** を標準条件として判定する。
- `0406/1406` block、`0401/1401` direct、`0403/1402` random、`0801/0802` monitor を実機確認済み。
- 書込み系は事前読出し、一時値書込み、読戻し、元値復元、最終読出しまで確認済み。
- `S`書込み、`LTS/LTC/LSTS/LSTC` のbit direct/block経路、`LCN/LCS/LCC` ロングカウンタ正規経路、`Z0..Z19` 上限、`LZ0/LZ1` ロング固定デバイス扱い、`U3E0\G/HG` と `U2\G100` positive path は分離先ファイルに記録。ロングタイマ、ロング積算タイマ、ロングカウンタはユーザー向けには専用ロング系経路に集約する。`LTS/LTC/LSTS/LSTC` の状態読出し、`LTN10:D`/`LSTN10:D` 現在値書込み、`LTC10:BIT`/`LSTC10:BIT` コイル書込みは read/write/restore成功。`LCN10:D`/`LCN10:L` の read/write/restore、`LCS10:BIT`/`LCC10:BIT` 状態読出し、`LCC10:BIT` コイル書込みも成功。`LCS` は接点なので今回の正規経路では書込み対象にしない。`LZ` の16-bit direct/blockは意味がないため必ずpositive pathにしない。`LZ0/LZ1` の random dword、named `:D`、named `:L` は read/write/restore成功。`U2\G100` は direct、random、monitorで成功。
- HGのCPU-buffer経路はiQ-R専用。iQ-F / iQ-L / LCPU / QCPU / QnU / QnUDV / MX系には定義しない。G系の `Un\Gn` ユニットバッファアクセスとは分けて扱う。
- `Un\Gn` はPLCのユニット構成で可否が変わるため、対象PLCごとに毎回実機確認する。

## 追加結果: QnUDV内蔵CPU実機検証（2026-07-03）

QnUDV内蔵CPU実機検証の詳細は `qnudv_slmp_live_verify_20260703.md` に分離した。

要点:
- QnUDV内蔵CPU の機能可否は **3Eフレーム + Q/L互換プロファイル + サブコマンド0000/0001** を標準条件として判定する。
- `D9000` direct/random word、`Y1FFF` direct/random bit は read/write/restore 成功。named read `D9000:U` / `Y1FFF:BIT` も成功。
- monitor `0801/0802` は `D9000` / `R10` / `ZR10` で成功。monitor登録は192 word成功、193 word rawで `C054`。
- `0101/0000` Read Type Name は `C059`。
- `0401/0080` extended read は `U0\G10` / `U2\G1000` とも `C070`。
- block `0406/1406` は high-level APIで送信前ガードし、raw送信でも `C059`。QnUDV内蔵Ethernet path のtarget/path非対応として扱う。
- direct最大点数は word 960点成功/961点`C051`、bit 7168点成功/7169点`C052`。
- random境界は read 192点成功/193点`C054`、word write weighted 1920成功/1932点相当`C054`、bit write 188点成功/189点`C053`。write境界は現在値をそのまま書き戻すsame-values方式で確認し、意図的な値変更は行っていない。
- `Z` は `Z0..Z19`、`R` は `R0..R32767`、`ZR` は `ZR0..ZR393215` が今回のQnUDV内蔵CPUで使用可。各上限+1はraw direct readで `4031`。`Z10` / `R10` / `ZR10` は direct、random、named `:U` で write/read/restore成功。
- ロングタイマ、ロング積算タイマ、ロングカウンタは今回のQnUDV内蔵CPUではなし。`LTN/LSTN/LCN/LCC` 代表readはいずれも `C05B` のため、R120Pの専用ロング系 positive path をQnUDVへ持ち込まない。write確認は事前readで失敗したため送信未到達。

## 追加結果: MELSEC-L/LCPU実機検証（2026-07-03）

MELSEC-L/LCPU実機検証の詳細は `lcpu_slmp_live_verify_20260703.md` に分離した。

要点:
- MELSEC-L/LCPU の機能可否は **3Eフレーム + Q/L互換プロファイル + サブコマンド0000/0001** を標準条件として判定する。
- `D10` direct/random word、`M10` direct/random bit は read/write/restore 成功。named read `D10:U` / `M10:BIT` も成功。
- monitor `0801/0802` は `D10` / `R10` / `ZR10` で成功。
- `0101/0000` Read Type Name は `C059`。
- `0401/0080` extended read は `U0\G10` / `U2\G1000` とも `C070`。
- block `0406/1406` は raw送信でも `C059`。LCPU pathでは block をpositive pathにしない。
- direct最大点数は word 960点成功/961点`C051`、bit 7168点成功/7169点`C052`。
- random境界は read 192点成功/193点`C054`、word write weighted 1920成功/1932点相当`C054`、bit write 188点成功/189点`C053`。write境界は現在値をそのまま書き戻すsame-values方式で確認し、意図的な値変更は行っていない。
- `D9000` はこのLCPUでは `4031` のため、点数上限確認の基点には使わない。
- `Z` は `Z0..Z19`、`R` は `R0..R32767`、`ZR` は `ZR0..ZR131071` が今回のLCPUで使用可。各上限+1はraw direct readで `4031`。`Z10` / `R10` / `ZR10` は direct、random、named `:U` で write/read/restore成功。
- ロングタイマ、ロング積算タイマ、ロングカウンタ、`LZ` は今回のLCPUではなし。`LTN/LSTN/LCN/LCC/LZ` 代表readはいずれも `C05B` のため、R120Pの専用ロング系 positive path と `LZ0/LZ1` positive path をLCPUへ持ち込まない。

## 追加結果: MELSEC iQ-F / FX5UC実機検証（2026-07-03）

MELSEC iQ-F / FX5UC実機検証の詳細は `iqf_slmp_live_verify_20260703.md` に分離した。

要点:
- MELSEC iQ-F / FX5UC の機能可否は **3Eフレーム + Q/L互換プロファイル + サブコマンド0000/0001** を標準条件として判定する。ソフト側プロファイルは `melsec:iq-f`。
- 型名応答 `0101/0000` は `FX5UC-32MT/D`、model code `0x4A91`。
- `X` / `Y` 文字表記は8進。`X1777` / `Y1777` は成功、`X2000` / `Y2000` は `C056`。
- `D10` direct/random/named word、`M10` direct/random bit は read/write/restore 成功。`X10` はread成功、`Y10` はwrite/read/restore成功。
- block `0406/1406` は `D10` / `M10` で read/write same-values成功。iQ-Fではblockをpositive pathにする。
- monitor `0801/0802` は `D10` 単独でも `C059`。iQ-Fではmonitorをpositive pathにしない。
- `0401/0080` extended read は初回FX5UC構成では `U0\G0` / `U1\G0` / `U2\G1000` がいずれも `C060`。特殊ユニットありFX5へ交換後、`U1\G0` read は成功。`Un\Gn` はiQ-Fでも構成依存として対象PLCごとに確認する。
- 特殊ユニットあり別品番FX5U-32MR/DSで全項目を再確認した結果、通常機能・境界・範囲・block/monitor可否・未対応デバイスは初回FX5UCと同等。差分は型名と `U1\G0/G1/G10` の成功のみ。`U1\G0/G1/G10` は write/read/restore も成功。詳細は `iqf_slmp_live_verify_20260703.md` に集約。
- HGのCPU-buffer経路はiQ-R専用であり、iQ-Fには定義しない。iQ-Fで採用するのは実在確認できた `U1\G...` のG系ユニットバッファアクセスのみ。
- direct最大点数は word 960点成功/961点`C052`、bit 3584点成功/3585点`C051`。iQ-Fのdirect bitだけ3584点上限を使う。
- random境界は read 192点成功/193点`C054`、word write 160点成功/161点`C054`、bit write 188点成功/189点`C053`。write境界は現在値をそのまま書き戻すsame-values方式で確認し、意図的な値変更は行っていない。
- `Z` は `Z0..Z19`、`R` は `R0..R32767`、ロングカウンタは `LC0..LC63`、`LZ` は `LZ0/LZ1` が今回のFX5UCで使用可。各上限+1は `C056`。
- `LCN10:D` / `LCN63:D`、`LCC10:BIT`、`LZ0:D` / `LZ1:D` は write/read/restore成功。`LCS` は状態読出し対象。`LZ` は16-bit directではなく32-bit経路（named/random dword）をpositive pathにする。
- `ZR`, `RD`, `V`, `LT`, `LST` は今回のFX5UCでは `C05C` のためpositive pathにしない。

## 修正結果（2026-07-03）

- F-1: dotnet / python / rust の標準拡張デバイス指定を、実機で成功したマニュアル順レイアウトへ修正済み。
- F-2: rust の要求データ長を `checked_add` + `u16::try_from` で検証し、65,535バイト超過時は送信前にエラー返却するよう修正済み。巨大ラベルpayloadで長さフィールドがu16切り捨てされず、フレーム未送信で止まることをテストで確認済み。
- F-3: dotnet / python / cpp の拡張ランダム/拡張モニタ登録を、008x 上限 96点 / weighted 960 / 94点で事前検証するよう修正済み。
- F-4: dotnet / python / rust / cpp / node-red の direct bit 一括読出/書込を、iQ-Fプロファイルのみ上限3584点で事前検証するよう修正済み。その他プロファイルの7168点、ワード単位960点は維持。
- F-5: dotnet / python / rust の4E応答処理を、要求serialと一致しないD4応答を破棄して次応答を待つよう修正済み。pythonは同期/非同期の両方で対応。異常系は模擬サーバで「不一致serial→一致serial」を再現し、正しい応答だけ採用することを確認済み。
- F-6: python 同期クライアントのUDPを接続済みソケットへ変更し、正規PLC以外の送信元から届いたUDPデータグラムを応答として採用しないよう修正済み。別ポートの偽送信元を使う模擬UDPテストで確認済み。
- F-8: dotnet / python / rust / cpp / node-red で、異常応答データ部9バイトを `network/station/module_io/multidrop/command/subcommand` として構造化するよう修正済み。FX5U上限超過時の実測エラー情報 `00 FF FF 03 00 01 04 01 00` を使う回帰テストで確認済み。
- Node-RED版: 現行公開APIに008x拡張ランダム/拡張デバイス指定ビルダーがないため、今回のF-1/F-3修正対象外。
- テスト: dotnet full test、python full pytest（F-6/F-8追加テスト含む）、rust cargo test（F-2/F-8追加テスト含む）、cpp `run_ci.bat`、node-red `npm test` は成功。
