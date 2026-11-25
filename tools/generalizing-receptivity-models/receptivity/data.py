"""Study loading, feature-space alignment and source balancing.

A *study* is one parquet file of receptivity samples: one row per delivered
prompt, one column per context feature, plus a binary ``receptive`` label and a
``participantId`` group column. Studies differ in which sensors they recorded,
so the columns present vary between files. Aligning several studies onto one
matrix is therefore the central data operation here, and :class:`FeatureSpace`
enumerates the three ways the paper does it.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, replace
from enum import Enum
from glob import glob
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

from .config import (
    GROUP_COLUMN,
    LABEL_COLUMN,
    PLATFORM_COLUMN,
    RESERVED_COLUMNS,
)


class FeatureSpace(str, Enum):
    """How source and target columns are reconciled into one matrix.

    ``INTERSECTION`` keeps only sensors guaranteed to exist everywhere, so the
    matrix is complete but narrow. The two union spaces keep the full sensor
    superset and admit structural missingness, which is what the missingness-aware
    and imputation strategies operate on. They differ in whether target-only
    sensors are carried along as all-missing columns.
    """

    INTERSECTION = "intersection"
    SOURCE_UNION = "source-union"
    FULL_UNION = "full-union"


@dataclass(frozen=True)
class Study:
    """One dataset file together with its samples."""

    name: str
    path: Path
    frame: pd.DataFrame

    @property
    def platform(self) -> str:
        return "ios" if self.name.endswith("_ios") else "and"

    @property
    def label(self) -> str:
        """Name as used in the paper, e.g. ``peach-ANDROID``."""
        cohort = self.name.rsplit("_", 1)[0]
        return f"{cohort}-{'iOS' if self.platform == 'ios' else 'ANDROID'}"

    @property
    def feature_columns(self) -> list[str]:
        return sorted(set(self.frame.columns) - RESERVED_COLUMNS)

    def __len__(self) -> int:
        return len(self.frame)


@dataclass(frozen=True)
class Split:
    """Source studies and one target study aligned onto a shared feature space.

    ``X_source`` and ``X_target`` carry ``NaN`` wherever a feature is structurally
    absent, i.e. the sensor was never recorded by the study that row came from.
    ``mask_*`` records the same information as an explicit indicator so models can
    consume availability as a signal rather than having to infer it from ``NaN``.
    """

    feature_names: list[str]
    feature_space: FeatureSpace

    X_source: np.ndarray
    y_source: np.ndarray
    mask_source: np.ndarray
    study_index_source: np.ndarray
    groups_source: np.ndarray

    X_target: np.ndarray
    y_target: np.ndarray
    mask_target: np.ndarray
    groups_target: np.ndarray

    source_names: tuple[str, ...]
    target_name: str

    @property
    def n_features(self) -> int:
        return len(self.feature_names)

    def study_size_weights(self) -> np.ndarray:
        """Per-row weights that equalise the influence of each source study.

        Each row is weighted by ``size of largest source / size of its own study``,
        so a small study is not drowned out by a large one when the sources are
        concatenated.
        """
        weights = np.ones(len(self.y_source), dtype=np.float64)
        sizes = np.bincount(self.study_index_source, minlength=len(self.source_names))
        largest = sizes.max()
        for study, size in enumerate(sizes):
            if size:
                weights[self.study_index_source == study] = largest / size
        return weights

    def with_source_rows(self, rows: np.ndarray) -> "Split":
        """Same split, restricted (or resampled) to the given source rows."""
        return replace(
            self,
            X_source=self.X_source[rows],
            y_source=self.y_source[rows],
            mask_source=self.mask_source[rows],
            study_index_source=self.study_index_source[rows],
            groups_source=self.groups_source[rows],
        )

    def as_source_fold(self, train_rows: np.ndarray, valid_rows: np.ndarray) -> "Split":
        """Rebuild the split with a held-out slice of the source acting as target.

        Hyperparameter search never touches the real target, so candidate
        configurations are scored against source rows presented through the same
        interface a model sees at evaluation time.
        """
        return replace(
            self,
            X_source=self.X_source[train_rows],
            y_source=self.y_source[train_rows],
            mask_source=self.mask_source[train_rows],
            study_index_source=self.study_index_source[train_rows],
            groups_source=self.groups_source[train_rows],
            X_target=self.X_source[valid_rows],
            y_target=self.y_source[valid_rows],
            mask_target=self.mask_source[valid_rows],
            groups_target=self.groups_source[valid_rows],
        )


def load_studies(data_dir: str | Path, pattern: str = "*.parquet") -> list[Study]:
    """Load every study in ``data_dir``, sorted by filename.

    An ``os`` column is added to every study so that device platform is available
    as a feature in each feature space, including the intersection.
    """
    paths = sorted(glob(str(Path(data_dir) / pattern)))
    if not paths:
        raise FileNotFoundError(f"No study files matching {pattern!r} in {data_dir}")

    studies = []
    for path in paths:
        name = "_".join(Path(path).stem.split("_")[:2])
        frame = pd.read_parquet(path)

        # Studies store the same sensor with different widths (bool, uint8, int32,
        # float64), which would otherwise change how a feature is scaled depending
        # on which file it came from.
        frame = frame.astype(
            {col: "float64" for col in frame.columns if col not in RESERVED_COLUMNS}
        )
        frame[PLATFORM_COLUMN] = 1.0 if name.endswith("_ios") else 0.0
        frame[LABEL_COLUMN] = frame[LABEL_COLUMN].astype(int)
        studies.append(Study(name=name, path=Path(path), frame=frame))
    return studies


def source_combinations(
    studies: Sequence[Study], target: Study
) -> list[tuple[Study, ...]]:
    """Every non-empty subset of the studies other than ``target``.

    With seven studies this yields 63 source pools per target and 441 source-target
    configurations overall, matching the leave-one-dataset-out sweep in the paper.
    """
    others = [study for study in studies if study.name != target.name]
    return [
        combination
        for size in range(1, len(others) + 1)
        for combination in itertools.combinations(others, size)
    ]


def resolve_feature_names(
    sources: Sequence[Study], target: Study, feature_space: FeatureSpace
) -> list[str]:
    source_features = [set(study.feature_columns) for study in sources]
    target_features = set(target.feature_columns)

    if feature_space is FeatureSpace.INTERSECTION:
        names = set.intersection(*source_features, target_features)
    elif feature_space is FeatureSpace.SOURCE_UNION:
        names = set.union(*source_features)
    elif feature_space is FeatureSpace.FULL_UNION:
        names = set.union(*source_features, target_features)
    else:  # pragma: no cover - exhaustive over the enum
        raise ValueError(f"Unsupported feature space: {feature_space}")
    return sorted(names)


def build_split(
    sources: Sequence[Study],
    target: Study,
    feature_space: FeatureSpace,
) -> Split:
    """Align ``sources`` and ``target`` onto one matrix in ``feature_space``."""
    feature_names = resolve_feature_names(sources, target, feature_space)
    if not feature_names:
        raise ValueError(
            f"No shared features between {[s.name for s in sources]} and {target.name}"
        )

    source_blocks, source_masks, source_labels, study_index = [], [], [], []
    source_groups = []
    for index, study in enumerate(sources):
        frame = study.frame.reindex(columns=feature_names)
        source_blocks.append(frame.to_numpy(dtype=np.float32))
        source_masks.append(
            _presence_mask(feature_names, study.feature_columns, len(frame))
        )
        source_labels.append(study.frame[LABEL_COLUMN].to_numpy(dtype=np.float32))
        study_index.append(np.full(len(frame), index, dtype=int))
        # Prefixed by study, so that identically named participants in two studies
        # cannot be merged into one group by a downstream split.
        source_groups.append(
            study.name + "/" + study.frame[GROUP_COLUMN].astype(str).to_numpy()
        )

    target_frame = target.frame.reindex(columns=feature_names)
    return Split(
        feature_names=feature_names,
        feature_space=feature_space,
        X_source=np.concatenate(source_blocks, axis=0),
        y_source=np.concatenate(source_labels, axis=0),
        mask_source=np.concatenate(source_masks, axis=0),
        study_index_source=np.concatenate(study_index, axis=0),
        groups_source=np.concatenate(source_groups, axis=0),
        X_target=target_frame.to_numpy(dtype=np.float32),
        y_target=target.frame[LABEL_COLUMN].to_numpy(dtype=np.float32),
        mask_target=_presence_mask(
            feature_names, target.feature_columns, len(target_frame)
        ),
        groups_target=target.frame[GROUP_COLUMN].to_numpy(),
        source_names=tuple(study.name for study in sources),
        target_name=target.name,
    )


def within_study_split(study: Study, feature_columns: Iterable[str] | None = None) -> Split:
    """A split whose source and target are the same study.

    Used by the within-study baseline, where participant folds are carved out of
    ``X_source`` by the runner rather than coming from a separate file.
    """
    feature_names = sorted(feature_columns or study.feature_columns)
    frame = study.frame.reindex(columns=feature_names)
    X = frame.to_numpy(dtype=np.float32)
    y = study.frame[LABEL_COLUMN].to_numpy(dtype=np.float32)
    mask = _presence_mask(feature_names, study.feature_columns, len(frame))
    groups = study.frame[GROUP_COLUMN].astype(str).to_numpy()
    return Split(
        feature_names=feature_names,
        feature_space=FeatureSpace.INTERSECTION,
        X_source=X,
        y_source=y,
        mask_source=mask,
        study_index_source=np.zeros(len(frame), dtype=int),
        groups_source=groups,
        X_target=X,
        y_target=y,
        mask_target=mask,
        groups_target=groups,
        source_names=(study.name,),
        target_name=study.name,
    )


def oversampled_rows(
    study_index: np.ndarray,
    n_studies: int,
    ratio: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Row indices that raise every small study to ``ratio`` of the largest one.

    Rows are drawn with replacement, so a study contributing few samples is
    repeated rather than reweighted. A single source needs no balancing.
    """
    if not 0.0 <= ratio <= 1.0:
        raise ValueError("ratio must lie in [0, 1]")

    rows = [np.arange(len(study_index))]
    if n_studies < 2:
        return rows[0]

    sizes = np.bincount(study_index, minlength=n_studies)
    floor = math.ceil(sizes.max() * ratio)
    for study, size in enumerate(sizes):
        if 0 < size < floor:
            pool = np.flatnonzero(study_index == study)
            rows.append(rng.choice(pool, size=floor - size, replace=True))
    return np.concatenate(rows)


def _presence_mask(
    feature_names: Sequence[str], available: Sequence[str], n_rows: int
) -> np.ndarray:
    present = np.isin(feature_names, list(available)).astype(np.float32)
    return np.tile(present, (n_rows, 1))
