
# SPEC for note 知识库

> **Inherits from**: (无，L0 是顶层)
> **Mode**: append + override
> **Updated**: 2026-08-11

---

## 全局规范

### 1. 命名约定

- 主模块：`{nn}.{english-name}/`，两位数字 + 英文小写 + 短横线（如 `01.java-and-jvm/`）
- 子目录：按概念或深度，由各模块 SPEC.md 定义
- 文件：`README.md` / `SPEC.md` / `index.md` 保留约定

### 2. commit 格式

```text
feat(note): 新增内容
refactor(note): 结构调整
fix(note): 修复
chore: 琐事
docs: 文档
```

### 3. 互链规则

- 每个**有父 README 的非 leaf 文件**必须有 `← [返回 ...]` 回链到父 README
- **豁免规则**：
  - ① **leaf 文件**（无 children 的最终文档）由父 README 反向链回即可，不必每篇都加 `← [返回 ...]`
  - ② **12.interview question 文件**（约 230 题）由 frontmatter `topic` 字段隐式关联到父 README，无需每题加回链字符
  - ③ **13.story 单篇**（约 50 篇）由 `13.story/README.md` 顶部"系列定位"段总目录统一显式链回
- 至少 2 个跨模块或同模块的互链
- 系列文章末尾必须有"系列导航表"（13.story 由 README.md 系列定位块承担）

### 4. frontmatter 规范

所有"知识文章"（非 SPEC.md / README.md / index.md）必须用 HTML-comment frontmatter。**三类 schema**（按文件类型选其一，字段定义见对应 `<module>/SPEC.md`）：

| 类型 | 用途 | 字段示例 | L1 详细定义 |
|---|---|---|---|
| `module:` | 通用知识文章（810+ 篇） | parent, slug, type, category, summary | 默认 |
| `question:` | 12.interview 各题（≈230 题） | id, topic, difficulty, frequency, scenario_type, tags | `12.interview/SPEC.md §4` |
| `story:` | 13.story 阿明餐厅系列（≈50 篇） | number, type, position, title, audience, depth | `13.story/SPEC.md §4` |

**module: 默认示例**（其他类型必填字段见 L1）：

```text
<!--module:
  parent: <module-slug>
  slug: <article-slug>
  type: article | atomic | moc
  category: ...
  summary: ...
-->
```

> 为什么 3 类：12.interview/13.story 因强骨架格式需要不同字段（id 锚点 / number 编号），硬塞进 module 会破坏 cheatsheet 自动生成与 cross-ref 网络。SPEC §7 模式 `append + override` 允许 L1 模块细化。

### 5. G1-G6 通用评分维度

| # | 维度 | 2 分 | 1 分 | 0 分 |
|---|------|------|------|------|
| G1 | frontmatter 完整性 | 有完整 frontmatter + 字段正确 | 有但缺字段 | 无 |
| G2 | 一句话定位 | H1 后 ≤80 字清晰定位 | 有定位但 >80 字或模糊 | 无 |
| G3 | 代码块规范 | 所有代码块声明语言 | 大部分声明 | 有裸代码块 |
| G4 | 回链 + 互链 | 有 footer 回链 + ≥2 个旧章节互链 | 有回链但互链不足 | 无回链 |
| G5 | 内容深度 | ≥4 个层面 + 实战案例 | 2-3 个层面 | 只有定义 |
| G6 | 可读性 | 结构清晰 + 表格/图/代码辅助 | 基本可读 | 大段纯文字 |

### 6. 11 类基础扫描规则

| # | 类别 | 检测方式 |
|---|------|----------|
| 1 | 数字一致性 | grep "篇\|个\|行" vs find 实测 |
| 2 | H1/H2 标题规范 | grep "^# " 检查数字编号 |
| 3 | 回链覆盖率 | grep "← \[返回" vs find README 数 |
| 3.5 | 孤岛检测 | 新文件未在父 README 登记 |
| 4 | 索引/入口缺失 | find -type d vs README 引用 |
| 5 | 内容重复 | grep 关键概念多文件匹配 |
| 6 | 内容缺口 | find 浅 README (<50 行) |
| 7 | 命名一致性 | 目录命名风格 |
| 8 | PNG/脚本残留 | find *.png vs 引用 |
| 9 | 系列完整性 | 编号系列文件缺失 |
| 10 | 归属合理性 | 子目录与父定位不符 |
| 11 | 合并检测 | 单文件 >500 行 + ≥8 H2 + ≥8 反模式 |

---

### 7. SPEC 分层（仅元规范）

知识库内的规范文件分两层，**不互相合并**：

