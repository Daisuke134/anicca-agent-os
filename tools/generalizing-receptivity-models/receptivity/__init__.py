"""Cross-study generalization of receptivity models for JITAIs.

Reference implementation for the models and evaluation protocols reported in
"Evaluating Cross-Study Generalization of Receptivity Models for Just-in-Time
Adaptive Interventions".
"""

from __future__ import annotations

from .data import FeatureSpace, Split, Study, build_split, load_studies, source_combinations
from .metrics import ParticipantScores, per_participant_auc, pooled_auc
from .models import MODELS, get_model
from .tuning import tune

__version__ = "1.0.0"

__all__ = [
    "FeatureSpace",
    "MODELS",
    "ParticipantScores",
    "Split",
    "Study",
    "__version__",
    "build_split",
    "get_model",
    "load_studies",
    "per_participant_auc",
    "pooled_auc",
    "source_combinations",
    "tune",
]
