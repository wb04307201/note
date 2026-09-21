<!--
question:
  id: 09.front-end-websocket-loss-handling
  topic: 09.front-end
  difficulty: ⭐⭐⭐⭐⭐
  frequency: 高频
  scenario_type: 通信可靠性
  tags: [09.front-end, WebSocket, realtime, heartbeat, reconnect]
-->

# WebSocket 丢包前端处理 —— 5 策略 + 7 反直觉点

> 一句话定位：**WebSocket 协议层不丢包，但"应用层看不见"就是丢了——5 策略（心跳 / 重连 / ACK / 排序 / 去重）覆盖全链路。**

> **系列定位**：经典前端面试题（IM / 实时通信 / 直播弹幕 高频）。考察的不是"WebSocket 是什么"，而是 **TCP 可靠 ≠ 应用层可靠** + **指数退避的 Jitter 思维** + **ACK 序号双端独立** + **messageId 幂等** + **网络切换与 tab inactive 边界场景**。

---

## 引子：IM 聊天消息"偶尔会丢"，前端怎么处理？

```text
老板：测试同学反馈，IM 聊天消息偶尔会丢，你前端排查一下。
你：WebSocket 不是基于 TCP 吗？TCP 不丢包啊，应该不是我的问题吧？
老板：那是啥问题？半天过去了，你给我一个方案。
你：……
```

**真相是：WebSocket 协议层（应用层帧）和 TCP 传输层都不丢包，但"应用层看不到"就等于丢了**——服务器压根没收到你的请求、半连接被默默掐了、反向代理缓冲了、用户 WiFi 切 4G 时 TCP 连接悄悄断掉但浏览器不知道。

只懂"WebSocket 是双向通信"是 60 分答法。面试官真正想看的是：你能不能从**协议层 → 网络层 → 应用层 → 浏览器机制** 4 层视角，把"消息可靠传输"拆成 5 个可落地的策略。

> 读完本文你能拿到 30s/90s 面试话术 + 4 段可运行实战代码 + 7 个反直觉避坑点 + 5 个高频追问应对。

> 📚 **前置知识**：[WebSocket 协议深度](../../../05.frontend/03-network/websocket/README.md)（先懂协议再看可靠性）

---

## 一、WebSocket 真的会丢包吗？（反直觉开篇）

### 1.1 WebSocket 基于 TCP，理论上不丢包

很多人第一反应：**"WebSocket 是基于 TCP 的，TCP 是可靠传输，不丢包啊？"**

✅ 这个理解**半对**：

| 层级 | 协议 | 是否可靠 |
|------|------|---------|
| **传输层** | TCP（ACK + 重传 + 序号） | ✅ 可靠（数据包层面）|
| **协议层** | WebSocket Frame（基于 TCP） | ✅ 可靠（TCP 之上不丢）|
| **应用层** | 业务消息（基于 WebSocket） | ❌ **不可靠**（"看不见"就是丢）|

**WebSocket 协议层确实不丢包**，因为它跑在 TCP 之上，TCP 会保证所有发送的字节按序到达。但是**应用层的"消息可靠传输" ≠ "TCP 可靠传输"**——TCP 不知道你的"业务消息"是什么，它只负责搬运字节流。

### 1.2 但"应用层看不到"就等于丢了（4 类丢包场景）

实战中"消息丢"的本质是**应用层感知不到消息**——服务器发了但你没收到、或者你发了但服务器没收到、或者两端都发出去了但中间链路断掉。典型场景：

| 场景 | 现象 | 根因 |
|------|------|------|
| **场景 1：服务器未发送** | 服务器根本没收到你的请求（比如网关 502 / 鉴权失败）| HTTP 升级失败 / 鉴权被拦截 |
| **场景 2：半连接（Half-Open）** | TCP 连接看似"活着"但实际已断（NAT/防火墙超时后悄悄 RST）| 应用层心跳缺失 |
| **场景 3：反向代理缓冲** | Nginx 把 WebSocket 帧缓冲起来，前端收不到实时消息 | `proxy_buffering` 默认开启 |
| **场景 4：网络切换** | 用户从 WiFi 切到 4G，IP 变了，TCP 连接悄无声息地死了 | 浏览器不自动重连 |

> **反直觉 ①**：WebSocket "协议层可靠"和"应用层消息可靠"是两回事。面试时把这两个分开说，立刻从 60 分答到 80 分。

