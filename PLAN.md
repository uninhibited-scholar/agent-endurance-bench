# PLAN · agent-endurance-bench

## 目标
专测**逐步累积上下文中的状态追踪/指令保持**（俗称 agent 长任务退化）的可复现基准，此组合（累积回放+确定性公开可重算 gold+干扰注入）为本项目关注的缺口：单任务成功率之外的另一维度——第 30–50 步后，agent 是否遗忘约束、状态漂移。中文任务载体（延续 uninhibited-scholar 中文评测矩阵），但测的问题全球通用。

## 验收（v1，已达成 ✅）
- [x] 种子化生成器 `scripts/gen_episodes.py`：12 episodes（50 步 ×6 + 100 步 ×6）× 3 领域，900 步 / 120 探针 / 24 干扰步，完全可复现。
- [x] 新增 `resist` 抗干扰探针 + distractor 干扰步（无审批码规则变更、假预算数）。
- [x] `scripts/curve.py` ASCII retention 曲线，多模型直接对比。
- [x] 双基线：window_agent（崩塌线 slope 0.933）+ perfect_memory（oracle 上界 slope 0.0）。
- [x] 探针确定性公开 gold（选项字母 / 数字），`scripts/score.py` 纯机器评分：retention_curve / degradation_slope / constraint_accuracy / state_accuracy / endurance_score。
- [x] `scripts/check_bench.py` + CI：schema、探针覆盖、**gold 重算校验**（state 探针由花费累加重算）、防作弊。
- [x] 滑窗基线 `baselines/window_agent.py`（K=10）：early 1.0 → xlong 0.067，slope 0.933，resist 0.0。
- [x] `scripts/run_model.py`：真实多轮对话回放（system=约束，逐步累积历史），任意 OpenAI 兼容端点。

## v1 基线结果
| 基线 | slope ↓ | endurance ↑ | resist ↑ |
|---|---:|---:|---:|
| window_agent (K=10) | 0.933 | 0.061 | 0.0 |
| perfect_memory (oracle) | 0.0 | 1.0 | 1.0 |

## 路线图
- **v2 已完成 2026-07-11**：3×200 步高压 episode（负数算术/同谎×3/错误审批码/假预算），成功拉开双模型：glm-5.2 slope 0.30、xxlong 0.70、state 0.681；deepseek 180 探针全对（饱和）。
- **v3 已完成 2026-07-11**：3×500步、干扰内嵌task步、cross多约束探针。glm state@500 崩到 5/39(13%)、slope 0.502；deepseek 330探针连续第三次全对。
- **v4（需质变）**：deepseek 对"规则记忆+数值状态"类构造已饱和，量变无效。候选方向：(a) 探针依赖多步推理链而非单步查表；(b) 需要模型主动发现矛盾（如预算将超支需提前预警）；(c) 无确定性gold的开放子任务改用程序化断言。
- **v1.x**：多模型排行榜（GLM / Qwen / DeepSeek / Doubao + GPT / Claude），画各模型 retention curve 对比图。
- **v2**：工具调用版 episode（约束表现为工具使用规则），与 [agent-safety-bench-zh](https://github.com/uninhibited-scholar/agent-safety-bench-zh) 打通。

## 边界
- Episode 为合成确定性工作流，非真实企业数据；测的是记忆/状态维持能力，不测领域知识。
- 许可 CC BY 4.0。
