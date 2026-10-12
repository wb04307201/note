---
name: note-health
description: Use when user wants to audit or evaluate the knowledge base — 结构体检 ("note 哪里需要优化" / "note 有哪些问题" / "扫一遍 note" / "体检") / 单篇质量评分 ("评价 note 质量" / "这篇文章质量怎么样" / "质量验收" / "评分") / 新文件基线 ("刚写的这篇质量如何" / "新写的 README 看看") — 单一分层体检:结构机械扫描 + leaf 判断式打分,全库穷举用 Workflow fan-out。 KB_DIR defaults to repo root, overridable via `NOTE_DIR` env var.
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

> **规则来源**：执行前必读 [`$KB_DIR/SPEC.md`](../../../SPEC.md) §5（G1-G6 通用评分维度）+ §6（11 类基础扫描规则）+ §7（SPEC 分层元规范）+ §8（新词检索映射表，Phase 1.15 稽核对象），并按需读各模块的 `<module>/SPEC.md`（如 `$KB_DIR/01.java-and-jvm/SPEC.md` 的 A 类维度、`$KB_DIR/12.interview/SPEC.md` §准入判定等强骨架规范）。模块结构通过 `find "$KB_DIR" -maxdepth 1 -type d` 运行时读取，不硬编码。
>
> **本 skill 自身重内容**（实现细节 / 阈值 / 误判识别）已下沉至本目录 `references/`，主文档只承载流程骨架 + 指针：
>
> | 重内容 | 落点 |
> |--------|------|
> | 11 类扫描执行步骤 + 自动化脚本 | `references/structural-checks.md` |
> | Leaf G1-G6 + A~G 维度打分 | `references/leaf-quality.md` |
> | 新文件 7 必选 + 3 可选结构基线 | `references/new-file-baseline.md` |
> | Phase 6 5 维评分（D1-D5） | `references/5-dim-rubric.md` |
> | Phase 7 拆分检测 | `references/split-detection.md` |
> | 主模块深度合理性扫描 | `references/main-module-depth.md` |
> | 主模块 ↔ 面试题映射 | `references/interview-main-mapping.md` |
> | Difficulty 自动校准 | `references/difficulty-calibration.md` |
>
> 操作层协议（subagent / git / peer session）见 [`$KB_DIR/.claude/ORCHESTRATION.md`](../../ORCHESTRATION.md)。

# note-health：note 知识库健康检查

对 `$KB_DIR/` 跑**单一分层体检**：结构机械扫描 + leaf 判断式打分，自底向上 8 相，输出统一 P0-P3 + 分批计划 + 逐篇评分表。重内容放在 `references/`，本文件只留决策骨架。

## When to Use

**Use when**（任一触发）：

- 用户问 `note 哪里需要优化` / `note 有哪些问题` / `扫一遍 note` / `体检` / `review note` → 触发**结构体检**（Phase 1-7 全跑）
- 用户问 `评价 note 质量` / `这篇文章质量怎么样` / `质量验收` / `评分` → 触发**单篇质量评分**（仅 Phase 2）
- 用户说 `刚写的这篇质量如何` / `新写的 README 看看` → 触发**新文件基线**（Phase 2 + `references/new-file-baseline.md`）

**Don't use when**：

- 用户问技术问题（"HashMap 原理"、"RAG 怎么用"）→ 走 `note-knowledge-qa`
- 用户问"X 应该沉淀到 note 什么位置" / "新增主题到 note" → 走 `note-precipitation-planning`
- 用户问"互链矩阵设计" / "全库反向链审计" → 走 `note-knowledge-qa`（它是 read-only 体检） — 或视为 `note-precipitation-planning` 的 Phase X 任务
- 用户问"我要加 14.llm-ops 模块" / "09 拆成两个" / "课程 lesson 批量导入" → 走 `note-precipitation-planning`（Build 行为）

## Phase 0：scope 判断（第一闸）

