<!--
module:
  parent: front-end
  slug: front-end/cross-platform-framework-design
  type: article
  category: 主模块子文章
  summary: 跨端框架设计：编译时 AST 转换 + 运行时适配层 + 沙箱隔离 三层架构原理。
  depth: ⭐⭐⭐⭐⭐
-->

# 跨端框架设计：从零设计跨端框架（小程序 + H5 + App WebView）

> 一句话定位：**跨端 = 编译时 AST 转换 + 运行时 API 适配 + 沙箱隔离 —— 用一套源码生成多个产物，每个产物在目标端的"双线程 / 单线程 / 多 WebView"运行时里跑通。**

> **系列定位**：架构师级别内容。不讲"如何用 Taro"（那是使用层），讲"如何从零设计一个 Taro"。覆盖微信小程序双线程模型、H5 单线程、App WebView（WKWebView / Chrome WebView）三大运行时的差异、AST 转换原理、JSBridge 桥接性能瓶颈、5+ 个反直觉点。

---

## 一、为什么需要"跨端框架"

业务诉求：**一份代码** → **N 个平台**（微信 / 支付宝 / 抖音 小程序 + H5 + iOS/Android App WebView）。如果没有跨端框架，每个平台都要单独写一套：

| 端 | DSL | 渲染线程 | JS 引擎 | 维护成本 |
|----|-----|---------|---------|---------|
| 微信小程序 | WXML/WXSS/JS | 逻辑层 + 渲染层（双线程） | V8 | 1 套 |
| 支付宝小程序 | AXML/ACSS/JS | 双线程 | V8 | 1 套 |
| 抖音小程序 | TTML/TTSS/JS | 双线程 | V8 | 1 套 |
| H5 | HTML/CSS/JS | 单线程 | 浏览器 V8 | 1 套 |
| App WebView | HTML/CSS/JS | 单线程（iOS WKWebView/Android Chrome WebView） | JSCore（iOS）/ V8（Android） | 1 套 |

→ **5 套代码 = 5 倍维护成本 + 5 倍 bug 修复 + 5 倍团队人力**。

跨端框架的核心使命：**统一源码 + 差异下沉到框架层**，业务只写一套，业务感知不到"端"的差异。

---

## 二、三端运行时差异（核心问题）

跨端框架的最大难点：**三端的运行时模型根本不同**。如果把它们当成"一样的环境"，跨端框架就会在性能、兼容性、调试上踩坑。

### 2.1 微信小程序：双线程架构

微信小程序采用 **逻辑层 + 渲染层** 分离的双线程架构：

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

**为什么要双线程？**
- **安全**：JS 无法直接操作 DOM（防止 XSS、防止误操作阻塞 UI）
- **性能**：渲染线程不跑 JS（防止 JS 长任务阻塞 UI 渲染）
- **隔离**：每个页面独立 WebView（内存隔离）

**双线程的代价：**
- **`setData()` 不是同步的**：逻辑层调用 `setData` → JSBridge 序列化 → 渲染层 deserialize → 渲染线程调度 → 真正渲染。这条链路耗时 5-50ms。
- **大数据量 setData 卡顿**：超过 100KB 数据 setData，序列化 + 跨线程传输 + 反序列化 + diff 渲染全程耗时 ≥ 200ms，肉眼可见卡顿。
- **API 只能在逻辑层调用**：`wx.*` API 在渲染层调用会失败。

### 2.2 H5：单线程 + 浏览器多进程

H5 在浏览器中运行，采用 **单 JS 线程 + 渲染线程 + 异步任务队列** 模型：

