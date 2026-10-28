<!--module:
  parent: ai
  slug: ai/milvus-architecture
  type: article
  category: 主模块子文章
  summary: Milvus 架构与核心机制——存算分离 / Segment 生命周期 / 一致性级别 / Partition Key
  depth: ⭐⭐⭐⭐
  status: active
  tags: [Milvus 架构, 向量数据库, 一致性级别, Partition Key]
-->

# Milvus 架构与核心机制

> ⬅️ [返回 L2 技术栈](../README.md)

> **一句话定位**：Milvus = **存算分离的分布式向量数据库**——无状态 worker(WAL + 对象存储持久化)+ Segment 生命周期(growing → sealed)+ **GuaranteeTs 四级一致性** + Partition Key 分区裁剪；「存算分离」分离的不是"内存和磁盘"，而是**计算节点无状态、数据持久化在 WAL/对象存储**，这是水平扩缩容与容灾的根因。

> **版本口径**（2026-10-26 GitHub Releases 实测）：当前双线 **v3.0.4**（v3.0.0 GA 2026-07-29）/ **v2.6.26**。本文 2.x / 3.x 口径分列，3.x 为新部署默认线。

---

## 🏗️ 分层架构：三层 + 存算分离

```text
Client (pymilvus / SDK / REST)
   │
   ▼
Access Layer   Proxy ×N —— 无状态；校验请求 + MPP 聚合后处理中间结果
   │
   ▼
Coordinator    主备模式(HA) —— 元数据/任务调度(2.x 为 Root/Query/Data/Index Coord)
   │
   ▼
Worker Nodes   无状态(存算分离) —— 3.x 三类: Streaming / Query / Data Node
```

| 组件 | 2.x 口径 | 3.x 口径 | 职责 |
|------|---------|---------|------|
| Proxy | 有 | 有(无状态) | 统一入口 + MPP 结果聚合 |
| Coordinator | Root/Query/Data/Index Coord | 单 Coordinator(主备) | 调度与元数据管理 |
| QueryNode | 有 | Query Node | sealed 段检索执行 |
| DataNode | 有 | Data Node | 数据持久化/导入 |
| IndexNode | 有(索引构建) | 并入 worker 简化 | 索引构建 |
| **Streaming Node** | 无 | **3.x 新增** | shard 级"小脑"：growing 数据查询 + 查询计划 + **growing→sealed 转化** + shard 级一致性与 WAL 容灾 |

**worker 无状态**的意义：数据不在节点内存里"扣着"，节点挂了换一个起来即可恢复（数据在 WAL + 对象存储）——这是 K8s 水平扩缩容与容灾的前提。

---

## 💾 存储依赖：etcd + 对象存储 + WAL

| 依赖 | 存什么 | 选项 |
|------|--------|------|
| **etcd** | 元数据：collection schema、节点状态、消费 checkpoint | 唯一 |
| **对象存储** | 索引文件 + binlog | MinIO / AWS S3 / S3 兼容 |
| **WAL（消息队列）** | 写前日志 | **Woodpecker（3.x 默认）** / Pulsar / Kafka / RocksMQ |

**口径修正**：「Milvus 依赖 etcd + MinIO + **Pulsar** 三件套」是 **2.x 时代**的说法（见 [13.story/37](../../../13.story/37-vector-database-and-embedding.md) §2.4 叙事版）。**3.x 默认 Woodpecker WAL + etcd + MinIO，不再需要额外消息中间件**；Pulsar/Kafka 降级为可选项。

---

## 📦 Segment 生命周期：数据怎么流动

```text
insert → growing segment(内存/Streaming Node 查询)
            │ seal(段写满/定时)
            ▼
        sealed segment → 建索引(产物写对象存储) → Query Node 检索
            │
            └── compaction(小段合并/清理删除) 持续进行
```

- **growing 段**：新写入数据，由 Streaming Node 负责查询与查询计划——量小可实时可查，但**没有完整索引**
- **sealed 段**：不可变、建索引后由 Query Node 用 ANN 索引检索；binlog 落对象存储
- **推论**：刚插入的数据"查得到但不快"（growing 通道），检索性能优化的主战场在 sealed 段的索引参数（见 [向量检索算法](../vector-search-algorithms/README.md)）

