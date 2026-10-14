<!--module:
  parent: front-end
  slug: front-end/vite
  type: article
  category: 主模块子文章
  summary: Vite 构建工具（Vite 8 起底层为 Rolldown + Oxc，Vite 7 及以前为 esbuild + Rollup）
  depth: ⭐⭐⭐
  status: active
-->

# Vite 构建工具

> 一句话定位：**Vite —— 2026 年前端构建的事实标准，ESM 原生的极速体验**

Vite（法语"快"）由 Vue.js 作者尤雨溪于 2020 年发布，到 2026 年已是新项目构建工具的主流选择（State of JS 调查中 Vite 的 retention/使用率长期领先 Webpack，具体分值随年度调查浮动，见 [State of JS](https://stateofjs.com/)）。

---

## 为什么 Vite 能替代 Webpack
### Webpack 的痛点
- ❌ 启动慢：打包整个应用后才能启动 dev server（大项目 30s+）
- ❌ HMR 慢：修改一个文件，重新打包整条链路
- ❌ 配置复杂：plugin / loader 学习曲线陡

### Vite 的核心突破

```mermaid
graph LR
  A[浏览器原生 ESM] --> B[Dev Server<br/>无需打包]
  B --> C[按需编译<br/>只编译访问到的模块]
  C --> D[极速启动<br/>毫秒级]
  D --> E[HMR<br/>仅更新变更模块]
  style A fill:#e3f2fd
  style D fill:#e8f5e9
```

| 阶段 | Webpack | Vite |
|------|---------|------|
| **Dev 启动** | 打包全部模块（30s+） | **毫秒级**（无打包） |
| **Dev HMR** | 重编译相关模块（1-3s） | **<50ms**（ESM 热更） |
| **Prod 构建** | 自身打包 | 统一 bundler（Vite 7 = Rollup；**Vite 8+ = Rolldown**） |

> **性能基准**（来源：[Vite 官方文档](https://vitejs.dev/guide/why.html) + [State of JS 2023](https://2023.stateofjs.com/)；数据采集于 Vite 5 时代，Vite 8 换用 Rolldown/Oxc 后构建性能进一步提升，具体数字以对应版本官方 benchmark 为准）：
> - 中型项目（~500 模块）：Vite 冷启动 ~300ms vs Webpack ~30s（**100x 提升**）
> - HMR 更新：Vite <50ms vs Webpack 1-3s（**20-60x 提升**）
> - 生产构建：Vite 比 Webpack 快 ~30%，产物体积更小 ~10%
> - **LCP 影响**：代码分割 + 资源内联优化后，典型电商首页 LCP 从 3.2s 降至 1.8s（[web.dev 案例](https://web.dev/vite-lcp/)）

---

## Vite 核心架构

> ⚠️ **版本分层口径**（2026-10 核实，vite v8.3.4）：Vite 的底层工具链在 v8 发生重大切换——官方《Migration from v7》原文：**"Vite 8 uses Rolldown and Oxc based tools instead of esbuild and Rollup"**。阅读下文时请区分版本：
>
> | | Vite 7 及以前 | Vite 8+ |
> |---|---|---|
> | 依赖预构建 | esbuild | **Rolldown**（`optimizeDeps.esbuildOptions` 已 deprecated，自动转换为 `optimizeDeps.rolldownOptions`，未来移除） |
> | JS 转译 | esbuild | **Oxc**（顶层 `esbuild` 配置项已 deprecated，自动转换为 `oxc`） |
> | 生产打包 | Rollup | **Rolldown**（`build.rollupOptions` 更名为 `build.rolldownOptions`） |
> | JS 压缩 | esbuild（默认）/ terser | **Oxc Minifier**（`build.minify` 默认 `'oxc'`；`'esbuild'` 已 deprecated） |
> | CSS 压缩 | esbuild | **Lightning CSS**（默认） |
>
> Rolldown 是 Rust 编写、Rollup 兼容 API 的 bundler（原 `rolldown-vite` 过渡包仓库已 archived，Vite 8 直接内建）。**不变的架构思想**：dev 用浏览器原生 ESM 免打包 + 依赖预构建，prod 用统一 bundler 打包。

### Dev 阶段：依赖预构建 + 原生 ESM

1. **依赖预构建**（Vite 7 及以前用 esbuild；Vite 8+ 用 Rolldown）：把 `node_modules` 里的 CJS/UMD 依赖转成浏览器可用的 ESM，并合并海量小模块减少请求数——这一步仍然必要，只是执行者换了
2. **源码按需编译**：浏览器请求 `import './App.tsx'` 时，Vite 实时编译（Vite 8+ 转译由 Oxc 承担）
3. **HMR**：通过 WebSocket 推送变更，浏览器局部热更

### Prod 阶段：统一 bundler 打包（Vite 7 = Rollup，Vite 8+ = Rolldown）

- ✅ 树摇（Tree Shaking）
- ✅ 代码分割（动态 `import()`；注意 Vite 8 移除了对象形式 `output.manualChunks`，函数形式 deprecated，推荐 Rolldown 的 `codeSplitting`）
- ✅ 资源内联（小图片 base64）
- ✅ CSS 提取

---

## 基础配置
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8080',
    },
  },
  
  build: {
    target: 'es2022',
    sourcemap: true,
    // ⚠️ Vite 8 起该键更名为 build.rolldownOptions（rollupOptions 保留为 deprecated 别名）
    // 且对象形式 output.manualChunks 在 Vite 8 已移除，函数形式 deprecated → 推荐 Rolldown codeSplitting
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
        },
      },
    },
  },
})
```

---

## 插件生态
| 插件 | 作用 | 适用 |
|------|------|------|
| **@vitejs/plugin-react** | React Fast Refresh | React 项目 |
| **@vitejs/plugin-vue** | Vue SFC 支持 | Vue 项目 |
| **vite-plugin-pwa** | PWA 支持 | PWA 应用 |
| **vite-plugin-inspect** | 查看插件链中间产物 | 调试 |
| **vite-plugin-compression** | Brotli / Gzip 压缩 | 性能优化 |
| **vite-plugin-svgr** | SVG 作为 React 组件 | UI 组件 |
| **unplugin-auto-import** | 自动导入 API | 开发体验 |

---

## Vite vs 其他构建工具
| 工具 | 启动速度 | 生产构建 | 适用 |
|------|---------|---------|------|
| **Vite 8+** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐（Rolldown） | **新项目首选** |
| **Webpack 5** | ⭐⭐ | ⭐⭐⭐⭐⭐ | 存量项目 |
| **Rspack** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Webpack 兼容 + 极速 |
| **Turbopack** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 仅 Next.js |
| **Rolldown** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Rust bundler（Rollup 兼容 API），Vite 8 底层 |
| **esbuild** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 库构建 / Vite 7 及以前的底层（Vite 8 起不再是默认底层） |
| **Rollup** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐（库首选） | 库 / 组件库 / Vite 7 及以前的 prod 底层 |

---

## 性能优化
### Dev 优化
```typescript
// 优化依赖预构建
export default defineConfig({
  optimizeDeps: {
    include: ['large-dep'],  // 强制预构建
    exclude: ['dep-to-skip'],
  },
})
```

### Prod 优化
```typescript
export default defineConfig({
  build: {
    // 资源内联阈值（默认 4KB）
    assetsInlineLimit: 8192,
    // 代码分割策略
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
      },
    },
    // 压缩（分版本口径：Vite 7 默认 esbuild，可选 terser；Vite 8 默认 'oxc'（Oxc Minifier），
    // 'esbuild' 已 deprecated 且需自装 esbuild，'terser' 仍可选；CSS 压缩 Vite 8 默认 Lightning CSS）
    minify: 'esbuild',
    // CSS 代码分割
    cssCodeSplit: true,
  },
})
```

---

## 环境变量
```bash
# .env
VITE_API_URL=https://api.example.com
VITE_APP_TITLE=My App

