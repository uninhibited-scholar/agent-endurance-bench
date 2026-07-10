# PLAN · agent-endurance-bench

## 目标
全球范围内第一批专测 **agent 长任务退化** 的可复现基准：单任务成功率之外的另一维度——第 30–50 步后，agent 是否遗忘约束、状态漂移。中文任务载体（延续 uninhibited-scholar 中文评测矩阵），但测的问题全球通用。

## 验收（v1，已达成 ✅）
- [x] 种子化生成器 `scripts/gen_episodes.py`：12 episodes（50 步 ×6 + 100 步 ×6）× 3 领域，900 步 / 120 探针 / 24 干扰步，完全可复现。
- [x] 新增 `resist` 抗干扰探针 + distractor 干扰步（无审批码规则变更、假预算数）。
- [x] `scripts/curve.py` ASCII retention 曲线，多模型直接对比。
- [x] 双基线：window_agent（崩塌线 slope 0.933）+ perfect_memory（oracle 上界 slope 0.0）。
- [x] 探针封闭 gold（选项字母 / 数字），`scripts/score.py` 纯机器评分：retention_curve / degradation_slope / constraint_accuracy / state_accuracy / endurance_score。
- [x] `scripts/check_bench.py` + CI：schema、探针覆盖、**gold 重算校验**（state 探针由花费累加重算）、防作弊。
- [x] 滑窗基线 `baselines/window_agent.py`（K=10）：early 1.0 → xlong 0.067，slope 0.933，resist 0.0。
- [x] `scripts/run_model.py`：真实多轮对话回放（system=约束，逐步累积历史），任意 OpenAI 兼容端点。

## v1 基线结果
| 基线 | slope ↓ | endurance ↑ | resist ↑ |
|---|---:|---:|---:|
| window_agent (K=10) | 0.933 | 0.061 | 0.0 |
| perfect_memory (oracle) | 0.0 | 1.0 | 1.0 |

## 路线图
- **v2 数据**：目标漂移探针（任务目标本身被带偏）、200+ 步 episode、多干扰叠加。
- **v1.x**：多模型排行榜（GLM / Qwen / DeepSeek / Doubao + GPT / Claude），画各模型 retention curve 对比图。
- **v2**：工具调用版 episode（约束表现为工具使用规则），与 [agent-safety-bench-zh](https://github.com/uninhibited-scholar/agent-safety-bench-zh) 打通。

## 边界
- Episode 为合成确定性工作流，非真实企业数据；测的是记忆/状态维持能力，不测领域知识。
- 许可 CC BY 4.0。
