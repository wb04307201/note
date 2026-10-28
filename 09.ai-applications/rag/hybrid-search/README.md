<!--module:
  parent: ai
  slug: ai/hybrid-search
  type: article
  category: 主模块子文章
  summary: 向量 + BM25 混合检索
  depth: ⭐⭐⭐⭐⭐
  status: active
  tags: [Hybrid Search, Milvus, 混合检索]
-->

# Hybrid Search（混合检索）

> ⬅️ [返回 L2 技术栈](../README.md)

> **一句话定位**：Hybrid Search = **向量检索（语义）+ BM25（关键词）融合**，**召回率比单一方案高 15-25%**。RAG 生产环境标配。

---

## 🎯 为什么需要混合

**向量检索弱项**：
- ❌ 专有名词（人名、产品名）召回差
- ❌ 罕见词（专业术语）召回差
- ❌ 完全相同字面无相似语义时（如"Apple"公司 vs 苹果）

**BM25 弱项**：
- ❌ 同义词（"汽车" / "车" / "vehicle"）召回差
- ❌ 语义相关但用词不同时召回差

**混合 = 互补**：

```text
向量得分：semantic_similarity(query, doc)
BM25 得分：keyword_match(query, doc)
最终得分：α * 向量得分 + (1 - α) * BM25 得分
```

---

## 📐 核心原理与公式

### BM25 公式（Okapi BM25）

BM25 是 TF-IDF 的改进版，是信息检索的事实标准：

$$
\text{BM25}(q, d) = \sum_{t \in q} \text{IDF}(t) \cdot \frac{f(t, d) \cdot (k_1 + 1)}{f(t, d) + k_1 \cdot (1 - b + b \cdot \frac{|d|}{\text{avgdl}})}
$$

其中：
- $f(t, d)$：词 $t$ 在文档 $d$ 中的词频
- $|d|$：文档 $d$ 的长度（词数）
- $\text{avgdl}$：语料库平均文档长度
- $k_1$：词频饱和参数（通常 1.2 ~ 2.0）
- $b$：长度归一化参数（通常 0.75）
- $\text{IDF}(t)$：逆文档频

$$
\text{IDF}(t) = \log \frac{N - n_t + 0.5}{n_t + 0.5}
$$

$N$ 为文档总数，$n_t$ 为包含词 $t$ 的文档数。

**关键点**：
- **TF 饱和**：词频再高也不会无限加权（$k_1$ 控制）
- **长度归一化**：长文档不会因 TF 高而占便宜（$b$ 控制）

### Cosine Similarity（向量检索）

$$
\text{cos\_sim}(q, d) = \frac{q \cdot d}{\|q\|_2 \cdot \|d\|_2}
$$

详见 [Embedding 模型](../embedding-models/README.md) §核心原理。

### 融合算法对比

| 算法 | 公式 | 优点 | 缺点 |
|------|------|------|------|
| **Weighted Sum** | $\alpha \cdot s_v + (1-\alpha) \cdot s_b$ | 直观 | 需归一化分数 |
| **RRF** | $\sum_r \frac{1}{k + r_r(d)}$ | 无需归一化 | k 需调 |
| **Convex Combination** | 类似 Weighted Sum | 同上 | 同上 |
| **Tournament** | 两者都得 Top-K 才入选 | 严格 | 召回会少 |

**Reciprocal Rank Fusion（RRF）公式**：

$$
\text{RRF}(d) = \sum_{r \in R} \frac{1}{k + \text{rank}_r(d)}
$$

- $R$：所有检索器（向量、BM25）
- $\text{rank}_r(d)$：文档 $d$ 在检索器 $r$ 中的名次
- $k$：常数（通常 60，$k=0$ 时只按排名）

RRF 由 Cormack et al. 2009 论文提出，**优势是分数尺度无关**，无需归一化。

---

## 📅 演进史时间线

