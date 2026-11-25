"""Model registry.

The six model families evaluated in the paper, plus the two feature-union
imputation variants of the boosted-tree model.
"""

from __future__ import annotations

from .base import ReceptivityModel, Validation
from .classical import (
    ImputedXGBoost,
    KNNImputedXGBoost,
    LogisticRegressionModel,
    MedianImputedXGBoost,
    RandomForestModel,
    XGBoostModel,
)
from .coral import DeepCORAL
from .neural import FCNN, MaskedFCNN, UnionNeuralModel

#: Within-study and feature-intersection baselines (RQ1, RQ2).
BASELINE_MODELS: dict[str, type[ReceptivityModel]] = {
    LogisticRegressionModel.name: LogisticRegressionModel,
    RandomForestModel.name: RandomForestModel,
    XGBoostModel.name: XGBoostModel,
    FCNN.name: FCNN,
}

#: Feature-union strategies that handle structural missingness (RQ3).
UNION_MODELS: dict[str, type[ReceptivityModel]] = {
    MedianImputedXGBoost.name: MedianImputedXGBoost,
    KNNImputedXGBoost.name: KNNImputedXGBoost,
    MaskedFCNN.name: MaskedFCNN,
    DeepCORAL.name: DeepCORAL,
}

MODELS: dict[str, type[ReceptivityModel]] = {**BASELINE_MODELS, **UNION_MODELS}


def get_model(name: str) -> type[ReceptivityModel]:
    try:
        return MODELS[name]
    except KeyError:
        raise KeyError(
            f"Unknown model {name!r}. Available: {', '.join(sorted(MODELS))}"
        ) from None


__all__ = [
    "BASELINE_MODELS",
    "DeepCORAL",
    "FCNN",
    "ImputedXGBoost",
    "KNNImputedXGBoost",
    "LogisticRegressionModel",
    "MODELS",
    "MaskedFCNN",
    "MedianImputedXGBoost",
    "RandomForestModel",
    "ReceptivityModel",
    "UNION_MODELS",
    "UnionNeuralModel",
    "Validation",
    "XGBoostModel",
    "get_model",
]
