#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run an OpenAI-compatible model through agent-endurance-bench episodes.
Replays each episode as a true multi-turn conversation (system = constraints,
each step = one user turn, model reply appended to history), records probe answers.

Usage:
  export OPENAI_API_KEY=...
  python3 scripts/run_model.py --model <name> [--base-url <url>] [--episodes ep-it-ticket-1,...]
Output: predictions_<model>.jsonl  ({"episode_id":..,"step":..,"answer":".."})
"""
import argparse, json, os, re, ssl, sys, time, urllib.request
try:
    import certifi
    _SSL = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    _SSL = None
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def call(base, key, model, messages, max_tokens):
    body = json.dumps({"model": model, "temperature": 0, "max_tokens": max_tokens,
                       "messages": messages}).encode()
    req = urllib.request.Request(base.rstrip("/") + "/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    for _r in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180, context=_SSL) as r:
                msg = json.loads(r.read())["choices"][0]["message"]
                # reasoning models: final answer in content; fall back to reasoning tail
                return msg.get("content") or (msg.get("reasoning_content") or "")[-200:]
        except Exception:
            time.sleep(2 * (_r + 1))
    return ""

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    ap.add_argument("--key", default=os.environ.get("OPENAI_API_KEY", ""))
    ap.add_argument("--episodes", default="")
    ap.add_argument("--out", default="")
    a = ap.parse_args()
    if not a.key:
        print("ERROR: set OPENAI_API_KEY"); return 2
    out = a.out or os.path.join(ROOT, f"predictions_{re.sub(r'[^a-zA-Z0-9._-]','_',a.model)}.jsonl")
    eps = [json.loads(l) for l in open(os.path.join(ROOT,"data","episodes.jsonl"),encoding="utf-8") if l.strip()]
    if a.episodes:
        want = set(a.episodes.split(","))
        eps = [e for e in eps if e["id"] in want]
    done = set()
    if os.path.exists(out):
        for l in open(out, encoding="utf-8"):
            if l.strip():
                try:
                    o = json.loads(l); done.add(o["episode_id"])
                except: pass
    with open(out, "a", encoding="utf-8") as w:
        for e in eps:
            if e["id"] in done:
                print(f"skip {e['id']} (done)"); continue
            print(f"episode {e['id']} ({e['n_steps']} steps)")
            msgs = [{"role": "system", "content": e["constraints"]}]
            for s in e["steps"]:
                msgs.append({"role": "user", "content": s["input"]})
                is_probe = s["type"] == "probe"
                reply = call(a.base_url, a.key, a.model, msgs, 1024 if is_probe else 512)
                msgs.append({"role": "assistant", "content": reply})
                if is_probe:
                    w.write(json.dumps({"episode_id": e["id"], "step": s["step"],
                                        "answer": reply.strip()}, ensure_ascii=False) + "\n")
                    w.flush()
                    print(f"  probe@{s['step']}: {reply.strip()[:40]!r}")
    print(f"\nwrote {out}")

if __name__ == "__main__":
    sys.exit(main())