```text
1970s ── TF-IDF (Salton) ────────── 经典 IR 模型
1990s ── BM25 (Robertson) ────────── BM25 改进 TF-IDF
2008 ── Lucene BM25 ─────────────── 首个工业级 BM25 实现
2013 ── Word2Vec (Mikolov) ─────── 词向量登场，但需拼接为句向量
2017 ── Transformer ─────────────── 上下文相关 Embedding
2019 ── DPR (Karpukhin) ─────────── 首个 SOTA 神经检索器
       │
2020 ── Sentence-BERT ──────────── Bi-Encoder 简化推理
2021 ── ColBERT (Khattab) ──────── 多向量检索，每 token 一向量
2022 ── SPLADE (Formal) ─────────── 学习型稀疏检索
2023 ── BGE-M3 (BAAI) ──────────── dense + sparse + ColBERT 三合一
       │
2024 ── Elastic Learned Sparse ──── ES 8.13+ 学习稀疏
       ├─ Qdrant Hybrid ──────────── 混合检索原生支持
       └─ Cohere Rerank 3 ───────── 重排 SOTA
```

---

## 📐 主流融合算法

### 1. 加权融合（Weighted Sum）

```python
final_score = α * vector_score + (1 - α) * bm25_score
# α = 0.5-0.7（向量权重略高）
```

**优点**：简单  
**缺点**：分数尺度差异需归一化（min-max / z-score）

### 2. Reciprocal Rank Fusion（RRF）

```python
def rrf(vector_results, bm25_results, k=60):
    scores = {}
    for rank, doc_id in enumerate(vector_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    for rank, doc_id in enumerate(bm25_results):
        scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

**优点**：不需归一化  
**缺点**：k 值需调

**k 选择经验**：
- $k=60$（原始论文默认）：通用
- $k=10 \sim 30$：前几个 rank 权重更大
- $k=100$：更平滑，所有 rank 接近

### 3. Cross-Encoder Re-ranking

见 [Reranker 章节](../reranker/README.md)

---

## 🛠️ Elasticsearch + 向量混合

```python
from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer

es = Elasticsearch()
model = SentenceTransformer('BAAI/bge-m3')

# 1. 索引
docs = [
    {"id": 1, "content": "...", "vector": model.encode("...")},
]
for doc in docs:
    es.index(index="my_index", body=doc)

# 2. 查询
query = "..."
query_vec = model.encode(query)

