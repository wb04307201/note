<!--module:
  parent: front-end
  slug: front-end/web-components
  type: article
  category: 主模块子文章
  summary: Web Components
  depth: ⭐⭐
  status: active
-->

# Web Components

> **一句话定位**：浏览器原生组件标准——Custom Elements + Shadow DOM + HTML Templates 三件套，跨框架复用，长期可维护。

---

**Web Components 是一套浏览器原生支持的组件化技术标准，它允许开发者创建可复用、封装良好的自定义 HTML 元素，并直接在浏览器中运行，无需依赖外部框架。**

## 一、核心组成
Web Components 由**三大核心技术**构成，共同实现组件的封装与复用：
1. **Custom Elements**
    - 允许开发者定义全新的 HTML 标签（如 `<my-button>`），并为其绑定自定义逻辑。
    - 提供生命周期回调（如 `connectedCallback`、`attributeChangedCallback`），便于管理组件状态。

2. **Shadow DOM**
    - 为组件创建独立的 DOM 树，实现样式和行为的隔离，避免全局 CSS/JS 污染。
    - 通过 `slot` 机制支持内容投影，增强组件灵活性。

3. **HTML Templates**
    - 定义可复用的 HTML 片段（`<template>` 标签），通过 JavaScript 动态实例化，减少重复代码。

