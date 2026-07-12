#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ASCII retention curve: probe accuracy per depth decile across one or more
prediction files. Zero-dependency leaderboard visual.
Usage: curve.py <pred1.jsonl> [pred2.jsonl ...]"""
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

def main():
    if len(sys.argv) < 2:
        print("usage: curve.py <pred.jsonl> [...]"); return 2
    eps = [json.loads(l) for l in open(os.path.join(ROOT,"data","episodes.jsonl"),encoding="utf-8") if l.strip()]
    golds = {(e["id"], s["step"]): s["gold"] for e in eps for s in e["steps"] if s["type"]=="probe"}
    for path in sys.argv[1:]:
        preds = {}
        for l in open(path, encoding="utf-8"):
            l = l.strip()
            if l:
                o = json.loads(l); preds[(o["episode_id"], int(o["step"]))] = o.get("answer","")
        dec = {}
        for (eid, step), gold in golds.items():
            d = min((step - 1) // 10, 49)
            hit, tot = dec.get(d, (0, 0))
            ok = (eid, step) in preds and norm(preds[(eid, step)]) == norm(gold)
            dec[d] = (hit + ok, tot + 1)
        name = os.path.basename(path).replace("predictions_","").replace(".jsonl","")
        print(f"\n{name}  (probe accuracy by step decile)")
        for d in sorted(dec):
            h, t = dec[d]
            a = h / t if t else 0
            bar = "█" * round(a * 30)
            print(f"  步 {d*10+1:>3}-{d*10+10:<3} {bar:<30} {a:.0%} ({h}/{t})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
