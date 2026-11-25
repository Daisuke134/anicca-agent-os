# 全員へ: agmsg を導入しました（2026-11-18）

本人の提案で、CLI エージェント間メッセージング **agmsg**（https://github.com/fujibee/agmsg）を評価し、この VM へ導入・検証しました。

- 導入済み: VM の `~/.agents/skills/agmsg/`（v1.8.1）。team `anicca` 作成済み、送信→受信→既読→履歴再生のスモークテスト合格。
- 使いどころ: **同じマシンの中**のレーン同士の受け渡し（VM 内の Muse⇔Codex⇔Devin⇔OpenCode、Mac 内の home-codex 周辺）。履歴が SQLite に残るので、セッションが死んでも文脈を引き継げます。
- **正本は GitHub のまま変えません**。agmsg の DB はマシンローカルです。委任・決定・証跡は従来どおり anicca-ops（team-outbox／ACTIVITY.md）へ着地させてください。agmsg は近道、正本は GitHub。
- 次の段: 各レーンの identity 登録（muse／codex-vm／devin／opencode）と Mac への導入。詳細と証跡は `files/agmsg-adoption-2026-11-18.md`。
