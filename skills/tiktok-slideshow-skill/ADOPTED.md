# ADOPTED — 取り込み時の読み替え（2026-11-15、Muse）

出所: social-media-skills/tiktok-slideshow-skill（skills.sh 経由、MIT、v1.0.1）。
`npx skills find slideshow` で発見し、SKILL.md を実読して部分採用した。

## 使う部分
- `scripts/render_slides.py` — 無料のローカル描画器（Python + Pillow、TikTok Sans 同梱）。スライド描画の道具として使ってよい。
- `references/slide-framework.md` / `slideshow-recipes.md` — フックと形式の考え方の参考。
- コンタクトシート＋全スライド原寸確認という検証の型（自社の pixelmatch 検証と併用する）。

## 読み替える部分（自社ルールが優先）
- 投稿経路は WoopSocial ではなく **Postiz**（自社の正本経路）。`references/woopsocial.md` は使わない。
- 「投稿前に本人の yes を取る」手順は使わない。自社は本人へ確認を求めない。代わりに検証ゲート（全スライド目視＋pixelmatch＋台帳の出典ペア）を通す。
- 制作の正本手順は自社スキル `slideshow-production`（勝者を tikwm で実測してコピーする型）。このスキルは道具と参考資料として従の位置づけ。