| scope | 触发例 | 行为 |
|---|---|---|
| **空 / 不存在**（2026-09-03 测试新增） | `$KB_DIR/` 不存在 / `find` 返回 0 | **直接返回**："KB_DIR 为空或不存在，无可体检内容"。不进入 Phase 1；不报错；不启动 workflow。 |
| 单篇 / 单目录 | "评价某模块下某篇" / "这篇质量怎么样" / "这篇新写的质量如何" | **只跑 Phase 2**：直接 Read + 按 `references/leaf-quality.md` 打分。**不启动 workflow**。**新文件**先读 `references/new-file-baseline.md` 拿到 7 必选 + 3 可选结构基线。 |
| 单模块 | "审一下某模块"（运行时读取 `find "$KB_DIR" -maxdepth 1 -type d`） | Phase 1 扫该模块 + Phase 2 小规模 fan-out（视 leaf 数手工切批，≤ 6 篇/批）。 |
| 全库（leaf ≤ 1000） | "note 哪里要优化" / "扫一遍 note" / "体检" | 完整 4 相；Phase 2 直接走「分层采样 + 优先级列表」策略（关键问题全评 + 各模块代表采样）。 |
| 全库（leaf > 1000） | 同上，但实时 `find "$KB_DIR" -name "*.md" \| wc -l` > 1000 | **触发 Phase 0.1 策略询问**：用 `AskUserQuestion` 让用户在「采样」/「穷举」/「混合」三选一，默认采样，**不再静默切换**。 |

**空 KB_DIR 检测**（2026-09-03 测试新增）：

```bash
# Phase 0 启动前必跑（< 1 秒）
KB_DIR="${NOTE_DIR:-$(git rev-parse --show-toplevel)}"
if [ ! -d "$KB_DIR" ] || [ -z "$(find "$KB_DIR" -maxdepth 5 -name "*.md" -print -quit 2>/dev/null)" ]; then
  echo "⚠️  KB_DIR ($KB_DIR) 为空或不存在，无可体检内容"
  echo "    提示：检查 NOTE_DIR 环境变量 / .claude/knowledge-base.config.json 配置"
  exit 0
fi
```

**原则**：单篇请求绝不启动重型机器；leaf 数 < 10 直接手工打分，不开 workflow。

> **全库策略**（leaf > 50）：
>
> - **优先级批**：浅 README（< 50 行）+ 无回链 + 无 frontmatter + 全部 broken link 来源（必评）
> - **采样批**：每主模块随机 3-5 篇代表 leaf
> - **leaf ≤ 1000** → 直接走采样（无需询问）
> - **leaf > 1000** → **触发 Phase 0.1 策略询问**（让用户显式选择）
> - leaf 数 ≤ 50 → 按单模块（主循环手工切批）

### Phase 0.1：全库规模触发的策略询问（leaf > 1000）

> 2026-08-23 新增：当 Phase 0 判 scope = 全库且实时 `find "$KB_DIR" -name "*.md" | wc -l` > 1000 时，**必须**用 `AskUserQuestion` 让用户在 3 种策略中显式选择，**不再静默切换**为采样。

**触发前先算 leaf 数**：

```bash
LEAF_COUNT=$(find "$KB_DIR" -name "*.md" | wc -l)
[ "$LEAF_COUNT" -gt 1000 ] && echo "全库 leaf = $LEAF_COUNT，超阈值，触发 Phase 0.1 询问"
```

**询问选项**（默认 Recommended = 选项 A 采样）：

| 选项 | token 估算 | 时长 | 适用场景 |
|------|-----------|------|----------|
| **A. 分层采样 + 优先级列表** (Recommended) | ~200k | 30-60min | 日常 review / 快速定位主要问题 |
| **B. 全库 fan-out 穷举** | ~3M | 4-6h | release 前最终审计 / 用户明确要求穷举 |
| **C. 混合：采样 + 高风险模块下钻** | ~300-500k | 1-2h | 平衡成本与覆盖率，先采样定位高风险区再 fan-out 补全 |

**选项触发判定**（按用户原话 / 上下文匹配）：

| 选项 | 触发信号 |
|------|----------|
| A 采样（默认） | "扫一遍" / "体检" / "哪里要优化" 等日常表述 |
| B 穷举 | "穷举" / "全部" / "每一篇" / "all" / "exhaustive" / release 前最终审计 |
| C 混合 | "重点模块下钻" / "高风险区补全" / "采样后补全" |

**询问失败降级**：

