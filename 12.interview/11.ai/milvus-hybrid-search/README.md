<!--question:
  id: 11.ai-milvus-hybrid-search
  topic: 11.ai
  difficulty: ⭐⭐⭐
  frequency: 中高频
  scenario_type: RAG 检索工程
  tags: [11.ai, Milvus, Hybrid Search, 混合检索, RRF, 向量数据库]
  status: active
-->

# Milvus Hybrid Search 是什么？dense + sparse 双路召回为什么是 RAG 生产标配？

> 一句话定位：Milvus Hybrid Search = **多向量字段 + `AnnSearchRequest` 多路召回 + ranker 融合排序**——把「向量 + 关键词融合」做进向量库内核，两路 ANN 检索与融合都在**库内**完成，应用层只发一次请求。完整深度见 [主模块 Hybrid Search §Milvus](../../../09.ai-applications/rag/hybrid-search/README.md)。

> **系列定位**：RAG 检索工程面试题（AI 应用岗 + 向量库选型高频）。考察的不是"会不会调 API"，而是 **库内融合 vs 应用层融合的边界** + **两条 sparse 实现路径** + **RRF / Weighted 融合语义差异**。

---

## 引子：专有名词召回事故

```text
RAG 问答上线后用户投诉："搜『雷霆 5 Pro 回收价』，知识库里明明有这篇文章却召回不到。"
排查发现：query 里的"雷霆 5 Pro"是产品名，向量检索只召回语义相近的泛文，
精确匹配的那篇沉在 50 名外。评审会上架构师问："Milvus Hybrid Search 是什么？
和我们自己在应用层跑两路检索再融合，差在哪？"
```

- **直觉解**："就是向量 + 关键词一起搜，谁分高谁排前"——说出了现象，没说出机制
- **踩坑点 1**：不知道融合发生在**库内**（服务端多路召回 + ranker），还是应用层拉两次结果自己求和
- **踩坑点 2**：API 签名背错——把不存在的 `ranker_type="rrf"` 当合法参数写进简历

**题意边界**：问的是"Milvus Hybrid Search 的**机制与边界**"，不是"混合检索有什么用"（那题见 [vector-search-algorithms](../vector-search-algorithms/README.md)）。

---

## 一、核心原理

### 1.1 三层结构：字段 → 多路请求 → 融合

```text
字段层   dense_vec(FLOAT_VECTOR)+ sparse_vec(SPARSE_FLOAT_VECTOR)双字段
查询层   AnnSearchRequest × N —— 每路独立:data / anns_field / param / limit / expr
融合层   ranker = RRFRanker(k=60) 或 WeightedRanker(0.7, 0.3)
```

每路召回是**独立的 ANN 检索**（各自 Top-K），ranker 在服务端把两路结果融合成最终 Top-K——对应主模块 §主流融合算法（RRF / Weighted Sum）的**库内实现**。

### 1.2 两条 sparse 实现路径

| 路径 | 稀疏向量来源 | index metric | 查询形态 | 适用 |
|------|------------|-------------|---------|------|
| 自建稀疏 | 应用侧生成（BGE-M3 sparse / SPLADE）写入 | `IP` | 传稀疏向量 | 已有稀疏模型、学习型稀疏 |
| **内置 BM25 Function** | `FunctionType.BM25` 自动：文本 → sparse（VARCHAR 须 `enable_analyzer=True`） | `metric_type="BM25"` | **传原文文本** | 全文检索即开即用 |

### 1.3 RRFRanker vs WeightedRanker

| | RRFRanker(k=60) | WeightedRanker(0.7, 0.3, norm_score=True) |
|---|---|---|
| 融合对象 | 排名（rank） | 分数（score） |
| 归一化 | **不需要**（尺度无关） | 需要（`norm_score=True` 自动归一化） |
| 可调参数 | k（60 通用，小 k 前排权重更高） | 每路权重（按序对应 reqs） |
| 适用 | 通用起步 | 业务有明确偏好（专有名词域 → BM25 权重高） |

