<!--module:
  parent: front-end/state-management
  slug: front-end/state-management/large-project-design
  type: article
  category: 主模块子文章
  summary: 大型前端项目状态管理的 7 大工程维度：store 拆分与模块化、四级状态分层治理、服务端/客户端状态协同、多标签页同步、SSR 水合注水、微前端共享状态、存量项目渐进迁移。
  depth: ⭐⭐⭐⭐
  tags: [状态管理, store 拆分, BroadcastChannel, SSR 水合, 微前端状态共享]
  status: active
-->

# 大型前端项目状态管理的工程设计

> 一句话定位：**选型只是起点 —— 大型项目真正的难题是 store 拆分、分层治理、多标签页同步、SSR 水合与跨应用共享这些工程维度。**

[父文](../README.md)解决了"用什么库"（Zustand / Redux Toolkit / Pinia / TanStack Query 选型对比 + 决策树），本文只回答"库选好了，几十人团队、上百页面、多应用共存时怎么组织状态"。7 个维度全部是大型项目特有、单页 Demo 里永远不会遇到的问题。

---

## 一、Store 拆分与模块化

### 1.1 问题场景

单一 store 的演进路径几乎总是同一个剧本：

```text
项目初期：1 个 store，50 行，清爽
    ↓ 半年后
中期：1 个 store，3000 行，所有 domain 混在一起
    ↓ 一年后
后期：改一个字段全组 review，任何 set() 都可能触发全站重渲染，
     新人不敢删"看起来没人用"的状态（其实有 3 处在用）
```

臃肿的三宗罪：**合并冲突高发**（所有人改同一文件）、**重渲染范围失控**（订阅粒度太粗）、**心智负担**（不知道某个状态归谁管）。

### 1.2 拆分策略：按领域（domain slice）vs 按页面

| 维度 | 按领域拆分（推荐） | 按页面拆分 |
|------|------------------|-----------|
| 切分依据 | 业务域：user / cart / order / settings | 路由：home / detail / checkout |
| 状态复用 | 天然复用（cart slice 被 5 个页面共享） | 跨页面共享状态无处安放，最终又回退到"全局" |
| 生命周期 | 与页面解耦，可独立持久化 | 页面卸载时状态归属模糊 |
| 适用 | 中大型项目默认选择 | 仅适合页面间零共享的独立工具型应用 |

> **判定原则**：状态跟着**数据的属主**走，不跟着**展示位置**走。"购物车"属于 cart 域，不管它出现在首页还是结算页。

### 1.3 三种库的模块化组织

**Redux Toolkit：slice + reducer 组合**

```typescript
// store/index.ts
import { combineSlices, configureStore } from '@reduxjs/toolkit'
import { userSlice } from './slices/userSlice'
import { cartSlice } from './slices/cartSlice'
import { api } from './api' // RTK Query

// combineSlices 支持运行时动态注入 slice（代码分割场景）
const rootReducer = combineSlices(userSlice, cartSlice, api.reducer)

export const store = configureStore({
  reducer: rootReducer,
  middleware: (getDefault) => getDefault().concat(api.middleware),
})
export type RootState = ReturnType<typeof store.getState>
```

**Zustand：多 store + slices pattern**

```typescript
// stores/userStore.ts —— 一个 domain 一个文件一个 store
import { create } from 'zustand'

interface UserState {
  profile: UserProfile | null
  setStatus: (s: Status) => void
  fetchProfile: () => Promise<void>
}

export const useUserStore = create<UserState>()((set) => ({
  profile: null,
  setStatus: (status) =>
    set((state) => ({ profile: state.profile ? { ...state.profile, status } : null })),
  fetchProfile: async () => {
    const profile = await api.getProfile()
    set({ profile })
  },
}))

// 大型单 store 也可用官方 slices pattern：每个 slice 是
// StateCreator，最终 create((...a) => ({ ...createUserSlice(...a), ...createCartSlice(...a) }))
```

**Pinia：天然多 store**

```typescript
// stores/cart.ts —— defineStore 的 id 就是模块边界
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const total = computed(() => items.value.reduce((s, i) => s + i.price, 0))
  // store 之间直接 import 使用：const user = useUserStore()
  return { items, total }
})
```

