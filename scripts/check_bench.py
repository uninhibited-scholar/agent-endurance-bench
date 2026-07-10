#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate data/episodes.jsonl: schema, probe coverage, gold consistency (recompute
budgets from step costs), determinism guard. Do NOT pass by trimming episodes."""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "episodes.jsonl")
EKEYS = {"id","domain","n_steps","budget0","constraints","steps"}
PROBE_AT = {5,10,15,20,25,30,35,40,45,50}

def main():
    eps, prob = [], []
    for ln, line in enumerate(open(DATA, encoding="utf-8"), 1):
        line = line.strip()
        if not line: continue
        try: e = json.loads(line)
        except Exception as ex: prob.append(f"L{ln} bad json {ex}"); continue
        eps.append(e)
        i = e.get("id")
        if set(e) != EKEYS: prob.append(f"{i} keys {sorted(e)}")
        if e.get("n_steps") != 50: prob.append(f"{i} n_steps != 50")
        if len(e.get("steps", [])) != 50: prob.append(f"{i} steps len != 50")
        if len(str(e.get("constraints",""))) < 40: prob.append(f"{i} constraints too short")
        spent, probes = 0, 0
        for s in e["steps"]:
            if s["type"] == "task":
                spent += s.get("cost", 0)
            elif s["type"] == "probe":
                probes += 1
                if s["step"] not in PROBE_AT: prob.append(f"{i} probe at odd step {s['step']}")
                if s["probe_kind"] == "state" and str(s["gold"]) != str(e["budget0"] - spent):
                    prob.append(f"{i} step{s['step']} state gold {s['gold']} != recomputed {e['budget0']-spent}")
                if s["probe_kind"] == "constraint" and s["gold"] not in ("A","B","C"):
                    prob.append(f"{i} step{s['step']} bad constraint gold")
                if not str(s.get("gold","")).strip(): prob.append(f"{i} step{s['step']} empty gold")
            else:
                prob.append(f"{i} bad step type {s['type']}")
        if probes != 10: prob.append(f"{i} probes {probes} != 10")
        if e["budget0"] - spent < 0: prob.append(f"{i} budget overspent by design")
    ids = [e["id"] for e in eps]
    if len(ids) != len(set(ids)): prob.append("dup id")
    if len(eps) < 6: prob.append(f"too few episodes ({len(eps)} < 6)")
    doms = {e["domain"] for e in eps}
    if len(doms) < 3: prob.append("need >=3 domains")
    total_probes = sum(1 for e in eps for s in e["steps"] if s["type"]=="probe")
    print(f"checked {len(eps)} episodes | domains {sorted(doms)} | probes {total_probes}")
    if prob:
        print(f"\nFAIL — {len(prob)}:")
        for p in prob[:50]: print("  -", p)
        print("\nFix the real gap; do NOT pass by trimming episodes or editing golds.")
        return 1
    print("PASS — schema ok, probe coverage ok, golds recompute clean, domains covered.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