```text
┌─────────────────────────────────┐
│        浏览器进程                 │
│  ┌──────────────────────────┐   │
│  │ 渲染进程（Renderer）        │   │
│  │  - JS 主线程（V8/SpiderMonkey）│
│  │  - GUI 渲染线程            │   │
│  │  - 事件循环（Event Loop）    │   │
│  │  - Web API（DOM/BOM/Fetch）│   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │ 浏览器进程                   │   │
│  │  - 网络栈                   │   │
│  │  - 存储（IndexedDB/LocalStorage）│
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

**单线程的优势：**
- 直接操作 DOM（`document.querySelector` 可用）
- 标准 Web API（Fetch / IndexedDB / WebSocket）
- Event Loop 模型清晰（宏任务 / 微任务）

**单线程的劣势：**
- 长任务阻塞渲染（>50ms 的 JS 任务会让页面卡顿）
- 主线程崩溃 = 页面崩溃

### 2.3 App WebView：多形态运行时

App 内嵌的 WebView（Hybrid App）有 3 种形态：

| 形态 | 引擎 | 代表 | 备注 |
|------|------|------|------|
| **iOS WKWebView** | JSCore / Nitro（iOS 14+） | Safari 引擎 | JavaScriptCore 在 iOS 7+，Nitro 是 iOS 14 后的 JIT 优化 |
| **Android Chrome WebView** | V8 | Chrome 内核 | Chromium 内核版本随系统更新 |
| **X5 内核（QQ/微信内置）** | V8 + 自定义 | 微信 WebView、QQ 浏览器 | 国内兼容性优化 |

**WebView 的关键差异：**
- **iOS WKWebView** 内存限制严格（300MB 左右），超出会白屏
- **Android Chrome WebView** 各厂商魔改严重（小米、华为、OPPO 的 WebView 行为不一致）
- **X5 内核** 提供 `window.__wxjs_environment` 标识

### 2.4 三端运行时差异速查表

| 维度 | 微信小程序 | H5 | App WebView |
|------|----------|-----|------------|
| **线程模型** | 双线程（逻辑层 + 渲染层） | 单线程 | 单线程 |
| **JS 引擎** | V8（微信定制） | 浏览器 V8 | JSCore / V8 / X5 |
| **DOM** | 无真实 DOM | 真实 DOM | 真实 DOM |
| **API 体系** | `wx.*` 平台 API | Web API | Web API + JSBridge |
| **存储** | `wx.setStorage`（10MB） | LocalStorage / IndexedDB | LocalStorage + JSBridge |
| **网络** | `wx.request` | fetch / axios | fetch + JSBridge |
| **跳转** | `wx.navigateTo` | History API | History API + JSBridge |
| **路由数限制** | 10 层 | 无限制 | 无限制 |
| **包大小限制** | 主包 2MB | 无 | 无（App 端看 WebView 加载） |

---

## 三、编译时：AST 转换与多端产物生成

跨端框架的第一道难关：**把统一源码编译成不同端的 DSL**。

### 3.1 AST 转换原理

跨端框架的核心编译流程：

```text
统一源码（JSX/Vue）
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

**Taro 4 的实际编译**（以 `<View>` 组件为例）：

```jsx
// 源码（统一）
<View className="container" onClick={handleClick}>
  <Text>{count}</Text>
</View>
```

**编译到微信小程序**（产物）：
```html
<!-- WXML -->
<view class="container" bindtap="handleClick">
  <text>{{count}}</text>
</view>
```

**编译到 H5**（产物）：
```html
<!-- HTML -->
<div class="container" onclick="handleClick()">
  <span>count</span>
</div>
```

**编译到 App WebView**（产物）：
```html
<!-- HTML -->
<div class="container" data-bridge-tap="handleClick">
  <span>count</span>
</div>
```

### 3.2 组件映射表

跨端框架的核心是 **组件映射表**（Component Map）：

| 统一组件 | 微信小程序 | H5 | App WebView |
|---------|----------|-----|------------|
| `<View>` | `<view>` | `<div>` | `<div>` |
| `<Text>` | `<text>` | `<span>` | `<span>` |
| `<Image>` | `<image>` | `<img>` | `<img>` |
| `<Button>` | `<button>` | `<button>` | `<button>` |
| `<ScrollView>` | `<scroll-view>` | `<div>` + overflow | `<div>` + overflow |

### 3.3 样式单位适配

不同端的样式单位不同：

| 端 | 推荐单位 | 设计稿基准 |
|----|---------|-----------|
| 微信小程序 | rpx（750rpx = 屏幕宽度） | 750px |
| H5 | rem / vw | 750px / 375px |
| App WebView | rem / px | 750px |

**统一方案**：源码用 `px`，编译时按端转换。

```js
// Taro 的 pxTransform 配置
{
  designWidth: 750,
  deviceRatio: { 640: 2.34/2, 750: 1, 828: 1.81/2, 375: 2/1 }
}
```

### 3.4 条件编译

跨端框架必须支持 **条件编译**（按 target 生成不同代码）：

```js
// 方式 1：内置 API 判断（运行时）
if (process.env.TARO_ENV === 'weapp') {
  // 微信小程序专属逻辑
} else if (process.env.TARO_ENV === 'h5') {
  // H5 专属逻辑
}

// 方式 2：文件后缀（编译时）
// utils.weapp.js → 仅微信小程序打包
// utils.h5.js → 仅 H5 打包
// utils.js → 默认打包
```

