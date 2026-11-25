"""Deep CORAL domain-generalization baseline.

Correlation alignment assumes a uniform feature space, so it cannot consume
structural missingness directly. It is therefore paired with k-nearest-neighbour
imputation over the sensor union, following the paper. Because the alignment term
needs a batch of unlabelled target features at every step, this baseline is
transductive rather than zero-shot: it sees the target distribution (never the
target labels) while training.
"""

from __future__ import annotations

from typing import Any, ClassVar, Iterator

import numpy as np
import torch
from hyperopt import hp
from sklearn.impute import KNNImputer
from sklearn.preprocessing import StandardScaler
from torch import Tensor, nn
from torch.utils.data import DataLoader, TensorDataset

from ..data import FeatureSpace, Split
from ._torch import ARCHITECTURES, coral_loss, normalised_mlp
from .base import Validation
from .neural import UnionNeuralModel


def _reshuffling(loader: DataLoader) -> Iterator:
    """Cycle a loader, re-drawing its shuffle order on every pass.

    ``itertools.cycle`` would cache the first pass and replay that one batch
    order for the whole run, correlating each source batch with a fixed target
    batch.
    """
    while True:
        yield from loader


class _CoralNetwork(nn.Module):
    """MLP that exposes its penultimate representation for alignment."""

    def __init__(self, input_size: int, hidden_sizes, dropout: float):
        super().__init__()
        self.feature_extractor = normalised_mlp(input_size, hidden_sizes, dropout)
        self.classifier = nn.Linear(hidden_sizes[-1], 1)

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        features = self.feature_extractor(x)
        return features, self.classifier(features).squeeze(-1)


class DeepCORAL(UnionNeuralModel):
    """KNN-imputed feature union with a covariance-alignment penalty."""

    name: ClassVar[str] = "coral"
    feature_space: ClassVar[FeatureSpace] = FeatureSpace.FULL_UNION
    uses_target_features: ClassVar[bool] = True

    # KNN imputation plus per-batch alignment makes each fit expensive, so
    # candidates are scored on one holdout instead of five folds.
    validation: ClassVar[Validation] = Validation.HOLDOUT
    max_evals: ClassVar[int] = 10

    # Neighbour search is quadratic in row count, so oversampling runs after
    # imputation. Duplicating rows first would make the imputer compute distances
    # over millions of identical points for no gain.
    oversample_before_preprocessing: ClassVar[bool] = False

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        space = super().search_space()
        space["coral_weight"] = hp.choice("coral_weight", [0.5, 1.0])
        return space

    def _prepare_source(self, split: Split) -> tuple[np.ndarray, np.ndarray]:
        X = split.X_source.astype(np.float64, copy=True)

        # Columns missing across the whole source pool give the imputer nothing to
        # interpolate from, and scikit-learn drops them, which would change the
        # input width between fit and transform. Anchoring at zero keeps the
        # network topology fixed.
        self._empty_columns = np.isnan(X).all(axis=0)
        X[:, self._empty_columns] = 0.0

        self._imputer = KNNImputer(
            n_neighbors=5, weights="distance", metric="nan_euclidean"
        ).fit(X)
        X = self._imputer.transform(X)
        self._scaler = StandardScaler().fit(X)
        return self._scaler.transform(X).astype(np.float32), split.mask_source

    def _prepare_target(self, X: np.ndarray) -> np.ndarray:
        X = X.astype(np.float64, copy=True)
        X[:, self._empty_columns] = 0.0
        return self._scaler.transform(self._imputer.transform(X)).astype(np.float32)

    def _build_network(self, input_size: int) -> nn.Module:
        return _CoralNetwork(
            input_size=input_size,
            hidden_sizes=ARCHITECTURES[self.params.get("architecture", "2large")],
            dropout=float(self.params.get("dropout", 0.3)),
        )

    def _on_fit_start(self, split: Split) -> None:
        """Prepare an endless stream of unlabelled target batches for alignment."""
        target = self._prepare_target(split.X_target)
        batch_size = int(self.params.get("batch_size", 64))
        dataset = TensorDataset(torch.as_tensor(target, dtype=torch.float32))
        # Dropping the ragged tail keeps every covariance estimate equally noisy,
        # but a target smaller than one batch would then yield no batches at all
        # and silently turn the alignment term off.
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            drop_last=len(dataset) >= batch_size,
        )
        self._target_batches: Iterator = _reshuffling(loader)

    def _forward(self, X: Tensor, mask: Tensor) -> Tensor:
        _, logits = self._network(X)
        return logits

    def _extra_loss(self, X: Tensor, mask: Tensor) -> Tensor:
        target_batch = next(self._target_batches, None)
        if target_batch is None:
            return torch.zeros((), device=self.device)

        target_X = target_batch[0].to(self.device)
        if target_X.size(0) <= 1:
            return torch.zeros((), device=self.device)

        source_features, _ = self._network(X)
        target_features, _ = self._network(target_X)
        weight = float(self.params.get("coral_weight", 1.0))
        return weight * coral_loss(source_features, target_features)