- 用户中断 / 跳过 → 默认走选项 A 采样（最低风险）
- `AskUserQuestion` 工具不可用 → 同上，log 一条「策略询问跳过，降级为默认采样」

**3 条硬性原则**：

- **询问必须在 Phase 1 启动前完成**，否则已启动的扫描会浪费 token（subagent 不能调 AskUserQuestion，工具不可用）
- **询问本身不消耗扫描成本**——`AskUserQuestion` 是对话层动作，不进入 `.health-tmp`
- **询问结果写到 report 头部**——Phase 4 输出必须含「策略选择：<选项>」一行，让用户事后能验证实际跑了哪个策略

> ⚠️ **边缘 case：兄弟相对路径**（如新增 `polymorphism/README.md`）：兄弟章节用 `polymorphism/README.md`（相对路径）形式链接近似安全，但 markdown 严格按相对路径解析，**从 `inner-class/README.md` 应解析到 `inner-class/polymorphism/README.md`**（不存在）。Phase 1 §6 broken-links 扫描命中后需人工二次确认「同目录」vs「跨目录」归属，Phase 4 综合报告必须标 `[同目录-边缘]` 而非纯 `[真错]`。

**新文件专属入口**：当用户问的是"评价一个新沉淀的文件 / 这篇新写的质量如何"，Phase 2 在打分前必须先读 `references/new-file-baseline.md` 拿到 7 必选 + 3 可选结构模板 + 快改/深耕写作模式，作为结构基线；再用 `references/leaf-quality.md` 打分。两者结合判断"是否符合新文件基线 + 是否达到 leaf 质量门槛"。

> 判定为"新文件"的启发：用户提到"刚写的 / 新沉淀的 / 这次新加的 / 初稿"，或 git 近期新增（`git log --since 近几天 --diff-filter=A`）。
>
> 完整新文件基线与 leaf 评分维度均为 references 层内容，**详见 `references/new-file-baseline.md` + `references/leaf-quality.md`**。

## 执行引擎：自底向上 8 相

> **底层规则与实现细节已外置**（11 类扫描执行步骤、5 维评分、拆分判定、leaf 打分等均落到 `references/` 子文件）。本节只承载**流程骨架 + 关键 Phase 的特殊处理约束**。

### Phase 1 — 结构扫描（主循环内，便贵）

> 执行前先建临时目录：`mkdir -p "$KB_DIR/.health-tmp"`
>
> 完整 11 类扫描的执行步骤、阈值、误判识别、自动化脚本均见 [`references/structural-checks.md`](references/structural-checks.md)。

**默认应跑的子阶段**（按时间线排）：

| 子阶段 | 来源 | 落地 |
|--------|------|------|
| 1.1 frontmatter 覆盖 | SPEC §6.1 | structural-checks.md |
| 1.2 orphan 目录 | SPEC §6.4 | structural-checks.md |
| 1.3 孤链（双口径：.md + 目录） | SPEC §6.3 | structural-checks.md |
| 1.4 README 总目录章节锚点 | SPEC §3 互链 | structural-checks.md |
| 1.5 数字一致性 | SPEC §6.1 | structural-checks.md |
| 1.6 单向链接扫描 | G4 互链 | structural-checks.md |
| 1.7 系列完整性 | SPEC §6.9 | structural-checks.md |
| 1.8 归属合理性 | SPEC §6.10 | structural-checks.md |
| 1.9 合并检测 | SPEC §6.11 | structural-checks.md |
| 1.10 PNG / 脚本残留 | SPEC §6.8 | structural-checks.md |
| 1.11 H1/H2 标题规范 | SPEC §6.2 | structural-checks.md |
| 1.12 命名一致性 | SPEC §6.7 | structural-checks.md |
| **1.13 弱关联扫描（v2 正文内链）** | Mistake 20 | `scripts/weak-link-scan.py` |
| **1.14 准入判定扫描** | `12.interview/SPEC.md §准入判定` | 本节下方 + structural-checks.md §9 |
| **1.15 关键词映射表稽核** | `SPEC.md §8` | 本节下方 |

**所有大输出重定向到文件**（`> "$KB_DIR/.health-tmp/scan-<phase>-<date>.txt"`），不堆进对话。Phase 1 不调 workflow。

