<!--
question:
  id: 09.front-end-cross-platform-framework-design
  topic: 09.front-end
  difficulty: ⭐⭐⭐⭐
  frequency: 高频
  scenario_type: 架构决策困境
  tags: [09.front-end, cross-platform, ast, bridge, runtime]
-->

# 跨端框架设计深度剖析：从零设计跨端框架要回答的 7 个问题

> 一句话定位：跨端框架设计 = 编译时 AST 转换 + 运行时 API 适配 + 沙箱隔离 —— 不是 polyfill，而是产物分支。

> **系列定位**：经典前端架构师面试题（高频、架构决策题）。考察的不是"用过 Taro 吗"，而是 **跨端运行时差异理解** + **AST 转换原理** + **JSBridge 性能瓶颈**。完整概念见 [主模块深度原理](../../../05.frontend/08-cross-platform/cross-platform-framework-design/README.md)。

---

## 引子：老板让你从零设计跨端框架，先做哪 3 件事？

2026 年初，老板拍着你肩膀说："咱们公司 5 个 App、3 个小程序、2 个 H5 站点，同一个后端。给你 6 个月，从零搭一个跨端框架，让业务只写一套代码就能跑所有端。先做哪 3 件事？"

你打开 IDE，发现 3 大现实问题扑面而来：

- **小程序没有 DOM**，`document.querySelector` 在微信环境里直接报 undefined
- **App WebView 的 iOS JSCore 在 iOS 13 上不支持 JIT**，JS 执行速度是 Chrome V8 的 1/3
- **JSBridge 传 100KB 数据要 200ms+**，活动页 1 万个商品一次性传给原生就卡到崩溃

面试官想要的答案，**不是"用 Taro"**，而是"我知道 Taro 底下是什么"。

---

## 一、核心原理（必读）

### 1.1 跨端框架要解决的 3 个根本矛盾

```text
矛盾 1：统一源码 vs 多端 DSL
  - 业务想写一套 JSX/React
  - 端要 WXML/HTML/AXML 不同 DSL
  - 解决：编译时 AST 转换（产物分支）

矛盾 2：统一 API vs 多端运行时
  - 业务想写 Taro.request(url, options)
  - 端要 wx.request / fetch / JSBridge
  - 解决：运行时 API 标准化层

矛盾 3：业务复用 vs 沙箱隔离
  - 业务想用 DOM、Cookie、IndexedDB
  - 端的安全模型只允许有限 API
  - 解决：每端独立沙箱，差异下沉到框架
```

### 1.2 编译时 vs 运行时的关键决策

| 维度 | 编译时（AST 转换） | 运行时（API 适配） |
|------|-------------------|-------------------|
| **处理时机** | 构建时 | 运行时 |
| **性能损耗** | 无（已编译为端代码） | 有（每次调用都走适配层） |
| **包大小** | 较大（每个端打包对应实现） | 较小（一份适配代码） |
| **调试友好** | 较好（可看到编译产物） | 一般（运行时拦截） |
| **跨端条件编译** | ✅ 产物分支 | ⚠️ 运行时分支 |
| **典型场景** | 组件映射、样式单位 | API 标准化 |

**核心原则**：**能用编译时做的，绝不用运行时**。运行时适配只是兜底。

---

## 二、3 端运行时模型对比（含表格）

### 2.1 线程模型差异

| 端 | 线程模型 | JS 引擎 | 真实 DOM | BOM |
|----|---------|---------|---------|-----|
| **微信小程序** | 双线程（逻辑层 + 渲染层） | V8（微信定制） | ❌ 无 | ❌ 无 |
| **H5** | 单线程 + Event Loop | V8（浏览器） | ✅ 有 | ✅ 有 |
| **App WebView** | 单线程 | JSCore（iOS）/ V8（Android） | ✅ 有 | ✅ 有 |

### 2.2 双线程架构的工作原理（小程序）

```text
┌──────────────────────────────────────────┐
│                微信客户端                  │
│  ┌──────────────────┐  ┌────────────────┐ │
│  │   逻辑层（JS）    │  │  渲染层（WebView）│ │
│  │   V8 引擎         │  │  浏览器内核      │ │
│  │   - 业务逻辑       │  │  - WXML 渲染     │ │
│  │   - 数据处理       │  │  - WXSS 样式     │ │
│  │   - setData()     │  │  - 真实 DOM      │ │
│  └────────┬─────────┘  └────────┬───────┘ │
│           │   JSBridge          │         │
│           │   (postMessage +    │         │
│           │    evaluateJS)      │         │
└───────────┼──────────────────────┼─────────┘
            ▼                      ▼
        业务逻辑              UI 渲染
```

