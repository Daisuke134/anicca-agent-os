#!/usr/bin/env python3
"""Deterministic retention benchmark checker (stdlib only, offline).
Benchmarks: Core-MBA synthesis of Adjust 2026 / AppsFlyer State of Subscriptions 2026 / Sensor Tower 2026.
Rule: business model is the benchmark, vertical is a tiebreaker.
- Cross-industry aggregate: D1 25-26%, D7 11-13%, D30 5-7%; top quartile D1>30, D7>15, D30>8; top decile D1>33.
- D1 floor: <20% = broken first session -> fix time-to-value (<60s) first.
- Subscription model multipliers on category baseline: D1 x1.05, D7 x1.35, D30 x2.50 (AppsFlyer: subscription D30 14% vs ad-supported 5.4%).
- Health & Fitness composite baseline: D1 27, D7 7, D30 3.
Usage: retention_bench_check.py D1 D7 D30 [--model subscription|ad|freemium|paid] [--category health_fitness|aggregate]
Exit 0 if D1 >= floor and no band is BROKEN; exit 1 otherwise (diagnosis, not a pass/fail of the business).
"""
import sys, json
BASE = {
 "aggregate": {"d1":25.5,"d7":12.0,"d30":6.0},
 "health_fitness": {"d1":27.0,"d7":7.0,"d30":3.0},
}
MULT = {"ad":(1.00,1.00,1.00),"freemium":(1.05,1.15,1.40),"subscription":(1.05,1.35,2.50),"paid":(1.10,1.25,1.55)}
def main():
    a=[x for x in sys.argv[1:] if not x.startswith("--")]
    opts=dict(x.split("=",1) for x in sys.argv[1:] if x.startswith("--") and "=" in x)
    model=opts.get("--model","subscription"); cat=opts.get("--category","health_fitness")
    d1,d7,d30=(float(a[0]),float(a[1]),float(a[2]))
    b=BASE[cat]; m=MULT[model]
    exp={"d1":round(b["d1"]*m[0],1),"d7":round(b["d7"]*m[1],1),"d30":round(b["d30"]*m[2],1)}
    out={"input":{"d1":d1,"d7":d7,"d30":d30,"model":model,"category":cat},
         "expected_segment_median":exp,
         "d1_floor_20pct": "BROKEN_FIRST_SESSION" if d1<20 else "ok",
         "bands":{"d1":"below_median" if d1<exp["d1"] else "at_or_above_median",
                  "d7":"below_median" if d7<exp["d7"] else "at_or_above_median",
                  "d30":"below_median" if d30<exp["d30"] else "at_or_above_median"},
         "first_fix": "time-to-value <60s + Day-1 push tied to onboarding intent" if d1<20 else "next lowest band"}
    print(json.dumps(out,indent=1))
    return 1 if d1<20 else 0
if __name__=="__main__": sys.exit(main())
