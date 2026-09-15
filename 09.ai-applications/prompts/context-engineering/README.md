<!--
module:
  parent: prompts
  slug: prompts/context-engineering
  type: index-only
  category: Context Engineering
  summary: Context Engineering（上下文工程）专题 —— Prompt 设计、上下文窗口管理、注意力分配的系统化方法
  depth: ⭐
-->

# Context Engineering 上下文工程

> **定位**：广义 Prompt 设计 + 上下文窗口管理 + 注意力分配的系统化方法论。不只是"写好 Prompt"，而是**如何在有限 context window 内最大化 LLM 输出质量**。

---

## 子文章清单（共 1 篇，find 校对 2026-08-20）

| 主题 | 难度 | 一句话核心 | 入口 |
|------|------|-----------|------|
| **Context Engineering 概念图谱** | ⭐⭐⭐ | 完整概念体系 + 实战策略地图（上下文构成 / 注意力机制 / 工具设计） | [concept-map.md](concept-map.md) |

---

## 关联主题

- **Prompt 工程**：[`../README.md`](../README.md) — 父级 Prompt 专题
- **Agent 架构**：[`../../agent/`](../../agent/) — Context Engineering 是 Agent 设计的核心
- **RAG**：[`../../rag/`](../../rag/) — Context Engineering 与 RAG 协同（检索即上下文增强）
- **评估方法**：[`../../eval/`](../../eval/) — 上下文设计的 A/B 评估

---

## 主题定位与适用人群

Context Engineering 是 2024-2025 年提出的**比 Prompt 工程更广**的概念,核心是把"如何用好 LLM 的输入"系统化为工程方法论。它包含但不限于:

- Prompt 文本(System Prompt / User Prompt / Few-shot)
- 检索增强(RAG 召回的文档)
- 工具调用(Tool / Function schema)
- 对话历史(Memory / Conversation buffer)
- 注意力分配(在长 context 中如何让 LLM 关注关键信息)

**适用人群**:

- ✅ 任何在做 LLM 应用的工程师——Context Engineering 是底层必备知识
- ✅ Agent 架构师——Agent 的"思考质量"本质就是 Context Engineering 的质量
- ✅ Prompt 工程师进阶——从"调 Prompt 措辞"升级到"设计整个输入上下文"
- ✅ 在做 RAG / 长文档处理 / 工具调用设计的工程师
- ✅ 准备 AI 面试——Context Engineering 是高频考点

**不适合**:只调 ChatGPT 简单问答的用户(用 [../prompt-engineering/](../prompt-engineering/) 入门即可);做模型训练的人(去 [../../../08.ai-foundations/](../../../08.ai-foundations/))。

## 阅读路径详解

### 阶段 0:Prompt 工程入门(如果还没看过)

1. 先读 [../README.md](../README.md) — 父级 Prompt 专题,建立 Few-shot / CoT / 温度 等基础概念
2. 再读 [../prompt-engineering/prompt-templates/](../prompt-engineering/prompt-templates/) — 看 Prompt 模板的设计模式
3. 然后回到这里读 [concept-map.md](concept-map.md) — 从"Prompt 文本"扩展到"整个上下文"

### 阶段 1:Context Engineering 入门(2-3 天)

1. 通读 [concept-map.md](concept-map.md) — 建立完整概念体系
2. 关注"上下文构成"和"注意力机制"两个核心章节
3. 配合 [`../../agent/`](../../agent/) 中的 Agent 案例,看 Context Engineering 在真实 Agent 中如何落地

### 阶段 2:深入应用(1-2 周)

1. 结合 [`../../rag/`](../../rag/) — 检索结果如何放入上下文、放在什么位置
2. 结合 [`../../agent/agent-memory/`](../../agent/agent-memory/) — 对话历史如何压缩 / 摘要 / 检索
3. 结合 [`../../agent/agent-execution-patterns/`](../../agent/agent-execution-patterns/) — ReAct / Plan-Execute 中工具调用结果如何格式化回上下文

### 阶段 3:高级 / 实战优化(持续)

- [concept-map.md](concept-map.md) 中的"工具设计"和"长上下文处理"专题
- 对照 [`../../llm-inference/`](../../llm-inference/) — Context Window 的成本(越长越贵)
- 对照 [`../../eval/`](../../eval/) — A/B 评估上下文设计的有效性

## 与相邻主题的反向链

- **[../README.md](../README.md)** — 父级 Prompt 专题。Context Engineering 是 Prompt 工程的超集和升级。
- **[../../agent/](../../agent/)** — Agent 是 Context Engineering 最重要的应用场景。每个 Agent 步骤都是一次 Context Engineering。
- **[../../rag/](../../rag/)** — RAG 的核心是"把检索到的内容作为上下文喂给 LLM",本质是 Context Engineering 的一种实现。
- **[../../agent/agent-context/](../../agent/agent-context/)** — Agent 的 Context 管理(短期/长期/记忆),是 Context Engineering 在 Agent 中的具体落地。
- **[../../eval/](../../eval/)** — 上下文设计没有标准答案,必须靠 A/B 测试 + 回归评测验证。
- **[../../llm-inference/](../../llm-inference/)** — Context Window 越长,推理成本越高。Context Engineering 也是成本优化的一部分。
- **[../../../08.ai-foundations/](../../../08.ai-foundations/)** — 理解 LLM 的 Attention 机制(Lost-in-Middle 等),才能做"注意力分配"的工程化。

