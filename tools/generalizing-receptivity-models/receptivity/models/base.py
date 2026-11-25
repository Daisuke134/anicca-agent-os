"""Common interface shared by every receptivity model."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, ClassVar

import numpy as np

from ..config import DEFAULT_SEED
from ..data import FeatureSpace, Split


class Validation(str, Enum):
    """How the tuner scores a candidate configuration on source data."""

    CV5 = "cv5"
    HOLDOUT = "holdout"


class ReceptivityModel(ABC):
    """A receptivity strategy: preprocessing, architecture and fitting in one unit.

    Preprocessing lives inside the model rather than in the runner because the
    strategies differ precisely in how they treat structural missingness --
    imputing it, masking it, or avoiding it by narrowing the feature space. Each
    model is therefore responsible for fitting its own scalers and imputers on
    source data only, which is what keeps the target study out of training.
    """

    name: ClassVar[str]
    feature_space: ClassVar[FeatureSpace]
    validation: ClassVar[Validation] = Validation.CV5
    max_evals: ClassVar[int] = 20

    #: Whether this model always consumes unlabelled target features. Deep CORAL
    #: does, which makes it transductive rather than zero-shot.
    uses_target_features: ClassVar[bool] = False

    def __init__(self, params: dict[str, Any] | None = None, seed: int = DEFAULT_SEED):
        self.params = dict(params or {})
        self.seed = seed

    @property
    def is_transductive(self) -> bool:
        """Whether *this configuration* consumes unlabelled target data.

        Distinct from :attr:`uses_target_features` because a model can be
        transductive only under some parameter settings, and a result is not
        comparable against zero-shot baselines when it is.
        """
        return self.uses_target_features

    @classmethod
    @abstractmethod
    def search_space(cls) -> dict[str, Any]:
        """Hyperopt search space, taken from the grids used in the paper's runs."""

    @abstractmethod
    def fit(self, split: Split) -> "ReceptivityModel":
        """Train on ``split``'s source rows."""

    @abstractmethod
    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        """Positive-class probability for each row of ``X``."""

    def predict_target(self, split: Split) -> np.ndarray:
        return self.predict_proba(split.X_target, split.mask_target)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"{type(self).__name__}({self.params})"