- **L1 `<module>/SPEC.md`**（每个模块必备）：评估维度 + 写作总则 + 子目录约定。
  继承自本文件 §5 / §6，模式 = append + override。
- **L1.5 `<module>/*-FORMAT-SPEC.md`**（仅强骨架模块按需存在）：强制文章结构
  （"## 引言"、"30s/90s 话术"、"## 第一章"、"系列定位块"）+ 反例表 + 版本日志。

**为何 L1.5 不并入 L1**：

- 行数差 5–7 倍（46 vs 306），合并后 L0→L1 继承清晰度被淹没
- 消费者不同（L1 给评审 / `note-health`；L1.5 给写作者 + cheatsheet 自动生成）
- 演化节奏不同（L1 稳定；L1.5 已有 v1.0→v1.1→v2.0 路线）

**何时新建 L1.5**：当模块出现**强制文章骨架**（不只是评估维度）
—— 例如 12 的"30s/90s 话术 + 追问模板"、13 的"编号 + 章节 + 系列定位"。
仅含评估维度的模块（如 01–11 大多数）**不需要** L1.5。

**当前存在的 L1.5**：**无**（v2.1 起，12.interview 原 `QUESTION-FORMAT-SPEC.md` 与 13.story 原 `STORY-FORMAT-SPEC.md` 均合并入各自主 L1 的 §4 / §5 — L1.5 是否独立存在应按模块规模与读者重合度判定）。

---

### 8. 新词检索映射表（Keywords Mapping · 2026-10-12 通用化重构新增）

> **本表是 KB 内的「主题词 → 路径」快速定位索引**——由 `note-knowledge-qa` skill 在 Phase 2 关键词提取时主读，`note-precipitation-planning` Phase 6 在沉淀新主题后顺手加 1 行，`note-health` Phase 1.15 自动稽核死链并报警。

#### 8.1 使用说明

- 任何 KB 借用 3 个 meta-skill 时，**应填充本表**（至少 5-10 条核心词）。
- 3 skill 通过 `$KB_DIR/SPEC.md §8` 自动读取，**不修改 skill 主体即可生效**。
- 主题词-路径映射是新词检索的**前置索引**，**不能取代** Phase 2 的正文 grep + 关联追踪——只做「快速定位」。

#### 8.2 词条格式

```text
| 主题词 | 主模块路径 | 12.interview 路径 | 出现频次 |
|--------|-----------|-------------------|---------|
| <词>   | <module>/... 或 `-` | <interview>/... 或 `-` | <N> |
```

字段语义：

- **主题词**：用户问句中**最可能命中**的关键词（首选中文 + 英文并列）
- **主模块路径**：深度原理 KB 路径（`-` 表示该主题暂无主模块，但有面试版）
- **12.interview 路径**：面试题 KB 路径（`-` 表示无面试版；`(聚合)` 表示聚合在父条目的面试版）
- **出现频次**：手动维护（问答时命中次数，用于 Phase 2 主题词排序），初始 = `-`

#### 8.3 note KB 词条（2026-10-12 重构抽取 · 原 50+ 新词映射表精简）

> 原 50+ 词表写于 2026-07-14，经历多次目录重构（`02-technology-stack/*` → `llm-inference/*`，`07-research/alignment` → `fine-tuning/0N-*.md`）。本节为 2026-10-12 重构时**精简版**（移除已失效词 + 聚合条目；保留 active 词 ~35 条）。

##### 8.3.1 LLM 架构层（1 词）

| 主题词 | 主模块路径 | 12.interview 路径 | 频次 |
|--------|-----------|-------------------|------|
| Transformer | - | `12.interview/11.ai/transformer` | - |
| Flash Attention | `09.ai-applications/llm-inference/flash-attention` | 聚合 | - |

##### 8.3.2 LLM 推理优化（10 词）

| 主题词 | 主模块路径 | 12.interview 路径 | 频次 |
|--------|-----------|-------------------|------|
| KV Cache | `09.ai-applications/llm-inference/kv-cache` | `12.interview/11.ai/llm-inference` | - |
| PagedAttention | `09.ai-applications/llm-inference/paged-attention` | 聚合 | - |
| Continuous Batching | `09.ai-applications/llm-inference/continuous-batching` | 聚合 | - |
| Speculative Decoding | `09.ai-applications/llm-inference/speculative-decoding` | 聚合 | - |
| 权重量化 | `09.ai-applications/llm-inference/weight-quantization` | 聚合 | - |
| MoE 推理 | `09.ai-applications/llm-inference/moe-inference` | 聚合 | - |
| 推理性能指标 (TTFT/TPOT) | `09.ai-applications/llm-inference/inference-metrics` | 聚合 | - |
| 推理框架对比 | `09.ai-applications/llm-inference/inference-frameworks` | 聚合 | - |
| LLM 推理优化大专题 | `09.ai-applications/llm-inference/llm-inference-optimization` | `12.interview/11.ai/llm-inference` | - |
| vLLM / TGI / SGLang | `09.ai-applications/llm-inference/inference-frameworks` | - | - |

