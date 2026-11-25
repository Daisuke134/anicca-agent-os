"""Cross-study sweep: one target study against every source pool (RQ2, RQ3).

One invocation covers one target and one model, which is the unit to parallelise
over (seven targets per model, run as separate jobs). Results are written
incrementally so a long sweep can be resumed.

Examples
--------
    # Feature-intersection baseline for target 0
    python -m receptivity.cli.cross_study --target-index 0 --model xgb

    # Feature-union strategies for the same target
    python -m receptivity.cli.cross_study --target-index 0 --model masked-fcnn
    python -m receptivity.cli.cross_study --target-index 0 --model coral
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from ..config import DEFAULT_SEED
from ..data import load_studies
from ..experiments import run_cross_study
from ..models import MODELS, get_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output-dir", default="results/cross-study")
    parser.add_argument("--model", required=True, choices=sorted(MODELS))
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target-index", type=int, help="Index into the sorted study list")
    group.add_argument("--target", help="Study name to hold out")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-evals", type=int, default=None)
    parser.add_argument("--max-epochs", type=int, default=None)
    parser.add_argument(
        "--max-configurations",
        type=int,
        default=None,
        help="Run only the first N source pools (default: all 63)",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Torch/XGBoost device, e.g. cuda or cpu (default: auto-detect)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    studies = load_studies(args.data_dir)

    if args.target is not None:
        matches = [study for study in studies if study.name == args.target]
        if not matches:
            raise SystemExit(f"No study named {args.target!r} in {args.data_dir}")
        target = matches[0]
    else:
        if not 0 <= args.target_index < len(studies):
            raise SystemExit(
                f"--target-index must be in [0, {len(studies) - 1}] for {args.data_dir}"
            )
        target = studies[args.target_index]

    model_cls = get_model(args.model)
    output_dir = Path(args.output_dir) / args.model
    output_dir.mkdir(parents=True, exist_ok=True)
    records_path = output_dir / f"{target.name}.jsonl"

    print(
        f"[{args.model}] target={target.name} feature space={model_cls.feature_space.value}",
        flush=True,
    )

    extra: dict[str, object] = {}
    if args.max_epochs:
        extra["max_epochs"] = args.max_epochs
    if args.device:
        extra["device"] = args.device

    records = []
    with records_path.open("w") as handle:
        results = run_cross_study(
            model_cls,
            studies,
            target,
            seed=args.seed,
            max_evals=args.max_evals,
            extra_params=extra,
            max_configurations=args.max_configurations,
        )
        for index, result in enumerate(results, start=1):
            record = result.as_record()
            handle.write(json.dumps(record, default=str) + "\n")
            handle.flush()
            records.append(record)
            status = result.failure or f"median AUC = {record.get('median_auc')}"
            print(f"  {index:>3}. {record['sources']} -> {status}", flush=True)

    frame = pd.DataFrame(records)
    frame.to_csv(output_dir / f"{target.name}.csv", index=False)

    scored = frame[frame["failure"].isna()]
    if not scored.empty:
        print(
            f"\n{args.model} / {target.name}: "
            f"mean of median AUCs = {scored['median_auc'].mean():.4f} "
            f"over {len(scored)} source pools",
        )


if __name__ == "__main__":
    main()
