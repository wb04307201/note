<!--question:
  id: 11.ai-vllm-vs-tei
  topic: 11.ai
  difficulty: ⭐⭐⭐
  frequency: 中高频
  scenario_type: 架构选型
  tags: [11.ai, vLLM, TEI, Embedding 推理, RAG 架构, PagedAttention]
  status: active
-->

# vLLM vs TEI：生成式推理与向量化推理为什么是互补而非替代？

> 一句话定位：RAG 链路里「检索侧 TEI、生成侧 vLLM」是按**计算图分工**，不是技术先进性排序——vLLM 能跑 embedding，但纯向量化场景 TEI 更省。完整深度见 [主模块 vllm-vs-tei 分工专题](../../../09.ai-applications/llm-inference/vllm-vs-tei/README.md)。

> **系列定位**：AI Infra / RAG 架构选型面试题（大厂 AI 平台岗高频）。考察的不是「谁比谁快」，而是 **生成式 vs Encoder 推理的计算图差异** + **Embedding 服务化选型** + **RAG 三阶段分工设计**。

---

## 引子：架构决策困境

```text
RAG 上线评审：知识库 500 万文档切片待向量化，线上问答要 LLM 生成。
架构师问："推理服务全用 vLLM 统一托管，还是生成、向量化各用专用引擎？"
```

- **统一派**：一套 vLLM 运维栈搞定，监控 / 扩容 / 发版只学一次
- **分工派**：TEI 向量化成本低一个量级，生成才需要 vLLM 的 PagedAttention
- 普通候选人会答"vLLM 更强，统一用 vLLM"——踩中「**能跑 ≠ 最优**、**忽视计算图差异**」两大雷区

**题意边界**：问的不是"vLLM 和 TEI 谁性能好"，而是**两类负载（生成 vs 向量化）怎么选运行时**——答案藏在计算图与资源模型的差异里。

---

## 一、核心原理

### 1.1 计算图差异：自回归生成 vs 一次前向编码

| 维度 | vLLM | TEI |
|------|------|-----|
| 核心任务 | 文本生成（Decoder-only 自回归逐 token 解码）| 向量化 / 重排序（Encoder 一次前向 pooling）|
| 优化重点 | KV Cache 管理（PagedAttention）+ 连续批处理 | Tokenization / 动态批处理 / 矩阵乘法效率，**无 KV Cache** |
| 资源特征 | 显存随生成长度动态增长 | 显存固定（max seq len × batch）|
| 实现语言 | Python / C++（CUDA）| Rust |

**要点**：一个要"边算边存历史"（KV Cache），一个"一次算完出向量"——显存模型、调度策略、容量估算公式全都不同，这不是同一类服务。

### 1.2 vLLM 的 Pooling Models 支持（口径修正）

- vLLM 支持**池化模型**（embedding / reranker 类 Encoder 模型）：任务取值 `embed` / `score` / `classify` / `token_embed` 等，经 `--pooler-config.task <task>` 指定或自动识别
- 对外端点：`/v1/embeddings`（向量化）、`/v1/score`、`/v1/rerank`（Cohere Rerank 兼容）
- ⚠️ 网上常见的"`--task pooling` 支持 embedding"是**错误口径**——"pooling"是模型类别名，不是任务取值

### 1.3 RAG 三阶段分工

1. **入库**：TEI 批量向量化文档切片 → 向量库（量大、成本敏感）
2. **检索**：TEI 向量化 query → Top-K（低延迟）；重排可走 TEI `/rerank`
3. **生成**：vLLM 驱动 LLM 读检索片段生成答案（吃 PagedAttention 高吞吐）

## 二、面试陷阱

### 陷阱 1：把 `--task pooling` 当合法参数背出来

- **❌ 错误解**："vLLM 加 `--task pooling` 参数就能跑 embedding 模型"
- **✅ 真相**：合法任务取值是 `embed` / `score` / `classify` / `token_embed`…；"Pooling Model"是模型类别名。答成"vLLM 通过 Pooling Models 支持 embedding/rerank，暴露 `/v1/embeddings` 与 `/v1/rerank`"才对
- **修正路径**：记"任务 = embed/score/classify，类别 = pooling model"，不记参数拼写

### 陷阱 2：把 TEI 当「小 vLLM」

- **❌ 错误解**："TEI 就是轻量版 vLLM，运维经验直接平移"
- **✅ 真相**：TEI 无 KV Cache、无自回归解码，显存模型是**固定**的（max seq len × batch）——vLLM 的显存估算公式、调度调优在 TEI 上完全不适用

