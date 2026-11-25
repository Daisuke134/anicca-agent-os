# Cross-study generalization of receptivity models

Reference implementation for **"Evaluating Cross-Study Generalization of Receptivity Models
for Just-in-Time Adaptive Interventions"**.

The repository contains the six model families reported in the paper, the two evaluation
protocols (within-study and cross-study), and a synthetic data generator so the whole
pipeline can be exercised without access to the original trial data.

---

## Why there is no data here

This work is a secondary analysis of datasets collected by independent teams during
previously published clinical trials (PEACH, ALLY, OPTIMAX, HAPPY). We do not own these
datasets and are bound by the original IRB protocols and participant consent forms, which
prohibit public release of participant sensing data. Researchers seeking access can
establish a data use agreement directly with the original study authors.

To keep the code verifiable without the data, `receptivity.synthetic` generates studies
with the same *structure* as the real ones — overlapping but unequal sensor sets, unequal
study sizes, participant grouping, and a weakly predictable label. The resulting AUCs are
meaningless, but every code path runs.

---

## Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Python 3.10 or newer. A GPU is optional; pass `--device cuda` through to the tree models or
let the neural models auto-detect CUDA/MPS.

---

## Data format

One parquet file per study, named `<cohort>_<platform>_*.parquet` (for example
`peach_and_LKV2__merged_cleaned.parquet`). The platform suffix must be `and` or `ios`, since
it determines the `os` feature. Each file has:

| Column | Meaning |
| --- | --- |
| `receptive` | Binary label: did the participant respond within the receptivity window |
| `participantId` | Grouping key; all cross-validation is grouped by participant |
| everything else | One context feature per column, numeric |

Studies deliberately do **not** share a column set: that structural heterogeneity is the
object of study, and the code discovers each study's sensors from its columns.

---

## Quick start

```bash
# 1. Generate synthetic studies and confirm the pipeline runs
python -c "from receptivity.synthetic import write_synthetic_studies as w; w('data-synthetic')"
python -m receptivity.cli.cross_study --data-dir data-synthetic --model xgb \
    --target-index 0 --max-configurations 3 --max-evals 2

# 2. Run the test suite
pip install pytest && pytest

# 3. Point the same commands at real data
python -m receptivity.cli.within_study --data-dir data
python -m receptivity.cli.cross_study  --data-dir data --model masked-fcnn --target-index 0
```

---

## The models

| Key | Class | Feature space | Paper role |
| --- | --- | --- | --- |
| `lr` | `LogisticRegressionModel` | intersection | Within-study and intersection baseline |
| `rf` | `RandomForestModel` | intersection | Within-study and intersection baseline |
| `xgb` | `XGBoostModel` | intersection | Within-study and intersection baseline |
| `fcnn` | `FCNN` | intersection | Within-study and intersection baseline |
| `xgb-median` | `MedianImputedXGBoost` | source union | Feature-union strategy (RQ3) |
| `xgb-knn` | `KNNImputedXGBoost` | source union | Feature-union strategy (RQ3) |
| `masked-fcnn` | `MaskedFCNN` | full union | Missingness-aware strategy (RQ3) |
| `coral` | `DeepCORAL` | full union | Domain-generalization baseline (RQ3) |

Three feature spaces are distinguished, because the strategies differ in exactly this
respect (`receptivity.data.FeatureSpace`):

- **intersection** — only sensors present in every source study *and* the target. Complete
  matrix, narrow. What the classical models require.
- **source union** — every sensor in any source study. Target-only sensors are dropped,
  since nothing in training could have learned to use them. Used by the imputation models.
- **full union** — source union plus target-only sensors, carried as all-missing columns.
  Used by the missingness-aware and CORAL models, which are dimensioned over the complete
  sensor superset.

Absent features are represented as `NaN` in `Split.X_*`, with a parallel binary
`Split.mask_*` recording availability. Each model decides what to do with them: narrow the
space (classical), impute (`xgb-median`, `xgb-knn`, `coral`), or consume availability as an
input signal (`masked-fcnn`).

### Notes on individual models

**`masked-fcnn`** gates the standardised features with the mask (`x * m`) and then
concatenates the mask, so the first dense layer has width `2d`. The gate matters because
standardising a zero-filled column leaves absent entries at `-mean/std` rather than zero;
the gate returns them to zero. The concatenation matters because without it, a zero could
mean either "absent" or "present and near the mean".

Its scaler is fitted on the source pool and reused unchanged for the target, so the model is
strictly zero-shot. Refitting on the target would absorb part of the covariate shift for
free, which inflates transfer performance by consuming unlabelled target data that a real
deployment would not have at training time.

