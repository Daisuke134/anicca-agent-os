## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第5ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。/tmp の空き容量は約490MBある。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第6ラウンド委任文（Maestro 用 Release ビルドの失敗の切り分け可能化）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `2b2591c21`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。

## 実測された事実（一次証拠）

- PR のビルドジョブ（run 43587914085、HEAD `2b2591c21`）: **Build and unit tests (unsigned) が success**。アプリ本体＋単体テストは Debug 構成・`generic/platform=iOS` では通る。
- Maestro run 43589033225（同じ HEAD、`run_maestro=true` で dispatch）: **failure**。失敗ステップは "Build, run the actual journey, and record"。artifact は **0件**（証拠保存ステップは `if: always()` だが証拠フォルダが空だった）。
- ジョブログの時系列: スクリプト開始 11:14:56 UTC、シミュレータ起動監視 11:15:42–11:18:57、その後ログ無出力のまま 11:36:22 に `exit code 65` で終了。無出力区間は `xcodebuild build` の出力がファイルへリダイレクトされている区間と一致する。
- スクリプト `apps/mobile/anicca-ios/scripts/run-soft-paywall-maestro.sh` の構造: `set -euo pipefail` の下で、Release 構成・特定シミュレータ宛ての `xcodebuild build`（出力は `$RUNNER_TEMP/anicca-soft-paywall-build.log` へ）を実行し、その後に証拠ファイル（maestro-version.txt 等）を書き始める。つまり**ビルドが失敗するとスクリプトは証拠を一切残さずに死に、ビルドログも artifact 化されない**。第3ラウンドでビルドジョブ側に直した「全文ログ保存」と同じ欠落が Maestro 側に残っている。
- なお、このスクリプトは修正前の Phase 1 コード（基点側）では完走実績がある（元の Phase 1 動画 run 43565027974）。PR ジョブ（Debug・generic）は通り、Maestro 側（Release・特定シミュレータ）だけが落ちる、というのが現在の切り分けである。Release 固有の失敗か、宛先固有の失敗か、ビルドフェーズのスクリプトかは、ログが無いため未確定である。断定しないこと。

## このラウンドの作業

1. **証拠の保存（必須）**: `run-soft-paywall-maestro.sh` を直し、ビルド失敗時にも `anicca-soft-paywall-build.log` が証拠フォルダ（`$evidence_dir`）へコピーされ、artifact として残るようにする。あわせて、失敗時にはエラー行（`error:` を含む行）と末尾をジョブのコンソールにも出す（第3ラウンドでビルドジョブに入れた形と同じ考え方）。ビルド設定（Release・宛先・scheme）やフローの意味は変えない。終了コードは元の xcodebuild のものを維持する。
2. **静的監査（可能な範囲）**: 第1〜第5ラウンドの差分について、Release 構成でのみ失敗しうる要因を監査する。観点の例: `#if DEBUG` / `#if !DEBUG` で囲まれた参照の不整合、Release でのみ有効なビルドフェーズやスクリプト、whole-module 最適化で表面化する重複・循環、特定シミュレータ宛てでのみ含まれるターゲット。確定できる不備があれば直し、無ければ「確定できるものは無かった」と候補の一覧とともに FIX-NOTES に書く。推測でコードを変えない。
3. **FIX-NOTES 第6ラウンド節**: 上記の実測事実（run 番号・artifact 0件・exit 65・時系列・Debug と Release の構造差）、スクリプトの変更内容、静的監査の結果を書く。根本原因は「未確定」と明記する（次回の Maestro run の artifact で確定させる段取りであること）。
4. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）を実行し、結果を第6ラウンド節に書く。シェルスクリプトの構文検査（`bash -n`）も行う。

## 必須条件

- 変更対象は原則 `run-soft-paywall-maestro.sh` と `PHASE1-UIUX-FIX-NOTES.md`、および静的監査で確定した不備の修正だけ。他に触れたら理由を FIX-NOTES に書く。
- XCTest / Maestro の実行結果を捏造しない（VM に Xcode は無い）。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
