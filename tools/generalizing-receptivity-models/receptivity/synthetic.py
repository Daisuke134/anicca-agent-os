"""Synthetic studies with the same structure as the real data.

The receptivity datasets are governed by the original trials' IRB protocols and
cannot be redistributed, so the pipeline would otherwise be unrunnable outside our
institutions. These generators reproduce the properties the code depends on --
overlapping but unequal sensor sets, unequal study sizes, participant grouping and
a weakly predictable label -- so the full sweep can be exercised end to end and
the plumbing verified before pointing it at real data. The numbers it produces are
meaningless; only the shapes are.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .config import GROUP_COLUMN, LABEL_COLUMN

#: Sensor blocks, mirroring how availability varies by platform and by cohort.
#: The names are deliberately generic placeholders: only the overlap structure
#: matters here, and the real feature set is not ours to publish.
_SHARED = [f"shared_{index}" for index in range(4)]
_ANDROID_ONLY = [f"android_{index}" for index in range(3)]
_IOS_ONLY = [f"ios_{index}" for index in range(2)]
_COHORT_ONLY = {
    cohort: [f"{cohort}_only_0"] for cohort in ("ally", "peach", "optimax", "happy15")
}

STUDY_SIZES: dict[str, tuple[int, int]] = {
    # study name -> (participants, samples per participant)
    "ally_and": (12, 10),
    "ally_ios": (14, 12),
    "optimax_and": (13, 11),
    "peach_and": (15, 9),
    "peach_ios": (12, 11),
    "happy15_and": (11, 8),
    "happy15_ios": (10, 9),
}


def synthetic_study(name: str, n_participants: int, n_per_participant: int, seed: int) -> pd.DataFrame:
    """One synthetic study frame with the sensor set implied by its name."""
    rng = np.random.default_rng(seed)
    cohort, platform = name.rsplit("_", 1)

    features = list(_SHARED)
    features += _IOS_ONLY if platform == "ios" else _ANDROID_ONLY
    features += _COHORT_ONLY.get(cohort, [])

    n_rows = n_participants * n_per_participant
    frame = pd.DataFrame(
        rng.normal(size=(n_rows, len(features))).astype(np.float32), columns=features
    )
    frame[GROUP_COLUMN] = [
        f"{name}-p{index // n_per_participant:02d}" for index in range(n_rows)
    ]

    # A label that depends on the shared sensors keeps AUC above chance, so a
    # broken preprocessing step shows up as a collapse towards 0.5.
    logit = frame[_SHARED].to_numpy() @ rng.normal(size=len(_SHARED))
    probability = 1.0 / (1.0 + np.exp(-(logit - logit.mean()) / (logit.std() + 1e-9)))
    frame[LABEL_COLUMN] = (rng.random(n_rows) < probability).astype(int)
    return frame


def write_synthetic_studies(
    directory: str | Path, seed: int = 0, sizes: dict[str, tuple[int, int]] | None = None
) -> list[Path]:
    """Write a full set of synthetic studies as parquet files."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)

    paths = []
    for offset, (name, (participants, per_participant)) in enumerate(
        (sizes or STUDY_SIZES).items()
    ):
        frame = synthetic_study(name, participants, per_participant, seed + offset)
        path = directory / f"{name}_synthetic.parquet"
        frame.to_parquet(path, index=False)
        paths.append(path)
    return paths