### 陷阱 3：「统一技术栈」= 全部上 vLLM

- **❌ 错误解**："vLLM 也能跑 embedding，统一用 vLLM 减少运维面"
- **✅ 真相**："能跑"≠"跑得最优"。纯向量化高并发下 TEI 通常延迟更稳、资源更省（社区基准定性口径）；反过来 rerank/embedding QPS 很低时，统一 vLLM 确实更省运维——**按负载规模权衡，不是教条**

## 三、最佳实践

- **分工基线**：入库 / 检索 / rerank → TEI；生成 → vLLM（"专用工具做专用事"）
- **合并例外**：向量化 QPS 低 + 已有 vLLM 运维栈 → 用 vLLM Pooling Models 统一托管，省一套服务
- **选型口径**：短序列低延迟看 TEI；大 batch 吞吐看 vLLM pooling——随硬件 / 序列长度互有胜负，**上线前按目标负载实测**
- **姊妹题对照**：[工业部署推理引擎选型](../inference-engine-selection/README.md)（vLLM vs Ollama，生成式引擎内战）——两题合起来覆盖"生成侧 + 向量化侧"完整选型图

## 四、面试话术（30 秒 + 90 秒）

**30 秒版**：

> "vLLM 和 TEI 不是竞争关系。vLLM 是 Decoder-only 生成引擎，核心是 PagedAttention 管 KV Cache；TEI 是 Encoder 向量化引擎，Rust 写的，一次前面向出向量、显存固定。RAG 里检索侧用 TEI、生成侧用 vLLM，各用所长。vLLM 确实能跑 embedding——叫 Pooling Models，任务是 embed/score/classify——但纯向量化高并发场景 TEI 通常更优。"

**90 秒版**（补纵深）：

> "先分计算图：生成是自回归解码，KV Cache 显存随输出长度涨；向量化是一次前向，显存只看 max 序列长乘 batch。所以两者的调度、显存估算、容量模型完全不同，不能互相平移。
> 再分场景：RAG 三阶段里，入库和检索是纯向量化负载，量大、成本敏感，用 TEI；生成阶段要 PagedAttention 的高吞吐和连续批处理，用 vLLM。
> 常见追问是'为什么不统一 vLLM'——可以统一，vLLM 有 Pooling Models，端点 `/v1/embeddings`、`/v1/rerank` 都有；但那是能力补齐，不是向量化负载的最优解。向量化 QPS 低时统一省运维，QPS 高时 TEI 延迟和资源通常更好。最后上线前拿目标负载压测，短序列低延迟 TEI 常占优，大 batch 吞吐 vLLM 池化提升明显。"

**延伸追问（含答案）**：

1. **Q：TEI 和"sentence-transformers 自己包一层 FastAPI"差在哪？**
   A：TEI 是专用 Rust 运行时——Tokenization、动态批处理、显存管理都是按 Encoder 负载优化的；Python 自建层受 GIL 约束、无请求级动态批处理，高并发下 p99 差距明显。低 QPS 工具场景自建够用。
2. **Q：vLLM `/v1/rerank` 和 TEI `/rerank` 怎么选？**
   A：同"分工基线 + 合并例外"逻辑——已统一 vLLM 栈且 rerank QPS 不高 → vLLM（score 任务）；rerank 量大延迟敏感 → TEI（cross-encoder 一次前向打分）。
3. **Q：Embedding 服务怎么定容量？**
   A：按 `max_seq_len × batch_size` 估显存（固定，好估），压测向量化 QPS 与 p99 随 batch 的变化；对比生成服务要按输出长度分布估 KV Cache——两类服务的容量模型不能混用。

## 五、相关章节

- 同栏目：[`inference-engine-selection`](../inference-engine-selection/README.md) — vLLM vs Ollama 姊妹题（生成式引擎内战）
- 同栏目：[`llm-inference`](../llm-inference/README.md) — PagedAttention / 连续批处理 / KV Cache 原理
- 主模块：[`vllm-vs-tei`](../../../09.ai-applications/llm-inference/vllm-vs-tei/README.md) — 5 维对比 + RAG 互补架构 + 参考来源（完整版）

---

> 📅 2026-10-28 · 咬文嚼字 · vLLM vs TEI · ⭐⭐⭐（高频面试 + 实战必会）

← [返回: 咬文嚼字 · vllm-vs-tei](../README.md)
