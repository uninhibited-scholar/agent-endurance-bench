#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Truncated-memory baseline: an agent that only remembers the last K steps
(sliding window, no summary). Deterministic simulation — answers a probe correctly
iff the information it needs still sits inside the window:
  - constraint probes need the opening rules (step 0)  -> correct iff probe_step <= K
  - state probes need every cost update so far          -> correct iff probe_step <= K
Shows exactly the degradation curve this bench measures.
Emits baselines/predictions_window_agent.jsonl  (K=10 by default)."""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
K = int(sys.argv[1]) if len(sys.argv) > 1 else 10

def main():
    out = os.path.join(ROOT, "baselines", "predictions_window_agent.jsonl")
    with open(out, "w", encoding="utf-8") as w:
        for l in open(os.path.join(ROOT, "data", "episodes.jsonl"), encoding="utf-8"):
            e = json.loads(l)
            for s in e["steps"]:
                if s["type"] != "probe": continue
                in_window = s["step"] <= K
                if in_window:
                    ans = s["gold"]
                else:
                    # info fell out of window: constraint -> guess 'A'; state -> current budget0 (forgot spending)
                    ans = "A" if s["probe_kind"] == "constraint" else str(e["budget0"])
                w.write(json.dumps({"episode_id": e["id"], "step": s["step"], "answer": ans},
                                   ensure_ascii=False) + "\n")
    print(f"wrote {out} (window K={K})")

if __name__ == "__main__":
    main()