### 1.4 store 间依赖的处理原则

- **单向依赖**：允许 cart store 读取 user store（下单要校验登录态），禁止反向；出现环 = 拆分边界错了，把共用部分抽成第三个 store。
- **事件解耦**：跨 store 的"通知型"联动（登出 → 清空购物车）不要 import 对方，走事件总线（见 [发布-订阅模式](../pub-sub-pattern/README.md)），保持 store 可独立测试。
- **派生不复制**：B store 需要 A 的数据时，用 selector / computed 现取，**禁止**把 A 的字段拷贝进 B（两份数据必然漂移）。

> ❌ **反模式**：一个 `appStore` 装下所有状态，用命名前缀（`user_xxx` / `cart_xxx`）假装模块化 —— 订阅粒度和文件冲突问题一个都没解决。

---

## 二、状态分层与边界治理

### 2.1 四级状态归属判定

| 层级 | 归属 | 例子 | 放错层的代价 |
|------|------|------|-------------|
| **全局** | 跨页面、跨领域的会话级状态 | 登录用户、主题、权限点 | 塞太多 → 任何变更全站重渲染 |
| **领域** | 单一业务域内共享 | 购物车、订单列表筛选条件 | 提到全局 → 领域边界被打穿，团队协作冲突 |
| **页面** | 仅当前路由内共享 | 列表页的选中行、tab 索引 | 提到全局 → 路由切换后残留脏状态 |
| **组件** | 单组件内部 | 弹窗开关、输入框值、hover | 提到 store → 状态总量爆炸，review 成本剧增 |

**判定口诀**：状态默认放在**能覆盖所有消费者的最低层级**，只有出现真实的跨层共享需求才上提。"以后可能用到"不是上提理由 —— 上提容易下沉难。

### 2.2 坚决不进 store 的三类状态

| 类型 | 正确归属 | 原因 |
|------|---------|------|
| **URL 可表达的** | 路由 query / params（筛选、分页、tab） | URL 天然可分享、可回退、刷新不丢；进 store 就失去了这三点 |
| **服务端持有的** | TanStack Query / SWR 缓存 | store 里再存一份 = 手动同步 = 必然过期（见 §三） |
| **可派生的** | selector / computed | 冗余存储是不一致的根源（父文反模式清单同款，大型项目要靠机制拦截而非自觉） |

### 2.3 治理机制：lint 约束 + code review 清单

大型项目不能靠人自觉，要把边界固化成工具约束：

```jsonc
// ESLint 边界规则示例（eslint-plugin-boundaries / no-restricted-imports）
{
  "no-restricted-imports": ["error", {
    "patterns": [{
      // feature 目录禁止直接 import 其他 feature 的 store 内部实现
      "group": ["@/features/*/stores/internal/**"],
      "message": "跨领域访问请走该 domain 的公开出口 index.ts"
    }]
  }]
}
```

**code review 五问清单**（状态相关 PR 必查）：

1. 这个状态能否用 URL / 派生 / 服务端缓存替代？
2. 它放在最低可行层级了吗？
3. 谁有权修改它？（写入点 > 2 处就要收敛为 action）
4. 订阅粒度对吗？（会不会一个字段变更触发无关组件重渲染）
5. 路由切换 / 登出时它该被重置吗？谁负责重置？

> ❌ **反模式**：用 store 当"跨组件传参通道" —— A 组件写、B 组件读完就丢的一次性数据，走 props / context / 事件即可，进 store 只会制造生命周期问题。

---

## 三、服务端状态与客户端状态协同

### 3.1 问题场景

服务端状态（API 数据）进了全局 store 之后，团队就要手写三件事：**缓存失效、竞态处理、乐观更新回滚** —— 这三件事正是 TanStack Query / SWR 的核心价值（库对比见[父文 §TanStack Query](../README.md)）。大型项目的正确形态是：**Query 缓存管服务端状态，store 只管纯客户端状态，两者之间划清边界**。

### 3.2 边界划分规则