> 详细 11 类扫描规则的执行步骤、误判识别、自动化脚本、输出落盘格式，均见 [`references/structural-checks.md`](references/structural-checks.md)。

> **🆕 2026-10-12 起**：准入判定扫描（Phase 1.14）新增 —— 对 12.interview 跑判定词库（**详见 [`$KB_DIR/12.interview/SPEC.md` §准入判定](../../../12.interview/SPEC.md)**），命中 4 类不适合样本的标记为 `P3 misplaced-warning`。
>
> **强约束**：
>
> - 本扫描**只标记，不动手**——移除执行必须由用户决策
> - 实际移除走 `note-precipitation-planning` Phase 6（迁移到正确主模块 + 加反向链 + 12.interview 旧文件保留 `→ [已迁移到:]` 跳转说明）
> - 9 类关键词库在 `references/structural-checks.md` §9（避免在 note-health 内另起一份重复规则）
>
> **来源**（2026-10-12）：沉淀 Maven release/source/target 时，`note-precipitation-planning` 把「高频踩坑」误判为「高频面试」。教训：准入判定必须有显式规则（沉淀 skill 之前散落的 Phase 2/3 信号不够精准），并由健康体检 skill 自动扫描兜底。

> **🆕 2026-10-12 起**：Phase 1.15 `keywords_mapping_validation` —— 扫 [`$KB_DIR/SPEC.md` §8](../../../SPEC.md) 所有「主题词 → 路径」映射：
>
> 1. 解析 §8 表格中**主模块路径**与 **12.interview 路径**两列（`-` / `(聚合)` 跳过）
> 2. 对每个路径 `os.path.exists(target_abs)` 校验
> 3. 死链标 P3 `misplaced-warning`（与 Phase 1.14 同级），附在体检报告后
> 4. **不动手修复**（按用户决策走 `note-precipitation-planning` Phase 6 沉淀流程，避免体检越界改 §8）
>
> **为何需要**：§8 表由「问答 skill 命中 + 沉淀 skill 补全」共建，可能因主模块结构重构产生死链；体检稽核是闭环兜底。完整词表与字段语义见 [`$KB_DIR/SPEC.md` §8](../../../SPEC.md)。

**关联强度扫描脚本**（Phase 1.13 v2 正文内链版，外置同目录 `scripts/weak-link-scan.py`）：

> 完整四步降噪（切代码块 / 排除表格 / 页脚截断 / 排除祖先回链）+ H1 关键词检查详见 [`scripts/weak-link-scan.py`](scripts/weak-link-scan.py) docstring。风格基线 `scripts/check-broken-links.py`。
>
> 用法：
>
> ```bash
> python scripts/weak-link-scan.py --dir "$KB_DIR" --output "$KB_DIR/.health-tmp/weak-link-<date>.txt"
> ```
>
> 输出：弱关联列表 → 报告 P2 项 + 推荐「删除或补语义描述」；不输出"强关联"（避免噪音）；**页脚/表格内的导航互链永不判弱关联**——它们是 G4 互链要求的合规载体，语义关联由正文承载。

### Phase 2 — Leaf 质量 fan-out

- **单篇 / 单目录 / 单模块**：直接 Read + 按 `references/leaf-quality.md` 的 G1–G6 + A~G 维度打分，**不开 workflow**。
- **全库**：先用以下命令枚举 leaf 文件清单，再把清单通过 `args.files` 传给 workflow：

```bash
find "$KB_DIR" -name "*.md" | python -c "import sys,os; [print(l.strip()) for l in sys.stdin if l.count('/')>=3]"
```

> 注：Windows 环境用 `python`（3.13+），macOS/Linux 也可用 `python3`。脚本应兼容两者。

然后调用 `references/health-workflow.js`（`args={files:[...], batchSize:6}`）。脚本按 ~6 篇/批 fan-out，每 agent 按 `references/leaf-quality.md` 打分并返回 `{file, moduleClass, total, maxScore, grade, findings}`。

**⚠️ Workflow 空结果降级**：如果 workflow 返回 `scored.length === 0`（常见原因：harness 调度失败、agent 全返回空），**不要卡住**，立即降级为手工 dispatch：
1. 把 files 清单按 ~6 篇/批切分
2. 用 `Agent` 工具逐批 dispatch（每批一个 agent），prompt 同 workflow 内的 agent prompt
3. 收集各 agent 返回的 JSON 结果，合并为 scored[]
4. 继续 Phase 3 上卷

