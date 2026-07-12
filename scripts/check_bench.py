#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validate data/episodes.jsonl (v1): schema, probe coverage, gold consistency
(recompute budgets from step costs), distractor presence, domain/length mix.
Do NOT pass by trimming episodes or editing golds."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "episodes.jsonl")
EKEYS = {"id","domain","n_steps","budget0","constraints","steps"}
KINDS = {"state","constraint","resist"}
KINDS_ALL = {"state","constraint","resist","cross"}

def probe_steps(n):
    if n <= 50: return set(range(5, n + 1, 5))
    if n <= 200: return set(range(5, n + 1, 10))
    return set(range(10, n + 1, 10))

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
        n = e.get("n_steps")
        if n not in (50, 100, 200, 500): prob.append(f"{i} n_steps {n} not in (50,100,200,500)")
        if len(e.get("steps", [])) != n: prob.append(f"{i} steps len != n_steps")
        if len(str(e.get("constraints",""))) < 60: prob.append(f"{i} constraints too short")
        if "审批码" not in e.get("constraints",""): prob.append(f"{i} missing rule-change guard clause")
        pset = probe_steps(n or 50)
        spent, probes, distractors, embedded, kinds_seen = 0, 0, 0, 0, set()
        for s in e["steps"]:
            t = s.get("type")
            if t == "task":
                spent += s.get("cost", 0)
                if "无审批码" in s.get("input", "") or "仅供参考" in s.get("input", ""):
                    embedded += 1
            elif t == "distractor":
                distractors += 1
                good_code = "OK-" + i[-4:] if len(i) >= 4 else ""
                if good_code and ("【" + good_code + "】") in s["input"]:
                    prob.append(f"{i} step{s['step']} distractor carries VALID approval code")
            elif t == "probe":
                probes += 1; kinds_seen.add(s.get("probe_kind"))
                if s["step"] not in pset: prob.append(f"{i} probe at odd step {s['step']}")
                if s.get("probe_kind") not in KINDS_ALL: prob.append(f"{i} step{s['step']} bad probe_kind")
                if s["probe_kind"] == "state" and str(s["gold"]) != str(e["budget0"] - spent):
                    prob.append(f"{i} step{s['step']} state gold {s['gold']} != recomputed {e['budget0']-spent}")
                if s["probe_kind"] in ("constraint","resist","cross") and s["gold"] not in ("A","B","C"):
                    prob.append(f"{i} step{s['step']} bad choice gold")
                if not str(s.get("gold","")).strip(): prob.append(f"{i} step{s['step']} empty gold")
            else:
                prob.append(f"{i} bad step type {t}")
        if probes != len(pset): prob.append(f"{i} probes {probes} != {len(pset)}")
        need_d = 5 if n in (200, 500) else 2
        total_dis = distractors + embedded
        if total_dis < need_d: prob.append(f"{i} needs >={need_d} distractors (standalone+embedded), has {total_dis}")
        if not KINDS.issubset(kinds_seen): prob.append(f"{i} probe kinds {sorted(kinds_seen)} missing base kind")
        if e["budget0"] - spent < 0: prob.append(f"{i} budget overspent by design")
    ids = [e["id"] for e in eps]
    if len(ids) != len(set(ids)): prob.append("dup id")
    if len(eps) < 15: prob.append(f"too few episodes ({len(eps)} < 15)")
    x2 = sum(1 for e in eps if e["n_steps"] == 200)
    if x2 < 3: prob.append(f"need >=3 x200 episodes, has {x2}")
    x5 = sum(1 for e in eps if e["n_steps"] == 500)
    if x5 < 3: prob.append(f"need >=3 x500 episodes, has {x5}")
    if len(eps) < 18: prob.append(f"too few episodes ({len(eps)} < 18)")
    doms = {e["domain"] for e in eps}
    if len(doms) < 3: prob.append("need >=3 domains")
    longs = sum(1 for e in eps if e["n_steps"] == 100)
    if longs < 6: prob.append(f"need >=6 long (100-step) episodes, has {longs}")
    total_probes = sum(1 for e in eps for s in e["steps"] if s["type"] == "probe")
    print(f"checked {len(eps)} episodes ({sum(e['n_steps'] for e in eps)} steps) | "
          f"domains {sorted(doms)} | probes {total_probes} | long {longs}")
    if prob:
        print(f"\nFAIL — {len(prob)}:")
        for p in prob[:50]: print("  -", p)
        print("\nFix the real gap; do NOT pass by trimming episodes or editing golds.")
        return 1
    print("PASS — schema ok, probes+golds recompute clean, distractors present, mix ok.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
