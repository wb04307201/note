<!--question:
  id: 11.ai-rag-evaluation
  topic: 11.ai
  difficulty: ⭐⭐⭐⭐
  frequency: 高频
  scenario_type: 反直觉代码
  tags: [11.ai, RAG, 评测, RAGAS, faithfulness, LLM-as-Judge, 黄金集]
  status: active
-->

# RAG 评测只看准确率召回率？—— 6 维评测体系 + 黄金集构建

> 一句话定位：RAG 评测不止「准确率 + 召回率」——完整维度是 **检索 × 生成 × 系统 × Agentic × LLM-as-Judge × 业务** 6 维矩阵。以为「超过 90% 截图汇报」就是初学者误区。完整深度见 [主模块 RAG 评估指标与工具](../../../09.ai-applications/rag/04-evaluation.md)。

> **系列定位**：经典 AI 工程面试题（字节 / 阿里 / 美团 / 滴滴 / 腾讯 出题率 80%+）。考察的不是「RAG 怎么用」，而是 **「如何系统评测 RAG」+「初学者朴素流程的 5 大反模式」+「LLM-as-Judge 的 5 大偏差」**。

---

## 引子：「超过 90% 截图汇报」的初学者误区

面试官：「你们怎么评测 RAG 系统的？」

候选人 A：「准备 100 个问题，看看检索的文档对不对，再算一下准确率和召回率，超过 90% 就 OK。」

面试官追问：「Faithfulness 看过吗？LLM-as-Judge 跟人类评估对齐过吗？线上指标监控了吗？」

候选人 A 卡壳。

**反直觉**：以为「**准确率 + 召回率 ≥ 90%**」就 OK 是初学者最大误区 —— 这只能覆盖**检索维度**，完全忽略**生成质量 / 幻觉 / 工程表现 / 业务指标**。

---

## 一、核心原理

### 1.1 朴素评测流程 vs 完整 6 维矩阵

**初学者朴素流程**（5 步）：

```text
1. 准备 100 个问题
2. 检索 Top-K 文档
3. 看文档对不对
4. 算准确率 + 召回率
5. 超过 90% 截图汇报
```

**问题**：只看检索维度，**完全忽略生成质量**（Faithfulness / Answer Relevancy）、**幻觉**、**线上表现**、**业务指标**。

**完整 6 维评测矩阵**：

| 维度 | 子指标 | 工具 | 解决的问题 |
|------|--------|------|-----------|
| **1. 检索维度** | Context Precision / Recall / MRR / NDCG | RAGAS / TruLens | 检索的文档对不对 |
| **2. 生成维度** | Faithfulness / Answer Relevancy / Correctness | RAGAS / DeepEval | 答案有没有幻觉 / 是否回答了问题 |
| **3. 系统维度** | Latency / Cost / User Feedback | 自研 / Langfuse | 跑得稳不稳 / 用户买不买账 |
| **4. Agentic 维度** | Task Success / Tool Call Accuracy / Self-Correction | RAGAS + 自研 | 多步智能体场景 |
| **5. LLM-as-Judge 校准** | 与人类评估对齐（> 0.8） | 人工标注 + Pearson 相关 | 评测工具本身的偏差 |
| **6. 业务维度** | 转化率 / 客诉率 / 留存率 | 业务埋点 | 真正的商业价值 |

### 1.2 反直觉 1：准确率 ≠ Faithfulness

- 检索的文档对 → LLM 可能**曲解文档内容**或**添加原文没有的信息**
- 这就是「**忠实性幻觉**」—— RAG 解决「有据可依」，但不能 100% 保证「据实生成」
- **必须看 Faithfulness 指标**（RAGAS 的核心指标之一）

### 1.3 反直觉 2：LLM-as-Judge 也有偏差

| 偏差类型 | 表现 | 缓解 |
|---------|------|------|
| **位置偏差** | 偏好放在前面的答案 | 多次随机位置打分取均值 |
| **长度偏差** | 偏好更长的答案 | 标准化答案长度 |
| **自评偏差** | GPT-4 偏好 GPT-4 的输出 | 多模型交叉评估 |
| **格式偏差** | 偏好 Markdown / 列表 | 结构化输出 |
| **知识偏差** | 用自己已知知识评判（而非 context） | Prompt 强制「仅基于 context」 |

### 1.4 反直觉 3：离线评估 ≠ 线上表现