---

## 🔒 一致性级别：GuaranteeTs 与四级

**机制**：每次查询带一个 **GuaranteeTs**（承诺时间戳），QueryNode 等到本地 **ServiceTime ≥ GuaranteeTs** 才执行——等待越久越"新"，延迟越高。

| 级别 | GuaranteeTs 取值 | 语义 | 代价 |
|------|-----------------|------|------|
| **Strong** | 最新时间戳 | 读到全部已确认写入 | 查询等 ServiceTime 追齐，尾延迟最高 |
| **Session** | 本客户端最后一次 insert 时间 | **读己之写**（read-your-writes） | 仅等自己的写入 |
| **Bounded**（默认） | 早于最新的一个时间点 | 容忍有限窗口的旧数据 | 平衡（RAG 检索默认之选） |
| **Eventually** | ≈1（跳过一致性检查） | 尽力而为 | 最快，可能读到旧数据 |

**默认是 Bounded，不是 Strong**——多数 RAG/检索场景不需要全局强一致，Bounded 用可控的新鲜度损失换延迟。选型见文末决策树。

---

## 🏢 多租户：Partition Key 与分区裁剪

1. **建模**：把租户标识等标量字段设为 **Partition Key**，建表时预建 `partitions_num` 个分区
2. **路由**：插入时对 Partition Key 值 hash + 对 `partitions_num` 取模 → 目标分区 ID
3. **裁剪**：查询带上 Partition Key 条件（`tenant == "x"` / `tenant in [...]`），检索范围**裁剪到少数分区**——这是 Partition Key 的核心收益（分区裁剪），不是"多租户安全"本身（权限仍要 [元数据过滤/ACL](../similar-doc-disambiguation/README.md) 兜底）
4. **Partition Key Isolation**：多租户场景下进一步隔离分区间的资源竞争，提升检索性能
5. **演进**：3.x schema 支持 `isClusteringKey`（聚簇键），是 Partition Key 的后继机制

**边界**：租户极少且要求硬隔离（专属资源/独立备份）→ collection 级隔离；租户多、查询都带租户条件 → Partition Key。

---

## 🎯 选型对照（向量库横向）

| 引擎 | 一句话 | 详链 |
|------|--------|------|
| **Milvus** | 分布式存算分离、亿级+、组件多运维重 | 本篇 |
| Qdrant | Rust 单机性能优、横向扩展弱 | [向量检索算法 §业界向量库](../vector-search-algorithms/README.md) |
| Weaviate | 模块化 + 多模态 | [13.story/37 §2.6](../../../13.story/37-vector-database-and-embedding.md) |
| pgvector | PG 扩展、百万级内轻量首选 | [13.story/37 §2.5](../../../13.story/37-vector-database-and-embedding.md) |

规模分档选型（<1000 万 → >10 亿）见 [向量检索算法](../vector-search-algorithms/README.md)；叙事版 6 库全景见 [13.story/37](../../../13.story/37-vector-database-and-embedding.md)。

---

## 📐 效果度量（R1）：一致性/分区裁剪最终回到检索指标

架构机制不直接产生"准确率"——上线前用黄金集验证（公式与工具横评见 [RAG 评估](../04-evaluation.md) / [../../eval/](../../eval/)）：

| 指标 | 公式 | 在本主题的含义 |
|------|------|----------------|
| **NDCG@K** | $DCG@K = \sum_{i=1}^{K} \frac{2^{rel_i}-1}{\log_2(i+1)}$，$NDCG = \frac{DCG@K}{IDCG@K}$ | 分区裁剪/一致性调优后，相关段排序是否退化 |
| **MRR** | $MRR = \frac{1}{rank_{\text{first relevant}}}$ | 第一条相关文档排第几——调优前后对照 |

**用法**：调 Partition Key `partitions_num` 或一致性级别后跑黄金集，NDCG/MRR 不回退 + 延迟下降才算有效（对比口径：Session vs Bounded 的写后读命中率）。

---

## ⚠️ 反直觉