### 1.4 库内融合 vs 应用层融合的边界

- **库内**（Milvus Hybrid Search）：两路 ANN + 融合 + 过滤全在服务端下推，一次 RPC；expr 先过滤再融合
- **应用层**（如 ES + 向量库各查一次再自己 RRF）：跨引擎异构融合才需要——两个不同源的检索系统，库内融合帮不了你
- **边界**：同库多向量字段 → 库内；跨引擎 / 融合逻辑强定制 → 应用层

## 二、面试陷阱

### 陷阱 1：把 `ranker_type="rrf"` 当合法 API

- **❌ 错误解**："调 `client.hybrid_search(data=[...], anns_field=[...], ranker_type='rrf', ranker_params={'k': 60})`"
- **✅ 真相**：**不存在该签名**。真实用法是 `reqs=[AnnSearchRequest(...), ...]` + `ranker=RRFRanker(k=60)`——每路一个 `AnnSearchRequest(data, anns_field, param, limit)`，融合器是对象不是字符串
- **修正路径**：记"AnnSearchRequest 列表 + Ranker 对象"，不记字符串参数拼写

### 陷阱 2：Client 与 ORM 的 `ranker` / `rerank` 命名混淆

- **✅ 真相**：`MilvusClient.hybrid_search(collection_name, reqs, **ranker**, limit)` 的参数名是 `ranker`；ORM `Collection.hybrid_search(reqs, **rerank**, limit)` 是 `rerank`——同一能力两个入口命名不同，答出这个细节直接加分

### 陷阱 3：BM25 Function 查询时传 embedding

- **❌ 错误解**："BM25 路的 query 也先向量化再传进去"
- **✅ 真相**：内置 BM25 路的 `data` **传原文文本**（`AnnSearchRequest(["雷霆 5 Pro 回收价"], "sparse_vec", {"metric_type": "BM25"}, limit=50)`），文本在库内分词映射为稀疏向量；且 VARCHAR 字段须 `enable_analyzer=True`，index 用 `SPARSE_INVERTED_INDEX` + `metric_type="BM25"`

### 陷阱 4："混合检索 = 加权求和"

- **❌ 错误解**："就是 α·向量分 + (1-α)·BM25 分"
- **✅ 真相**：那是 Weighted Sum；Milvus 默认推荐 **RRF 排名融合**——只看名次不看分数，**天然免归一化**（BM25 与 cosine 分数尺度差异大，见主模块 §分数归一化）。加权融合还要操心 `norm_score`，不是"一句话求和"

## 三、最佳实践

- **每路 limit > 最终 limit**：双路各召回 50-100，融合后取 10——单路 `limit=10` 会让 RRF 候选集过小、两路重叠即枯竭
- **RRF 起步，Weighted 按业务调**：k=60 通用；专有名词域（产品名 / 案号）把 BM25 权重调高（对照主模块案例 3 模式）
- **expr 下推**：过滤条件写进 `AnnSearchRequest(expr=...)`，库内先过滤再融合，别拉回应用层过滤
- **姊妹题对照**：[10 亿级向量检索](../vector-search-algorithms/README.md)（HNSW/IVF 索引选型）——那题管"单路怎么搜快"，本题管"两路怎么融"

## 四、面试话术（30 秒 + 90 秒）

**30 秒版**：

> "Milvus Hybrid Search 是把混合检索做进向量库内核：表里存 dense + sparse 两个向量字段，查询时每路一个 AnnSearchRequest 独立做 ANN 召回，再用 ranker 在服务端融合。融合器两种：RRFRanker 按排名融合、免归一化，k=60 起步；WeightedRanker 按分数加权、自动归一化，适合业务有明确偏好的场景。sparse 路可以自建稀疏向量，也可以用内置 BM25 Function——文本自动转稀疏，查询时直接传原文。"

**90 秒版**（补纵深）：

