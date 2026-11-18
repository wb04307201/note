# 规则引擎 + SPEC 生命周期(方案 2 + Tier 1)Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把已验证的"规则命中→预案→综合裁决"判定模型从测试文件迁进 3 skill 正式机制(rule-catalog + Phase 3/4 三段式 + SPEC §1.6 谓词 + SPEC-LIFECYCLE),并以重建冻结的 R0 基线证明 IT 行为零回退。

**Architecture:** 规则语义单源进 `rule-catalog.md`(skill references 层),KB 侧只声明谓词(`SPEC.md §1.6`,默认值按角色推导);precipitation Phase 3/4 改三段式输出(命中表→预案集→综合裁决带溯源链);SPEC 生命周期四问收编进 `SPEC-LIFECYCLE.md`(收编不复制);R0 十例基线重建入库、签认冻结后做回归对照。

**Tech Stack:** Markdown(知识/规范文档)+ git(conventional commits)+ Python(`check-broken-links.py` / `yaml.safe_load`)+ bash(Windows git bash)。

**Spec:** `.claude/skills/rule-engine-design.md`(设计稿 v2,已批准;executors 必须连同本计划一起读——内容级决策在 spec,本计划只钉位置/接口/验证)

## Global Constraints

- commit 格式:`<type>(<scope>): <描述>`,消息末尾 `Co-Authored-By: Claude Code <noreply@anthropic.com>`;**数字不虚报**(commit-msg hook 对篇/处/个/项/次 警告)
- 5 层防护链不破坏:每个 commit 前 staged `.md` 必过 `python .github/workflows/scripts/check-broken-links.py <files>`
- 改任何 `SKILL.md` 后必跑 Safeguards 三查:YAML frontmatter 解析(`yaml.safe_load`)、章节锚点审计(`grep -rn 'Phase [0-9]'`)、派发 smoke(3 类原话路由)
- Anti-goals(出现即失败):规则**语义**两处维护 / IT 最终方案改变 / 泛化稀释特化 / 规则全文复制进 KB SPEC
- 链接唯一可靠标准 = 目标文件真实存在(`os.path.isfile`);`.claude/skills/` 在 pre-commit 排除名单内,**不依赖 hook 兜底,每 task 自跑链接校验**
- 测试 KB `D:/developer/IdeaProjects/note-kb-test/`(coffee/invest/fitness)全程 **read-only**
- 单一来源(SPEC §9.2):规则语义 = skill references;规则实例/谓词 = KB SPEC

## Review Focus

1. **SKILL.md 改写后 YAML frontmatter 损坏**(skill 加载失败,无报错只有静默失效)→ Task 4 Step 6 YAML 解析 + Task 6 复跑
2. **新增互链断链**(rule-catalog/SPEC-LIFECYCLE/§1.6 的相对路径层级深,极易写错)→ Task 3 Step 5 / Task 5 Step 4 的 `os.path.isfile` 逐链核对
3. **三段式悄悄改变 IT 决策语义**(R0 漂移)→ Task 6 Step 1 R0 十例对照冻结基线,最终方案 10/10 一致才算过
4. **谓词默认值方向错**(无角色 KB 误双层 / note KB 丢双层)→ Task 6 Step 2 I2 探针(无角色端)+ R0 探针 P1(note 端)
5. **规则语义双处维护**(catalog 全文被复制回 SKILL)→ Task 4 Step 7 grep 核查:SKILL Phase 3/4 不再含 R7-R10/R23/R25 语义正文,仅 R# 引用

---

## File Structure