| 误区 | 真相 |
|------|------|
| ❌ Milvus 依赖 etcd + MinIO + Pulsar 三件套 | ✅ 2.x 口径；**3.x 默认 Woodpecker WAL**，免消息中间件 |
| ❌ 四级一致性是 Strong/Bounded/Staleness/Eventually | ✅ 真名 **Strong / Bounded / Session / Eventually**（Bounded 的全称才是 Bounded Staleness）；Session = 读己之写 |
| ❌ 一致性默认 Strong 最稳 | ✅ **默认 Bounded**；Strong 要等 ServiceTime 追齐，尾延迟高，按需才开 |
| ❌ 查询慢/结果不对就调一致性级别 | ✅ 一致性管**新鲜度**不管**排序质量**——排序是索引参数/Rerank 的事（见 [Reranker](../reranker/README.md)） |
| ❌ 多租户 = 每租户一个 collection/手动分区 | ✅ Partition Key **hash 路由 + 分区裁剪**，免海量分区管理；Isolation 再兜资源竞争 |
| ❌ 刚插入的数据和历史数据一样快 | ✅ growing 段无完整索引（Streaming Node 通道），seal + 建索引后才进 ANN 快路径 |

---

## 🔀 决策树

```text
一致性级别怎么选？
├─ 写后立刻要读到自己的写入？   → Session（读己之写）
├─ 不能读到任何过期数据？       → Strong（接受尾延迟）
├─ 默认 / 大多数 RAG 检索       → Bounded（默认，平衡）
└─ 日志分析类可容忍丢失？       → Eventually

多租户建模怎么选？
├─ 租户多、查询都带租户条件     → Partition Key（+ Isolation）
├─ 租户少、要求硬隔离           → collection 级隔离
└─ 权限控制（防越权）           → metadata ACL，见相似文档消歧 §元数据过滤
```

---

## 🔗 兄弟章节

- **机制深读**：[Hybrid Search](../hybrid-search/README.md)（§Milvus 库内融合 API）/ [向量检索算法](../vector-search-algorithms/README.md)（sealed 段索引选型）/ [相似文档消歧](../similar-doc-disambiguation/README.md)（expr 下推实战）
- **叙事对照**：[13.story/37 味道仓库](../../../13.story/37-vector-database-and-embedding.md) —— 向量库 6 库全景（本篇是"巨型中央仓库"的内核深读）
- **规范互链**：[../../prompts/](../../prompts/)（生成阶段基础）/ [../../eval/](../../eval/)（评估方法论）/ [../../agent/](../../agent/)（Agentic RAG 延伸）

---

## 📚 参考来源（2026-10-28 核实）

- [Milvus Docs · Architecture Overview (v3.0.x)](https://github.com/milvus-io/milvus-docs/blob/v3.0.x/site/en/reference/architecture/architecture_overview.md) — 三层架构 / Proxy MPP / Streaming Node 职责 / worker 无状态（一手依据）
- [Milvus Docs · Main Components](https://github.com/milvus-io/milvus-docs/blob/v3.0.x/site/en/reference/architecture/main_components.md) — 3.x 组件清单（Coordinator/Proxy/Streaming/Query/Data Node）
- [Milvus Docs · Data Infra Integration Overview](https://github.com/milvus-io/milvus-docs/blob/v3.0.x/site/en/adminGuide/data-infra-integration-overview.md) — etcd/MinIO/WAL 三依赖 + **3.x 默认 Woodpecker** 口径
- [Milvus Docs · Tune Consistency](https://github.com/milvus-io/milvus-docs/blob/v3.0.x/site/en/reference/tune_consistency.md) — 四级一致性 + GuaranteeTs/ServiceTime 机制 + 默认 Bounded
- [Milvus Docs · Use Partition Key](https://github.com/milvus-io/milvus-docs/blob/v3.0.x/site/en/userGuide/search-query-get/use-partition-key.md) — hash+modulo 路由 / 分区裁剪 / Partition Key Isolation
- [Milvus GitHub Releases](https://github.com/milvus-io/milvus/releases) — 版本口径：v3.0.4 / v2.6.26（2026-10-26）双线

> 来源级别：官方文档（一手）+ 官方 Releases API（一手）。存疑点建议对照官方文档复核。

---

> 📅 2026-10-28 · 咬文嚼字 · Milvus 架构 · ⭐⭐⭐⭐

← [返回 L2 技术栈](../README.md)
