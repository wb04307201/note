---
name: note-precipitation-planning
description: Use when user wants to modify or extend the knowledge base — 新增主题 ("X 应该沉淀到 note 什么位置" / "X 怎么归档" / "放在 note 哪个位置" / "如何沉淀 X" / "新增主题到 note") / 新增模块 ("加 14.llm-ops 模块" / "新加一个目录") / 批量迁移 ("课程 lesson 批量导入" / "从外部源引入") / 结构重构 ("09 拆成两个" / "合并两个 README" / "批量错位修正") / 修复更新 ("X 写错了" / "数字校对" / "数字统一") — covers location decision between main module / 12.interview / 13.story, layered precipitation, structural refactor (merge/split/relocate), batch migration (content-driven from external sources), and reverse-link verification. KB_DIR defaults to repo root, overridable via `NOTE_DIR` env var.
---

> [!IMPORTANT]
> **KB_DIR 守卫（2026-09-23 统一）**：KB_DIR 必须在执行任何 find/grep/python 之前导出。
>
> Bash 单行（放任何脚本顶部）：
> ```bash
> export KB_DIR="${NOTE_DIR:-$(git rev-parse --show-toplevel)}"
> ```
>
> Python heredoc（任何 `python << 'PYEOF'` 块开头必加）：
> ```python
> import os; KB_DIR = os.environ.get('KB_DIR', '.')
> ```
>
> 文档中所有 `$KB_DIR/...` 字面量是 LLM 路径示意，不参与 shell 展开；实操时用守卫段导出 `$KB_DIR` 让脚本内引用生效。

> **规则来源**：执行前必读 `$KB_DIR/SPEC.md`（G1-G6 通用评分 + 11 类扫描 + commit 格式 + 互链规则 + §7 SPEC 分层）以及目标模块的 `<module>/SPEC.md`（如 `$KB_DIR/01.java-and-jvm/SPEC.md`）。**若目标模块有强骨架规范**（如 `$KB_DIR/12.interview/QUESTION-FORMAT-SPEC.md`），同时必读 `<module>/*-FORMAT-SPEC.md`；13.story 已合并入 `<module>/SPEC.md` §4。模块结构在运行时通过 `find "$KB_DIR" -maxdepth 1 -type d` + `cat $KB_DIR/<module>/README.md` 读取，不硬编码。

> **目录变量（通用化）**：本 skill 默认使用仓库根目录的 `$KB_DIR/` 作为知识库根。**支持自定义**：
> 1. **环境变量**：`NOTE_DIR=./docs/knowledge` 覆盖
> 2. **配置优先**：项目根有 `.claude/knowledge-base.config.json`（schema: `{"kb_dir": "./docs/knowledge"}`）优先用配置
> 3. **自动检测**：`[ -d note ] && KB=note || KB=.`（无 `$KB_DIR/` 时用项目根）
>
> **本 skill 文档中所有 `$KB_DIR/` 在 bash / Python 代码块中已替换为 `$KB_DIR/`**，运行时按上述规则解析。

# note 沉淀规划

## 核心原则：**避免新文件成孤岛**

**任何新增 README 必须满足 3 个互链条件**，缺一即视为"孤岛"：

1. **新文件 → 旧章节**：新文件至少链接 2 个旧章节（避免"不知道放在哪")
2. **旧章节 → 新文件**：被链接的旧章节必须有**反向链接**（避免"单向链接")
3. **父 README / 总目录 → 新文件**：父目录 README / 总目录表 必须添加新文件链接（避免"父不知道有新成员")
4. **系列内兄弟互链**：当向已有系列添加新文章时，新文件**必须链向系列内所有已有兄弟**，且**所有已有兄弟必须回链新文件**（避免"同系列但互不知道"）

> **反直觉 1**：很多人以为"我加了反向链接就完事" —— 但**总目录扫描**经常漏掉。新文件链接了主模块 README，但主模块 README 没在目录表里加新文件 → **总目录是孤岛**。
>
> **反直觉 2**：Mistake 9 覆盖了 parent ↔ child 的反向链，但**同系列兄弟**之间是另一个维度。例如某系列有 01 / 02 文件，但 01 和 02 的文件末尾**没有链向** 03 和 04 —— 它们只链回 README。正确做法：每篇文件末尾加"系列导航表"，链向系列内所有其他文件。

## Overview

当用户问"这个主题应该新增/更新到 KB 的什么位置"时，遵循 8 步流程输出沉淀方案（Phase 0-7）。

> **模块结构与主题词映射**：13 主模块列表、12 强骨架栏目、子目录命名、常见主题词 → 路径的快速定位索引见 `$KB_DIR/SPEC.md §1`（L0 主模块规范）与 `$KB_DIR/SPEC.md §8`（关键词检索映射表）。本 skill 运行时通过 `find "$KB_DIR" -maxdepth 1 -type d` + `cat $KB_DIR/<module>/README.md` 读取模块列表，不硬编码路径。

> 🆕 **Phase 0 强化**：用户输入可能是**多个主题**（如"X 5 个灵魂拷问"实际包含 5 个独立子主题）。Phase 0 在盘点前先识别并拆分多主题，避免把 N 个独立主题错误合并成一个文件。
>
> **多主题拆分判定信号**（任一为 Yes → 拆分为多个 single-topic 文件）：
> - [ ] 文件覆盖 ≥3 个互不相关子主题？（"X 是什么"、"X 6 大"、"X 综述" 类标题）
> - [ ] 每个子主题都有自己的 30s/90s 话术？（合并文件通常每节都有完整话术模板）
> - [ ] 任一项 Yes → 拆分为多个 single-topic 文件，每个子题独立 frontmatter

## When to Use

**Use when**：
- 用户问"X 应该沉淀到 note 的什么位置？"
- 用户问"如何在 note 里新增/更新 X 主题？"
- 用户提供主题 + 问"放在 note 哪个位置合适？"

**Don't use when**：
- 用户已知具体位置（如"在 04.spring-backend 加 Spring Boot 3.5 新特性"）→ 直接实施
- 用户问"note 的现状" → 直接展示，不需要沉淀规划
- 用户问"note 的整体结构" → 直接展示 README
- 用户问"修复 X 文件" → 直接修复，不需要规划