---

## 二、5 大策略（核心内容）

要让 WebSocket 消息在应用层"可靠传输"，必须叠加 5 个策略。**这 5 个策略不是互斥的，是层层叠加的缺一不可**：

```
可靠传输 = 心跳（探活）+ 重连（恢复）+ ACK（确认）+ 排序（顺序）+ 去重（幂等）
```

### 2.1 心跳（Heartbeat）—— 让半连接"现形"

**目的**：探测半连接（Half-Open）状态、维持 NAT/防火墙映射。

#### 2.1.1 WebSocket 原生 ping/pong（控制帧）

WebSocket 协议规范定义了**控制帧**（Control Frame）：`Ping` (0x9) 和 `Pong` (0xA)。

```javascript
// 浏览器端：底层会自动响应服务器 ping，但**不允许主动发 ping**
// 所以需要"应用层心跳"来兜底

// 服务端 ping 客户端（Node.js ws 库示例）
ws.ping()  // 发送 Ping 帧
ws.on('pong', () => {
  ws.isAlive = true  // 标记存活
})

// 浏览器 WebSocket API：
// ❌ 没有 ws.ping() 方法
// ❌ 也没有 ws.onpong 事件
// 浏览器自动响应服务器 Ping（不发 Pong 给应用层）
```

**关键事实**：浏览器 WebSocket API **不允许主动 ping**（W3C 规范限制）。所以需要**应用层心跳**（业务消息假装 ping）。

#### 2.1.2 应用层自定义心跳（业务消息 + 时间戳）

```javascript
// 客户端：30 秒发一次心跳（业务消息）
class Heartbeat {
  constructor(ws, intervalMs = 30000) {
    this.ws = ws
    this.intervalMs = intervalMs
    this.timer = null
    this.lastPongAt = Date.now()
  }
  start() {
    this.timer = setInterval(() => {
      // 检查上次 pong 距今是否超过 90s（3 次心跳）
      if (Date.now() - this.lastPongAt > 90_000) {
        console.warn('心跳超时，强制重连')
        this.ws.close()  // 触发 onclose → 走重连逻辑
        return
      }
      // 发应用层心跳（业务消息）
      this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }))
    }, this.intervalMs)
  }
  onPong() {
    this.lastPongAt = Date.now()
  }
  stop() {
    clearInterval(this.timer)
  }
}

// 用法
const ws = new WebSocket('wss://chat.example.com/ws')
const heartbeat = new Heartbeat(ws, 30_000)
ws.addEventListener('open', () => heartbeat.start())
ws.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data)
  if (msg.type === 'pong') heartbeat.onPong()  // 收到 pong 续命
  // ...
})
ws.addEventListener('close', () => heartbeat.stop())
```

**心跳间隔选择**：
- **30-60 秒**：推荐值（NAT/防火墙默认超时 60-120 秒）
- 太短（< 10s）浪费带宽 + 耗电
- 太长（> 60s）容易在 NAT 表项过期前没来得及探测

> **反直觉 ②**：心跳**不是**"检查对方在线"的，而是**"维持 NAT/防火墙映射 + 探测半连接"**。把这条答出来，面试官会眼前一亮。

#### 2.1.3 心跳超时检测（3 次未响应 → 视为断线）

```javascript
// 3 次心跳没响应 = 90s（3 × 30s）→ 视为断线
// 为什么不立即重连？给弱网一点容错
```

### 2.2 重连（Reconnect）—— 指数退避 + Jitter

**目的**：连接断开后恢复，不能"立刻重连"（会雪崩）。

#### 2.2.1 指数退避（Exponential Backoff）

```javascript
// ❌ 错：固定间隔重连（雷鸣群 / thundering herd）
function reconnectBad() {
  setTimeout(() => connect(), 3000)  // 1000 个客户端同时重连 = 服务器雪崩
}

// ✅ 对：指数退避 1s → 2s → 4s → 8s → 16s → 30s（封顶）
function backoffMs(attempt) {
  return Math.min(30_000, 1000 * Math.pow(2, attempt))
}
```

**指数退避序列**：

| 第 N 次重试 | 延迟（基础） | 说明 |
|----------|---------|------|
| 1 | 1s | 第一次快速重试 |
| 2 | 2s | |
| 3 | 4s | |
| 4 | 8s | |
| 5 | 16s | |
| 6 | 30s | 封顶 |
| 7+ | 30s | 不再增长 |

