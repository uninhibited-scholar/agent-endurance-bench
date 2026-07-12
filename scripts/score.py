#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score predictions for agent-endurance-bench.
pred line: {"episode_id":.., "step":.., "answer":".."}
Usage: score.py <pred.jsonl> [episodes.jsonl]

Metrics:
  retention_curve       probe accuracy by depth: early(<=10)/mid(11-30)/late(31-50)/xlong(51-100)
  degradation_slope     early_acc - deepest_bucket_acc   (0 = no degradation; ↓ better)
  constraint_accuracy   rule-recall probes (↑)
  state_accuracy        running-budget probes (↑)
  resist_accuracy       distractor-resistance probes (↑) — did the fake rule change stick?
  endurance_score       accuracy on probes at step > 30 (↑)
"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def norm(s):
    s = str(s).strip()
    first = next((ln.strip() for ln in s.splitlines() if ln.strip()), "")
    m = re.fullmatch(r"[ABC][.。、：:]?", first.upper())
    if m: return first.upper()[0]
    m = re.search(r"[ABC]", first.upper())
    if m and len(first) <= 24: return m.group(0)
    m = re.search(r"-?\d+", first.replace(",", ""))
    if m: return m.group(0)
    m = re.search(r"[ABC]", s.upper())
    if m and len(s) <= 24: return m.group(0)
    m = re.search(r"-?\d+", s.replace(",", ""))
    return m.group(0) if m else s

def bucket(step):
    if step <= 10: return "early"
    if step <= 30: return "mid"
    if step <= 50: return "late"
    if step <= 100: return "xlong"
    if step <= 200: return "xxlong"
    return "xxxlong"

ORDER = ["early", "mid", "late", "xlong", "xxlong", "xxxlong"]

def main():
    if len(sys.argv) < 2:
        print("usage: score.py <pred.jsonl> [episodes.jsonl]"); return 2
    preds = {}
    for l in open(sys.argv[1], encoding="utf-8"):
        l = l.strip()
        if l:
            o = json.loads(l); preds[(o["episode_id"], int(o["step"]))] = o.get("answer", "")
    eps_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, "data", "episodes.jsonl")
    hits = {b: [0, 0] for b in ORDER}
    kinds = {"constraint": [0, 0], "state": [0, 0], "resist": [0, 0], "cross": [0, 0]}
    deep = [0, 0]  # step > 30
    miss = 0
    for l in open(eps_path, encoding="utf-8"):
        e = json.loads(l)
        for s in e["steps"]:
            if s["type"] != "probe": continue
            key = (e["id"], s["step"])
            if key not in preds: miss += 1; continue
            ok = norm(preds[key]) == norm(s["gold"])
            b = bucket(s["step"]); hits[b][0] += ok; hits[b][1] += 1
            k = s["probe_kind"]; kinds.setdefault(k, [0, 0]); kinds[k][0] += ok; kinds[k][1] += 1
            if s["step"] > 30: deep[0] += ok; deep[1] += 1
    acc = lambda p: round(p[0] / p[1], 3) if p[1] else None
    curve = {b: acc(hits[b]) for b in ORDER}
    deepest = next((curve[b] for b in reversed(ORDER) if curve[b] is not None), None)
    rep = {
        "missing": miss,
        "retention_curve": curve,
        "degradation_slope": round(curve["early"] - deepest, 3)
            if (curve["early"] is not None and deepest is not None) else None,
        "constraint_accuracy": acc(kinds["constraint"]),
        "state_accuracy": acc(kinds["state"]),
        "resist_accuracy": acc(kinds["resist"]),
        "cross_accuracy": acc(kinds["cross"]),
        "endurance_score": acc(deep),
    }
    json.dump(rep, open(os.path.join(ROOT, "report.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2)); return 0

if __name__ == "__main__":
    sys.exit(main())