**反直觉点**：跨端条件编译**不是 polyfill**（运行时修补），而是 **产物分支**（编译时生成不同代码）。运行时 polyfill 有性能损耗，产物分支无损耗但增加包大小。

---

## 四、运行时：API 适配与桥接层

跨端框架的第二道难关：**不同端的 API 体系不同**，需要在运行时做适配。

### 4.1 API 标准化层

跨端框架的核心运行时：**API 标准化层**（Bridge Layer）。

```text
业务代码（统一 API）
   ↓
标准化层（Taro.request / wx.request / fetch / JSBridge）
   ↓
平台实现（按 target 选择不同实现）
```

**示例：网络请求的标准化**

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
  // + JSBridge 调用原生能力（如有）
```

### 4.2 JS 引擎差异

不同端的 JS 引擎对 ES 新特性的支持不同：

| 引擎 | 版本 | 兼容性 |
|------|------|--------|
| V8（微信/H5/Android） | 8.x+ | 支持 ES2020 |
| JSCore（iOS WebView） | iOS 14+ 引擎升级 | iOS 14+ 支持大部分 ES2020 |
| Hermes（React Native） | 0.7+ | 字节码预编译，启动快 |

**反直觉点**：JSCore 在 iOS 14 之前不支持 JIT 编译（解释执行），导致 JS 执行速度比 V8 慢 2-3 倍。**App WebView 在 iOS 13 及以下的 JS 性能是 H5（Chrome V8）的 1/3**。这是为什么老版本 iOS WebView 卡顿严重。

### 4.3 WebView 桥接（JSBridge）

App WebView 与原生的通信通过 **JSBridge**：

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

**JSBridge 的实现原理：**
- **iOS**：`WKWebView` 的 `WKScriptMessageHandler`（推荐）/ `WKScriptMessage` 注入
- **Android**：`addJavascriptInterface()` / `evaluateJavascript()` / `shouldOverrideUrlLoading()` 拦截 scheme

**JSBridge 的性能瓶颈**（反直觉点 3）：
- **小数据量（< 1KB）**：JSBridge 很快（< 1ms）
- **中数据量（1-100KB）**：JSBridge 性能急剧下降（JSON 序列化 + 跨语言调用 + 反序列化）
- **大数据量（> 100KB）**：JSBridge 性能断崖式下跌（> 100ms），**这是 App WebView 跨域性能瓶颈的根本原因**

**实战优化**：
```js
// ❌ 大数据量 JSBridge 调用（卡顿）
window.webkit.messageHandlers.nativeBridge.postMessage({
  action: 'setItems',
  data: { items: 10000 个商品数据 }  // 1000KB+
})

// ✅ 分批 JSBridge 调用（流畅）
const chunks = chunkArray(items, 100)
chunks.forEach(chunk => {
  window.webkit.messageHandlers.nativeBridge.postMessage({
    action: 'appendItems',
    data: { items: chunk }
  })
})
```

---

## 五、沙箱与隔离（核心安全机制）

跨端框架必须解决 **多端隔离** 问题：每个端都有自己的"沙箱"机制。

### 5.1 小程序双线程 = 内置沙箱

- 逻辑层（JS）**无法直接访问** 渲染层 DOM
- 渲染层**只接收** 逻辑层通过 `setData` 推送的数据
- 第三方 JS 代码无法访问 `wx.*` API 的内部实现

### 5.2 H5 单线程 = 同源策略

- 同源策略（Same-Origin Policy）限制跨域访问
- iframe + postMessage 实现跨窗口通信
- Web Worker 提供子线程（但无 DOM 访问）

### 5.3 App WebView = JSBridge 双向校验

**核心问题**：WebView 是"半沙箱" —— JS 能调用原生能力，但缺乏访问控制。

**反直觉点**：WebView 默认没有任何权限隔离，第三方 WebView 代码可以调用所有注入的 JSBridge 方法 → **App WebView 的 XSS 风险比 Web H5 更高**（因为有 JSBridge 这个"超级 API"）。

**安全防护**：
1. **白名单 URL Scheme**：拦截非业务 URL
2. **JSBridge 方法白名单**：只暴露必要的 API
3. **输入校验**：所有 JSBridge 入参做合法性校验
4. **域名校验**：限制 WebView 加载的 URL 域名

```js
// Android WebView 安全配置示例
webView.settings.javaScriptEnabled = true
webView.settings.allowFileAccess = false  // 禁止 file:// 访问
webView.settings.allowContentAccess = false
webView.addJavascriptInterface(bridge, "NativeBridge")

