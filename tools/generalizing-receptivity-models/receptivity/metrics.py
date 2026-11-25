"""Per-participant scoring.

Every headline number in the paper is a median over per-participant AUCs rather
than a single pooled AUC. Pooling would let between-participant differences in
base receptivity rate inflate the score, so discrimination is measured inside
each participant and then aggregated.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import roc_auc_score

from .config import MIN_CLASSES_PER_PARTICIPANT


@dataclass
class ParticipantScores:
    aucs: list[float] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)
    n_skipped: int = 0

    @property
    def median_auc(self) -> float | None:
        return float(np.median(self.aucs)) if self.aucs else None

    @property
    def mean_auc(self) -> float | None:
        return float(np.mean(self.aucs)) if self.aucs else None

    def summary(self) -> dict[str, object]:
        return {
            "median_auc": self.median_auc,
            "mean_auc": self.mean_auc,
            "n_participants_scored": len(self.aucs),
            "n_participants_skipped": self.n_skipped,
            "participant_aucs": list(self.aucs),
            "participants": list(self.participants),
        }


def per_participant_auc(
    y_true: np.ndarray, y_score: np.ndarray, groups: np.ndarray
) -> ParticipantScores:
    """AUC within each participant, skipping participants with one class only."""
    scores = ParticipantScores()
    for participant in np.unique(groups):
        rows = groups == participant
        labels = y_true[rows]
        if len(np.unique(labels)) < MIN_CLASSES_PER_PARTICIPANT:
            scores.n_skipped += 1
            continue
        scores.aucs.append(float(roc_auc_score(labels, y_score[rows])))
        scores.participants.append(str(participant))
    return scores


def pooled_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    """Plain AUC over all rows, used to score hyperparameter candidates."""
    if len(np.unique(y_true)) < MIN_CLASSES_PER_PARTICIPANT:
        return 0.5
    return float(roc_auc_score(y_true, y_score))
