# agmsg 導入評価（2026-11-18）

本人の提案（2026-11-18）を受けて、CLI エージェント間メッセージング **agmsg**（https://github.com/fujibee/agmsg）を評価し、この VM へ導入してスモークテストまで完了した記録。正本はこのファイル。チーム周知は `team-outbox/muse/to-all-2026-11-18-agmsg.md`。

## agmsg とは何か

- Claude Code・Codex・Gemini CLI・Copilot CLI・Antigravity・OpenCode・Devin・Grok Build 等の **CLI エージェント同士が直接メッセージを送り合う**ための道具。人間がコピペの運び屋をしなくて済む。
- 実体は bash スクリプト群＋共有 **SQLite**（WAL モード）。デーモンなし・ネットワークなし・MCP ではない。任意の常駐サービス agmsgd（beta）は自分で選んだときだけ入る。
- メッセージ履歴は DB に残り続け、`history.sh` で新しいセッションへ再生できる＝**セッション境界でのコンテクスト喪失への対策**が主目的に合う。
- 概念: team（名前つきグループ）／agent（team 内の identity。1プロジェクトで複数ロールは `actas`）／delivery mode（agmsgd・monitor・turn・both・off）。
- 導入先は `~/.agents/skills/agmsg/`。バージョンは **1.8.1**。

## 導入記録（この VM）

前提（実測）: bash 5.2.21 ✓／sqlite3 3.45.1 ✓／node v24.22.1 ✓／python3 3.12.3 ✓。

ソース取得の経路（本日 VM の書き込み障害 EPERM のため通常経路が全滅し、最終経路で成功）:

| 経路 | 結果 |
|---|---|
| `git clone` | ✗ テンプレート複写で EPERM |
| `git clone --template=<空>` | ✗ HEAD symref 書き込みで EPERM |
| `gh api .../tarball` | ✗ 0 バイトで着地 |
| `curl` codeload tarball | ✗ write error (23) |
| **GitHub API で blob を個別取得し再構成** | ✓ **296 ファイル全件、サイズ照合一致** |

- 再構成先: `~/workspace/tools/agmsg`（取得スクリプトは `~/workspace/tools/fetch_agmsg.py`、冪等・リトライつき）。
- 不足していた `CHANGELOG.md` と `plugins/README.md` を追加取得してから `./install.sh --cmd agmsg` を実行。初回は CHANGELOG 不足で途中終了し操作ロックが残ったため、インストーラ提示のリカバリ（`install.sh --cmd agmsg --recover <operation_id>`）で完走。
- 導入の副作用（インストーラの正規動作）: `~/.agents/skills/agmsg/` 本体、Claude Code 用コマンド `~/.claude/commands/`、OpenCode／Hermes／Grok／Gemini 用スキル配置、`~/.codex/config.toml` の変更（変更前に `~/.codex/config.toml.bak` へバックアップ）、既定 config と DB の作成（`~/.agmsg/agmsg/db/messages.db`）。
- agmsgd は有効化していない（install の既定どおり）。

## スモークテスト（合格）

`~/.agents/skills/agmsg/scripts/` の CLI で実施（プロジェクト: `~/workspace/tools/agmsg-smoke`）:

```
$ join.sh anicca smoke-alice claude-code <project>
Created team: anicca
Joined team anicca as smoke-alice
$ join.sh anicca smoke-bob codex <project>
Joined team anicca as smoke-bob
$ send.sh anicca smoke-alice smoke-bob "smoke test: hello from alice (claude-code) to bob (codex) — agmsg evaluation 2026-11-18"
Sent to smoke-bob in team anicca
$ inbox.sh anicca smoke-bob
1 new message(s):
  [2026-11-18T06:12:41Z] smoke-alice: smoke test: hello from alice (claude-code) to bob (codex) — agmsg evaluation 2026-11-18
$ inbox.sh anicca smoke-bob        # 2回目
No new messages.
$ history.sh anicca
  ○ [2026-11-18T06:12:41Z] smoke-alice → smoke-bob: smoke test: hello from alice ...
```

- 送信→相手視点での受信→既読化→履歴再生まで全て実測で動作。
- スモーク用2名は退会済み。team `anicca` と履歴1件は DB に保持されている（永続性の実証を兼ねる）。
- 未検証の範囲: 実セッションへの push 配信（monitor／agmsgd）は、稼働中エージェントの再起動と identity 登録が要るため本回は未検証。シェル層のメッセージング基盤のみ合格。

## 適合性評価

### 本当に効くところ
- **同一マシン内の CLI レーン間**。VM 上の Muse（Muse）⇔ Codex exec レーン群・Devin CLI・OpenCode・Command Code は同じ SQLite を共有でき、委任・レビュー依頼・完了通知をその場で往復できる。Mac 上の home-codex 周辺も同型。
- **履歴の永続性**。セッションが死んでも DB に残り、新セッションが `history` で文脈を引き継げる。今日の「起動したはずのレーンが無言で死んでいた」型の事故で、引き継ぎの材料がマシン内に残る。

### 置き換えてはいけないもの
- **正本は GitHub（anicca-ops の team-outbox＋ACTIVITY.md）のまま**。当社のエージェントは VM と Mac mini に分散しており、agmsg の DB はマシンローカル。マシンが死ねばローカル履歴も死ぬ。会社全体の記録・委任・証跡は GitHub に着地させる現行ルールを一切変えない。
- Slack は従来どおり鏡のみ。
- agmsg は「同じマシンの隣のレーンへの近道」であり、GitHub は「会社全体の正本」。役割が違う。

### クロスマシン同期について
- agmsg には remote sync がある（自己ホストのリファレンスサーバー＋PostgreSQL、平文または age 暗号化の E2E）。ただし Docker Compose 前提の追加インフラであり、この VM には Docker が無い。**今回は導入しない**。クロスマシンの即時メッセージングが本当に必要になった時点で、サーバーホストを決めて別途判断する。

## ロールアウト提案

1. **Phase 1（VM、即時）**: team 名は `anicca` で統一。実レーンの identity を各プロジェクトで登録する: `muse`（claude-code）／`codex-vm`（codex）／`devin`（devin）／`opencode`（opencode）。delivery は各レーンの対応に応じ turn から始め、monitor は実セッションで検証してから広げる。同マシン内の受け渡し（例: Muse→Codex のレビュー依頼）は agmsg で速くし、**記録は従来どおり GitHub team-outbox にも着地**させる。
2. **Phase 2（Mac mini）**: Mac は git・ネットワークが健全なので通常経路（clone＋install.sh）で導入し、team `anicca`、identity は `home-codex` 等。VM と Mac の DB は別フロアとして扱い、マシンを跨ぐ話は GitHub が正本のまま。
3. **Phase 3（任意・要判断）**: remote sync サーバーの設置可否。やるなら暗号化経路（age）前提、ホストは常時稼働の1台に固定。
4. 命名規約: team = `anicca` 固定。agent 名はレーン名そのもの（muse／codex-vm／home-codex／devin／opencode／grok／dots）。1レーン1マシン1 identity を原則とする。
