# 機種プロファイル制限 実装作業指示書（リポジトリ別）

- 作成日: 2026-07-03
- 前提資料（すべて本リポジトリ内）:
  - 設計指示書: `instructions/slmp_profile_restriction_instructions_20260703.md`（state定義・ガード仕様・思想はこちらが正。本書は作業手順のみ）
  - 正準データ: `capability/slmp_builtin_ethernet_profiles.json`
  - 根拠: `evidence/` 一式
- 本書の使い方: 各実装リポジトリで作業セッション（Claude Code等）を開き、**共通仕様（§1〜§4）＋該当リポジトリの節（§5）**を読ませて実行させる。1リポジトリ=1ブランチ=1PR。

## 0. 好材料（実装前に知っておくこと）

全5ライブラリに `SlmpPlcProfile`（正準ID `melsec:iq-r` 等9種のparse/文字列化）と、SD由来のデバイス範囲カタログが**既に実装済み**である。本作業で新設するのは次の3点だけ:

1. **capabilityテーブル**（正準JSONの写し、言語内静的データ）
2. **featureガード層**（高レベルAPI入口、フレーム構築前）
3. **上限表の差し替え**（既存のシリーズ分岐上限を「プロファイル×コマンド×サブコマンド」キーの表参照に置換。監査F-3/F-4の恒久修正を兼ねる）

## 1. 共通仕様（全リポジトリ）

### 1.1 テーブルの持ち方

- 正準JSONを**ビルド時/コミット時に言語内静的テーブルへ写す**（実行時にJSONファイルへ依存しない）。手写し可・生成可、いずれも§3の整合テストで一致を担保する。
- テーブルのコメント/docに出典を残す: `plc-comm-slmp-profiles <タグ名> capability/slmp_builtin_ethernet_profiles.json`
- 取り込んだ正準JSONそのものも `tests/fixtures/`（相当）へコピーし、整合テストの比較元にする。

### 1.2 ガード動作（設計指示書§3・§4の要約）

- state별動作: `blocked`/`unverified` → strict時は送信前エラー。`supported`/`config-dependent`/`delegated` → ガードなし。
- strictフラグ: 正準名 `strict_profile`、**既定 true**。クライアント生成オプション。falseで state 由来ガードのみ無効。
- **limits は strict に関係なく常時強制**。
- **write_policy（S read-only 等）も strict に関係なく常時強制**（既存実装の挙動を維持）。
- raw送信API（raw_command相当）はガード対象外のまま残す。
- `melsec:qcpu` / `melsec:qnu` は正準JSONの capability profile として扱う。QnUDV同等の state / limits（source は policy）で feature ガードと上限を適用する。
- プロファイル未指定のクライアントは完全に現行動作（後方互換、opt-in導入）。

### 1.3 エラー仕様

- 新設エラー型（言語慣習名で可、例: `SlmpProfileFeatureError`）。**PLC終了コードエラーと同型にしない**。
- メッセージ必須要素: プロファイルID / featureキー / state / 根拠（実測終了コードがあれば。例: `block(0406/1406) returned C059 on live QnUDV`）/ 解除方法（`strict_profile=false`）。
- 上限超過はプロファイル導入前から存在する既存のバリデーションエラー型を維持してよい（新設不要）。メッセージにプロファイルIDと採用上限を含めること。

### 1.4 やらないこと

- フレームビルダー・コーデックには触らない（本作業はビルダーより手前の層のみ）。
- rust の要求長 u16 ラップ修正（監査F-2）は**別コミット/別PR**。混ぜない。
- 自動リトライ・自動フォールバックは追加しない（既存方針どおりPLC終了コードは素通し）。
- デバイス範囲・ファミリ存在判定には触らない（既存の範囲取得関数の担当）。

## 2. 作業手順テンプレート（各リポジトリ共通）

