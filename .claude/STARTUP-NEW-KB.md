# 全新知识库启动指南：用本仓库的 3 skill + ORCHESTRATION 启动新 KB

> **Inherits from**: [`.claude/ORCHESTRATION.md`](./ORCHESTRATION.md)
> **Scope**: 项目级（与 ORCHESTRATION.md 同层；不绑具体 skill）
> **Updated**: 2026-10-12（基于元问题 3 通用化重构实战）
> **适用读者**: 任何要用本仓库沉淀 / 体检 / 问答 3 个 meta-skill 启动新 KB 的人

## 0. 适用场景

- 个人 / 团队新领域 wiki
- 内部知识库（机器学习框架 wiki / 团队协作文档 / 内部培训手册）
- 不愿白手起家 → 复用本仓库沉淀 + 体检 + 问答流程

**反例**（不适用本文）:
- 只想写一篇文章 → 直接用 Obsidian 即可
- 想做静态文档站 → 用 VitePress / Docusaurus
- 临时任务笔记 → 用 README.md 单文件足够

## 1. 复制工具（4 项）

把以下文件 / 目录从本仓库（`note/`）复制到新 KB 根：

| 来源 | 目标 | 用途 |
|------|------|------|
| [`.claude/ORCHESTRATION.md`](./ORCHESTRATION.md) | `<新 KB>/.claude/ORCHESTRATION.md` | 3 skill 共享运维协议 |
| [`.claude/skills/note-precipitation-planning/SKILL.md`](./skills/note-precipitation-planning/SKILL.md) | `<新 KB>/.claude/skills/note-precipitation-planning/` | 沉淀 skill（Phase 0-7） |
| [`.claude/skills/note-health/SKILL.md`](./skills/note-health/SKILL.md) | `<新 KB>/.claude/skills/note-health/` | 体检 skill（Phase 1.1-1.15） |
| [`.claude/skills/note-knowledge-qa/SKILL.md`](./skills/note-knowledge-qa/SKILL.md) | `<新 KB>/.claude/skills/note-knowledge-qa/` | 问答 skill（Phase 0-4） |
| `.github/workflows/scripts/check-broken-links.py` | `<新 KB>/scripts/check-broken-links.py` | 链接完整性自检（可选但推荐） |

> **为什么不需要复制 `references/`**：3 skill 各自的 `references/` 子目录已通过 `cp -r` 整个目录一并复制（如 `note-precipitation-planning/references/MODULE-CREATION-SPEC.md` 等）。

### 1.1 KB_DIR 环境变量（必须）

3 skill 用 `$KB_DIR/` 引用路径，**必须 export**：

```bash
# Bash: 加到 ~/.bashrc / ~/.zshrc 或单次 export
export KB_DIR="${NOTE_DIR:-$(git rev-parse --show-toplevel)}"

# 或在 KB 根目录跑命令时自动检测 CWD（fallback）
cd <新 KB>
python scripts/check-broken-links.py  # 自动用 CWD 作 KB_DIR
```

## 2. 新 KB 必备骨架（最少 7 项）

### 2.1 目录结构（最小）

```text
<新 KB>/
├── SPEC.md                          # L0 通用规范（详见 §2.2）
├── README.md                        # 总目录（链到所有主模块）
├── 01.<主模块 A>/                   # 至少 2 个主模块（命名 NN.<name>/）
│   ├── SPEC.md                      # L1 模块规范（可选，推荐）
│   └── README.md                    # 主模块总入口
├── 02.<主模块 B>/                   # 第 2 个主模块
│   └── README.md
├── .claude/
│   ├── ORCHESTRATION.md             # 已复制（见 §1）
│   └── skills/                      # 已复制（见 §1）
├── scripts/
│   └── check-broken-links.py        # 已复制（见 §1）
└── （可选）<module>/SPEC.md         # 模块级评估维度
```

### 2.2 SPEC.md 必填章节（最低 7 节）

