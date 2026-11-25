## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第6ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。/tmp の空き容量は約490MBある。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第7ラウンド委任文（Release ビルドの actor 隔離エラーの修正）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `2745f3ad3`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。

## 実測された根本原因（一次証拠）

Maestro run 43591626995（HEAD `2745f3ad3`）も failure だったが、第6ラウンドの証拠保存が機能し、artifact `soft-paywall-evidence-2745f3ad3...` に Release ビルドログ（`anicca-soft-paywall-build.log`）が残った。統合側が実読した診断は次の3件だけである:

```
Services/ProfileSyncService.swift:34:9:  error: actor-isolated property 'buffer' cannot be passed 'inout' to implicitly 'async' function call
Services/ProfileSyncService.swift:49:29: error: actor-isolated property 'buffer' cannot be passed 'inout' to implicitly 'async' function call
Services/ProfileSyncService.swift:62:17: error: actor-isolated property 'buffer' cannot be passed 'inout' to implicitly 'async' function call
```

該当箇所は `actor ProfileSyncService` 内の `buffer.enqueue(profile)`（34行）、`buffer.take()`（49行）、`buffer.restoreUnlessNewer(profile)`（62行）で、いずれも actor 隔離プロパティ `buffer`（`ProfileSyncBuffer` 構造体）への mutating 呼び出しである。プロジェクトには `SWIFT_DEFAULT_ACTOR_ISOLATION = MainActor` の設定があり、構造体の mutating メソッドが MainActor 隔離として扱われ、別 actor からの呼び出しが「implicitly async な呼び出しへの inout 渡し」になる、というのが診断の読み筋である（最終的な切り分けは修正後の再ビルドで確定させる。断定として FIX-NOTES に書くときは、この診断文と行番号を一次証拠として引用すること）。

PR ジョブ（Debug・generic/platform=iOS）では成功し、Maestro 側（Release・x86_64 シミュレータ、whole-module 最適化）でのみ表面化した。`ProfileSyncBuffer` は第2ラウンドで「同期中の追加回答が消える」問題への対処として入った形（送信前に pending を消費し、失敗時はより新しい回答が無ければ復元する）であり、その意味論は維持しなければならない。

## このラウンドの作業

1. **修正**: 上記3件の診断が出ない形へ `ProfileSyncService` / `ProfileSyncBuffer` を直す。方針の例（意味論を変えない範囲で最も素直なものを選ぶこと）:
   - `ProfileSyncBuffer` の操作を「新しい値を返す非 mutating 形」にし、actor 側で `buffer = buffer.enqueued(profile)` のように代入で完結させる。
   - または `ProfileSyncBuffer` 自体を隔離の対象から外す明示的な形（メソッドへの `nonisolated` の明示など）にする。ただしデフォルト隔離設定との相互作用を FIX-NOTES に説明すること。
   - `@unchecked Sendable` や診断の握り潰しで通すことはしない。
   意味論の維持条件: (a) ネットワーク await の前に pending を消費する（古い送信の完了で新しい回答が消えない）、(b) 失敗時は「より新しい pending が無い場合だけ」失敗した profile を復元する、(c) 同期中の enqueue は次回分として残る。
2. **同型パターンの棚卸し**: 第1〜第6ラウンドの差分全体で、`actor` の隔離プロパティに対する mutating 呼び出しが他にも無いか grep で確認する。あれば同じ診断が次に表面化する前に直し、無ければ「無かった」と FIX-NOTES に書く。
3. **FIX-NOTES 第7ラウンド節**: run 43591626995 の artifact からの引用（診断3件・ファイル・行）、原因の読み筋、直し方と意味論を維持した根拠、棚卸しの結果を書く。「直った」の確定は次回の Maestro run の結果で行う旨も書く。
4. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）を実行し、結果を第7ラウンド節に書く。

## 必須条件

- 変更対象は原則 `ProfileSyncService.swift`（必要なら `ProfileSyncBuffer` の定義ファイル）、棚卸しで確定した同型箇所、`PHASE1-UIUX-FIX-NOTES.md` だけ。他に触れたら理由を FIX-NOTES に書く。
- XCTest / Maestro の実行結果を捏造しない（VM に Xcode は無い。判定は push 後の Actions で行う）。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
