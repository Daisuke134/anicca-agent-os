## 先行承認（冒頭で必ず読むこと）

`scripts/verify-source-boundary.sh` が旧名 life-manager の固定パスで exit 2 になること、および origin が改名後の Daisuke134/anicca であることは、第1〜第7ラウンドで確認済みの既知の不一致である。委任元はこの不一致を承知のうえで、この指定作業ツリー（~/workspace/life-manager-phase1、branch claude/phase1-personalized-onboarding、origin Daisuke134/anicca）での作業を明示的に指示している。この例外は承認済みとして扱い、確認の質問で停止しないこと。境界スクリプト自体は変更しない。/tmp の空き容量は約490MBある。大きな一時ファイルは ~/workspace 配下へ置くこと。

# Phase 1 UI/UX 修正 第8ラウンド委任文（Maestro フローの2つの実測失敗の修正）

宛先: 作業担当エージェント（Codex CLI）／ 対象: `~/workspace/life-manager-phase1`、ブランチ `claude/phase1-personalized-onboarding`、開始 HEAD `a5e1c19bf`。commit / push / merge / PR 作成 / ASC 提出はしない（統合側が行う）。**このラウンドはアプリの Swift コードを変更しない。対象は Maestro フローと実行スクリプトだけである。**

## 実測された事実（一次証拠: Maestro run 43595457904、HEAD `a5e1c19bf`）

Release ビルドは通過し（第7ラウンドの修正が確定）、アプリは起動して画面遷移した。証拠 artifact `soft-paywall-evidence-a5e1c19bf...` に動画（experience.mp4、578秒）と両フローのログがある。統合側がログと動画フレームを実読した結果、失敗は次の2件である。どちらもアプリ本体の欠陥ではなく、フローの作りの問題である。

### 失敗1: メインフロー（01-soft-paywall.yaml）が最初の待機で時間切れ

- ログ: `[Failed] ... (2m 13s) (Assertion is false: id: onboarding-welcome-cta is visible)`。`clearState` + `clearKeychain` + `launchApp` の後、`onboarding-welcome-cta` の表示を60秒待って現れなかった、という内容。
- 動画の実読: ウェルカム画面そのものは表示されていた（見出し「…when you need them most」、Anicca のワードマーク、進捗バー）。ただしその上に **OS の「Sign in to Apple Account」ダイアログ**（StoreKit の商品取得が引き起こすサンドボックスのサインイン要求）が重なっており、記録の最後まで残っていた。適応フローの側でも同じダイアログがウェルカム画面の時点から出ていた。
- メインフロー冒頭の `tapOn: text "Cancel|Not Now" optional` は起動直後の1回だけで、ダイアログがその後に現れると誰も消さない。表示判定はダイアログに遮られて失敗する。タイミング依存の詰まりである。
- なお適応フローは同じダイアログが出ていても先へ進めた（途中のステップで消えたとみられる）。両フローの差分も含めて、出現した時点で確実に消す形に統一すること。

### 失敗2: 適応フロー（02-adaptive-modules.yaml）が最初の takeScreenshot で失敗

- ログ: `[Failed] ... (4m 46s) (Invalid path "/Users/runner/work/_temp/soft-paywall-evidence/frames/02f-stress-trigger.png" for takeScreenshot: it resolves outside this run's takeScreenshot output folder. ...)`。
- フローは `${EVIDENCE_DIR}/frames/<番号-名前>`（EVIDENCE_DIR はスクリプトが `-e` で渡す `$RUNNER_TEMP/soft-paywall-evidence`）へ撮影する作りだが、CI 上の Maestro 2.12.1 は「この run の takeScreenshot 出力フォルダの外」へのパスを拒否する。対話ステップ自体は 02f の撮影直前まで全て成功していた（動画で stress の深掘り画面「When does stress feel heaviest?」が新しいデザインで表示されていることを統合側が確認済み）。

## このラウンドの作業

1. **ダイアログの消去（失敗1の修正）**: 両フロー（および共有の `_start-to-pain.yaml`）で、「Sign in to Apple Account」ダイアログが出たら Cancel で消す処理を、起動直後だけでなく、ウェルカム画面の表示待機と競合しない形で組み込む。例: 表示待機の前に「ダイアログが見えたら Cancel を押す」条件付き runFlow を置き、必要ならペイウォールの購入系ステップの前にも同じものを置く。アサーション自体（60秒待機や表示確認）は弱めない。ダイアログが無い環境では何もしないで通過すること。
2. **撮影パスの修正（失敗2の修正）**: Maestro 2.12.1 が受け付ける形（run の出力フォルダ内に解決される相対名など、公式ドキュメントで確認できる方式）に takeScreenshot を変更し、撮影されたフレームが最終的に証拠フォルダの `frames/` へ、従来と同じファイル名（00-welcome、01-q1-goal、01b-name、…、監査と同じ番号体系）で集まるよう、スクリプト側の後処理（コピー）を含めて揃える。フレーム名と番号は変えない。方式の根拠（Maestro 公式ドキュメントの該当箇所）を FIX-NOTES に書く。
3. **FIX-NOTES 第8ラウンド節**: run 43595457904 の実測（両フローの失敗文の原文、動画 578秒、統合側が動画で確認した画面: ウェルカム画面がダイアログの下に存在したこと、困りごと選択画面と stress 深掘り画面が新デザインで描画されていたこと）、2件の修正内容と根拠を書く。アプリの欠陥ではない旨も明記する。
4. Python 検査（`python3 -m unittest discover -s scripts/tests`、apps/mobile/anicca-ios 配下）と `bash -n`（スクリプトを変更した場合）を実行し、結果を第8ラウンド節に書く。フローの YAML 構文も検証する（python の yaml パース等）。

## 必須条件

- 変更対象は `apps/mobile/anicca-ios/maestro/` 配下のフロー、`apps/mobile/anicca-ios/scripts/run-soft-paywall-maestro.sh`、`PHASE1-UIUX-FIX-NOTES.md` だけ。Swift コードに触れたら理由を FIX-NOTES に書く（原則として触らない）。
- アサーションを弱めて「通ったことにする」変更はしない。消去処理はダイアログが存在する場合にだけ効く形にする。
- Maestro の実行結果を捏造しない（VM に Xcode/Maestro の実走環境は無い。判定は push 後の Actions で行う）。
- 欠陥 D-01〜D-16 は再撮影フレームの目視確認まで全件「未完了」のまま。
- 監査ファイル（anicca-ops 側）は変更しない。提出はしない。新規の有料支払いはしない。
