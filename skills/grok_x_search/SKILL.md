# Grok Build で X を探す（手順書・実行は Grok レーン）

出典: @ojigineko_tips の SKILL CARD No.001「Xポスト読み取りスキル」（本人が 2026-11-15 にチーム共有を指示）。

## 位置づけ（最初に読むこと）

- 役割分担は「探す＝Grok Build」「読む＝FxTwitter」。URL が分かっているポストを読むのは `fxtwitter_post_reader` スキル（全員の道具）。話題やキーワードからポストを**探す**のは Grok Build（xAI の CLI `grok` の x_search）。
- **このスキルは手順書である。** Grok Build のログイン・`grok` CLI のインストール・有料プラン枠の消費は、X レーンの DRI である **Grok 本人の担当**。Muse・Codex・Dots・Pickle はこのスキルを読んで手順を理解するが、ログイン実行やインストールは行わない。検索が要るときは Grok へ team-outbox で依頼し、返ってきた URL を `fxtwitter_post_reader` で読み直す。
- 検索はユーザーの Grok サブスクの枠を消費する。範囲を絞って低頻度に使う。

## 導入とログイン（Grok 本人の環境での手順）

- CLI が無い場合は x.ai の公式インストーラで `grok` を入れる（導入先は `~/.grok/bin/grok`。中身を確認し、ホーム配下にだけ書くことを確かめてから実行）。
- ログイン状態は `grok models` で確認する。"You are logged in with grok.com" と出れば OK。
- 未ログインなら `grok login --device-code` を実行し、URL とコードをユーザに渡して本人の端末で承認してもらう。パスワード等をチャットで受け取ったり `~/.grok/auth.json` を読んだりしない。
  - 注: Anicca チームの運用では承認・資格情報は本人へ回さず Grok 自身のレーンで完結させる（チーム恒常ルールが優先）。

## 検索のしかた

- 実行形式: `grok --no-subagents --max-turns 6 --reasoning-effort low -p "<指示文>"`
- 指示文には必ず入れる:
  - x_search だけを使う
  - 話題・名前・期間を具体的に
  - 件数を絞る
  - 日付・アカウント・要約・URL を返す
  - 無ければ「見つからない」と答える

## つなぎ方（検索→読み取りの検証）

1. Grok Build で話題を1つ検索し、ポストの URL を1件取る。
2. その URL を FxTwitter（`fxtwittergo`）で読み直す。
3. 検索結果の要約と原文が一致すれば「探す→読む」がつながっている。

## 検証済みテスト（2026-11-15、読み取り側）

- 読み取り側（FxTwitter）の実走テストは `fxtwitter_post_reader` スキルに記録済み（テストポスト https://x.com/ojigineko_tips/status/2120622660833173617 、期待値と全項目一致）。
- Grok Build へのログインと検索の実走は Grok 本人のレーンのため、このスキル作成時点では未実施（手順書として保存のみ）。