| 数据 | 归属 | 判定依据 |
|------|------|---------|
| 列表 / 详情 / 聚合报表 | Query 缓存 | 真相在服务端，客户端只是快照 |
| 当前登录用户身份 | store | 会话级客户端状态（获取动作可用 Query，落地在 store） |
| "哪些行被选中" | store 或 URL | 纯客户端交互态 |
| 购物车条目 | Query（服务端购物车）/ store（本地购物车） | 看购物车的持久层在哪 |

**禁止双写**：同一份 API 数据既在 Query 缓存又在 store 里存一份，是最常见的协同事故源。需要基于服务端数据做交互态时，用 queryKey 关联而不是复制数据。

### 3.3 乐观更新与回滚（TanStack Query v5）

```typescript
const mutation = useMutation({
  mutationFn: (todo: Todo) => api.updateTodo(todo),
  onMutate: async (newTodo) => {
    // 1. 取消同 key 的在途请求，防止回来覆盖乐观值
    await queryClient.cancelQueries({ queryKey: ['todos', newTodo.id] })
    // 2. 快照旧值用于回滚
    const previous = queryClient.getQueryData(['todos', newTodo.id])
    // 3. 乐观写入
    queryClient.setQueryData(['todos', newTodo.id], newTodo)
    return { previous }
  },
  onError: (_err, newTodo, context) => {
    // 4. 失败回滚到快照
    queryClient.setQueryData(['todos', newTodo.id], context?.previous)
  },
  onSettled: () => {
    // 5. 无论成败都重新同步服务端真相
    queryClient.invalidateQueries({ queryKey: ['todos'] })
  },
})
```

### 3.4 失效驱动 vs 推送驱动

| 策略 | 机制 | 适用 | 代价 |
|------|------|------|------|
| **失效驱动（pull）** | mutation 后 `invalidateQueries`，或 staleTime 到期后台 refetch | 绝大多数业务（默认选择） | 有秒级延迟窗口 |
| **推送驱动（push）** | WebSocket / SSE 收到事件 → `setQueryData` 或 `invalidateQueries` | 实时性硬要求：行情、协作编辑、IM | 需要维护连接、断线补偿、事件与 queryKey 的映射 |

两者可以叠加：推送只传"什么变了"（事件体尽量小），客户端收到后走 invalidate 拉全量 —— 比推送完整数据更不容易产生状态漂移。

> ❌ **反模式**：把 WebSocket 推来的数据直接 `setQueryData` 写满整个列表，却不处理乱序 / 丢包 —— 推送通道必须假设"会丢消息"，兜底靠定时或聚焦时的 invalidate。

---

## 四、多标签页 / 多窗口状态同步

### 4.1 问题场景

用户在标签页 A 登出，标签页 B 还显示已登录；在 A 加购物车，B 的角标不动。浏览器每个标签页是独立的 JS 运行环境，store 天然不共享 —— 大型项目必须显式处理跨标签页一致性。

### 4.2 三方案对比

| 方案 | 机制 | 适用场景 | 兼容性 / 复杂度 |
|------|------|---------|----------------|
| **`storage` 事件** | 一个标签页写 localStorage，**其他同源标签页**收到 `window.addEventListener('storage', ...)`（写入方自身不触发） | 低频状态同步（登录态、主题），且状态本来就要持久化 | 全平台可用；零额外基础设施，复杂度最低 |
| **BroadcastChannel** | 同源 browsing context 之间的命名消息通道，`postMessage` 走结构化克隆 | 通用跨标签页通信首选（MDN Baseline：广泛可用，2022 年 3 月起跨浏览器支持） | 不落盘、纯内存消息；API 简单 |
| **SharedWorker** | 多个标签页连接同一个 worker，由 worker 持有共享状态 | 需要"单一真相源 + 计算共享"（多页签行情、共享一条 WebSocket） | MDN Baseline 为 2026 年新近可用（Safari 支持较晚），老环境需降级；复杂度最高 |

**选型口诀**：状态本来就在 localStorage → storage 事件够用；纯通知 / 增量同步 → BroadcastChannel；要在多页签间共享连接或有中心计算 → SharedWorker。

