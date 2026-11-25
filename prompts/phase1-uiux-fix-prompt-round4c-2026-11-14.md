## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第3ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。第3ラウンドの FIX-NOTES にも同じ判断が記録されている。

# Phase 1 UI/UX 修正 第4ラウンド委任文（独立レビュー指摘の修正）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`。現在の作業ツリーには第1〜第3ラウンドの未コミット変更がある。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。

## 背景

第3ラウンドまでの差分に対し、実装を担当していない別のエージェントが独立レビューを行い、確定のコンパイルエラー1件と仕様逸脱1件、minor 7件を指摘した。このラウンドはその修正だけを行う。新機能は追加しない。`PHASE1-UIUX-FIX-NOTES.md` に「第4ラウンド」節を追加し、各指摘への対応（直した／直さない理由）と、過去の記述の訂正を書くこと。

## BLOCKING: B-1 未解決シンボル

`apps/mobile/anicca-ios/aniccaios/Models/SyntheticUser.swift` 33行目が `QuoteProvider.dualCategories` を参照しているが、このシンボルはリポに存在しない。実在するのは `QuoteProvider.swift` 60行目の `goalCategories`（同ファイル66行目で同じ目的に使われている）。

- `dualCategories` → `goalCategories` に直す。
- あわせて、第3ラウンドの Python 検査（native コンパイル検査）が `PaywallPackageSelection.swift` 単体しか見ていなかったために見逃した、という経緯を FIX-NOTES に書き、検査の対象を新規ファイル（少なくとも `SyntheticUser.swift`、`ManagerBenchCase.swift` 等の今回の新規モデル）へ広げられる範囲で広げる。広げられない場合はその理由を書く。
- FIX-NOTES 第3ラウンド A節の「追加の確定コンパイル不備は見つからなかった」と、再レビュー「新規指摘0件」の記述は、事実と異なるため第4ラウンド節で明示的に訂正する（第3ラウンド節自体は書き換えず、訂正として追記する）。

## MAJOR: M-1 名前の質問の復帰（仕様逸脱の解消）

第3ラウンドは「名前は合成ユーザーの条件づけ軸に寄与しない」を理由に journey から名前ステップを外した。しかし一次資料の対応表（anicca-ops `files/onboarding-answer-change-mapping-2026-11-14.md`）は、名前の用途を最初から「条件づけ軸ではなく、最初の介入の呼びかけに使う（端末内表示のみ・分析へ送らない）」と定めており、監査 F-06 も「名前は目標と別のステップで聞く」が仕様である（勝者 I am も独立ステップで聞く）。さらに第3ラウンドが作った reveal（04/08 の `growth_first_for_name`）は `preferredName` を読むのに、削除後は本番経路に書き込み箇所が無く、新規ユーザーが呼びかけ付き介入を受けられない不整合になっている。よって選択肢 (a)「F-06 どおり名前ステップを journey に戻す」で直す:

- journey に `.name`（rawValue 9、不変）を第1ラウンドの順序（welcome → goal → **name** → その後）で戻す。NameStepView が `preferredName` を端末内へ保存する本番経路を復活させる。
- 再開時の変換（resumable で `.name` → `.birthContext` へ読み替える処理）は、journey に `.name` が戻るため不要になる。旧保存値（rawValue 9）で再開したユーザーが名前ステップへ正しく着地するよう直す。
- Maestro 01: 名前入力が表示されないことの assert を外し、第1ラウンドの形（01b-name の撮影つき）へ戻す。
- journey のテスト（`precondition(!journey.contains(.name))` とコメント）は仕様に合わせて直す。
- SyntheticUser の軸↔質問の対応表（FIX-NOTES 第3ラウンド節）へ訂正を追記する: 名前は条件づけ軸ではなく呼びかけ専用（対応表の定義どおり）であり、だからこそ聞く。名前が分析・同期・eval・合成ユーザーの記録へ入らない現状の境界は維持する。
- 画面数は名前込みの数へ更新する（第3ラウンドの「19〜23画面」は名前なしの数）。

## minor のうち eval と選択の正しさに触れるもの（このラウンドで直す）

- **m-1**: `NotificationPermissionStepView.savePermission` が、適応回答が空でも `profile.answers` を `adaptiveAnswers` に代入し `hasAdaptiveAnswers` が立ってしまう。適応回答が実際に存在する場合だけ代入するよう直す（旧版から `.notifications` で再開したユーザーが適応モードに誤って入らないこと）。
- **m-2**: `ManagerBenchCase.closeObservationWindow` が全 source で `app_opened` を false に確定させる。アプリ内 source（daily_home / onboarding 系）の判断点はアプリを開いている最中に作られるため「窓内の復帰なし」は無反応ではない。通知 source 以外では `app_opened` を null のままにする（または同等の区別を実装し、FIX-NOTES の定義表を更新する）。
- **m-4**: DOB 選択時に書く `birth_context = ["date_provided"]` が `OnboardingQuestion.birthContext.optionIDs` の語彙に無い。語彙へ寄せるか、消費側（`ids(for:)`）が誤読しない形に直す。
- **m-7**: `OnboardingFlowView` の `case .name, .birthContext:` の到達不能ケースと screen_id のずれ。M-1 の復帰で到達可能性が変わるため、復帰後の形で正しくなるよう直す。

## minor のうち、このラウンドでは判断を記録するもの

- **m-3**（テスト失敗時にビルドログ artifact が残らない）: 小さい変更で済むなら直す。済まないなら理由を FIX-NOTES に書く。
- **m-5**（SyntheticUser 永続化に schema ゲートが無い）: schemaVersion の読み側チェックを足せるなら足す。足さない場合は理由を書く。
- **m-6**（同期 payload の世代混在）: プライバシー問題ではないため、現状維持ならその判断と理由を書く。

## 必須条件（全ラウンド共通）

- 成果物として `PHASE1-UIUX-FIX-NOTES.md` の第4ラウンド節を必ず差分に含める。各指摘（B-1、M-1、m-1〜m-7）への対応を1件ずつ書く。
- この VM には Swift/Xcode が無い。XCTest の実行結果を捏造しない。Python 検査は実行し、結果を書く。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。直ったと書かない。
- 監査ファイル（anicca-ops 側）は一切変更しない。提出はしない。新規の有料支払いはしない。
