# agent-endurance-bench

逐步累积上下文中的**状态追踪与指令保持**评测（long-horizon state-tracking & instruction retention · 可机器评分 · 种子化可复现）。俗称"agent 耐力"，但准确说测的是：多轮累积对话里模型对开局约束、数值状态和未授权变更的保持能力——**不覆盖**带外部记忆、摘要压缩、工具调用或自检策略的完整 agent 系统。

[![CI](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml/badge.svg)](https://github.com/uninhibited-scholar/agent-endurance-bench/actions/workflows/validate.yml)
[![License: CC BY 4.0](https://img.shields.io/badge/license-CC%20BY%204.0-green.svg)](https://creativecommons.org/licenses/by/4.0/)

主流 agent 评测（AgentBench / GAIA / SWE-bench 类）以单任务成功率为主轴；长上下文与指令保持已有专门评测，但**逐步累积 + 封闭可重算 gold + 干扰注入**的组合是本项目关注的缺口。本基准测：**跑到第 50–100 步之后，agent 还记得开局约束吗？账还算得对吗？未经授权的"规则变更"能不能把它带偏？**——长任务下的遗忘、状态漂移与抗干扰。

## 怎么测
15 个种子化生成的确定性 episode（IT 工单 / 采购 / 客服 × 标准 50 步 ×2 + 长程 100 步 ×2 + **v2 高压 200 步 ×1**），共 1500 步、180 个探针、42 个干扰步。v2 高压层新增：**退款回补（负数算术）、同一谎言重复 3 次、携带错误审批码的规则变更、假预算反复提及**：

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
| `retention_curve` | — | early(≤10)/mid(11–30)/late(31–50)/xlong(51–100)/xxlong(101–200) 探针准确率 |
| `degradation_slope` | ↓ | early − 最深段，0 = 无退化 |
| `constraint_accuracy` | ↑ | 规则忘没忘 |
| `state_accuracy` | ↑ | 账算没算对 |
| `resist_accuracy` | ↑ | 假"规则变更"顶没顶住 |
| `endurance_score` | ↑ | 30 步之后的探针准确率 |

## 基线：崩塌线与上界
| 模型/基线（v2 全量 180 探针） | slope ↓ | endurance ↑ | constraint ↑ | state ↑ | resist ↑ | xxlong ↑ |
|---|---:|---:|---:|---:|---:|---:|
| window_agent (K=10) | 0.833 | — | — | — | 0.0 | 0.167 |
| glm-5.2 | 0.30 | 0.795 | 0.965 | 47/69 (0.681) | **1.0** | 21/30 [0.52,0.83] |
| **deepseek-v4-flash** | **0.0** | **1.0** | **1.0** | 69/69 | **1.0** | 30/30 [0.89,1.00] |
| perfect_memory (oracle) | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

**v2 成功拉开两模型**：glm-5.2 的退化随深度持续放大——state 探针从 v1 的 0.812 掉到 0.681，xxlong（101–200 步）段只剩 70%，slope 从 0.167 恶化到 0.30；错误全部是累计预算算错（级联误差、答过期旧值），规则记忆 96.5%、抗带偏 100% 依旧坚挺。**退化形态锁定："记得规则、算错账"，且账越长错得越多**。deepseek-v4-flash 则 **180 探针全对**——负数算术、错误审批码、重复谎言全部顶住，v2 对它仍是天花板之下。

> 评分器说明：v1.1 修复了 norm 解析（模型答对但附加说明文字时先取首行），修复后 deepseek 从表面 0.917 修正为 1.0；glm-5.2 分数不变（其错误为真实算错/漂移）。诚实披露：glm-5.2 部分探针 content 为空、回退取推理链尾部，其真实分数可能略被低估。

```
window_agent  (probe accuracy by step decile)
  步   1-10  ██████████████████████████████ 100%
  步  11-20  ███████                        22%
  步  21-30  ██                             6%
  步  41-50                                 0%
  步  91-100                                0%
```
**看点**：真实模型曲线落在崩塌线与 oracle 之间——glm-5.2：early 100% → xlong 80% → xxlong 70%；deepseek：全程 100%。跑 `python3 scripts/curve.py predictions_*.jsonl` 直接对比。

**诚实披露**：deepseek-v4-flash 连续打满 v1/v2，当前难度对它已饱和——只能给"≥此难度无退化"的下界结论。xxlong 段仅 3 个 episode/30 探针，且同 episode 内探针高度相关，方括号 Wilson 95% CI 很宽；gold 确定性公开（生成器可重建），**非隐藏测试集，不抗污染**，榜单为基准内结论，不外推模型一般能力。v3 扩难方向：干扰写进任务步而非独立步（无法按步类型忽略）、多约束交叉（预算×禁止项×规则同时探）、任务文本噪声化、500 步级 episode。

## 跑真实模型
```bash
export OPENAI_API_KEY=...     # 任意 OpenAI 兼容端点
python3 scripts/run_model.py --model <模型名> [--base-url <端点>]
python3 scripts/score.py predictions_<模型名>.jsonl
python3 scripts/curve.py predictions_<模型名>.jsonl   # ASCII retention 曲线
```
`run_model.py` 按真实多轮对话回放 episode（逐步累积历史），探针步记录模型原话再评分。

## 质量保证
`scripts/check_bench.py` + CI 做**结构与内部一致性校验**：schema、探针覆盖、state gold 重算（由花费累加重建）、干扰步存在性、配比；CI 另跑 **确定性锁**——重新执行种子化生成器并 `git diff --exit-code`，数据与生成器不一致（删 episode、改 gold、改题面）即 FAIL。改动必须体现在生成器代码 diff 中，强制可审查。

## 诚实说明
v1、12 episodes / 900 步 / 120 探针 / 24 干扰步、单人构建、双模拟基线——**能跑通、有论点、可复现**。episode 为合成确定性工作流，测记忆/状态维持/抗干扰能力，不测领域知识。路线图（目标漂移探针、200+ 步、多模型 retention 曲线榜）见 [PLAN.md](PLAN.md)。设计细节见 [docs/design.md](docs/design.md)。许可 CC BY 4.0。
