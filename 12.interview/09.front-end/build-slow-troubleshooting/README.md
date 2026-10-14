<!--question:
  id: 09.front-end-build-slow-troubleshooting
  topic: 09.front-end
  difficulty: ⭐⭐⭐⭐
  frequency: 中高频（高级前端/工程化岗）
  scenario_type: 生产 Bug
  tags: [09.front-end, 构建性能, webpack, vite, 缓存, sourcemap, monorepo]
  status: active
-->

# 前端项目打包越来越慢怎么排查 —— 只会换 esbuild 远远不够

> **一句话定位**：构建慢是**多因叠加**——先分层测量归因（transform / minify / sourcemap / 缓存 / 编排），再对症下药；换打包器只解决「单次编译速度」一个维度。

> **系列定位**：经典前端工程化面试题（高级前端 / 工程化岗中高频）。考察的不是"用什么打包器快"，而是 **构建流水线的分层归因能力** + **诊断工具链的实操经验** + **「越来越慢」与「一直慢」的病因区分**。

---

## 引子：换了 Vite，CI 还是慢得离谱

```text
场景：某中后台项目，3 年演进，webpack 5 + TS + React，800+ 页面模块
（以下为场景设定口径，非实测 benchmark）

恶化曲线：
  本地 dev 冷启动：8 秒（3 年前）→ 90 秒（现在）
  CI 全量构建：    3 分钟（3 年前）→ 22 分钟（现在）

团队第一反应："webpack 老了，换 Vite！"
换完之后：
  ✅ dev 冷启动确实快了（ESM 按需编译 + 依赖预构建）
  ❌ CI 构建只从 22 分钟降到 16 分钟——离预期差得远
```

为什么换了「更快的打包器」CI 还是慢？因为团队从头到尾没做过一次分层测量。事后拆开看，这个项目的构建时间里藏着至少四个独立的病灶：**类型检查跑在构建主线程、sourcemap 用了最重的配置、CI 缓存从来没命中过、monorepo 里改一行全仓重建**——这四个病灶里，只有第一个和「打包器」沾边。

**「换 esbuild / Vite / Rspack」只优化了 transform 这一层的单次速度，而大型项目的构建慢从来不是单因问题。** 这道题的正确打开方式：先建立归因坐标系，再测量，最后才谈手段。

---

## 一、核心原理：构建流水线分层（先建立归因坐标系）

### 1.1 一次构建到底在做什么

把「构建」拆开成可测量的阶段，"慢"才能被定位：

```text
依赖解析(resolve) → 加载(load) → 转换(transform: TS/JSX/CSS/loader 链)
       → 模块图构建 → 优化(tree-shaking / splitChunks)
       → 生成 chunk → 压缩(minify) → sourcemap 生成 → 写盘/上传产物
```

| 层 | 典型耗时占比 | 常见瓶颈 |
|----|------------|---------|
| **resolve** | 小头，但 monorepo 下会放大 | 深路径别名、`resolve.modules` 搜索链过长、symlink |
| **transform** | dev 下通常是大头 | babel / ts-loader 逐文件转译，TS 类型检查混在里面 |
| **优化 + 生成 chunk** | prod 中头 | splitChunks 策略、tree-shaking 分析范围 |
| **minify** | prod 大头之一 | 压缩器选择、chunk 数量（每个 chunk 独立压缩） |
| **sourcemap** | prod 大头之一，常占三成以上 | devtool 配置档位、产物体积 |
| **写盘 / 上传** | CI 里容易被忽略 | 产物体积、上传 sourcemap 到错误监控平台 |

### 1.2 关键区分一：dev 慢 / prod 慢 / CI 慢是三套归因

| 场景 | 关注点 | 典型元凶 |
|------|--------|---------|
| **dev 慢** | 冷启动 + HMR 增量速度 | 依赖预构建反复触发、barrel 文件请求瀑布、类型检查阻塞 |
| **prod 慢** | 全量构建总时长 | minify + sourcemap、splitChunks 过度拆分、持久化缓存失效 |
| **CI 慢** | 端到端流水线时长 | 缓存未命中（每次冷构建）、并行度不足、机器规格、monorepo 全量重建 |

