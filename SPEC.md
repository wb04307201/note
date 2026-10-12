
# SPEC for note 知识库

> **Inherits from**: (无，L0 是顶层)
> **Mode**: append + override
> **Updated**: 2026-08-11

---

## 全局规范

### 1. 命名约定

- 主模块：`{nn}.{english-name}/`，两位数字 + 英文小写 + 短横线（如 `01.java-and-jvm/`）
- 子目录：按概念或深度，由各模块 SPEC.md 定义
- 文件：`README.md` / `SPEC.md` / `index.md` 保留约定

### 2. commit 格式

```text
feat(note): 新增内容
refactor(note): 结构调整
fix(note): 修复
chore: 琐事
docs: 文档
```

### 3. 互链规则

- 每个**有父 README 的非 leaf 文件**必须有 `← [返回 ...]` 回链到父 README
- **豁免规则**：
  - ① **leaf 文件**（无 children 的最终文档）由父 README 反向链回即可，不必每篇都加 `← [返回 ...]`
  - ② **12.interview question 文件**（约 230 题）由 frontmatter `topic` 字段隐式关联到父 README，无需每题加回链字符
  - ③ **13.story 单篇**（约 50 篇）由 `13.story/README.md` 顶部"系列定位"段总目录统一显式链回
- 至少 2 个跨模块或同模块的互链
- 系列文章末尾必须有"系列导航表"（13.story 由 README.md 系列定位块承担）

### 4. frontmatter 规范

所有"知识文章"（非 SPEC.md / README.md / index.md）必须用 HTML-comment frontmatter。**三类 schema**（按文件类型选其一，字段定义见对应 `<module>/SPEC.md`）：

| 类型 | 用途 | 字段示例 | L1 详细定义 |
|---|---|---|---|
| `module:` | 通用知识文章（810+ 篇） | parent, slug, type, category, summary | 默认 |
| `question:` | 12.interview 各题（≈230 题） | id, topic, difficulty, frequency, scenario_type, tags | `12.interview/SPEC.md §4` |
| `story:` | 13.story 阿明餐厅系列（≈50 篇） | number, type, position, title, audience, depth | `13.story/SPEC.md §4` |

**module: 默认示例**（其他类型必填字段见 L1）：

```text
<!--module:
  parent: <module-slug>
  slug: <article-slug>
  type: article | atomic | moc
  category: ...
  summary: ...
-->
```

> 为什么 3 类：12.interview/13.story 因强骨架格式需要不同字段（id 锚点 / number 编号），硬塞进 module 会破坏 cheatsheet 自动生成与 cross-ref 网络。SPEC §7 模式 `append + override` 允许 L1 模块细化。

### 5. G1-G6 通用评分维度

| # | 维度 | 2 分 | 1 分 | 0 分 |
|---|------|------|------|------|
| G1 | frontmatter 完整性 | 有完整 frontmatter + 字段正确 | 有但缺字段 | 无 |
| G2 | 一句话定位 | H1 后 ≤80 字清晰定位 | 有定位但 >80 字或模糊 | 无 |
| G3 | 代码块规范 | 所有代码块声明语言 | 大部分声明 | 有裸代码块 |
| G4 | 回链 + 互链 | 有 footer 回链 + ≥2 个旧章节互链 | 有回链但互链不足 | 无回链 |
| G5 | 内容深度 | ≥4 个层面 + 实战案例 | 2-3 个层面 | 只有定义 |
| G6 | 可读性 | 结构清晰 + 表格/图/代码辅助 | 基本可读 | 大段纯文字 |

### 6. 11 类基础扫描规则

| # | 类别 | 检测方式 |
|---|------|----------|
| 1 | 数字一致性 | grep "篇\|个\|行" vs find 实测 |
| 2 | H1/H2 标题规范 | grep "^# " 检查数字编号 |
| 3 | 回链覆盖率 | grep "← \[返回" vs find README 数 |
| 3.5 | 孤岛检测 | 新文件未在父 README 登记 |
| 4 | 索引/入口缺失 | find -type d vs README 引用 |
| 5 | 内容重复 | grep 关键概念多文件匹配 |
| 6 | 内容缺口 | find 浅 README (<50 行) |
| 7 | 命名一致性 | 目录命名风格 |
| 8 | PNG/脚本残留 | find *.png vs 引用 |
| 9 | 系列完整性 | 编号系列文件缺失 |
| 10 | 归属合理性 | 子目录与父定位不符 |
| 11 | 合并检测 | 单文件 >500 行 + ≥8 H2 + ≥8 反模式 |

---

### 7. SPEC 分层（仅元规范）

知识库内的规范文件分两层，**不互相合并**：

- **L1 `<module>/SPEC.md`**（每个模块必备）：评估维度 + 写作总则 + 子目录约定。
  继承自本文件 §5 / §6，模式 = append + override。
- **L1.5 `<module>/*-FORMAT-SPEC.md`**（仅强骨架模块按需存在）：强制文章结构
  （"## 引言"、"30s/90s 话术"、"## 第一章"、"系列定位块"）+ 反例表 + 版本日志。

**为何 L1.5 不并入 L1**：

- 行数差 5–7 倍（46 vs 306），合并后 L0→L1 继承清晰度被淹没
- 消费者不同（L1 给评审 / `note-health`；L1.5 给写作者 + cheatsheet 自动生成）
- 演化节奏不同（L1 稳定；L1.5 已有 v1.0→v1.1→v2.0 路线）

**何时新建 L1.5**：当模块出现**强制文章骨架**（不只是评估维度）
—— 例如 12 的"30s/90s 话术 + 追问模板"、13 的"编号 + 章节 + 系列定位"。
仅含评估维度的模块（如 01–11 大多数）**不需要** L1.5。

**当前存在的 L1.5**：**无**（v2.1 起，12.interview 原 `QUESTION-FORMAT-SPEC.md` 与 13.story 原 `STORY-FORMAT-SPEC.md` 均合并入各自主 L1 的 §4 / §5 — L1.5 是否独立存在应按模块规模与读者重合度判定）。