#### 2.2.2 必须加随机抖动（Jitter）：±50%

```javascript
// ✅ 加 Jitter 防雷鸣群（thundering herd）
function backoffWithJitter(attempt) {
  const base = Math.min(30_000, 1000 * Math.pow(2, attempt))
  const jitter = base * 0.5 * (Math.random() - 0.5) * 2  // ±50%
  return base + jitter
}

// 示例：第 3 次重试 base = 4000ms
// 实际可能是 2000ms ~ 6000ms 之间的随机值
```

**为什么必须加 Jitter**：1000 个客户端同时断线，如果不加 Jitter，它们会在同一毫秒重连 → 服务器瞬间被打爆。加 Jitter 后，重连时刻被随机分散在 ±50% 区间内。

> **反直觉 ③**：指数退避**不加 Jitter = 雷鸣群**。大厂生产事故 50% 都源于这条。

#### 2.2.3 最大重连次数 + 状态机

```javascript
class ReconnectWS {
  constructor(url, maxAttempts = 10) {
    this.url = url
    this.maxAttempts = maxAttempts
    this.attempt = 0
    this.state = 'connecting'  // connecting | open | reconnecting | closed | failed
    this.ws = null
  }

  connect() {
    this.state = 'connecting'
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this.attempt = 0
      this.state = 'open'
      console.log('connected')
    }

    this.ws.onclose = () => {
      this.state = 'reconnecting'
      if (this.attempt >= this.maxAttempts) {
        this.state = 'failed'
        alert('连接失败，请刷新页面')  // 提示用户手动重试
        return
      }
      const delay = backoffWithJitter(this.attempt)
      this.attempt++
      setTimeout(() => this.connect(), delay)
    }

    this.ws.onerror = (err) => {
      console.error('ws error', err)
    }
  }
}
```

**完整状态机**：
```
connecting → open → (断网) → reconnecting → open
                                ↓ (失败 10 次)
                              failed → 提示用户
```

### 2.3 ACK 确认 —— 让发送方知道"对方收到了"

**目的**：客户端发消息后要确认服务器收到了。**WebSocket 协议本身不保证应用层 ACK**——服务器只负责"成功把帧送到对端 TCP 缓冲区"，但不保证业务处理成功。

#### 2.3.1 客户端发消息 → 等待 ACK → 超时重传

```javascript
class AckClient {
  constructor(ws, ackTimeoutMs = 5000) {
    this.ws = ws
    this.ackTimeoutMs = ackTimeoutMs
    this.pending = new Map()  // messageId → { resolve, reject, timer, payload }
  }

  send(payload) {
    const messageId = crypto.randomUUID()  // UUID v4
    const message = { ...payload, messageId }
    const envelope = { type: 'chat', messageId, payload }

    return new Promise((resolve, reject) => {
      // 设置 ACK 超时定时器
      const timer = setTimeout(() => {
        this.pending.delete(messageId)
        reject(new Error(`ACK timeout: ${messageId}`))
        // 这里可以选择自动重发（需要 messageId 去重配合）
      }, this.ackTimeoutMs)

      this.pending.set(messageId, { resolve, reject, timer, envelope })
      this.ws.send(JSON.stringify(envelope))
    })
  }

  // 收到 ACK 帧
  onAck(messageId) {
    const entry = this.pending.get(messageId)
    if (entry) {
      clearTimeout(entry.timer)
      this.pending.delete(messageId)
      entry.resolve(entry.envelope)
    }
  }
}

// 服务端 ACK（伪代码）
// ws.on('message', (data) => {
//   const msg = JSON.parse(data)
//   // 处理业务逻辑...
//   ws.send(JSON.stringify({ type: 'ack', messageId: msg.messageId }))
// })
```

#### 2.3.2 ACK 序号双端独立（防服务器重置冲突）

```javascript
// ❌ 错：客户端和服务端共享同一个全局 seq 计数器
// 场景：服务器重启后 seq 从 0 重新开始，客户端已经收到 seq=1000
// 客户端按 seq=0,1,2... 处理 → 全乱

// ✅ 对：ACK 序号双端各自独立
// 客户端：localSeq = 1, 2, 3...（用于客户端排序）
// 服务端：serverSeq = 1, 2, 3...（用于服务端去重）
// 两端互不干扰，服务器重启不影响客户端序号
```