> ⚠️ **已废弃的第四项标准 — HTML Imports**
>
> HTML Imports 曾被列为 Web Components 的第四项核心技术，用 `<link rel="import" href="...">` 跨文件导入组件模板。但因与 ES Modules 功能重叠、各浏览器实现支持不一，**Chrome 73 (2019) 起被移除，2019-2020 年期间 Firefox / Safari / Edge 也全面下线**。现代项目应改用 **ES Modules**（`import { ... } from './xxx.js'`）+ 构建工具（Vite / Rollup / esbuild）替代。
>
> 参考：[MDN — HTML Imports](https://developer.mozilla.org/en-US/docs/Web/Web_Components/HTML_Imports)

### 最小完整示例：`<my-button>`

三件套（Custom Element + Shadow DOM + `<template>`）组合成一个可运行的自定义按钮：

```html
<template id="btn-tpl">
  <style>
    /* 样式被 Shadow DOM 隔离，不会泄漏到页面，也不受外部 CSS 影响 */
    button { padding: 6px 16px; border-radius: 4px; border: 1px solid #4a7; }
    :host([disabled]) button { opacity: 0.5; cursor: not-allowed; }
  </style>
  <button part="inner"><slot>默认文本</slot></button>
</template>

<script>
class MyButton extends HTMLElement {
  constructor() {
    super();
    // 创建 Shadow Root，实现 DOM/样式隔离
    this.attachShadow({ mode: 'open' });
    // 克隆 <template> 内容作为组件的内部结构
    const tpl = document.getElementById('btn-tpl');
    this.shadowRoot.appendChild(tpl.content.cloneNode(true));
  }
  connectedCallback() {
    // 元素插入文档时触发：绑定事件、读取初始属性
    this.shadowRoot.querySelector('button')
      .addEventListener('click', () => this.dispatchEvent(new CustomEvent('my-click')));
  }
  static get observedAttributes() { return ['label']; }
  attributeChangedCallback(name, _, val) {
    if (name === 'label') this.shadowRoot.querySelector('slot').textContent = val;
  }
}
customElements.define('my-button', MyButton); // 注册标签名（必须含连字符）
</script>

<!-- 使用：像原生标签一样 -->
<my-button label="提交"></my-button>
```

**Shadow DOM 隔离效果**（为何"组件内样式互不干扰"）：

```html
<style>p { color: red; }</style>
<p>我是页面里的段落，红色</p>
<my-button></my-button> <!-- Shadow DOM 内部的 <p>/按钮不受外部 p{color:red} 影响 -->
```

外部选择器无法穿透 Shadow 边界（除非组件用 `::part` / CSS 变量显式暴露），这就是"封装性与安全性"的技术来源。

## 二、核心优势
1. **跨框架兼容性**
    - 作为浏览器原生技术，Web Components 可无缝集成到 React、Vue、Angular 等任意框架中，甚至用于纯 JavaScript 项目或服务端渲染（SSR）。
    - **案例**：Microsoft 基于 FAST 库构建的 Web Components 应用于 MSN、Edge、VS Code 等产品线；YouTube 长期使用 Web Components 构建界面。

2. **长期可维护性**
    - 不依赖特定框架版本，避免框架升级或停更带来的风险。例如，Github 逐步用 Web Components 替换 jQuery，降低技术债务。

3. **原生性能优势**
    - 直接运行在浏览器中，无需虚拟 DOM 或额外渲染层。
    - 体积与效率的**定性结论**：原生 Custom Element 不需要打包框架运行时（React/Vue 运行时本身即为数十 KB 级的额外依赖），因此在"只交付组件"的场景下整体交付体积通常更小、启动开销更低。具体数字随组件复杂度与所用库（原生 vs Lit vs Stencil）差异很大，如需精确对比请以 [bundlephobia](https://bundlephobia.com/) 实测各库 minified + gzip 体积为准，不建议直接引用固定数字。

4. **封装性与安全性**
    - Shadow DOM 隔离样式和脚本，防止组件间冲突；自定义元素命名空间避免全局标签污染。

## 三、典型应用场景
1. **开发跨框架 UI 组件库**
    - 构建一套组件库供多技术栈项目使用，如哈啰平台开源的 Web Components 组件库。

2. **老旧项目升级**
    - 逐步用 Web Components 重构非组件化代码，拆分应用为可维护模块，降低升级风险。

3. **微前端架构**
    - 作为独立部署的微应用单元，支持不同团队独立开发、部署，且互不干扰。

4. **跨平台应用**
    - 在桌面、移动端、Web 多平台复用 UI 组件，如 SpaceX 龙飞船显示器广泛使用 Web Components。

## 四、挑战与解决方案
1. **浏览器兼容性**
    - **现状**：Chrome、Firefox、Edge、Safari 已原生支持，IE11 需 Polyfill 填补。
    - **建议**：通过 `@webcomponents/webcomponentsjs` 等库提供兼容支持。

2. **开发复杂度**
    - **问题**：需手动管理 DOM、状态和生命周期，学习曲线较陡。
    - **解决方案**：使用 Stencil.js、Lit 等库简化开发，提供装饰器、状态管理等高级特性。

3. **生态成熟度**
    - **对比框架**：社区规模和工具链不如 React/Vue 完善，但快速增长中。
    - **趋势**：Material Web Components、Shoelace 等开源库逐步完善，企业级应用案例增多。

4. **无障碍（a11y）挑战**
    - **问题**：Shadow DOM 的隔离边界同时挡住了辅助技术（屏幕阅读器）与全局样式/焦点管理的"惯例路径"，是最容易被忽视的一类坑。
    - **ARIA 穿透**：Shadow 边界内外的 ARIA 关联会断裂——外部元素的 `aria-labelledby` 无法指向 Shadow 内部的节点，反之亦然。解法：把 `role` / `aria-*` 写在**宿主元素本身**（custom element 标签上），或组件内部用 `ElementInternals`（`this.attachInternals()`）声明语义（如 `internals.role = 'button'`），这是目前标准化的正确姿势。
    - **焦点管理**：Tab 键可以进入 Shadow DOM 内部的聚焦元素（浏览器原生支持），但常见坑有三个：① 宿主元素自身默认不可聚焦，需要显式 `tabindex`；② 焦点进入 Shadow 内部后，`document.activeElement` 只显示宿主，调试要用 `shadowRoot.activeElement`（或 `event.composedPath()`）；③ 模态类组件需要自己实现焦点圈闭（focus trap）与 `Esc` 关闭，Shadow DOM 不会代劳。
    - **样式穿透**：外部无法用普通选择器给 Shadow 内部元素加样式（包括 `:focus-visible` 高亮、Windows 高对比度模式适配）。组件作者必须主动暴露定制点：用 `::part()` 导出内部部件（`<button part="inner">` → 外部 `my-button::part(inner) { outline: ... }`）、用 CSS 自定义属性做主题通道（`--my-btn-color`）、并支持 `:host-context()` / 媒体查询响应系统级偏好（`prefers-reduced-motion`、`forced-colors`）。
    - **建议**：把 a11y 当作组件 API 的一部分设计（role/label/焦点行为在组件内部实现好），而不是留给使用方补救；可参考 Shoelace、Material Web 等成熟库的 a11y 实现方式。

## 五、未来展望
- **标准化推进**：WHATWG 和 W3C 持续完善规范，浏览器原生支持将更广泛。
- **框架融合**：React/Vue 等框架可能增加对 Web Components 的深度集成，形成互补生态。
- **企业级采纳**：随着对长期维护性和跨框架兼容性的重视，Web Components 或成为大型项目标配。

---

← [返回 前端架构](../README.md)
