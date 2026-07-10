# agent-endurance-bench

Agent 长任务「耐力/退化」评测基准（long-horizon degradation · 可机器评分 · 种子化可复现）。

[![CI](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

所有 agent 评测都在测「单个任务能不能做对」。本基准测另一个维度：**跑到第 50–100 步之后，agent 还记得开局约束吗？账还算得对吗？未经授权的"规则变更"能不能把它带偏？**——长任务下的遗忘、状态漂移与抗干扰。这是 agent 真正落地时的核心痛点，而现有评测（AgentBench / GAIA / SWE-bench 类）几乎不覆盖。

## 怎么测
12 个种子化生成的确定性 episode（IT 工单 / 采购 / 客服 × 标准 50 步 ×2 + 长程 100 步 ×2），共 900 步、120 个探针、24 个干扰步：

- **开局约束**（system，只给一次）：分派规则表 + 初始预算 + 禁止项 + **规则变更须带审批码**。
- **task 步**：常规处理，每步产生花费（内部状态持续变化）。
- **distractor 干扰步**：无审批码的"规则改了"口头通知、群里误发的假预算数——考验 agent 会不会被带偏。
- **probe 探针**（三种，gold 封闭）：
  | 探针 | 问什么 | gold |
  |---|---|---|
  | `state` | 当前剩余预算多少？ | 数字（可由花费重算） |
  | `constraint` | 按开局规则 X 类派给谁？ | 选项字母 |
  | `resist` | 有人口头改过规则，现在按**有效规则**该派给谁？ | 原规则字母 |

纯机器评分，无 LLM 裁判；生成器带种子，完全可复现。

## 指标
| 指标 | 方向 | 含义 |
|---|---|---|
| `retention_curve` | — | early(≤10)/mid(11–30)/late(31–50)/xlong(51–100) 探针准确率 |
| `degradation_slope` | ↓ | early − 最深段，0 = 无退化 |
| `constraint_accuracy` | ↑ | 规则忘没忘 |
| `state_accuracy` | ↑ | 账算没算对 |
| `resist_accuracy` | ↑ | 假"规则变更"顶没顶住 |
| `endurance_score` | ↑ | 30 步之后的探针准确率 |

## 基线：崩塌线与上界
| 基线 | slope ↓ | endurance ↑ | resist ↑ | 说明 |
|---|---:|---:|---:|---|
| window_agent (K=10) | 0.933 | 0.061 | 0.0 | 只记最近 10 步：窗口内满分，滑出即崩塌 |
| perfect_memory | 0.0 | 1.0 | 1.0 | 完美记忆上界（oracle） |

```
window_agent  (probe accuracy by step decile)
  步   1-10  ██████████████████████████████ 100%
  步  11-20  ███████                        22%
  步  21-30  ██                             6%
  步  41-50                                 0%
  步  91-100                                0%
```
**看点**：真实模型的 retention 曲线会落在崩塌线与 oracle 之间——位置即其「耐力」。跑 `python3 scripts/curve.py predictions_*.jsonl` 直接对比多模型曲线。

## 跑真实模型
```bash
export OPENAI_API_KEY=...     # 任意 OpenAI 兼容端点
python3 scripts/run_model.py --model <模型名> [--base-url <端点>]
python3 scripts/score.py predictions_<模型名>.jsonl
python3 scripts/curve.py predictions_<模型名>.jsonl   # ASCII retention 曲线
```
`run_model.py` 按真实多轮对话回放 episode（逐步累积历史），探针步记录模型原话再评分。

## 质量保证
`scripts/check_bench.py` + CI：schema、探针覆盖、**gold 重算校验**（state 探针答案由步骤花费逐步累加重算，改 gold 必被抓）、干扰步存在性、领域与长度配比。**禁止靠删 episode 或改 gold 骗过校验。**

## 诚实说明
v1、12 episodes / 900 步 / 120 探针 / 24 干扰步、单人构建、双模拟基线——**能跑通、有论点、可复现**。episode 为合成确定性工作流，测记忆/状态维持/抗干扰能力，不测领域知识。路线图（目标漂移探针、200+ 步、多模型 retention 曲线榜）见 [PLAN.md](PLAN.md)。设计细节见 [docs/design.md](docs/design.md)。许可 CC BY 4.0。
