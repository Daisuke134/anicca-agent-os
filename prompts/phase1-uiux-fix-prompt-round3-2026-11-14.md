# 委任 第3ラウンド: ビルド修正＋差分指示2件（Anicca iOS、Issue #9353）

これは ROUTE: LOCAL 相当のコード作業である。対象はこの作業ディレクトリ（Daisuke134/anicca のブランチ `claude/phase1-personalized-onboarding`、PR #9352）の `apps/mobile/anicca-ios`。第1ラウンド（commit `1f26b0f42`）と第2ラウンド（commit `10c4cc93c`）の上に続ける。GitHub Issue #9353 に紐づく作業である。進め方は Anthropic の形（エージェントが書き、別のエージェントがレビューし、エージェントが統合する）。App Store Connect への提出は絶対にしない。記録は `apps/mobile/anicca-ios/PHASE1-UIUX-FIX-NOTES.md` に「第3ラウンド」節を追加する形で行う。

## A. ビルド失敗の修正（最優先）

第1ラウンドの push で GitHub Actions のビルドが失敗した（run 43581061697、"Build app (unsigned)"、exit 65）。ワークフローのビルドステップが `xcodebuild ... | tail -40` のため、コンパイラのエラー本文はログに残っていない。残っている唯一の手がかりは "Failed frontend command" の対象ファイル群である:

HabitSleepFollowUpView.swift、ShareImageRenderer.swift、AuthPresentationDelegate.swift、NotificationScheduler.swift、StruggleDepthStepView.swift、QuoteNavigationCoordinator.swift、CustomProblem.swift、DailyAffirmationStore.swift（新規）、InitialAffirmationExperience.swift、PrimaryButton.swift、VerticalPager.swift、AppState.swift、AccessorylessTextField.swift、ScheduledSet.swift、ReviewPromptCoordinator.swift、LLMGeneratedNudge.swift、LikedQuotesStore.swift、OnboardingBibleViews.swift、AppBackground.swift、TraitsDetailView.swift、HabitNameField.swift、NudgeContent.swift、OnboardingProgressBar.swift、LLMNudgeService.swift、PricingDisclosureBanner（ファイル名は途中までしか残っていない）を含むバッチ。

やること:
1. systematic-debugging の手順で、このバッチのファイルと、第1・2ラウンドで変更した全ファイルについて、Swift の型エラー・未解決シンボル・重複定義・actor 隔離の不整合・参照サイクルになりうる変更を精査し、根本原因を特定して直す。推測で直さず、各修正に「なぜこれがエラーになるか」を FIX-NOTES に書く。
2. 特に注意: DailyAffirmationStore（新規ファイル）と、それを参照する FeedRootView / InitialAffirmationExperience の整合。新規 XCTest ファイル2件（DailyAffirmationStoreTests、PaywallDisclosureTests）の project.pbxproj 登録の正しさ。削除した旧 View の参照残り。第2ラウンドで追加した AdaptiveOnboarding / PersonalizationProfile / AdaptiveQuestionStepView の型整合。
3. ワークフロー `.github/workflows/anicca-ios-build.yml` のビルドステップを、単体テストステップと同じ形（全文をファイルへ保存し、エラー行を grep して表示し、最後に要約を出す）に直す。失敗時に全文ログを artifact として残すステップも足す。これにより次回の失敗は診断可能になる。ワークフローの他のジョブ・条件は変えない。

## B. 差分指示（2026-11-14 18:45 JST、本人の確定）

### B-1. アニメーションと UI/UX で「驚かせる」ことを中核の受け入れ条件にする

具体化は勝者の一次資料で裏付けられる範囲に限る。裏付けは次の3点だけであり、これを超える独自の動きは作らない。

1. reveal の構造は「1つの入力 → 見える変換 → 結果の出現」。根拠: 勝者調査 `files/ux-experience-winner-research-2026-11-14.md`（anicca-ops）211行目。Cal AI のデモは「スキャンのアニメーション → 結果のカードが現れる」で成立し、同調査はこれを Phase 1 の reveal（答え → その人の言葉が現れる）と同じ構造と明記している。個人化プレビュー（04）と最初の介入（08）は即時切り替えではなく、答えがその人の言葉へ変わる過程が見える段階的な出現にする。待ち時間の水増しはしない（変換が見える最小限の時間にする）。
2. 受け入れの物差しは魔法の瞬間（答え終えて数秒で「分かってもらえた」と感じること）。動きの目的はこの瞬間に置き、他の画面へ派手な動きを足さない。
3. reveal の着地はテーマの絵と一体のカード（監査 S4 の勝者対比どおり）。文字だけの画面にしない。

