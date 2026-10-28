<!--question:
  id: 11.ai-milvus-architecture
  topic: 11.ai
  difficulty: ⭐⭐⭐
  frequency: 中高频
  scenario_type: 向量库选型
  tags: [11.ai, Milvus, 架构, 一致性, 向量数据库]
  status: active
-->

# Milvus 架构长什么样？存算分离 / Segment / 一致性级别一次讲清

> 一句话定位：Milvus = **存算分离的分布式向量数据库**——无状态 worker + Segment 生命周期（growing → sealed）+ GuaranteeTs 四级一致性（默认 **Bounded**）+ Partition Key 分区裁剪。「存算分离」分离的是**计算节点无状态 vs 数据持久化在 WAL/对象存储**。完整深度见 [主模块 Milvus 架构](../../../09.ai-applications/rag/milvus-architecture/README.md)。

> **系列定位**：向量库内核面试题（AI 应用岗 + 基础架构岗高频）。考察的不是"背组件清单"，而是 **存算分离到底分离了什么** + **一致性四级的真名与默认值** + **2.x → 3.x 口径演进**。

---

## 引子："存算分离"分离了什么？

```text
面试官："你们向量库为什么选 Milvus？"
候选人："因为 Milvus 是存算分离的分布式架构，扩展性好。"
面试官："存算分离分离了什么？数据一致性怎么保证？"
候选人："……就是计算和存储分开？一致性……Strong？"
```

- **直觉解**："存算分离 = 内存和磁盘分开"——说错了分离对象
- **踩坑点 1**：不知道分离的是「worker 无状态」vs「数据持久化在 WAL + 对象存储」
- **踩坑点 2**：一致性级别背错名（Staleness?）、默认值答 Strong（实际 **Bounded**）

**题意边界**：问的是 Milvus **内核机制**，不是"HNSW 怎么选"（那题见 [vector-search-algorithms](../vector-search-algorithms/README.md)），也不是"Hybrid Search API"（见 [milvus-hybrid-search](../milvus-hybrid-search/README.md)）。

---

## 一、核心原理

### 1.1 三层架构 + 存算分离

```text
Access Layer   Proxy ×N 无状态 —— 校验请求 + MPP 聚合中间结果
Coordinator    主备 HA —— 调度与元数据管理
Worker Nodes   3.x 三类: Streaming / Query / Data Node —— 全部无状态
存储底座       etcd(元数据) + MinIO/S3(索引 + binlog) + WAL(写前日志)
```

「存算分离」= worker 无状态、数据持久化在 WAL + 对象存储 → 节点挂了换新节点即可恢复，支撑 K8s 水平扩缩容与容灾。

### 1.2 2.x → 3.x 组件演进（加分点）

| | 2.x 口径 | 3.x 口径 |
|---|---|---|
| worker | QueryNode / DataNode / IndexNode | **Streaming** / Query / Data Node |
| WAL | Pulsar / Kafka 为主 | **Woodpecker 默认**，免消息中间件 |
| 新增 | — | Streaming Node：growing 查询 + **growing→sealed 转化** + shard 级一致性 |

### 1.3 Segment 生命周期

```text
insert → growing 段(Streaming Node 处理,无完整索引)
           │ seal
           ▼
       sealed 段 → 建索引(产物写对象存储) → Query Node ANN 检索 → compaction
```

刚插入的数据"查得到但不快"——性能调优主战场在 sealed 段索引。

### 1.4 一致性四级（GuaranteeTs 机制）

查询带 **GuaranteeTs**，QueryNode 等本地 **ServiceTime ≥ GuaranteeTs** 才执行：

| 级别 | GuaranteeTs | 语义 |
|------|------------|------|
| Strong | 最新时间戳 | 全量已确认写入，尾延迟最高 |
| Session | 本客户端最后 insert | **读己之写** |
| **Bounded（默认）** | 早于最新的时间点 | 容忍有限旧数据，平衡 |
| Eventually | ≈1 | 尽力而为，最快 |

### 1.5 Partition Key 多租户

标量字段设为 Partition Key → 插入时 hash + 对 `partitions_num` 取模路由分区 → 查询带租户条件触发**分区裁剪**；Partition Key Isolation 兜资源竞争。租户少且硬隔离才用独立 collection。

## 二、面试陷阱

### 陷阱 1：把「etcd + MinIO + Pulsar 三件套」当现状

- **❌ 错误解**："Milvus 依赖 etcd、MinIO、Pulsar 三个组件"
- **✅ 真相**：那是 **2.x 口径**；3.x 默认 **Woodpecker WAL**，不需要额外消息中间件，Pulsar/Kafka 降为可选
- **修正路径**：答"2.x 三件套 → 3.x Woodpecker 默认"的演进，比只背一个口径更稳

### 陷阱 2：一致性级别背错名 / 默认值答 Strong

- **❌ 错误解**："四级是 Strong / Bounded / Staleness / Eventually，默认 Strong"
- **✅ 真相**：真名 **Strong / Bounded / Session / Eventually**（Bounded 的全称才是 Bounded Staleness），**默认 Bounded**；Session = 读己之写

### 陷阱 3：把一致性当排序质量开关

- **❌ 错误解**："检索结果不对，把一致性调到 Strong 就好了"
- **✅ 真相**：一致性管**新鲜度**（能不能读到刚写的数据），不管**排序质量**——排序是索引参数 / Rerank 的事

### 陷阱 4："多租户 = 每租户一个 collection"

