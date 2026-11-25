"""Fully connected neural baselines.

:class:`FCNN` is the intersection baseline: a plain MLP on the sensors every study
shares. :class:`MaskedFCNN` is the missingness-aware union model, which keeps the
full sensor superset and feeds the availability pattern to the network as an
explicit input.
"""

from __future__ import annotations

import copy
from typing import Any, ClassVar

import numpy as np
import torch
from hyperopt import hp
from sklearn.preprocessing import StandardScaler
from torch import Tensor, nn
from torch.optim.lr_scheduler import ReduceLROnPlateau
from torch.utils.data import DataLoader, TensorDataset

from ..config import OVERSAMPLE_RATIO
from ..data import FeatureSpace, Split, oversampled_rows
from ..metrics import pooled_auc
from ..splitting import grouped_holdout
from .base import ReceptivityModel, Validation
from ._torch import (
    ARCHITECTURES,
    normalised_mlp,
    positive_class_weight,
    resolve_device,
    set_seed,
)


class _PlainMLP(nn.Module):
    def __init__(self, input_size: int, n_layers: int, width: int, dropout: float):
        super().__init__()
        layers: list[nn.Module] = []
        in_size = input_size
        for _ in range(n_layers):
            layers += [nn.Linear(in_size, width), nn.ReLU(), nn.Dropout(dropout)]
            in_size = width
        layers.append(nn.Linear(in_size, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x: Tensor) -> Tensor:
        return self.network(x).squeeze(-1)


class FCNN(ReceptivityModel):
    """MLP on the feature intersection, tuned against a stratified holdout.

    Repeated inner cross-validation is too costly for a network, so candidate
    configurations are scored on a single held-out slice of the source pool. The
    same mechanism drives early stopping during the final fit, monitoring AUC
    rather than loss because AUC is the reported metric.
    """

    name: ClassVar[str] = "fcnn"
    feature_space: ClassVar[FeatureSpace] = FeatureSpace.INTERSECTION
    validation: ClassVar[Validation] = Validation.HOLDOUT
    max_evals: ClassVar[int] = 10

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "n_layers": hp.quniform("n_layers", 1, 4, 1),
            "width": hp.choice("width", [16, 32, 64, 128, 256]),
            "dropout": hp.uniform("dropout", 0.1, 0.5),
            "learning_rate": hp.loguniform(
                "learning_rate", np.log(1e-4), np.log(1e-2)
            ),
            "batch_size": hp.choice("batch_size", [32, 64, 128, 256]),
        }

    def fit(self, split: Split) -> "FCNN":
        set_seed(self.seed)
        self.device = resolve_device(self.params.get("device"))

        weights = split.study_size_weights()
        train_rows, valid_rows = grouped_holdout(
            split.y_source,
            split.groups_source,
            train_fraction=0.9,
            seed=self.seed,
        )

        self._scaler = StandardScaler().fit(split.X_source[train_rows])
        X_train = self._scaler.transform(split.X_source[train_rows])
        X_valid = self._scaler.transform(split.X_source[valid_rows])
        y_train = split.y_source[train_rows]
        y_valid = split.y_source[valid_rows]

        loader = DataLoader(
            TensorDataset(
                torch.as_tensor(X_train, dtype=torch.float32),
                torch.as_tensor(y_train, dtype=torch.float32),
                torch.as_tensor(weights[train_rows], dtype=torch.float32),
            ),
            batch_size=int(self.params.get("batch_size", 64)),
            shuffle=True,
        )
        valid_tensor = torch.as_tensor(X_valid, dtype=torch.float32).to(self.device)

        self._network = _PlainMLP(
            input_size=split.n_features,
            n_layers=int(self.params.get("n_layers", 2)),
            width=int(self.params.get("width", 64)),
            dropout=float(self.params.get("dropout", 0.2)),
        ).to(self.device)

        criterion = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor(
                positive_class_weight(y_train), device=self.device
            ),
            reduction="none",
        )
        optimizer = torch.optim.Adam(
            self._network.parameters(),
            lr=float(self.params.get("learning_rate", 1e-3)),
        )
        scheduler = ReduceLROnPlateau(optimizer, mode="max", factor=0.5, patience=2)

        best_auc, best_state, stale = -np.inf, None, 0
        for _ in range(int(self.params.get("max_epochs", 150))):
            self._network.train()
            for batch_X, batch_y, batch_w in loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                batch_w = batch_w.to(self.device)
                optimizer.zero_grad()
                loss = (criterion(self._network(batch_X), batch_y) * batch_w).mean()
                loss.backward()
                optimizer.step()

            self._network.eval()
            with torch.no_grad():
                scores = torch.sigmoid(self._network(valid_tensor)).cpu().numpy()
            auc = pooled_auc(y_valid, scores)
            scheduler.step(auc)

            if auc > best_auc:
                best_auc, stale = auc, 0
                best_state = copy.deepcopy(self._network.state_dict())
            else:
                stale += 1
                if stale >= int(self.params.get("early_stopping_patience", 5)):
                    break

        if best_state is not None:
            self._network.load_state_dict(best_state)
        self.validation_auc_ = float(best_auc)
        return self

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        self._network.eval()
        tensor = torch.as_tensor(
            self._scaler.transform(X), dtype=torch.float32, device=self.device
        )
        with torch.no_grad():
            return torch.sigmoid(self._network(tensor)).cpu().numpy()


