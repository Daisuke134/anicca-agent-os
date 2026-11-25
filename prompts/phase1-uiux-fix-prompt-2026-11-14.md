# 委任: Phase 1 UI/UX 監査の修正（Anicca iOS）

これは ROUTE: LOCAL 相当のコード作業である。対象はこの作業ディレクトリ（Daisuke134/anicca のブランチ `claude/phase1-personalized-onboarding`、PR #9352）の `apps/mobile/anicca-ios` である。

背景: 提出を凍結した Phase 1（個人化オンボーディング）について、全画面監査で欠陥16件（D-01〜D-16）が確定した。監査の正本は別リポ anicca-ops の `files/phase1-uiux-audit-2026-11-14.md` で、この委任文に修正仕様（監査第7章 F-01〜F-13）と受け入れ条件を全文埋め込んである。添付画像は監査の証拠フレーム（番号は監査と同じ）と勝者 I am の画面である。

## 絶対条件

1. App Store Connect への提出は絶対にしない。バージョン申請・審査提出・ストア掲載情報の変更はしない。
2. 成果物、または変更しない理由を書いたファイルを、必ず差分（diff）に含めること。具体的には `apps/mobile/anicca-ios/PHASE1-UIUX-FIX-NOTES.md` を新規作成し、F-01〜F-13 の各項目について「変更した内容（ファイル名つき）」または「変更しなかった理由」を1項目ずつ書くこと。このファイルが無い差分は未完了として差し戻される。
3. 修正後、GitHub Actions（`.github/workflows/anicca-ios-build.yml` の Build and unit tests ジョブ）でビルドと単体テストを回し、結果を添えること。この Linux 環境では xcodebuild は動かないので、ローカルで Swift の構文・型の整合を可能な範囲で確認し、Actions の結果は委任元（Muse）が push 後に確認して記録に添える。コードはコンパイルが通る状態に保つこと（未使用シンボル・型不一致を残さない）。
4. 再撮影（Maestro E2E）で全画面の新しいフレームを取り、監査の証拠と同じ番号（01〜13）で並べられる形にすること。Maestro の実行自体は GitHub Actions の workflow_dispatch（run_maestro=true）が正本であり委任元が行う。あなたの仕事は、既存の Maestro フロー（`scripts/run-soft-paywall-maestro.sh` と配下の flow ファイル）が必要な画面を全て通るように保つ／必要なら flow を拡張すること。拡張した場合はその旨を FIX-NOTES に書くこと。
5. 既存の単体テストを壊さない。テストが仕様変更で古くなる場合は、テスト側も新しい確定仕様に合わせて直し、その旨を FIX-NOTES に書く。

## 修正仕様（監査第7章 F-01〜F-13、根拠つき）

共通の受け入れ条件: 修正後、全画面を原寸フレームで再監査し、欠陥番号が閉じていることを目で確認してから提出する（提出自体は今回しない）。

