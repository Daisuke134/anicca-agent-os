# Larry（TikTok スライドショー・スキル）使い方メモ

取得日: 2026-11-03 / 取得元: GitHub（いずれも MIT ライセンス）

## Larry とは
- インディー開発者 Oliver Henry（@oliverhenry / olliewazza）が自分の OpenClaw エージェントに付けた名前。その TikTok スライドショー・マーケティング手法がスキル **`tiktok-app-marketing`（通称 Larry スキル / Larry Marketing）** として公開されている。
- 実績（スキル側の自己申告）: X 記事 700 万表示、TikTok 100 万+再生、アプリ MRR $670/月。
- 公式配布は LarryBrain（https://larrybrain.com）。マーケットプレイス自体は $29.99/月だが、**Larry Marketing スキル自体は無料枠**（解約後も無料スキルは残ると明記）。製品版 LarryLoop は $39/月〜（https://www.larryloop.com/）。
- 手法の中身: 競合リサーチ → 勝ちフックの型で 6 枚スライド生成 → 1 枚目にフック文字オーバーレイ → TikTok 下書きへ投稿（音楽は API で付けられないため下書き止まりが正規フロー）→ 分析 → 次バッチのフックへ反映、の閉ループ。

## 取得した2バリアント
### 1. larry-postiz/（Postiz 版・自社スタックに一致）
- 出典: https://github.com/uerzer/nebula-skills（`larry-skill/` + `projects/larry-skill/scripts/` を統合）
- 必要: Node.js 18+、`npm install canvas`（node-canvas）、Postiz アカウント＋API（Standard $29/月〜、自社は接続済み）、画像生成キー（OpenAI `gpt-image-1.5` 推奨 ※1 ではなく 1.5。約 $0.50/6枚投稿）、任意で RevenueCat。
- スクリプト: generate 系は SKILL.md の手順ベース（このミラーには generate-slides.js が無い）。add-text-overlay.js / post-to-tiktok.js / check-analytics.js / daily-report.js / competitor-research.js / onboarding.js あり。

### 2. larry-marketing-upload-post/（Upload-Post 版・最も完全なパッケージ）
- 出典: https://github.com/Majayly/upload-post-skills（`skills/larry-marketing/`、LICENSE: MIT / TONVI TECH SL）
- 必要: Node.js、`GEMINI_API_KEY`（画像生成）、`UPLOAD_POST_API_KEY`（TikTok＋IG 同時投稿。自社は Upload-Post 未登録 → 使うなら新規登録が必要。今回は登録していない）
- スクリプト完備: generate-slides.js / add-text-overlay.js / post-to-platforms.js / check-analytics.js / daily-report.js / competitor-research.js / onboarding.js、references/ に slide-structure.md（6枚構成の型）、feedback-loop.md 等。

## 自社の「勝者ダウンロード→差分ゼロコピー→投稿」工程への組み込み
- **そのまま使える部品**: `add-text-overlay.js`（node-canvas で文字のサイズ・位置・スタイルを実測調整済みの型）。勝者スライドをダウンロードした後の「文字載せ」再現に使うのが本命。
- **型としてコピーする部分**: references/slide-structure.md の 6 枚構成、フック生成→計測→次バッチ反映の feedback loop、競合リサーチ手順（competitor-research.md）。
- **注意**: Larry 本来の方式は「勝者の実ファイルを複製」ではなく「競合リサーチに基づき AI 画像を新規生成」。自社の差分ゼロ・コピー基準では、生成部は使わず、オーバーレイと構成・計測ループだけを道具として使うのが適合する。
- **投稿の制約**: TikTok は下書き投稿（SELF_ONLY）が前提で、公開と音楽付けは別工程。Postiz 経由は自社の既存経路と同一。

## 未実施事項
- LarryBrain / Upload-Post / LarryLoop への登録・契約はしていない（Larry Marketing スキル本体は GitHub の MIT 版で取得済みのため不要）。
- 投稿は一切していない。