class UnionNeuralModel(ReceptivityModel):
    """Base class for the neural models that train on the full sensor superset.

    Both subclasses share the same optimisation recipe -- hold out whole
    participants for early stopping on validation loss, oversample the smaller
    source studies within what remains, and train a layer-normalised MLP with a
    class-rebalanced BCE objective. They differ in how absent sensors are handled
    and in the loss they minimise, which is what the overridable hooks below
    express.

    Oversampling deliberately happens after the holdout is carved off. Drawing the
    holdout from an already-oversampled pool would put exact duplicates of training
    rows into it, so early stopping and the learning-rate schedule would be reacting
    to memorisation rather than to generalisation.
    """

    feature_space: ClassVar[FeatureSpace] = FeatureSpace.FULL_UNION
    validation: ClassVar[Validation] = Validation.CV5
    max_evals: ClassVar[int] = 20

    #: Whether the training rows are oversampled before preprocessing statistics
    #: are fitted, which lets duplicates from the smaller studies pull those
    #: statistics towards themselves. Subclasses whose preprocessing cost grows
    #: with row count set this to false and oversample afterwards instead.
    oversample_before_preprocessing: ClassVar[bool] = True

    @classmethod
    def search_space(cls) -> dict[str, Any]:
        return {
            "architecture": hp.choice("architecture", list(ARCHITECTURES)),
            "train_ratio": hp.choice("train_ratio", [0.7, 0.8]),
            "learning_rate": hp.choice("learning_rate", [0.01, 0.001]),
            "dropout": hp.choice("dropout", [0.1, 0.3, 0.5]),
            "batch_size": hp.choice("batch_size", [32, 64, 128]),
            "scheduler_factor": hp.choice("scheduler_factor", [0.1, 0.3, 0.5]),
            "scheduler_patience": hp.choice("scheduler_patience", [10, 20, 25]),
            "early_stopping_patience": hp.choice(
                "early_stopping_patience", [10, 20, 25]
            ),
        }

    # --- hooks ------------------------------------------------------------
    def _prepare_source(self, split: Split) -> tuple[np.ndarray, np.ndarray]:
        """Return the scaled source matrix and its availability mask."""
        raise NotImplementedError

    def _prepare_target(self, X: np.ndarray) -> np.ndarray:
        """Scale a target matrix with statistics established during ``fit``."""
        raise NotImplementedError

    def _build_network(self, input_size: int) -> nn.Module:
        raise NotImplementedError

    def _forward(self, X: Tensor, mask: Tensor) -> Tensor:
        raise NotImplementedError

    def _extra_loss(self, X: Tensor, mask: Tensor) -> Tensor:
        """Additional term added to the classification loss during training."""
        return torch.zeros((), device=self.device)

    def _on_fit_start(self, split: Split) -> None:
        return None

    # --- training ---------------------------------------------------------
    def fit(self, split: Split) -> "UnionNeuralModel":
        set_seed(self.seed)
        self.device = resolve_device(self.params.get("device"))
        rng = np.random.default_rng(self.seed)

        train_rows, valid_rows = grouped_holdout(
            split.y_source,
            split.groups_source,
            train_fraction=float(self.params.get("train_ratio", 0.8)),
            seed=self.seed,
        )
        # Positions within the training rows, so no duplicate can reach the holdout.
        resampled = oversampled_rows(
            split.study_index_source[train_rows],
            n_studies=len(split.source_names),
            ratio=float(self.params.get("oversample_ratio", OVERSAMPLE_RATIO)),
            rng=rng,
        )

        if self.oversample_before_preprocessing:
            train_split = split.with_source_rows(train_rows[resampled])
            X_train, mask_train = self._prepare_source(train_split)
            y_train = train_split.y_source
        else:
            train_split = split.with_source_rows(train_rows)
            X_train, mask_train = self._prepare_source(train_split)
            X_train, mask_train = X_train[resampled], mask_train[resampled]
            y_train = train_split.y_source[resampled]

        # Preprocessing is fitted on training rows only, so the holdout is scaled
        # and imputed exactly as an unseen study would be.
        X_valid = self._prepare_target(split.X_source[valid_rows])
        mask_valid = split.mask_source[valid_rows]
        y_valid = split.y_source[valid_rows]

        self._network = self._build_network(split.n_features).to(self.device)
        self._on_fit_start(split)

        criterion = nn.BCEWithLogitsLoss(
            pos_weight=torch.tensor(
                positive_class_weight(y_train), device=self.device
            )
        )
        optimizer = torch.optim.Adam(
            self._network.parameters(),
            lr=float(self.params.get("learning_rate", 1e-3)),
            weight_decay=1e-5,
        )
        scheduler = ReduceLROnPlateau(
            optimizer,
            mode="min",
            factor=float(self.params.get("scheduler_factor", 0.5)),
            patience=int(self.params.get("scheduler_patience", 10)),
        )

        batch_size = int(self.params.get("batch_size", 64))
        train_loader = self._loader(
            X_train, mask_train, y_train, batch_size, shuffle=True
        )
        valid_loader = self._loader(
            X_valid, mask_valid, y_valid, batch_size, shuffle=False
        )

        best_loss, best_state, stale = np.inf, None, 0
        patience = int(self.params.get("early_stopping_patience", 20))
        for _ in range(int(self.params.get("max_epochs", 1000))):
            self._network.train()
            for batch_X, batch_mask, batch_y in train_loader:
                if batch_X.size(0) <= 1:
                    continue
                batch_X = batch_X.to(self.device)
                batch_mask = batch_mask.to(self.device)
                batch_y = batch_y.to(self.device)
                optimizer.zero_grad()
                logits = self._forward(batch_X, batch_mask)
                loss = criterion(logits, batch_y) + self._extra_loss(
                    batch_X, batch_mask
                )
                loss.backward()
                optimizer.step()

            validation_loss = self._validation_loss(valid_loader, criterion)
            scheduler.step(validation_loss)

            if validation_loss < best_loss:
                best_loss, stale = validation_loss, 0
                best_state = copy.deepcopy(self._network.state_dict())
            else:
                stale += 1
                if stale >= patience:
                    break

        if best_state is not None:
            self._network.load_state_dict(best_state)
        self.validation_loss_ = float(best_loss)
        return self

    def _validation_loss(self, loader: DataLoader, criterion: nn.Module) -> float:
        self._network.eval()
        total, batches = 0.0, 0
        with torch.no_grad():
            for batch_X, batch_mask, batch_y in loader:
                if batch_X.size(0) <= 1:
                    continue
                batch_X = batch_X.to(self.device)
                batch_mask = batch_mask.to(self.device)
                batch_y = batch_y.to(self.device)
                total += criterion(
                    self._forward(batch_X, batch_mask), batch_y
                ).item()
                batches += 1
        return total / max(1, batches)

    def _loader(
        self,
        X: np.ndarray,
        mask: np.ndarray,
        y: np.ndarray,
        batch_size: int,
        shuffle: bool,
    ) -> DataLoader:
        dataset = TensorDataset(
            torch.as_tensor(X, dtype=torch.float32),
            torch.as_tensor(mask, dtype=torch.float32),
            torch.as_tensor(y, dtype=torch.float32),
        )
        return DataLoader(dataset, batch_size=batch_size, shuffle=shuffle)

    def predict_proba(self, X: np.ndarray, mask: np.ndarray) -> np.ndarray:
        self._network.eval()
        X_tensor = torch.as_tensor(
            self._prepare_target(X), dtype=torch.float32, device=self.device
        )
        mask_tensor = torch.as_tensor(mask, dtype=torch.float32, device=self.device)
        with torch.no_grad():
            return torch.sigmoid(self._forward(X_tensor, mask_tensor)).cpu().numpy()


