"""Within-study baseline: leave-one-participant-out inside each study (RQ1).

Example
-------
    python -m receptivity.cli.within_study --data-dir data --models lr rf xgb fcnn
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ..config import DEFAULT_SEED
from ..data import load_studies
from ..experiments import run_within_study
from ..models import BASELINE_MODELS, get_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data", help="Directory of study parquet files")
    parser.add_argument("--output-dir", default="results/within-study")
    parser.add_argument(
        "--models",
        nargs="+",
        default=list(BASELINE_MODELS),
        help=f"Models to run (default: {' '.join(BASELINE_MODELS)})",
    )
    parser.add_argument(
        "--studies", nargs="*", default=None, help="Study names to run (default: all)"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument(
        "--max-evals",
        type=int,
        default=None,
        help="Hyperopt evaluations per fold (default: the model's own setting)",
    )
    parser.add_argument(
        "--max-epochs",
        type=int,
        default=None,
        help="Cap on training epochs for the neural models, useful for quick runs",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Torch/XGBoost device, e.g. cuda or cpu (default: auto-detect)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    studies = load_studies(args.data_dir)
    if args.studies:
        studies = [study for study in studies if study.name in set(args.studies)]

    extra: dict[str, object] = {}
    if args.max_epochs:
        extra["max_epochs"] = args.max_epochs
    if args.device:
        extra["device"] = args.device

    records = []

    for name in args.models:
        model_cls = get_model(name)
        for study in studies:
            print(f"[{name}] {study.name}: {len(study)} samples", flush=True)
            result = run_within_study(
                model_cls,
                study,
                seed=args.seed,
                max_evals=args.max_evals,
                extra_params=extra,
            )
            print(f"    median AUC = {result.scores['median_auc']}", flush=True)
            records.append(result.as_record())

            path = output_dir / f"{name}_{study.name}.json"
            path.write_text(json.dumps(result.as_record(), indent=2, default=str))

    summary = pd.DataFrame(records)[
        ["model", "study", "median_auc", "mean_auc", "n_participants_scored"]
    ]
    summary.to_csv(output_dir / "summary.csv", index=False)
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