| 文件 | 动作 | 职责 |
|------|------|------|
| `.claude/skills/cross-domain-{generality-test-design,generality-report,evidence,rule-trace}.md` | commit(Task 1) | 测试产物落库(已存在,未提交) |
| `.claude/skills/rule-engine-design.md` + `rule-engine-plan.md` | commit(Task 1) | 设计 + 计划落库 |
| `.claude/skills/cross-domain-r0-baseline.md` | Create(Task 2) | R0 十例基线(P1-P10),签认后冻结 |
| `.claude/skills/note-precipitation-planning/references/rule-catalog.md` | Create(Task 3) | R1-R25 单源:登记 + 覆盖/组合序 + 谓词默认值 |
| `SPEC.md` | Modify(Task 3/5) | §1.6 谓词层新增;§9.1 加 2 行引用契约 |
| `.claude/skills/note-precipitation-planning/SKILL.md` | Modify(Task 4) | Phase 3/4 三段式 + R# 标注 + V4/V5 |
| `.claude/skills/note-precipitation-planning/references/SPEC-LIFECYCLE.md` | Create(Task 5) | SPEC 生命周期四问(收编不复制) |
| `.claude/STARTUP-NEW-KB.md` | Modify(Task 5) | §2.2 加 §1.6 行 + SPEC-LIFECYCLE 指针 |
| `.claude/skills/note-precipitation-planning/references/MODULE-CREATION-SPEC.md` | Modify(Task 5) | Step 2 指针 SPEC-LIFECYCLE |
| `.claude/skills/note-knowledge-qa/SKILL.md` | Modify(Task 6) | V3 学习路径模板域中立化 |

---

### Task 1: Phase B 存量落库

**Files:**
- Commit: `.claude/skills/cross-domain-*.md`(4 个未跟踪)+ 6 个已修改文件(STARTUP-NEW-KB / 5-dim-rubric / leaf-quality / new-file-baseline / qa SKILL / precipitation SKILL)
- Commit: `.claude/skills/rule-engine-design.md` + `rule-engine-plan.md`

**Interfaces:**
- Consumes: 工作区现有未提交产出(Phase B P1 修复 + 测试 4 件)
- Produces: 干净工作树(后续 task 的 `git diff --name-only HEAD` 只含本 task 改动)

- [ ] **Step 1: 确认工作区状态符合预期**

Run: `git status --short`
Expected: 恰好 6 个 ` M` + 6 个 `??`(4 个 cross-domain + rule-engine-design + rule-engine-plan)。多出的文件 → 停下询问。

- [ ] **Step 2: commit 测试产物(4 件)**

```bash
git add .claude/skills/cross-domain-generality-test-design.md .claude/skills/cross-domain-generality-report.md .claude/skills/cross-domain-evidence.md .claude/skills/cross-domain-rule-trace.md
git commit -m "docs(note): 归档跨域通用性测试产物(设计/报告/证据/规则溯源)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

- [ ] **Step 3: commit Phase B P1 修复(6 文件)**

```bash
git add .claude/STARTUP-NEW-KB.md .claude/skills/note-health/references/5-dim-rubric.md .claude/skills/note-health/references/leaf-quality.md .claude/skills/note-health/references/new-file-baseline.md .claude/skills/note-knowledge-qa/SKILL.md .claude/skills/note-precipitation-planning/SKILL.md
git commit -m "fix(note): 落地跨域测试 P1 修复(V1/S1/K3/K2/V2/K4)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

- [ ] **Step 4: commit 设计 + 计划文档**