- 离线黄金集**不代表真实用户 query 分布**
- 必须做**线上 A/B Test + 持续监控**
- 指标下降 > 5% 立即告警

### 1.5 反直觉 4：Faithfulness ≠ Answer Relevancy

| 指标 | 关注点 | 失败信号 |
|------|--------|---------|
| **Faithfulness** | 答案是否忠于 context（无幻觉） | 答案包含 context 没有的信息 |
| **Answer Relevancy** | 答案是否回答了用户问题 | 答非所问 / 跑题 |

---

## 二、代码示例

### 2.1 完整 RAG 评测（RAGAS 0.2+）

```python
from ragas import evaluate
from ragas.dataset_schema import EvaluationDataset, SingleTurnSample
from ragas.metrics import (
    LLMContextPrecisionWithReference,  # 检索精确率
    LLMContextRecall,                  # 检索召回率
    Faithfulness,                      # 答案忠实度（无幻觉）
    ResponseRelevancy,                 # 答案相关度
    AnswerCorrectness,                 # 答案正确度
)

# 1. 准备黄金集（100-500 条，覆盖 4 类问题）
samples = [
    SingleTurnSample(
        user_input="什么是 RAG？",
        retrieved_contexts=["RAG 是检索增强生成..."],
        response="RAG 是一种结合检索和生成的技术...",
        reference="检索增强生成，结合外部知识...",
    ),
    # ... 100-500 条
]
dataset = EvaluationDataset(samples=samples)

# 2. 多指标评估（不要只跑 1 个指标！）
result = evaluate(
    dataset,
    metrics=[
        LLMContextPrecisionWithReference(),  # 检索
        LLMContextRecall(),                  # 检索
        Faithfulness(),                      # 生成（最关键）
        ResponseRelevancy(),                 # 生成
        AnswerCorrectness(),                 # 生成
    ],
)

print(result)
# {'context_precision': 0.85, 'context_recall': 0.78,
#  'faithfulness': 0.92, 'answer_relevancy': 0.88,
#  'answer_correctness': 0.86}

# ⚠️ Faithfulness < 0.8 → 幻觉风险高，必须优化
```

### 2.2 LLM-as-Judge 与人类评估对齐

```python
from scipy.stats import pearsonr

# 1. 人类标注（200-500 条）
human_scores = [0.9, 0.7, 0.85, 0.6, ...]  # 人类标注 0-1 分

# 2. LLM-as-Judge 评分
llm_scores = []
for item in dataset:
    score = llm_judge(
        prompt=f"基于以下 context 评分 0-1：\nContext: {item.context}\nAnswer: {item.response}"
    )
    llm_scores.append(score)

# 3. 计算对齐（Pearson 相关系数）
correlation, _ = pearsonr(human_scores, llm_scores)
print(f"LLM-Judge vs Human correlation: {correlation:.3f}")

# ✅ correlation > 0.8 → LLM-as-Judge 可信
# ❌ correlation < 0.6 → 必须重新校准 Prompt 或换模型
```

### 2.3 黄金集构建 4 类覆盖

```text
100-500 条黄金集必须覆盖：
├─ 简单问题（60%）：基础事实查询，"公司 XX 政策"
├─ 复杂问题（20%）：多跳推理，"对比 X 和 Y 的优劣"
├─ 边界问题（10%）：超范围，"竞品 XX 的策略" → 期望拒答
└─ 错误问题（10%）：诱导陷阱，"如果文档说 X 是错的..."
```

---

## 三、常见陷阱（5 大反模式）

### 陷阱 1：只看准确率 + 召回率

- 错：`accuracy = 0.95, recall = 0.90` 就截图汇报
- 对：**至少看 4 个指标**：Context Precision / Recall + Faithfulness + Answer Relevancy

### 陷阱 2：用单一黄金集评估 1 次就上线

- 错：跑 1 次 RAGAS 看到分数 OK 就上线
- 对：**分层评估**（开发期小集 + 上线前大集 + 上线后线上监控）

### 陷阱 3：Faithfulness 指标用 OpenAI 默认 GPT-4

- 错：用 GPT-4 直接做 Judge —— **自评偏差**（GPT-4 偏好 GPT-4 的输出）
- 对：**多模型交叉**（GPT-4 + Claude + Gemini 取平均）或**人工校准**