> **反直觉 ④**：ACK 序号必须**双端独立**，否则服务器重启后客户端序号全乱。生产环境血泪教训。

### 2.4 消息排序（Sequence）—— 按顺序处理

**目的**：网络抖动 / 重连可能让消息乱序到达，必须按发送顺序处理。

```javascript
class OrderedHandler {
  constructor() {
    this.nextExpectedSeq = 1  // 期望下一个 seq
    this.buffer = new Map()   // 缓冲未来 seq 的消息
  }

  // 收到消息（可能乱序）
  onMessage(msg) {
    if (msg.seq === this.nextExpectedSeq) {
      this.process(msg)  // 命中 → 处理
      this.nextExpectedSeq++

      // 检查 buffer 里是否有序号连续的
      while (this.buffer.has(this.nextExpectedSeq)) {
        const buffered = this.buffer.get(this.nextExpectedSeq)
        this.buffer.delete(this.nextExpectedSeq)
        this.process(buffered)
        this.nextExpectedSeq++
      }
    } else if (msg.seq > this.nextExpectedSeq) {
      // 未来的消息，先缓存
      this.buffer.set(msg.seq, msg)
      // 可选：触发"跳号请求补发"
      this.requestResend(this.nextExpectedSeq, msg.seq - 1)
    } else {
      // 旧消息（已处理过）→ 丢弃
      console.warn('丢弃过期消息', msg.seq)
    }
  }

  process(msg) {
    // 实际业务处理
    console.log('处理消息', msg.seq, msg.payload)
  }

  requestResend(from, to) {
    // 通知服务端补发 [from, to] 区间的消息
    // this.ws.send(JSON.stringify({ type: 'resend', from, to }))
  }
}
```

### 2.5 消息去重（Deduplication）—— messageId + 服务端幂等

**目的**：ACK 超时重传 + 网络抖动重发，可能让同一条消息到达服务端多次。必须靠 messageId 去重。

#### 2.5.1 客户端：LRU Set 缓存最近 N 个 messageId

```javascript
class Deduplicator {
  constructor(maxSize = 1000) {
    this.maxSize = maxSize
    this.seen = new Set()  // 已见过的 messageId
  }

  // 返回 true = 已处理过（应丢弃），false = 新消息（应处理）
  check(messageId) {
    if (this.seen.has(messageId)) {
      return true  // 已处理，跳过
    }
    this.seen.add(messageId)
    // LRU 淘汰：超过容量删掉最老的
    if (this.seen.size > this.maxSize) {
      const firstKey = this.seen.values().next().value
      this.seen.delete(firstKey)
    }
    return false
  }
}

// 用法
const dedup = new Deduplicator(1000)
ws.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data)
  if (msg.type === 'chat') {
    if (dedup.check(msg.messageId)) return  // 已处理过
    // 处理新消息...
  }
})
```

#### 2.5.2 服务端：幂等保证（业务层去重）

```sql
-- 服务端：消息入库前先检查 messageId（数据库唯一索引）
CREATE TABLE messages (
  id BIGINT PRIMARY KEY,
  message_id VARCHAR(36) NOT NULL UNIQUE,  -- UUID 唯一索引
  content TEXT,
  created_at TIMESTAMP
);

-- INSERT IGNORE INTO messages (id, message_id, content) VALUES (...)
-- 或 ON CONFLICT (message_id) DO NOTHING
```

> **反直觉 ⑤**：消息去重**靠 messageId + 服务端幂等**，**不是**"我以为丢了就重发"。如果服务端不幂等，重发就成"重复消息"了。

---

## 三、实战代码（手写实现）

### 3.1 30 行心跳封装（直接拷贝即用）

