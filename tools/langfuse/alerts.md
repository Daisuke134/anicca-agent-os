# アラート定義（Phase 0、Cloud Hobby 上限 = 2件）

出典設計: `~/workspace/research_notes/agent-observability-2026-11-06/report.md` §5.4。
作成場所: Langfuse Cloud の対象プロジェクト（distribution）→ Settings → Alerts。
通知先は Webhook または Slack。Webhook の受け口 URL は秘密値として金庫にのみ置く（このファイルには書かない）。

## アラート 1: ループ無データ（run-distribution-max）

- 目的: 「止まっている」を朝に人間が見つける状態を二度と作らない（§5.4）。
- 対象: トレース名 `run-distribution-max`（プロジェクト distribution）。
- 条件: 直近 4時間（ループ間隔 3時間 ＋ 猶予 1時間）のウィンドウでトレース件数 = 0。
- 通知先: Webhook（修復側が受け取る受け口）。
- 備考: Langfuse の無データ検知は公式機能（調査レポート §5.4）。UI 上の正確な設定項目名は作成時に実画面で確認する。

## アラート 2: 到達失敗（artifact_delivered < 1）

- 目的: 実物が出ていない実行をその場で直す対象として修復側へ回す（§5.4）。
- 対象: スコア `artifact_delivered`、トレース名 `run-distribution-max`。
- 条件: 直近 3時間のウィンドウで `artifact_delivered` の平均 < 1（= 実物が未達の実行が1件でもある）。
- 通知先: アラート 1 と同じ Webhook。
- 発火試験: アカウント開通後、`python3 ~/workspace/tools/langfuse/langfuse_emit.py test` の
  失敗ケース（存在しない URL の artifact）で `artifact_delivered=0` のトレースを送り、
  通知が受け口に届くことを確認する。

## Hobby 枠の制約で Phase 0 に入れないもの（Phase 1 で追加）

- エラー率（ERROR observation 比率の閾値超過）
- コスト超過（ループ別・日次コスト）
- 売上ゼロの継続（日次集計ジョブ側の判定＋Webhook）