// JSBridge 方法白名单
const ALLOWED_METHODS = ['getUserInfo', 'openCamera', 'closePage']
function nativeBridge(method, params) {
  if (!ALLOWED_METHODS.includes(method)) {
    throw new Error('Method not allowed: ' + method)
  }
  // 调用原生实现
}
```

---

## 六、5+ 个反直觉点（含 ❌/✅ 对照）

### 反直觉 1：小程序没有 BOM/DOM

❌ **错误认知**：以为小程序是"阉割版 Web"，可以直接用 `document.querySelector`。

```js
// 小程序里
document.querySelector('#app')  // ❌ 报错：document is not defined
window.location.href = '/next'  // ❌ 报错：location is not defined
```

✅ **真相**：小程序运行在 V8 引擎里，但**没有 BOM/DOM 对象**。所有 DOM 操作通过框架封装（如 `Taro.createSelectorQuery()`）。

```js
// 正确方式
Taro.createSelectorQuery()
  .select('#app')
  .boundingClientRect()
  .exec()
```

### 反直觉 2：setData 不是同步的

❌ **错误认知**：以为 `setData` 后立刻能读到新值。

```js
// ❌ 错误用法
this.setData({ count: 1 })
console.log(this.data.count)  // 打印旧值（异步）
```

✅ **真相**：`setData` 通过 JSBridge 推送到渲染层（5-50ms 延迟）。需要立即使用新值，必须用局部变量：

```js
// ✅ 正确用法
const newCount = this.data.count + 1
this.setData({ count: newCount })
console.log(newCount)  // 直接用新值
```

**频繁 setData 触发渲染线程排队**：
- 1ms 内连续调用 100 次 `setData` → 渲染层合并为 1 次渲染（V8 内部 batching）
- 但每次 `setData` 的数据都会被 **JSON 序列化** → 频繁调用有性能损耗
- 最佳实践：**合并 setData**（一次调用设置多个字段）

### 反直觉 3：JSBridge 跨域性能瓶颈在大数据量

❌ **错误认知**：以为 JSBridge 性能瓶颈在 JS 引擎。

✅ **真相**：JSBridge 性能瓶颈在 **JSON 序列化 + 跨语言边界调用**。> 100KB 数据传输，序列化耗时是传输耗时的 10 倍。

```js
// ❌ 大数据 JSBridge（1000 个商品）
window.webkit.messageHandlers.bridge.postMessage({
  action: 'syncProducts',
  data: products  // 假设 1000 个商品 × 500 字节 = 500KB
})
// 耗时 200ms+，UI 卡顿

// ✅ 分批传输
const batches = chunk(products, 50)
batches.forEach((batch, i) => {
  setTimeout(() => {
    window.webkit.messageHandlers.bridge.postMessage({
      action: 'syncProducts',
      batch: i,
      data: batch
    })
  }, i * 16)  // 60fps 节流
})
```

### 反直觉 4：H5 的 IndexedDB 在小程序里没有

❌ **错误认知**：以为 IndexedDB 是 Web 标准，小程序也能用。

✅ **真相**：微信小程序没有 IndexedDB，必须用 `wx.setStorage` / `wx.setStorageSync`（10MB 上限）。

```js
// H5
const req = indexedDB.open('myDB', 1)
req.onsuccess = (e) => { /* ... */ }

// 小程序（必须用 wx.storage）
wx.setStorage({
  key: 'userInfo',
  data: { name: 'ming' }
})

