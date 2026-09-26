# MODULE-CREATION-SPEC: 新增主模块 SOP

> **来源**: 2026-09-26 抽自 `.claude/skills/note-precipitation-planning/SKILL.md` Phase 3.5
> **Scope**: 用户需要**新建一个顶层模块**（如"加 14.llm-ops"）时使用

---

## 判定：建模块 vs 加主题

| 用户原话 | 判定 | 走哪 |
|---------|------|------|
| "加 14.llm-ops 模块" / "建一个新模块" / "新加一个目录" | **建模块** | 本 SOP |
| "X 应该放在哪个模块" / "X 沉淀到 09.ai-applications" | 加主题 | Phase 3 普通决策树 |

---

## 5 步清单

### Step 1：定位

- NN 编号（14/15/...）是否已被占用？
- 命名是否符合现有 13 模块惯例（`NN.<kebab-name>/`）？
- 参考 `$KB_DIR/README.md` 总目录检查已用编号

### Step 2：建 `SPEC.md`

参考 `01.java-and-jvm/SPEC.md` 结构：
- 模块定位
- 从 L0 继承
- 评估维度 D1-D5
- 子目录约定
- 链接回 `../SPEC.md` §7

### Step 3：建 `README.md`

含：
- 模块定位 1 段
- 子目录表（占位即可）
- 互链规则（指向总目录 + 13 模块导航）

### Step 4：建 4 个标准子目录占位（按需）

- `01-fundamentals/`
- `02-technology-stack/`
- `03-engineering/`
- `04-architecture/`

参照 09.ai-applications 现有 4 子目录结构。

### Step 5：注册到全局

- 更新 `$KB_DIR/README.md` 总目录（每模块一行）
- 更新 `CLAUDE.md` 关键规范引用表的「各模块自有 SPEC」行
- 更新 `.github/workflows/difficulty-calibration.yml` paths 触发器（添加新模块路径）
- 如有 `references/` 共享资源需要复制到新模块（评估维度 / 模板），单独 commit

---

## Commit 格式

建议 5 commit（每个步骤 1 个），便于 review 与回滚：

```
1. docs(SPEC): 14.llm-ops - 新模块 SPEC.md（模块定位 + D1-D5 + 子目录约定）
2. docs(README): 14.llm-ops - 模块总览 README（定位 + 子目录表 + 互链规则）
3. chore(structure): 14.llm-ops - 4 子目录占位 + 占位 README
4. chore(root): 总目录 / CLAUDE.md 同步新增 14.llm-ops
5. chore(workflow): difficulty-calibration.yml paths 触发器添加 14.llm-ops/**
```

---

## 回链必备

- 新 `SPEC.md` 必须有 `← 返回 note 总目录` footer（同其他模块）
- 新 `README.md` 必须有 `← [返回: 14.llm-ops]` footer（与本仓库 SPEC.md §G4 一致）

---

## Don't use when

- 用户问"X 应该放在哪个现有模块" → 走 Phase 3 普通决策树
- 用户问"我要拆 09.ai-applications 成两个" → REFACTOR-SPEC（不是这里）
- 用户问"新加一个子目录到 09.ai-applications" → 本 SOP 的"建子目录"子流程（去掉步骤 1-2，保留 3-5）

---

## 相关文件

- `note-precipitation-planning/SKILL.md` Phase 3.5（指针）
- `note-precipitation-planning/SKILL.md` Phase 4 普通决策树（替代选项）
- `REFACTOR-SPEC.md`（模块级重构 SOP，姊妹文件）