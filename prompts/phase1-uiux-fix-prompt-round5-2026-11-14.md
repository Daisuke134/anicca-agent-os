## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第4ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。/tmp の空き容量は回復済み（約490MB）。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第5ラウンド委任文（テストターゲットの既存破損の修正）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `50d61c59a`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。

## 実測された事実（一次証拠）

GitHub Actions run 43586731563（HEAD `50d61c59a`、PR #9352）の artifact（build-output.log / test-output.log）を統合側が実読した:

- アプリ本体のビルド: **エラー0件**（build-output.log 1902行、`error:` は0件）。第3ラウンドの根本原因修正と第4ラウンドの参照修正が効いている。
- 単体テストのビルド: エラー3件、全て `apps/mobile/anicca-ios/aniccaiosTests/OnboardingV2Tests.swift` の129・139・144行目。`AnalyticsEvent.paywallTimelineViewed` / `.paywallDrawerViewed` / `.paywallDrawerConverted` が存在しない、という内容。
- この3つのイベントは、ブランチの基点 `2bac2ac6c` 時点の `AnalyticsManager.swift` にも存在しない（統合側が grep で確認済み）。つまりテストターゲットの破損は第1ラウンド以前からある既存の問題で、今回の修正差分が壊したものではない。3つのイベントは旧ペイウォール（タイムライン／ドロワー形式）のもので、その UI は監査の修正で置き換え済みである。

## このラウンドの作業（これだけ）

1. `OnboardingV2Tests.swift` の当該3テスト（`test_analytics_paywallTimelineViewed_exists`、`test_analytics_paywallDrawerViewed_exists`、`test_analytics_paywallDrawerConverted_exists`）を削除する。削除する理由は「対象のイベントと UI が現行コードに存在せず、基点時点でも存在しなかった」ため。**列挙型へ死んだイベントを足し戻してテストを通すことはしない**（実在しない画面の計測イベントを復活させるのは誤り）。
2. 近傍の現行イベントのテスト（paywallPrimerViewed、paywallPlanSelectionViewed 等）は触らない。
3. `PHASE1-UIUX-FIX-NOTES.md` に「第5ラウンド」節を追加し、次を書く: run 43586731563 の実測（アプリ本体はエラー0件、テストは上記3件）、基点 `2bac2ac6c` でもイベントが存在しなかった事実、削除の判断と理由、他に触っていないこと。
4. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）を実行し、結果を第5ラウンド節に書く。

## 必須条件

- 変更は上記2ファイル（テスト1件＋FIX-NOTES）だけに抑える。他のファイルに触れたら理由を FIX-NOTES に書く。
- XCTest の実行結果を捏造しない（VM に Xcode は無い。判定は push 後の Actions で行う）。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
