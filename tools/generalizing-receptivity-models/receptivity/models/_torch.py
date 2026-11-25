"""Small PyTorch helpers shared by the neural models."""

from __future__ import annotations

import random
from typing import Sequence

import numpy as np
import torch
from torch import Tensor, nn

ARCHITECTURES: dict[str, tuple[int, ...]] = {
    "2small": (32, 16),
    "2large": (64, 32),
    "3small": (64, 32, 16),
}


def resolve_device(preferred: str | None = None) -> torch.device:
    if preferred:
        return torch.device(preferred)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def normalised_mlp(
    input_size: int, hidden_sizes: Sequence[int], dropout: float
) -> nn.Sequential:
    """Dense stack with layer normalisation, as used by the feature-union models.

    LayerNorm rather than BatchNorm because batches mix studies with different
    sensor availability, which makes batch statistics unstable across domains.
    """
    layers: list[nn.Module] = []
    in_size = input_size
    for hidden_size in hidden_sizes:
        layers += [
            nn.Linear(in_size, hidden_size),
            nn.LayerNorm(hidden_size),
            nn.ReLU(),
            nn.Dropout(dropout),
        ]
        in_size = hidden_size
    return nn.Sequential(*layers)


def positive_class_weight(y: np.ndarray) -> float:
    """Ratio of negatives to positives, used to rebalance the loss."""
    positives = float((y == 1).sum())
    negatives = float((y == 0).sum())
    return negatives / max(1.0, positives)


def coral_loss(source: Tensor, target: Tensor) -> Tensor:
    """Squared difference between the feature covariances of two domains.

    This is the Deep CORAL alignment penalty: matching second-order statistics of
    the learned representation pushes the network towards features whose
    covariance structure is the same in the source pool and the target study.
    """
    dim = source.size(1)
    cov_source = _covariance(source)
    cov_target = _covariance(target)
    return (cov_source - cov_target).pow(2).sum() / (4 * dim * dim)


def _covariance(features: Tensor) -> Tensor:
    n = features.size(0)
    total = features.sum(dim=0, keepdim=True)
    return (features.t() @ features - (total.t() @ total) / n) / (n - 1)