1. ブランチ作成: `feature/plc-profile-capability-guard`
2. 正準JSONを取り込み、capabilityテーブルを実装（§1.1）
3. featureガード層を高レベルAPI入口に実装（§1.2）
4. 既存上限バリデータをプロファイル上限表参照に置換（該当言語の節を参照）
5. エラー型追加（§1.3）
6. テスト実装（§3）
7. 既存テスト全通過を確認（回帰ゼロ）
8. ドキュメント: README/CHANGELOG にプロファイルオプションと strict_profile を追記。python は `internal_docs/maintainer/manual_implementation_differences.md` にも1項追加
9. PR作成。本文に取り込んだ profiles リポジトリのタグ名を明記

## 3. テスト仕様（全リポジトリ同一ケース）

期待値はすべて取り込んだ正準JSONから導出し、テストコードに数値をベタ書きしない。

| # | テスト | 内容 |
|---|--------|------|
| T1 | ガード | 各プロファイル×`blocked`/`unverified` feature: 高レベルAPIが送信前エラー。モックトランスポートに**1バイトも流れない**こと |
| T2 | strict解除 | 同ケースで `strict_profile=false` なら送信されること（モックで送信バイトを確認） |
| T3 | 通過 | `supported`/`config-dependent` feature: ガードされず、プロファイル規定のフレーム種別+サブコマンドでフレーム構築されること（例: iq-f→3E+0000系、mx-r→4E+0002系） |
| T4 | 上限 | 各limitsエントリ: max点で通過、max+1点で送信前エラー。strict解除でもmax+1はエラー |
| T5 | write_policy | read-onlyファミリへのwriteが送信前拒否（全プロファイル: S） |
| T6 | 整合 | 実装内テーブル全エントリ == fixtureの正準JSON（state/上限値/サブコマンド組の完全一致） |
| T7 | 後方互換 | プロファイル未指定クライアントで既存代表APIの挙動が変わらないこと |

## 4. 展開順

`dotnet → python → rust → node-red → cpp-minimal`。dotnetのPRで公開API名・エラーメッセージ文面を確定し、以降は言語慣習への写像のみ（判断の再発明をしない）。

---

## 5. リポジトリ別の作業内容

### 5.1 plc-comm-slmp-dotnet（起点・リファレンス実装）

既存資産: `SlmpEnums.cs`（SlmpPlcProfile）、`SlmpPlcProfiles.cs`（parse/既定値解決 SlmpPlcProfileDefaults）、`SlmpConnectionOptions.cs`、`SlmpDeviceRanges.cs`、`SlmpClient.cs` 内の点数上限バリデータ群・`DirectBitPointLimit` 等の定数。

| 作業 | 内容 |
|------|------|
| テーブル | 新規 `SlmpCapabilityProfiles.cs`: プロファイル→feature state / limits / write_policy の静的表 |
| オプション | `SlmpConnectionOptions` に `StrictProfile`（bool, 既定true）を追加。プロファイル指定プロパティは既存の仕組みを使う |
| ガード | `SlmpClient` の高レベルAPI（block/monitor/typename/拡張系/ロング系の各入口）に capability 照会を挿入 |
| 上限 | 既存のシリーズ分岐上限（`DirectBitPointLimit=7168` 固定等）を capability 表参照へ。**iq-f の bit 3584 と 0082/0083系 random 96/94/80 がここで直る** |
| エラー | `SlmpProfileFeatureException` 新設 |
| 注意 | `bin/` 配下の生成物は触らない。Legacy/iQ-Rモード（CompatibilityMode）とプロファイルの優先関係は既存 `SlmpPlcProfileDefaults` の解決を踏襲 |

### 5.2 plc-comm-slmp-python

既存資産: `slmp/core.py`（SlmpPlcProfile enum・点数上限群）、`slmp/device_ranges.py`、`slmp/errors.py`、`slmp/client.py` / `async_client.py`。

| 作業 | 内容 |
|------|------|
| テーブル | 新規 `slmp/capability_profiles.py`（dict定数。dotnetの表と同一内容） |
| オプション | クライアントコンストラクタに `strict_profile: bool = True` |
| ガード | `client.py` / `async_client.py` 両方の高レベルAPI入口（同期/非同期で判定関数は共有） |
| 上限 | `core.py` の上限検証群をプロファイル表参照へ |
| エラー | `errors.py` に `SlmpProfileFeatureError` |
| 注意 | `raw_command` はガード対象外を維持。`manual_implementation_differences.md` に本機構の項を追加 |