降级时 log 一条：`workflow 返回空，降级为手工 dispatch N 批`。

**断点续跑**：脚本本身不做状态持久化；如需续跑，由调用方给 Workflow 工具传 `resumeFromRunId`，让 harness 从上次中断的批次开始。本 skill 不写任何续跑逻辑。

### Phase 3 — 逐层上卷

> 数据来源：Phase 2 的 workflow 返回值 scored[]（全库）或直接打分结果（单篇/单模块）。逐层上卷 = 在主循环内对 scored[] 按 topic 目录 / module 分组聚合，无需重读正文。

把 leaf findings 逐层上卷：
- **leaf** → 同 topic 兄弟互链 / 系列完整性（来自 Phase 1）
- **topic** → 模块级均分 / README 索引（来自 Phase 1）
- **module** → 跨模块数字 / 架构一致性（来自 Phase 1 跨模块扫描）
- **repo** → 总目录 / CONTRIBUTING / frontmatter 规范

### Phase 4 — 综合输出

把结构 findings（Phase 1）+ 质量 findings（Phase 2/3）合并成统一报告，写到 `.health-tmp/report-<date>.md`。详见下文「Output Format」。

### Phase 5 — 修复后验证

> 完整验证协议（commit 落地 / 工作树干净 / 内容质量 / 无新断链 + author 一致性 + subagent 收尾 commit）见 [`$KB_DIR/.claude/ORCHESTRATION.md` §1-§2](../../ORCHESTRATION.md)。本节只列简版步骤与失败处置。
>
> **简版步骤**（执行 Batch 1+ 修复后必跑，确保修复实际落地而非"报告完成但 git 没 commit"）：
>
> 1. **commit 落地确认**：`git log --oneline -N` 确认本轮每条修复 commit 都有真实 hash
> 2. **工作树干净**：`git status --short` 应输出空
> 3. **内容质量达标**：`wc -l FILE` 扩充后文件行数 ≥ 目标值
> 4. **无新断链**：对修改文件跑 `python .github/workflows/scripts/check-broken-links.py <file>` 校验
> 5. **author 验证**：`git log -1 --format="%an <%ae>" -- FILE` 输出必含主账号（`吴博 <wubo_aaa@163.com>`）
>
> **失败处置**：
>
> - commit hash 缺失 → 立即补 commit
> - 工作树有未提交修改 → 决定 commit 或 discard
> - author 错误 → 用 ORCHESTRATION §1 给出的 rebase 修正
> - broken links → 立即修复，不要累积
> - subagent 报告完成但 `git log` 无新 commit → 立即 abort + 收尾 commit（**不信任 subagent 自我报告**）

### Phase 6 — 5 维评分

> 5 维度（D1 深度 / D2 广度 / D3 频次 / D4 追问空间 / D5 反直觉）定义、阈值（≥ 7 保留 / 4-6 灰色 / ≤ 3 迁出）、与 difficulty 校准衔接、4 个实战教训（标题预筛 false positive 70% / difficulty 偏乐观 / 分批 dispatch / 灰色地带处置），**详见 [`references/5-dim-rubric.md`](references/5-dim-rubric.md)**。
>
> 何时读：用户问"X 题是否过于简单" / "split-hairs 哪些该迁出"时必读。

### Phase 7 — 拆分检测

> 判定信号（覆盖 ≥ 3 互不相关子主题 / 标题宽泛 / 子主题各自合格但合并违反）、拆分后规则（每个子主题 → 独立 README.md + frontmatter）、验证标准（commit hash / git status / 行数 / broken links），**详见 [`references/split-detection.md`](references/split-detection.md)**。
>
> 何时读：体检发现文件覆盖 ≥ 3 个互不相关子主题 / 标题宽泛 / 违反单点定位时必读。

## Output Format（统一报告骨架）

合并两套旧 skill 的输出：

### 1. 分批执行计划（P0-P3 + 机械/判断分类）