```javascript
class WSHeartbeat {
  constructor(ws, opts = {}) {
    this.ws = ws
    this.interval = opts.interval || 30000      // 30s 一次
    this.timeout = opts.timeout || 90000         // 90s 无响应视为断线
    this.timer = null
    this.checkTimer = null
    this.lastPongAt = Date.now()
    this.onTimeout = opts.onTimeout || (() => {})
  }

  start() {
    this.stop()
    this.lastPongAt = Date.now()
    // 心跳发送
    this.timer = setInterval(() => {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping', ts: Date.now() }))
      }
    }, this.interval)
    // 超时检测
    this.checkTimer = setInterval(() => {
      if (Date.now() - this.lastPongAt > this.timeout) {
        this.onTimeout()  // 触发重连
      }
    }, this.interval)
  }

  onPong() {
    this.lastPongAt = Date.now()
  }

  stop() {
    clearInterval(this.timer)
    clearInterval(this.checkTimer)
    this.timer = null
    this.checkTimer = null
  }
}

// 用法
const ws = new WebSocket('wss://chat.example.com/ws')
const heartbeat = new WSHeartbeat(ws, {
  interval: 30000,
  timeout: 90000,
  onTimeout: () => {
    console.warn('心跳超时，主动关闭触发重连')
    ws.close()  // 触发 onclose → 走重连逻辑
  },
})

ws.addEventListener('open', () => heartbeat.start())
ws.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data)
  if (msg.type === 'pong') heartbeat.onPong()
  // ...
})
ws.addEventListener('close', () => heartbeat.stop())
```

### 3.2 指数退避重连（含 Jitter 实现）

```javascript
function reconnectWithBackoff(connectFn, opts = {}) {
  const {
    maxAttempts = 10,
    baseDelay = 1000,
    maxDelay = 30000,
    jitterRatio = 0.5,  // ±50%
  } = opts

  let attempt = 0

  return function tryReconnect() {
    if (attempt >= maxAttempts) {
      console.error('已达最大重连次数，停止重连')
      // 提示用户手动刷新
      return false
    }

    const base = Math.min(maxDelay, baseDelay * Math.pow(2, attempt))
    const jitter = base * jitterRatio * (Math.random() * 2 - 1)
    const delay = Math.max(0, base + jitter)

    console.log(`第 ${attempt + 1} 次重连，延迟 ${delay}ms`)
    attempt++
    setTimeout(connectFn, delay)
    return true
  }
}

// 用法
const tryReconnect = reconnectWithBackoff(() => {
  const ws = new WebSocket('wss://chat.example.com/ws')
  ws.onopen = () => { attempt = 0; heartbeat.start() }
  ws.onclose = () => tryReconnect()
  // ...
}, { maxAttempts: 10, baseDelay: 1000 })
```

### 3.3 ACK 超时重传

```javascript
class ReliableSender {
  constructor(ws, opts = {}) {
    this.ws = ws
    this.ackTimeoutMs = opts.ackTimeoutMs || 5000
    this.maxRetries = opts.maxRetries || 3
    this.pending = new Map()
    this.dedup = new Set()  // 服务端已确认的 messageId
  }

  async send(payload) {
    const messageId = crypto.randomUUID()
    const envelope = { type: 'chat', messageId, payload }

    for (let retry = 0; retry < this.maxRetries; retry++) {
      try {
        await this._sendOnce(envelope, messageId)
        return messageId  // 成功
      } catch (err) {
        console.warn(`第 ${retry + 1} 次发送失败：${err.message}`)
        if (retry === this.maxRetries - 1) throw err
        await this._sleep(1000 * (retry + 1))  // 退避后重试
      }
    }
  }

  _sendOnce(envelope, messageId) {
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(messageId)
        reject(new Error('ACK timeout'))
      }, this.ackTimeoutMs)

      this.pending.set(messageId, { resolve, reject, timer })
      this.ws.send(JSON.stringify(envelope))
    })
  }

  onAck(messageId) {
    const entry = this.pending.get(messageId)
    if (entry) {
      clearTimeout(entry.timer)
      this.pending.delete(messageId)
      entry.resolve()
    }
    this.dedup.add(messageId)
  }

  _sleep(ms) {
    return new Promise(r => setTimeout(r, ms))
  }
}

// 用法
const sender = new ReliableSender(ws, {
  ackTimeoutMs: 5000,
  maxRetries: 3,
})

ws.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data)
  if (msg.type === 'ack') sender.onAck(msg.messageId)
  // ...
})

// 发送消息
await sender.send({ text: '你好', from: 'user-1' })
```

### 3.4 消息去重（LRU Set）

