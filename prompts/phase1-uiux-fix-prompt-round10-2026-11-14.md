## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第9ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第10ラウンド委任文（ダイアログ照合パターンの実測不整合の修正）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `8a59bd237`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。**アプリの Swift コードは変更しない。対象は Maestro フローだけである。**

## 実測された根本原因（一次証拠: Maestro run 43606475166 の画面階層 JSON）

- 両フローとも `Assertion is false: id: onboarding-welcome-cta is visible` で失敗した（メイン 2分20秒、適応 4分20秒）。PR ビルド＋単体テスト（run 43606478090）は success。
- artifact に残った画面階層 JSON（`step-012/016/020-assertCondition-onboarding-welcome-cta.json`、いずれも同内容）を統合側が実読した。待機中の画面階層には、アプリ側の要素が一切無く、**OS のアラートだけ**が含まれていた。そのアラートのタイトル文字列は、記録上こうなっている:

  `Sign in to Apple\xa0Account`（"Apple" と "Account" の間は通常の空白ではなく **U+00A0 のノーブレークスペース**。ボタンは `Cancel` と `OK`）

- 第8・第9ラウンドの消去条件は正規表現 `(?i)sign in to (your )?apple (account|id)` で、"apple" の直後に**通常の空白**を要求する。そのため実在のタイトル文字列に一致せず、消去は一度も発火しなかった。アラートが出ている間は画面階層がアラートだけになるため、`onboarding-welcome-cta` の表示待機も永遠に成功しない。これが第3〜第5の Maestro 試行すべてに共通する詰まりの正体である（第8ラウンドの JS フラグ問題は、その上に重なった別の問題だった）。

## このラウンドの作業

1. `apps/mobile/anicca-ios/maestro/v1.9.14/` 配下の全フロー・サブフローで、上記の照合パターンを使っている箇所を全て探し（`grep` で洗い出す）、U+00A0 を含む実文字列に一致する形へ直す。方針の例: (a) パターンを空白に依存しない形にする（例: `(?i)sign in to (your )?apple` で打ち切る）、(b) 空白類に U+00A0 を明示的に含める。どちらでもよいが、選んだ形が記録された実文字列 `Sign in to Apple\xa0Account` に一致することを、ローカルで正規表現の照合テスト（python 等）で示し、その結果を FIX-NOTES に残す。あわせて通常空白の表記（`Sign in to Apple Account`）にも一致する形であること（OS の表記が将来どちらでも効くように）。
2. 消去の発火条件と待機の構造（第9ラウンドの形: 消去の有界ループ→素の `extendedWaitUntil`）は変えない。変えるのは照合パターンの文字列だけ。フレーム名・番号、アサーション、待機時間は変えない。
3. **FIX-NOTES 第10ラウンド節**: run 43606475166 の実測（両フローの失敗文、画面階層 JSON にアラートだけが含まれていたこと、タイトル文字列の `\xa0` の記録）、根本原因（空白の種類の不整合で消去が一度も発火しなかったこと。第3〜第5試行共通の詰まりであること）、修正したパターンと、その照合テストの結果（実文字列と通常空白の両方に一致）を書く。撮影パスの修正が依然未検証である旨も明記する（フローはまだ撮影ステップへ到達していない）。
4. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）と YAML 構文検証を実行し、結果を第10ラウンド節に書く。

## 必須条件

- 変更対象は `apps/mobile/anicca-ios/maestro/v1.9.14/` 配下のフローと `PHASE1-UIUX-FIX-NOTES.md` だけ。Swift コードと実行スクリプトには触れない（触れる必要が生じたら理由を FIX-NOTES に書く）。
- Maestro の実行結果を捏造しない（判定は push 後の Actions）。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