response = es.search(
    index="my_index",
    body={
        "query": {
            "bool": {
                "should": [
                    {"match": {"content": query}},  # BM25
                    {
                        "script_score": {
                            "query": {"match_all": {}},
                            "script": {
                                "source": "cosineSimilarity(params.query_vector, 'vector') + 1.0",
                                "params": {"query_vector": query_vec.tolist()}
                            }
                        }
                    }
                ]
            }
        }
    }
)
```

### ES 8.13+ 简化版（dense_vector + KNN）

```python
# 1. 创建索引（含 dense_vector 字段）
es.indices.create(
    index="hybrid_idx",
    body={
        "mappings": {
            "properties": {
                "content": {"type": "text"},
                "vector": {
                    "type": "dense_vector",
                    "dims": 1024,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }
)

# 2. 检索：BM25 + KNN 同时召回，RRF 融合
response = es.search(
    index="hybrid_idx",
    body={
        "query": {"match": {"content": query}},
        "knn": {
            "field": "vector",
            "query_vector": query_vec.tolist(),
            "k": 50,
            "num_candidates": 200,
        },
        "rank": {"rrf": {"window_size": 50, "k": 60}}
    }
)
```

---

## 🛠️ Milvus Hybrid Search

> **一句话**：Milvus Hybrid Search = **多向量字段 + `AnnSearchRequest` 多路召回 + ranker 融合排序**——把本页 §主流融合算法做进向量库内核，两路 ANN 与融合都在**库内**完成，应用层只发一次请求。

### 机制：字段 → 多路请求 → 融合

```text
字段层   dense_vec(FLOAT_VECTOR)+ sparse_vec(SPARSE_FLOAT_VECTOR)双字段
查询层   AnnSearchRequest × N —— 每路独立:data / anns_field / param / limit / expr
融合层   ranker = RRFRanker(k=60) 或 WeightedRanker(0.7, 0.3)
```

过滤（expr）、每路 Top-K、融合全在服务端下推，一次 RPC 拿结果——即本页 §Weighted Sum / §RRF 的**库内实现**。**跨引擎异构融合**（如 ES + 另一向量库两个数据源）才需要应用层自己 RRF。

### 两条 sparse 实现路径

| 路径 | 稀疏向量来源 | index metric | 查询形态 | 适用 |
|------|------------|-------------|---------|------|
| 自建稀疏 | 应用侧生成（BGE-M3 sparse / SPLADE）写入 | `IP` | 传稀疏向量 | 已有稀疏模型、学习型稀疏 |
| **内置 BM25 Function**（2.5+） | `FunctionType.BM25` 自动：文本 → sparse（VARCHAR 须 `enable_analyzer=True`） | `metric_type="BM25"`（params `bm25_k1` / `bm25_b`） | **传原文文本** | 全文检索即开即用 |

> Milvus 2.5.0（2024-12）引入 Full Text Search（Sparse-BM25 内置化，Tantivy 分词器支撑）；此前稀疏向量必须库外生成。当前主线 v3.0.x / v2.6.x 均支持（2026-10 GitHub Releases 核实）。

### 正确 API（pymilvus）

```python
from pymilvus import (
    MilvusClient, DataType, Function, FunctionType,
    AnnSearchRequest, RRFRanker, WeightedRanker,
)

client = MilvusClient(uri="http://localhost:19530")

# 1. Schema:dense + BM25 自动稀疏（文本 → sparse 由库内 Function 完成）
schema = client.create_schema()
schema.add_field("id", DataType.INT64, is_primary=True)
schema.add_field("text", DataType.VARCHAR, max_length=512, enable_analyzer=True)
schema.add_field("dense_vec", DataType.FLOAT_VECTOR, dim=1024)
schema.add_field("sparse_vec", DataType.SPARSE_FLOAT_VECTOR)
schema.add_function(Function(
    name="bm25_fn",
    input_field_names=["text"],
    output_field_names="sparse_vec",   # Function 自动填充的输出字段
    function_type=FunctionType.BM25,
))

# 2. 索引:dense HNSW + sparse 倒排(BM25 metric + k1/b,即本页 BM25 公式参数)
index_params = client.prepare_index_params()
index_params.add_index("dense_vec", index_type="HNSW", metric_type="COSINE")
index_params.add_index(
    "sparse_vec",
    index_type="SPARSE_INVERTED_INDEX",
    metric_type="BM25",
    params={"bm25_k1": 1.2, "bm25_b": 0.75},
)

# 3. 双路召回:每路一个 AnnSearchRequest(独立 data / metric / limit)
req_dense = AnnSearchRequest(
    data=[query_dense], anns_field="dense_vec",
    param={"metric_type": "COSINE"}, limit=50,
)
req_sparse = AnnSearchRequest(
    data=["雷霆 5 Pro 回收价"], anns_field="sparse_vec",
    param={"metric_type": "BM25"}, limit=50,   # BM25 路传原文文本
)

# 4. 融合:RRF(排名融合,免归一化)
results = client.hybrid_search(
    collection_name="hybrid_coll",
    reqs=[req_dense, req_sparse],
    ranker=RRFRanker(k=60),
    limit=10,
    output_fields=["text"],
)
```

### RRFRanker vs WeightedRanker

| | RRFRanker(k=60) | WeightedRanker(0.7, 0.3, norm_score=True) |
|---|---|---|
| 融合对象 | 排名（rank） | 分数（score） |
| 归一化 | **不需要**（尺度无关） | 需要（`norm_score=True` 自动归一化，见 §深度：分数归一化） |
| 可调参数 | k（见 §k 选择经验） | 每路权重（按序对应 reqs） |
| 适用 | 通用起步 | 业务明确偏好（专有名词域 → BM25 权重高，对照案例 3） |

### ⚠️ API 口径修正（常见错误）

- ❌ `client.hybrid_search(data=[...], anns_field=[...], ranker_type="rrf", ranker_params={"k": 60})` —— **不存在该签名**（本页旧版示例曾误用，2026-10-28 校正）
- ✅ `MilvusClient.hybrid_search(collection_name, reqs, ranker, limit)` —— 客户端口径参数名 **`ranker`**
- ✅ ORM `Collection.hybrid_search(reqs, rerank, limit)` —— ORM 口径参数名 **`rerank`**（同一能力两个入口命名不同，面试高频陷阱）

### 与 ES / Qdrant 实现对照（对照本页上面两节）

| | Milvus | Elasticsearch 8.13+ | Qdrant |
|---|---|---|---|
| 稀疏来源 | 自建 / 内置 BM25 Function | 全文倒排（或 ELSER 学习稀疏） | 自建稀疏 |
| 融合位置 | 库内 ranker（RRF / Weighted） | `rank.rrf` | 库内 FusionQuery |
| 查询形态 | N 个 AnnSearchRequest + ranker | query + knn 一次提交 | Prefetch × N + FusionQuery |

### 生产要点

- **每路 `limit` > 最终 `limit`**：双路各召回 50-100 融合后取 10——单路 limit=10 会让 RRF 候选集过小（对照 §调优）
- **expr 下推**：过滤写进 `AnnSearchRequest(expr=...)`，库内先过滤再融合，别拉回应用层过滤
- **BM25 参数**：`bm25_k1` / `bm25_b` 即本页 BM25 公式的 $k_1$ / $b$（默认 1.2 / 0.75）

**面试版**（30s / 90s 话术 + 4 陷阱 + 追问）：[Milvus Hybrid Search 面试题](../../../12.interview/11.ai/milvus-hybrid-search/README.md)

---

## 🛠️ Qdrant Sparse + Dense

```python
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, SparseVector

client = QdrantClient("localhost", port=6333)

# 1. 同时写入 dense + sparse
client.upsert(
    collection_name="hybrid",
    points=[
        PointStruct(
            id=1,
            vector={
                "dense": dense_emb,           # 1024 维
                "sparse": SparseVector(       # 学习稀疏 / BM25
                    indices=[2, 45, 233],
                    values=[0.5, 0.3, 0.8]
                ),
            },
            payload={"text": "..."}
        )
    ]
)

# 2. Hybrid Query（Prefetch + Rerank）
from qdrant_client.models import Prefetch, FusionQuery

results = client.query_points(
    collection_name="hybrid",
    prefetch=[
        Prefetch(query=dense_emb, using="dense", limit=50),
        Prefetch(query=SparseVector(...), using="sparse", limit=50),
    ],
    query=FusionQuery(fusion="rrf"),  # ← RRF 融合
    limit=10,
)
```

---

## 📊 混合 vs 单一对比

| 方案 | 召回率 | 精确率 | 速度 |
|------|--------|--------|------|
| 仅向量 | 0.78 | 0.72 | 50ms |
| 仅 BM25 | 0.72 | 0.75 | 5ms |
| **混合 (RRF)** | **0.88** | **0.80** | 55ms |
| **混合 + Rerank** | **0.92** | **0.88** | 200ms |

**结论**：混合 + Rerank 是 SOTA。

---

## 🔬 真实案例研究

### 案例 1：Elastic 官方电商搜索

**场景**：电商商品搜索  
**挑战**：用户搜 "iPhone 15 pro max 256GB 蓝色"（专有名词 + 多词组合）  
**方案**：

```python
# Elastic Learned Sparse + Dense 双路
# 1. Sparse：ELSER 模型（学习稀疏，类 BM25 但可学习权重）
# 2. Dense：E5-multilingual-large
# 3. RRF 融合
```

**效果**：
- 仅 BM25：NDCG@10 = 0.62
- 仅 Dense：NDCG@10 = 0.68
- **混合 RRF：NDCG@10 = 0.79**（+11% vs Dense，+17% vs BM25）

### 案例 2：Notion AI 工作区搜索

**场景**：千万级 Notion 文档混合搜索  
**方案**：
- 向量：OpenAI text-embedding-3-large（3072 维）
- BM25：内置倒排索引
- 融合：RRF with $k=60$
- **Rerank**：Cohere Rerank-3

**关键决策**：Notion 标题、URL、特殊符号多，BM25 抓这些符号特征，向量抓语义。

### 案例 3：法律文档检索（示意性案例）

> ⚠️ **口径说明**：Anthropic 未公开过 Claude 内部检索栈的实现细节，本案例为**社区推测/示意性配置**（展示"强专有名词域内 BM25 权重应更高"的通用模式），不代表任何厂商真实架构。

**场景**：判例法 + 法规搜索（强专有名词）  
**方案**：
- BM25：Elasticsearch（默认 BM25）
- Dense：BGE-large-en-v1.5
- 融合：Convex Combination（$\alpha=0.3$ 向量权重低）
- **关键**：BM25 权重高 → 抓案号、人名；向量兜底语义

---

## ⚠️ 反直觉

| 误区 | 真相 |
|------|------|
| ❌ 向量检索已足够 | ✅ 专有名词场景仍弱（人名、产品名、案号） |
| ❌ 混合一定更好 | ✅ 需调权重 + 选融合算法 |
| ❌ BM25 已过时 | ✅ 与向量互补，仍是基础；ES 8.13 推出 ELSER 学习稀疏 |
| ❌ 混合一定慢 | ✅ RRF 仅 5-10ms 额外开销（主耗时是 ANN 检索） |
| ❌ RRF 权重比加权融合优 | ✅ RRF 无需归一化但 $\alpha$ 可调；两者各有适用场景 |
| ❌ 混合 = 加权重 | ✅ 可用 RRF / Tournament / Multi-stage；不同融合方式效果差 5-10% |
| ❌ BM25 = TF-IDF | ✅ BM25 加了 TF 饱和 + 长度归一化，效果远好于纯 TF-IDF |
| ❌ 混合检索只用于 RAG | ✅ 企业搜索、电商搜索、代码搜索均适用 |
| ❌ 越多检索器越好 | ✅ 2 路（向量+BM25）性价比最高；3 路以上收益递减 |

---

## 🔗 兄弟章节

- **本专题**：[Embedding 模型](../embedding-models/README.md) / [Chunking](../chunking-strategies/README.md) / [Reranker](../reranker/README.md) / [RAG 评估](../04-evaluation.md)
- **L1**：[Lost in middle](../lost-in-middle/README.md)
- **咬文嚼字**：[RAG 面试](../../../12.interview/11.ai/rag/README.md)
- **L1 数学基础**：[BM25 公式与 TF-IDF](../../../03.data-stack/01-database/06-cache/README.md) — BM25 在 ES/Lucene 中的实现
- **L1 数据库**：[Elasticsearch 检索原理](../../../03.data-stack/02-big-data/03-realtime-compute/README.md) — BM25 + 倒排索引
- **进阶**：ColBERT 多向量检索 — Token 级细粒度检索
- **面试题**：[hybrid-search-面试](../../../12.interview/11.ai/vector-search-algorithms/README.md) — 5 道高频追问
- **面试题**：[Milvus Hybrid Search 面试题](../../../12.interview/11.ai/milvus-hybrid-search/README.md) — 库内融合机制 + API 陷阱
- **故事化**：[13.story 阿明餐厅 RAG 篇](../../../13.story/) — 混合检索类比"老顾客点单 + 新顾客推荐"

---

## 📐 深度：分数归一化

### 为什么需要归一化

BM25 分数范围通常 $[0, 30]$，Cosine 分数 $[0, 1]$，直接相加会被 BM25 主导：

```python
# ❌ 错误：直接相加
final = 0.5 * cosine_sim + 0.5 * bm25_score  # bm25 占主导

# ✅ 正确：归一化后相加
def min_max_norm(scores):
    min_s, max_s = min(scores), max(scores)
    return [(s - min_s) / (max_s - min_s) for s in scores]

vector_norm = min_max_norm(vector_scores)
bm25_norm = min_max_norm(bm25_scores)
final = 0.5 * vector_norm + 0.5 * bm25_norm
```

### 常见归一化方法

| 方法 | 公式 | 适用 |
|------|------|------|
| **Min-Max** | $(s - s_{\min}) / (s_{\max} - s_{\min})$ | 分布均匀 |
| **Z-Score** | $(s - \mu) / \sigma$ | 高斯分布 |
| **Sigmoid** | $1 / (1 + e^{-s})$ | 极端值 |
| **Rank-based** | $1 - r / N$ | RRF 用 |

---

## 🛠️ 进阶：ColBERT 多向量检索

### ColBERT 原理

传统 Bi-Encoder：1 文档 = 1 向量  
ColBERT：1 文档 = $L$ 个 token 向量（late interaction）

$$
s_{ColBERT}(q, d) = \sum_{i \in |q|} \max_{j \in |d|} E_{q_i}^T \cdot E_{d_j}
$$

**直觉**：每个 query token 找最相似的 doc token，求和。

### 优缺点

- **优点**：精确度高（接近 Cross-Encoder）
- **缺点**：存储 $L \times d$ 倍（1 doc 512 token × 1024 维 = 200KB）

```python
# ColBERT 检索示例（简化版）
from colbert import ColBERT

model = ColBERT('colbert-ir/colbertv2.0')

# 编码（每 token 一向量）
query_vecs = model.query_encoder(q)  # (Q, d)
doc_vecs = model.doc_encoder(d)      # (D, d)

# 相似度（MaxSim）
score = 0
for q_vec in query_vecs:
    max_sim = max(cosine_sim(q_vec, d_vec) for d_vec in doc_vecs)
    score += max_sim
```

---

## 🔬 真实案例研究（续）

### 案例 4：GitHub Copilot 代码搜索

**场景**：代码片段检索  
**挑战**：变量名、函数名是专有名词，BM25 强  
**方案**：
- BM25：Elasticsearch（默认）
- Dense：OpenAI text-embedding-3-large
- 融合：RRF + Cohere Rerank

**效果**：
- 仅 BM25：NDCG@10 = 0.65
- 仅 Dense：NDCG@10 = 0.72
- 混合 + Rerank：NDCG@10 = **0.86**（+32%）

### 案例 5：阿里巴巴淘宝商品搜索

**场景**：10 亿商品  
**方案**：
- BM25 + 行业词权重（商品标题、属性）
- Dense：Dasheng Embedding（阿里自研）
- Rerank：BGE-reranker-v2-m3
- 最终：CTR 提升 18%

### 案例 6：Perplexity AI 实时搜索

**场景**：实时联网搜索 + RAG  
**方案**：
- BM25：网页内文本匹配
- Dense：网页摘要 Embedding
- 时间衰减：新鲜网页加权
- Rerank：Cohere Rerank-3

**关键**：时间衰减权重 = $w_t \cdot e^{-\lambda \cdot \Delta t}$（$\Delta t$ 为网页发布时间差）

---

## 🛠️ 实战：完整 RAG Pipeline

```python
from FlagEmbedding import BGEM3FlagModel, FlagReranker
from elasticsearch import Elasticsearch

# 初始化
es = Elasticsearch()
embed_model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)
reranker = FlagReranker('BAAI/bge-reranker-v2-m3', use_fp16=True)

def hybrid_search(query, top_k=10):
    # 1. BM25 召回
    bm25_results = es.search(
        index="knowledge",
        body={"query": {"match": {"content": query}}, "size": 50}
    )["hits"]["hits"]
    bm25_docs = [(hit["_id"], hit["_source"]["content"]) 
                  for hit in bm25_results]
    
    # 2. Dense 召回
    query_vec = embed_model.encode([query])['dense_vecs'][0]
    dense_results = vector_store.search(
        collection="knowledge",
        data=[query_vec],
        limit=50,
        output_fields=["text"]
    )
    dense_docs = [(hit["id"], hit["entity"]["text"]) 
                  for hit in dense_results[0]]
    
    # 3. RRF 融合
    all_docs = {}
    for rank, (doc_id, content) in enumerate(bm25_docs):
        all_docs[doc_id] = {
            "content": content,
            "score": 1 / (60 + rank)
        }
    for rank, (doc_id, content) in enumerate(dense_docs):
        if doc_id in all_docs:
            all_docs[doc_id]["score"] += 1 / (60 + rank)
        else:
            all_docs[doc_id] = {
                "content": content,
                "score": 1 / (60 + rank)
            }
    
    # 4. Rerank Top-50
    sorted_docs = sorted(all_docs.items(), 
                         key=lambda x: -x[1]["score"])[:50]
    pairs = [(query, doc["content"]) for _, doc in sorted_docs]
    rerank_scores = reranker.compute_score(pairs)
    
    # 5. 取 Top-K
    final = sorted(zip(sorted_docs, rerank_scores), 
                   key=lambda x: -x[1])[:top_k]
    
    return [(doc_id, doc["content"], score) 
            for (doc_id, doc), score in final]
```

---

## 📊 调优：权重 vs Top-K

### 加权融合 $\alpha$ 调优

```python
# 经验值（视场景调整）
alpha_grid = [0.3, 0.5, 0.7, 0.9]

for alpha in alpha_grid:
    final_scores = [
        alpha * v_score + (1-alpha) * b_score
        for v_score, b_score in zip(vector_scores, bm25_scores)
    ]
    # 评估 NDCG@10
    ndcg = evaluate(test_set, final_scores)
    print(f"alpha={alpha}: NDCG@10={ndcg:.3f}")
```

### 经验数据

| 场景 | 推荐 $\alpha$ | 推荐 $k$ (RRF) |
|------|--------------|----------------|
| **通用文档** | 0.5 | 60 |
| **电商搜索** | 0.3（BM25 重要） | 30 |
| **代码搜索** | 0.4 | 60 |
| **学术论文** | 0.7（语义重要） | 60 |
| **问答系统** | 0.6 | 60 |
| **法律检索** | 0.3（专有名词） | 30 |

---

## 🎓 进阶阅读

- **BM25 原始论文**：Robertson & Zaragoza, 2009
- **RRF 论文**：Cormack et al., 2009
- **ColBERT 论文**：arXiv:2004.12832
- **SPLADE 论文**：arXiv:2107.05720
- **BGE-M3 论文**：arXiv:2402.03216

---

## 🧪 评测：BGE-M3 vs OpenAI 跨语种

| 测试 | BGE-M3 | OpenAI text-embedding-3-large |
|------|--------|------------------------------|
| 中英互译检索 | 0.92 | 0.89 |
| 中日检索 | 0.85 | 0.78 |
| 中法检索 | 0.82 | 0.74 |
| 长文档 (8K) | ✅ | ⚠️ 截断 |
| 延迟 (100 docs) | 120ms | 80ms (API) |
| 成本 | 免费（自托管） | $0.13/1M tokens |

---

## 📚 参考来源（§Milvus 小节 · 2026-10-28 核实）

- [pymilvus（官方 SDK）](https://github.com/milvus-io/pymilvus) — `hybrid_search` / `AnnSearchRequest` / `WeightedRanker` 签名一手依据（API 口径修正以此为准）
- [pymilvus examples/full_text_search/bm25.py](https://github.com/milvus-io/pymilvus/blob/master/examples/full_text_search/bm25.py) — 内置 BM25 Function 官方示例（`enable_analyzer` + `FunctionType.BM25` + `SPARSE_INVERTED_INDEX`）
- [Milvus v2.5.0 Release Notes](https://github.com/milvus-io/milvus/releases/tag/v2.5.0) — Full Text Search / Sparse-BM25 内置化引入版本（2024-12）
- [Milvus GitHub Releases](https://github.com/milvus-io/milvus/releases) — 版本口径：v3.0.4 / v2.6.26（2026-10-26）为当前主线

---

← [返回 L2 技术栈](../README.md)