```bash
git add .claude/skills/rule-engine-design.md .claude/skills/rule-engine-plan.md
git commit -m "docs(note): 归档规则引擎设计与实施计划

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

- [ ] **Step 5: 验证工作树干净 + 3 commit 落地**

Run: `git status --short && git log --oneline -3`
Expected: status 空;log 前 3 行 = 上面 3 个 commit。

---

### Task 2: R0 基线重建 + 签认冻结(含用户 GATE)

**Files:**
- Create: `.claude/skills/cross-domain-r0-baseline.md`

**Interfaces:**
- Consumes: `.claude/skills/test-scenarios.md`(66 场景母集)· `cross-domain-generality-report.md` §2 R0 结论行
- Produces: `cross-domain-r0-baseline.md`(探针编号 **P1-P10**,与规则 R1-R25 命名隔离;每探针含:问法 / 决策类 / 期望最终方案 / 依据规则 R#)——Task 6 回归对照的唯一基线

**R0 结论行对齐目标**(报告 §2 原文,重建探针的决策类必须逐一对齐):
`R1 双层 / R2 拆分 / R3 08 主模块 / R4 拒绝 / R5 13.story / R6-R8 QA 三型 / R9 G1-G6+E 类 / R10 Phase 0.1 询问`

- [ ] **Step 1: 确认母集存在**

Run: `ls .claude/skills/test-scenarios.md && grep -c "^##" .claude/skills/test-scenarios.md`
Expected: 文件存在;章节数 > 0(66 场景母集)。不存在 → 停下询问(不可凭空造问法)。

- [ ] **Step 2: 写 `cross-domain-r0-baseline.md` 初稿**

结构(header 仿 cross-domain 系列):`Status: 待签认` + 冻结说明 + P1-P10 表。探针清单(**决策类固定,问法从母集采样可改写**):

| 探针 | 决策类 | 期望最终方案(方案级冻结) |
|------|--------|--------------------------|
| P1 | 双层 | 双层;位置 = interview + depth 两版互链;2 commit |
| P2 | 拆分(多主题输入) | 拆为 single-topic 多文件(**只验决策结果**) |
| P3 | 位置决策 | 落 08.ai-applications 主模块 |
| P4 | 拒绝(一句话讲清类) | 不沉淀(**只验决策结果**) |
| P5 | 叙事 | 13.story 三层联动(过 §3.5 准入) |
| P6 | QA A 型 | A 型:检索 ≥3 篇 + 📚 知识来源表 |
| P7 | QA B 型 | B 型:题目 + 三层答案 + 陷阱表 + 话术模板 |
| P8 | QA C 型 | C 型:方案对比表 + 推荐 + 设计点 |
| P9 | health 评分 | G1-G6 通用维 + 模块专属 E 类维生效 |
| P10 | Phase 0.1 分流 | 修复类意图 → 直接修复,不走沉淀规划 |

P1-P5 每条加"依据规则"列(R4-R10/R23/R25 按实际);P6-P10 注明"非 Phase 3/4 决策,无溯源链要求"(§5.2 裁决)。

- [ ] **Step 3: 链接校验**

Run: `python .github/workflows/scripts/check-broken-links.py .claude/skills/cross-domain-r0-baseline.md`
Expected: 总计 0。

- [ ] **Step 4: 【GATE】交用户签认**

把 P1-P10 表呈现给用户。**等待用户确认或修改**;按反馈改初稿。未获签认不得进入 Step 5。

- [ ] **Step 5: 冻结 + commit**

改 header:`Status: 已签认冻结(YYYY-MM-DD)`;补签认行。

```bash
git add .claude/skills/cross-domain-r0-baseline.md
git commit -m "docs(note): 新增 R0 回归基线(签认冻结)

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 3: rule-catalog.md + SPEC.md §1.6 谓词层

**Files:**
- Create: `.claude/skills/note-precipitation-planning/references/rule-catalog.md`
- Modify: `SPEC.md`(`### 2. commit 格式` 标题行之前插入 §1.6;§9.1 责任矩阵表加 1 行)

**Interfaces:**
- Consumes: `cross-domain-rule-trace.md` Part 1A(R1-R25 原文)+ 设计 §5.1(Part 2/3 内容)
- Produces: `rule-catalog.md` 三部分锚点——`Part 1 规则登记` / `Part 2 覆盖与组合序` / `Part 3 适用性谓词与默认值`;`SPEC.md §1.6` 表格。Task 4 消费 R# 编号与 Part 2 裁决序

- [ ] **Step 1: 写 `rule-catalog.md` Part 1(规则登记)**

R1-R25 全量登记,每条 schema:`规则一句话 / 来源 phase / 适用性谓词(如适用) / 预案片段(仅下列 11 条) / 语义位置`。**分级(本计划钉死)**:
- **完整预案片段**(形态/位置/commit 数/理由):R4、R5、R6、R7、R8、R9、R10、R11、R23、R24、R25
- **仅登记**(一行摘要 + `语义见 SKILL <phase>,流程暂不改`):R1、R2、R3、R12、R13-R22(其中 R13-R21 标注"QA/health,流程暂不改")
- 规则原文从 `cross-domain-rule-trace.md` Part 1A 迁入,**域中立**(coffee/投资实例不进 catalog,留测试文件)

- [ ] **Step 2: 写 Part 2 + Part 3**

Part 2 内容**从设计 §5.1 Part 2 原样迁入**(覆盖:R23⊃R8/R9、R10⊃R8、R2 例外;组合:R11+R8、R11+R5、R25 约束;冲突未定义 → 记「规则缺口」)。
Part 3 表格**从设计 §5.1 Part 3 原样迁入**(6 谓词 × 读取处 × 默认值列;含默认语义说明行"无 §1.6 的 KB 按默认语义")。

