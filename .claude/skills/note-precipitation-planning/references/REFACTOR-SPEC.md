# REFACTOR-SPEC: 模块级重构 SOP

> **来源**: 2026-09-26 抽自 `.claude/skills/note-precipitation-planning/SKILL.md` Phase 6.9
> **Scope**: Phase 6.1（merge/split/relocate）只覆盖单文件级。当用户需要**整个模块或大批量文件的重构**时使用本 SOP

---

## 何时用

- Phase 6.1 单文件级 relocate 不够
- 需要跨多个文件/整个模块的拆/合/批量错位

---

## 3 类操作

### A. 拆分模块（如 "09.ai-applications → 09 + 14.llm-ops"）

1. **切分主题清单**：扫描 `$KB_DIR/09.ai-applications/` 下所有 README，分类：哪些子主题归新模块？哪些留原模块？（参考 `references/main-module-depth.md` 现有子目录划分）
2. **建新模块骨架**：按 [MODULE-CREATION-SPEC.md](./MODULE-CREATION-SPEC.md) 走 SPEC.md + README.md + 子目录创建
3. **git mv 切分**：把分类到新模块的子目录/文件 `git mv` 到 `$KB_DIR/14.llm-ops/`
4. **批量路径重写**：
   ```bash
   # 找出所有指向旧路径的链接(全库搜索,排除 .git .claude)
   grep -rl '09\.ai-applications/old-sub' $KB_DIR --include='*.md' | grep -v '\.claude/skills/'

   # sed 批量替换(先 dry-run 验证 1 个文件)
   sed -i 's|09\.ai-applications/old-sub|14.llm-ops/old-sub|g' <file-list>
   ```
5. **反向链批量修复**：跑 `python .github/workflows/scripts/check-broken-links.py` 全库扫描 — 0 断链才能 commit
6. **注册到全局**：更新总目录 + CLAUDE.md + workflow paths 触发器（同 MODULE-CREATION-SPEC.md Step 5）

### B. 合并两个模块（如 "10.business-systems + 11.product-and-pm → 10"）

1. 决定保留哪个 NN 编号（推荐保留较小编号 = 时间优先）
2. git mv 待合并模块的子目录/文件到保留模块
3. 路径重写（反向操作：旧路径 → 保留模块路径）
4. 反向链 + check-broken-links.py 全库扫描
5. 删除空模块目录

### C. 批量错位修正（如 "全库 230 处断链对应的文件路径纠正"）

1. **收集目标错位清单**：
   ```bash
   grep -rl 'old-pattern' $KB_DIR --include='*.md' | wc -l  # 确认影响范围
   ```
2. **写 sed 脚本**：先 `--dry-run` 验证 1-2 个文件（避免误改）
3. **分批替换**：每 N 个文件 1 个 commit（推荐 N=20-50，避免 1 commit 100+ 文件不可逆）
4. **每 commit 后跑 check-broken-links.py**：错误数应该递减，最终 0

---

## Lesson（Session 6 教训）

结构重组是 230 处断链的 87% 来源。每次模块级重构 commit 后必须：

```bash
python .github/workflows/scripts/check-broken-links.py  # 全库扫描,断链数必须 ≤ 上次
```

---

## Don't use when

- 单文件错位 → Phase 6.1 relocate（不需要本 SOP 这么重）
- 加新主题到现有模块 → Phase 3 普通决策树
- 加全新主模块 → [MODULE-CREATION-SPEC.md](./MODULE-CREATION-SPEC.md)

---

## 相关文件

- `note-precipitation-planning/SKILL.md` Phase 6.9（指针）
- `note-precipitation-planning/SKILL.md` Phase 6.1（单文件级 relocate）
- [MODULE-CREATION-SPEC.md](./MODULE-CREATION-SPEC.md)（姊妹：模块创建 SOP）
- `.github/workflows/scripts/check-broken-links.py`（验证工具）