## Project Context（必读）

> **主模块结构**：KB 主模块列表、子目录约定 → 见 `$KB_DIR/SPEC.md §1`（L0 主模块规范）。运行时通过 `find "$KB_DIR" -maxdepth 1 -type d` 读取，**不硬编码模块名**。

**3 大沉淀模式**（每次都问用哪个）：

| 模式 | 适用 | 落地位置 |
|------|------|---------|
| **单文件** | 内容 < 150 行 或 极专一 | 主模块子 README / 强骨架栏目（如 `<强骨架模块>/<topic>/`） |
| **双层沉淀**（最常用）| 面试高频 + 需深度原理 | 强骨架栏目（面试版） + 主模块（深度原理版） + 互链 |
| **三层 + 叙事联动** | 重要主题 + 有叙事价值 | 双层 + 叙事专栏加章节反向链 |

> **具体路径**：落点由 `$KB_DIR/SPEC.md §1`（主模块）与 `<module>/SPEC.md`（各 L1/L1.5）共同决定。运行 `exec_cmd {"cmd": "ls $KB_DIR/"}` 查看当前 KB 实际主模块名。

## 8 步核心流程

### Phase 0: 主题识别与拆分（必做，第一步）

**目的**：避免多主题错误合并成一个文件

#### Phase 0.1 修复/更新 vs 新增 沉淀 检测

**触发**：用户输入**第一句**含以下关键词时，先判定是"修复现有内容"还是"新增沉淀"：

| 关键词 | 含义 | 行动 |
|--------|------|------|
| "修复" / "fix" / "修正" / "改正" / "校准" / "数字统一" | 现有内容存在错误，需修正 | **不要**走沉淀规划，引导直接修复（用 Edit 工具）|
| "更新" / "补全" / "完善" / "深化" / "扩展" | 现有内容但有缺口 | **不要**走沉淀规划，识别目标文件后做增量修改 |
| "如何在 note 里 X" / "note 里 X 不对" / "note 中 X 错误" | 现有内容定位后修正 | 同上 |
| "新增" / "沉淀" / "添加" / "放 note" / "归档" | 全新内容 | **走** Phase 1-7 沉淀规划 |

**判定示例**：
- 用户："如何在 note 里修复 X"（X 已在 KB 中存在） → 走"修复" → 直接 Edit 修复
- 用户："沉淀 X" → 走"新增" → Phase 1-7

**Phase 0.1 输出格式**（命中修复类时）：

```markdown
## 🔧 Phase 0.1: 检测到「修复/更新」意图

**用户输入关键词**："<关键词>"
**判定**：修复现有内容（不是新增沉淀）

**目标文件**：`<目标文件>.md`（按 Phase 1 现状盘点定位）

**建议**：
- 选项 A：直接 Edit 修复该文件（推荐）
- 选项 B：补充新章节（如果缺口真实，需要新增 README）
- 选项 C：暂不处理

> 注：本 skill 不直接修复，请用 Read + Edit 工具操作；或转给其他工具
```

#### Phase 0.2 多主题识别（必做，第一步）

**判断逻辑**：

```text
用户输入包含多个独立概念？
├─ 有编号（"5 个灵魂拷问"、"3 大模式"、"N 种方案"） → 多主题
├─ 有并列（"A + B + C"、"A / B / C"、"A、B、C"） → 多主题
├─ 有"和"、"与"、"以及"连接不同领域主题 → 可能多主题
├─ 用户提到"N 个"、"几种"、"系列" → 多主题
└─ 单一概念 → 单主题
```

**多主题时的进一步判断**：

```text
多主题识别后，判断关联强度：
├─ 强关联（同一框架的不同维度，如"X 系统稳定性 5 问"）
│   → 创建系列目录，每个子主题独立成文
│
├─ 弱关联（只是同时提到，如"A + B + C"）
│   → 各自独立沉淀，互不依赖
│
└─ 部分关联（核心主题 + 边缘子话题）
    → 核心主题沉淀为主文件，边缘子话题作为章节或链接
```

**单主题时**：直接进入 Phase 1。

### Phase 0.5: 上下文预算评估（多主题时必做）

> **触发**：Phase 0 识别到 **≥ 2 个独立子主题**时必做。多主题沉淀可能占满上下文 → compact → 后续工作需手动恢复。

**复杂度评估**（每个子主题）：

| 因素 | 权重 | 说明 |
|------|------|------|
| 沉淀模式 | 单文件=1 / 双层=2 / 三层=3 | 双层涉及 2 个文件 + 2-3 个 commit |
| 父 README 更新数 | 每更新 1 个 +0.5 | 如 <强骨架栏目>/<module>/README.md + 主模块 README |
| 反向链复杂度 | 简单=0 / 中等=0.5 / 复杂=1 | 跨模块链接需路径验证 |
| 系列导航表 | 需要=1 / 不需要=0 | 向已有系列新增时需更新所有兄弟 |

**复杂度分级**：
- **简单主题**（总分 ≤ 2）：单文件 + 少量反向链
- **中等主题**（总分 2.5-4）：双层沉淀 + 2-3 个父 README 更新
- **复杂主题**（总分 ≥ 4.5）：三层沉淀 + 系列导航表 + 跨模块链接

**单次沉淀上限**：

| 场景 | 建议上限 | 理由 |
|------|---------|------|
| 全简单主题 | ≤ 3 个 | 每个 ~500 行上下文 |
| 混合（简单+中等） | ≤ 2 个 | 避免超过 2000 行上下文 |
| 全中等主题 | ≤ 2 个 | 每个 ~800 行上下文 |
| 含复杂主题 | **分批**（每次 1 个） | 复杂主题可能 > 1000 行上下文 |

**分批执行协议**：
1. **Batch 1**：沉淀前 1-2 个主题 → commit → 验证 → 输出总结
2. **主动提示用户**："Batch 1 完成。是否继续 Batch 2？（建议先 compact 再续）"
3. **Batch 2+**：用户确认后 → compact → 从 git log 恢复进度 → 继续

