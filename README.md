# agent-endurance-bench

逐步累积上下文中的**状态追踪与指令保持**评测（long-horizon state-tracking & instruction retention · 可机器评分 · 种子化可复现）。俗称"agent 耐力"，但准确说测的是：多轮累积对话里模型对开局约束、数值状态和未授权变更的保持能力——**不覆盖**带外部记忆、摘要压缩、工具调用或自检策略的完整 agent 系统。

[![CI](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

主流 agent 评测（AgentBench / GAIA / SWE-bench 类）以单任务成功率为主轴；长上下文与指令保持已有专门评测，但**逐步累积 + 确定性公开且可重算 gold + 干扰注入**的组合是本项目关注的缺口。本基准测：**跑到第 50–100 步之后，agent 还记得开局约束吗？账还算得对吗？未经授权的"规则变更"能不能把它带偏？**——长任务下的遗忘、状态漂移与抗干扰。

## 怎么测
18 个种子化生成的确定性 episode（IT / 采购 / 客服 × 50步×2 + 100步×2 + **200步×1** + **v3 500步×1**），共 3000 步、330 个探针。v2 高压层：退款负数算术、同谎×3、错误审批码、假预算反复。**v3 高压层**再加两招：**干扰内嵌进正常 task 步文本**（模型无法按步类型忽略）、**cross 多约束交叉探针**（分派规则 × 禁止项联合判断）：

- **开局约束**（system，只给一次）：分派规则表 + 初始预算 + 禁止项 + **规则变更须带审批码**。
- **task 步**：常规处理，每步产生花费（内部状态持续变化）。
- **distractor 干扰步**：无审批码的"规则改了"口头通知、群里误发的假预算数——考验 agent 会不会被带偏。
- **probe 探针**（三种，gold 确定性、公开且可重算）：
  | 探针 | 问什么 | gold |
  |---|---|---|
  | `state` | 当前剩余预算多少？ | 数字（可由花费重算） |
  | `constraint` | 按开局规则 X 类派给谁？ | 选项字母 |
  | `resist` | 有人口头改过规则，现在按**有效规则**该派给谁？ | 原规则字母 |

纯机器评分，无 LLM 裁判；生成器带种子，完全可复现。

## 指标
| 指标 | 方向 | 含义 |
|---|---|---|
| `retention_curve` | — | early/mid/late/xlong/xxlong(101–200)/xxxlong(201–500) 探针准确率 |
| `degradation_slope` | ↓ | early − 最深段，0 = 无退化 |
| `constraint_accuracy` | ↑ | 规则忘没忘 |
| `state_accuracy` | ↑ | 账算没算对 |
| `resist_accuracy` | ↑ | 假"规则变更"顶没顶住 |
| `cross_accuracy` | ↑ | 规则×禁止项联合判断（v3） |
| `endurance_score` | ↑ | 30 步之后的探针准确率 |

## 基线：崩塌线与上界
| 模型/基线（v3 全量 330 探针） | slope ↓ | endurance ↑ | state ↑ | resist ↑ | cross ↑ | xxxlong(201–500) ↑ | state@500步 |
|---|---:|---:|---:|---:|---:|---:|---:|
| window_agent (K=10) | 0.889 | — | — | 0.0 | 0.0 | 0.111 | — |
| glm-5.2 | 0.502 | 0.682 | 0.481 | 0.911 | 28/36 [0.62,0.88] | 41/90 [0.36,0.56] | **5/39 [0.06,0.27]** |
| **deepseek-v4-flash** | **0.0** | **1.0** | **1.0** | **1.0** | 36/36 [0.90,1.00] | 90/90 [0.96,1.00] | 39/39 [0.91,1.00] |
| perfect_memory (oracle) | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

**v3 把 glm 的算术状态追踪彻底压垮**：500 步 episode 上，glm 的 state 探针只剩 **5/39（13%，Wilson [0.06,0.27]）**——累计预算追踪在 500 步尺度基本失效；xxxlong(201–500) 段 41/90，slope 恶化到 0.502。但它的规则记忆（constraint 0.875）、抗带偏（resist 0.911）、甚至新的 cross 多约束探针（28/36）都远好于状态追踪。**"记得规则、算错账"在 500 步被推到极端：规则类能力保持，纯数值状态崩塌**——这对"上下文即状态"的做法是明确警告。deepseek-v4-flash 则**连 v3 也是 330 探针全对**（含内嵌干扰、cross 联合判断、500 步算术）——三个版本连续满分，本基准在此构造下无法证伪其状态保持能力，只能持续给下界。

> 评分器说明：v1.1 修复了 norm 解析（模型答对但附加说明文字时先取首行），修复后 deepseek 从表面 0.917 修正为 1.0；glm-5.2 分数不变（其错误为真实算错/漂移）。诚实披露：glm-5.2 部分探针 content 为空、回退取推理链尾部，其真实分数可能略被低估。

```
window_agent  (probe accuracy by step decile)
  步   1-10  ██████████████████████████████ 100%
  步  11-20  ███████                        22%
  步  21-30  ██                             6%
  步  41-50                                 0%
  步  91-100                                0%
```
**看点**：glm-5.2 曲线随深度单调下滑至 201–500 步段 46%；deepseek 全程 100%。跑 `python3 scripts/curve.py predictions_*.jsonl` 对比。

**诚实披露**：deepseek-v4-flash 连续打满 v1/v2，当前难度对它已饱和——只能给"≥此难度无退化"的下界结论。xxlong 段仅 3 个 episode/30 探针，且同 episode 内探针高度相关，方括号 Wilson 95% CI 很宽；gold 确定性公开（生成器可重建），**非隐藏测试集，不抗污染**，榜单为基准内结论，不外推模型一般能力。（v3 已落地：干扰内嵌 task 步、cross 多约束探针、500 步级。deepseek 仍满分——v4 需要质变而非量变，方向见 PLAN。）

## 跑真实模型
```bash
# 默认走本地 Ollama（http://localhost:11434/v1，无需 key）：
# ollama serve && python3 scripts/run_model.py --model qwen2.5
# 云端可选：export OPENAI_API_KEY=... OPENAI_BASE_URL=<端点>
python3 scripts/run_model.py --model <模型名> [--base-url <端点>]
python3 scripts/score.py predictions_<模型名>.jsonl
python3 scripts/curve.py predictions_<模型名>.jsonl   # ASCII retention 曲线
```
`run_model.py` 按真实多轮对话回放 episode（逐步累积历史），探针步记录模型原话再评分。

## 质量保证
`scripts/check_bench.py` + CI 做**结构与内部一致性校验**：schema、探针覆盖、state gold 重算（由花费累加重建）、干扰步存在性、配比；CI 另跑 **确定性锁**——重新执行种子化生成器并 `git diff --exit-code`，数据与生成器不一致（删 episode、改 gold、改题面）即 FAIL。改动必须体现在生成器代码 diff 中，强制可审查。

## 诚实说明
v1、12 episodes / 900 步 / 120 探针 / 24 干扰步、单人构建、双模拟基线——**能跑通、有论点、可复现**。episode 为合成确定性工作流，测记忆/状态维持/抗干扰能力，不测领域知识。路线图（目标漂移探针、200+ 步、多模型 retention 曲线榜）见 [PLAN.md](PLAN.md)。设计细节见 [docs/design.md](docs/design.md)。许可 CC BY 4.0。
