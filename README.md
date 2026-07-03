# plc-comm-slmp-profiles

SLMP通信ライブラリ群（dotnet / python / rust / node-red / cpp-minimal）が共通で参照する**機種プロファイルの正準データ**を一元管理するリポジトリ。ここにある JSON が唯一の正であり、各実装リポジトリはタグを固定して取り込む。

## 構成

| パス | 内容 |
|------|------|
| `capability/slmp_builtin_ethernet_profiles.json` | 機種別の機能可否プロファイル（7プロファイル）。**内蔵Ethernetポート**で使える機能のみを基準としたポリシー定義。フレーム種別/サブコマンド組・コマンド可否（5値state）・点数上限・書込ポリシー・経路振り分け |
| `device-ranges/slmp_device_range_rules.json` | デバイス範囲取得の正準規則（9プロファイル）。SDレジスタブロックの読出し位置とファミリ別解決規則（fixed / word / dword / clipped / unsupported / undefined）、および**実行時散策（runtime_probes）**の仕様 |
| `instructions/slmp_profile_restriction_instructions_20260703.md` | 機能可否プロファイルを5ライブラリへ横展開する実装指示書（ガード仕様・strict_profile・適合テスト） |
| `evidence/` | 2026-07-03 実機検証記録（R120P / iQ-L / iQ-F / LCPU / QnUDV）、QnUDVフレーム別プローブ結果、マニュアル照合監査レポート |

## 2つのJSONの役割分担

- **capability** は「その機種の内蔵Ethernetで何を送ってよいか」（実行時に問い合わせようがないポリシー）。デバイスの存在有無・範囲は持たない。
- **device-ranges** は「デバイスの存在有無・範囲をどうやって実機から取得するか」の規則。SDに範囲が書き込まれないPLC側問題（Q系の一部デバイス）に対する散策アルゴリズム仕様を含む。

## プロファイルID

正準IDは各実装の `SlmpPlcProfile` 相当と一致させる:
`melsec:iq-r` / `melsec:iq-l` / `melsec:mx-r` / `melsec:mx-f` / `melsec:iq-f` / `melsec:qcpu` / `melsec:lcpu` / `melsec:qnu` / `melsec:qnudv`

（capability は実機検証またはユーザー判断があった7種のみ。qcpu / qnu は device-ranges のみに存在し、capability は未定義＝プロファイル指定不可）

## 編集ルール

1. **根拠のないエントリを追加しない。** 変更には必ず `source`（live / manual / spec / policy / inferred）と evidence または note を付け、実測なら `evidence/` に記録を追加する。
2. 実測との食い違いを見つけたら、正準JSONを黙って直さず、まず evidence に記録してから変更する。
3. 変更はコミット＋**タグ発行**で公開する。各実装リポジトリは参照タグを明記して追従し、適合テストで一致を担保する。
4. スキーマを変える場合は `schema_version` を上げ、全実装の追従が完了するまで旧タグを維持する。

## 経緯

2026-07-03 のマニュアル照合監査（`evidence/review_slmp_spec_audit_20260703.md`）と5機種の実機検証を起点に作成。検証は内蔵Ethernetポート・TCP 1025 で実施。拡張Ethernetユニット構成は対象外（ポリシー、詳細は instructions を参照）。
