# Measurement kit（計測ツール基盤）

2026-11-05 構築。本人指示「未検証は整備対象。勝者の計測ツールを調べ、無料のものを使い始め、全指標を継続計測できる形にする」への実装。

## 動くもの（この VM から API キーなしで実行可能）

| スクリプト | 計測対象 | 経路 | 実行 |
|---|---|---|---|
| `aso_rank.py` | App Store キーワード順位（Anicca 6755129214 と I am 874656917、US 10語・JP 7語） | Apple iTunes Search API（公式・無料・認証不要）。順位は検索結果の relevance 順＝無料経路の標準プロキシ。人気度スコアそのものは Apple Search Ads / Astro(Mac専用・有料)でのみ取得可 | `python3 ~/workspace/tools/measurement/aso_rank.py` |
| `serp_bing.py` | Bing 検索順位（対象7語 × aniccaai.com / thevisionboard.app / happierhuman.com） | Bing HTML を直接取得し redirect を復号。**Google 順位ではない**（Bing インデックス）。キー不要で VM から定期実行できる唯一の SERP 経路 | `python3 ~/workspace/tools/measurement/serp_bing.py` |
| `geo_pollinations.py` | GEO（AI 回答での Anicca 推奨・引用。集合は baseline8＋expanded100＋core16＋intents24＝148件、分母の定義は anicca-ops `files/geo-scale-10000-spec-2026-11-14.md`、2026-11-19 の intents24 追加は `files/geo-intents24-2026-11-19.md`） | Pollinations text API（無料・キー不要・キー無し LLM 回答、openai-fast）。プロンプト集合とブランド照合は citeshine-audit の config／方法と同一。**ChatGPT/Perplexity の Web 回答ではない＝代理標本**（台帳行に engine=pollinations、engine_kind=keyless-llm-api と明記） | 15分ループは `python3 ~/workspace/tools/measurement/geo_pollinations.py --set baseline8`（時系列用8件のみ）。拡大集合は専用 cron `anicca-geo-expanded-loop`（6時間ごと）が `--set expanded100 --offset/--limit` のチャンク並列＋ `--set core16` ＋ `--set intents24` で全走する（2026-11-15 分母修理。正本: anicca-ops `files/geo-denominator-fix-2026-11-15.md`。intents24 は 2026-11-19 追加） |
| `rankings_snapshot.py` | 台帳の最新行から rankings スナップショットを生成 | measurement-ledger.jsonl を一次入力として `hidden_files/rankings-latest.json` を再生成。/open ダッシュボード構築がこのオブジェクトを data.json の `rankings` セクションへ取り込むための確定入力 | `python3 ~/workspace/tools/measurement/rankings_snapshot.py` |

継続実行: cron `anicca-measurement-loop`（15分間隔）が上記4スクリプト＋Google スナップショット（検索ツール、type=seo_google）を回し、台帳と rankings-latest.json を更新し続ける。GEO の拡大集合だけは `anicca-geo-expanded-loop`（6時間間隔）が担当し、rankings_snapshot.py の geo は集合ごとに prompt_id 単位の最新行で集計する（分母148。2026-11-19 に intents24 を追加して124から拡大。中核枠は59。2026-11-15 修理前は最新 ts の一括バッチのみで、分母が構造的に8に固定されていた）。

両スクリプトとも結果を `~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-ledger.jsonl` へ JSONL 追記する（type=aso / seo_bing）。継続計測は「同じスクリプトを定期実行し、前回行と diff を取る」形。

## インストール済み（実行には追加の鍵・経路が必要）

- **citeshine-audit**（OSS・MIT、GEO引用計測）: `~/.local/share/citeshine-audit/` に clone 済み。Anicca 用 config = `configs/anicca.json`（プロンプト8件 EN6/JP2、競合10ブランド）作成済み。実行には `OPENAI_API_KEY`（Responses API + web search）または `PERPLEXITY_API_KEY` が必要（VM の env には未設定）。鍵が入れば: `cd ~/.local/share/citeshine-audit && python3 -m citeshine_audit configs/anicca.json -n 3`
- **geo-optimizer-skill**（GeoReady の OSS CLI、AI引用されやすさ監査）: venv `~/.local/share/measurement-venv/` に install 済み（`geo` コマンド）。ただしこの VM では DNS/プロキシの判定で全 URL が "non-public address" とされ監査実行不可（example.com でも同一エラー＝環境側の制限）。代替は Web 版 https://geoready.dev/（無料・無アカウント、ブラウザ操作が必要）。

## 既存の実証済み経路（流用）

- **GSC**: Google Search Console は共有ブラウザプロファイルの既存セッションで読み取り可（2026-11-04 実証、SEO ループに配線済み）。API 化（サービスアカウント）は Google Cloud 側の作成＋プロパティ追加が前提で未実施。
- **ASC API**: `~/workspace/tools/asc`（Rork の asc CLI）＋ `~/.config/asc/` の鍵で VM から直接読み取り可（2026-11-05 に apps list で実証、24アプリ）。売上・評価・順位以外のアプリ指標はこちら。
- **Google 順位スナップショット**: エージェントの検索ツールで対象クエリを引き、返却結果内の順位を記録する手続き（2026-11-05 ベースラインで使用）。自動化の本命は SerpBear（OSS）＋無料 SERP API キー（ScrapingRobot 無料 5,000回/月 or Serper.dev 無料 2,500回）。鍵の取得は Web フォーム登録＋メール確認が必要（エージェント所有メール anicca-agent@inkboxmail.com を使用し、鍵は 1Password「Agents」へ。値そのものはファイルに書かない）。

## ベースライン

`~/workspace/goals/anicca-revenue-growth-as-life-manager/hidden_files/measurement-baseline-2026-11-05.md`
