# 機種プロファイル制限 実装GOAL定義書

- 作成日: 2026-07-03
- 形式: GOAL形式（手順ではなく、達成すべき最終状態と検証可能な受入条件で定義する。実現手段は各セッションの裁量）
- 正準データ: `plc-comm-slmp-profiles` タグ **v1.0.0** の `capability/slmp_builtin_ethernet_profiles.json`
- 補足資料: 設計指示書 `slmp_profile_restriction_instructions_20260703.md`（state定義・思想）、作業指示書 `slmp_profile_implementation_steps_20260703.md`（参考手順。GOALと矛盾する場合はGOALが優先）

---

## GOAL-0: 共通（全リポジトリの不変条件）

**達成状態**: 各ライブラリが正準JSONと同一内容の capability テーブルを内蔵し、プロファイル指定時は内蔵Ethernetポートで使えない機能が送信前に検出される。プロファイル未指定の既存利用者には一切の挙動変化がない。

**受入条件**:

- [ ] 実装内テーブルの全エントリ（feature state / 点数上限 / サブコマンド組 / write_policy）が、取り込んだ正準JSON（fixtureとして同梱）と機械比較で完全一致する
- [ ] `strict_profile`（既定 true）指定時、state が `blocked` / `unverified` の feature に対応する高レベルAPIは、モックトランスポートに1バイトも送信せずに専用エラーで失敗する
- [ ] 同ケースで `strict_profile=false` にすると送信される
- [ ] `supported` / `config-dependent` / `delegated` の feature はガードされない
- [ ] 点数上限は strict に関係なく常時強制される（max点は通過、max+1点は送信前エラー）
- [ ] write_policy（read-only ファミリへの書込拒否）は strict に関係なく常時強制される
- [ ] 専用エラーにはプロファイルID・featureキー・state・実測根拠（終了コードがある場合）・解除方法が含まれ、PLC終了コードエラーとは型で区別できる
- [ ] raw送信API（raw_command 相当）はガードを受けない
- [ ] `melsec:qcpu` / `melsec:qnu`（capability未定義）はfeatureガード非適用で現行動作を維持する
- [ ] プロファイル未指定のクライアントは既存動作と完全一致（既存テスト全通過、回帰ゼロ）
- [ ] フレームビルダー・コーデック・デバイス範囲取得関数に変更がない

**非スコープ**: 拡張Ethernetユニット対応 / UDP経路の判断 / 自動リトライ / rust F-2(u16ラップ)修正（別PR）

---

## GOAL-1: plc-comm-slmp-dotnet（起点・リファレンス実装）

**達成状態**: `SlmpClient` が `SlmpPlcProfile` と `SlmpConnectionOptions.StrictProfile`（既定 true）に基づき GOAL-0 を満たし、既存のシリーズ分岐上限定数（`DirectBitPointLimit=7168` 固定等）が capability テーブル参照に置き換わっている。ここで確定した公開API名・エラーメッセージ文面が他言語の写像元になる。

**受入条件**: GOAL-0 全項目に加えて

- [ ] `SlmpProfileFeatureException`（名称はdotnet慣習で最終決定可）が公開され、XMLドキュメントコメントを持つ
- [ ] `melsec:qnudv` + strict で block 系APIが送信前に失敗し、メッセージに `C059` と解除方法が含まれる
- [ ] `melsec:iq-f` で direct bit 3585点が送信前エラーになる（監査F-4の恒久修正）
- [ ] `melsec:iq-r` で random read 97点が送信前エラーになる（監査F-3の恒久修正）
- [ ] README / CHANGELOG に profile + StrictProfile の説明と取込タグ名（v1.0.0）が記載されている

---

## GOAL-2: plc-comm-slmp-python

**達成状態**: 同期・非同期クライアント双方が `strict_profile: bool = True` コンストラクタ引数と既存 `SlmpPlcProfile` に基づき GOAL-0 を満たし、`core.py` の上限検証群が capability テーブル参照に置き換わっている。判定ロジックは同期/非同期で共有される。

**受入条件**: GOAL-0 全項目に加えて

- [ ] `errors.py` に `SlmpProfileFeatureError` が追加され、dotnetで確定したメッセージ要素と同内容
- [ ] dotnet と同じ代表ケース（qnudv block / iq-f bit 3585 / iq-r random 97）が同じ結果になる
- [ ] `internal_docs/maintainer/manual_implementation_differences.md` に本機構の項（manual expectation / implemented behavior / reason / status）が追加されている

---

## GOAL-3: plc-comm-slmp-rust

**達成状態**: クライアントが `strict_profile`（既定 true）と既存 `PlcProfile` に基づき GOAL-0 を満たし、`client_rules.rs` のシリーズキー上限がプロファイルキーの capability テーブルに置き換わっている。featureガードは1箇所に集約され、`route_validation.rs` と役割が重複しない。

**受入条件**: GOAL-0 全項目に加えて

- [ ] 既存 error enum に `ProfileFeature` 系 variant が追加され、dotnet確定のメッセージ要素を持つ
- [ ] dotnet と同じ代表3ケースが同じ結果になる
- [ ] `build_request_frame` の u16 ラップ（F-2）に触れていない（別PRであることをPR本文に明記）

---

## GOAL-4: node-red-contrib-plc-comm-slmp

**達成状態**: ノード設定のプロファイル選択と `strict profile` チェックボックス（既定ON）に基づき、**適用可能な feature（type_name / direct / random / block / monitor / long_device_path / lz_32bit_path）の範囲で** GOAL-0 を満たす。008x拡張系・HGはAPI自体が存在しないため適用外。

**受入条件**: GOAL-0 の該当項目（適用featureの範囲）に加えて

- [ ] ガードエラーがフロー側で捕捉可能（`node.error` + msg）で、メッセージ要素はdotnet確定と同内容
- [ ] README に適用feature一覧と**適用外キー（ext_module_access / ext_link_direct / hg_cpu_buffer）**が明記されている
- [ ] qnudv block / iq-f bit 3585 の代表ケースが同じ結果になる

---

## GOAL-5: plc-comm-slmp-cpp-minimal

**達成状態**: クライアント設定の `strict_profile`（既定 true）に基づき、**実装済み高レベルAPIに対応する feature の範囲で** GOAL-0 を満たす。依存追加なし・minimal の思想を維持し、テーブルは静的配列＋検索関数で実現されている。

**受入条件**: GOAL-0 の該当項目（適用featureの範囲）に加えて

- [ ] 適用した featureキーと適用外キーが README に明記されている
- [ ] エラーはライブラリ既存のエラー通知方式（エラーコード等）に統合され、プロファイルID・feature・解除方法が判別できる
- [ ] 外部依存が増えていない

---

## 進め方

- 展開順: GOAL-1 → 2 → 3 → 4 → 5（GOAL-1 で公開API名・メッセージ文面を確定し、以降は写像）
- 1 GOAL = 1ブランチ（`feature/plc-profile-capability-guard`）= 1PR。PR本文に取込タグ（v1.0.0）と、達成したGOALの受入条件チェックリストを貼る

## セッション起動プロンプト（コピペ用）

> D:\APP\plc-comm-slmp-profiles\instructions\slmp_profile_implementation_goals_20260703.md を読み、GOAL-0 と GOAL-N（このリポジトリの節）を達成してください。正準データは D:\APP\plc-comm-slmp-profiles\capability\slmp_builtin_ethernet_profiles.json（タグ v1.0.0）です。ブランチ feature/plc-profile-capability-guard で作業し、受入条件を全て満たしたことをチェックリストで示してから PR を作成してください。

（GOAL-N は対象リポジトリの番号に置き換える）
