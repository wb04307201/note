# 5-DIM-RUBRIC: 5 维评分标准

> **来源**: 2026-09-26 抽自 `.claude/skills/note-health/SKILL.md` Phase 6
> **Scope**: 当用户问"X 题是否过于简单"或"split-hairs 哪些该迁出"时触发。在 Phase 1/2/5 之上做**内容质量评分**。

---

## 5 维度定义

每维 0-2 分，总分 0-10。

| 维度 | 含义 | 2 分 | 1 分 | 0 分 |
|------|------|------|------|------|
| **D1 知识深度** | 源码级 + JVM/字节码 + 版本演进 | 含源码级深度 | 表面介绍 | 浅显 |
| **D2 知识广度** | 跨主模块联动 | ≥3 个主模块交叉 | 单一模块 | 局限 |
| **D3 面试频次** | 真实面试出现频率 | 高频必考 | 偶尔考 | 罕见 |
| **D4 追问空间** | 面试官可追问几层 | ≥3 层深入空间 | 1-2 层 | 一问到底 |
| **D5 反直觉/陷阱** | 反直觉陷阱 / 生产事故案例 | 有事故 + 教训提炼 | 有陷阱无案例 | 平铺直叙 |

---

## 阈值

| 总分 | 判定 | 行动 |
|------|------|------|
| ≥ 7 | 保留 | 维持当前位置 |
| 4-6 | 灰色 | 评估是否有补救空间 |
| ≤ 3 | 迁出 | 移至 split-hairs 或删除 |

---

## 配套评分表

E7-E11 评分表见 `references/leaf-quality.md` 末尾（E7-E11 节）。

---

## 与 difficulty 深度校准的衔接

本阶段产出的五维分同时是 `difficulty` 深度校准的数据源——

| 总分 | 建议星级 |
|------|---------|
| 9-10 | ⭐⭐⭐⭐ |
| 7-8 | ⭐⭐⭐ |
| 5-6 | ⭐⭐ |
| ≤ 4 | ⭐ |

偏差 ≥ 1 星进校准清单。完整执行流程见 `references/structural-checks.md` Phase 15「深度校准流程」。

全库打分时 `health-workflow.js` 已自动采集 `fiveDim`，无需单独再跑一轮五维评分。

---

## 4 个实战教训（2026-08-10 总结）

### 教训 1：标题/文件名预筛 false positive 高达 70%

`closure`、`prototype-chain`、`mysql-int-define`、`redis-eviction` 等看着基础但实际深度评分 8-10。

**禁止仅基于文件名/行数判定**，必须 Read 全文。

### 教训 2：frontmatter `difficulty` 标记偏乐观

本次发现 19 处 frontmatter difficulty 与实际内容深度不一致（16 处低估 + 3 处高估）。

Phase 1 应加 **frontmatter 一致性校准**（见 `structural-checks.md` Phase 15）。

### 教训 3：按子目录分批 dispatch 是高效模式

避免单 agent 全库评估时的疲劳偏差（如 11.ai 体量大易被误杀）。

按子目录 6-15 篇/agent，每个 agent 上下文清晰。

### 教训 4：灰色地带处置模式

4-6 分的题有 3 种处置：
1. 保留（内容够）
2. 加 frontmatter 校准（difficulty 反映实际深度）
3. 拆分综述（多主题合并文件违反 split-hairs 单点深挖定位）
4. 迁出（保留 30s/90s 话术作为"速记卡"追加主模块）

---

## 相关文件

- `note-health/SKILL.md` Phase 6（指针）
- `note-health/references/leaf-quality.md` E7-E11 节
- `note-health/references/structural-checks.md` Phase 15 深度校准流程
- `note-health/references/health-workflow.js`（runtime 五维采集）