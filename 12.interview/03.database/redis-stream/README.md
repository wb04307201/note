<!--question:
  id: 03.database-redis-stream
  topic: 03.database
  difficulty: ⭐⭐⭐
  frequency: 中频
  scenario_type: 架构困境
  tags: [03.database, Redis, redis, Redis Stream, 消息队列]
  status: active
-->

# Redis Stream 消息队列：为什么 pub/sub 会丢消息，Stream 就"不丢"吗？

> **一句话定位**：Stream 是 Redis 5.0 引入的可持久化、带消费组的消息队列结构——补齐 pub/sub「发完即忘、不回放、无 ACK」三短板，但"消息不丢失"是**相对 pub/sub 的口径**，端到端不丢仍受持久化策略与主从复制约束。

> **系列定位**：经典 Redis 面试题（消息队列 / 可靠性语义高频）。考察的不是"命令怎么背"，而是 **pub/sub → Stream 的能力演进** + **Consumer Group / PEL 的至少一次投递** + **持久化边界下的"不丢失"口径**。

---

## 引子：订单事件该发 pub/sub 还是 Stream？

```text
订单系统要把"支付成功"事件发给积分、物流两个下游服务。
评审时架构师问："用 Redis pub/sub 广播，还是 Redis Stream？
听说 Stream 就是消息队列，消息不会丢。"
```

- **pub/sub 派**：一行 SUBSCRIBE 就能广播，接入成本最低
- **Stream 派**：能持久化、能回放、有 ACK，可靠性强
- 普通候选人会顺着"消息不会丢"往下背——踩中「**把相对优势说成绝对保证**」的雷区：Redis 进程宕机丢不丢，恰恰不取决于 Stream 本身

**题意边界**：问的不是"Stream 有哪些命令"，而是**Stream 到底保证了什么、没保证什么**——答案分三层：能力层（对比 pub/sub）、语义层（至少一次投递）、持久化层（RDB/AOF 边界）。

---

> 📚 **前置知识**：[Redis](../../../03.data-stack/01-database/07-redis/README.md)

## 一、核心原理

### 1.1 pub/sub 的 3 个短板 → Stream 逐项补位

| 维度 | pub/sub | Stream |
|------|---------|--------|
| 持久化 | 发完即忘，订阅者不在线消息直接丢 | 消息留存流中（随 RDB/AOF 持久化），订阅者离线不丢 |
| 历史回放 | 不支持，错过就没了 | 支持——按消息 ID / 时间范围 `XRANGE` 回读 |
| 消费语义 | 广播、无 ACK | Consumer Group + PEL + `XACK`，至少一次投递 |
| 消费位置 | 无状态 | 组级游标（last-delivered-id）+ 消费者级 PEL |

**定位**：Stream 是「**内存优先的轻量消息队列**」——比 pub/sub 可靠，比 Kafka / RabbitMQ 轻（无独立 Broker，直接跑在 Redis 里）。

### 1.2 消息模型与命令族

- **消息 ID**：`<毫秒时间戳>-<序号>`（如 `1730000000000-0`），`XADD ... *` 自动生成，天然近似单调递增，支持按 ID / 时间范围读取
- **写入**：`XADD key MAXLEN ~ 10000 * field value ...`（`MAXLEN ~` 近似裁剪，控制保留量）
- **独立读**：`XREAD COUNT 10 STREAMS key 0`（任意游标回放）/ `XREAD BLOCK 0 STREAMS key $`（阻塞等新消息）
- **消费组读**：`XREADGROUP GROUP g1 c1 COUNT 10 BLOCK 5000 STREAMS key >`
- **确认与回收**：`XACK`（确认）/ `XPENDING`（未确认清单）/ `XCLAIM`、`XAUTOCLAIM`（转移超时消息）
- **裁剪**：`XTRIM key MAXLEN 10000`（回放窗口受保留策略限制）

```bash
# 生产者：写入并限制保留量
XADD orders:events MAXLEN ~ 10000 * type paid order_id 1001

# 消费组：创建组 → 消费 → 确认
XGROUP CREATE orders:events g1 $
XREADGROUP GROUP g1 c1 COUNT 10 BLOCK 5000 STREAMS orders:events >
XACK orders:events g1 1730000000000-0
```

