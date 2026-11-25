#!/usr/bin/env python3
"""Langfuse emitter for Anicca cron loops (Phase 0, shared wrapper).

Design: research_notes/agent-observability-2026-11-06/report.md §5.
One loop run = one trace. Deterministic code evaluators run HERE and post
scores via the Langfuse SDK, per §5.3:
  - artifact_delivered : 1 iff every expected artifact URL actually exists
                         (this script re-fetches each URL to verify, §5.2 verify)
  - winner_named       : 1 iff winner account + winner post URL are recorded
  - copy_diff_zero     : 1 iff measured diff_count == 0 (unmeasured -> 0)
  - cost_recorded      : 1 iff every generation carries model + usage
  - revenue_attributed : 1 iff every revenue event carries an item id

v2 (2026-11-06): Langfuse Cloud organizations created now reject the legacy
REST ingestion endpoint for traces ("Event type trace-create is not
accepted ... send traces via OpenTelemetry"). Sending therefore uses the
official Langfuse Python SDK (OTel-based), installed in
~/workspace/tools/langfuse-venv. When this script runs under a Python
without the SDK, it re-executes itself with the venv Python. Scores go
through the SDK as well (verified live: traces readable via
GET /api/public/v2/observations, scores via GET /api/public/v3/scores).

v2.1 (2026-11-06, sanbou-token-repair): minimal token/cost linkage scope.
Trace metadata now also accepts agent_id / task_id / accepted_outcome_id
(top-level or inside metadata; metadata wins). Generation observations pass
through full usage_details (input/output/total plus extra keys such as cache
tokens, kept separate) and explicit cost_details (SDK 5.2.0). No change to
business behaviour: evaluate() scoring is untouched; callers that send no
generation still send none, and cost stays unmeasured (null), never zero.

Keys are read from environment variables LANGFUSE_HOST / LANGFUSE_PUBLIC_KEY /
LANGFUSE_SECRET_KEY, falling back to ~/.langfuse/keys.env (KEY=VALUE lines).
Secret values are never printed or logged. If no keys are configured (or the
SDK send fails), the run record is appended to a local spool file and the
script exits 0, so adding this to a loop never changes the loop's own
behaviour (fail-soft).

Environment quirk (measured 2026-11-06): this VM's NO_PROXY value contains
an IPv6 entry that crashes httpx URL parsing inside the SDK. The emitter
drops NO_PROXY/no_proxy from its own process environment before creating
the SDK client; the proxy itself (HTTPS_PROXY) is kept.

Usage:
  python3 langfuse_emit.py emit < run.json     # one run record (schema in README.md)
  python3 langfuse_emit.py test                # built-in sample runs (1 pass + 1 deliberate fail)
"""
import json
import os
import sys
import urllib.request
import urllib.error
import uuid
from datetime import datetime, timezone
from pathlib import Path

SPOOL_DIR = Path(__file__).resolve().parent / "spool"
KEYS_FILE = Path.home() / ".langfuse" / "keys.env"
VENV_PYTHON = Path.home() / "workspace" / "tools" / "langfuse-venv" / "bin" / "python"
DEFAULT_HOST = "https://cloud.langfuse.com"


def load_config():
    cfg = {
        "host": os.environ.get("LANGFUSE_HOST", ""),
        "public": os.environ.get("LANGFUSE_PUBLIC_KEY", ""),
        "secret": os.environ.get("LANGFUSE_SECRET_KEY", ""),
    }
    if not (cfg["public"] and cfg["secret"]) and KEYS_FILE.exists():
        for line in KEYS_FILE.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            v = v.strip().strip('"').strip("'")
            if k.strip() == "LANGFUSE_HOST" and not cfg["host"]:
                cfg["host"] = v
            elif k.strip() == "LANGFUSE_PUBLIC_KEY" and not cfg["public"]:
                cfg["public"] = v
            elif k.strip() == "LANGFUSE_SECRET_KEY" and not cfg["secret"]:
                cfg["secret"] = v
    cfg["host"] = (cfg["host"] or DEFAULT_HOST).rstrip("/")
    return cfg