class _MaskedMLP(nn.Module):
    """MLP whose input is the gated feature vector concatenated with its mask."""

    def __init__(self, input_size: int, hidden_sizes, dropout: float):
        super().__init__()
        self.body = normalised_mlp(input_size * 2, hidden_sizes, dropout)
        self.head = nn.Linear(hidden_sizes[-1], 1)

    def forward(self, x: Tensor, mask: Tensor) -> Tensor:
        gated = torch.cat([x * mask, mask], dim=1)
        return self.head(self.body(gated)).squeeze(-1)


class MaskedFCNN(UnionNeuralModel):
    """Missingness-aware FCNN over the full sensor union.

    Standardisation statistics are computed over observed values only, so a sensor
    that just some studies recorded is scaled by its own mean and variance rather
    than by a mixture of real readings and filler. Absent entries are then set to
    zero and gated by the mask, which keeps them at zero and out of the first
    layer. The mask is concatenated to the gated vector, which is what lets the
    network tell "sensor absent" apart from "sensor present and happens to be zero"
    and condition its decision boundary on which modalities a study recorded.

    Standardisation is fitted on source rows only and reused unchanged for the
    target, so the model is strictly zero-shot: nothing about the target
    distribution, labelled or not, reaches training or inference.
    """

    name: ClassVar[str] = "masked-fcnn"

    def _prepare_source(self, split: Split) -> tuple[np.ndarray, np.ndarray]:
        # StandardScaler ignores NaN when fitting and preserves it when
        # transforming, which is what keeps structurally absent entries out of the
        # statistics. Columns absent from every source row have no statistics at
        # all; they are left untouched and zeroed below.
        scaler = StandardScaler().fit(split.X_source)
        scaler.mean_ = np.nan_to_num(scaler.mean_, nan=0.0)
        scaler.scale_ = np.where(
            np.isfinite(scaler.scale_) & (scaler.scale_ > 0), scaler.scale_, 1.0
        )
        self._source_scaler = scaler
        return self._scale(split.X_source), split.mask_source

    def _prepare_target(self, X: np.ndarray) -> np.ndarray:
        return self._scale(X)

    def _scale(self, X: np.ndarray) -> np.ndarray:
        return np.nan_to_num(self._source_scaler.transform(X), nan=0.0)

    def _build_network(self, input_size: int) -> nn.Module:
        return _MaskedMLP(
            input_size=input_size,
            hidden_sizes=ARCHITECTURES[self.params.get("architecture", "2large")],
            dropout=float(self.params.get("dropout", 0.3)),
        )

    def _forward(self, X: Tensor, mask: Tensor) -> Tensor:
        return self._network(X, mask)