**换打包器直接受益的是 dev 冷启动**（Vite 的 ESM 按需编译天然快）；prod 和 CI 的瓶颈往往根本不在 transform 层——这就是引子里「dev 快了但 CI 没快」的结构性原因。

### 1.3 关键区分二：「越来越慢」≠「一直慢」

题目里的「越来越慢」是**增量恶化**，与「一直慢」的归因完全不同。增量恶化必然存在**随代码量 / 依赖量增长而放大的因素**：

```text
一直慢：      配置问题（sourcemap 档位 / 无缓存 / 类型检查同步）→ 静态病灶
越来越慢：    增长型病灶 → 必须找"什么在随代码量线性/超线性膨胀"
              候选：模块图规模、barrel 文件 re-export 链、
                   类型检查范围、sourcemap 体积、缓存失效频率、
                   monorepo 包数量（无 affected 检测时全量重建）
```

排查「越来越慢」时，除了看当前配置，还要回答一个问题：**三年前同样的配置为什么不慢？**——答案通常在代码组织方式（barrel 文件越积越多、tsconfig include 范围越来越大）而不是构建配置本身。

---

## 二、排查方法论：先测量，再动手

**反模式：不测量就换工具。** 换打包器是手段里代价最大、收益最不可控的一个（生态兼容、loader 重写、行为差异），却常被放在第一步。正确顺序是：**建立基线 → 二分定位 → 归因到层 → 针对层选手段**。

### 2.1 诊断工具链

| 层 | 工具 | 用法要点 |
|---|------|---------|
| webpack 各阶段耗时 | `speed-measure-webpack-plugin` | 包裹 config，输出每个 plugin / loader 耗时，定位 transform 层元凶 |
| webpack 内建 | `webpack --profile --json > stats.json` | 官方口径，拿模块级耗时与依赖图 |
| 产物体积归因 | `webpack-bundle-analyzer` / `rollup-plugin-visualizer` | 区分「构建慢」与「产物大」——两者相关但不同因 |
| Vite | `vite --debug` / `DEBUG=vite:*` | 看依赖预构建（optimizeDeps）是否反复触发——常见 dev 慢元凶 |
| TS 类型检查 | `tsc --noEmit --extendedDiagnostics` | 区分「编译慢」与「类型检查慢」——ts-loader 同步类型检查常是隐形大头 |
| CI | 分阶段计时 + 缓存命中率日志 | 确认是构建本身慢还是缓存没命中 |

```js
// speed-measure-webpack-plugin：一行包裹，看每个 plugin/loader 耗时
const SpeedMeasurePlugin = require('speed-measure-webpack-plugin');
const smp = new SpeedMeasurePlugin();

module.exports = smp.wrap(webpackConfig);
// 输出示例（结构示意）：
//  Total time: 128453ms
//  ForkTsCheckerWebpackPlugin  41230ms   ← 类型检查是大头
//  TerserPlugin                30112ms   ← minify 次之
//  babel-loader                22870ms
```

```bash
# TS 类型检查独立计时（--extendedDiagnostics 输出各阶段耗时）
npx tsc --noEmit --extendedDiagnostics
# 关注：Check time（类型检查）vs Emit time（产出）
# 如果 Check time 巨大 → 病灶在类型系统，不在打包器

# webpack 模块级耗时
npx webpack --profile --json > stats.json
# stats.json 可喂给 webpack-bundle-analyzer 或官方 analyse 页面

# Vite 依赖预构建调试
DEBUG=vite:* npx vite
# 关注 "new dependencies optimized" / "reloading" 日志——反复出现 = 预构建抖动
```

### 2.2 方法论四步