### 5.3 plc-comm-slmp-rust

既存資産: `model.rs`（PlcProfile enum + defaults解決）、`client_rules.rs`（シリーズキー上限）、`device_ranges.rs`、`route_validation.rs`。

| 作業 | 内容 |
|------|------|
| テーブル | 新規 `capability_profiles.rs`（const表 or `phf`不使用のmatch関数。既存 client_rules.rs の流儀に合わせる） |
| オプション | クライアントビルダー/optionsに `strict_profile`（既定true） |
| ガード | 高レベルAPI入口。エラーは既存 error enum に `ProfileFeature` variant 追加 |
| 上限 | `client_rules.rs` のシリーズキー上限をプロファイルキーへ置換 |
| 注意 | **F-2（build_request_frame の u16 ラップ）はこのPRに含めない**。route_validation.rs と役割が重複しないよう、featureガードは1箇所に集約 |

### 5.4 node-red-contrib-plc-comm-slmp

既存資産: `lib/slmp/core.js` / `client.js` / `high-level.js`（plc_profile 対応済み）、serialキー管理のtransport。

| 作業 | 内容 |
|------|------|
| テーブル | `lib/slmp/capability-profiles.js`。**適用featureは type_name / direct / random / block / monitor / long_device_path / lz_32bit_path のみ**（008x拡張系・HGのAPIが存在しないため ext_module_access / ext_link_direct / hg_cpu_buffer は対象外。READMEに適用外キーを明記） |
| オプション | ノード設定UIにプロファイル選択（既存があれば流用）と `strict profile` チェックボックス（既定ON） |
| ガード | `high-level.js` の入口。エラーは `node.error` + msg でフロー側が捕捉できる形 |
| 上限 | 既存上限チェックをプロファイル表参照へ |

### 5.5 plc-comm-slmp-cpp-minimal

既存資産: `slmp_minimal.h/.cpp`（plc_profile対応・4Eシリアル照合あり）、`slmp_high_level.h/.cpp`。

| 作業 | 内容 |
|------|------|
| テーブル | 静的配列 + 検索関数（ヘッダオンリーの流儀を崩さない）。実装済み機能に該当するキーのみ（direct / random / ext_link_direct / ext_module_access ほか、実装済みAPIと突き合わせて決定し、適用外キーをREADMEに明記） |
| オプション | クライアント構造体/設定に `strict_profile`（既定true） |
| ガード | `slmp_high_level` の入口。エラーコード方式なら専用エラーコード追加 |
| 上限 | 既存上限チェックをプロファイル表参照へ |
| 注意 | minimal の思想（依存追加なし）を崩さない |

---

## 6. 受入基準（Definition of Done、各リポジトリ）

- [ ] T1〜T7 全通過（node-red/cppは適用featureの範囲で）
- [ ] 既存テスト全通過（回帰ゼロ）
- [ ] `melsec:qnudv` + strict で block API がフレーム構築前にエラーになり、エラーメッセージに `C059` と解除方法が含まれる（スポット確認の代表ケース）
- [ ] `melsec:iq-f` で direct bit 3585点が送信前エラー（F-4恒久修正の確認）
- [ ] プロファイル未指定の既存コードがそのまま動く
- [ ] README/CHANGELOG 更新、取り込みタグ名の明記

## 7. 各リポジトリのセッション起動プロンプト例

> D:\APP\plc-comm-slmp-profiles\instructions\slmp_profile_implementation_steps_20260703.md の §1〜§4 と §5.X（このリポジトリの節）、および同リポジトリの設計指示書 slmp_profile_restriction_instructions_20260703.md を読んで、このリポジトリに機種プロファイル制限を実装してください。正準データは D:\APP\plc-comm-slmp-profiles\capability\slmp_builtin_ethernet_profiles.json（タグ vX.Y.Z）です。ブランチ feature/plc-profile-capability-guard で作業し、受入基準（§6）を満たしたらPRを作成してください。

（§5.X は対象リポジトリの節番号に置き換える）