### Phase 1: 现状盘点（必做，不能跳过）

**目的**：避免重复沉淀、找到补充位置、识别已有结构

**操作**（`<强骨架栏目>` / `<叙事专栏>` / `<module>` 取自 $KB_DIR/SPEC.md §1 运行时读取）：
```bash
# 1.1 关键词搜索
export KB_DIR="${NOTE_DIR:-$(git rev-parse --show-toplevel)}"
grep -rl "<关键词>" $KB_DIR/ | head -10

# 1.2 主题目录扫描
find $KB_DIR/<module> -type d -name "*<topic>*" 2>/dev/null
ls $KB_DIR/<module>/

# 1.3 强骨架栏目同栏目兄弟
ls $KB_DIR/<强骨架栏目>/<module>/ | grep -v README

# 1.4 叙事专栏相关章节
grep -l "<关键词>" $KB_DIR/<叙事专栏>/*.md 2>/dev/null

# 1.5 系列结构检查（已有 01-N 编号文件 → 需补全系列内互链）
ls $KB_DIR/<target-dir>/[0-9]*.md 2>/dev/null

# 1.6 总目录入口验证（防"总目录孤岛"）
NEW_FILE="$KB_DIR/<target-module>/<topic>.md"
NEW_BASE=$(basename "$NEW_FILE" .md)
TARGET_README="$KB_DIR/<target-module>/README.md"
if [ -f "$TARGET_README" ] && ! grep -q "\[$NEW_BASE\]" "$TARGET_README" 2>/dev/null; then
  echo "⚠ $NEW_FILE 未在 $TARGET_README 目录表中登记（总目录孤岛）"
fi

# 1.8 同模式范例对照（先例优先 — troubleshooting 类先例 ≥ 3 篇 → 默认单面试题版）
ls $KB_DIR/<强骨架栏目>/<module>/ | grep -E "troubleshooting|incident|故障|排查" | head -10
for f in $KB_DIR/<强骨架栏目>/<module>/*/README.md; do
  if grep -q "troubleshooting\|排查\|故障" "$f"; then
    echo "$(wc -l < "$f") $f"
  fi
done | sort -n

# 1.9 Bonus 修复同源错误 grep（沉淀前主动检查）
#   grep -rn "<本案例核心反直觉点关键词>" $KB_DIR/
#   找到 1 处 → 顺手 fix commit；2+ 处 → 评估批量修复
```

**输出**：5-10 个相关文件 + 每个文件的"覆盖深度"评估（"已有详细"/"一笔带过"/"完全缺失"）+ **总目录验证结果** + **同模式先例行数对照表** + **Bonus 修复候选清单（如有）**

### Phase 2: 深度评估（值得沉淀吗？）

**值得沉淀的 3 个信号**：
1. **高频**（面试常考 / 实际生产常见）
2. **内容足够深**（4 个层面以上 + 5 个反模式 + 实战案例）
3. **缺口真实**（现有内容一笔带过 / 完全缺失 / 内容错误）

**不值得沉淀的信号**：
- 一句话就能讲清（如"什么是 HashMap"）
- 已有 5+ 重复内容
- 用户场景明确不需要

### Phase 3: 位置决策（用决策树）

```
用户场景是什么？
├─ 面试题 → <强骨架栏目>/<module>/<topic>.md（栏目名取自 $KB_DIR/SPEC.md §1）
├─ 深度原理 → 主模块（取自 $KB_DIR/SPEC.md §1）/<topic>/<topic>.md
├─ 叙事 → <叙事专栏>/<topic>.md（前传/续集/番外）
└─ 实战框架 → 主模块的工程子目录（如 <engineering>/<framework>.md）
```

> **强骨架栏目 + 主模块名 + 叙事专栏名** → 运行时读 `$KB_DIR/SPEC.md §1`。常见组合示例：
> - 13 主模块笔记库：12 个强骨架栏目 + 13.story 叙事专栏 + 11 个技术主模块
> - 简化笔记库：仅 N 个主模块，无强骨架栏目 + 叙事专栏 → 跳过双层 / 三层选项

**特殊位置判断**（按内容类型优先于用户场景）：
- 架构/模式 → 主模块的 `04-architecture/` 或 `02-technology-stack/` 子目录（命名约定见 `$KB_DIR/SPEC.md §1`）
- 算法原理 → 主模块的 `01-fundamentals/` 或 `02-technology-stack/`
- 面试 Q&A → `<强骨架栏目>/<module>/<topic>.md`

### Phase 3.5: 新增主模块 SOP（→ references/MODULE-CREATION-SPEC.md）

> 🆕 **v2.0 重构（2026-09-26）**：Phase 3.5 详细 5 步清单 / 判定表 / commit 模板 / Don't use when
> 已抽到 `references/MODULE-CREATION-SPEC.md`。
>
> **何时读**：用户问"加 NN.xxx 模块" / "建新模块" / "新加一个目录"时，沉淀前必读。
>
> **简版入口**（本 skill 触发判定）：
> - 判定：用户问"建模块"（不是"加主题到现有模块"）→ 走本 SOP
> - 5 步：定位（NN 是否占用）→ 建 SPEC.md → 建 README.md → 建 4 子目录占位 → 注册全局（README + CLAUDE.md + workflow）
> - 完整内容见 references/MODULE-CREATION-SPEC.md

### Phase 4: 沉淀方式决策（用决策树）