**双线程架构的好处**：JS 线程无法阻塞 UI 渲染（防止长任务卡顿），JS 无权操作 DOM（防止 XSS）。

**双线程的代价**：`setData` 不是同步的（5-50ms 延迟），大量数据 setData 性能急剧下降。

### 2.3 单线程的 Event Loop 模型（H5 / App WebView）

```text
任务队列（宏任务）：
  - setTimeout / setInterval
  - I/O（fetch 完成）
  - 事件回调

微任务队列：
  - Promise.then
  - MutationObserver

执行顺序：
  1. 执行同步代码
  2. 清空微任务队列
  3. 取出 1 个宏任务执行
  4. 重复 2-3
```

**长任务阻塞**：JS 任务超过 50ms 会阻塞渲染，导致页面卡顿。

---

## 三、代码转换机制（AST + 组件映射 + 样式适配）

### 3.1 跨端框架的编译流程

```text
统一源码（JSX / Vue SFC）
   ↓
Babel/Parser → AST（抽象语法树）
   ↓
AST 转换器（按 target 走不同分支）
   ↓
各端代码生成器
   ↓
产物：
  - 微信小程序：WXML + WXSS + JS
  - H5：HTML + CSS + JS
  - App：HTML + CSS + JS + JSBridge 调用
```

### 3.2 组件映射表

| 统一组件 | 微信小程序 | H5 | App WebView |
|---------|----------|-----|------------|
| `<View>` | `<view>` | `<div>` | `<div>` |
| `<Text>` | `<text>` | `<span>` | `<span>` |
| `<Image>` | `<image>` | `<img>` | `<img>` |
| `<Button>` | `<button>` | `<button>` | `<button>` |
| `<ScrollView>` | `<scroll-view>` | `<div>` + overflow | `<div>` + overflow |

### 3.3 样式单位适配（px → rpx / rem / vw）

| 端 | 推荐单位 | 设计稿基准 |
|----|---------|-----------|
| 微信小程序 | rpx（750rpx = 屏幕宽度） | 750px |
| H5 | rem / vw | 750px / 375px |
| App WebView | rem / px | 750px |

**统一方案**：源码用 `px`，编译时按端转换：

```js
// Taro 的 pxTransform 配置
{
  designWidth: 750,
  deviceRatio: { 640: 2.34/2, 750: 1, 828: 1.81/2, 375: 2/1 }
}
```

### 3.4 条件编译：产物分支 vs 运行时判断

```js
// 方式 1：运行时判断（❌ 反模式）
if (typeof wx !== 'undefined' && wx.request) {
  wx.request({ ... })
} else {
  fetch(url, ...)
}

// 方式 2：编译时分支（✅ 推荐）
// utils.weapp.js → 仅微信小程序打包
// utils.h5.js → 仅 H5 打包
// utils.js → 默认打包
import request from './utils'
```

**反直觉**：跨端条件编译**不是 polyfill**，而是**产物分支**。运行时 polyfill 有性能损耗，产物分支无损耗但增加包大小。

---

## 四、运行时适配层（API 标准化 + JS 引擎差异 + JSBridge）

### 4.1 API 标准化层

```text
业务代码（统一 API）
   ↓
标准化层（Taro.request / wx.request / fetch / JSBridge）
   ↓
平台实现（按 target 选择不同实现）
```

**网络请求标准化示例**：

```js
// 统一 API（Taro）
Taro.request({
  url: '/api/user',
  method: 'POST',
  data: { name: 'ming' }
})

// 微信小程序实现
wx.request({ url, method, data, success, fail })

// H5 实现
fetch(url, { method, body: JSON.stringify(data) })
  .then(res => res.json())

// App WebView 实现
fetch(url, { method, body: JSON.stringify(data) })
  .then(res => res.json())
```

### 4.2 JS 引擎差异（性能关键）