**① 建立基线（可复现）**：固定机器、固定缓存状态（冷/热各测一次）、记录各阶段耗时。没有基线，一切「优化」都无法验证。

**② 二分定位（逐个变量关）**：

```bash
# 变量 1：关 sourcemap
# webpack: devtool: false / vite: build.sourcemap: false
# 若耗时大幅下降 → sourcemap 层是病灶

# 变量 2：关 minify
# webpack: optimization.minimize: false / vite: build.minify: false
# 若耗时大幅下降 → minify 层是病灶（结合 chunk 数量看）

# 变量 3：关类型检查（transpileOnly / 移除 fork-ts-checker）
# 若耗时大幅下降 → 类型检查是病灶（用 tsc --extendedDiagnostics 确认）

# 变量 4：缩小构建范围（只构建一个子模块/子包）
# 若耗时近似线性下降 → 病灶随代码量增长（barrel 文件/模块图膨胀方向）
# 若耗时不降 → 病灶在固定开销（缓存读写、CI 环境、插件初始化）
```

**③ 归因到层**：把 ② 的结果映射回 1.1 的流水线分层表。

**④ 针对层选手段**：见第三节 8 大真凶与第六节手段对照表——**换打包器只是 transform 层的选项之一，且通常是最后才动的选项**。

### 2.3 排查决策树

```text
构建耗时超预期
       │
       ▼
  哪个场景慢？
  ├─ dev 慢 ──→ DEBUG=vite:* 看预构建是否反复触发（真凶 8）
  │             浏览器 Network 看请求瀑布（真凶 1 barrel 文件）
  ├─ prod 慢 ─→ smp 看 plugin 耗时分布
  │             ├─ 类型检查大头 → 真凶 2
  │             ├─ minify/sourcemap 大头 → 真凶 3 / 真凶 6
  │             └─ loader 大头 → 真凶 5
  └─ CI 慢 ───→ 分阶段计时 + 缓存命中日志
                ├─ 构建本身慢 → 回到 prod 分支（热缓存下重测）
                ├─ 缓存不命中 → 真凶 4
                └─ monorepo 全量重建 → 真凶 7
```

---

## 三、根因深挖：8 大真凶（按「越容易被忽略」排序）

### 3.1 barrel 文件（桶文件）滥用

- **症状识别**：dev 冷启动巨慢、浏览器 Network 面板里几百个模块请求；`stats.json` 里模块数量远超页面数量。
- **为什么慢**：`import { Button } from '@/components'` 会触发整个 `index.ts` re-export 链的模块图展开——你只用 1 个组件，构建器却要解析、转换它背后 re-export 的几百个模块。dev 下 Vite 的 ESM 按需编译会变成**请求瀑布爆炸**；webpack 下则是模块图膨胀。项目越老、桶文件越多，恶化越明显——这是「越来越慢」的头号增长型病灶。
- **怎么修**：直接深路径 import（`@/components/Button`）；高频依赖加进 Vite `optimizeDeps.include` 预打包；组件库用 `babel-plugin-import` 类按需引入方案。

### 3.2 TS 类型检查跑在构建主线程

- **症状识别**：`speed-measure-webpack-plugin` 显示 `ForkTsCheckerWebpackPlugin` 或 `ts-loader` 耗时占比异常；`tsc --noEmit --extendedDiagnostics` 的 Check time 很大。
- **为什么慢**：ts-loader 默认**同步做完整类型检查**，每个文件都要等类型系统算完才能继续。类型检查复杂度随类型数量超线性增长——这也是增长型病灶。
- **怎么修**：`ts-loader` 开 `transpileOnly: true` + `fork-ts-checker-webpack-plugin` 把类型检查分离到独立进程异步跑；或走 Vite/esbuild 路线（**只转译不检查类型**）+ CI 里单独跑 `tsc --noEmit` 兜底。

