## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第8ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。/tmp の空き容量は約430MBある。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第9ラウンド委任文（Maestro 待機の仕組みの単純化）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `50597d6a1`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。**このラウンドもアプリの Swift コードは変更しない。対象は Maestro フローと実行スクリプトだけである。**

## 実測された事実（一次証拠: Maestro run 43600894800、HEAD `50597d6a1`）

- Release ビルド通過、PR ビルド＋単体テストは run 43600895804 で success。
- 両フローとも約6分で失敗し、失敗文は両方とも `Assertion is false: false is true`。これは第8ラウンドで追加した `_wait-for-storekit-screen.yaml` 末尾の `assertTrue: ${output.storeKitScreenReady}` の失敗である（result.xml と maestro.log の要約で確認）。
- 適応フローの詳細ログ（artifact 内 `maestro-run.*/adaptive/.../logs/maestro.log`）の実読:
  - 待機の準備状態を立てる内側 runFlow の条件が、ログに `Run flow when id: ${READY_ID} is visible and "(?i)sign in to (your )?apple (account|id)" is not visible` と**プレースホルダが生のまま**表示され、ポーリングのたびに `SKIPPED` になった。呼び出し側（`_start-to-pain.yaml` 14-17行、`01-soft-paywall.yaml` 14-17行）は `READY_ID: onboarding-welcome-cta`、`WAIT_TIMEOUT_MS: 60000` を env で渡している。run 43595457904 の失敗メッセージでは条件内の id は実値で表示されていた（`id: onboarding-welcome-cta is visible`）ため、今回の生表示は「この入れ子位置では置換されていない」ことの証拠として読める（ログがテンプレートを生で出すだけの可能性は完全には排除できない。その場合でも、下記の単純化はどちらの読みでも正しい）。
  - ループは 60 秒の予算より早く（約33秒で）抜け、その後の assert が失敗した。同じ失敗がリトライでもう1回起きた（14:17:10 と 14:18:21）。
  - 消去サブフロー `_dismiss-apple-account.yaml` 自体の条件は、その時点でダイアログが見えなければ `SKIPPED`（正常）になることは確認できた。
- フレーム回収（相対名撮影→証拠フォルダへコピー）は、両フローとも撮影ステップへ到達しなかったため**依然未検証**である。撮影名（37枚）と回収の仕組みは変えない。
- 参考: run 43595457904（第8ラウンド前）では、適応フローは同じダイアログが出ていても素の `extendedWaitUntil` 系の進行で困りごと選択や stress 深掘りまで到達していた。詰まったのは「ダイアログが残ったまま60秒待った」メインフローの初回待機だけである。

## このラウンドの作業（仕組みの単純化）

1. **JS フラグによる合否ゲートを廃止する**: `_wait-for-storekit-screen.yaml` の `output.storeKitScreenReady` フラグ、入れ子の `when`（env プレースホルダを含む条件）、末尾の `assertTrue` を使わない形へ作り替える。置換の効かない位置に変数を置く設計そのものをやめる。
2. **待機は呼び出し側の素のプリミティブに戻す**: 準備完了の待機は、各呼び出し箇所で従来の `extendedWaitUntil`（対象 id を YAML に直接書く。変数経由にしない）をそのまま使う。待機時間（60秒）も変えない。
3. **ダイアログ消去は待機の前に独立して行う**: 各待機の直前に、消去サブフローを有界回数だけ繰り返す小さなポーリング（例: 「ダイアログが見えたら Cancel」→短い待機、を最大で数十秒分）を置く。ダイアログが無ければ即通過し、あれば消してから待機へ入る。ペイウォールの購入系ステップ前（現在 `_wait-for-storekit-screen.yaml` を呼んでいる箇所）も同じ形（消去→素の待機）に揃える。消去はダイアログが存在する場合にだけ効く条件付きのままとし、アサーションは弱めない。
4. 変更後、CI ログ上で「待機条件に実値の id が表示される」「消去と待機が分離して実行される」ことが読み取れる形になっていることを、FIX-NOTES に設計として明記する（実走の判定は push 後の Actions で行う。捏造しない）。
5. **FIX-NOTES 第9ラウンド節**: run 43600894800 の実測（両フローの失敗文、詳細ログの該当行の引用: 生プレースホルダ表示と SKIPPED の繰り返し、約33秒でループを抜けたこと、リトライでも同じ失敗）、原因の読み筋（置換の効かない入れ子条件に合否を依存させた設計が原因。アプリの欠陥ではない）、単純化の内容を書く。撮影パスの修正が依然未検証である旨も明記する。
6. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）、フローの YAML 構文検証、`bash -n`（スクリプト変更時）を実行し、結果を第9ラウンド節に書く。

## 必須条件

- 変更対象は `apps/mobile/anicca-ios/maestro/` 配下のフロー、`apps/mobile/anicca-ios/scripts/run-soft-paywall-maestro.sh`（必要な場合のみ）、`PHASE1-UIUX-FIX-NOTES.md` だけ。Swift コードには触れない。
- フレーム名・番号（37枚）と既存のアサーション（表示・非表示の確認内容）は変えない。待機時間を延ばして誤魔化さない。
- Maestro の実行結果を捏造しない。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
