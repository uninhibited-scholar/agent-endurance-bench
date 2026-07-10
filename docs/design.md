# 设计说明 · design

## 测什么
所有 agent 评测都在测「单个任务能不能做对」。本基准测的是另一个维度：**跑了 30–50 步之后，agent 还记得开局约束吗？还在正确追踪状态吗？**——即长任务下的**退化（degradation）**：遗忘约束、状态漂移、目标漂移。

## Episode 结构
每个 episode 是一段确定性的 50 步工作流（IT 工单 / 采购 / 客服三个领域）：

1. **开局约束**（system 消息）：分派规则表、初始预算、禁止项。
2. **task 步**：常规工作步，每步产生一笔花费（改变内部状态）。
3. **probe 步**（第 5,10,…,50 步注入，共 10 个）：
   - `constraint` 探针——按开局规则该派给谁？（三选一，gold = 选项字母）
   - `state` 探针——当前剩余预算多少？（gold = 数字，可由步骤花费重算校验）

探针答案封闭 → **纯机器评分**，无需 LLM 裁判；生成器带种子 → **完全可复现**。

## 指标
| 指标 | 含义 |
|---|---|
| `retention_curve` | early(≤10) / mid(11–30) / late(31–50) 三段探针准确率 |
| `degradation_slope` | early − late；0 = 无退化，越大越退化 |
| `constraint_accuracy` | 约束回忆准确率（规则忘没忘） |
| `state_accuracy` | 状态追踪准确率（账算没算对） |
| `endurance_score` | late 段准确率——30 步之后还剩多少能力 |

## 数据字段
```json
{
  "id": "ep-it-ticket-1", "domain": "it-ticket", "n_steps": 50,
  "budget0": 8000, "constraints": "……开局规则……",
  "steps": [
    {"step": 1, "type": "task", "input": "第1步：新工单…花费 80 元…", "cost": 80},
    {"step": 5, "type": "probe", "probe_kind": "state", "input": "【探针】剩余预算…", "gold": "7690"}
  ]
}
```

## 为什么基线选「滑动窗口 agent」
K=10 滑窗 agent 是对「上下文装不下 / 记忆被截断」的最小模拟：窗口内的探针全对（early 1.0），信息滑出窗口后崩塌（late 0.083），退化斜率 0.917——证明指标对"遗忘"高度灵敏。真实长上下文模型的曲线会落在滑窗基线与完美记忆（斜率 0）之间，位置即其耐力。

## 防作弊
`check_bench.py` 重算每个 state 探针的 gold（由步骤花费累加），改 gold 或删 episode 都会 FAIL。
