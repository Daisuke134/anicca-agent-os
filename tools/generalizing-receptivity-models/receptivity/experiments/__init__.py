"""Evaluation protocols: within-study and cross-study."""

from .cross_study import CrossStudyResult, run_cross_study, run_configuration
from .within_study import WithinStudyResult, run_within_study

__all__ = [
    "CrossStudyResult",
    "WithinStudyResult",
    "run_configuration",
    "run_cross_study",
    "run_within_study",
]