def verify_url(url, timeout=30):
    """Deterministic arrival check: True iff the URL answers 2xx/3xx.

    Timeout raised 10s -> 30s in v2.2 (2026-11-16): through this VM's proxy
    a healthy https://aniccaai.com/ fetch measures ~10-11s, so the old 10s
    budget made the pass case flaky (artifact_verified_count=0 measured).
    """
    try:
        req = urllib.request.Request(
            url, method="GET", headers={"User-Agent": "anicca-langfuse-verify/1.0"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return 200 <= resp.status < 400
    except urllib.error.HTTPError as e:
        return 200 <= e.code < 400
    except Exception:
        return False


def evaluate(run):
    """Return (scores, artifact_results). Pure/deterministic; no LLM."""
    scores = []
    artifacts = run.get("artifacts") or []
    results = []
    delivered = 0
    for a in artifacts:
        v = a.get("verified")
        if v is None and a.get("url"):
            v = verify_url(a["url"])
        ok = bool(v)
        delivered += 1 if ok else 0
        results.append({**a, "verified": ok})
    expected = run.get("expected_artifact_count")
    need = expected if isinstance(expected, int) else len(artifacts)
    artifact_delivered = 1 if artifacts and delivered >= max(need, 1) and delivered == len(artifacts) else 0
    scores.append(("artifact_delivered", artifact_delivered))
    scores.append(("artifact_count", len(artifacts)))
    scores.append(("artifact_verified_count", delivered))

    md = run.get("metadata") or {}
    winner_named = 1 if (
        (md.get("winner_account") and md.get("winner_post_url"))
        or (artifacts and all(a.get("winner_post_url") for a in artifacts))
    ) else 0
    scores.append(("winner_named", winner_named))

    diff = run.get("diff_count")
    if isinstance(diff, (int, float)):
        scores.append(("diff_count", diff))
        scores.append(("copy_diff_zero", 1 if diff == 0 else 0))
    else:
        # Unmeasured diff counts as not-zero (report §5.3: missing source = 0).
        scores.append(("copy_diff_zero", 0))

    gens = [o for o in (run.get("observations") or []) if o.get("type") == "generation"]
    if gens:
        ok = all(o.get("model") and o.get("usage") and "input" in o["usage"] and "output" in o["usage"] for o in gens)
        scores.append(("cost_recorded", 1 if ok else 0))

    rev = run.get("revenue_events") or []
    if rev:
        scores.append(("revenue_attributed", 1 if all(r.get("item_id") for r in rev) else 0))
    return scores, results


def spool(record, reason):
    SPOOL_DIR.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = SPOOL_DIR / f"spool-{day}.jsonl"
    with path.open("a") as f:
        f.write(json.dumps({"spooled_at": datetime.now(timezone.utc).isoformat(), "reason": reason, "run": record}, ensure_ascii=False) + "\n")
    return path


def sdk_available():
    try:
        import langfuse  # noqa: F401
        return True
    except Exception:
        return False


def maybe_reexec():
    """Re-run under the venv Python when the SDK is not importable here."""
    if sdk_available():
        return False
    if os.environ.get("LANGFUSE_EMIT_REEXEC") == "1":
        return False
    if VENV_PYTHON.exists():
        os.environ["LANGFUSE_EMIT_REEXEC"] = "1"
        os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), str(Path(__file__).resolve())] + sys.argv[1:])
    return False