```js
// webpack: 转译与类型检查分离
module.exports = {
  module: {
    rules: [{
      test: /\.tsx?$/,
      loader: 'ts-loader',
      options: { transpileOnly: true },  // 只转译，不同步查类型
      exclude: /node_modules/,
    }],
  },
  plugins: [
    new ForkTsCheckerWebpackPlugin(),    // 类型检查异步独立进程
  ],
};
```

### 3.3 sourcemap 配置不当

- **症状识别**：prod 构建耗时里关掉 devtool 后大幅下降；产物目录里 `.map` 文件比 JS 还大。
- **为什么慢**：`devtool: 'source-map'` 生成完整独立 map 文件，通常占 prod 构建三成以上耗时，且产物巨大（写盘、上传都变慢）。
- **怎么修**：按场景选档位——本地排查用 `eval-cheap-module-source-map`（快）；线上需要排错用 `hidden-source-map`（生成但不在 bundle 里暴露引用，map 只上传到 Sentry 等错误平台）；确实不需要就关。**不要为了提速直接关线上 sourcemap**（见陷阱 3）。

### 3.4 持久化缓存没开 / 频繁失效

- **症状识别**：本地二次构建和冷构建一样慢；CI 每次都是全量时长。
- **为什么慢**：webpack 5 提供 `cache.type: 'filesystem'`，把模块转换结果缓存到磁盘，二次构建跳过大部分 transform。没开 = 每次全量。开了但 `buildDependencies` 配错 = 缓存 key 计算不对，**永远不命中或永远脏读**。CI 上则是缓存目录没上传/路径不对，等于每次冷构建。
- **怎么修**（webpack.js.org 官方机制：`buildDependencies` 列出的文件用 hash 参与缓存失效判定，默认包含 webpack 自身）：

```js
// webpack.config.js
module.exports = {
  cache: {
    type: 'filesystem',              // 磁盘持久化缓存
    buildDependencies: {
      config: [__filename],          // 配置文件变更 → 缓存失效
      // 默认已含 webpack/lib，无需重复声明
    },
  },
};
```

```yaml
# CI 侧：把缓存目录真正持久化（GitHub Actions 示例）
- uses: actions/cache@v4
  with:
    path: |
      node_modules/.cache/webpack    # webpack filesystem cache 默认位置
      ~/.npm
    key: webpack-${{ runner.os }}-${{ hashFiles('**/package-lock.json', 'webpack.config.js') }}
```

### 3.5 loader 链过长 + 作用范围过宽

- **症状识别**：`speed-measure-webpack-plugin` 里某个 loader 耗时异常；`stats.json` 显示 node_modules 里的文件也过了 babel。
- **为什么慢**：babel 处理了 node_modules、没配 `exclude`、postcss 全量跑——每个文件的 transform 成本 = loader 链长度 × 文件数。
- **怎么修**：收窄 `test` / 配 `exclude: /node_modules/`；babel-loader 开 `cacheDirectory: true`；审一遍 loader 链，删掉不再需要的历史遗留 loader。

### 3.6 splitChunks 策略不当

- **症状识别**：产物目录里几百个小 chunk；minify 阶段耗时随 chunk 数线性涨。
- **为什么慢**：**过度拆分**导致 chunk 数量爆炸——每个 chunk 都要独立 minify + 独立生成 sourcemap，固定开销乘以 chunk 数；反过来**完全不拆**则单 chunk 巨大，minify 单文件耗时也会失控，且首屏加载变慢。
- **怎么修**：按 `minSize` / `maxSize` / `cacheGroups` 收敛拆分粒度；改动后用 analyzer 看 chunk 分布是否合理。

### 3.7 monorepo 全量构建（换打包器完全触及不到的维度）

- **症状识别**：monorepo 里改一个包的一个文件，CI 构建时长 ≈ 全仓构建时长。
- **为什么慢**：没有 affected 检测，构建编排层把所有包全量重建。这是**构建编排层**的问题，与用 webpack 还是 esbuild 无关——引子场景里 CI 降不下来的主要病灶就在这层。
- **怎么修**：Turborepo / Nx 的 affected 增量构建 + 任务级缓存 + 远端缓存（团队共享，一人构建全队命中）。Rspack 生态的具体编排特性若不确证，选型时需单独核实。