- [ ] **Step 3: 写 SPEC.md §1.6**

插入位置:`### 2. commit 标题`之前(**注意 SPEC.md 存在历史遗留的重复 `### 1.5.` 标题,§1.6 插在第二个 §1.5 块末尾与 §2 之间;重复 §1.5 不在本计划修复**)。标题:`### 1.6. KB 谓词定义(规则引擎输入)`,内容 = 设计 §5.3 模板 + note KB 回填 4 行:

| 谓词 | 本 KB 定义 | 影响规则 |
|------|-----------|---------|
| 考试价值高 | 12.interview 高频题(高频考点/新人常见疑问) | R4 / R8 |
| 叙事价值高 | 13.story 叙事准入(§3.5 六信号) | R6 / R9 |
| 先例口径 | 同栏目「-troubleshooting / 案例」类计数 | R10 |
| 招聘语境 | 有(12.interview 含方法论模块) | R16 / S1 |

- [ ] **Step 4: SPEC.md §9.1 责任矩阵加 1 行**

`| note-precipitation-planning | **Phase 3/4** 三段式决策 | references/rule-catalog.md + $KB_DIR/SPEC.md §1.6 | 规则目录 + 谓词默认值 |`(SPEC-LIFECYCLE 行由 Task 5 加,避免指向未存在文件)

- [ ] **Step 5: 链接校验(相对路径层级深,逐链 isfile)**

Run: `python .github/workflows/scripts/check-broken-links.py .claude/skills/note-precipitation-planning/references/rule-catalog.md SPEC.md` + 对 rule-catalog 内每个相对链接跑 `python -c "import os;print(os.path.isfile('<目标>'))"`
Expected: 总计 0;每个 True。**重点核对**:`../../cross-domain-rule-trace.md`、`../SKILL.md`、`../../../../SPEC.md`。

- [ ] **Step 6: commit**

```bash
git add .claude/skills/note-precipitation-planning/references/rule-catalog.md SPEC.md
git commit -m "feat(note): 新增 rule-catalog 规则目录与 SPEC §1.6 谓词层

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 4: precipitation SKILL 三段式重写(含 V4/V5)

**Files:**
- Modify: `.claude/skills/note-precipitation-planning/SKILL.md`(Phase 3 / Phase 4 区块重组;Phase 5 / Quick Checklist / Phase 5.5 小改)

**Interfaces:**
- Consumes: Task 3 的 `rule-catalog.md`(R# 编号、Part 2 裁决序、Part 3 谓词)
- Produces: SKILL.md 新锚点 `### Phase 3/4: 位置 + 层级决策(三段式)`;溯源链格式行(下游 Task 6 回归按此格式验收过程输出)

- [ ] **Step 1: 重组 Phase 3/4 为三段式**

