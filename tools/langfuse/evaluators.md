# コード評価器の定義（Phase 0）

出典設計: `~/workspace/research_notes/agent-observability-2026-11-06/report.md` §5.3。
Phase 0 では評価器を「自社側の決定的コード（`langfuse_emit.py` の `evaluate()`）が判定し、
Scores API（ingestion の score-create）でトレースへ付ける」形で実装する。
LLM ジャッジは導入しない（§5.3 の順序どおり、コード評価器が先）。

| eval名 | 型 | 定義（二値） | 実装状態 |
|---|---|---|---|
| `artifact_delivered` | コード、0/1 | 期待された実物（投稿URL等）が存在し、エミッタの再取得で実在が取れたら 1。artifacts が空、未達が1件でもある、期待件数に届かない、のいずれかで 0 | 実装済み（URL 再取得による到達確認つき） |
| `winner_named` | コード、0/1 | metadata に勝者アカウント＋原典URLがある、または全 artifacts に winner_post_url がある | 実装済み |
| `copy_diff_zero` | コード、0/1 ＋ `diff_count` 数値 | diff_count が実測され 0 のときだけ 1。未計測は 0 | 実装済み |
| `cost_recorded` | コード、0/1 | トレース内の全 generation にモデル名と usage（input/output）がある。generation が無い回は付けない | 実装済み |
| `revenue_attributed` | コード、0/1 | 売上イベントがある回に、全イベントへ item_id の紐づけがある | 実装済み |
| `artifact_count` / `artifact_verified_count` | 数値 | 到達率の分母・分子（アラートと集計用） | 実装済み |
| `tokens_to_money_daily` | 数値（日次集計） | ループ別・日次で 売上USD ÷ コストUSD | Phase 0 の範囲外（日次集計ジョブ側で後日） |
| `post_quality_vs_winner` | LLMジャッジ | 勝者との一致をルーブリックで判定 | 後導入（人手ラベル検証が前提。Phase 0 では作らない） |

補助: Langfuse 側にも同名のスコア定義が自動で作られる（score-create の初回送信時）。
Langfuse ネイティブのコード評価器への移行は、セルフホスト（Phase 1）以降の検討事項として残す。