| 引擎 | 版本 | 兼容性 | 性能 |
|------|------|--------|------|
| V8（微信/H5/Android） | 8.x+ | 支持 ES2020 | ⭐⭐⭐⭐⭐ |
| JSCore（iOS 13） | iOS 13 | 不支持 JIT | ⭐⭐⭐ |
| JSCore（iOS 14+） | iOS 14+ | 启用 Nitro | ⭐⭐⭐⭐ |
| Hermes（React Native） | 0.7+ | 字节码预编译 | ⭐⭐⭐⭐ |

**反直觉点**：JSCore 在 iOS 13 及以下不支持 JIT 编译，**App WebView 在老版本 iOS 的 JS 性能是 Chrome V8 的 1/3**。这是为什么老版本 iOS WebView 卡顿严重。

### 4.3 JSBridge 的性能瓶颈

```text
JS 层                          原生层（Native）
  │                                 │
  │ window.webkit.messageHandlers  │
  │   .nativeBridge.postMessage()   │
  │ ──────────────────────────────► │
  │                                 │ 原生处理
  │ ◄────────────────────────────── │
  │ callback(data)                  │
```

**JSBridge 的性能规律**：

| 数据量 | 耗时 | 主要瓶颈 |
|--------|------|---------|
| < 1KB | < 1ms | 跨语言调用 |
| 1-100KB | 1-50ms | JSON 序列化 |
| > 100KB | > 100ms | 序列化 + 跨进程通信 |
| > 1MB | > 1s | 序列化 + 跨进程 + 原生处理 |

**反直觉点**：**JSBridge 的性能瓶颈不在 JS 引擎，而在 JSON 序列化**。1000 个商品一次性 JSBridge 传输，序列化耗时是传输耗时的 10 倍。

**实战优化**：
```js
// ❌ 大数据 JSBridge 调用（卡顿）
window.webkit.messageHandlers.bridge.postMessage({
  action: 'syncProducts',
  data: products  // 1000 个商品 × 500 字节 = 500KB
})

// ✅ 分批 JSBridge 调用（流畅）
const chunks = chunkArray(products, 50)
chunks.forEach((chunk, i) => {
  setTimeout(() => {
    window.webkit.messageHandlers.bridge.postMessage({
      action: 'syncProducts',
      batch: i,
      data: chunk
    })
  }, i * 16)  // 60fps 节流
})
```

---

## 五、5 个反直觉点（含 ❌/✅ 对照）

### 反直觉 1：小程序没有 BOM/DOM

❌ **错误认知**：以为小程序是"阉割版 Web"，可以直接用 `document.querySelector`。

```js
// 小程序里
document.querySelector('#app')  // ❌ 报错：document is not defined
window.location.href = '/next'  // ❌ 报错：location is not defined
```

✅ **真相**：小程序运行在 V8 引擎里，但**没有 BOM/DOM 对象**。所有 DOM 操作通过框架封装（如 `Taro.createSelectorQuery()`）。

### 反直觉 2：setData 不是同步的

❌ **错误认知**：以为 `setData` 后立刻能读到新值。

```js
// ❌ 错误用法
this.setData({ count: 1 })
console.log(this.data.count)  // 打印旧值（异步）
```

✅ **真相**：`setData` 通过 JSBridge 推送到渲染层（5-50ms 延迟）。需要立即使用新值，必须用局部变量。

```js
// ✅ 正确用法
const newCount = this.data.count + 1
this.setData({ count: newCount })
console.log(newCount)  // 直接用新值
```

**频繁 setData 触发渲染线程排队**：1ms 内连续调用 100 次 `setData` → 渲染层合并为 1 次渲染。但每次 `setData` 的数据都会被 **JSON 序列化**，频繁调用有性能损耗。**最佳实践：合并 setData**。

### 反直觉 3：JSBridge 跨域性能瓶颈在大数据量

❌ **错误认知**：以为 JSBridge 性能瓶颈在 JS 引擎。

✅ **真相**：JSBridge 性能瓶颈在 **JSON 序列化 + 跨语言边界调用**。> 100KB 数据传输，序列化耗时是传输耗时的 10 倍。

### 反直觉 4：H5 的 IndexedDB 在小程序里没有

❌ **错误认知**：以为 IndexedDB 是 Web 标准，小程序也能用。