### 3.8 依赖预构建反复触发（Vite 特有）

- **症状识别**：`DEBUG=vite:*` 日志里反复出现 "new dependencies optimized" 和整页 reload；dev 用着用着突然卡一下全页刷新。
- **为什么慢**：Vite dev 启动时预构建依赖，之后每发现一个**未预构建的新依赖**就要重跑 optimizeDeps 并触发整页 reload——依赖发现是渐进的，于是预构建反复触发。
- **怎么修**：把高频间接依赖显式声明进 `optimizeDeps.include`，一次性预构建完。注意 Vite 8 起底层改用 **Rolldown + Oxc**（不再是 esbuild + Rollup），`optimizeDeps.esbuildOptions` 已 deprecated——升级时按 vite.dev 官方迁移指南处理。

```js
// vite.config.js
export default {
  optimizeDeps: {
    include: ['lodash-es', 'axios', 'dayjs', '@some-ui/icons'],  // 显式声明，避免渐进发现
  },
};
```

---

## 四、❌/✅ 反例对比

### 对比 1：barrel 文件 import

```ts
// ❌ 桶文件：拉进整个 utils 索引的 re-export 链，模块图爆炸
import { formatDate } from '@/utils';

// ✅ 深路径：模块图只含真正用到的文件
import { formatDate } from '@/utils/date';
```

### 对比 2：TS 类型检查位置

```js
// ❌ ts-loader 默认：同步类型检查阻塞 transform 主流程
{ test: /\.tsx?$/, loader: 'ts-loader' }

// ✅ transpileOnly + fork-ts-checker：转译与检查分离，检查异步化
{ test: /\.tsx?$/, loader: 'ts-loader', options: { transpileOnly: true } }
// + plugins: [new ForkTsCheckerWebpackPlugin()]
```

### 对比 3：CI 缓存

```yaml
# ❌ 无缓存：每次 PR 都冷构建，node_modules + webpack cache 全部重来
steps:
  - run: npm ci
  - run: npm run build

# ✅ 依赖缓存 + webpack filesystem cache 持久化
steps:
  - uses: actions/cache@v4
    with:
      path: |
        ~/.npm
        node_modules/.cache/webpack
      key: webpack-${{ runner.os }}-${{ hashFiles('**/package-lock.json') }}
  - run: npm ci
  - run: npm run build
```

---

## 五、常见陷阱

### 陷阱 1：换了 Vite/Rspack 就以为解决了
- **真相**：dev 快 ≠ CI 快 ≠ prod 快，这是三套归因（见 1.2）。Vite 的 dev 优势来自 ESM 按需编译，但 CI 全量构建走的是 Rollup/Rolldown 路径，瓶颈常在 minify / sourcemap / 缓存 / 编排层——引子场景里换完 Vite CI 只降了不到三成，就是因为病灶根本不在 transform 层。

### 陷阱 2：只看构建时间，不看产物体积
- **真相**：构建变快和产物变小是两件事，甚至可能互相冲突——比如关掉 minify 构建立刻变快，但产物膨胀、线上运行时反而变慢。优化前后必须**同时记录构建耗时和产物体积**两条曲线，用 bundle analyzer 确认没有此消彼长。

### 陷阱 3：为了提速直接关线上 sourcemap
- **真相**：关 sourcemap 确实提速，但线上报错从此无法定位到源码。正确姿势是 `hidden-source-map`：照常生成 map 文件但不在 bundle 里暴露 `//# sourceMappingURL` 引用，map 只上传到 Sentry 等错误监控平台——构建成本没省，但产物安全性和排错能力兼得；真正想省成本可评估降低 map 精度档位。

