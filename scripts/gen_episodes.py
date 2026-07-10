#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministically generate data/episodes.jsonl (seeded, reproducible).
Each episode: opening constraints -> 50 task steps with probes injected.
Probes have closed gold answers (choice letter or number) => machine-scorable."""
import json, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "episodes.jsonl")
SEED = 20260710
N_STEPS = 50
PROBE_AT = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

# domain -> (assignment rule table, ticket kinds)
DOMAINS = {
    "it-ticket": {
        "rule": {"数据库": "B组", "网络": "C组", "账号权限": "A组"},
        "kinds": ["数据库", "网络", "账号权限"],
        "noun": "工单",
    },
    "procurement": {
        "rule": {"办公耗材": "本地采购", "电子设备": "集中采购", "软件许可": "法务会签"},
        "kinds": ["办公耗材", "电子设备", "软件许可"],
        "noun": "采购单",
    },
    "cs-ticket": {
        "rule": {"退款": "财务复核", "物流": "仓储对接", "产品缺陷": "质检上报"},
        "kinds": ["退款", "物流", "产品缺陷"],
        "noun": "客服单",
    },
}

def gen_episode(eid, domain, rng):
    d = DOMAINS[domain]
    kinds = d["kinds"]
    budget0 = rng.choice([5000, 8000, 10000])
    forbidden = rng.choice(["周五", "月底", "节假日"])
    constraints = (
        f"你是{d['noun']}处理助手，全程遵守以下开局规则，不得遗忘：\n"
        f"1) 分派规则：" + "；".join(f"{k}类→{v}" for k, v in d["rule"].items()) + "。\n"
        f"2) 预算：初始预算 {budget0} 元，每步花费后自行累计剩余额，不允许超支。\n"
        f"3) 禁止项：{forbidden}不得安排上门处理。\n"
        f"每步只需简短确认处理；遇到【探针】问题时，只输出答案本身。"
    )
    steps, spent = [], 0
    for i in range(1, N_STEPS + 1):
        if i in PROBE_AT:
            if (PROBE_AT.index(i) % 2) == 0:  # even slots: state tracking
                steps.append({
                    "step": i, "type": "probe", "probe_kind": "state",
                    "input": f"【探针】截至目前累计花费后，剩余预算是多少元？只输出数字。",
                    "gold": str(budget0 - spent),
                })
            else:  # odd slots: constraint recall (multiple choice)
                k = kinds[(i // 7) % len(kinds)]
                opts = list(d["rule"].values())
                rng.shuffle(opts)
                letter = "ABC"[opts.index(d["rule"][k])]
                steps.append({
                    "step": i, "type": "probe", "probe_kind": "constraint",
                    "input": (f"【探针】按开局分派规则，{k}类{d['noun']}应派给谁？"
                              f"A. {opts[0]}  B. {opts[1]}  C. {opts[2]}。只输出选项字母。"),
                    "gold": letter,
                })
        else:
            k = kinds[rng.randrange(len(kinds))]
            cost = rng.choice([30, 50, 80, 120, 150])
            spent += cost
            steps.append({
                "step": i, "type": "task",
                "input": f"第{i}步：新{d['noun']} #{eid[-1]}{i:03d}（{k}类），本步处理花费 {cost} 元，请确认处理。",
                "cost": cost,
            })
    return {"id": eid, "domain": domain, "n_steps": N_STEPS,
            "budget0": budget0, "constraints": constraints, "steps": steps}

def main():
    rng = random.Random(SEED)
    eps = []
    for domain in DOMAINS:
        for j in (1, 2):
            eps.append(gen_episode(f"ep-{domain}-{j}", domain, rng))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for e in eps:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    n_probe = sum(1 for e in eps for s in e["steps"] if s["type"] == "probe")
    print(f"wrote {len(eps)} episodes, {n_probe} probes -> {OUT}")

if __name__ == "__main__":
    main()