✅ **真相**：微信小程序没有 IndexedDB，必须用 `wx.setStorage`（10MB 上限）。

```js
// H5
const req = indexedDB.open('myDB', 1)  // H5 支持

// 小程序（必须用 wx.storage）
wx.setStorage({ key: 'userInfo', data: { name: 'ming' } })  // 小程序支持

// 跨端兼容写法（Taro 标准化层）
Taro.setStorage({ key: 'userInfo', data: { name: 'ming' } })
// Taro 编译时根据 target 自动选择 wx.setStorage / localStorage
```

### 反直觉 5：跨端条件编译不是 polyfill

❌ **错误认知**：以为条件编译是"运行时 polyfill"（运行时判断端类型再调用不同 API）。

✅ **真相**：跨端条件编译是 **产物分支**（编译时生成不同代码）。运行时判断有性能损耗，且包大小膨胀。

---

## 六、解决（含代码块 + 配置 diff）

### 6.1 跨端组件库的抽象封装

```jsx
// 业务代码（统一组件）
import { View, Text, Button } from '@cross-platform/ui'

function Page() {
  return (
    <View className="page">
      <Text>Hello, Cross-Platform!</Text>
      <Button onClick={handleClick}>Click</Button>
    </View>
  )
}

// @cross-platform/ui 的实现
// - View → 各端映射（view/div）
// - Text → 各端映射（text/span）
// - Button → 各端映射（button）
```

### 6.2 网络请求统一封装

```js
// src/utils/request.js（跨端兼容）
import Taro from '@tarojs/taro'

export function request(options) {
  // Taro 自动按 target 选 wx.request / fetch
  return Taro.request({
    url: options.url,
    method: options.method || 'GET',
    data: options.data,
    header: options.header || {}
  })
}
```

### 6.3 大数据 setData 优化

```js
// ❌ 频繁 setData（性能差）
items.forEach(item => {
  this.setData({ [`item_${item.id}`]: item })  // 100 次 setData
})

// ✅ 合并 setData（性能好）
const updateObj = {}
items.forEach(item => {
  updateObj[`item_${item.id}`] = item
})
this.setData(updateObj)  // 1 次 setData

// ✅ 分批 setData（超大数据）
const batches = chunkArray(items, 50)
batches.forEach((batch, i) => {
  setTimeout(() => {
    const updateObj = {}
    batch.forEach(item => {
      updateObj[`item_${item.id}`] = item
    })
    this.setData(updateObj)
  }, i * 16)  // 60fps 节流
})
```

### 6.4 JSBridge 数据分批传输

```js
// src/utils/bridge.js（App WebView）
function callBridge(method, data) {
  // 大数据自动分批
  if (JSON.stringify(data).length > 100 * 1024) {
    return callBridgeInChunks(method, data, 50)
  }
  
  return new Promise((resolve, reject) => {
    window.webkit.messageHandlers.bridge.postMessage({
      method,
      data,
      callbackId: Date.now() + '_' + Math.random()
    })
    // 监听回调
    window.addEventListener('bridgeCallback_' + callbackId, (e) => {
      resolve(e.detail)
    })
  })
}
```

---

## 七、面试话术（30s / 90s 版本）

### 30s 简短版（适合追问 + 时间紧迫）

> "跨端框架设计 3 大核心：**编译时 AST 转换**（把统一 JSX 编译成各端 DSL）、**运行时 API 标准化层**（Taro.request 屏蔽 wx.request / fetch / JSBridge 差异）、**沙箱隔离**（每端独立沙箱，差异下沉到框架）。关键反直觉：1) 小程序没有 BOM/DOM；2) `setData` 不是同步的（5-50ms 延迟）；3) JSBridge 性能瓶颈在 JSON 序列化，> 100KB 数据要分批传。"

### 90s 完整版（适合技术终面）

