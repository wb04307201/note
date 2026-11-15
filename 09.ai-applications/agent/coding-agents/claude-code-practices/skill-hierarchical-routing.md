<!--module:
  parent: ai
  slug: ai/claude-code-practices/skill-hierarchical-routing
  type: article
  category: 主模块子文章
  summary: Agent 选错 Skill 的路由架构解法——单层路由崩溃机理 + 三级渐进披露 + 级联分层路由（规则粗筛 → 命名空间收敛 → LLM 精排 → 拒识兜底）+ 成本账 + 漏斗评估。
  depth: ⭐⭐⭐⭐
  status: active
  tags: [Skill 分层路由, Progressive Disclosure, 级联路由, Skill 命中率]
-->

# Agent 总选错 Skill？分层路由（Hierarchical Routing）

> 一句话定位：选错 Skill 的根因往往不是"描述写得不够好"，而是**单层路由的候选数超过了单次判别的分辨力**。分层路由 = 把"50 选 1"拆成一串"5 选 1"——每层只做小规模判别，候选集逐级收敛，成本逐级上升、流量逐级下降。

> **同模块兄弟**：[skill-hit-rate.md](skill-hit-rate.md) 给出命中率的四层模型（描述/路由/加载/评估），其 **L2 路由层只讲了"规则 + LLM 兜底"一句话**；本文是 L2 的架构深潜——分层路由怎么设计、每层用什么 router、成本怎么算、漏斗怎么评估。[skill-design.md](skill-design.md) 管"单个 Skill 怎么写"，本文管"一堆 Skill 怎么选"。

> ⚠️ **术语辨析**：本文"分层路由"指 **Skill 候选集的分层收敛**（选对能力）；[成本上限与自动降级](../../production-stability/02-cost-control-and-degradation.md) 的"5 层路由"指 **模型成本的分级降级**（cache → cheap → big → SaaS → human，选对算力）。两者同构（级联 + 逐级兜底）但对象不同，面试时先问清指哪个。

---

## 一、单层路由为什么崩溃（机理，不是玄学）

Skill 数量 N 增长时，"把全部描述塞进一个 Prompt 让 LLM 直接选"的单层路由在 4 个维度同时退化：

| # | 崩溃维度 | 机理 | N=50 时的量级 |
|---|---------|------|--------------|
| 1 | **元数据常驻成本** | 官方机制：启动时把每个 Skill 的 name + description 注入 system prompt | ~100 token/Skill → **5k token 每轮常驻**，还没干活先烧钱 |
| 2 | **注意力稀释** | 候选描述在长列表中互相竞争注意力，中部条目被忽略（[Lost in Middle](../../../rag/lost-in-middle/README.md) 同一机理） | 排在列表中部的 Skill 命中率系统性偏低 |
| 3 | **描述碰撞对数爆炸** | 两两可能冲突的描述对是 $O(N^2)$，而写描述的人只按单个 Skill 视角优化 | 50 个 Skill = 1225 对潜在碰撞，人工审计不现实 |
| 4 | **LLM 选择漂移** | 同一 query 在不同上下文/措辞下选不同 Skill——判别边界模糊时输出不稳定 | 命中率方差大，无法回归 |

> **反直觉**：很多人第一反应是"把 description 写得更细"。描述优化只能缓解 #3，救不了 #1/#2——**常驻 token 和注意力稀释是架构问题，不是文案问题**。这就是为什么要动路由架构。

## 二、官方机制底座：三级渐进披露（Progressive Disclosure）

Anthropic Agent Skills 的设计本身就是分层的——分层路由是对这个机制的"路由侧对偶"：

```text
Level 1 · 元数据（常驻）   name + description，~100 token/Skill，注入 system prompt
Level 2 · SKILL.md 正文    触发命中后才加载（官方建议 < 5k words）
Level 3 · 捆绑资源         references/ scripts/ 按需读取/执行，从不全量进上下文
```

**关键洞察**：加载侧已经"按需分层"了，但**判别侧（选哪个 Skill）如果还是单层全量对比，Level 1 的常驻成本就白花**——N 越大，每条描述分到的注意力越少。分层路由 = 让判别侧与加载侧同构：先用便宜手段收敛候选，再让 LLM 只对小候选集精排。

## 三、级联分层路由架构（推荐落地）

