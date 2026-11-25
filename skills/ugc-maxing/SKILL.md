---
name: ugc-maxing
description: UGC Maxing — Anicca の配信の柱。エンジンは「ユーザーがアニッチャの UI/UX のスクリーンショットをシェアすること」。言葉が強く動機づけられ、面白くて、シェアしたくなるから回る。製品側のスクショ導線設計、SNS 側の宣言・唱和・保存型、受け皿（ハッシュタグ／メンション）の収集と再投稿増幅、主指標＝スクショシェア発生数の計測までを1つのループで回す。UGC、ユーザー生成コンテンツ、スクショシェア、宣言コメント、再投稿の話が出たら使う。
metadata:
  version: 1.0.0
---

# UGC Maxing（Anicca 正本スキル）

創業者の確定（2026-11-22）: UGC Maxing は配信の柱。中核仕様は同日 17:31 の明言——エンジンは「ユーザーがアニッチャの UI/UX のスクリーンショットをシェアすること」。画面の言葉が強く動機づけられて、面白くて、シェアしたくなるから回る。

## 前提条件（これが無いと回らない）

言葉の個人化と面白さが前提。新バージョンのモデル生成の言葉（Manager がその人専用に選び、笑える言葉も含む）がホームに届いていない間、スクショシェアのエンジンは本格的には回らない。その間は SNS 側の参加型（宣言・唱和・保存）で受け皿と習慣だけを先に作り、製品導線はモデル生成の本番有効化と同時に有効化する。段階を飛ばして「スクショしてください」とだけ言っても回らない。

## 採用した道具とスキル（全て無料・オーガニックのみ）

背骨と運用は既製品をそのまま使う（車輪の再発明をしない）:

- **ugc-strategy**（arnabbagxd/brand-building-skills、skills.sh、Price: 0 USD）— 全体設計の背骨。顧客に作らせる仕組み、ブランドハッシュタグ、コンテスト mechanics、権利管理（legal rights）。
  https://skills.sh/arnabbagxd/brand-building-skills/ugc-strategy
- **gingiris-ugc-matrix**（gingiris-1031/gingiris-skills、skills.sh、Price: 0 USD、単独で有料ツール不要と明記）— 収集・検収・公開の分離、再利用権、自然流量と有料流量を分けて測る帰因ルール。
  https://skills.sh/gingiris-1031/gingiris-skills/gingiris-ugc-matrix
- **referrals**（coreyhaines31/marketingskills、skills.sh）— 共有動線の設計（'made with' バッジ、review campaigns）。
  https://skills.sh/coreyhaines31/marketingskills/referrals
- **challenge-funnel**（manojbajaj95/claude-gtm-plugin、skills.sh、Price: 0 USD）— 複数日チャレンジ（例: 7日間宣言チャレンジ）の設計。
  https://skills.sh/manojbajaj95/claude-gtm-plugin/challenge-funnel
- 社内スキル: **winner_copy_by_measurement**（コピーの作法。キーワードコメントは返信で実物を届けられる場合だけ含める）、**slideshow-production**（パック制作）、**social_post_lane_check**（投稿先レーン確認）。
- 計測: **tikwm**（`~/workspace/tools/tikwm/tikwm`、TikTok の再生・いいね・コメント・共有・保存。写真投稿の再生数も取れる）。
- 将来の収集基盤候補: **Staticman**（MIT、https://github.com/eduardoboucas/staticman）— aniccaai.com の体験談収集を有料 SaaS なしで自前化する時に使う。今は導入しない。

却下（有料・対象外）: fal.ai 系 UGC 生成スキル（全面禁止＋課金生成 API）、muapi／Veo／Seedance 等の AI 生成「UGC 風広告」工場、Okendo／Loox／Yotpo／Judge.me 等の UGC 収集 SaaS、クリエイター有料発注プラットフォーム全般、UGC 広告台本スキル（paid 前提）。金のかかる成長施策は検討自体が禁止。

## エンジンの設計

### 1. 製品側: スクショしたくなる瞬間と、スクショ自体が広告になるデザイン

- シェア導線は「言葉が表示された直後」に置く。特に、個人化された言葉・笑える言葉がホームに出た瞬間がスクショしたくなる瞬間。
- スクショの中に必ず入る要素: (a) アニッチャの名前／ロゴ、(b) その人の言葉そのもの、(c) 日付、(d) 見た人が欲しくなる要素——「つらい日・笑いたい日に開くアプリ」という約束が伝わる一文。スクショが単体で広告として成立すること。
- 共有文には受け皿（ハッシュタグ＋メンション）を自動で含める。
- 実装は製品 Issue 側（Daisuke134/anicca、DRI は Codex レーン）。前提はモデル生成の言葉の本番有効化。

