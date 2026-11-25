"""Cross-study evaluation (RQ2, RQ3): leave one dataset out.

Each study takes a turn as the unseen target, and every non-empty subset of the
remaining studies takes a turn as the source pool. With seven studies that is 63
source pools per target and 441 configurations in total. Sweeping subsets rather
than pooling everything reflects the situation a new deployment is actually in,
where only an opportunistic handful of prior studies is available.

A configuration is scored by training on the source pool alone, predicting every
target participant, and taking the median of the per-participant AUCs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Sequence

from ..config import DEFAULT_SEED
from ..data import Study, build_split, source_combinations
from ..metrics import per_participant_auc
from ..models.base import ReceptivityModel
from ..tuning import tune


@dataclass
class CrossStudyResult:
    model: str
    target: str
    sources: tuple[str, ...]
    n_features: int
    feature_space: str = ""
    transductive: bool = False
    scores: dict[str, Any] = field(default_factory=dict)
    params: dict[str, Any] = field(default_factory=dict)
    failure: str | None = None

    def as_record(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "target": self.target,
            "sources": "+".join(self.sources),
            "n_sources": len(self.sources),
            "n_features": self.n_features,
            "feature_space": self.feature_space,
            "transductive": self.transductive,
            "params": _serialisable(self.params),
            "failure": self.failure,
            **self.scores,
        }


def run_configuration(
    model_cls: type[ReceptivityModel],
    sources: Sequence[Study],
    target: Study,
    seed: int = DEFAULT_SEED,
    max_evals: int | None = None,
    extra_params: dict[str, Any] | None = None,
) -> CrossStudyResult:
    """Train on ``sources``, evaluate on every participant of ``target``."""
    split = build_split(sources, target, model_cls.feature_space)

    best = tune(
        model_cls, split, max_evals=max_evals, seed=seed, extra_params=extra_params
    )
    model = model_cls(params=best.params, seed=seed).fit(split)
    scores = per_participant_auc(
        split.y_target, model.predict_target(split), split.groups_target
    )

    return CrossStudyResult(
        model=model_cls.name,
        target=target.name,
        sources=tuple(study.name for study in sources),
        n_features=split.n_features,
        feature_space=model_cls.feature_space.value,
        transductive=model.is_transductive,
        scores=scores.summary(),
        params=best.params,
    )


def run_cross_study(
    model_cls: type[ReceptivityModel],
    studies: Sequence[Study],
    target: Study,
    seed: int = DEFAULT_SEED,
    max_evals: int | None = None,
    extra_params: dict[str, Any] | None = None,
    max_configurations: int | None = None,
    on_result: Callable[[CrossStudyResult], None] | None = None,
) -> Iterator[CrossStudyResult]:
    """Yield one result per source pool for the given target.

    Results are yielded as they complete so a long sweep can be checkpointed
    incrementally. A configuration that fails, most often because the feature
    intersection between a source pool and the target is empty, is recorded with
    its error rather than aborting the sweep.
    """
    combinations = source_combinations(studies, target)
    if max_configurations is not None:
        combinations = combinations[:max_configurations]

    for sources in combinations:
        try:
            result = run_configuration(
                model_cls,
                sources,
                target,
                seed=seed,
                max_evals=max_evals,
                extra_params=extra_params,
            )
        except Exception as error:  # noqa: BLE001 - one bad pool must not stop the sweep
            result = CrossStudyResult(
                model=model_cls.name,
                target=target.name,
                sources=tuple(study.name for study in sources),
                n_features=0,
                feature_space=model_cls.feature_space.value,
                transductive=model_cls.uses_target_features,
                failure=f"{type(error).__name__}: {error}",
            )
        if on_result is not None:
            on_result(result)
        yield result


def _serialisable(params: dict[str, Any]) -> dict[str, Any]:
    return {
        key: (list(value) if isinstance(value, tuple) else value)
        for key, value in params.items()
    }


__all__ = ["CrossStudyResult", "run_configuration", "run_cross_study"]