// 跨端兼容写法（Taro 标准化层）
Taro.setStorage({ key: 'userInfo', data: { name: 'ming' } })
// Taro 编译时根据 target 自动选择 wx.setStorage / localStorage
```

### 反直觉 5：跨端条件编译不是 polyfill

❌ **错误认知**：以为条件编译是"运行时 polyfill"（运行时判断端类型再调用不同 API）。

```js
// ❌ "polyfill"式条件编译（运行时判断）
if (typeof wx !== 'undefined' && wx.request) {
  wx.request({ ... })
} else {
  fetch(url, ...)
}
```

✅ **真相**：跨端条件编译是 **产物分支**（编译时生成不同代码）。运行时判断有性能损耗，且包大小膨胀。

```js
// ✅ 真正的跨端条件编译（编译时分支）
// utils.weapp.js → 只在编译到微信小程序时打包
// utils.h5.js → 只在编译到 H5 时打包
import request from './utils'  // Taro 自动选 utils.weapp.js 或 utils.h5.js
```

### 反直觉 6（加分）：App WebView 的 JS 引擎选择不可控

❌ **错误认知**：以为 App 可以强制使用 V8。

✅ **真相**：App WebView 的 JS 引擎由**操作系统决定**（iOS 系统决定 JSCore，Android 系统决定 V8 版本），App 端无法强制指定。**性能调优必须考虑最弱引擎**（iOS 13 的 JSCore）。

---

## 七、三大平台核心差异速查表

| 维度 | 微信小程序 | H5 | App WebView |
|------|----------|-----|------------|
| **线程** | 双线程（逻辑层 + 渲染层） | 单线程 + 异步 | 单线程 |
| **JS 引擎** | V8（微信定制） | V8（浏览器） | JSCore（iOS）/ V8（Android） |
| **真实 DOM** | ❌ 无 | ✅ 有 | ✅ 有 |
| **BOM** | ❌ 无 | ✅ 有 | ✅ 有 |
| **API 风格** | `wx.*` 异步回调 | Web 标准 | Web + JSBridge |
| **路由** | `wx.navigateTo`（10 层限制） | History API | History + JSBridge |
| **存储上限** | 10MB | LocalStorage 5MB / IndexedDB 无 | LocalStorage 5MB |
| **包大小** | 主包 2MB / 总包 20MB | 无限制 | 无限制（WebView 加载） |
| **离线能力** | 内置 | Service Worker | 原生缓存 + WebView 缓存 |
| **启动时间** | 1-2s（首次） | 2-5s（首次） | 1-3s |
| **调试工具** | 微信开发者工具 | Chrome DevTools | Chrome DevTools（远程调试）|
| **更新方式** | 审核后发布 | 服务端部署 | 服务端部署 + App 审核 |

---

## 八、实战案例：跨端方案剖析

### 8.1 美团：原生 + H5 + 小程序 三端混合

美团的跨端策略是 **按业务场景分端**：
- **核心交易链路**（外卖下单、支付）→ 原生（极致性能）
- **活动页、营销页** → H5（快速迭代 + 服务端配置）
- **工具类入口**（会员、签到）→ 小程序（微信生态流量）

**技术架构**：
```
┌──────────┐  ┌──────────┐  ┌──────────┐
│ 原生 App  │  │  H5 页    │  │ 小程序    │
└────┬─────┘  └────┬─────┘  └────┬─────┘
     │             │             │
     └─────────────┼─────────────┘
                   ▼
            ┌──────────────┐
            │ 统一 API 网关  │ (BFF 层)
            └──────┬───────┘
                   ▼
            ┌──────────────┐
            │ 微服务后端    │
            └──────────────┘