裏付けが無いものの扱い: I am のアニメーションの具体（時間・イージング・種類）は自社の実測資料に記録が無い。勝者の動きの逐語コピーはできないので、上の構造だけを実装し、その旨を FIX-NOTES に書く。

### B-2. 1画面1質問の確定

第2ラウンドまでの形を維持する。新しい画面を足す場合も1画面1問にする。

### B-3. 合成ユーザーを作り、そこから個人化を始める（製品の流れの固定）

- 流れ: 回答が集まる → その人の合成ユーザー（synthetic user）を作る → その合成ユーザーで個人化を始める。
- 実装: オンボーディング完了時に、第2ラウンドで保存した回答（安定 ID の軸データ）から合成ユーザーの記録を端末内に生成・保存する。合成ユーザーの記録は、属性（年齢層の列挙 ID、生活文脈）、状態の初期値（気分の土台）、信念のテーマ、トリガーの文脈、受容性の時間窓、静かな時間、介入の履歴、動機を構造化して持つ。個人化（アファメーション選択と通知の条件づけ）は、この合成ユーザーの記録を入力として読む形にそろえる（現在の UserProfile 直接読みが残る場合は、合成ユーザーの記録を正とし、UserProfile はその材料として位置づける）。
- 質問の見直し: 合成ユーザーを作るのに要る軸が第2ラウンドの質問で欠けていれば、質問を足す。どの軸のデータにもならない質問は置かない。見直しの結果（軸の一覧と対応する質問）を FIX-NOTES に表で書く。
- プライバシー: 合成ユーザーの記録と分析に残すのは列挙 ID のみ。名前・生年月日の実値は含めない。
- 根拠: anicca-ops `files/user-simulation-loop-spec-2026-11-14.md`（条件づけの材料は回答と反応履歴）、`files/humansand-competitor-research-2026-11-13.md`（Persimmon はプロフィールと履歴で条件づけたユーザーモデル）。

## C. 差分指示2（2026-11-14 18:49–18:51 JST、本人の追加確定）

**Model・Eval・Product の接続は今行う。** 今夜出す版に入る物として扱う。

- オンボーディングの回答と通知への反応は、eval の共通形（状況→刺激→実測の反応）でそのまま学習と評価の材料になる形式で永続化する。フィールド定義は ManagerBench／one-benchmark-plan の共通形に合わせる。正本: anicca-ops `files/one-benchmark-plan-2026-11-13.md`: 状況（文脈）→ AI が作ったもの（刺激）→ 人の実際の反応（実測）。ground truth は実測の反応（受け取ったか、開かれたか、続けているか）。通知・ナッジのケースは「言葉×タイミング×人の状態 → 反応」。
- 第2ラウンドの判断点の記録（DecisionPointRecorder、delivery_id 結合）を土台に、永続化される1行が3要素を明示的に持つ形へそろえる:
  - 状況: 回答 snapshot（列挙 ID の辞書）、文脈（予定時刻の時間帯、曜日、通知許可の状態）。
  - 刺激: message_id、候補のカテゴリとタグ、予定時刻と配信時刻、treatment_assigned、assigned_probability（必須）、policy_version。
  - 反応: notification_delivered、notification_opened、app_opened、responded、skipped、saved、shared（取れるもの）と各時刻。未観測は null、観測窓終了後の無反応は false と区別する（既存の計測契約どおり）。
- フィールド名と意味は ManagerBench の行としてそのまま使える形にし、対応表（アプリのフィールド ↔ 共通形の要素）を FIX-NOTES の第3ラウンド節に書く。
- プライバシーは維持: 仮名化した person_id と列挙 ID のみ。名前・生年月日の実値・自由文はケースに含めない。

## 完了の定義

- A の根本原因が特定され、修正と理由が FIX-NOTES にある。ワークフローのログ改善が差分に含まれる。
- B と C が実装され、FIX-NOTES の第3ラウンド節に対応表（合成ユーザーの軸↔質問、アプリのフィールド↔eval 共通形）がある。
- 既存の Python 検査とローカライズ照合で、新しい欠落を作っていない。
- コミットはしなくてよい（委任元が差分を読んでから commit/push する）。作業ツリーに変更を残した状態で終えること。欠陥 D-01〜D-16 は引き続き全件未完了として扱う（閉鎖は再撮影フレームの目視でのみ）。
