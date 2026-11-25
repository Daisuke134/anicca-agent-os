#!/usr/bin/env python3
"""Drain the langfuse_emit spool backlog into Langfuse Cloud (batch, one client).

Reads spool-*.jsonl files (default: all in ./spool), sends each spooled run as
a trace with the same deterministic scores langfuse_emit.evaluate() computes.
Artifacts that already carry a `verified` flag keep it (no re-fetch); others
are re-fetched once by evaluate(). Successfully sent entries are recorded in
spool/drained-ledger.jsonl; source spool files are NOT modified.
Run under the langfuse venv python.
"""
import json, os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.pop("NO_PROXY", None); os.environ.pop("no_proxy", None)
os.environ.setdefault("OTEL_EXPORTER_OTLP_TIMEOUT", "120")
os.environ.setdefault("OTEL_BSP_EXPORT_TIMEOUT", "120000")
import langfuse_emit as E
from langfuse import Langfuse, propagate_attributes

SPOOL_DIR = Path(__file__).resolve().parent / "spool"
LEDGER = SPOOL_DIR / "drained-ledger.jsonl"

def already_drained():
    done = set()
    if LEDGER.exists():
        for line in LEDGER.read_text().splitlines():
            try:
                d = json.loads(line); done.add((d["file"], d["idx"]))
            except Exception: pass
    return done

def main():
    files = sys.argv[1:] or [str(p) for p in sorted(SPOOL_DIR.glob("spool-*.jsonl"))]
    cfg = E.load_config()
    if not (cfg["public"] and cfg["secret"]):
        print("no keys configured; abort"); return 1
    lf = Langfuse(public_key=cfg["public"], secret_key=cfg["secret"], host=cfg["host"], timeout=120)
    done = already_drained()
    sent = skipped = failed = 0
    led = LEDGER.open("a")
    for fpath in files:
        p = Path(fpath)
        for idx, line in enumerate(p.read_text().splitlines()):
            if (p.name, idx) in done: skipped += 1; continue
            try:
                rec = json.loads(line); run = rec["run"]
                if "loop_id" not in run or "trace_name" not in run:
                    run.setdefault("loop_id", "anicca-observability-loop"); run.setdefault("trace_name", "run-spooled")
                scores, artifact_results = E.evaluate(run)
                md = run.get("metadata") or {}
                trace_meta = {}
                for k, v in {**md, "loop_id": run["loop_id"], "run_id": run.get("run_id"), "spool_replay": "2026-11-24", "spooled_at": rec.get("spooled_at")}.items():
                    if v is not None: trace_meta[k] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                started = run.get("started_at") or rec.get("spooled_at") or "2026-11-22"
                session_id = f"{str(started)[:10]}:{run['loop_id']}"
                tags = list(dict.fromkeys(["production", run["loop_id"], "spool-replay"] + (run.get("tags") or [])))
                out_obj = run.get("output_summary")
                if artifact_results: out_obj = {"summary": out_obj, "artifacts": artifact_results}
                with propagate_attributes(session_id=session_id, tags=tags, metadata=trace_meta, trace_name=run["trace_name"]):
                    with lf.start_as_current_observation(name=run["trace_name"], as_type="span", input=run.get("input_summary"), output=out_obj) as root:
                        for o in run.get("observations") or []:
                            ck = {"name": o.get("name", "step"), "input": o.get("input"), "output": o.get("output"), "as_type": "generation" if o.get("type") == "generation" else "span"}
                            if o.get("level"): ck["level"] = o["level"]
                            if o.get("status_message"): ck["status_message"] = o["status_message"]
                            if o.get("type") == "generation" and o.get("model"): ck["model"] = o["model"]
                            with root.start_as_current_observation(**ck): pass
                        for name, value in scores: root.score_trace(name=name, value=value, data_type="NUMERIC")
                sent += 1
                led.write(json.dumps({"file": p.name, "idx": idx, "loop_id": run["loop_id"]}) + "\n"); led.flush()
                if sent % 50 == 0: lf.flush(); print(f"progress sent={sent}", flush=True)
            except Exception as e:
                failed += 1
                print(f"FAIL {p.name}#{idx}: {type(e).__name__}: {str(e)[:160]}", flush=True)
    lf.flush()
    print(f"DRAIN_DONE sent={sent} skipped={skipped} failed={failed}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