> "从零设计跨端框架，要回答 3 个根本矛盾：
>
> 1. **统一源码 vs 多端 DSL**：用编译时 AST 转换，Babel 把 JSX 转成各端代码。组件映射表（如 View → view/div），样式单位适配（px → rpx/rem）。
>
> 2. **统一 API vs 多端运行时**：用运行时 API 标准化层，业务调 Taro.request，框架内部根据 target 选 wx.request / fetch / JSBridge。
>
> 3. **业务复用 vs 沙箱隔离**：每端独立沙箱，小程序是双线程隔离，App WebView 是 JSBridge 白名单。
>
> 关键反直觉点有 5 个：
>
> - 小程序没有 BOM/DOM，document.querySelector 直接报错
> - setData 不是同步的，5-50ms 延迟，频繁调用要合并
> - JSBridge 性能瓶颈在 JSON 序列化，> 100KB 要分批
> - H5 的 IndexedDB 小程序里没有，必须用 wx.storage
> - 条件编译是产物分支，不是运行时 polyfill
>
> 实际项目中要权衡：编译时处理（无性能损耗但包大）vs 运行时处理（包小但有性能损耗）。"

### 关键词流（面试官会重点抓取）

- AST 转换、Babel、组件映射表、API 标准化层
- 双线程 vs 单线程、V8 vs JSCore、JIT 编译
- JSBridge、JSON 序列化、跨语言调用
- 沙箱隔离、白名单、SourceMap

---

## 八、追问模板（5 个高频追问）

### 追问 1：小程序为什么要双线程？Web Worker 不行吗？

**回答要点**：
- 双线程的核心目的：**JS 无法操作 DOM**（防止 XSS）+ **JS 不阻塞 UI**（防止长任务）
- Web Worker 也无法操作 DOM，但 **Web Worker 是同进程子线程**，小程序双线程是**跨进程通信**（更彻底隔离）
- 双线程代价：setData 跨线程传输有 5-50ms 延迟

### 追问 2：setData 频繁调用会不会被合并？

**回答要点**：
- V8 内部 batching：1ms 内连续调用 100 次 `setData` → 渲染层合并为 1 次渲染
- 但每次 `setData` 的数据都会 **JSON 序列化** → 频繁调用有性能损耗
- 最佳实践：**手动合并 setData**（一次调用设置多个字段）

### 追问 3：JSBridge 为什么大数据量会卡顿？

**回答要点**：
- JSBridge 性能瓶颈在 **JSON 序列化**（数据越大，序列化时间越长）
- 数据 > 100KB 时，序列化耗时 > 跨语言调用耗时
- 优化方案：**分批传输**（50 条/批）+ **60fps 节流**

### 追问 4：跨端条件编译和 polyfill 的本质区别？

**回答要点**：
- **条件编译**：编译时生成不同产物（每个端打包对应实现）→ **无运行时性能损耗**，但**包大小膨胀**
- **Polyfill**：运行时判断端类型再调用不同 API → **包大小可控**，但**每次调用都有性能损耗**

### 追问 5：iOS 13 WebView 性能差，怎么优化？

**回答要点**：
- iOS 13 JSCore **不支持 JIT 编译**，JS 执行速度是 Chrome V8 的 1/3
- 优化策略：
  1. **减少 JS 计算**（用 CSS 动画替代 JS 动画）
  2. **避免大型 JS 框架**（用轻量库如 Preact 替代 React）
  3. **用 WebAssembly**（计算密集型任务用 Rust/C++ 编译）

---

## 九、相关章节

### 9.1 同栏目兄弟链

- [Virtual DOM 与 Diff 算法](../virtual-dom-diff/README.md) — Virtual DOM 的"JS 对象描述 DOM"思想，与跨端组件映射（统一组件 → 各端 DOM）是同一思路
- [HTTP 缓存](../http-cache/README.md) — App WebView 缓存策略与 H5 HTTP 缓存的差异

### 9.2 主模块深度原理

- [跨端框架设计深度原理](../../../05.frontend/08-cross-platform/cross-platform-framework-design/README.md) — 架构师视角的 5 层架构 + 实战案例

### 9.3 跨模块关联

- [XSS / CSRF / CSP](../../05.security/xss-csrf-csp/README.md) — WebView 桥接与 XSS 攻击的关联（JSBridge 是潜在的 XSS 入口）

### 9.4 餐厅叙事版

- [一个厨房，四个门面](../../../13.story/20-multiplatform-architecture.md) — 阿明餐厅的多端架构哲学（用餐厅叙事讲透跨端原理）

---

> 📅 2026-09-21 · 咬文嚼字 · 前端架构 · ⭐⭐⭐⭐（高频面试 + 架构师必会）

← [返回: 09.front-end](../README.md)