# 仅 VITE_ 前缀暴露给客户端
```

```typescript
// 使用
const apiUrl = import.meta.env.VITE_API_URL
const isDev = import.meta.env.DEV
const isProd = import.meta.env.PROD
const mode = import.meta.env.MODE
```

```typescript
// 类型声明（env.d.ts）
/// <reference types="vite/client" />
interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_APP_TITLE: string
}
interface ImportMeta {
  readonly env: ImportMetaEnv
}
```

---

## 常见问题
| 问题 | 原因 | 解决 |
|------|------|------|
| **HMR 不生效** | 模块没导出 / 命名导入问题 | 检查导出 / 使用 named export |
| **依赖报错** | CJS 模块未预构建 | `optimizeDeps.include` |
| **生产环境路由 404** | 服务端未配置 SPA fallback | Nginx `try_files $uri /index.html` |
| **路径别名不生效** | `resolve.alias` + TS `paths` 需同步 | 两边都配置 |

---

## 学习路径
1. **入门**（1 天）：`npm create vite@latest` 跑通基础项目
2. **进阶**（1 周）：插件配置、环境变量、路径别名
3. **高级**（持续）：自定义插件、构建优化、Monorepo 集成

## 交叉引用
- [`04-engineering/`](../) — 工程化总览
- [`04-engineering/monorepo-practice/`](../monorepo-practice/) — Vite 在 Monorepo 的应用
- [`06-performance/`](../../06-performance/) — 构建与性能
- [Webpack → Vite/Rspack 迁移坑](../../../12.interview/09.front-end/webpack-vite-migration/README.md) — 迁移实战坑（CJS vs ESM / Tree-Shaking）
- 🆕 [前端构建越来越慢怎么排查](../../../12.interview/09.front-end/build-slow-troubleshooting/README.md) — 构建性能分层归因与诊断工具链

## 参考来源
- [Vite 官方《Migration from v7》](https://vite.dev/guide/migration.html) — "Vite 8 uses Rolldown and Oxc based tools instead of esbuild and Rollup"；`optimizeDeps.esbuildOptions` / `build.minify: 'esbuild'` deprecation 口径出处（2026-10 核实，对应 vite v8.3.4）
- [Vite build.minify 配置](https://vite.dev/config/build-options.html#build-minify) — Vite 8 默认 `'oxc'`，类型 `boolean | 'oxc' | 'terser' | 'esbuild'`
- [Rolldown GitHub](https://github.com/rolldown/rolldown) — "Fast Rust bundler for JavaScript/TypeScript with Rollup-compatible API"（官网 `https://rolldown.rs/` 本次核实环境网络不可达，故引用 GitHub 仓库）

## 可访问性（a11y）
Vite 构建产物对可访问性的影响：

- **语义化 HTML**：Vite 不破坏 HTML 结构，但需确保组件库输出语义化标签（`<button>` / `<nav>` / `<main>`）
- **插件支持**：`vite-plugin-aria` 自动注入 ARIA 属性；`eslint-plugin-jsx-a11y` 集成到 Vite 的 ESLint 配置
- **构建优化**：代码分割不影响屏幕阅读器，但需确保动态导入的组件有 `aria-live` 区域提示加载状态
- **测试集成**：`vitest` + `@testing-library/react` 的 `a11y` 插件可在 CI 中检测可访问性问题

---

← [返回 前端工程化](../README.md)
