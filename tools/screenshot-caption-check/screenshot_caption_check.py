#!/usr/bin/env python3
"""Deterministic screenshot caption / frame-order checker (stdlib only, free, offline).
Gates from Nakxi ASO Screenshots Best Practices 2026 (full read 2026-11-12)
+ AppFollow 1,200-app review + SplitMetrics via Screencraft:
 SC-1 First three frames exist in order Promise(1) -> Proof(2) -> Payoff(3)
 SC-2 Every headline in frames 1-3 is 4-7 words (readable at ~200px search strip)
 SC-3 One phrase per frame: headline is a single phrase (no sentence punctuation
      splitting it into two phrases, no second headline field)
 SC-4 Frames 1-3 show real app UI (Guideline 2.3.3); frame 1 is not a splash/login
 SC-5 Frame 1 headline shares >=1 content word with title/subtitle (matches search)
 SC-6 Trust frame (job=trust) only passes if trust_claim_real is true
 SC-7 Test discipline: at most 1 change queued in the test (test_changes <= 1)
Usage: screenshot_caption_check.py <set.json> -> JSON verdict, exit 0 if pass else 1
Set JSON: {"title": str, "subtitle": str, "test_changes": int,
           "frames": [{"n":1,"job":"promise","headline":"...","shows_real_ui":true,
                        "is_splash_or_login":false,"trust_claim_real":null}, ...]}
"""
import json, sys, re
STOP={"the","a","an","your","you","for","and","or","to","of","in","on","with"}
def words(s): return re.findall(r"[A-Za-z']+", (s or ""))
def check(p):
    frames={f.get("n"):f for f in (p.get("frames") or [])}
    f123=[frames.get(i) for i in (1,2,3)]
    sc1 = all(f123) and [ (f.get("job") or "").lower() for f in f123]==["promise","proof","payoff"]
    sc2 = all(f and 4 <= len(words(f.get("headline"))) <= 7 for f in f123)
    def one_phrase(f):
        if not f: return False
        h=(f.get("headline") or "").strip()
        if f.get("second_headline"): return False
        # two sentences / two phrases separated by . ! ? ; or em-dash clause
        if re.search(r"[.!?;]", h): return False
        return len(h)>0
    sc3 = all(one_phrase(f) for f in f123)
    sc4 = all(f and f.get("shows_real_ui") is True and f.get("is_splash_or_login") is not True for f in f123)
    # SC-5
    title_words={w.lower() for w in words((p.get("title") or "")+" "+(p.get("subtitle") or ""))} - STOP
    f1_words={w.lower() for w in words(f123[0].get("headline") if f123[0] else "")} - STOP
    sc5 = len(title_words & f1_words) >= 1 if title_words and f1_words else False
    trust_frames=[f for f in (p.get("frames") or []) if (f.get("job") or "").lower()=="trust"]
    sc6 = all(f.get("trust_claim_real") is True for f in trust_frames) if trust_frames else True
    sc7 = (p.get("test_changes") is not None) and p.get("test_changes") <= 1
    passed = bool(sc1 and sc2 and sc3 and sc4 and sc5 and sc6 and sc7)
    return {"SC-1_first3_promise_proof_payoff": bool(sc1),
            "SC-2_headline_4_to_7_words_first3": bool(sc2),
            "SC-3_one_phrase_per_frame": bool(sc3),
            "SC-4_real_ui_not_splash_first3": bool(sc4),
            "SC-5_frame1_matches_title_subtitle": bool(sc5),
            "SC-6_trust_claim_real_or_no_trust_frame": bool(sc6),
            "SC-7_single_change_test": bool(sc7),
            "pass": passed}
if __name__=="__main__":
    data=json.load(open(sys.argv[1]))
    v=check(data)
    print(json.dumps(v, indent=2))
    sys.exit(0 if v["pass"] else 1)