```javascript
class LRUdedup {
  constructor(maxSize = 1000) {
    this.maxSize = maxSize
    this.map = new Map()  // messageId → 插入顺序
  }

  // 返回 true = 已存在（应跳过），false = 新增
  add(messageId) {
    if (this.map.has(messageId)) {
      // 刷新 LRU 顺序
      this.map.delete(messageId)
      this.map.set(messageId, true)
      return true
    }
    this.map.set(messageId, true)
    if (this.map.size > this.maxSize) {
      // 删除最老的（Map 迭代顺序 = 插入顺序）
      const oldest = this.map.keys().next().value
      this.map.delete(oldest)
    }
    return false
  }

  has(messageId) {
    return this.map.has(messageId)
  }

  clear() {
    this.map.clear()
  }
}

// 用法
const dedup = new LRUdedup(1000)
ws.addEventListener('message', (e) => {
  const msg = JSON.parse(e.data)
  if (msg.type === 'chat') {
    if (dedup.add(msg.messageId)) {
      console.log('重复消息，跳过', msg.messageId)
      return
    }
    // 处理新消息...
  }
})
```

---

## 四、7 大反直觉点（避坑指南）

### 反直觉 1：WebSocket 基于 TCP 理论上不丢包，但"应用层看不见"就等于丢了

- ❌ 错答："WebSocket 是 TCP 的，不会丢包"
- ✅ 正解：协议层（WebSocket Frame）确实不丢，但应用层消息**会因为 4 类场景"看不见"**：服务器未发 / 半连接 / 反向代理缓冲 / 网络切换

### 反直觉 2：心跳不是"检查对方在线"，而是"维持 NAT/防火墙映射 + 探测半连接"

- ❌ 错答："心跳是为了确认对方还活着"
- ✅ 正解：NAT/防火墙会**默默 RST 掉**长时间空闲的 TCP 映射（默认 60-120s）。心跳是"假装有数据"维持映射 + 探测"连接看似活但实际已死"的半连接

### 反直觉 3：指数退避不加 Jitter = 雷鸣群（thundering herd）

- ❌ 错答："指数退避就够了"
- ✅ 正解：1000 个客户端同时断线，不加 Jitter 会在同一毫秒重连，服务器瞬间雪崩。**必须**加 ±50% 随机抖动分散重连时刻

### 反直觉 4：ACK 序号必须双端独立，否则服务器重启客户端全乱

- ❌ 错答："用全局递增 seq 就行"
- ✅ 正解：服务器重启后 seq 从 0 开始，但客户端已经收到 seq=1000，**客户端无法区分新旧消息**。两端各自维护自己的 seq，互不干扰

### 反直觉 5：消息去重靠 messageId + 服务端幂等，不是"我以为丢了就重发"

- ❌ 错答："我看 ACK 没回来就重发"
- ✅ 正解：ACK 超时可能是网络延迟，消息其实到了。**重发前必须确认服务端没收到**——靠 messageId 唯一索引 + 数据库 INSERT IGNORE 兜底

### 反直觉 6：浏览器 tab inactive 时 WebSocket 被节流（1 msg/min）

```javascript
// ❌ 隐藏的坑：用户切到别的 tab，你的 WebSocket 发送频率被浏览器节流到 1 msg/min
// 这是 Chrome / Firefox 的后台节流策略（WebSocket 不在白名单）

// ✅ 解法：监听 visibilitychange，tab 可见时主动恢复
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) {
    // tab 切回前台，主动检查心跳 / 重连
    heartbeat.onPong()
    if (ws.readyState !== WebSocket.OPEN) {
      ws.close()  // 触发重连
    }
  }
})
```

### 反直觉 7：网络切换（WiFi → 4G）WebSocket 不自动感知

```javascript
// ❌ 隐藏的坑：用户从 WiFi 切到 4G，IP 变了，TCP 连接悄无声息地死了
// 但浏览器的 ws.readyState 仍然是 OPEN（因为浏览器没收到 RST 通知）

// ✅ 解法：监听 navigator.onLine + online/offline 事件
window.addEventListener('offline', () => {
  console.warn('网络断开，主动关闭连接触发重连')
  ws.close()  // 触发 onclose → 重连
})

window.addEventListener('online', () => {
  console.log('网络恢复，主动重连')
  ws.close()
})

// 兜底：心跳超时（前面 §2.1.3 已讲）
```

---

## 五、面试话术（30s / 90s 版本）

### 30 秒版（精炼版）