新骨架(内容按设计 §5.2;旧决策树节点**删除语义正文、保留 R# 引用**):

```markdown
### Phase 3/4: 位置 + 层级决策(三段式 · rule-catalog 驱动)
Stage 1 规则命中表:输入属性(预估行数/主题数/先例数/§1.5 角色/§1.6 谓词)
  → 对照 rule-catalog.md Part 1 逐规则判定;谓词不满足 → 显式排除声明
Stage 2 预案集:每命中规则 → 一条预案(rule-catalog 预案片段格式)
Stage 3 综合裁决:按 Part 2 覆盖/组合序合并 → 最终方案 + 溯源链
溯源链格式:`R#(判据:输入属性) + R#(判据) → 综合 = 方案`
```

保留并加 R# 标注:特殊位置判断(R5)、§1.8 先例对照(R10,含 cpu-spike 示例——示例留 SKILL,catalog 保持域中立)、2026-08-28 经验补充(R10)、双层/三层模板(R8/R9)。三段式只管 Phase 3/4;R1/R2/R3 留原 Phase 原样加 R# 标注。Quick Reference 表加"规则"列(R7-R10)。

- [ ] **Step 2: Phase 5 + Quick Checklist 小改**

Phase 5 选项呈现加一行:"每选项标注「对应预案组合」";Quick Checklist 加一项:"决策输出含溯源链(R# 判据 → 综合)"。

- [ ] **Step 3: V5 修复(13.story 字面残留)**

grep -n "13.story" SKILL.md:Phase 4 树内 `$KB_DIR/13.story/SPEC.md §3.5` 字面引用改 `<叙事专栏>/SPEC.md §3.5` 参数化(其余合法上下文如示例注释保留)。

- [ ] **Step 4: V4 修复(Phase 5.5 窄查询模板)**

Phase 5.5 领域 query 模板加 1 行非 IT 示例:`<领域> <主题> <year> best practice`,并在噪音 fallback 行加"非 IT 域优先宽查询 + 人工转译"提示。

- [ ] **Step 5: 【GATE 中点】自查设计 anti-goal**

Run: `grep -n "R7\|R8\|R9\|R10\|R23\|R25" .claude/skills/note-precipitation-planning/SKILL.md`
Expected: Phase 3/4 区内只有 R# 引用(如"R8 双层"短语),**无规则语义正文**(判定条件/行数阈值正文只在 rule-catalog.md)。有 → 删 SKILL 侧语义,保 catalog 单源。

- [ ] **Step 6: Safeguards 三查**

```bash
python -c "import yaml; yaml.safe_load(open('.claude/skills/note-precipitation-planning/SKILL.md',encoding='utf-8').read().split('---',2)[1]); print('YAML OK')"
grep -rn 'Phase [0-9]' .claude/skills/note-precipitation-planning/SKILL.md | head -20   # 锚点:Phase 编号引用仍解析(Phase 3/4 改名处的跨文件引用一并 grep 全库)
grep -rn 'Phase 3/4\|Phase 4' .claude/skills/ CLAUDE.md --include='*.md' | grep -v rule-engine | head -20   # 找指向旧 Phase 4 树的外部引用
```
Expected: YAML OK;外部引用(如 CLAUDE.md、note-health 的 "Phase 4 决策树"字样)同步改口径或保持语义仍正确;派发 smoke 3 类原话("X 沉淀到哪"/"扫一遍 note"/"查 note")人工核路由不变。

- [ ] **Step 7: 链接校验 + commit**

Run: `python .github/workflows/scripts/check-broken-links.py .claude/skills/note-precipitation-planning/SKILL.md`(Expected 0)

```bash
git add .claude/skills/note-precipitation-planning/SKILL.md
git commit -m "refactor(note): precipitation Phase 3/4 三段式决策重构

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 5: SPEC-LIFECYCLE.md + 三处接线

**Files:**
- Create: `.claude/skills/note-precipitation-planning/references/SPEC-LIFECYCLE.md`
- Modify: `.claude/STARTUP-NEW-KB.md`(§2.2 表 + §5)
- Modify: `.claude/skills/note-precipitation-planning/references/MODULE-CREATION-SPEC.md`(Step 2)
- Modify: `SPEC.md`(§9.1 加 SPEC-LIFECYCLE 行)

**Interfaces:**
- Consumes: 设计 §5.4(四问内容与两张表——"缺失,本设计补"行是本 task 的增量)
- Produces: `SPEC-LIFECYCLE.md` 四个锚点(`① 何时生成`/`② 怎么生成`/`③ 何时修改`/`④ 怎么修改`);三处接线指针

- [ ] **Step 1: 写 SPEC-LIFECYCLE.md(收编不复制)**

四章内容按设计 §5.4:4 触发表 / 生成顺序(§1→§2→§3→§1.5→§1.6→§8→§9)/ 修改事件表(7 行,含 4 行"缺失本设计补")/ 修改方法(顺序 + 版本日志 + 改后三查 + 禁忌)。**既有内容只放一行摘要 + 相对链接**(§8.4 → `../../../../SPEC.md`、§9.3 同;MODULE-CREATION → `MODULE-CREATION-SPEC.md`;STARTUP → `../../../STARTUP-NEW-KB.md`);新增内容(增删角色同步 §1.5/§1.6、catalog 变更核对、frontmatter 增删、体检 P1 对应节)写全文。

- [ ] **Step 2: STARTUP-NEW-KB 接线**

§2.2 必填章节表加行:`| §1.6 | KB 谓词定义(规则引擎输入) | ⭕ | 至少 3 行谓词 |`;表下注释加一句指向 `SPEC-LIFECYCLE.md`(何时/怎么生成修改 SPEC)。

- [ ] **Step 3: MODULE-CREATION + §9.1 接线**

MODULE-CREATION Step 2(建 SPEC.md)末尾加一行:`SPEC 生成顺序与修改协议见 SPEC-LIFECYCLE.md`;SPEC.md §9.1 加行:`| note-precipitation-planning | **Phase 3.5/6.9** SPEC 生命周期 | references/SPEC-LIFECYCLE.md | 何时/怎么 生成修改 |`。

- [ ] **Step 4: 链接校验(isfile 逐链)+ commit**

Run: `python .github/workflows/scripts/check-broken-links.py .claude/skills/note-precipitation-planning/references/SPEC-LIFECYCLE.md .claude/STARTUP-NEW-KB.md .claude/skills/note-precipitation-planning/references/MODULE-CREATION-SPEC.md SPEC.md` + isfile 抽查 4 个相对链。Expected: 0;全 True。

```bash
git add .claude/skills/note-precipitation-planning/references/SPEC-LIFECYCLE.md .claude/STARTUP-NEW-KB.md .claude/skills/note-precipitation-planning/references/MODULE-CREATION-SPEC.md SPEC.md
git commit -m "feat(note): 新增 SPEC-LIFECYCLE 与三处接线

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---

### Task 6: IT 回归 + V3 顺手项 + 结果落库

**Files:**
- Modify: `.claude/skills/note-knowledge-qa/SKILL.md`(V3)
- Modify: `.claude/skills/cross-domain-r0-baseline.md`(追加回归结果节)

**Interfaces:**
- Consumes: Task 2 冻结基线(P1-P10)· Task 4 后的 SKILL 行为 · note-kb-test/invest(coffee 只读)
- Produces: 回归结果表(追加进 r0-baseline);V3 修复

- [ ] **Step 1: R0 十例重放(对照冻结基线)**

对 P1-P10 逐条:按问法走 Task 4 后的 skill 决策流程(P1-P5 记录 命中表/预案/裁决,最终方案 = 位置/层数/commit 数;P6-P10 记录回答类型/维度/分流)。对照基线表逐列比对。**验收:P1-P10 最终方案全一致**;P2/P4 只验决策结果;过程输出格式差异(三段式可见)允许。

- [ ] **Step 2: 降级探针抽测(note-kb-test,只读)**

- I2:对 invest KB(无角色)问「定投 vs 一次性买入」类沉淀需求 → 期望:**单文件 + 显式降级声明**;硬造双层 = FAIL。依据:§1.5 无角色 → R23(默认值推导路径,Task 3 Part 3)。
- C12′:对 coffee KB 出 B 型题 → 期望称谓「认证题/话术要点」,**零「面试」原词**。
- 记录:每探针一行(期望/实际/结论)。

- [ ] **Step 3: V3 修复(qa SKILL 学习路径模板)**

`note-knowledge-qa/SKILL.md` F 型学习路径模板:「基础/进阶/源码/深度/实战」目录假设改为"按 `$KB_DIR/SPEC.md §1` 模块结构生成学习顺序"(删 IT 学科目录字面)。改后跑 Safeguards YAML 查。

- [ ] **Step 4: Safeguards 三查(全量)**

对本计划改过的全部 SKILL.md 跑:YAML 解析 + Phase 锚点审计 + 派发 smoke 3 类原话。Expected: 全过。

- [ ] **Step 5: 全库链接校验**

Run: `python .github/workflows/scripts/check-broken-links.py`
Expected: `.md 断链: 0 / 目录断链: 0 / 总计: 0`。

- [ ] **Step 6: 回归结果落库 + commit**

在 `cross-domain-r0-baseline.md` 追加 `## 回归结果(YYYY-MM-DD)` 表:P1-P10 结论 + I2/C12′ + Safeguards + 链接。

```bash
git add .claude/skills/note-knowledge-qa/SKILL.md .claude/skills/cross-domain-r0-baseline.md
git commit -m "fix(note): qa 学习路径模板域中立化并记录规则引擎 IT 回归结果

Co-Authored-By: Claude Code <noreply@anthropic.com>"
```

---
