"""Within-study baseline (RQ1): leave-one-participant-out inside a single study.

This measures the performance reachable when training and test data come from the
same deployment, and provides the reference level against which all cross-study
transfer is compared. Hyperparameters are re-tuned inside every fold so the
held-out participant never influences model selection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from sklearn.model_selection import LeaveOneGroupOut

from ..config import DEFAULT_SEED
from ..data import Study, within_study_split
from ..metrics import ParticipantScores, per_participant_auc
from ..models.base import ReceptivityModel
from ..tuning import tune


@dataclass
class WithinStudyResult:
    model: str
    study: str
    scores: dict[str, Any]
    fold_params: list[dict[str, Any]] = field(default_factory=list)

    def as_record(self) -> dict[str, Any]:
        record = {"model": self.model, "study": self.study, **self.scores}
        record["fold_params"] = self.fold_params
        return record


def run_within_study(
    model_cls: type[ReceptivityModel],
    study: Study,
    seed: int = DEFAULT_SEED,
    max_evals: int | None = None,
    extra_params: dict[str, Any] | None = None,
) -> WithinStudyResult:
    """Leave-one-participant-out evaluation of ``model_cls`` on one study."""
    split = within_study_split(study)
    folds = LeaveOneGroupOut().split(
        split.X_source, split.y_source, split.groups_target
    )

    scores = ParticipantScores()
    fold_params: list[dict[str, Any]] = []

    for train_rows, test_rows in folds:
        fold = split.as_source_fold(train_rows, test_rows)
        held_out = split.groups_target[test_rows]

        if len(np.unique(fold.y_target)) < 2:
            scores.n_skipped += 1
            continue

        best = tune(
            model_cls, fold, max_evals=max_evals, seed=seed, extra_params=extra_params
        )
        model = model_cls(params=best.params, seed=seed).fit(fold)
        predictions = model.predict_target(fold)

        fold_scores = per_participant_auc(fold.y_target, predictions, held_out)
        scores.aucs.extend(fold_scores.aucs)
        scores.participants.extend(fold_scores.participants)
        scores.n_skipped += fold_scores.n_skipped
        fold_params.append(_serialisable(best.params))

    return WithinStudyResult(
        model=model_cls.name,
        study=study.name,
        scores=scores.summary(),
        fold_params=fold_params,
    )


def _serialisable(params: dict[str, Any]) -> dict[str, Any]:
    return {
        key: (list(value) if isinstance(value, tuple) else value)
        for key, value in params.items()
    }


__all__ = ["WithinStudyResult", "run_within_study"]