```text
用户 query
   │
   ▼
[L0 规则粗筛]  关键词/正则/路径特征 → 直接命中则短路返回（确定性，0 LLM 调用）
   │ 未命中
   ▼
[L1 域路由]    先选"命名空间/域"（如 部署 / 数据 / 文档 / 评审），50 → 5-10 个候选
   │           router 可用：规则表、轻量分类模型、或 embedding 召回 top-K
   ▼
[L2 LLM 精排]  只把 L1 收敛后的候选描述给 LLM 做小规模多选（≤10 选 1 判别力充足）
   │
   ▼
[L3 拒识兜底]  置信度低 / 全部不匹配 → 返回 SKIP + 追问澄清，绝不硬选
```

每层的设计要点：

| 层 | 职责 | 流量占比（经验示意） | 延迟/成本 | 失败模式 |
|----|------|:---:|---------|---------|
| L0 规则 | 高频确定性场景短路 | ~40-60% | ~0 | 规则过宽误命中（要写 when_not_to_use 对偶规则） |
| L1 域路由 | 候选集收敛 | 剩余流量 | 低（分类/向量检索） | **域分错则全盘皆输**——域边界必须互斥 + 有"其他"域 |
| L2 LLM 精排 | 小候选集判别 | L1 输出的 top-K | 中（一次 LLM 调用） | 候选 >10 时退化回单层问题——控制 K |
| L3 拒识 | 不硬选 | 少量 | 一次追问 | 没有 SKIP 路径 = 逼模型选错（同 RAG 无拒答则强答） |

**与 [skill-hit-rate.md](skill-hit-rate.md) L2 路由层的关系**：那篇的"规则 + LLM 兜底"是本文 L0 + L2 的压缩版；本文补上 **L1 域收敛**（数量大时的关键层）与 **L3 显式拒识**（防止硬选）。

## 四、每层 router 选型

| Router 类型 | 适合层 | 优点 | 缺点 |
|------------|-------|------|------|
| 关键词/正则规则表 | L0 | 确定、零成本、可观测 | 覆盖不了长尾表述；维护成本随 N 涨 |
| 轻量分类器（fine-tuned small model） | L1 | 域分类准确、延迟低 | 需要标注数据；新增域要重训 |
| Embedding 召回 top-K | L1 | 零标注、长尾友好 | 召回错就完蛋——只做收敛不做终判 |
| LLM 多选 | L2 | 语义判别力最强 | 贵、有漂移——只在候选 ≤10 时用 |

**原则**：判别力与成本成正比，**让便宜的手段处理大流量，贵的手段只见收敛后的候选**——与 [RAG 知识冲突仲裁](../../../rag/knowledge-conflict-resolution/README.md)"规则优先、LLM-as-Judge 兜底"同一工程哲学。

## 五、成本账（单层 vs 分层）

> ⚠️ 示意口径（合成计算，用于展示量级差异，非实测 benchmark）：

```text
单层：50 Skill × 100 token = 5000 token 常驻/轮，每轮都付
分层：L1 域路由（embedding 检索，~0 LLM token）
     + L2 只注入 top-8 候选 × 100 = 800 token
     + 命中后按需加载 SKILL.md 正文（Level 2）
常驻判别成本 5000 → 800 token（-84%），且 N 再涨时 L2 候选数不变
```

**规模不变式**：单层成本 O(N) 常驻；分层成本 ≈ O(K) 常驻（K = L2 候选上限）——**N 增长时分层架构的成本是平的**，这是它最重要的性质。

## 六、路由评估：漏斗指标，不是单一命中率

分层后评估也要分层——只看端到端命中率会掩盖"哪一层漏的"：

```text
评测集（≥100 条 query + 期望 Skill 标注）逐层回放：
L0 规则层：误命中率（短路到错误 Skill 的比例）——最危险，错了连纠错机会都没有
L1 域路由：域级 recall@K（正确 Skill 所在域是否进入候选）——目标 ≥ 98%
L2 精排：  候选内选择正确率——目标 ≥ 90%
L3 拒识：  该 SKIP 时 SKIP 的比例（硬选率越低越好）
端到端：  命中率 + 每层延迟分解；每次 Skill 增删跑回归（复用 skill-hit-rate 评测集）
```