- **✅ 真相**：海量租户下 collection 数量失控——Partition Key hash 路由 + 分区裁剪才是主流解法；越权防护仍要 ACL / metadata 过滤兜底（见 [相似文档消歧 §元数据过滤](../similar-doc-disambiguation/README.md)）

## 三、最佳实践

- **默认 Bounded，按需升级**：写后读场景升 Session（读己之写），金融级才 Strong（接受尾延迟）
- **多租户用 Partition Key + Isolation**：查询**必须带 Partition Key 条件**才触发分区裁剪——不带条件等于全分区扫
- **性能调优主战场在 sealed 段**：growing 段无完整索引，seal + 建索引后才进 ANN 快路径；索引参数见 [10 亿级向量检索](../vector-search-algorithms/README.md)
- **姊妹题对照**：[Milvus Hybrid Search](../milvus-hybrid-search/README.md) —— 那题管"两路怎么融"，本题管"内核怎么组织数据"

## 四、面试话术（30 秒 + 90 秒）

**30 秒版**：

> "Milvus 是存算分离的分布式向量数据库：Proxy 无状态入口做请求校验和结果聚合，Coordinator 主备调度，3.x 的 worker 是 Streaming、Query、Data 三类且全部无状态——数据持久化在 etcd 元数据、MinIO 索引加 binlog、WAL 写前日志三件套里，3.x 默认 Woodpecker，不再强依赖 Pulsar。数据走 Segment 生命周期：新数据进 growing 段由 Streaming Node 处理，seal 后建索引进 sealed 段走 ANN。一致性靠 GuaranteeTs 四级控制，Strong、Session、Bounded、Eventually，默认 Bounded。多租户用 Partition Key 做 hash 路由和分区裁剪。"

**90 秒版**（补纵深）：

> "先说'存算分离'分离了什么：不是内存和磁盘，而是**计算节点无状态、数据持久化在 WAL 加对象存储**——节点挂了换一个起来就能恢复，这是 K8s 扩缩容和容灾的前提。
> 三层架构：Access 层 Proxy 无状态，做请求校验和 MPP 中间结果聚合；Coordinator 主备做调度；worker 3.x 是 Streaming、Query、Data 三类。对比 2.x 的 QueryNode/DataNode/IndexNode，新增的 Streaming Node 是 shard 级小脑，负责 growing 数据查询、查询计划和 growing 到 sealed 的转化。存储依赖三个：etcd 存元数据、MinIO 存索引和 binlog、WAL 做写前日志——注意口径，2.x 时代是 etcd+MinIO+Pulsar 三件套，3.x 默认 Woodpecker，免消息中间件。
> Segment 生命周期：insert 进 growing 段，查得到但没有完整索引；seal 后建索引进 sealed 段才是 ANN 快路径，compaction 持续合并小段。一致性机制是每次查询带 GuaranteeTs，QueryNode 等 ServiceTime 追上才执行——四级是 Strong、Session、Bounded、Eventually，注意不是 Staleness，Bounded 的全称才是 Bounded Staleness；默认是 Bounded 不是 Strong，Strong 尾延迟高，写后读用 Session。
> 多租户建模：Partition Key 指定标量字段，插入 hash 取模路由到预建分区，查询带租户条件触发分区裁剪，Partition Key Isolation 再兜资源竞争。最后记边界：一致性管新鲜度不管排序质量，排序是索引参数和 Rerank 的事。"

**延伸追问（含答案）**：

1. **Q：默认一致性级别是什么？为什么不默认 Strong？**
   A：默认 **Bounded**。Strong 要求 QueryNode 等 ServiceTime 追上最新 GuaranteeTs，写入密集时查询尾延迟明显升高；RAG/检索场景多能容忍秒级旧数据，Bounded 用可控的新鲜度损失换延迟，是更合理的默认。
2. **Q：2.x 和 3.x 架构差在哪？**
   A：三点：① worker 从 QueryNode/DataNode/IndexNode 变为 Streaming/Query/Data Node，新增的 Streaming Node 承担 growing 查询、growing→sealed 转化、shard 级一致性与 WAL 容灾；② WAL 默认从 Pulsar/Kafka 变为 Woodpecker，3.x 部署不再需要额外消息中间件；③ Coordinator 收敛为主备单组件。
3. **Q：多租户为什么不用每租户一个 collection？**
   A：租户上万后 collection 数量失控（元数据、索引、连接管理都爆）。Partition Key 把租户字段 hash 取模路由到预建分区，查询带租户条件自动分区裁剪，管理成本 O(1)；代价是隔离粒度粗，资源竞争靠 Isolation 缓解，越权仍要 ACL/metadata 过滤兜底。租户个位数且要求硬隔离（独立备份/专属资源）才用独立 collection。

## 五、相关章节

- 同栏目：[Milvus Hybrid Search](../milvus-hybrid-search/README.md) — 库内 dense+sparse 双路召回与融合 API
- 同栏目：[10 亿级向量检索](../vector-search-algorithms/README.md) — sealed 段索引选型（HNSW/IVF/DiskANN）
- 同栏目：[相似文档消歧](../similar-doc-disambiguation/README.md) — expr/Partition Key 下推的实战场景
- 主模块：[Milvus 架构与核心机制](../../../09.ai-applications/rag/milvus-architecture/README.md) — 完整架构图 + 一致性/Partition Key 详解 + 参考来源

---

> 📅 2026-10-28 · 咬文嚼字 · Milvus 架构 · ⭐⭐⭐（向量库选型高频 + 口径陷阱密集）

← [返回: 咬文嚼字 · milvus-architecture](../README.md)