def send_sdk(run, scores, artifact_results, cfg):
    """Send one trace + child observations + scores via the official SDK.

    Returns the actual trace id assigned by the SDK.
    """
    # httpx (used by the SDK) crashes parsing this VM's NO_PROXY IPv6 entry.
    os.environ.pop("NO_PROXY", None)
    os.environ.pop("no_proxy", None)
    # v2.2 (2026-11-16): this VM reaches Langfuse Cloud through a slow proxy;
    # single API/OTLP requests routinely take 10-30s, so the SDK/OTel default
    # timeouts dropped span batches and one score batch in the self-test
    # (measured: scores arrived, observations=0). Raise the timeouts inside
    # this process only; callers need no changes.
    os.environ.setdefault("OTEL_EXPORTER_OTLP_TIMEOUT", "120")
    os.environ.setdefault("OTEL_BSP_EXPORT_TIMEOUT", "120000")
    from langfuse import Langfuse, propagate_attributes

    lf = Langfuse(public_key=cfg["public"], secret_key=cfg["secret"], host=cfg["host"], timeout=120)
    started = run.get("started_at") or datetime.now(timezone.utc).isoformat()
    date_part = started[:10]
    session_id = f"{date_part}:{run['loop_id']}"
    tags = list(dict.fromkeys(["production", run["loop_id"]] + (run.get("tags") or [])))
    md = run.get("metadata") or {}
    trace_meta = {}
    for k, v in {**md, "loop_id": run["loop_id"], "run_id": run.get("run_id")}.items():
        if v is not None:
            trace_meta[k] = v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
    # Minimal scope addition (2026-11-06, sanbou-token-repair): explicit
    # linkage ids. Top-level values are accepted as well as metadata ones;
    # metadata wins when both are present (existing behaviour preserved).
    for f in ("agent_id", "task_id", "accepted_outcome_id"):
        if run.get(f) is not None and f not in trace_meta:
            trace_meta[f] = run[f] if isinstance(run[f], str) else json.dumps(run[f], ensure_ascii=False)
    trace_context = None
    tid = run.get("trace_id")
    if isinstance(tid, str) and len(tid) == 32:
        try:
            int(tid, 16)
            trace_context = {"trace_id": tid}
        except ValueError:
            trace_context = None
    output_summary = run.get("output_summary")
    out_obj = output_summary
    if artifact_results:
        out_obj = {"summary": output_summary, "artifacts": artifact_results}
        if run.get("revenue_events"):
            out_obj["revenue_events"] = run["revenue_events"]
    actual_trace_id = None
    with propagate_attributes(session_id=session_id, tags=tags, metadata=trace_meta, trace_name=run["trace_name"]):
        kwargs = {"name": run["trace_name"], "as_type": "span",
                  "input": run.get("input_summary"), "output": out_obj}
        if trace_context:
            kwargs["trace_context"] = trace_context
        with lf.start_as_current_observation(**kwargs) as root:
            actual_trace_id = lf.get_current_trace_id()
            for o in run.get("observations") or []:
                otype = o.get("type", "span")
                child_kwargs = {"name": o.get("name", "step"),
                                "input": o.get("input"), "output": o.get("output")}
                if o.get("level"):
                    child_kwargs["level"] = o["level"]
                if o.get("status_message"):
                    child_kwargs["status_message"] = o["status_message"]
                if otype == "generation":
                    child_kwargs["as_type"] = "generation"
                    if o.get("model"):
                        child_kwargs["model"] = o["model"]
                    usage = o.get("usage") or {}
                    usage_details = {}
                    for k in ("input", "output", "total"):
                        if k in usage:
                            usage_details[k] = usage[k]
                    # Extra usage_details keys (e.g. cache tokens) pass
                    # through verbatim and stay separate from input/output
                    # in aggregation (SDK 5.2.0: Dict[str, int], free keys).
                    for k, v in (o.get("usage_details") or {}).items():
                        if k not in usage_details:
                            usage_details[k] = v
                    if usage_details:
                        child_kwargs["usage_details"] = usage_details
                    # Explicit cost (SDK 5.2.0: cost_details Dict[str, float]).
                    # Used when the model has no Langfuse price table entry;
                    # never invent a price -- only pass through a given one.
                    cost_details = o.get("cost_details") or {}
                    if isinstance(cost_details, dict) and cost_details:
                        child_kwargs["cost_details"] = cost_details
                else:
                    child_kwargs["as_type"] = "span"
                with root.start_as_current_observation(**child_kwargs):
                    pass
            for name, value in scores:
                root.score_trace(name=name, value=value, data_type="NUMERIC")
    lf.flush()
    return actual_trace_id