```
主题深度？
├─ < 100 行内容 → 单文件（1 commit）
├─ 100-300 行 + 面试价值 → 双层沉淀（2 commit）
└─ 300+ 行 + 已有叙事专栏相关章节 → 三层 + 叙事专栏联动（3+ commit）
    ⚠ 三层前必过 `<叙事专栏>/SPEC.md §3.5 准入判定`（6 信号：人物弧/类比落地/事故戏剧化为核心信号）
    ——「叙事价值高」不是循环直觉，①②③ 全过 + ④⑤⑥ 至少 2 过才走三层（详见 `$KB_DIR/13.story/SPEC.md §3.5`）

目标模块有无强骨架规范（L1 / L1.5）？
├─ 强骨架栏目（如面试版 / QA 库）→ 必读 `<强骨架栏目>/SPEC.md` §4 强骨架格式（如 30s/90s 话术 + 追问模板 + ## 引子/## 追问骨架）
│                  **必先过准入判定**：`<强骨架栏目>/SPEC.md §准入判定`（适合/不适合判定 + 反例清单）→ 不符合准入不准进
│                  （与 `note-health` Phase 1.14 `misplaced_classification` 协同兜底）
├─ 叙事专栏 → 必读 `<叙事专栏>/SPEC.md` §4 强骨架格式规范（如编号 + 章节骨架 + 系列定位块 + 文末回链）
└─ 其他主模块 → 当前无独立 `*-FORMAT-SPEC.md`；如本主题需强制骨架，**并入** `<module>/SPEC.md` 对应章节
              （遵循"并入主 SPEC"模式：v2.0 起全部 L1.5 已合并入 L1，不再另开 `*-FORMAT-SPEC.md`）

🆕 2026-08-28 经验补充：先例对照覆盖决策（基于 §1.8 同模式先例盘点）
├─ 同栏目 troubleshooting 类先例 ≥ 3 篇 + 用户输入是生产 Bug 案例 → **默认单面试题版**（不双层）
│   例：<现象>-troubleshooting（按 cpu-spike-troubleshooting 排比） — 都是 189-430 行单面试题
│   反模式：硬塞双层（主模块深读 800+ 行 + 面试题 200 行）→ 主模块过载 + 面试题泛化
├─ 同栏目无先例 + 内容跨多领域（如 Maven + JVM + 容器） → 拆分为多个单面试题
│   各自独立成文 + 互链（同 Mistake 16 多主题拆分）
└─ 内容是理论/原理（非生产 Bug 案例） → 走原 Phase 3 决策树（主模块深读 / 双层）
```

**双层沉淀模板**（commit 格式严格遵循 `$KB_DIR/SPEC.md §2`，`<type>(<scope>): <描述>`）：
```
Commit 1: feat(<强骨架栏目>): <强骨架栏目>/<module> - 新增'<topic>'面试题 + 陷阱表
Commit 2: feat(<主模块>): <主模块> - 新增'<topic>'深度原理（含源码分析）
```

**三层沉淀模板**：
```
Commit 1: feat(<强骨架栏目>): <强骨架栏目>/<module> - 新增'<topic>'面试题
Commit 2: feat(<主模块>): <主模块> - 新增'<topic>'深度原理
Commit 3: refactor(<强骨架栏目>): <叙事专栏相关> - 加反向链（指向新文件）
```

> **commit 格式 + 类型清单 + scope 命名约束** → 详见 `$KB_DIR/SPEC.md §2`（L0 commit 规范）。
>
> **典型 scope**（按仓库统一规范，不嵌模块名进 scope）：
> - 强骨架栏目沉淀：`feat(<强骨架栏目>)` / `fix(<强骨架栏目>)`
> - 主模块沉淀：`feat(<主模块>)` / `refactor(<主模块>)`
> - 全局 metadata：`docs(note)` / `style(note)` / `chore(note)`

### Phase 5: 选项呈现（用 AskUserQuestion，orchestrator 执行）

**关键**：如果作为 subagent 执行，**不能直接调 AskUserQuestion**，必须返回选项让 orchestrator 转交。

**选项呈现要点**：
1. **2-4 个选项**，每个选项 1-2 句说明
2. **推荐项放第一个** + 标注"(推荐)"
3. **每个选项要能独立执行**（不要有"以上全部"这种依赖项）
4. **不要列 16 种组合**（如 4×4 维度相乘）——会让用户决策瘫痪

**错误示例**：
```
A1 A2 A3 A4  ×  B1 B2 B3 B4  =  16 种组合
```

**正确示例**：
```
A. 双层沉淀 + 完整主模块推导（推荐）
B. 只动面试深挖版（最小改动）
C. 双层 + 联动（最完整）
D. 暂不沉淀
```

### Phase 5.5: 知识丰富度评估（条件触发网络搜索）

**目的**：在实施前判断是否需要补充外部知识，避免"用过时/不足的知识写文章"。

**触发条件**（满足任一 → 执行 WebSearch）：

| 信号 | 示例 |
|------|------|
| **快速演进领域**（AI / 云原生 / 框架版本等半年内可能变化） | "大模型 JSON 输出"、"分层路由" |
| **深度缺口**（Phase 1 扫描发现现有内容 < 20 行） | "统一权限系统设计" |
| **用户明确要求** | "搜索网络知识" / "给我最新方案" |
| **模型不确定**（具体 API / 框架版本 / 实现细节） | unsure about latest Spring Boot version |

**不触发条件**（直接用模型知识写）：

| 信号 | 示例 |
|------|------|
| **经典 CS 知识**（数据结构 / 算法 / 语言特性 / OS 原理） | StringBuilder、try-catch、虚拟线程 |
| **增量补充**（现有内容 > 100 行，只需追加） | 约定优于配置 |
| **面试八股文**（答案稳定、不随时间变化） | 死锁排查、Redis 单线程 |

**执行流程**（当触发时）：

```
1. WebSearch("<topic> <year> best practice / architecture")
2. 筛选 3-5 篇高质量结果（优先：官方博客 > 论文 > 技术博客）
3. 提取：最新方案 / 框架对比 / 反模式 / 生产数据
4. 与模型知识合并 → 写文章时标注"参考来源"章节
```

> **抓取受阻 fallback**（企业网络/沙箱常见）：`WebFetch` 可能因企业策略拦截官方文档域名。此时按序降级：
> 1. `chrome-devtools` MCP `navigate_page` **重试** + `evaluate_script` 取 `document.body.innerText`
> 2. `bing-search` MCP 搜索 → `crawl_webpage` 抓取高质量二手深度文交叉核实
> 3. 用户已在 prompt 中提供的权威命令/参数列表 = 一手依据
> **务必**：二手来源核实的关键语义要在文末「参考来源」标注来源级别，并提示用户对照官方复核存疑点。