**定位效率**：域 recall 高但端到端低 → 问题在 L2 描述碰撞；域 recall 低 → 问题在 L1 域划分，改 L2 没用。

## 七、反直觉

| 误区 | 真相 |
|------|------|
| ❌ 选错 Skill 就重写 description | ✅ 先定位哪层漏的（§六漏斗）——描述碰撞只是 4 个崩溃维度之一 |
| ❌ 分层路由 = 多次 LLM 调用，更贵 | ✅ 恰恰相反：常驻 token O(N)→O(K)，多数流量被零成本规则/检索层消化 |
| ❌ 域路由用 LLM 更准 | ✅ L1 要的是便宜 + 高 recall 的收敛，embedding/分类器足够；LLM 留给 L2 小候选集精排 |
| ❌ 命中不了就选最像的 | ✅ 没有 SKIP 路径 = 逼模型硬选（同 RAG 强答即幻觉）——拒识是路由的一等公民 |
| ❌ 渐进披露是"加载优化" | ✅ 它同时约束判别侧——加载按需分层了，选择还是单层全量对比，Level 1 常驻就白付 |
| ❌ 规则层太 low，全 LLM 才先进 | ✅ 规则层确定性 + 零成本 + 可观测，兜住高频场景正是分层的第一收益来源 |

## 八、决策树

```text
Agent 总选错 Skill？→
├─ N ≤ 10？                → 不用分层：优化 description（when_not_to_use + 差异化动词）即可
├─ N > 10 且高频 query 集中？ → 【L0 规则表】先短路 top 场景，剩余交单层 LLM
├─ N > 30 或描述碰撞多？     → 【L1 域路由】命名空间收敛（embedding/分类器）+ L2 top-K 精排
├─ 错误集中在"硬选了不该选的"？→ 【L3 拒识】加 SKIP 路径 + 置信度阈值 + 追问澄清
└─ 不知道哪层的问题？        → 先建漏斗评估（§六），逐层定位再动架构
```

## 九、相关章节

**同模块姐妹**：
- [Skill 命中率](skill-hit-rate.md) — 四层模型总论（本文是其 L2 路由层的架构深潜）
- [Skill 设计](skill-design.md) — 单个 Skill 的 frontmatter / when_not_to_use 写法（L0 规则与 L1 域划分的原料）
- [Claude Code 实践总览](README.md) — 渐进披露基础

**跨模块**：
- [Lost in Middle](../../../rag/lost-in-middle/README.md) — 注意力稀释（崩溃维度 #2）的机理根源
- [成本上限与自动降级 · 5 层路由](../../production-stability/02-cost-control-and-degradation.md) — 同构的"级联 + 兜底"，但对象是模型成本（见文首术语辨析）
- [知识冲突解决](../../../rag/knowledge-conflict-resolution/README.md) — "规则优先、LLM 兜底"同一工程哲学
- [Skill 命中率面试题](../../../../12.interview/11.ai/skill-hit-rate/README.md) — 配套面试版（Q3 规则路由 vs LLM 自由选择）
- [13.story · 扩招 50 个厨师](../../../../13.story/45-skill-scheduling-restaurant.md) — 前厅手册（规则路由）+ 资深厨师兜底（LLM 精排）的餐厅叙事

---

← [返回 Claude Code 实践总览](README.md)

## 📚 参考来源

1. **Anthropic Engineering**：*Equipping agents for the real world with Agent Skills*. https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills — SKILL.md frontmatter 启动注入 system prompt 的官方机制
2. **Claude Platform Docs**：*Agent Skills Overview*. https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview — "filesystem-based progressive disclosure：按阶段加载而非预先占用上下文"官方表述
3. **Anthropic Engineering**：*Effective context engineering for AI agents*. https://www.anthropic.com/research/effective-context-engineering-for-ai-agents — 上下文预算与最小高信号 token 原则
4. **Lee Hanchung**：*Claude Agent Skills: A First Principles Deep Dive*. https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/ — 三级加载机制的第一性拆解
5. **SwirlAI**：*Agent Skills: Progressive Disclosure as a System Design*. https://www.newsletter.swirlai.com/p/agent-skills-progressive-disclosure — 渐进披露作为系统设计模式的分析

> 三级渐进披露 token 量级（~100 token/Skill 元数据、SKILL.md < 5k words）来自来源 1/2 官方口径；§五成本账为示意合成计算。