> WebSocket 基于 TCP 协议层不丢包，但应用层消息会"看不见"——服务器未发、半连接、反向代理缓冲、网络切换这 4 类场景都会丢。处理思路是 5 个策略叠加：
> 1. **心跳**：30-60s 一次，目的不是检查存活，而是维持 NAT 映射 + 探测半连接
> 2. **重连**：指数退避 1s→2s→4s→8s→30s 封顶，必须加 ±50% Jitter 防雷鸣群
> 3. **ACK**：客户端发消息后等 ACK，5s 超时未回则重发，ACK 序号双端独立
> 4. **排序**：全局递增 seq，客户端按 seq 处理，断号时请求补发
> 5. **去重**：UUID messageId + 客户端 LRU Set + 服务端数据库唯一索引幂等

### 90 秒版（深度版）

> WebSocket "丢包"其实是个伪命题——WebSocket 基于 TCP，协议层确实不丢包。但**应用层消息可靠传输**和 TCP 可靠传输是两回事。实战中"消息丢"的本质是**应用层感知不到消息**，典型场景有 4 类：服务器压根没收到你的请求、TCP 半连接（NAT 超时但浏览器不知道）、反向代理缓冲了帧、用户从 WiFi 切到 4G。
>
> 要解决应用层可靠传输，必须叠加 5 个策略：
>
> **第一，心跳**。30-60 秒一次应用层心跳消息，目的不是"检查对方在线"，而是**维持 NAT/防火墙的 TCP 映射（默认 60-120 秒超时）+ 探测半连接**。3 次心跳没回应（90s）就主动关闭走重连。浏览器 WebSocket API 不允许主动发 ping，必须用应用层心跳兜底。
>
> **第二，重连**。连接断开后用指数退避：1s → 2s → 4s → 8s → 16s → 30s 封顶。**必须加 ±50% Jitter**，否则 1000 个客户端同时断线会在同一毫秒重连，服务器瞬间被打爆——这就是雷鸣群效应。
>
> **第三，ACK**。客户端发消息后等 ACK，5 秒没回就重发。但**ACK 序号必须双端独立**——服务器重启后序号从 0 开始，如果客户端按全局 seq 处理就会全乱。
>
> **第四，排序**。全局递增 seq，客户端按 seq 处理，断号时主动请求服务端补发。
>
> **第五，去重**。每条消息带 UUID messageId，客户端用 LRU Set 缓存最近 1000 个防止重复处理，**服务端必须用 messageId 唯一索引幂等**——否则客户端重发就成重复消息了。
>
> 还有两个**反直觉的坑**：浏览器 tab 切到后台时 WebSocket 会被节流到 1 msg/min，要靠 visibilitychange 监听恢复；用户从 WiFi 切到 4G 时 TCP 连接悄无声息地死掉，要靠 navigator.onLine + online/offline 事件主动重连。

### 关键术语清单（背诵）

- **Heartbeat（心跳）**：NAT/防火墙保活 + 探测半连接
- **Reconnect / Exponential Backoff / Jitter（重连/指数退避/抖动）**：防雷鸣群
- **ACK / 序号双端独立（Acknowledgment）**：确认对方收到
- **Sequence / Ordering（排序）**：处理乱序
- **Deduplication / Idempotency（去重/幂等）**：靠 messageId + 数据库唯一索引
- **Half-Open Connection（半连接）**：TCP 看似活但实际已死
- **Thundering Herd（雷鸣群）**：大量客户端同时重连雪崩

---

## 六、5 个追问模板（面试官可能继续问）

### Q1：SSE 也有同样问题吗？

**答**：SSE 有**内置自动重连**（`Last-Event-ID` + `retry` 字段），浏览器自动处理断线重连。但 SSE 没有 ACK（单向推）、没有 messageId 去重（依赖 Last-Event-ID 服务端去重）。SSE 适合**单向流式**（AI 对话 / 通知），WebSocket 适合**双向通信**（IM / 协同编辑）。

详见 [SSE vs WebSocket — AI 对话为什么选 SSE](../../02.computer-basics/sse-vs-websocket/README.md)

### Q2：消息可靠传输 vs WebSocket 协议层可靠 vs TCP 可靠 三者区别？

**答**：

| 层级 | 含义 | 谁负责 |
|------|------|--------|
| **TCP 可靠** | 字节流按序到达，不丢包不重复 | 内核 TCP 协议栈 |
| **WebSocket 协议层可靠** | WebSocket Frame 在 TCP 之上，协议层不丢包 | 浏览器 + 服务端 WS 实现 |
| **应用层消息可靠** | 业务消息从用户 A 的"发送"动作到用户 B 的"看到"全过程可靠 | 业务代码（前端 + 后端 + 存储）|