## 常见误区与选型陷阱

1. **❌ "Prompt 工程 = Context Engineering"**
   - ✅ Prompt 工程只是 Context Engineering 的一部分。Context Engineering 还包括检索、工具、对话历史、注意力分配。

2. **❌ "Context 越长越好"**
   - ✅ LLM 的 attention 有 **Lost-in-Middle** 现象:中间位置的信息容易被忽略。**关键信息放首尾,冗余信息放中间压缩或删除**。

3. **❌ "检索到的内容越多越好"**
   - ✅ 检索召回的 top-k 不是越大越好。**过多噪音会让 LLM 注意力分散**。配合 reranker 做"精排",通常 3-5 个 chunk 效果最佳。

4. **❌ "Few-shot examples 越多越好"**
   - ✅ Few-shot 会占用 context window,而且**示例会 bias 模型输出风格**。3-5 个高质量示例通常比 20 个示例效果更好。

5. **❌ "System Prompt 写一次就不改了"**
   - ✅ System Prompt 应该和代码一样**版本化管理**:变更要有记录、有 A/B 评估、有回滚能力。

6. **❌ "工具调用 schema 越详细越好"**
   - ✅ 工具 schema 过长会占用 context,且 LLM 不一定能"读懂"。**保持 schema 简洁,描述准确**。

7. **❌ "Context Engineering 只关注输入"**
   - ✅ 输出侧的结构化(让 LLM 输出 JSON / XML / Markdown)也是 Context Engineering 的一部分——**输出格式影响下一轮的输入**。

## 面试高频 vs 工程实战对照

| 面试高频(背) | 工程实战(理解) |
|--------------|----------------|
| "Context Engineering 是什么?" | 比 Prompt 工程更广的系统化方法论,涵盖 Prompt + RAG + 工具 + 记忆 + 注意力。 |
| "Lost-in-Middle 现象?" | LLM 对 context 中间位置的信息关注度低。**关键信息放首尾**。 |
| "Context Window 怎么选?" | 长 context 贵且慢,优先用 RAG / 摘要压缩。同时评估 Lost-in-Middle 风险。 |
| "RAG 和 Context Engineering 关系?" | RAG 是 Context Engineering 的**检索增强子集**。 |
| "Few-shot 怎么用?" | 3-5 个高质量示例。**示例太多 bias 输出、占 context**。 |
| "Prompt 版本管理怎么做?" | 模板文件 + Git 版本化 + A/B 评估 + 灰度上线。 |
| "为什么 System Prompt 比 User Prompt 重要?" | System Prompt 设定模型行为基线,影响所有后续交互。**生产中必须严格版本管理**。 |

> 配套 [`../../../12.interview/11.ai/`](../../../12.interview/11.ai/) 有专门的 Context Engineering 面试题与陷阱版。

## 实战检查清单(速查版)

每次设计新的 LLM 应用前,过一遍这个清单:

- [ ] **Prompt 文本**:System Prompt / User Prompt 分开管理、版本化
- [ ] **检索增强**:是否需要 RAG?召回 top-k 是多少?是否需要 reranker?
- [ ] **工具调用**:工具 schema 是否简洁?工具描述是否准确?
- [ ] **对话历史**:短期 / 长期记忆如何区分?是否需要摘要压缩?
- [ ] **注意力分配**:关键信息放首尾,冗余信息压缩或删除
- [ ] **输出格式**:是否需要结构化输出(JSON / XML)?对下游处理更友好
- [ ] **A/B 评估**:context 设计有量化指标吗?有回归集吗?
- [ ] **成本意识**:context 越长越贵,是否值得?

## 子文章预告与扩展阅读

本目录当前收录 1 篇核心文章 [concept-map.md](concept-map.md),后续计划补充:

- **实战策略篇**:基于真实案例的 Context Engineering 优化(对话机器人 / Agent / RAG 三大场景)
- **常见反模式篇**:从生产事故中总结的 Context 设计错误
- **工具链篇**:Context Window 可视化分析、Token 预算管理、A/B 测试工具

扩展阅读推荐:

- [concept-map.md](concept-map.md) — 本目录核心,必读
- [`../prompt-engineering/prompt-templates/`](../prompt-engineering/prompt-templates/) — Prompt 模板,Context Engineering 的起点
- [`../../rag/lost-in-middle/`](../../rag/lost-in-middle/) — Lost-in-Middle 现象的工程化对策
- [`../../agent/agent-context/context-engineering/`](../../agent/agent-context/context-engineering/) — Context Engineering 在 Agent 中的应用
- [`../../../12.interview/11.ai/`](../../../12.interview/11.ai/) — 面试高频陷阱题与 30 秒话术

---

← [返回 Prompt 专题总览](../README.md)