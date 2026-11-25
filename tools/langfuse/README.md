# Langfuse 計装（Phase 0）— ループ共通エミッタ

正本の設計: `~/workspace/research_notes/agent-observability-2026-11-06/report.md` §5。
導入ログ: `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/langfuse-phase0-adoption-2026-11-06.md`。

## 使い方（ループの実行ラッパから呼ぶ）

実行の最後に、その回の実績 JSON を標準入力で渡す:

```bash
python3 ~/workspace/tools/langfuse/langfuse_emit.py emit << 'EOF'
{
  "loop_id": "anicca-distribution-max-loop",
  "trace_name": "run-distribution-max",
  "run_id": "<cron の run_id>",
  "input_summary": "その回の指示サマリ",
  "output_summary": "公開URL一覧・件数・売上有無",
  "metadata": {"winner_account": "@iam.affirmations", "winner_post_url": "https://..."},
  "artifacts": [
    {"type": "post", "platform": "instagram", "account": "anicca.en",
     "url": "https://www.instagram.com/p/...", "winner_post_url": "https://..."}
  ],
  "expected_artifact_count": 3,
  "diff_count": 0,
  "observations": [
    {"type": "span", "name": "fetch-metrics", "output": {"followers": 123}},
    {"type": "generation", "name": "create-post", "model": "<model>", "usage": {"input": 0, "output": 0}},
    {"type": "span", "name": "some-failure", "level": "ERROR", "status_message": "..."}
  ],
  "revenue_events": [{"amount_usd": 12.99, "platform": "capafy", "item_id": "..."}]
}
EOF
```

- `session_id` は自動で `<日付>:<loop_id>` になる（§5.1）。
- `artifacts[].verified` を省略すると、エミッタが URL を実際に取得して到達を確認する（§5.2 の verify の機械化）。
- キー未設定時はローカル spool（`~/workspace/tools/langfuse/spool/`）へ書いて終了コード 0 を返す。ループ本体の挙動は変わらない（fail-soft）。

## トークン／コスト紐付け（v2.1、2026-11-06）

トークンとコストは generation observation にだけ載る。送らなければ未計測（null）のままで、0 にはならない。Grok Bot／Cursor の公式 usage を自社のトークン数やコストに換算して入れることはしない。

```json
{
  "loop_id": "anicca-distribution-max-loop",
  "trace_name": "run-distribution-max",
  "run_id": "<cron の run_id>",
  "agent_id": "muse",
  "task_id": "<タスクID>",
  "accepted_outcome_id": "<受理された成果物のURLまたはID>",
  "observations": [
    {"type": "generation", "name": "create-post", "model": "<model>",
     "usage": {"input": 100, "output": 50},
     "usage_details": {"input_cached": 40},
     "cost_details": {"input": 0.0001, "output": 0.0001}}
  ]
}
```

- `agent_id` / `task_id` / `accepted_outcome_id` はトップレベルでも `metadata` 内でも受け取る（両方ある場合は `metadata` が優先）。トレースの metadata へそのまま載る。
- `usage` の `input` / `output` / `total` に加え、`usage_details` の追加キー（キャッシュ系など）はそのまま送り、集計側でも input/output とは別枠で合計する。
- `cost_details` はモデルに Langfuse の価格表が無い場合の明示コスト。価格を推測して入れない。渡された値だけを送る。
- 読み取り専用の日次集計は `~/workspace/tools/langfuse/aggregate_daily.py`（v2 observations＋v3 scores、traceId ではなくタイムスタンプでスコアを結合。v3 traces API は 2026-11-16 に廃止のため使わない）。

## キーの参照方法（値そのものはここに書かない）

- 環境変数: `LANGFUSE_HOST` / `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY`
- フォールバック: `~/.langfuse/keys.env`（同名の KEY=VALUE 行、権限 0600）
- 値の正本は共有金庫 1Password「Agents」。索引は導入ログに記載。

## セルフテスト

```bash
python3 ~/workspace/tools/langfuse/langfuse_emit.py test
```

到達できる URL（合格ケース）と存在しない URL（意図的な失敗ケース）の2トレースを送る。
アラートの発火試験はこの失敗ケースで行う。