```

**关键决策**：每端独立开发，**通过 API 网关统一后端**，避免"为某一端妥协架构"。

### 8.2 京东：Taro + 自研 mp 框架

京东早期用 Taro 1.x 跨端，后期自研基于 Taro 的 mp 框架：
- 业务代码 100% 用 React JSX
- Taro 编译到 5 端（微信 / 支付宝 / 抖音 / H5 / RN）
- 自研 JS 运行时（避免 Taro 升级带来的 breaking change）

### 8.3 微信读书：Taro + 自研跨端组件库

微信读书的跨端方案：
- 业务层：Taro 4 + React 18
- 组件层：自研 `@weread/ui` 跨端组件库（统一设计语言）
- 编译产物：H5 + 微信小程序 + App WebView 三端

**踩坑教训**：早期直接用 Taro 官方组件库，发现样式不统一（每个端都要 override），后期自研组件库后样式一致性提升 80%。

---

## 九、选型 vs 设计：与 mini-program / mobile-tech-stack 的关系

本文是 **设计层视角**（如何从零设计跨端框架），与同模块的两篇文章形成完整闭环：

| 文章 | 视角 | 重点 |
|------|------|------|
| [mobile-tech-stack](../mobile-tech-stack/README.md) | 选型视角 | 原生 vs Flutter vs RN vs H5 vs 小程序 决策矩阵 |
| [mini-program](../mini-program/README.md) | 使用视角 | Taro 4 / Uni-app x 跨端开发实战 |
| **本文（cross-platform-framework-design）** | 设计视角 | 编译时 AST 转换 + 运行时适配层 架构原理 |

**学习路径建议**：
1. **选型阶段**：读 mobile-tech-stack → 决定用哪条跨端路线
2. **使用阶段**：读 mini-program → 学习 Taro 实战
3. **设计阶段**：读本文 → 理解框架底层原理（架构师视角）

---

## 十、设计跨端框架的 7 个核心问题

当老板让你"从零设计一个跨端框架"，按以下 7 个问题展开：

### Q1：支持哪些端？

- 决策树：用户量分布 → DAU 高的端优先支持
- 主流组合：微信小程序 + H5（90% 业务场景）

### Q2：用什么 DSL 作为统一源码？

- React JSX（团队熟悉度高）
- Vue SFC（Vue 团队首选）
- 自研 DSL（学习成本高，不推荐）

### Q3：AST 转换用什么工具链？

- Babel（JS/JSX 首选）
- PostCSS（样式处理）
- SWC（Rust 实现，性能优于 Babel）

### Q4：组件映射表怎么设计？

- 优先映射到 W3C 标准（如 `<div>` 而不是 `<view>`）
- 保留扩展组件（如 `<Map>`、`<Canvas>`）作为平台特定 API

### Q5：API 标准化层如何实现？

- 接口统一 + 实现差异
- 异步风格：Promise 化（避免回调地狱）
- 错误处理：统一 error code

### Q6：JSBridge 如何设计？

- 方法白名单（安全）
- 数据压缩（性能）
- 异步回调（Promise 化）

### Q7：调试体验怎么保障？

- 源码映射（SourceMap）
- 多端模拟器
- 远程调试（Chrome DevTools for WebView）

---

## 十一、性能与坑点速查

### 11.1 性能坑

| 坑点 | 原因 | 解决方案 |
|------|------|---------|
| `setData` 大数据卡顿 | 跨线程序列化 | 分批 setData / 用 `wx.setStorage` 中转 |
| JSBridge 大数据卡顿 | JSON 序列化 | 分批传输 / 用 shared memory |
| iOS 13 WebView 慢 | JSCore 无 JIT | 减少 JS 计算 / 用 CSS 动画 |
| 路由数超过 10 层 | 小程序限制 | 重定向代替导航 / 用 wx.reLaunch |

### 11.2 兼容性坑

| 坑点 | 原因 | 解决方案 |
|------|------|---------|
| Android WebView 行为不一 | 厂商魔改 | 用 X5 内核统一 |
| iOS Safari 日期解析 | `new Date('2026-01-01')` 失败 | 用 `new Date('2026/01/01')` |
| 小程序 rpx 单位精度 | 浮点数误差 | 设计稿按 750px 基准 |

### 11.3 调试坑

| 坑点 | 原因 | 解决方案 |
|------|------|---------|
| WebView 远程调试断连 | 系统切换后台 | 用 Chrome DevTools over USB |
| 小程序 vConsole 与真机差异 | 模拟器简化 | 真机自测 |
| SourceMap 不准确 | 多层编译 | 用 `sourcemap-chain` 合并 |

---

## 十二、相关章节

### 12.1 同模块互链

- 使用层视角：[小程序开发](../mini-program/README.md) — Taro / Uni-app 跨端实战
- 选型层视角：[App 技术栈选型](../mobile-tech-stack/README.md) — 原生 vs Flutter vs RN vs H5 vs 小程序 决策矩阵

### 12.2 面试题版

- 高频题版：[跨端框架设计面试题](../../../12.interview/09.front-end/cross-platform-framework-design/README.md) — 30s/90s 面试话术 + 5 反直觉点

### 12.3 餐厅叙事版

- 故事版：[一个厨房，四个门面](../../../13.story/20-multiplatform-architecture.md) — 阿明餐厅的多端架构哲学

---

## 📚 参考来源

1. **微信小程序官方文档** — 双线程架构（https://developers.weixin.qq.com/miniprogram/dev/framework/quickstart/framework.html）
2. **Taro 4 官方文档** — AST 转换原理（https://taro-docs.jd.com/）
3. **WKWebView 官方文档** — JSBridge 实现（Apple Developer）
4. **美团技术博客** — 跨端混合开发实践（2024）
5. **京东技术博客** — Taro + 自研 mp 框架演进（2025）
6. **微信读书技术博客** — 跨端组件库设计（2025）

---

← [返回: 08 跨端](../README.md)
