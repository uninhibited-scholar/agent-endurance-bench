#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Perfect-memory oracle: answers every probe from gold. Anchors the upper bound
(degradation_slope = 0). Real models land between this and the sliding-window
collapse line. Emits baselines/predictions_perfect_memory.jsonl."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def main():
    out = os.path.join(ROOT, "baselines", "predictions_perfect_memory.jsonl")
    with open(out, "w", encoding="utf-8") as w:
        for l in open(os.path.join(ROOT, "data", "episodes.jsonl"), encoding="utf-8"):
            e = json.loads(l)
            for s in e["steps"]:
                if s["type"] == "probe":
                    w.write(json.dumps({"episode_id": e["id"], "step": s["step"],
                                        "answer": s["gold"]}, ensure_ascii=False) + "\n")
    print(f"wrote {out}")

if __name__ == "__main__":
    main()