**`coral`** is transductive by construction: the alignment penalty needs a batch of
unlabelled target features at every optimisation step. It never sees target labels, but it
is not zero-shot, and results carry a `transductive` flag to make this explicit.

---

## Evaluation protocols

### Within-study (RQ1)

Leave-one-participant-out inside a single study. Hyperparameters are re-tuned inside every
fold, so the held-out participant influences neither fitting nor model selection.

```bash
python -m receptivity.cli.within_study --data-dir data --models lr rf xgb fcnn
```

### Cross-study (RQ2, RQ3)

Leave-one-dataset-out. Each study takes a turn as the unseen target, and *every* non-empty
subset of the remaining studies takes a turn as the source pool: 63 pools per target, 441
configurations across seven studies. Sweeping subsets rather than pooling everything
reflects the position a new deployment is actually in, where only an opportunistic handful
of prior studies is available.

Each configuration is scored by training on the source pool alone, predicting every target
participant, and taking the **median of per-participant AUCs**. Per-participant scoring
prevents differences in base receptivity rate between participants from inflating the
result.

One invocation covers one model and one target, which is the unit to parallelise over:

```bash
for target in 0 1 2 3 4 5 6; do
  python -m receptivity.cli.cross_study --data-dir data --model xgb-median --target-index "$target"
done
```

Results stream to `results/cross-study/<model>/<target>.jsonl` as each configuration
finishes, so an interrupted sweep loses at most one configuration.

### Leakage control

Every scaler, imputer and class-balance statistic is fitted on source data only and then
applied to the target. Hyperparameter search scores candidates on held-out *source* rows,
presented through the same interface a model sees at evaluation time
(`Split.as_source_fold`). Target labels are never read by anything except the final scoring
call.

Exactly one model reads unlabelled target *features*, which makes it transductive rather
than zero-shot: `coral`, whose alignment objective requires a batch of them at every step.
It is the only model for which `is_transductive` is true and the only one whose records
carry `transductive: true`; filter on that field before comparing against the zero-shot
baselines. Every other model, `masked-fcnn` included, standardises and imputes the target
with source-fitted statistics alone.

This is enforced by test rather than by convention. `test_only_coral_is_transductive` pins
the flag, and `test_prediction_does_not_depend_on_the_rest_of_the_target` checks the
underlying invariant for every model: a row's score must be identical whether or not the
other target rows are present, which no target-fitted scaler or target-neighbour imputation
can satisfy.

---

## Source balancing

Source studies differ in size by more than an order of magnitude, so a naive concatenation
lets the largest study dominate. Two schemes are used, matching the paper:

- **Study-size weights** (classical and intersection models): each row is weighted by
  `size of largest source / size of its own study`.
- **Oversampling** (feature-union neural models): each smaller study is resampled with
  replacement up to 80% of the largest study's size (`OVERSAMPLE_RATIO`).

Class imbalance is handled separately, by `pos_weight` in the BCE objective for the neural
models and `scale_pos_weight` for the imputation models.

---

## Hyperparameter search

Tree-structured Parzen Estimator search via `hyperopt`, over the grids used for the
reported runs (`receptivity/models/*.py`, `search_space`). Candidates are scored either by
5-fold stratified cross-validation inside the source pool, or, where refitting five times
per candidate is not affordable, on a single stratified holdout:

| Model | Scoring | Evaluations |
| --- | --- | --- |
| `lr`, `rf`, `xgb`, `xgb-median` | 5-fold CV | 20 |
| `fcnn` | stratified holdout | 10 |
| `masked-fcnn` | 5-fold CV | 20 |
| `xgb-knn`, `coral` | stratified holdout | 10 |

`--max-evals` and `--max-epochs` override these for quick runs.

---

## Environment notes

**OpenMP on macOS.** `xgboost` and `torch` each bundle their own copy of the OpenMP runtime.
If xgboost is imported first, subsequent torch CPU operations segfault (exit 139) with no
Python traceback. `receptivity/models/classical.py` imports torch before xgboost to fix the
order for every entry point. If you import xgboost yourself before importing anything from
this package, import torch first too.

**scikit-learn 1.8.** `LogisticRegression(penalty=...)` is deprecated in favour of
`l1_ratio`. The parameter still behaves correctly (an L1 fit is still sparse), so the code
keeps `penalty` for compatibility with the versions in `requirements.txt`; expect a
deprecation warning on 1.8 and newer.

---

## Citation

```bibtex
will be added soon
}
```