### 2. 受け皿

- ハッシュタグ: **#アニッチャ**（日本語面）／ **#AniccaWords**（英語面）
- メンション: IG **@anicca.company**、TikTok **@anicca.jp**
- 受け皿の存在は公式プロフィールと固定投稿で常時明示する。「あなたの今日の言葉をスクショして投稿したら、公式が紹介します」。

### 3. SNS 側: 今すぐ回る参加型（勝者型の正本は viral-patterns 台帳）

台帳: `~/workspace/goals/anicca-revenue-growth-as-life-manager/files/anicca-distribution/viral-patterns-2026-10-24.md`

主軸（摩擦が低く、計測でき、返信経路に依存しないもの）:
- **A13 型**（@affirmsoftly、勝者実測 12,720 likes・8,107 comments）: 画像自体が宣言の台本。「3回読んで、コメントにそのまま打つ」＋「自分に送れ」。
- **A20 型**（@affirmsoftly、コメント率 48〜65%）: キャプションは「Send this to yourself」1行のみ。共有・保存がエンジン。
- **A14／A19 型**（@soothify.app）: 日付イベントをフックに「Save this and repeat」「Share it with someone」。
- **A15／A18 型**（@iam.affirmations）: 「ロック画面に設定して保存」。
- **唱和型**（@ican.tracks 等）: 投稿本文＝唱える一文。視聴者の仕事は感想ではなく、その文をコメントで自分の言葉として宣言すること。

主軸にしない: キーワードコメント→DM ファネル（A12／A16）。理由は自社実測——posts-ledger で自社投稿のコメントは全件 0（41件、2026-11-17〜18 計測）。返信で実物を届けられる経路が安定するまでは従属扱い（winner_copy_by_measurement の規定）。

新規の柱: **スクショ招待型**。公式投稿で「あなたの今日の言葉」をスクショして受け皿つきで投稿するよう招待し、公式が拾って紹介する。製品導線が無くても、現在のホーム画面のスクショから始められる。

### 4. 増幅ループ（毎日、DRI = Muse）

ジョブ: `anicca-ugc-maxing-loop`（daily）。手順:

1. 受け皿チェック: ハッシュタグ／メンションのユーザー投稿を収集する（IG／TikTok）。スクショシェア発生数を数える（主指標）。
2. 計測: 自社投稿の宣言コメント数・保存数・共有数を tikwm／コネクタで実測し、`hidden_files/ugc-ledger.md` に1行追加する。数字は実測のみ、出典と日付つき。
3. 再投稿・増幅: 優秀なユーザー投稿と宣言コメントを再投稿パック化し、`hidden_files/distribution-material-stock-2026-11-10.md` の UGC 節へ READY で追加する（公開は既存の面別 pub ループが消費する。UGC ループ自身は公開しない＝単一書き手を壊さない）。再投稿は投稿者に許可を取り、クレジットを明記する（ugc-strategy の権利管理に従う）。
4. 参加型パックの補充: UGC 節の READY が3未満なら、勝者型から新パックを補充する（文面は quote_dedup_check のゲート通過が条件）。
5. 製品側の学びを製品 Issue へフィードバック: どの言葉がスクショされたか、どの言葉が唱和されたかを記録し、Manager の言葉選びの材料にする（behavior data は売り物であり資産）。

### 5. 計測の物差し

- **主指標: スクショシェア発生数／日**（受け皿で検出したユーザー投稿数）
- 副指標: 宣言コメント数、保存数、共有数、再投稿パック数、UGC 経由のフォロー増
- ベースライン（2026-11-22 時点の実測）: 自社投稿のコメント 0／41件、スクショシェア発生数 0。ここからの伸びだけを見る。累計でごまかさない。

## 絶対ルールとの整合

- 無料・オーガニックのみ。有料発注・有料 SaaS・課金生成 API は検討しない。
- 投稿は勝者型の 100% コピー（文面の逐語コピーは除く）、公開前に原典と並べて検証する。
- ユーザー投稿の再投稿は許可＋クレジット必須。許可が取れないものは再投稿しない。
- 数字は実測のみ。測れていないものは「未計測」と書く。
