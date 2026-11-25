"""End-to-end checks on synthetic studies.

These tests do not validate the scientific claims of the paper. They check that
every model trains and produces scores, that hyperparameter search never sees the
target study, and that the feature-space and missingness bookkeeping is correct.
"""

from __future__ import annotations

import numpy as np
import pytest

from receptivity.data import (
    FeatureSpace,
    build_split,
    load_studies,
    source_combinations,
)
from receptivity.experiments import run_configuration, run_within_study
from receptivity.metrics import per_participant_auc
from receptivity.models import MODELS, get_model
from receptivity.synthetic import write_synthetic_studies

FAST_PARAMS = {"max_epochs": 2}


@pytest.fixture(scope="module")
def studies(tmp_path_factory):
    directory = tmp_path_factory.mktemp("synthetic-data")
    write_synthetic_studies(directory, seed=7)
    return load_studies(directory)


def test_seven_studies_and_441_configurations(studies):
    assert len(studies) == 7
    total = sum(len(source_combinations(studies, target)) for target in studies)
    assert total == 7 * 63 == 441


def test_intersection_is_narrower_than_union(studies):
    sources, target = studies[:3], studies[3]
    intersection = build_split(sources, target, FeatureSpace.INTERSECTION)
    source_union = build_split(sources, target, FeatureSpace.SOURCE_UNION)
    full_union = build_split(sources, target, FeatureSpace.FULL_UNION)

    assert set(intersection.feature_names) < set(full_union.feature_names)
    assert set(source_union.feature_names) <= set(full_union.feature_names)
    assert not np.isnan(intersection.X_source).any()
    assert np.isnan(full_union.X_source).any()


def test_mask_marks_exactly_the_absent_features(studies):
    sources, target = studies[:2], studies[2]
    split = build_split(sources, target, FeatureSpace.FULL_UNION)

    assert np.array_equal(split.mask_source == 0, np.isnan(split.X_source))
    assert np.array_equal(split.mask_target == 0, np.isnan(split.X_target))


def test_study_size_weights_equalise_source_contributions(studies):
    sources, target = studies[:3], studies[3]
    split = build_split(sources, target, FeatureSpace.INTERSECTION)
    weights = split.study_size_weights()

    totals = {
        index: weights[split.study_index_source == index].sum()
        for index in range(len(sources))
    }
    assert np.allclose(list(totals.values()), max(totals.values()))


def test_source_fold_never_leaks_the_target(studies):
    sources, target = studies[:2], studies[2]
    split = build_split(sources, target, FeatureSpace.INTERSECTION)
    fold = split.as_source_fold(np.arange(10), np.arange(10, 20))

    assert len(fold.y_source) == 10
    assert len(fold.y_target) == 10
    assert fold.X_target.shape[0] == 10


@pytest.mark.parametrize("name", sorted(MODELS))
def test_every_model_trains_and_scores(studies, name):
    model_cls = get_model(name)
    result = run_configuration(
        model_cls,
        sources=studies[:2],
        target=studies[2],
        max_evals=2,
        extra_params=FAST_PARAMS,
    )

    assert result.failure is None
    assert result.scores["n_participants_scored"] > 0
    assert 0.0 <= result.scores["median_auc"] <= 1.0


def test_only_coral_is_transductive():
    """Deep CORAL's objective needs unlabelled target features; nothing else may."""
    for name in sorted(MODELS):
        expected = name == "coral"
        assert get_model(name)().is_transductive is expected, name


@pytest.mark.parametrize("name", sorted(MODELS))
def test_prediction_does_not_depend_on_the_rest_of_the_target(studies, name):
    """A row's score must be identical whether or not its neighbours are present.

    Any statistic fitted on the target at inference time -- a rescaling, a
    recentring, an imputation drawing on target neighbours -- would make a row's
    prediction move when unrelated rows are withheld. This is the sharpest cheap
    test for transductive contamination, and it must hold even for `coral`, which
    is allowed to align on the target during training but not to adapt at
    inference.
    """
    sources, target = studies[:2], studies[2]
    model_cls = get_model(name)
    split = build_split(sources, target, model_cls.feature_space)
    model = model_cls(params=FAST_PARAMS).fit(split)

    subset = slice(0, max(2, split.X_target.shape[0] // 4))
    full = model.predict_target(split)
    partial = model.predict_proba(split.X_target[subset], split.mask_target[subset])

    np.testing.assert_allclose(partial, full[subset], atol=1e-6)


def test_within_study_runs(studies):
    result = run_within_study(
        get_model("lr"), studies[0], max_evals=2, extra_params=None
    )
    assert result.scores["n_participants_scored"] > 0


def test_per_participant_auc_skips_single_class_participants():
    y = np.array([1, 1, 0, 1])
    scores = np.array([0.9, 0.8, 0.2, 0.7])
    groups = np.array(["a", "a", "b", "b"])

    result = per_participant_auc(y, scores, groups)
    assert result.n_skipped == 1
    assert len(result.aucs) == 1