**领域 query 模板**（按主题领域套用）：

> **具体领域列表 + 当前 KB 主题词速查** → 详见 `$KB_DIR/SPEC.md §8`（L0 关键词检索映射表）。KB 借用本 skill 时，应在 §8 自维护关键词映射表，**不必**绑这 5 类——可按 KB 实际内容领域扩展。
>
> **通用模式**（按内容领域归类）：
> - **AI / LLM**：`<topic> <year> benchmark / comparison`
> - **Spring / Java 框架**：`<topic> <version> release notes / migration`
> - **云原生 / DevOps**：`<topic> <year> production deployment`
> - **数据库 / 缓存**：`<topic> vs <alternative> benchmark`
> - **架构 / 设计**：`<topic> <year> architecture pattern`

**筛选优先级**：官方博客（*.<vendor>.com） > arXiv 论文 > InfoQ/DZone/Medium 技术博客 > 个人博客

**文章中的体现**：
- 末尾增加 `## 📚 参考来源` 章节，列出搜索到的 3-5 篇参考文章（含 URL + 一句话说明）
- 正文中引用的具体数据/方案标注来源

### Phase 6: 实施（dispatch subagent）

#### ⚠️ Phase 6.0 关键决策：内容驱动 vs 外部源映射（2026-08-14 教训）

**核心原则**：**按内容主题分类，不要按外部源编号机械复制**。外部源（课程 lesson / 培训材料 / 第三方仓库）是**编排**，不是**内容分类**——同一外部源不同文件可去不同 KB 目标。

**判断方法**：
1. 读每个文件的 `# 标题` + 第一段
2. 提取主题关键词
3. 按关键词决定目标子目录

#### ⚠️ Phase 6.1 深度重组（2026-08-14 教训·必做·不询问用户）

**核心原则**：沉淀 ≠ cp -r。沉淀必须做 **3 类主动整理**：

```
1. 合并（merge）
   ├─ 场景：同主题有 ≥2 篇文件
   ├─ 操作：选最长/最权威的为基准，其余合并入主文
   ├─ 必须保留所有原始引用 + 来源标注
   └─ 禁止：留 2 篇同主题文件让用户自己选

2. 拆分（split）
   ├─ 场景：单篇 ≥ 500 行且 H2 ≥ 8 且涵盖 ≥ 2 独立主题
   ├─ 操作：按 H2 主题切分 → 多个 single-topic 文件
   └─ 判定信号：见 Mistake "多主题错误合并"

3. 错位修正（relocate）
   ├─ 场景：文件内容主题与所在目录的父 README 定位不符
   ├─ 操作：移动文件到正确目录 + 加反向链
   └─ 判定：标题含与目录定位不同的关键词
```

**自动判定（不询问用户）**：
```python
for file in target_dir:
    title = read_h1(file)
    parent_dir_purpose = read_h1(f"{target_dir}/README.md")
    if topic_match(title, parent_dir_purpose):
        merge_or_keep(file, parent_dir)
    else:
        relocate(file, correct_topic_dir)
```

**反模式**（必须避免）：
- ❌ 留 2 篇同主题文件让用户决定 / 按文件名猜分类 / 机械复制 `cp -r <外部源>/...`
- ❌ 错位文件放错目录加 TODO / cp -r 后用 README 反向链接掩盖错位

**报告**（实施完成后）：合并了多少组 / 移动了多少错位文件 / 拆分了多少多主题大文件

**实施规范**：
- commit 格式遵循 `$KB_DIR/SPEC.md §2`
- 互链必须在 commit 中明示（"新增章节 + 加反向链"）
- 数字声明必须在 commit 前重新数（避免虚报）
- **目标路径必须实际验证**：写链接前用 `find "$KB_DIR" -name "<target>" -type f` 确认目标存在
- **每文件 commit 后立即跑 broken links 扫描**：发现新引入立刻修，不要累积
- 若 Phase 5.5 触发了网络搜索，文章末尾必须有 `## 📚 参考来源` 章节

**每 commit 后 broken links 扫描脚本**：
```bash
CHANGED=$(git diff --name-only --since="<本次沉淀开始时间>" | grep "\.md$" || true)
if [ -n "$CHANGED" ]; then
  python .github/workflows/scripts/check-broken-links.py $CHANGED
fi
```
如果 `real_broken > 0`，**立即修复下一个 commit**，不要等到沉淀结束。

**subagent "silent failure" 防御（强约束）**：

> ⚠️ 历史教训：曾出现多次 subagent 报告 "11/11 PASS" 但 `git status --short` 为空 / `ls file` 不存在（commit 1 subagent 多次完全无动作）。**subagent 自我报告 ≠ 实际落地**。
>
> 🆕 **2026-07-25 升级**（Phase 4 体检 + Batch 1-5 修复经验）：~6 个 subagent **修改了文件但没 commit**（"完成"报告但 `git log` 无 commit），需 orchestrator 收尾 commit。本条防御至关重要。

- **强制使用 Write 工具**：subagent 必须**实际调用 Write 工具**写入完整文件内容（不允许 placeholder / 占位符 / 仅创建空目录）
- **commit 前三步验证**：
  1. `ls -la FILE` 确认文件**真实存在**且**非空**（用 `wc -c` 验证文件大小 > 100 字节）
  2. `git status --short` 确认 staged/unstaged 状态**符合预期**
  3. `git log --oneline -3` 确认 commit 实际**落地**（前 3 commit 含本次 commit hash）
- **commit hash 必传**：subagent final report 必含**真实 commit hash**（不是"已 commit" 而是 `<hash> refactor(<slug>): ...`）。缺失则视为 commit 失败
### Phase 6.5-6.8: 操作层规范（已抽到 ORCHESTRATION.md）

