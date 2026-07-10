#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score predictions for agent-endurance-bench.
pred line: {"episode_id":.., "step":.., "answer":".."}
Usage: score.py <pred.jsonl> [episodes.jsonl]

Metrics:
  retention_curve      probe accuracy by depth bucket: early(<=10) / mid(11-30) / late(31-50)
  degradation_slope    early_acc - late_acc            (0 = no degradation; ↓ better)
  constraint_accuracy  accuracy on constraint-recall probes (↑)
  state_accuracy       accuracy on state-tracking probes (↑)
  endurance_score      late-bucket accuracy (↑) — what still works after 30+ steps
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def norm(s):
    s = str(s).strip()
    m = re.search(r"[ABC]", s.upper())
    if m and len(s) <= 24: return m.group(0)
    m = re.search(r"-?\d+", s.replace(",", ""))
    return m.group(0) if m else s

def bucket(step):
    return "early" if step <= 10 else ("mid" if step <= 30 else "late")

def main():
    if len(sys.argv) < 2:
        print("usage: score.py <pred.jsonl> [episodes.jsonl]"); return 2
    preds = {}
    for l in open(sys.argv[1], encoding="utf-8"):
        l = l.strip()
        if l:
            o = json.loads(l); preds[(o["episode_id"], int(o["step"]))] = o.get("answer", "")
    eps_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "episodes.jsonl")
    hits = {"early": [0,0], "mid": [0,0], "late": [0,0]}
    kinds = {"constraint": [0,0], "state": [0,0]}
    miss = 0
    for l in open(eps_path, encoding="utf-8"):
        e = json.loads(l)
        for s in e["steps"]:
            if s["type"] != "probe": continue
            key = (e["id"], s["step"])
            if key not in preds: miss += 1; continue
            ok = norm(preds[key]) == norm(s["gold"])
            b = bucket(s["step"]); hits[b][0] += ok; hits[b][1] += 1
            k = s["probe_kind"]; kinds[k][0] += ok; kinds[k][1] += 1
    acc = lambda p: round(p[0]/p[1], 3) if p[1] else None
    curve = {b: acc(v) for b, v in hits.items()}
    rep = {
        "missing": miss,
        "retention_curve": curve,
        "degradation_slope": round(curve["early"] - curve["late"], 3)
            if (curve["early"] is not None and curve["late"] is not None) else None,
        "constraint_accuracy": acc(kinds["constraint"]),
        "state_accuracy": acc(kinds["state"]),
        "endurance_score": curve["late"],
    }
    json.dump(rep, open(os.path.join(ROOT, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