### 4.3 BroadcastChannel 同步 store（Zustand 示例）

```typescript
// syncTabs.ts —— 通用跨标签页同步中间件思路
const channel = new BroadcastChannel('app-state')

export const useCartStore = create<CartState>()((set) => ({
  items: [],
  addItem: (item: CartItem) => {
    set((s) => ({ items: [...s.items, item] }))
    // 广播的是"意图/增量"，不是整个 store 快照
    channel.postMessage({ type: 'cart/add', payload: item })
  },
}))

channel.addEventListener('message', (e) => {
  const msg = e.data as { type: string; payload: CartItem }
  if (msg.type === 'cart/add') {
    // 收到远端增量后本地重放，避免全量覆盖丢失本地未同步变更
    useCartStore.setState((s) => ({ items: [...s.items, msg.payload] }))
  }
})
```

### 4.4 两个经典场景

- **登录态跨标签页同步**：token 存 localStorage，登出时既清 storage 又 `channel.postMessage({ type: 'logout' })`；各标签页收到后清 store、跳登录页。只用 storage 事件也可（登出即 removeItem，其他页监听到 key 消失）。
- **购物车合并**：用户未登录加购（本地 store）→ 另一标签页登录成功 → 登录事件广播回来 → 本地购物车与服务端购物车做**合并写入**（同 SKU 数量相加，冲突以服务端为准 + 提示用户），合并完成前不发下单请求。

> ❌ **反模式**：用轮询 localStorage 代替事件监听 —— 既费性能又有延迟；`storage` / BroadcastChannel 都是事件驱动的，没有理由轮询。

---

## 五、SSR / SSG 水合与状态注水

### 5.1 问题场景

SSR 时服务端已经请求过数据并渲染了 HTML；如果客户端不复用这份数据，hydration 后会再请求一次 —— 页面闪烁（内容 → loading → 内容）+ 双倍请求。**注水（hydration）= 把服务端取到的状态序列化进 HTML，客户端启动时反序列化进缓存**。

### 5.2 TanStack Query 的 dehydrate / hydrate（v5 官方通道）

```typescript
// 服务端（Next.js pages router 示例；App Router 见官方 Advanced SSR 指南）
import { dehydrate, HydrationBoundary, QueryClient } from '@tanstack/react-query'

export async function getServerSideProps() {
  const queryClient = new QueryClient() // 每请求一个实例，防止跨用户串数据
  await queryClient.prefetchQuery({ queryKey: ['posts'], queryFn: getPosts })
  return { props: { dehydratedState: dehydrate(queryClient) } }
}

export default function PostsRoute({ dehydratedState }) {
  return (
    <HydrationBoundary state={dehydratedState}>
      <Posts /> {/* 内部 useQuery(['posts']) 直接命中缓存，不发请求 */}
    </HydrationBoundary>
  )
}
```

关键细节（均出自官方 SSR 指南）：

- `dehydrate` **默认只序列化成功的查询**，失败的留给客户端重试；要改变行为用 `shouldDehydrateQuery` 选项。
- 服务端 `QueryClient` 必须**每请求新建**（放在 loader / `useState` 里），文件级单例会导致所有用户共享缓存 —— 数据泄露级事故。
- SSR 下 `staleTime` 建议 > 0，否则 hydration 后立即后台 refetch，注水白做。
- 序列化通道只能过 JSON 安全值；自定义 SSR 用 `devalue` / serialize-javascript 转义，直接 `JSON.stringify` 内联进 HTML 有 XSS 风险（官方明确警告）。

### 5.3 hydration mismatch 的典型来源

| 来源 | 例子 | 规避 |
|------|------|------|
| **时间** | `new Date()` 渲染相对时间，服务端与客户端时刻不同 | 服务端时间随注水数据下发；或客户端挂载后再显示相对时间 |
| **随机数** | `Math.random()` 生成 id / 占位图 | 用确定性 id（`useId`）；随机逻辑挪到 `useEffect` / `onMounted` |
| **仅客户端 API** | `window.innerWidth` 参与首屏分支渲染 | 首屏渲染统一走"未知"分支，挂载后二次渲染（双 pass） |
| **浏览器插件篡改 DOM** | 插件注入节点 | 不可控，报 warning 时可容忍，不要为此改架构 |

