# agent-endurance-bench

Agent 长任务「耐力/退化」评测基准（long-horizon degradation · 可机器评分 · 种子化可复现）。

[![CI](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

所有 agent 评测都在测「单个任务能不能做对」。本基准测另一个维度：**跑到第 30–50 步之后，agent 还记得开局约束吗？账还算得对吗？**——长任务下的遗忘、状态漂移与退化。这是 agent 真正落地时的核心痛点，而现有评测（AgentBench / GAIA / SWE-bench 类）几乎不覆盖。

## 怎么测
6 个种子化生成的确定性 episode（IT 工单 / 采购 / 客服 × 2），每个 50 步：
- **开局约束**：分派规则表 + 初始预算 + 禁止项（system 消息，只给一次）。
- **task 步**：常规处理步，每步产生花费（内部状态持续变化）。
- **probe 探针**（第 5,10,…,50 步，共 60 个）：
  - 约束回忆——「按开局规则，X 类该派给谁？」（三选一）
  - 状态追踪——「当前剩余预算多少？」（数字，可由花费重算）

探针 gold 封闭 → 纯机器评分，无 LLM 裁判；生成器带种子 → 完全可复现。

## 指标
| 指标 | 方向 | 含义 |
|---|---|---|
| `retention_curve` | — | early(≤10) / mid(11–30) / late(31–50) 探针准确率 |
| `degradation_slope` | ↓ | early − late，0 = 无退化 |
| `constraint_accuracy` | ↑ | 规则忘没忘 |
| `state_accuracy` | ↑ | 账算没算对 |
| `endurance_score` | ↑ | late 段准确率：30 步后还剩多少能力 |

## 基线：K=10 滑动窗口 agent
只记得最近 10 步的 agent（模拟上下文截断/无摘要记忆）：
```json
{
  "retention_curve": {"early": 1.0, "mid": 0.083, "late": 0.083},
  "degradation_slope": 0.917,
  "constraint_accuracy": 0.333,
  "state_accuracy": 0.2,
  "endurance_score": 0.083
}
```
**看点**：窗口内满分，信息滑出窗口即崩塌——**early 100% → late 8.3%**。真实模型的曲线会落在这条崩塌线与完美记忆（slope 0）之间，位置即其「耐力」。

## 跑真实模型
```bash
export OPENAI_API_KEY=...     # 任意 OpenAI 兼容端点
python3 scripts/run_model.py --model <模型名> [--base-url <端点>]
python3 scripts/score.py predictions_<模型名>.jsonl
```
`run_model.py` 按真实多轮对话回放 episode（逐步累积历史），探针步记录模型原话再评分。

## 质量保证
`scripts/check_bench.py` + CI：schema、探针覆盖、**gold 重算校验**（state 探针答案由步骤花费逐步累加重算，改 gold 必被抓）、领域覆盖。**禁止靠删 episode 或改 gold 骗过校验。**

## 诚实说明
v0、6 episodes / 300 步 / 60 探针、单人构建、模拟基线——**能跑通、有论点、可复现**的种子基准。episode 为合成确定性工作流，测记忆/状态维持能力，不测领域知识。路线图（干扰项、目标漂移探针、100+ 步、多模型 retention 曲线对比）见 [PLAN.md](PLAN.md)。设计细节见 [docs/design.md](docs/design.md)。许可 CC BY 4.0。
