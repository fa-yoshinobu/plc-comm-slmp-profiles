# SLMP機種プロファイル制限 実装指示書

- 作成日: 2026-07-03
- 対象: plc-comm-slmp-dotnet / plc-comm-slmp-python / plc-comm-slmp-rust / node-red-contrib-plc-comm-slmp / plc-comm-slmp-cpp-minimal
- 正準データ: **`plc-comm-slmp-profiles` リポジトリの `capability/slmp_builtin_ethernet_profiles.json`**（以下「正準JSON」）
- 関連データ: 同リポジトリ `device-ranges/slmp_device_range_rules.json`（SD由来デバイス範囲取得の正準規則。本指示書の対象外だが同じ運用ルールで管理する）

## 1. 目的と思想

機種（プロファイル）ごとに、**内蔵Ethernetポートで使える機能だけ**を既定で許可する制限機構を5ライブラリへ横展開する。

- 拡張Ethernetユニット（QJ71E71 / RJ71EN71 等）を使うと使える機能は増えるが、仕様が複雑になるため**対象外**とする。これは物理的制約ではなく**ポリシー**である。したがって制限は既定ON・解除可能とする（§4）。
- 可否の根拠は 2026-07-03 の実機検証記録（§8）または明示的なユーザー方針にある。**根拠のない可否を正準JSONに追加しない**こと。追加時は必ず `source` と `evidence`/`note` を伴う。
- **デバイスの存在有無・範囲はプロファイルで扱わない。** SD読出しによる既存のデバイス範囲取得関数が実行時に判定する（ファミリ不存在 — 例: FX5 の ZR/RD/V/LT/LST — も範囲取得関数の担当）。プロファイルが持つのは実行時に問い合わせようがない通信仕様ポリシーのみ:
  1. フレーム種別（3E/4E）とサブコマンド組
  2. コマンド可否（type_name / block / monitor / 拡張アクセス経路 / ロング系経路 等）
  3. 点数上限（コマンド×サブコマンド別）
  4. 書込ポリシー（S read-only 等）
  5. ロング系・LZ の経路振り分けルール

## 2. プロファイルID（9種）

| ID | フレーム | サブコマンド組 | 実機検証 |
|----|---------|----------------|----------|
| `melsec:iq-r` | 4E | 0002/0003, 0082/0083 | R120PCPU 実測 |
| `melsec:iq-l` | 4E | 0002/0003, 0082/0083 | L16HCPU 実測 |
| `melsec:mx-r` | 4E | 0002/0003, 0082/0083 | なし（iQ-R同等扱い、HGのみblocked確定） |
| `melsec:mx-f` | 4E | 0002/0003, 0082/0083 | なし（iQ-R同等扱い、HGのみblocked確定） |
| `melsec:iq-f` | 3E | 0000/0001, 0080/0081 | FX5UC / FX5U 実測 |
| `melsec:qcpu` | 3E | 0000/0001, 0080/0081 | なし（QnUDV同等扱い、source は policy） |
| `melsec:lcpu` | 3E | 0000/0001, 0080/0081 | LCPU 実測 |
| `melsec:qnu` | 3E | 0000/0001, 0080/0081 | なし（QnUDV同等扱い、source は policy） |
| `melsec:qnudv` | 3E | 0000/0001, 0080/0081 | QnUDV 実測 |

- `melsec:iq-l` と `melsec:lcpu` は**別プロファイル**。混同しないこと。
- MXR/MXF はマルチCPU構成が組めないため **HG CPUバッファ経路のみ blocked で確定**。それ以外は iQ-R 同等（2026-07-03 ユーザー判断）。実機入手後に実測へ差し替える。
- QCPU/QnU は実機未確認だが、2026-07-03 のユーザー判断により QnUDV と同等の capability profile として扱う。根拠種別は `policy` とし、実機入手後に差し替える。

## 3. 状態（state）の定義と動作

正準JSONの各 feature は次の5状態のいずれかを持つ。**判定ロジックを各言語で再発明せず、JSONのデータをそのまま取り込むこと**（監査F-1の教訓: 散文指示からの言語別実装は必ずドリフトする）。

| state | 意味 | strict時の動作 | strict解除時 |
|-------|------|----------------|--------------|
| `supported` | 実機で成功確認済み（または同等扱い決定済み） | 通常送信 | 通常送信 |
| `blocked` | 実機で不可確認済み／仕様上不可確定 | **送信前ガードでエラー** | 送信する |
| `config-dependent` | ユニット実在などPLC構成依存 | ガードせず送信、PLC応答に委ねる | 同左 |
| `unverified` | 未検証 | **送信前ガード**（blocked扱い） | 送信する |
| `delegated` | 範囲取得関数など既存機構が判定 | プロファイルは関与しない | 同左 |

feature キー: `type_name` / `direct` / `random` / `block` / `monitor` / `ext_module_access`（U\G） / `ext_link_direct`（J\） / `hg_cpu_buffer` / `long_device_path` / `lz_32bit_path`

## 4. ガード実装仕様

