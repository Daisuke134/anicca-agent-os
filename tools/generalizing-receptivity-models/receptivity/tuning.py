"""Bayesian hyperparameter search over source data only.

Candidates are scored without ever touching the target study: either by 5-fold
cross-validation inside the source pool, or, for the models where repeated
refitting is too expensive, on a single holdout. Both are grouped by participant
and stratified by label, so a candidate cannot be rewarded for recognising people
it will not meet again. The search itself is Tree-structured Parzen Estimator
optimisation via hyperopt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from hyperopt import STATUS_OK, Trials, fmin, space_eval, tpe

from .config import DEFAULT_SEED
from .data import Split
from .metrics import pooled_auc
from .models.base import ReceptivityModel, Validation
from .splitting import grouped_folds, grouped_holdout


@dataclass
class TuningResult:
    params: dict[str, Any]
    score: float
    n_evaluations: int


def tune(
    model_cls: type[ReceptivityModel],
    split: Split,
    max_evals: int | None = None,
    seed: int = DEFAULT_SEED,
    extra_params: dict[str, Any] | None = None,
) -> TuningResult:
    """Search ``model_cls``'s space and return the best configuration."""
    space = model_cls.search_space()
    if not space:
        return TuningResult(params=dict(extra_params or {}), score=float("nan"), n_evaluations=0)

    folds = _validation_folds(model_cls, split, seed)

    def objective(candidate: dict[str, Any]) -> dict[str, Any]:
        params = {**candidate, **(extra_params or {})}
        aucs = []
        for train_rows, valid_rows in folds:
            fold = split.as_source_fold(train_rows, valid_rows)
            model = model_cls(params=params, seed=seed).fit(fold)
            aucs.append(pooled_auc(fold.y_target, model.predict_target(fold)))
        return {"loss": -float(np.mean(aucs)), "status": STATUS_OK}

    trials = Trials()
    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=max_evals or model_cls.max_evals,
        trials=trials,
        rstate=np.random.default_rng(seed),
        show_progressbar=False,
    )
    return TuningResult(
        params={**space_eval(space, best), **(extra_params or {})},
        score=-float(min(trials.losses())),
        n_evaluations=len(trials.trials),
    )


def _validation_folds(
    model_cls: type[ReceptivityModel], split: Split, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    if model_cls.validation is Validation.CV5:
        return grouped_folds(split.y_source, split.groups_source, n_splits=5, seed=seed)
    return [
        grouped_holdout(
            split.y_source, split.groups_source, train_fraction=0.8, seed=seed
        )
    ]