> "先说边界：Hybrid Search 解决的是向量检索对专有名词、罕见词召回差的问题，靠 dense 抓语义、sparse 抓字面互补。Milvus 的做法是库内融合——字段层双向量字段，查询层每个路一个 AnnSearchRequest，携带自己的 data、metric、limit，甚至 expr 过滤，最后 ranker 在服务端把两路 Top-K 融合成最终结果。好处是过滤、召回、融合全部下推，一次 RPC 拿结果；跨引擎异构融合才需要应用层自己做。
> 融合器选型上，RRF 只看排名不看分数，天然免归一化，k=60 通用——BM25 分数和 cosine 分数尺度差异大，直接加权求和必须先归一化，这是很多人踩的坑。WeightedRanker 有 norm_score 参数自动归一化，适合明确要偏向 BM25 或向量的业务，比如法律、电商这类专有名词域。
> 实现路径有两条：自建稀疏向量适合已有 BGE-M3 sparse 这类学习型稀疏模型；内置 BM25 Function 是即开即用的全文检索，VARCHAR 开 enable_analyzer，索引用 SPARSE_INVERTED_INDEX 配 metric_type=BM25，查询传原文文本而不是向量。
> 最后两个细节加分：一是每路 limit 要比最终 limit 大，比如各召回 50 融合后取 10，否则 RRF 候选集不够；二是 API 口径，MilvusClient 的参数叫 ranker，ORM Collection.hybrid_search 的参数叫 rerank，没有 ranker_type 这种字符串参数。"

**延伸追问（含答案）**：

1. **Q：和"ES 查一次 + 向量库查一次、应用层自己 RRF"比，库内融合好在哪？**
   A：一是**过滤语义正确**——expr 在每路召回前下推，先过滤再融合；应用层融合常常是召回后过滤，容易"融合分算完发现都不合法"。二是**性能**：两路 ANN 并行 + 服务端融合，一次 RPC，省一次网络往返和应用层排序。但**跨引擎**（ES 索引和 Milvus 是两个数据源）时应用层融合仍是唯一选择。
2. **Q：RRF 的 k 怎么调？**
   A：k=60 是 Cormack 原始论文默认，通用起步。k 越小前几名权重越陡（Top-1 贡献大），对"头部精准"场景友好；k 越大越平滑。主模块 §调优 给了场景经验表：通用 60、电商/法律这类字面匹配域 30。调法是拿黄金集扫 k∈{10, 30, 60, 100} 看 NDCG@10。
3. **Q：什么时候用 WeightedRanker 不用 RRF？**
   A：当**分数本身有业务含义**且你信任它的尺度时——比如自建稀疏分是人工调的行业词权重，明确想让 BM25 占 70%，那用 WeightedRanker(0.7, 0.3) 直接表达偏好；或者做了分数量化、两路分数可比。两路分数尺度不明（典型：cosine 0-1 vs BM25 0-30）就用 RRF 免归一化。

## 五、相关章节

- 同栏目：[10 亿级向量检索](../vector-search-algorithms/README.md) — HNSW/IVF/DiskANN 单路索引选型
- 同栏目：[RAG 架构设计](../rag/README.md) — 混合检索在 RAG 链路中的位置
- 同栏目：[相似文档消歧](../similar-doc-disambiguation/README.md) — 字面兜底救不了的场景（相对时间/属性歧义）怎么解
- 同栏目：[Milvus 架构](../milvus-architecture/README.md) — 内核机制（存算分离 / Segment / 一致性 / Partition Key）
- 主模块：[Hybrid Search §Milvus Hybrid Search](../../../09.ai-applications/rag/hybrid-search/README.md) — 双路召回机制 + 正确 API 完整代码 + RRF/Weighted 对比 + 参考来源（完整版）

---

> 📅 2026-10-28 · 咬文嚼字 · Milvus Hybrid Search · ⭐⭐⭐（RAG 生产标配 + API 陷阱高频）

← [返回: 咬文嚼字 · milvus-hybrid-search](../README.md)