| 优先级 | 类别 | 含义 | 例 |
|---|---|---|---|
| P0 | 机械 | 必修，脚本可全自动改 | frontmatter 缺失、orphan 目录、孤链 |
| P0 | 判断 | 必修，需人审 | 与规范冲突的核心表述 |
| P1 | 机械 | 应修，批量可改 | README 章节锚点漂移 |
| P1 | 判断 | 应修，需重写 | 系列不完整、断章 |
| P2 | 机械 | 可修 | dead image 引用、过期链接 |
| P2 | 判断 | 可修 | 内容深度不够、可读性差 |
| P3 | 任意 | 锦上添花 | 亮点保留 / 未来沉淀方向 / 准入判定误归类 / §8 词表死链 |

**分批执行计划表**（按 commit 批次组织）：

```
Batch 1 (P0 机械): <N 项> — 一条 commit 全部搞定
Batch 2 (P0 判断): <N 项> — 每项一条 commit
Batch 3 (P1 机械 + 判断): <N 项>
Batch 4 (P2): <N 项> — 集中改
Batch 5 (P3 / 亮点): 不动或单列
```

### 2. 逐篇评分表（来自 leaf-quality）

| 文件 | moduleClass | 总分 / 满分 | 等级 | 主要 findings |
|---|---|---|---|---|

### 3. 亮点（保留 / 不动）

列出不该改的优秀片段，作为后续沉淀的范例。

## Phase 8 — 链接完整性强制校验

> **触发条件**：任何"全库"或"单模块"scope 的体检，**Phase 1 启动前必跑**。
>
> **目的**：避免"subagent 自己写扫描脚本"导致扫描口径漂移——**统一入口是 [`check-broken-links.py`](../../../workflows/scripts/check-broken-links.py)**，subagent 不应自创扫描脚本。

**执行命令**：

```bash
# 全库扫描
python "$KB_DIR/.github/workflows/scripts/check-broken-links.py"

# 或单模块
python "$KB_DIR/.github/workflows/scripts/check-broken-links.py" --module 09.ai-applications
```

**接受标准**：

| 检查项 | 通过条件 |
|--------|---------|
| 断链数 | **= 0**（CI 月度 cron 模式）|
| 断链数 | **≤ 5**（单模块体检，允许边界 case）|
| 双口径 | .md 链接 + ](dir/) 目录链接 均扫描 |

**断链数 > 0 时处置**：

| 情况 | 处置 |
|------|------|
| 全库扫描 | **Phase 1 不启动**，先把断链修完再跑体检 |
| 单模块扫描 | 把断链列入 Phase 4 P0 必修项，与 Phase 2 评分同步修复 |
| 边界 case（如 README 同目录）| 标 `[同目录-边缘]`，人工二次确认 |

> **与 note-knowledge-qa §3.5 的区别**：体检时（结构维度，全库扫描，失败时 Phase 1 拒绝启动） vs 检索时（QA 维度，单次检索的目标文件，失败时在回答里标注"路径待修复"）。
>
> **反直觉 5**："subagent 自己写的扫描脚本更灵活" —— 灵活 ≠ 一致。Session 6 教训：subagent 自己写了 `scan-broken-links.py`，但口径与 Phase 1.6 略有差异，导致需要二次校验。

## Common Mistakes

**不重复正文，写指针**：

- **结构类**问题（frontmatter、orphan、孤链、目录结构）：见 [`references/structural-checks.md`](references/structural-checks.md)。
- **内容类**问题（深度、可读性、系列完整性）：见 [`references/leaf-quality.md`](references/leaf-quality.md)。
- **新文件结构基线**（10 段模板 + 快改/深耕模式）：见 [`references/new-file-baseline.md`](references/new-file-baseline.md)。
- **5 维评分 / 拆分检测 / 弱关联算法 / 主模块深度 / difficulty 校准**：见 [`references/5-dim-rubric.md`](references/5-dim-rubric.md) / [`split-detection.md`](references/split-detection.md) / [`scripts/weak-link-scan.py`](scripts/weak-link-scan.py) / [`main-module-depth.md`](references/main-module-depth.md) / [`difficulty-calibration.md`](references/difficulty-calibration.md)。
- **操作层协议**（subagent / git / peer session）：见 [`$KB_DIR/.claude/ORCHESTRATION.md`](../../ORCHESTRATION.md)。
- **模块专属规则**（如 12.interview 准入判定）：见对应 `<module>/SPEC.md`。