### 1.3 Consumer Group + PEL：至少一次投递

```text
Stream key
└── Consumer Group g1（组级游标 last-delivered-id）
    ├── c1 的 PEL：[msg-5, msg-7]   ← 已投递未 ACK
    └── c2 的 PEL：[msg-6]
```

1. `XREADGROUP` 把消息投给组内消费者，同时记入该消费者的 **PEL（pending entries list）**
2. 消费者处理完 `XACK` 确认 → 消息从 PEL 移除
3. 消费者宕机 / 超时未 ACK → 消息**留在 PEL**，`XCLAIM` / `XAUTOCLAIM` 可转移给其他消费者重试
4. 所以投递语义是 **at-least-once**（至少一次）：故障场景会重复投递 → **消费端必须幂等**

### 1.4 ⚠️「消息不丢失」的语义边界（口径修正）

常见口径："Stream 确保即使网络断开或 Redis 宕机，消息也不会丢失。"——**把相对优势说成了绝对保证**，实际要拆成三层：

| 场景 | Stream 的真实行为 |
|------|------------------|
| 客户端断线 / 消费者离线 | ✅ 消息仍在流中，重连后按游标续读——这正是 pub/sub 做不到的（"不丢"的正确含义） |
| Redis 进程宕机 | ⚠️ 取决于持久化：`AOF always` 逐写刷盘不丢；`AOF everysec` 最多丢约 1 秒；只开 RDB 丢两次快照间的写入 |
| 主从 / Cluster 故障转移 | ⚠️ 复制是异步的，从节点提升可能丢最后几条写入（`WAIT` 可缓解，非零丢失） |
| 超出保留窗口 | ⚠️ `XTRIM` / `MAXLEN` 裁掉的消息**物理删除**，窗口外不可回放 |

**准确口径**：Stream 相比 pub/sub 提供「**持久化 + 可回放 + 至少一次投递**」；端到端不丢 = AOF 策略 + 主从同步（`WAIT` / `min-replicas-to-write`）+ 消费幂等，三件套配套。

## 二、面试陷阱

### 陷阱 1：把"消息不丢失"当绝对保证

- **❌ 错误解**："Stream 保证消息不丢失，宕机也不丢"
- **✅ 真相**：消息可靠性 = Stream 机制 × 持久化配置 × 主从同步策略。`everysec` 宕机最多丢约 1 秒、故障切换异步复制丢尾部写入——"不丢"是相对 pub/sub 的能力口径，不是绝对承诺
- **修正路径**：按"三层边界"作答（断线续读 ✅ / 宕机看持久化 / 故障切换看复制）+ 配套（AOF + `WAIT` + 幂等）

### 陷阱 2：把 Stream 当"平替 Kafka"

- **❌ 错误解**："Stream 有消费组，可以直接替代 Kafka / RocketMQ"
- **✅ 真相**：Stream 是**单实例、内存优先的轻量队列**——无分区再均衡、无多副本，保留窗口受内存约束（`MAXLEN` 裁剪）。中小流量、已有 Redis 的场景够用；大规模日志 / 流处理仍要 Kafka，事务消息仍要 RocketMQ（横评见 [消息队列](../../../06.distributed-systems/04-high-performance/mq/README.md)）

### 陷阱 3：以为 `XREADGROUP` 读到 = 消费完成

- **❌ 错误解**："XREADGROUP 返回了消息就算消费完了"
- **✅ 真相**：读到只是**投递**，消息进入 PEL；必须业务处理成功后 `XACK`。不 ACK 会堆积 PEL、消息被重复投递（at-least-once）——生产必须"处理 + ACK + 幂等"三件套

## 三、最佳实践