##### 8.3.3 LLM 训练与对齐（5 主词 · 聚合 8 词）

> 原表 8 词 → 精简为 5 主词（RLHF/PPO/Reward Model 聚合；newer-methods 聚合 ORPO/RFT）

| 主题词 | 主模块路径 | 12.interview 路径 | 频次 |
|--------|-----------|-------------------|------|
| SFT | `09.ai-applications/fine-tuning/01-sft.md` | `12.interview/11.ai/llm-alignment` | - |
| RLHF（含 PPO/Reward Model） | `09.ai-applications/fine-tuning/02-rlhf.md` | 聚合 | - |
| DPO | `09.ai-applications/fine-tuning/03-dpo.md` | 聚合 | - |
| Constitutional AI | `09.ai-applications/fine-tuning/04-constitutional-ai.md` | 聚合 | - |
| KTO / IPO / SimPO（含 ORPO/RFT） | `09.ai-applications/fine-tuning/05-newer-methods.md` | 聚合 | - |

##### 8.3.4 LLM 应用层（9 主词）

| 主题词 | 主模块路径 | 12.interview 路径 | 频次 |
|--------|-----------|-------------------|------|
| Lost In the Middle | `09.ai-applications/rag/lost-in-middle` | 聚合 | - |
| Chunking 策略 | `09.ai-applications/rag/chunking-strategies` | 聚合 | - |
| Embedding 模型 | `09.ai-applications/rag/embedding-models` | 聚合 | - |
| Hybrid Search | `09.ai-applications/rag/hybrid-search` | 聚合 | - |
| Reranker | `09.ai-applications/rag/reranker` | 聚合 | - |
| Query Rewrite | `09.ai-applications/rag/query-rewrite` | - | - |
| RAG Pipeline | `09.ai-applications/rag/01-pipeline.md` | - | - |
| RAG 评估（含 RAGAS/TruLens） | `09.ai-applications/rag/04-evaluation.md` | - | - |

##### 8.3.5 传统 ML 算法（8 主词 · 含 1 纯面试版）

| 主题词 | 主模块路径 | 12.interview 路径 | 频次 |
|--------|-----------|-------------------|------|
| K-means | `02.cs-foundations/01-algorithms/clustering/k-means` | `12.interview/02.computer-basics/machine-learning` | - |
| 梯度下降 | `02.cs-foundations/01-algorithms/optimization/gradient-descent` | 聚合 | - |
| PCA | `02.cs-foundations/01-algorithms/dimensionality-reduction/pca` | 聚合 | - |
| 分支界限 | `02.cs-foundations/01-algorithms/search/branch-and-bound` | - | - |
| ID3 / C4.5 / CART | `02.cs-foundations/01-algorithms/decision-tree` | 聚合 | - |
| Random Forest | `02.cs-foundations/01-algorithms/ensemble` | - | - |
| XGBoost / LightGBM | `02.cs-foundations/01-algorithms/ensemble` | - | - |
| 集成学习 | `02.cs-foundations/01-algorithms/ensemble` | - | - |
| ML 面试（含评估指标 F1/AUC） | - | `12.interview/02.computer-basics/machine-learning` | - |

#### 8.4 自动维护协议（3 skill 协同）

| 角色 | Skill | 时机 | 动作 |
|------|-------|------|------|
| **读取** | `note-knowledge-qa` | Phase 2 关键词提取 | 读 §8 做问句 → 主题词匹配；命中表内主题词 → 直接定位到主模块/12.interview 路径 |
| **写入** | `note-precipitation-planning` | Phase 6 沉淀新主题后 | 在 §8 末尾加 1 行（频次 = `-`）；**不强制**，由 subagent 报告「主题词有意义」时触发 |
| **稽核** | `note-health` | Phase 1.15 全库扫描 | 扫 §8 所有路径是否真实存在；不存在的标 P3 misplaced-warning，**不动手修复**（按用户决策走 Phase 6 沉淀流程）|

> ⚠ **本表是「前置索引」而非「权威路径」**——路径失效时 (`./xx/README.md` 不存在)，答案应转去正文 grep 而非报错。体检告警仅供维护者参考。