执行本 skill 时遇到常见错误模式先查 references / `<module>/SPEC.md` / ORCHESTRATION，再决定是否纳入 P0/P1。

## Real-World Impact

| scope | 输出形式 | token / 时长 |
|-------|---------|------------|
| 单篇 / 单目录 | `references/leaf-quality.md` 打分表 + findings 列表 | ~10k tokens，~1 分钟 |
| 单模块（≤50 leaf） | Phase 1 + Phase 2 手工切批 | ~50k tokens，~10 分钟 |
| 全库（leaf ≤ 1000） | Phase 1 + Phase 2 sampling fan-out | ~200k tokens，30-60 分钟 |
| 全库（leaf > 1000） | 触发 Phase 0.1 策略询问，默认 A 采样 | ~300k tokens，1-2 小时 |
| 全库穷举（B 选项） | Phase 1-7 全跑 + Workflow fan-out | ~3M tokens，4-6 小时（release 前审计） |

**典型用户场景 + 预期产出**（不绑具体模块路径；模块名由 KB 运行时 `find` 决定）：

- "扫一遍 KB 看看哪里要优化" → 全库体检 → P0-P3 分批报告 + 逐篇评分表
- "评价某模块/某篇/README.md 这篇质量怎么样" → 单篇质量验收 → 评分 + findings
- "这篇新写的 README 看看" → 新文件基线 → 7 必选 + 3 可选结构检查
- "KB 哪里要优化" → 体检 → 同上

**避免的失败**：

- ❌ 不确认 KB_DIR 就跑全库（可能数小时扫描无意义目录）
- ❌ 跳过 Phase 8 链接校验（230 处断链教训）
- ❌ 漏掉 frontmatter `difficulty` 与 5-dim 一致性（19 处偏差教训）

## Quick Checklist（执行前必过）

- [ ] 确认 KB_DIR 指向正确知识库（默认仓库根，支持 NOTE_DIR 覆盖）
- [ ] 确认 scope（单篇 / 单模块 / 全库），全库 > 1000 leaf 时走 Phase 0.1 策略询问
- [ ] 单篇质量评分先读 `references/new-file-baseline.md` 拿结构基线
- [ ] Phase 1 结构扫描结果落 `$KB_DIR/.health-tmp/scan-1-<date>.txt`（保留可复查证据）
- [ ] Phase 8 链接校验单独跑：`python $KB_DIR/.github/workflows/scripts/check-broken-links.py`
- [ ] 输出报告含「策略选择：<选项>」一行（事后可验证）

**执行后验证**：

- [ ] `git log --oneline -N` 确认每条修复 commit 都有真实 hash
- [ ] `git status --short` 工作树干净
- [ ] `wc -l FILE` 扩充后文件行数达标
- [ ] 重新跑 `check-broken-links.py` 无新断链

## 调用示例

```
# 全库体检（leaf ≤ 1000）
"扫一遍 KB 看看哪里要优化"
→ Phase 0: 全库（leaf ≤ 1000），直接走采样
→ Phase 1: 跑 structural-checks.md 扫描，结果落 $KB_DIR/.health-tmp/scan-1-<date>.txt
→ Phase 1.14 + 1.15: 准入判定扫描 + §8 词表稽核（只标记 P3，不动手）
→ Phase 2: find + python 枚举 leaf，调 health-workflow.js（args.files=...，batchSize=6）
→ Phase 3: 上卷
→ Phase 4: 写 $KB_DIR/.health-tmp/report-<date>.md，header 含「策略选择：A 采样」

# 全库体检（leaf > 1000）
"扫一遍 KB 看看哪里要优化"
→ Phase 0: 全库（leaf > 1000），触发 Phase 0.1 策略询问
→ AskUserQuestion: 用户选 A/B/C（默认 A）
→ Phase 1-4 同上，header 含「策略选择：<选项>」

# 单篇质量验收
"评价某模块/某篇/README.md 这篇质量怎么样"
→ Phase 0: 单篇
→ Phase 2: 直接 Read + leaf-quality.md 打分，不开 workflow
→ 直接在对话里给评分表 + findings
```