> 🆕 **v2.0 重构（2026-09-26）**：subagent silent failure / git author / 并发协调 / 父 README 更新职责 4 类操作层规范已抽到项目级 `.claude/ORCHESTRATION.md`。
>
> 本 skill 只关心**沉淀流程**（Phase 0-6.9 的内容决策与实施），不耦合 orchestration 工具层细节。3 个 skill 共用同一份 ORCHESTRATION.md。
>
> **何时读 ORCHESTRATION.md**：
> - 派发 subagent 前 → 必读 §1-4 全部 4 节
> - subagent 报告"完成"后 → §1 + §3 验证 4 项命令输出
> - 多 session 并行 → §2 + §3
> - 沉淀后验收 → §4

### Phase 6.9: 模块级重构 SOP（→ references/REFACTOR-SPEC.md）

> 🆕 **v2.0 重构（2026-09-26）**：Phase 6.9 详细 3 类操作（拆分 / 合并 / 批量错位）
> 已抽到 `references/REFACTOR-SPEC.md`。
>
> **何时读**：用户需要**整个模块或大批量文件的重构**时（Phase 6.1 单文件级不够），沉淀前必读。
>
> **简版入口**（本 skill 触发判定）：
> - Phase 6.1 只覆盖单文件级；跨文件/整个模块的拆/合/批量错位 → 走本 SOP
> - 3 类操作：A. 拆分模块（如 09 → 09 + 14）B. 合并两个模块 C. 批量错位修正
> - Lesson：结构重组 = 230 处断链 87% 来源，每次 commit 后必跑 check-broken-links.py
> - 完整内容见 references/REFACTOR-SPEC.md

### Phase 6.10: 沉淀后 §8 映射表维护协议（→ SPEC.md §8.4）

> 🆕 **2026-10-12 通用化重构新增**（详见 commit `c5690f3` + `94078d2` + `fa927ef` + 本节）：本协议让 `note-precipitation-planning` Phase 6 完成新主题沉淀后，**自动把新主题词登记到 `$KB_DIR/SPEC.md §8` 词表**——实现「前向写 + 后向读」自动维护（`note-knowledge-qa` Phase 2 读取 / `note-health` Phase 1.15 稽核）。

#### 触发条件

- Phase 6 subagent 报告「已新增 `<module>/<topic>.md`（路径 `<path>`）」并 commit 落地
- 主题词有**跨模块检索价值**（关键词不在 §8 现有词表中，且属于 §8.3 五大领域之一）

#### 协议步骤（orchestrator 执行 · v3.x tags §8 write-time 同步）

1. **主对话校验** subagent 报告 —— 确认新文件路径 + frontmatter（含 `status:` / `tags:`） + commit hash（ORCHESTRATION.md §1）
2. **关键词提取** —— 从新文件 H1 / 关键词 / frontmatter `tags:` 提取 1-3 个核心词（优先读 `tags:` 列表，比 H1 关键词更结构化）
3. **路径定位** —— 复用 Phase 3 决策（主模块 + `<type=interview 模块>/` 路径，由 `SPEC.md §1.5` 自动发现）
4. **write-time 同步（v3.x 双 bridge 核心）**：
   - **写 §8** —— 在 `$KB_DIR/SPEC.md §8.X.Y` 对应分区末尾加 1 行（5 字段：主题词 / 主模块路径 / 12.interview 路径 / 频次 `-`）
   - **写 tags** —— 确保新文件 frontmatter 含 `tags: [<同 §8 主题词>]`（如果 subagent 漏填，orchestrator 在同步 §8 时一并补 tags）
5. **同 commit 内** —— 主题词词条 + tags 字段更新 + Phase 6 commit 合并为同一 commit（避免拆出独立 commit）
6. **跳过条件** —— subagent 报告主题不明确 / 工具配置类不入 12.interview / 主题已存在

#### 不强制场景

- 主题已被现有 §8 词覆盖（如新文件叫「RAG 工程化实施」，但 §8 已有「RAG Pipeline」）→ 跳过
- 主题是工具链小调整（如 Maven 编译参数、IntelliJ 配置）→ 跳过（§8 不收录）
- 主题是 troubleshooting 型（如 cpu-spike-troubleshooting）→ 跳过（§8 不收录）

#### 反例（不要加 §8 · 2026-10-12 v3.x 通用化）

> 反例已占位符化（v3.x）—— 任何 KB 都可借鉴：

| 反例类型（note KB 实例） | 不加原因（通用模式） |
|------------------------|---------------------|
| **构建工具配置类**（note 实例：Maven release/source/target 三参数，2026-10-12） | 任何 KB 的 `<type=interview 模块>/SPEC.md §准入判定` 反例清单都已包含；构建工具配置类不入 §8 |
| **非高频运行时参数**（note 实例：JVM 启动参数 `-Xmx` / `-XX:+UseG1GC`） | 已沉淀在 `<depth 模块>/<parameters 目录>/` 主模块，§8 不重复 |
| **工程模板类**（note 实例：Dockerfile / Docker Compose 写法） | 面试几乎不考（不入 §8 后 QA 也难命中）|

#### 长期验收

- `note-health` Phase 1.15 全库扫描会自动稽核 §8 词表所有路径（见 commit `94078d2`），死链则 P3 warning
- `note-knowledge-qa` Phase 2 关键词提取是 §8 的「消费者」（见 commit `fa927ef`）—— QA 时若发现 §8 缺关键主题词，**回填**到本协议

### Phase 7: 验证 + 自检（必做）

**自检清单**：
- [ ] `git diff --check` 无警告
- [ ] 抽查 5 条新加链接：`grep -RE '<pattern>' <module>/`
- [ ] 主 README 中章节锚点仍指向正确路径
- [ ] frontmatter 完整性：所有新增 README 都有 frontmatter
- [ ] 数字校对：声明篇数与 find 实际结果一致
- [ ] 互链成网：新内容与至少 2 个旧章节互链（避免孤儿）
- [ ] **互链双向性扫描**：每个反向链接的 parent / 同级兄弟**必须回链**到新文件（避免"单向链接"）
- [ ] **每个 PASS 都有证据**：附 commit hash + `wc -l` 输出 + 行号引用，不接受泛泛"全部 PASS"
- [ ] **严格对照用户原规格**：用户原文提到的具体链接必须 grep 验证
- [ ] **代码示例若规格要求**：bash / ffmpeg / openssl 等必须**实际代码块**而非文字描述
- [ ] **数字实时核对**：subagent 报告行数必须 orchestrator 独立 `wc -l` 校验，不接受 subagent 自我声明