### 陷阱 4：缓存开了但 buildDependencies 配错
- **真相**：`cache.buildDependencies` 参与缓存 key 的 hash 计算。漏配了会被读取的外部配置文件（如 babel.config.js、动态 env 文件）→ 配置改了缓存不失效，**永远脏读**；把每次都变化的文件（如含时间戳的生成物）配进去 → 缓存 key 每次都变，**永远不命中**。缓存开了 ≠ 缓存在工作，要用「二次构建耗时」验证命中率。

### 陷阱 5：把 esbuild/Rolldown 当万能
- **真相**：esbuild 快的代价是能力边界——不支持部分 webpack loader 生态（自定义 loader 要重写）、TS **只转译不做类型检查**（类型安全要靠 CI 单独跑 tsc 兜底）、部分高级优化行为与 webpack 有差异。换打包器前先盘点：自定义 loader/plugin 数量、对 tree-shaking 行为的依赖、生态插件兼容性——这是姊妹题「webpack → Vite 迁移坑」的主题。

---

## 六、解决与验证

### 6.1 分层手段对照表

| 病灶层 | 手段 | 预期收益 | 代价 |
|--------|------|---------|------|
| barrel 文件 | 深路径 import / optimizeDeps.include / 按需引入插件 | dev 冷启动、模块图规模 | 需要改 import 习惯 + ESLint 规则约束 |
| 类型检查 | transpileOnly + fork-ts-checker / CI 单独 tsc | transform 层大头 | 编辑器外错误延迟到 CI 才暴露 |
| sourcemap | 按场景选 devtool 档位 / hidden-source-map | prod 构建三成上下 | 排错流程要接错误监控平台 |
| 缓存 | filesystem cache + buildDependencies + CI cache | 二次构建、CI 冷构建 | 配置不当会脏读/不命中（陷阱 4） |
| loader 链 | exclude 收窄 + cacheDirectory + 删遗留 loader | transform 层 | 需要回归验证产物一致性 |
| splitChunks | 收敛拆分粒度 | minify + sourcemap 层 | 需要重新验证首屏加载性能 |
| monorepo 编排 | Turborepo/Nx affected + 远端缓存 | CI 端到端 | 引入编排层工具的学习成本 |
| 打包器本身 | Vite/Rspack/esbuild（**最后才动**） | transform 层单文件速度 | 生态兼容、迁移成本、行为差异 |

### 6.2 验证闭环：回到基线对比

改完必须回到 2.2 ① 的基线做 before/after 对比，避免"感觉快了"：

```text
| 阶段                | 优化前（基线） | 优化后 | 变化 |
|--------------------|--------------|--------|------|
| dev 冷启动          |              |        |      |
| dev 二次启动（热缓存）|              |        |      |
| prod 构建（冷缓存）  |              |        |      |
| prod 构建（热缓存）  |              |        |      |
| CI 端到端           |              |        |      |
| 产物总体积          |              |        |      |  ← 必须同时记录，防陷阱 2
```

每项优化**单独提交、单独测量**——一次改五个变量，快了你也不知道是谁的功劳，慢了你不知道是谁的锅。

### 6.3 防复发

- **CI 构建耗时门禁**：每次构建记录耗时，超过阈值（如基线 + 20%）告警——把「越来越慢」扼杀在增量阶段。
- **bundle size 预算**：产物体积超预算 CI 标红（size-limit 类工具或 analyzer 脚本化）。
- **定期跑 analyzer**：每月看一次模块数量 / chunk 分布 / 依赖体积趋势，barrel 文件与重复依赖会在曲线上先于体感暴露。
- **ESLint 约束 import 路径**：`no-restricted-imports` 禁止新增桶文件顶层 import。

---

## 七、面试话术（30 秒版 + 90 秒版）