| § | 内容 | 必填性 | 最低要求 |
|---|------|:---:|----------|
| §1 | 命名约定（主模块前缀、子目录规则、文件名规范） | ✅ | 至少 3 条 |
| §2 | commit 格式（`<type>(<scope>): <描述>` + type 列表） | ✅ | 至少 4 个 type |
| §3 | 互链规则（`← [返回]` footer + 豁免条件） | ✅ | 至少 3 条 |
| §4 | frontmatter（3 类 schema：module / question / story） | ⭕ | 至少 1 类 |
| §5 | G1-G6 评分维度（可简化） | ⭕ | 至少 5 个维度名 |
| §6 | 11 类扫描规则（可减） | ⭕ | 至少 5 类 |
| §7 | SPEC 分层（L0 / L1 / L1.5 关系） | ⭕ | 1 段即可 |
| **§8** | **新词检索映射表** | **✅** | **≥ 5 词条** |
| §9 | 3 skill × phase 引用契约 | ✅ | 至少 5 行 |

> **§8 是 3 skill 协同核心**——问答读取、沉淀写入、体检稽核都在 §8。**没有 §8 = 3 skill 失效**。

### 2.3 §8 词表最低配置（≥ 5 词）

```markdown
### 8. 新词检索映射表

| 主题词 | 主模块路径 | 专题路径 | 出现频次 |
|--------|-----------|---------|---------|
| <词 1> | <module>/<subdir>/ | <专题>/ 或 `-` | `-` |
| <词 2> | <module>/<subdir>/ | - | - |
| ...（至少 5 条）... |
```

### 2.4 README 最低配置（≥ 5 篇）

| 文件 | 必填性 | 最低内容 |
|------|:---:|----------|
| `<KB>/README.md`（总目录） | ✅ | 模块列表 + 链接到 §1 / §2 |
| `<KB>/01.<A>/README.md` | ✅ | 一句话定位 + 子目录列表 |
| `<KB>/02.<B>/README.md` | ✅ | 同上 |
| 每个主模块下至少 1 篇 topic README | ⭕ | H1 + 一段话 + 反向链 |

## 3. 启动 6 步验证清单

| 步 | 动作 | 验证命令（手动） |
|----|------|----------|
| 1 | 复制 §1 的 4 项工具到新 KB | `ls .claude/ORCHESTRATION.md && ls .claude/skills/` |
| 2 | 建 `<KB>/SPEC.md` 7 章节（§1/§2/§3/§8/§9 必填） | `wc -l SPEC.md` 应 ≥ 50 |
| 3 | 建 `<KB>/README.md` 总目录（链到所有主模块） | `grep -c "README\\|模块" README.md` 应 ≥ 2 |
| 4 | 建 ≥ 2 主模块 + ≥ 5 篇 README | `find . -name "README.md" \| wc -l` 应 ≥ 5 |
| 5 | §8 词表 ≥ 5 词 | 见下方词表稽核命令 |
| 6 | 跑 check-broken-links.py smoke test | `python scripts/check-broken-links.py` 应 0 断链 |

### 3.1 词表稽核命令

```bash
# §8 词条计数（自动）
awk '/^### 8\\./,/^### 9\\./' SPEC.md | grep -c "^|"
# 期望: ≥ 6（含 1 表头 + 5 词条）
```

### 3.2 链接完整性命令

```bash
# 全 KB 自检
python scripts/check-broken-links.py

# 单文件自检（推荐 commit 前跑）
python scripts/check-broken-links.py SPEC.md 03.<module>/README.md
# 期望: .md 断链: 0 / 目录断链: 0
```

## 4. 常见坑（5 项 + 修复）

| 坑 | 症状 | 修复 |
|----|------|------|
| **KB_DIR 未 export** | SKILL.md 中 `$KB_DIR/...` 路径失效 / broken link 爆炸 | export `KB_DIR=<KB>` 或 cd 到 KB 根跑命令（CWD fallback） |
| **ORCHESTRATION.md 路径错** | subagent silent failure（commit hash 无输出，subagent "完成"但 git log 无 commit） | ORCHESTRATION.md **必须**放在 `<KB>/.claude/` 下 |
| **§8 词表为空** | note-knowledge-qa Phase 2 答不出关键词；note-health Phase 1.15 无死链可稽核 = 静默失效 | 加 ≥ 5 词（见 §2.3） |
| **note-health Phase 1.14 仍硬编码 `12.interview/`** | 借 KB 时若面试题库不叫 `12.interview`，该扫描静默失效 | 见 §5 v3.x 改进路线 / 当前 workaround：把面试题库命名为 `12.interview/` |
| **主模块前缀跳号** | 体检 §6.7 命名一致性 P3 警告 | §1 命名约定强约束 `NN.<name>/` NN 必须连号（如 01/02/03 不能跳 04） |