### 陷阱 4：把「线上 A/B Test」等同「线上监控」

- 错：A/B Test 跑 1 周看转化率，就以为系统稳了
- 对：**持续指标监控**（每周自动跑黄金集 + Faithfulness 告警阈值）

### 陷阱 5：用 RAG 准确率汇报领导，但不解决幻觉

- 错：「领导，我们 RAG 准确率 95%」 —— 领导问「为什么用户投诉答案胡说八道」时无言以对
- 对：**Faithfulness 是安全底线**，必须先于准确率达标

---

## 四、最佳实践（4 步上线流程）

### 步骤 1：开发期（小黄金集 + 离线）

```text
100 条黄金集（含 4 类问题）
跑 RAGAS 4-6 个指标
→ 优化检索 / Prompt / Chunking
```

### 步骤 2：上线前（大黄金集 + 多模型 Judge）

```text
500 条黄金集
多模型 LLM-as-Judge 交叉评估
与人类评估对齐（> 0.8 correlation）
→ 灰度发布
```

### 步骤 3：上线后（线上 A/B Test）

```text
10% 流量跑新版本
指标：转化率 / 客诉率 / Faithfulness（线上抽样）
→ 全量发布
```

### 步骤 4：长期（持续监控 + 自动告警）

```text
每周自动跑 100 条线上 query
Faithfulness 下降 > 5% → 告警
每月人工抽样核对（200 条）
→ 迭代优化
```

---

## 五、面试话术（90 秒版本）

> 「**RAG 评测只看准确率和召回率是初学者误区。** 完整评测是 **6 维矩阵**——
>
> **1️⃣ 检索维度**：Context Precision / Recall / MRR / NDCG —— 看检索的文档对不对
> **2️⃣ 生成维度**：Faithfulness / Answer Relevancy / Correctness —— 看答案有没有幻觉
> **3️⃣ 系统维度**：Latency / Cost / User Feedback —— 看跑得稳不稳
> **4️⃣ Agentic 维度**（多步场景）：Task Success / Tool Call Accuracy / Self-Correction
> **5️⃣ LLM-as-Judge 校准**：必须与人类评估对齐，**correlation > 0.8** 才可信
> **6️⃣ 业务维度**：转化率 / 客诉率 —— 看真正的商业价值
>
> **3 大反直觉**：
> 1️⃣ **准确率 ≠ Faithfulness**：检索对 → LLM 可能曲解或添加原文没有的信息 → **忠实性幻觉**
> 2️⃣ **LLM-as-Judge 也有偏差**：位置偏差 / 长度偏差 / 自评偏差 → 必须多模型交叉 + 人工校准
> 3️⃣ **离线评估 ≠ 线上表现**：必须持续监控 + A/B Test + 告警阈值
>
> **黄金集构建**：100-500 条覆盖 4 类问题（简单 / 复杂 / 边界 / 错误）。
> **上线流程**：开发期小集 → 上线前大集 + 多模型 Judge → 上线后 A/B Test → 长期持续监控。
>
> **典型反模式**：「领导，准确率 95%」 → 用户投诉答案胡说八道 → **Faithfulness 是安全底线，必须先于准确率达标**。
>
> 本质：**RAG 评测是 6 维系统工程，不是 1 维数字游戏**。」

---

## 六、交叉引用

- 主模块深度：[`09.ai-applications/rag/04-evaluation`](../../../09.ai-applications/rag/04-evaluation.md) —— 6 维指标 + RAGAS/TruLens/DeepEval 工具横评
- 兄弟章节：[RAG 架构设计](../rag/README.md) —— RAG Pipeline 综述
- 兄弟章节：[RAG 超范围拒答](../rag-out-of-domain-rejection/README.md) —— Faithfulness 的生产落地
- 兄弟章节：[RAG 权限隔离设计](../rag-permission-isolation/README.md) —— 4 种隔离方案

---

## 相关章节

- 同栏目：[Agent 性能量化](../agent-performance-evaluation/README.md) —— Agent 6 大评测维度
- 主模块：[`09.ai-applications/eval`](../../../09.ai-applications/eval/README.md) —— 评测框架总览

---

> 📅 2026-10-16 · 咬文嚼字 · 11.ai · ⭐⭐⭐⭐ · 6 维评测矩阵 + 5 反模式 + 4 步上线流程

← [返回: AI 咬文嚼字](../README.md)