1. **適用位置**: 高レベルAPIの入口、フレーム構築より前。トランスポートに到達させない（QnUDV monitor probe の「send-before guard」と同じ位置づけ）。raw送信API（`raw_command` 等）はガード対象外のまま残す（検証・診断用の逃げ道）。
2. **strictフラグ**: 正準名 `strict_profile`、既定 `true`。クライアント生成時オプションとする（言語慣習に合わせた名前可: dotnet `StrictProfile`, rust `strict_profile`, node-red はノード設定チェックボックス）。`false` で state 由来のガードのみ無効化する。
3. **点数上限（limits）は strict 解除でも常に強制する。** これはポリシーではなくプロトコル上限（実測根拠つき）であるため。既存のシリーズ分岐ハードコードの上限検証は、プロファイルの limits 表参照へ移管する（監査 F-3/F-4 の恒久修正を兼ねる。特に FX5 bit=3584、008x系 random=96/94/960）。
4. **エラー内容**: ガードエラーには最低限次を含める。
   - プロファイルID、featureキー、state
   - 根拠（実測終了コードがあれば併記。例: `blocked on melsec:qnudv: block(0406/1406) returned C059 on live target`）
   - 解除方法の案内（`strict_profile=False` / 拡張Ethernetユニット構成では別途検討、の一言）
   - エラー型は各言語の既存例外階層に追加（例: python `SlmpProfileFeatureError`、dotnet `SlmpProfileFeatureException`）。**PLC終了コードエラーと同じ型にしない**こと（送信前と送信後を呼び出し側が区別できるように)。
5. **書込ポリシー**: `write_policy` に `read-only` とあるファミリへの書込は strict に関係なく送信前に拒否（既存の S read-only 実装と同じ扱い）。
6. **後方互換**: プロファイル未指定のクライアントは現行動作のまま（featureガードなし、上限は現行実装）。プロファイル指定は opt-in で導入し、既存利用者を壊さない。

## 5. 言語別の適用

展開順は従来運用どおり **dotnet 起点 → python → rust → node-red → cpp-minimal**。

| リポジトリ | 適用内容 | 注意 |
|-----------|---------|------|
| dotnet | 全featureキー適用。`SlmpClient` にプロファイルオプション追加、既存 `DirectBitPointLimit=7168` 等の定数をプロファイル表参照に置換 | Legacy/iQ-R モードとプロファイルの整合（プロファイル指定時はフレーム/サブコマンド組もプロファイルが決める） |
| python | 全featureキー適用。`core.py` の limits 群（1059-1092付近）をプロファイル表へ | `manual_implementation_differences.md` に本機構の項を追記 |
| rust | 全featureキー適用。`client_rules.rs` のシリーズキー上限をプロファイルキーへ | F-2（u16ラップ）修正と同時に触る場合は別コミットに分ける |
| node-red | 008x拡張系APIが存在しないため `ext_module_access` / `ext_link_direct` / `hg_cpu_buffer` は**適用対象外**。適用したキーと未適用キーを README に明記 | ノード設定UIにプロファイル選択を追加 |
| cpp-minimal | 実装済み機能（direct/random/link-direct/module-buf 等）に該当するキーのみ適用 | 最小実装の思想を崩さない範囲で。テーブルは静的配列で可 |

正準JSONは共通リポジトリ **`plc-comm-slmp-profiles`** で一元管理する。各実装リポジトリは共通リポジトリの**タグ（バージョン）を固定して**JSONを取り込み（コピーまたはsubmodule）、取り込んだタグ名をコメントで残す。手写し・言語別テーブル生成のいずれの場合も§6の整合テストで正準JSONとの一致を担保する。正準JSONの変更は共通リポジトリへのコミット＋タグ発行で行い、各実装は追従時にタグを更新する。

## 6. 適合テスト

正準JSONを共有テストフィクスチャとして5言語で同一ケースを実行する。

1. **ガードテスト**: 各プロファイル×`blocked`/`unverified` feature — 高レベルAPI呼出しで送信前エラー、モックトランスポートに1バイトも流れないこと。`strict_profile=false` では送信されること。
2. **通過テスト**: `supported`/`config-dependent`/`delegated` feature — ガードされず、プロファイル規定のフレーム種別・サブコマンドでフレームが構築されること（例: `melsec:iq-f` は 3E+0000系、`melsec:mx-r` は 4E+0002系）。
3. **上限テスト**: 各 limits エントリの max（通過）と max+1（送信前エラー）。strict 解除でも max+1 がエラーになること。
4. **書込ポリシーテスト**: read-only ファミリへの write が送信前拒否されること。
5. **整合テスト**: リポジトリ内テーブルと正準JSONの全エントリ一致（JSON同梱ならロード比較、手写しならゴールデン比較）。

期待値はすべて正準JSONから導出し、テストコードに数値をベタ書きしない。

## 7. 未確定事項（要追試 or 承認）

| # | 項目 | 現状の扱い | 確定方法 |
|---|------|-----------|----------|
| 1 | `melsec:iq-r` の `ext_link_direct` | iQ-L判断に合わせ config-dependent（許可）**※推定、要ユーザー承認** | 承認 or リンク機材で追試 |
| 2 | `melsec:iq-l` / `melsec:lcpu` の monitor 登録上限 | 同一サブコマンド組の実測から推定（96 / 192）、`source: inferred` | 実機で 97 / 193 点登録を1回試す |
| 3 | block の最大ブロック数（120等） | 未実測。既存バリデータのマニュアル由来値を維持し、プロファイルには持たない | 必要になったら実測して limits に追加 |
| 4 | `melsec:iq-l` random write の weighted 上限 | 未実測（iq-r は 960 実測） | 実測後に追記 |
| 5 | MXR / MXF 全般 | iQ-R同等扱い（HGのみblocked確定） | 実機入手後に実測へ差し替え |
| 6 | UDP経路 / UDF | 本指示書の対象外（検証記録どおり） | — |

## 8. 根拠資料

- 実機検証記録: `r120p_slmp_live_verify_20260703.md` / `iql_slmp_live_verify_20260703.md` / `iqf_slmp_live_verify_20260703.md` / `lcpu_slmp_live_verify_20260703.md` / `qnudv_slmp_live_verify_20260703.md`（いずれも D:\APP\）
- 意図的差異の記録: `plc-comm-slmp-python/internal_docs/maintainer/manual_implementation_differences.md`（本機構導入後、同ファイルに項を追加すること）