## 5. 已知未完美项（v3.x 改进路线）

本仓库 3 skill 在借 KB 时仍存在一些硬编码盲点（本会话 2026-10-12 元问题 3 smoke test 发现）：

| 未完美项 | 影响 | 改进路径（待办） |
|---------|------|-----------------|
| **note-health Phase 1.14 仍硬编码 `12.interview/`** | 借 KB 时面试题库若不叫 `12.interview`，扫描静默失效 | SPEC.md 新增 §1.5 自描述「模块角色清单」，Phase 1.14 读 §1.5 找面试题库路径 |
| **note-knowledge-qa Phase 0 E/G 类型** | 若新 KB 没有「教育背景」区分，QA 流程略退化 | 简化 Phase 0：E/G 可选关 |
| **note-precipitation-planning Phase 6.10 反例清单 3 条** | 反例绑了 note 的 `12.interview/SPEC.md §准入判定`、`JVM 调优` 等具体路径 | 反例改为 placeholder |

**v3.x 计划**（尚未实施）：以上 3 项的反模式彻底 pointer 化。

**当前 workaround**：新 KB 命名面试题库叫 `12.interview/`、叙事模块叫 `13.story/`，跟 note 仓库对齐即可规避 80% 硬编码盲点。

## 6. Smoke test 验证（一键命令）

```bash
# 从新 KB 根跑
cd <新 KB>
export KB_DIR=$PWD

# 1. 链接完整性
python scripts/check-broken-links.py
# 期望: .md 断链: 0 / 目录断链: 0 / 总计: 0

# 2. §8 词条稽核（手动）
awk '/^### 8\\./,/^### 9\\./' SPEC.md | grep "^|"
# 期望: ≥ 5 词条
```

## 7. 沉淀第一个主题

启动验证通过后，按 note-precipitation-planning Phase 0-7 流程开始日常沉淀：

1. 用户问「X 应该沉淀到哪」 → 触发 Phase 0-7（含 Phase 6.10 自动写 §8）
2. 用户「扫一遍 KB」 → 触发 note-health（含 Phase 1.14 / 1.15）
3. 用户「X 是什么」/「出一题」 → 触发 note-knowledge-qa（读 §8 + 模块定位）

## 8. 实战 demo 对照

`D:/developer/IdeaProjects/note-temp/`（不入 note 仓库 git）是一份按本文 §2 骨架启动的简化 KB，仅供参考 demo：

| 项 | note-temp 实际 | 文档最低要求 | 通过 |
|---|----------------|--------------|:---:|
| 复制 4 工具 | ORCHESTRATION.md + 3 skill 全套 | §1 | ✅ |
| SPEC.md 章节 | §1/§2/§3/§8/§9 全有 + 简化 §4/§5/§6 | §2.2 | ✅ |
| §8 词条数 | 5（Cookie / Session / 分布式锁 / CAP / 共识） | §2.3 ≥5 | ✅ |
| 主模块数 | 3（01.java-basics / 02.distributed-systems / 03.interview） | §2.1 ≥2 | ✅ |
| README 总数 | 4（README + SPEC.md + 2 篇 topic） | §2.4 ≥5 | ⚠ |
| broken links | 0（smoke test 验证） | §3 步 6 | ✅ |

> **note-temp vs 文档差异**：README 总数 4 < 5（少 1 篇）。这不影响 3 skill 跑通，但**建议新 KB ≥ 5 篇以满足 §2.4**。
>
> **note-temp 重命名**（已修复 sub-agent B 残留未完美点）：Phase 1.14 的 `12.interview/` 硬编码导致 `03.interview/cookie-troubleshooting/README.md` 不在 Phase 1.14 扫描范围内。这是 note-temp 故意用 `03.interview/` 命名来验证 Phase 1.14 未完美点对借 KB 的实际影响。

## 9. 同源文档

- 元问题 3 通用化 plan：`C:\Users\wb043\.claude\plans\keen-foraging-eagle.md`
- 元问题 3 闭环 commit：`c5690f3` / `94078d2` / `d7914b7` / `32843af` / `fa927ef` / `49fc03f`
- 3 skill 主体 → SPEC.md 责任矩阵：`SPEC.md §9.1`（新 KB 启动时可参考简化版）
- 3 skill 协同协议：`SPEC.md §8.4`（新 KB 启动时按本指南同步落地 §8）