- **可靠性组合**：`AOF everysec` + 混合持久化打底，强一致场景 `WAIT` 等从节点确认；消费端幂等（去重键 = 消息 ID 或业务单号）
- **积压治理**：`XPENDING` 监控 PEL 长度，`XAUTOCLAIM` 回收超时消费者的消息，处理失败进自建"死信" Stream
- **容量控制**：`XADD MAXLEN ~ N` 近似裁剪（比精确 `XTRIM` 高效），保留窗口 = 业务可容忍的回放时长
- **选型边界**：流量小、已有 Redis、可接受内存保留 → Stream；高吞吐 / 长期保留 / 事务消息 → Kafka / RocketMQ（见 [消息队列](../../../06.distributed-systems/04-high-performance/mq/README.md)）
- **姊妹题对照**：[Redis 持久化](../redis-persistence/README.md)——`everysec` 丢 1 秒的根源就在那里，两题合起来覆盖"消息可靠性 = 机制 × 持久化"完整图

## 四、面试话术（30 秒 + 90 秒）

**30 秒版**：

> "Redis Stream 是 5.0 引入的可持久化消息队列结构，补齐 pub/sub 三个短板：不持久化、不回放、无 ACK。它有消息 ID、Consumer Group 和 PEL，提供至少一次投递，断线后能按游标续读。但'消息不丢失'是相对 pub/sub 的口径——Redis 宕机丢多少取决于持久化策略，everysec 最多丢约 1 秒，主从切换还可能丢最后几条写入。准确说法是：Stream 提供持久化 + 回放 + 至少一次，端到端不丢要靠 AOF 策略加消费端幂等。"

**90 秒版**（补纵深）：

> "先对比 pub/sub：纯广播、发完即忘，订阅者不在线消息就没了，也没有消费位置概念。Stream 是 5.0 加的数据结构，消息写进流里就留存，ID 是毫秒时间戳加序号，可按 ID 或时间范围回放——这是第一个补位。
> 第二个补位是消费组：XREADGROUP 投递时把消息记进消费者 PEL，处理完 XACK 才算消费；宕机没 ACK 的消息留在 PEL，可用 XCLAIM 转移重试。所以语义是至少一次，消费端要幂等。
> 最后是'不丢'的边界：断线续读没问题；但 Redis 进程宕机丢多少看持久化——AOF always 不丢，everysec 最多丢约 1 秒，只开 RDB 丢一个快照周期；主从切换因复制异步可能丢尾部写入，WAIT 能缓解。另外 MAXLEN 裁掉的消息是真删了，回放窗口外读不到。所以要把'不丢失'拆三层答，再补配套：AOF 策略、WAIT / 最少从节点、幂等消费。流量再大就该上 Kafka，那是另一个量级的系统。"

**延伸追问（含答案）**：

1. **Q：Stream 和 List（LPUSH / BRPOP）做队列差在哪？**
   A：List 是"取出即删"，一条消息只给一个消费者，无回放、无消费位置记录、无 ACK 语义；Stream 支持消费组内多消费者分摊、PEL 追踪未确认消息、按 ID 回放。要"广播 + 回放 + 可靠投递"用 Stream，简单 FIFO 任务队列 List 仍够用。
2. **Q：怎么监控 Stream 消费积压？**
   A：`XPENDING key group` 看 PEL 数量与最老未确认消息；`XLEN` / `XINFO STREAM` 看流长度；`XINFO GROUPS` 的 `lag` 字段（消费滞后）看组游标落后量。告警指标：PEL 持续上涨、消费者 idle 超时。
3. **Q：`MAXLEN ~` 的波浪号是什么意思？**
   A：近似裁剪——Redis 按节点粒度批量裁剪，允许实际长度在阈值附近浮动，换来接近 O(1) 的裁剪开销；不带 `~` 的精确裁剪逐条删、开销大。生产用 `~` 即可。

## 五、相关章节

- 同栏目：[`redis-persistence`](../redis-persistence/README.md) — RDB / AOF 语义（"宕机丢多少"的答案源头）
- 主模块：[`07-redis`](../../../03.data-stack/01-database/07-redis/README.md) — Stream 与消息队列章节（完整命令族 + 三方案对比）
- 相关：[`mq`](../../../06.distributed-systems/04-high-performance/mq/README.md) — 独立 MQ 横评（Kafka / RocketMQ / RabbitMQ / Pulsar）

---

> 📅 2026-10-28 · 咬文嚼字 · Redis Stream · ⭐⭐⭐（中频面试 + 实战必会）

← [返回: 咬文嚼字 · redis-stream](../README.md)
