# 项目报告：中文网络弱点双评测基准（供外部 agent 审查）

日期：2026-07-11 · 作者：zhujiehan（GitHub: uninhibited-scholar）· 构建协作：Claude Code
本报告自包含，审查者无需本对话上下文。所有数字可由仓库内脚本零依赖复现。

---

## 0. 项目概述

一个母题、两个子项目：**围绕"中文网络/中文 AI 生态的现实弱点"构建可机器评分、可复现的评测基准**，并用真实模型跑出排行榜。

| 子项目 | 针对的弱点 | 仓库 | 版本轨迹 |
|---|---|---|---|
| fraud-detect-bench-zh | 电信网络诈骗（中文互联网重大现实危害面） | https://github.com/uninhibited-scholar/fraud-detect-bench-zh | v0(42条)→v1(80条) |
| agent-endurance-bench | 累积上下文状态追踪/指令保持（本项目关注的组合缺口） | https://github.com/uninhibited-scholar/agent-endurance-bench | v0(6ep)→v1(12ep)→v2(15ep) |

两者与作者已有基准（agent-safety-bench-zh「该拦的拦没拦」、defensive-refusal-bench-zh「不该拒的拒没拒」）构成矩阵；fraud 补"该识别的识别没"，endurance 把维度从单任务成功率扩展到时间轴。

共同工程原则：零依赖 Python（标准库）；**确定性、公开 gold**（随仓库分发，非隐藏测试集，不抗训练数据污染——榜单为基准内结论）；纯机器评分、无 LLM 裁判；种子化生成或人工构造、完全可复现；CI 做**结构与内部一致性校验 + 改动可见性锁定**（fraud：manifest 精确 ID 集合与逐条哈希；endurance：CI 重跑生成器 + `git diff --exit-code`——删样本/改 gold 而不显式改 manifest/生成器即 FAIL，改动强制进入可审查的 git diff）；CC BY 4.0；模型预测文件随仓库附带。

---

## 1. fraud-detect-bench-zh（中文诈骗识别评测）

### 1.1 任务定义
模型读一条中文短信/消息，输出 `{verdict: fraud|legit, category}`。9 类诈骗：冒充公检法 / 刷单返利 / 杀猪盘 / 客服退款 / 钓鱼链接 / 冒充熟人 / 虚假中奖 / 贷款代办 / 冒充物流。

### 1.2 数据（v1，80 条）
- 54 条 fraud（每类 5–7 条，难度 easy/medium/hard 混合）
- 26 条 legit **硬负样本**：真实正规但表面像诈骗的银行/政务/快递短信（含"补贴发放""境外消费提醒""96110 反诈劝阻"等高误报场景），专门惩罚"见词报警"
- 纯净度约束：不含真实域名/电话/账户，非可发送模板；无国家归因（CI 强制）

### 1.3 指标
fraud_recall ↑ / false_alarm_rate ↓ / category_accuracy ↑ / detection_gap = recall − false_alarm ↑

### 1.4 排行榜（全量 80 条）
| 模型 | recall | false_alarm | category | gap |
|---|---:|---:|---:|---:|
| keyword_guard（基线） | 0.537 | 0.462 | 0.724 | 0.075 |
| glm-5.2 | 54/54 [0.93,1.00] | 1/26 [0.01,0.19] | 49/54 [0.80,0.96] | 0.962 |
| deepseek-v4-flash | 54/54 [0.93,1.00] | 0/26 [0.00,0.13] | 47/54 [0.76,0.94] | 1.0 |

方括号为 Wilson 95% CI。两推理模型 vs 关键词基线差距显著；两模型之间（1/26 vs 0/26、49/54 vs 47/54）区间高度重叠，**不构成稳定排序**。

### 1.5 发现
1. **语义判别 vs 见词报警差 12 倍以上**（gap 0.962/1.0 vs 0.075）——基准核心论点成立。
2. **verdict 已被推理模型打满**，差异化战场移到类别归因（triage）。
3. 两模型**归因错法同构**：混合话术含"银保监会""禁毒大队"等机关字样即被带偏归为冒充公检法（glm 错 5 条、deepseek 错 7 条）。
4. v2 方向：提高混合话术与 hard 负样本比例，重新拉开 verdict 天花板。

---

## 2. agent-endurance-bench（累积上下文中的状态追踪/指令保持评测）

### 2.1 任务定义
准确定位：测**逐步累积多轮对话**中模型对开局约束、数值状态、未授权变更的保持能力（俗称 agent 耐力）。**不覆盖**带外部记忆、摘要压缩、工具调用或自检策略的完整 agent 系统。主流 agent 评测以单任务成功率为主轴，长上下文/指令保持已有专门评测；本项目的组合缺口是：累积回放 + 封闭可重算 gold + 干扰注入。

### 2.2 结构（v2，15 episodes / 1500 步 / 180 探针 / 42 干扰步）
3 领域（IT 工单/采购/客服）× {50 步×2、100 步×2、200 步高压×1}。每 episode：
- **开局约束**（system，仅一次）：分派规则表 + 初始预算 + 禁止项 + 规则变更须带审批码【OK-xxxx】
- **task 步**：每步花费，数值状态持续变化；v2 含**负数花费**（退款回补）
- **distractor 干扰步**：无审批码规则变更、假预算数；v2 加**同谎重复×3**、**携带错误审批码的规则变更**（考核对而非识别）
- **probe 探针**（gold 确定性、公开，可由生成器重建）：state（剩余预算，可由花费重算）/ constraint（规则三选一）/ resist（干扰后问当前有效规则）

### 2.3 指标
retention_curve（early≤10/mid/late/xlong/xxlong 101–200）· degradation_slope ↓ · constraint/state/resist_accuracy ↑ · endurance_score（>30 步准确率）↑