- F-01 デザインの言語を1つに固定する（D-05）。見出しの書体、背景、主ボタンの色、選択肢カードの形、選択された状態の表し方を全画面でそろえる。土台は系統A（セリフ体＋温かい背景）とする。実測では系統A = 背景 #F1F1E8→#E3E9DA の薄緑グラデーション＋セリフ体見出し＋深緑ボタン、系統B = #F7F2EB 一色＋太いサンセリフ＋黒ボタン、系統C = システム既定シート（いいね一覧・テーマ選択）。Q2・Q3・リマインダー許可・ペイウォール（系統B）と、いいね一覧・テーマ選択（系統C）を系統A の言語に統一する。選択肢カードの形（3種類ある）と選択状態の表し方も1つにそろえる。根拠: 勝者 I am は全画面が1つの言語（温かいベージュ＋セリフ体）で統一されている。
- F-02 ペイウォールを1画面に収める（D-01、D-02）。前面に出すのは年額＋トライアルの1つのオファーとする（勝者の形）。3プランを出す場合は、3つのタイルと日程とボタンがスクロールなしで全部見える大きさに収める。Lifetime の価格も見えること。日程の文は、切れない長さに書き直すか、折り返して全文を表示する。根拠: ScreensDesign の I am 実測（ペイウォールは年額＋3日トライアルを前面に提示）。
- F-03 年額に月額換算を併記する（D-13）。根拠: ScreensDesign の実測（価格を小さな月額換算に分けて見せる）。ただし追補の受け入れ条件（下記）を優先する: 総請求額（実際に請求される年額と期間）が価格表示の主役であり、月額/日額換算は位置と大きさの両方で従属させる。換算額を実際の月次請求と誤認させない。
- F-04 文字切れを全画面で無くす（D-02、D-03）。見出し・本文・日程のどこにも「…」での切り捨てを出さない。通知設定（ReminderScheduleStepView）の見出し「A little kindness. Righ…」と本文「Scheduled in your time zone. Device settings and…」は、入り切る長さに書き直し、レイアウト側でも切れないようにする（行数制限を外す／折り返す）。「GMT」という浮いたラベルは消す（D-04）。
- F-05 ホームを確定した形にする（D-06）。開いたら今その人に必要な1つが出ている形にし、無限にめくれるスワイプ式フィードを既定のホームにしない。根拠: 製品の確定事項（フィードは捨て、開いたら今必要な1つ）と、勝者の核がロック画面とウィジェットへの配信であること。実装の範囲: FeedRootView の既定表示を「今日のその人の言葉1つ」を中心にした画面に変える。フィード自体を削除する必要はないが、起動直後の既定ホームは単一表示にすること。判断に迷う場合は FIX-NOTES に設計判断を書くこと。
- F-06 最初の画面に導入を置き、質問を1画面1問に分ける（D-07、D-08）。WelcomeStepView を `OnboardingStep.initialJourney` の先頭に戻す。名前は目標と別のステップで聞く（現在 Q1 は目標の質問と名前入力が同じ画面にある）。`resumableInitialStep` の goal への読み替えも welcome の扱いに合わせて直す。
- F-07 最初の介入（FirstInterventionStepView）のボタンの文言を行き先に合わせる（D-10）。現在、個人化プレビュー（FirstAffirmationStepView）と最初の介入で同じ文言「Make room for a daily moment」が使われ、行き先が違う（前者は通知設定へ、後者はフィードへ）。行き先が分かる別々の文言にする。
- F-08 テーマ選択に、選択中のテーマの印を出す（D-11）。勝者 I am のテーマ画面と同じく、現在のテーマにチェックの印を出す。
- F-09 いいね一覧で、保存した言葉をテーマ付きのカードで見せる（D-12）。現在は白いカードに素のテキストが並ぶだけ。保存した言葉を、そのテーマの見た目（背景）を持ったカードとして表示する。
- F-10 ホームの先頭に、最初の介入で見せたその人の言葉を出す（D-14）。現在、最初の介入で見せた言葉（その人の答えから選ばれた言葉）とホームの最初のカードが違う。個人化の約束とホームの先頭を一致させる。
- F-11 App Store スクリーンショットの1枚目を、ロック画面とウィジェットの到達画面にする（D-16）。これはアプリコードの変更ではなくストア素材の作業である。この委任では実装しなくてよい。代わりに FIX-NOTES に「コード変更の対象外であり、ストア素材の別作業として残す」と理由を書くこと。
- F-12 到達できない旧画面群の扱いを決める。現在の流れ（initialJourney）から到達できない画面: WelcomeStepView（F-06 で復帰させるものを除く）、ProcessingStepView、ComparisonTableStepView、`Onboarding/OnboardingBibleViews.swift` 内の旧ステップ群（AgeRangeStepView、GoalStepView、TinderPainCardsView、WhatTriedStepView、StressSliderStepView、SocialProofStepView、PreferredNudgeTimesView、MeditationExperienceStepView、PaywallValueTimelineStepView）。使う画面は現在の流れに戻し、使わない画面は削除する。残置はしない。削除したファイル・シンボルは FIX-NOTES に列挙すること。削除によって参照が壊れる場合は、その参照側も直す。
- F-13 未確認の画面を再監査できるようにする。監査で未確認だった画面: フィード設定シート（Views/Feed/SettingsSheet.swift）、フィード内の通知シート、プロフィール特性詳細（Views/Profile/TraitsDetailView.swift）、利用上限モーダル（Views/UsageLimitModalView.swift）、継続オファーシート（Onboarding/RetentionOfferSheet.swift）、習慣フォローアップ3画面（Settings/HabitSleepFollowUpView.swift、HabitTrainingFollowUpView.swift、HabitWakeFollowUpView.swift）、認証必須プレースホルダ（Session/AuthRequiredPlaceholderView.swift）、ウィジェット（AniccaWidget/AniccaWidget.swift、AniccaWidgetLiveActivity.swift）、共有画像出力（Views/Feed/ShareImageRenderer.swift）、ペイウォールのプライマー（Onboarding/PaywallPrimerStepView.swift）。これらの画面そのもののデザイン統一（F-01 の言語）は本委任の範囲に含める。再撮影で到達できるよう、Maestro フローで設定シートとテーマ選択・いいね一覧を開く手順が無ければ追加する。到達できない画面が残る場合は、その理由を FIX-NOTES に書くこと。

## 追補の受け入れ条件（Dots レビュー、Apple 公式根拠つき。F-02/F-03 に適用）

出典: Apple Developer, Auto-renewable subscriptions, "Clearly describing subscriptions / Billing amount / Free trials"（https://developer.apple.com/app-store/subscriptions/、2026-11-14 実読）。

- 総請求額が価格表示の主役であること。年額の月額換算を追加しても、実際に請求される年額と期間を最も目立つ価格表示にする。月額/日額換算・割引比較は位置と大きさの両方で従属させる。
- トライアル後の請求を全文読めること。選択された商品について、トライアル期間、終了後の実際の請求額と更新期間を切らずに表示する。Lifetime 等へ選択を変えた場合も、別プランの年額やトライアル説明を残さない。
- 復元と規約への導線を失わないこと。1画面に収める修正で Restore Purchases、Terms、Privacy を削除しない。

## 完了の定義

- 上記の変更が作業ツリーに差分として存在し、`PHASE1-UIUX-FIX-NOTES.md` が F-01〜F-13 全項目の結果（変更内容または変更しない理由）を含むこと。
- 変更したファイルの一覧と、各欠陥番号（D-01〜D-16）のうちどれが閉じたかを FIX-NOTES の末尾に表で書くこと。閉じていない欠陥は「未完了」と明記すること（全部直ったと書くのは再撮影フレームで確認できたときだけであり、それは委任元の再監査で行う）。
- コミットはしなくてよい（委任元が差分を読んでから commit/push する）。ただし作業ツリーに変更を残した状態で終えること。