#### 🆕 §7.1 链接路径校验（2026-09-02 教训·必做）

**Session 6 教训**：230 处断链 = 87% 来自"结构重组遗留路径错位"。新增内容时若引用其他模块路径，**必须执行实际路径校验**，仅看 README 文字描述不够。

**校验步骤**（commit 前必跑，统一调 `check-broken-links.py`）：
```bash
python .github/workflows/scripts/check-broken-links.py <新增文件列表>
```
**接受标准**：断链数 = 0。如有 1+ 断链，**修复后才 commit**（不允许"已知 broken"）。

**历史教训**（结构重组后未跟进 README 反链的典型案例）：
- `<module>/<topic>/` 引用了不存在的目录（迁移后未删除 README 残留链接）
- `<module>/<旧名>/` 旧名未及时跟进结构重组 → 新目录路径不一致
- `<叙事专栏>/<NN>-<topic>.md` 文件名已重命名，旧版反链失效

**反直觉 3**："我看了 README 觉得路径是对的" —— README 文字描述 ≠ 实际文件位置。**唯一可靠标准是 `os.path.isfile(target_abs)`**。

#### 🆕 §7.2 单文件自检（2026-09-02 教训·必做）

**触发时机**：Phase 6 subagent 报告 "完成" 后，orchestrator commit 前 **必做**。

**目的**：避免 subagent 自报 "全部 commit 完毕" 但实际引入新断链。**subagent 自我声明不算数**。

**执行命令**：
```bash
CHANGED_FILES=$(git diff --name-only HEAD | grep "^$KB_DIR/.*\.md$" || true)
if [ -n "$CHANGED_FILES" ]; then
  python scripts/check-broken-links.py $CHANGED_FILES  # 期望：❌ 0 处
fi
```

**接受标准**：断链数 = 0；父 README / 总目录回链已确认（§7 自检清单）

**失败处理**：
- 断链数 > 0 → **立即修复**（最常见是路径纠正，参考 §7.1）
- 修复不成功 → **不允许 commit**，返回 Phase 6 重做

**反直觉 4**："subagent 说做完了" ≠ "实际做完了"。**subagent 自我声明不算数**——必 orchestrator 独立校验。

**与 pre-commit hook 的关系**：
- pre-commit hook（`.githooks/pre-commit`）=**被动防护**（commit 时跑）
- §7.2 单文件自检 =**主动验证**（commit 前跑）
- **推荐流程**：subagent 完成 → orchestrator §7.2 → pre-commit 兜底

## Quick Reference

| 场景 | 推荐模式 | 落地位置 | Commit 数 |
|------|---------|---------|----------|
| 面试题（高频）| 双层 | <强骨架栏目> + 主模块 | 2 |
| 深度原理 | 双层 | 主模块 + <强骨架栏目> | 2 |
| 规模阶梯（10B→100B→1T）| 三层 + <叙事专栏> | 主模块 + <叙事专栏> 联动 | 3+ |
| 叙事价值高（过 `<叙事专栏>/SPEC.md §3.5` 准入 6 信号）| 三层 + <叙事专栏> | <叙事专栏> + 主模块 + <强骨架栏目> | 3+ |
| 单一补充（如 "X 的新特性"）| 单文件 | 主模块子 README | 1 |
| **🆕 生产 Bug 案例（同栏目 troubleshooting 先例 ≥ 3）**| 单面试题 | `<强骨架栏目>/<module>/<现象>-troubleshooting/` | 2-3 |

> **强骨架栏目 / 主模块 / 叙事专栏的实际名称** → 见 `$KB_DIR/SPEC.md §1`（运行时读取，不硬编码）。

### §X: 生产 Bug 类面试题特化（→ <强骨架栏目>/SPEC.md §5）

> **何时读**：用户提供生产事故案例 + 同栏目 troubleshooting 先例 ≥ 3 时，沉淀前必读 `<强骨架栏目>/SPEC.md` §5 决定命名 + 骨架 + 修复协议。
>
> **简版触发判定**（本 skill 入口）：
> - 触发条件：用户提供"线上 X 报警" / "X 100% 失败" / "X 反复触发"且故事完整
> - 命名规则：`<现象>-troubleshooting`（按 cpu-spike-troubleshooting 排比）
> - 7 节骨架：引子 → 核心原理 → 排查方法论 → 根因深挖 → 解决 → 验证 → 面试话术 → 相关章节
> - 完整内容见 `<强骨架栏目>/SPEC.md §5`（运行时读取栏目名）

## Common Mistakes

> 20 个 Mistake 全部下放到 [`references/mistakes.md`](references/mistakes.md) (~470 行)。SKILL.md 只保留索引。

**索引**（20 项 + 主题速查）：

| # | Mistake | 主题 |
|---|---------|------|
| 1 | 跳过现状盘点 | 流程 |
| 2 | 单一深度评估 | 流程 |
| 3 | 位置错位 | 分类 |
| 4 | 缺互链 | 互链 |
| 5 | subagent 调 AskUserQuestion 失败 | subagent |
| 6 | 缺 commit 策略 | commit |
| 7 | 数字虚报 | commit |
| 8 | 路径深度错误 | 路径 |
| 9 | 单向链接（child 链 parent，parent 不回链） | 互链 |
| 10 | 系列内兄弟不互链 | 互链 |
| 11 | subagent silent failure | subagent |
| 12 | git reset --soft + git commit --amend 错位 | commit |
| 13 | 过度宣称 PASS | subagent |
| 14 | 新内容引入新 broken links | 断链 |
| 15 | 同 README 内重复维护多个等价表格 | 文档 |
| 16 | 多主题错误合并成一个文件 | 拆分 |
| 17 | 多主题沉淀导致上下文溢出 | 上下文 |
| 18 | 并行 subagent 共享父 README 导致题数漂移 | 并发 |
| 19 | 父 README 历史遗留问题 | 并发 |
| 20 | 双层沉淀的"弱关联"互链 | 互链 |