### 5.4 框架官方注水通道

- **Next.js**：Pages Router 走 `getServerSideProps` 返回值；App Router 里服务端数据随 RSC payload 下发，客户端库（如 TanStack Query）配合 `<HydrationBoundary>` + `useState(() => new QueryClient())` 模式。
- **Nuxt**：`useState(key, init)` 的值自动进 payload 并在客户端恢复（SSR-safe 的官方状态通道）；Pinia 用官方 `@pinia/nuxt` 模块自动处理 store 状态的序列化与恢复。
- **纯客户端状态（Zustand persist 等）**：注意 persist 中间件从 localStorage 恢复是异步的，SSR 场景需 `skipHydration` 手动控制，否则服务端渲染与客户端恢复后的首帧不一致。

> ❌ **反模式**：为了消灭 mismatch 把 `suppressHydrationWarning` 到处贴 —— 它是给时间戳这类不可控差异留的逃生门，滥用会掩盖真实 bug。

---

## 六、微前端 / 多应用共享状态

架构全景见[微前端](../../micro-frontend/README.md)，这里只讲**状态共享**这一面。

### 6.1 三方案对比

| 方案 | 机制 | 适用 | 风险 |
|------|------|------|------|
| **qiankun `initGlobalState`** | 主应用初始化全局状态，返回 `MicroAppStateActions`（`onGlobalStateChange` / `setGlobalState` / `offGlobalStateChange`）；子应用从 `mount(props)` 拿到通信方法 | qiankun 体系内的轻量共享（用户信息、主题） | 官方约束：**只能按一级属性 set**，子应用只能改已存在的一级属性；无类型契约、无 devtools |
| **自定义事件总线** | 主应用挂一个 mitt/EventEmitter 到 props 或全局，子应用 on/emit | 跨技术栈（React 子应用 + Vue 子应用）通知型通信 | 无状态存储，事件丢失不可恢复；需自管解绑防泄漏 |
| **共享 store 包（monorepo npm 包）** | 把某个 domain store 抽成框架无关的包（如 Nano Stores），主子应用共同依赖 | 需要真正的共享"状态"而非"通知"，且能控制构建 | 多实例问题（打包两份 = 两个 store）；版本漂移（见下） |

```typescript
// qiankun 主应用
import { initGlobalState, type MicroAppStateActions } from 'qiankun'

const actions: MicroAppStateActions = initGlobalState({ user: null, theme: 'light' })
actions.onGlobalStateChange((state, prev) => console.log(state, prev))
actions.setGlobalState({ theme: 'dark' }) // 只能一级属性浅合并

// 子应用：mount 生命周期里从 props 取同一组方法
export function mount(props) {
  props.onGlobalStateChange((state) => applyTheme(state.theme))
  props.setGlobalState({ theme: 'dark' })
}
```

### 6.2 版本漂移与 schema 兼容治理

共享状态的真正杀手不是通信机制，而是**契约演化**：主应用发布新版把 `user.level` 改成 `user.tier`，某个子应用还在独立发布节奏上读旧字段 —— 线上直接 undefined。

治理手段：

- **契约包独立版本化**：共享状态的 TypeScript 类型 + 运行时校验（zod 等）单独成包，子应用锁定 major 版本。
- **只加不删的演化纪律**：字段废弃走"新增替代字段 → 双写过渡期 → 下个大版本删旧字段"，禁止直接改名。
- **边界状态最小化**：跨应用只共享"会话级、低频、小体积"状态（用户、主题、权限）；业务数据一律走接口各自获取 —— 共享面越小，漂移伤害越小。

> ❌ **反模式**：把整个主应用 store 通过 props 灌给子应用 —— 子应用开始依赖主应用内部结构，微前端"独立开发部署"的收益归零。

---

## 七、存量项目迁移策略

### 7.1 问题场景

"Redux 老项目迁 Zustand / RTK Query"几乎不可能一次切完 —— 几百个 `connect()` / `useSelector` 调用点、业务不能停。唯一可行的是**渐进共存迁移**。