> **30 秒版**：
>
> "构建慢我会先分层归因再动手，不会上来就换打包器——换打包器只解决 transform 一层的单次编译速度。首先区分 dev 慢、prod 慢还是 CI 慢，这是三套归因：dev 看冷启动和依赖预构建，prod 看 minify 和 sourcemap，CI 看缓存命中和构建编排。然后用工具测量：speed-measure-webpack-plugin 看各 plugin/loader 耗时，tsc --extendedDiagnostics 把类型检查单独计时，bundle analyzer 看产物归因。'越来越慢'还要额外找随代码量增长的因素，最常见的是 barrel 文件滥用和类型检查范围膨胀。"

> **90 秒版**：
>
> "我的原则是**先测量后动手**。第一步建基线：固定环境记录 dev 冷启动 / prod 构建 / CI 端到端三组数字。第二步用工具链归因到层：webpack 项目用 speed-measure-webpack-plugin 看每个 plugin 和 loader 的耗时分布，产物侧用 webpack-bundle-analyzer，类型检查用 tsc --noEmit --extendedDiagnostics 单独计时，Vite 项目开 DEBUG=vite:* 看 optimizeDeps 是否反复触发，CI 侧加分阶段计时和缓存命中日志。
>
> 实际项目里最高频的三个真凶：一是 **barrel 文件滥用**——`import { x } from '@/utils'` 把整个 re-export 链拉进模块图，这是'越来越慢'最典型的增长型病灶，修法是深路径 import 加 optimizeDeps.include；二是 **TS 类型检查跑在构建主线程**——ts-loader 默认同步查类型，修法是 transpileOnly 加 fork-ts-checker 异步分离，或者 CI 单独跑 tsc 兜底；三是 **缓存没命中**——webpack 5 filesystem cache 没开、或开了但 buildDependencies 配错导致永远脏读或永远不命中、或 CI 缓存目录没持久化。
>
> 还有一个换打包器完全触及不到的维度：**monorepo 构建编排**。没有 affected 检测时改一个包全仓重建，这要靠 Turborepo/Nx 的任务级缓存和增量构建解决，跟用 webpack 还是 esbuild 无关。我见过的典型失败案例就是团队把希望全押在换 Vite 上，dev 确实快了，但 CI 只降了一小截——因为 CI 的病灶在缓存和编排层。
>
> 最后一定要有验证闭环：每项优化单独提交，回到基线做 before/after 对比，构建耗时和产物体积两条曲线一起看；然后在 CI 加构建耗时门禁和 bundle size 预算，防止再次增量恶化。"

**加分项**：提及 Vite 8 起底层从 esbuild + Rollup 换成 **Rolldown + Oxc** 的演进（说明你跟踪工具链前沿，且理解"打包器也在被分层重构"）；或提及 `no-restricted-imports` ESLint 规则从源头禁止新增桶文件顶层 import（防复发而不只是救火）。

---

## 八、相关章节

### 同栏目兄弟

- [Webpack → Vite/Rspack 迁移坑](../webpack-vite-migration/README.md) — 姊妹题：换工具本身的风险（CJS/ESM 差异、loader 生态、行为差异）——本文说「什么时候不该换」，它说「决定换了要防什么坑」

### 主模块深读

- [Vite 架构与性能配置](../../../05.frontend/04-engineering/vite/README.md) — 依赖预构建 / ESM dev server / Rolldown 演进
- [monorepo 实践](../../../05.frontend/04-engineering/monorepo-practice/README.md) — 增量构建与缓存编排（真凶 7 的展开）
- [前端性能优化](../../../05.frontend/06-performance/optimization/README.md) — 运行时性能（与本文的构建性能是两个维度，陷阱 2 的展开）
- [TypeScript](../../../05.frontend/02-language/typescript/README.md) — tsconfig 的 skipLibCheck / isolatedModules 对构建的影响
- [前端工程化总览](../../../05.frontend/04-engineering/README.md) — 工程化知识体系入口

---

> 📅 2026-10-14 · 咬文嚼字 · 构建性能排查 · ⭐⭐⭐⭐（中高频面试 + 实战必会）

← [返回: 咬文嚼字 · build-slow-troubleshooting](../README.md)