📖 **完整内容**: [`references/mistakes.md`](references/mistakes.md) — 每个 Mistake 含「症状 / 修复 / 反直觉点」三段，带历史案例与检测脚本。

---

## Output Format

**作为 orchestrator**（直接面对用户）：

```
## 📋 现状盘点
（5-10 个相关文件 + 覆盖深度）

## 🎯 深度评估
（值得沉淀的 3 个信号 + 反信号）

## 💡 位置 + 方式建议
（决策树应用结果 + 推荐模式）

## ❓ 选项
（2-4 个选项 + 推荐项放第一）

[用 AskUserQuestion 呈现]
```

**作为 subagent**（让 orchestrator 转交）：

```markdown
## 报告：<topic> 沉淀分析

### 1. 现状盘点
（5-10 个相关文件 + 覆盖深度）

### 2. 深度评估
（值得/不值得 + 理由）

### 3. 位置 + 方式建议
（决策树应用结果 + 推荐模式）

### 4. 选项（请用户选择 A/B/C/D）

#### A. 双层沉淀 + 双向联动（推荐）
- 改动：3 文件 + 3 commit
- 优点：闭环最完整
- 缺点：改动略多

#### B. 只动面试深挖版
- 改动：1 文件 + 1 commit
- 优点：最小改动
- 缺点：缺深度原理层

#### C. 暂不沉淀
- 优点：避免冗余
- 缺点：现有缺口保留

### 5. 风险评估（如有） / 6. 验证清单（实施后需检查的 5 项）

[不要用 AskUserQuestion — orchestrator 转交]
```

## Cross-References（与其他 skill 的联动）

### 上游触发器（什么场景会触发本 skill）

| 触发来源 | 触发场景 | 跳转 Phase |
|---------|---------|-----------|
| `note-knowledge-qa` 未覆盖主题 | 用户问"X 是什么"但 KB 未沉淀 | Phase 0 → 现状盘点 → Phase 3 |
| `note-health` P0/P1 修复项 | 体检报告说"该模块 X 缺失" | Phase 3 → Phase 6 |

### 下游去向（沉淀完之后做什么）

| 沉淀结果 | 下一步 skill | 触发场景 |
|---------|------------|---------|
| 新文件落地 | `note-health` Phase 2 | "评价这篇新写的" / 自动 P1 检查 |
| 双层 / 三层故事联动 | `note-knowledge-qa` 直接可引用 | 后续问答命中新主题 |
| 结构性重构（拆/合模块） | `note-health` Phase 1 全库扫 | 验证重构后无新断链 |

### 关键 cross-ref 边界

- **本 skill 不处理**：纯内容问询（"X 原理" / "X 怎么用"）→ 走 `note-knowledge-qa`
- **本 skill 不处理**：质量评分（"这篇文章质量怎么样"）→ 走 `note-health` 单篇评分
- **本 skill 不处理**：全库互链矩阵设计 / 全局反向链审计（属于 QA 的检索行为或未来的全局互链 skill）

## Real-World Impact

> **沉淀结果统计**：KB 已沉淀 N 个主题 / commit 数 M → 详见 `$KB_DIR/CLAUDE.md`（仓库根仓库统计）+ `$KB_DIR/README.md`（各模块 leaf 数）。

<!-- v2.0 重构后此处不再硬编码主题列表，避免主题变化后 SKILL.md 失效。
     借用本 skill 的 KB 沉淀新主题后，按需在 $KB_DIR/CLAUDE.md 维护总览表。 -->

**沉淀流程价值**（避免的失败）：
- ❌ 重复沉淀（已有 X → 不重复）
- ❌ 位置错位（X 应在主模块 Y 而非 Z）
- ❌ 孤岛文件（每个新 README 至少 2 个反向链）
- ❌ 空 commit（commit 计划严格执行）

## Quick Checklist（执行前必过）

- [ ] Phase 1 完成：现状盘点（5-10 文件）
- [ ] Phase 2 完成：深度评估（3 信号检查）
- [ ] Phase 3 完成：位置决策（决策树应用）
- [ ] Phase 4 完成：方式决策（单/双/三层）
- [ ] Phase 5 完成：选项呈现（2-4 项 + 推荐）
- [ ] Phase 5.5 评估：知识丰富度（触发搜索 or 直接写）
- [ ] Phase 6 计划：commit 策略 + 互链 + 参考来源（如有搜索）
- [ ] Phase 7 计划：验证清单（5 项）+ **互链双向性扫描**

## Quick Checklist（执行后追加 — 避免新文件成孤岛）

- [ ] **新文件链接 ≥ 2 个旧章节**（避免"不知道放在哪"）
- [ ] **被链接的旧章节必须反向链回新文件**（避免"单向链接"）
- [ ] **新文件链到的同级兄弟必须回链**（避免同目录 leaf 互相不知）
- [ ] **父 README / 总目录表已加新文件链接**（避免"总目录孤岛"）
- [ ] **总目录数字（题目数 / leaf 数）已同步更新**（避免数字不一致）
- [ ] **系列内所有文件都有"系列导航表"**（当目标目录已有编号系列时，见 Mistake 10）
- [ ] **互链关联强度判定**（见 Mistake 20）：每个被链接的兄弟文件，grep "目标主题关键词"≥ 1 处才算强关联；弱关联（0 命中）即使"同栏目"也应删除
- [ ] **新 README 文末必须含 `← [返回:` footer 回链**（避免格式约定违反）
  - 自检命令：`grep -L "← \[返回:" $(find "$KB_DIR" -name "README.md" -newer <commit-base>)`
  - **新 README 必须有**，根目录 README（`README.md`）除外
- [ ] **新 README 内每张表格只承载一个职责**（避免同 README 内重复维护多张等价表，见 Mistake 15）
  - 自检：grep 新 README 的 `\|---` 表格分隔行数 ≥ 2 → 人工检查表格列字段是否重叠 ≥ 50%