def emit(run):
    scores, artifact_results = evaluate(run)
    cfg = load_config()
    score_str = ", ".join(f"{n}={v:g}" for n, v in scores)
    if cfg["public"] and cfg["secret"]:
        maybe_reexec()
        if not sdk_available():
            path = spool(run, "sdk-not-available")
            print(f"LANGFUSE_SPOOLED trace_id=unknown file={path} reason=sdk-not-available scores[{score_str}]")
            return 0
        try:
            trace_id = send_sdk(run, scores, artifact_results, cfg)
            print(f"LANGFUSE_SENT trace_id={trace_id} scores[{score_str}]")
            return 0
        except Exception as e:
            path = spool(run, f"send-failed: {type(e).__name__}: {e}")
            print(f"LANGFUSE_SPOOLED_AFTER_ERROR file={path} error={type(e).__name__} scores[{score_str}]")
            return 0
    path = spool(run, "no-keys-configured")
    print(f"LANGFUSE_SPOOLED trace_id=pending file={path} scores[{score_str}]")
    return 0


def sample_runs():
    base = {
        "loop_id": "anicca-distribution-max-loop",
        "trace_name": "run-distribution-max",
        "run_id": "phase0-test",
        "input_summary": "Phase 0 emitter self-test",
        "metadata": {"winner_account": "@iam.affirmations", "winner_post_url": "https://www.instagram.com/p/DfNAP4Pln3G/"},
        "observations": [
            {"type": "span", "name": "verify", "output": {"checked": 1}},
        ],
    }
    good = {**base, "output_summary": "self-test pass case: aniccaai.com reachable",
            "artifacts": [{"type": "post", "platform": "web", "account": "aniccaai.com", "url": "https://aniccaai.com/",
                           "winner_post_url": "https://www.instagram.com/p/DfNAP4Pln3G/"}],
            "expected_artifact_count": 1, "diff_count": 0,
            # v2.1 scope test: linkage ids + a generation carrying real
            # model/usage (cache key kept separate) and explicit cost.
            "agent_id": "muse", "task_id": "phase0-test",
            "accepted_outcome_id": "https://aniccaai.com/",
            "observations": [
                {"type": "span", "name": "verify", "output": {"checked": 1}},
                {"type": "generation", "name": "create-post", "model": "test-model",
                 "usage": {"input": 100, "output": 50},
                 "usage_details": {"input_cached": 40},
                 "cost_details": {"input": 0.0001, "output": 0.0001}},
            ]}
    bad = {**base, "output_summary": "self-test deliberate-fail case: artifact URL does not exist",
           "artifacts": [{"type": "post", "platform": "web", "account": "aniccaai.com",
                          "url": "https://aniccaai.com/langfuse-phase0-no-such-page",
                          "winner_post_url": "https://www.instagram.com/p/DfNAP4Pln3G/"}],
           "expected_artifact_count": 1, "diff_count": 3}
    return [good, bad]


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    # Re-exec into the venv BEFORE stdin is consumed: emit mode parses the run
    # from stdin in this process, so re-execing later (inside emit) would make
    # the child re-read an already-drained stdin and crash. (Found 2026-11-22
    # during the monitoring repair; this is why emits died whenever the SDK
    # was not importable by the calling python.)
    maybe_reexec()
    mode = sys.argv[1]
    if mode == "emit":
        run = json.load(sys.stdin)
        return emit(run)
    if mode == "test":
        rc = 0
        for run in sample_runs():
            rc |= emit(run)
        return rc
    print(f"unknown mode: {mode}")
    return 2


if __name__ == "__main__":
    sys.exit(main())
