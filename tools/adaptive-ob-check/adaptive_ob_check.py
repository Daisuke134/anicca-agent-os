import json,sys
def check(d):
    fails=[]
    qs=d.get("questions",[])
    if len(qs)<5: fails.append("AO-1 questions<5: synthetic user needs more data")
    for q in qs:
        if not q.get("changes"): fails.append(f"AO-2 question {q.get('id')} changes nothing -> cut it")
        if not q.get("synthetic_field"): fails.append(f"AO-3 question {q.get('id')} maps to no synthetic-user field")
    if not d.get("branching"): fails.append("AO-4 no branching: next question never depends on previous answer")
    if not d.get("reflection_interpolates_answers"): fails.append("AO-5 reflection/plan reveal does not interpolate actual answers")
    if not d.get("paywall_references_answers"): fails.append("AO-6 paywall does not reference onboarding answers")
    if not d.get("first_intervention_from_answers"): fails.append("AO-7 first intervention not selected from answers")
    return fails
for p in sys.argv[1:]:
    d=json.load(open(p)); f=check(d)
    print(p, "PASS" if not f else f"FAIL {len(f)}", *f, sep="\n  ")