**关键**：WebSocket 协议层可靠**不保证**应用层可靠。**应用层可靠 = 心跳 + 重连 + ACK + 排序 + 去重** 五件套。

### Q3：浏览器多 Tab 时如何共享 WebSocket 连接？

**答**：3 种方案：

| 方案 | 实现 | 优缺点 |
|------|------|--------|
| **每个 Tab 独立连接** | 不共享 | 简单但浪费（10 个 Tab = 10 个连接）|
| **BroadcastChannel 同步** | 一个 Tab 拥有连接，其他 Tab 监听消息广播 | 节省连接，但 "拥有者" Tab 关掉要转移 |
| **SharedWorker 共享** | SharedWorker 维护连接，所有 Tab 共享 | 最优雅，但兼容性（旧浏览器不支持）|

```javascript
// BroadcastChannel 示例
const channel = new BroadcastChannel('ws-shared')
const ws = new WebSocket('wss://chat.example.com/ws')
ws.onmessage = (e) => {
  channel.postMessage(e.data)  // 广播给其他 Tab
}
channel.onmessage = (e) => {
  // 其他 Tab 发来的消息（如发送消息）
  ws.send(e.data)
}
```

### Q4：心跳包大小多大合适？心跳频率 vs 移动端耗电？

**答**：

| 场景 | 心跳间隔 | 心跳大小 | 说明 |
|------|---------|---------|------|
| **PC 浏览器** | 30s | 几十字节（`{type:'ping',ts:1234}`）| 平衡 |
| **移动 Web** | 60s | 几十字节 | 省电（基站切换频繁）|
| **Native App** | 30-60s | 心跳包 + 业务数据 | 可携带增量数据 |
| **弱网（2G/3G）** | 90s | 极小（`<10` 字节）| 省流量 |

**反直觉**：心跳频率太高**不会更可靠**，反而会**增加耗电 + 占用带宽**。30s 是工业界默认平衡值。

### Q5：WebSocket 鉴权怎么做？

**答**：3 种方案：

| 方案 | 实现 | 优缺点 |
|------|------|--------|
| **URL 带 Token（推荐）** | `wss://chat.example.com/ws?token=xxx` | 简单，但 Token 会进 access log |
| **Sec-WebSocket-Protocol** | 客户端在握手时把 Token 放在子协议头 | 不进 access log，更安全 |
| **握手后第一帧发 Token** | 客户端连接成功后立即发 `{type:'auth',token:'xxx'}` | 最灵活，但增加一次交互 |

**安全提示**：**不要**把长期 Token 放在 URL（会被中间件日志记录），推荐用短期 JWT + 握手后第一帧鉴权。

---

## 七、相关章节（必看）

### 同栏目兄弟（高频面试题）

- [网页端接受推送消息的方式 — message](../message/README.md) — 轮询 / SSE / WebSocket / WebTransport 全景对比（推送方案选型基础）
- [SSE vs WebSocket — AI 对话为什么选 SSE](../../02.computer-basics/sse-vs-websocket/README.md) — 协议对比（WebSocket vs SSE 选型决策）
- [跨端框架设计](../cross-platform-framework-design/README.md) — WebSocket 在跨端场景的桥接（JSBridge 心跳）

### 主模块深度（必读）

- [WebSocket 协议深度](../../../05.frontend/03-network/websocket/README.md) — 协议原理 + 4 大实现库 + vs SSE 对比（理解 WebSocket 是什么）

### 跨栏目实战（可选）

- [直播弹幕 100k 实战](../../04.system-design/live-barrage-100k/README.md) — WebSocket 百万连接的工程实践（WebSocket 集群、Redis Pub/Sub、消息可靠性）

### 互链反指（指向本文件）

- `12.interview/02.computer-basics/sse-vs-websocket/README.md` — 协议对比时反链本文件
- `05.frontend/03-network/websocket/README.md` — 主模块深度时反链本文件
- `12.interview/09.front-end/message/README.md` — 消息推送全景时反链本文件

---

> 📅 2026-09-21 · 咬文嚼字 · WebSocket 可靠性 · ⭐⭐⭐⭐⭐（高频面试 + 实战必会 + 5 策略 + 7 反直觉点）

← [返回: 09.front-end](../README.md)