### 7.2 渐进迁移四步法

| 步骤 | 动作 | 关键点 |
|------|------|--------|
| **1. 桥接共存** | 新旧 store 并行，桥接层双向同步过渡状态 | 桥接只覆盖"迁移期双方都要读"的 slice，其余各管各的 |
| **2. 按 slice 逐个搬** | 从**依赖最少、写入点最少**的 slice 开始（通常是 settings/theme 类），最后搬核心域 | 一次 PR 只搬一个 slice，可独立回滚 |
| **3. 双写过渡** | 迁移中的 slice 新旧两边都写，读逐步切到新侧 | 双写期尽量短（一个迭代内），拖长了两侧必然漂移 |
| **4. 拆除旧侧** | 删除旧 slice + 桥接代码，跑全量回归 | 用全局搜索确认旧 action type / selector 零引用再删 |

```typescript
// 桥接示例：旧 Redux store → 新 Zustand store 单向同步（迁移期）
import { store as legacyStore } from '@/legacy/store'
import { useSettingsStore } from '@/stores/settingsStore'

const unsub = legacyStore.subscribe(() => {
  const legacy = legacyStore.getState().settings
  const next = useSettingsStore.getState()
  // 只在真实变化时写入，避免同步风暴
  if (legacy.theme !== next.theme) {
    useSettingsStore.setState({ theme: legacy.theme })
  }
})
// slice 迁移完成后调用 unsub() 并删除本文件
```

### 7.3 迁移中的状态一致性验证

- **快照对比测试**：同一串用户操作分别打到新旧 store，断言最终状态与关键 UI 输出一致（迁移期最高性价比的回归手段）。
- **双读校验（灰度期）**：读新侧渲染的同时，采样对比旧侧值，不一致上报 —— 用线上流量验证迁移正确性，而不是只靠测试环境。
- **DevTools 并排**：迁移期保留 Redux DevTools + 新库 devtools（Zustand 有 devtools 中间件），排查"哪边没同步"类问题。

> ❌ **反模式**：大爆炸式重写（"这个迭代把状态层全部换掉"）—— 状态层是全应用的血管，一次性替换等于让所有业务 PR 与迁移 PR 互相冲突，失败率极高且无法回滚。

---

## 八、七维度速查表

| # | 维度 | 一句话结论 |
|---|------|-----------|
| 1 | store 拆分 | 按领域拆，单向依赖，事件解耦，派生不复制 |
| 2 | 分层治理 | 状态放最低可行层级；URL / 派生 / 服务端数据不进 store；边界靠 lint 和 review 清单固化 |
| 3 | 服务端协同 | Query 缓存管 API 数据，store 管客户端状态，禁止双写；乐观更新必须带回滚 + onSettled 失效 |
| 4 | 多标签页 | storage 事件（持久态）/ BroadcastChannel（通用首选）/ SharedWorker（中心真相源），广播增量不广播全量 |
| 5 | SSR 水合 | dehydrate/hydrate 走框架官方通道；每请求一个 QueryClient；mismatch 三大来源：时间 / 随机 / 仅客户端 API |
| 6 | 微前端 | 共享面最小化（会话级状态）；契约包版本化 + 只加不删 |
| 7 | 存量迁移 | 桥接共存 → 按 slice 搬 → 双写过渡 → 拆除；快照对比 + 灰度双读验证 |

---

## 交叉引用

- [12.interview/09.front-end/large-project-state-management/](../../../../12.interview/09.front-end/large-project-state-management/README.md) — 本文的面试深挖版（高频问法 + 30 秒话术 + 追问链）
- [状态管理（父文）](../README.md) — 库选型对比 / 三大范式 / TanStack Query / 选型决策树（本文不重复）
- [发布-订阅者模式](../pub-sub-pattern/README.md) — 跨 store 事件解耦、跨标签页通信的底层模式
- [微前端](../../micro-frontend/README.md) — qiankun 沙箱与应用通信全景（§六 只覆盖状态共享切面）

---

← [返回: 状态管理](../README.md)
