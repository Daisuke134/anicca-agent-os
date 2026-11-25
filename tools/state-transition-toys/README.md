# state-transition-toys

状態遷移と文脈バンディットの最小の実走スクリプト（2026-11-14 導入・実走済み）。
出典と判定は anicca-ops `files/state-transition-research-2026-11-14.md`。

- `hmm_quickfit.py`: hmmlearn の GaussianHMM を、自社の状態ログの形をした小さな手製の系列（実測ではない）に適合し、遷移行列と状態の復号を出す。
- `bandit_quickrun.py`: MABWiser（LinTS）と contextualbandits（LinTS）を、決定点の表の形をした手製の記録で学習と予測まで回す。

## 動かし方

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python hmm_quickfit.py
.venv/bin/python bandit_quickrun.py
```

## 実走の記録（2026-11-14、自社 VM）

- hmmlearn: 適合し、遷移行列（3状態）と36点の復号列が出た。
- MABWiser: 8件の記録で学習し、文脈2件への予測と期待報酬が返った。
- contextualbandits: 200件で学習し、検証側で最良の腕を選んだ割合は 0.30〜0.34（実行ごとに変わる）。偶然の 0.333 と変わらず、この小さな条件では学習の効果は示せていない。仕組みが動くことだけを確認した。
- 数字は全て手製データのもので、介入の良さを示すものではない。

受容性のほうの実走は `~/workspace/tools/generalizing-receptivity-models/`（別フォルダ）。そちらは import に torch（CPU 版）が要る。