### 2.4 排行榜（v2 全量 180 探针）
| 模型/基线 | slope ↓ | endurance ↑ | constraint ↑ | state ↑ | resist ↑ | xxlong ↑ |
|---|---:|---:|---:|---:|---:|---:|
| window_agent K=10（崩塌线） | 0.833 | 0.061* | 0.417* | 0.25* | 0.0 | 0.167 |
| glm-5.2 | 0.30 | 0.795 | 0.965 | 47/69 (0.681) | 1.0 | 21/30 [0.52,0.83] |
| deepseek-v4-flash | **0.0** | **1.0** | **1.0** | 69/69 | **1.0** | 30/30 [0.89,1.00] |
| perfect_memory（oracle 上界） | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

*基线部分列为 v1 时数值，方向性不变。xxlong 仅 3 episode/30 探针且同 episode 内高度相关，CI 宽——glm 深处退化方向明确，但幅度估计不稳。

### 2.5 发现
1. **glm-5.2 退化形态锁定："记得规则、算错账，账越长错得越多"**——规则记忆 96.5%、抗带偏 100%，但 state 探针 v1 0.812 → v2 0.681，xxlong 段仅 70%；错误全部是累计预算级联误差（如 17580→17680 后续全错）或答过期旧值。
2. **deepseek-v4-flash 连续打满 v1/v2**（负数算术、错误审批码、重复谎言全顶住）——对最强模型本基准目前只能给"≥此难度无退化"的**下界结论**（README 已披露）。
3. v2 扩难**成功拉开双模型**（v1 时 slope 0.167 vs 0，v2 时 0.30 vs 0），证明难度轴有效。
4. v3 方向：干扰写进任务步（无法按步类型忽略）、多约束交叉探针、任务文本噪声化、500 步级。

---

## 2.6 外部审查采纳记录（2026-07-11）
独立审查复现全部主榜数字后提出 5 条意见，已全部落实并推送（两仓库 CI 绿）：
1. "封闭 gold"更正为"确定性、公开 gold"，README 明示非隐藏测试集、不抗污染；
2. "CI 防作弊"降级为"结构与内部一致性校验"，并补硬机制——fraud 加 data/MANIFEST.sha256（精确 ID 集 + 逐条哈希，负向测试：删 1 条样本 FAIL 已验证）、endurance CI 加"重跑生成器 + git diff --exit-code"确定性锁；
3. 榜单改为原始计数 + Wilson 95% CI，标注模型间不显著差距；
4. endurance 定位更名为"累积上下文中的状态追踪/指令保持"，明确不覆盖外部记忆/工具 agent；
5. "全球空白""最大危害面"等绝对措辞降级为"本项目关注的缺口"。

## 3. 诚实披露（审查者重点）

1. **评分器修复（endurance v1.1）**：初版 norm() 对"答对但附说明文字"的回复解析失败，deepseek 表面 11 错经人工核查全为解析缺陷；修复（先取首行再匹配）后 deepseek 0.917→1.0，glm 分数不变（其错误为真实算错），window 基线 sanity 不变。修复过程在 README 与 commit 历史中完整可查。
2. **glm-5.2 可能被低估**：其推理模式下部分探针 content 为空，run_model.py 回退取推理链尾部 200 字符，解析成功率低于正常 content。
3. **评测模型仅 2 个**：同一火山 Ark 端点的 glm-5.2 与 deepseek-v4-flash-260425；结论不宜外推到未测模型。
4. **合成数据边界**：endurance episode 为确定性合成工作流，测记忆/状态/抗干扰，不测领域知识；fraud 消息为人工编写识别目标，非真实语料。
5. **单人构建**：无第二标注者、无标注一致性检验；fraud 类别边界（如"冒充公检法"与"贷款诈骗中出现监管机构"）存在主观性——两模型归因分歧部分源于此。
6. **样本量**：fraud 80 条、endurance 180 探针，置信区间宽；榜上小差距（如 category 0.907 vs 0.87）不显著。

## 4. 复现
```bash
git clone https://github.com/uninhibited-scholar/fraud-detect-bench-zh && cd fraud-detect-bench-zh
python3 scripts/check_bench.py && python3 scripts/score.py predictions_glm-5.2.jsonl   # 无需 API key

git clone https://github.com/uninhibited-scholar/agent-endurance-bench && cd agent-endurance-bench
python3 scripts/gen_episodes.py   # 种子化，diff 应为空
python3 scripts/check_bench.py && python3 scripts/score.py predictions_deepseek-v4-flash-260425.jsonl
python3 scripts/curve.py predictions_*.jsonl
```
新模型上榜：`export OPENAI_API_KEY=…; python3 scripts/run_model.py --model <名> --base-url <OpenAI 兼容端点>`。

## 5. 提交历史（时间序）
fraud：v0 创建 → v1 扩量 80 条 → glm-5.2 上榜 → 预测文件附带 → deepseek 上榜（verdict 饱和结论）。
endurance：v0 创建 → v1（100 步/resist 探针/双基线/曲线）→ glm-5.2 上榜 → 预测文件附带 → 评分器修复 + deepseek 满分 → v2 扩难（200 步/负数/错码/叠加谎言）→ v2 终榜。
两仓库 CI（GitHub Actions 校验器 + 基线）全程绿。

## 6. 待办
- fraud v2：混合话术拉开 verdict 天花板；更多模型上榜
- endurance v3：干扰入任务步、多约束交叉、500 步级；更多模型（Qwen/Doubao/Claude/GPT）画多曲线对比
- 双基准发现整理为公开文章（素材已齐）
