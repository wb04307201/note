# SPLIT-DETECTION: 拆分检测标准

> **来源**: 2026-09-26 抽自 `.claude/skills/note-health/SKILL.md` Phase 7
> **Scope**: 检测"多主题错误合并"——单文件覆盖多个互不相关子主题（违反 split-hairs 单点深挖定位）

---

## 历史案例

原 split-hairs `02.computer-basics/machine-learning/README.md` 是 6 大算法综述（违反 split-hairs 单点深挖定位），已拆分为 6 个 single-topic deep-dive。

---

## 判定标准

任一为是 → 触发拆分：

| 信号 | 阈值 |
|------|------|
| 文件覆盖 ≥ 3 个互不相关子主题 | 30s 话术对应不同子主题 |
| 标题过于宽泛 | "X 是什么" / "X 综述" / "X 全景" / "X 6 大" |
| 每个子主题都合格 | 但合并后违反单点定位 |

---

## 拆分后

- 每个子主题 → 独立 `<topic>/README.md` + frontmatter（question 类型）
- 原综述文件删除（或保留为索引页，引用所有 deep-dive）
- 父 README 目录表更新

---

## 验证通过标准

- ✅ 每条 commit 有真实 hash（不是"已 commit" 文字）
- ✅ `git status --short` 输出为空
- ✅ 扩充后行数 ≥ 300 行（或目标值）
- ✅ broken links 扫描输出为空（或只有预期的边缘 case）

---

## 验证失败处理

| 失败 | 处置 |
|------|------|
| commit hash 缺失 | 立即补 commit |
| 工作树有未提交修改 | 决定是否 commit 或 discard |
| broken links | 立即修复，不要累积 |

---

## 相关文件

- `note-health/SKILL.md` Phase 7（指针）
- `note-precipitation-planning/SKILL.md` Mistake 16（多主题错误合并教训）
- `.github/workflows/scripts/check-broken-links.py`（验证工具）