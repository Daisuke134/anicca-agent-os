"""Participant-grouped, label-stratified partitions of the source pool.

Every internal partition -- hyperparameter search folds and the neural models'
early-stopping holdout -- keeps each participant wholly on one side. Splitting on
rows instead would let a participant appear in both halves, and because receptivity
is strongly person-specific a model can then score well by recognising the person
rather than the situation. That inflates internal scores and biases selection
towards configurations which memorise, none of which survives the move to an unseen
cohort.

Grouping is enforced here rather than at each call site so that no model can opt
out of it by accident.
"""

from __future__ import annotations

import numpy as np
from sklearn.model_selection import (
    GroupShuffleSplit,
    StratifiedGroupKFold,
    train_test_split,
)

__all__ = ["grouped_folds", "grouped_holdout"]


def grouped_folds(
    y: np.ndarray, groups: np.ndarray, n_splits: int, seed: int
) -> list[tuple[np.ndarray, np.ndarray]]:
    """``n_splits`` participant-disjoint folds, stratified by label where possible."""
    n_groups = len(np.unique(groups))
    if n_groups < n_splits or len(np.unique(y)) < 2:
        return [grouped_holdout(y, groups, train_fraction=0.8, seed=seed)]

    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    return list(splitter.split(np.arange(len(y)), y, groups=groups))


def grouped_holdout(
    y: np.ndarray, groups: np.ndarray, train_fraction: float, seed: int
) -> tuple[np.ndarray, np.ndarray]:
    """One participant-disjoint holdout of roughly ``1 - train_fraction`` of the rows.

    Falls back progressively when the pool is too small to honour every
    constraint: stratified and grouped, then grouped only, then stratified only.
    The last case can only arise when there is a single participant, where no
    grouped split exists at all.
    """
    rows = np.arange(len(y))
    n_groups = len(np.unique(groups))

    if n_groups > 1:
        # A k-fold with k = 1/(1 - train_fraction) yields a first fold of about the
        # requested size while also balancing labels, which GroupShuffleSplit
        # cannot do.
        n_splits = int(round(1.0 / max(1e-9, 1.0 - train_fraction)))
        n_splits = max(2, min(n_splits, n_groups))
        if len(np.unique(y)) > 1:
            try:
                splitter = StratifiedGroupKFold(
                    n_splits=n_splits, shuffle=True, random_state=seed
                )
                return next(iter(splitter.split(rows, y, groups=groups)))
            except ValueError:
                pass
        try:
            splitter = GroupShuffleSplit(
                n_splits=1, train_size=train_fraction, random_state=seed
            )
            return next(iter(splitter.split(rows, y, groups=groups)))
        except ValueError:
            pass

    stratify = y if len(np.unique(y)) > 1 else None
    try:
        return train_test_split(
            rows, train_size=train_fraction, stratify=stratify, random_state=seed
        )
    except ValueError:
        return train_test_split(rows, train_size=train_fraction, random_state=seed)
