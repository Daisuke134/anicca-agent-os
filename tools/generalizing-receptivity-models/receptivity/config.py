"""Shared constants for the receptivity generalization experiments."""

from __future__ import annotations

LABEL_COLUMN = "receptive"
GROUP_COLUMN = "participantId"
PLATFORM_COLUMN = "os"

RESERVED_COLUMNS = frozenset({LABEL_COLUMN, GROUP_COLUMN})

DEFAULT_SEED = 42

# Minimum size of each source study relative to the largest source study, used by
# the oversampling balancer of the feature-union neural models.
OVERSAMPLE_RATIO = 0.8

# Participants with a single observed class cannot yield an AUC and are skipped.
MIN_CLASSES_PER_PARTICIPANT = 2
