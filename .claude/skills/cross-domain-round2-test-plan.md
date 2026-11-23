# 跨域通用性测试 R2 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用健康/法律/音乐 3 个全新测试 KB（含单角色中 KB）+ IT 对照完成规则引擎首考，测试驱动修复（F0 + P2 背包 + 新发现），证明「通用、稳定、可用」。

**Architecture:** 生成式建 3 个外部测试 KB（`note-kb-test/`，git 快照管理）→ A.0 规则溯源表机械推导并由用户签认 → 真实 skill 调用跑 26 个非 IT 场景（三段式输出逐字留证）+ R0 冻结基线十例重放 → 规则溯源判定（PASS/DEGRADE/FAIL）→ 用户批准修复清单后修 F0 语义冲突 + P2 六项 → IT 回归（R0 + Safeguards + note-temp 冒烟）→ 快照复测 + 终版报告。

**Tech Stack:** 3 个 meta-skill（`.claude/skills/note-*/`）· `rule-catalog.md`（R1-R25）· `check-broken-links.py` · git tag 快照 · Markdown 证据文件

**Spec:** `.claude/skills/cross-domain-round2-test-design.md`（已批准，2026-11-20）——计划从该设计稿推导，执行者两份都读

## Global Constraints

- 测试 KB 一律放 `D:/developer/IdeaProjects/note-kb-test/{health,law,music}/`，**不入 note 仓库 git**；每 KB 独立 `git init`
- note 主仓库全程 **read-only**（场景执行不写不 commit）；仅计划内 fix/docs commits 触碰本仓库
- 场景执行协议（设计 §5.5）：选项呈现**原文记录**（全部选项+推荐项）；实施类选推荐项继续；交互类用固定画像脚本；R0 沉淀类**止于 Phase 5**；测试 KB 场景**全实施**（含 commit）
- 改变 KB 状态的场景执行前 `git tag scenario-<id>`；Phase D 复测 `git checkout` 回快照重跑
- 判定 = 规则溯源双条件（一致性 + 可追溯）；溯源链断/缺段/编造 R# = FAIL；冲突探针行（H3/H7/L2/M5）按设计 §6.1 四分支判定
- commit 格式 Conventional（`docs(skill)` / `fix(skill)` / `feat(skill)`）+ `Co-Authored-By: Claude Code <noreply@anthropic.com>`；数字禁 hardcode，一律 `find` 实时校对
- 任改 SKILL.md 后必跑 Safeguards 三查（YAML 解析 / Phase 锚点审计 / 派发 smoke 3 原话，见 CLAUDE.md）
- 链接校验必须 0 断链：note 仓库用 `.github/workflows/scripts/check-broken-links.py`；测试 KB 用各自 `scripts/` 副本
- 反目标守则：不许全局替换稀释 IT 特化——修复走 §1.5/§1.6/§8/`<module>/SPEC.md` 参数化老路，IT 行为只能变宽不能变差
- 发现三分类记账：① skill 缺陷（细分引擎层/语义层/既有机制层）② 契约-文档缺口 ③ 领域失配；内容问题单独记账

## Review Focus

1. **生成内容质量不齐 → 内容问题被误判 skill 问题**：每批生成后 note-health 单篇评分抽查必须留记录，内容瑕疵单独记账（Task 2-4 抽查步）
2. **场景执行污染主仓库**：每场景批完成后 `git status --short` 必须 clean，否则证据无效（Task 8-11 校验步）
3. **三段式证据缺段仍判 PASS（判定松弛）**：证据文件每行必须含命中表/预案/裁决三段 + R# 溯源链，缺段即 FAIL，不许事后补记（Task 8-11 核查步）
4. **F0 冲突探针跨行不一致被放过**：H3/H7/L2/M5 同构输入处置不一致且无谓词差异说明 = FAIL，专项核查（Task 11）
5. **数字 hardcode / 虚报**：leaf 篇数、场景数、R0 结果一律 `find`/逐列比对实时校对后才许写进报告（Task 4/11/15）

---

### Task 1: health KB 骨架 + SPEC（契约层）

**Files:**
- Create: `D:/developer/IdeaProjects/note-kb-test/health/{README.md, SPEC.md, scripts/check-broken-links.py}`
- Create: `D:/developer/IdeaProjects/note-kb-test/health/{01.body-basics,02.nutrition,03.mental-health,04.common-conditions,05.medical-stories}/README.md`（5 个模块空骨架）

**Interfaces:**
- Consumes: `.claude/STARTUP-NEW-KB.md` §2.2（SPEC 必填节）+ §1.5 角色契约 + §1.6 谓词声明；`cross-domain-round2-test-design.md` §4.1
- Produces: health KB 契约就绪状态——Task 2-4 填内容，Task 7 读 `SPEC.md §1.5/§1.6` 冻结谓词

- [ ] **Step 1: git init + 目录骨架**

```bash
mkdir -p D:/developer/IdeaProjects/note-kb-test/health/{scripts,01.body-basics,02.nutrition,03.mental-health,04.common-conditions,05.medical-stories}
cd D:/developer/IdeaProjects/note-kb-test/health && git init
cp D:/developer/IdeaProjects/note/.github/workflows/scripts/check-broken-links.py scripts/
```

- [ ] **Step 2: 写 SPEC.md（按 STARTUP-NEW-KB §2.2）**

必含：§1 模块结构（5 模块）· §2 commit 格式 · §3 互链规则 · §8 词表（空表起）· §9 引用契约；**§1.5 角色清单只有 `05.medical-stories: type=story`（不设 interview——单角色不对称是刻意设计）**；§1.6 谓词声明（has_narrative / has_story_role=true / has_interview_role=false / precedent_count 等按 §1.6 契约写默认值）。README.md 含「学习笔记，非专业建议」免责声明。

- [ ] **Step 3: 写 5 个模块 leaf README 骨架（`← 返回` 回链 + frontmatter `module:` 类型）**

- [ ] **Step 4: 链接自检 + commit**

Run: `cd D:/developer/IdeaProjects/note-kb-test/health && python scripts/check-broken-links.py`
Expected: `总计: 0`。commit `docs(health-kb): 契约骨架（SPEC §1.5 单角色 + §1.6 谓词）`

### Task 2: health 批 1——01.body-basics + 02.nutrition

**Files:**
- Create: `note-kb-test/health/01.body-basics/` 与 `02.nutrition/` 各 ~15-20 篇 leaf
- Modify: 两模块 `README.md`（索引表）· `05.medical-stories` 等不动

**Interfaces:**
- Consumes: Task 1 骨架
- Produces: H1/H2/H5 场景所需内容素材（睡眠机制 / 维生素 D 数字断言 / 营养批量素材源）

- [ ] **Step 1: 生成 01.body-basics（~15-20 leaf）**：睡眠/免疫/消化等机制深度原理；科普级常识为界，不造专业建议；每篇 frontmatter + 互链合规
- [ ] **Step 2: 生成 02.nutrition（~15-20 leaf）**：营养素/膳食主题；含指南版本时效表述（「截至 XX 年推荐」）与可核实数字（为 H2/H5 铺素材）
- [ ] **Step 3: note-health 单篇评分抽查（≥2 篇）并记录分数**——内容瑕疵单独记账，不算 skill 发现
- [ ] **Step 4: 链接自检 + find 校对篇数 + commit**

Run: `python scripts/check-broken-links.py && find . -name "*.md" | wc -l`
Expected: 断链 `总计: 0`；篇数与本步记录一致（禁 hardcode 进后续文档）。commit `docs(health-kb): 批1 人体机制 + 营养`

### Task 3: health 批 2——03.mental-health + 04.common-conditions

**Files:**
- Create: `03.mental-health/`（~15-20 leaf）· `04.common-conditions/`（~15-20 leaf，**含编号系列**「常见病 01/02/…」）
- Modify: 两模块 `README.md`

**Interfaces:**
- Consumes: Task 2 批 1（词表素材积累）
- Produces: H4/H6/H7 场景载体（误区拆分素材 / 编号系列 / 同栏先例 ≥3 的案例栏目）

- [ ] **Step 1: 生成 03.mental-health（~15-20 leaf）**：压「常识 vs 专业」边界（哪些太泛不值得沉淀、哪些有机制深度）——为 L8/H 类准入判定铺素材
- [ ] **Step 2: 生成 04.common-conditions（~15-20 leaf）**：**必须含 3+ 篇同栏「临床案例」先例**（H7 先例覆盖的前置状态）+ 一组编号系列（H6 加篇载体）
- [ ] **Step 3: note-health 抽查（≥2 篇）** + **Step 4: 链接自检 + find 校对 + commit**（同 Task 2 模式）。commit `docs(health-kb): 批2 心理 + 常见病`

### Task 4: health 批 3——05.medical-stories + §8 词表 + 全库自检

**Files:**
- Create: `05.medical-stories/`（~10-15 leaf：病例叙事 / 医学史）
- Modify: `SPEC.md §8`（词表收口）· 各模块 README

**Interfaces:**
- Consumes: Task 2/3 全部内容
- Produces: health KB 完整态（目标 ~80-120 leaf）——Task 7 冻结谓词、Task 8 跑场景

- [ ] **Step 1: 生成 05.medical-stories（~10-15 leaf）**：叙事主导，过叙事准入 6 信号；**含 1 篇「机制深度 + 叙事」混合体裁**（H3 的三层缺省层素材）
- [ ] **Step 2: §8 词表收口**：汇总 3 批新词登记（R12 口径，write-time 同步）
- [ ] **Step 3: 全库验收**：note-health 抽查 + 链接 0 断链 + `find` 校对总 leaf 数（设计预期 ~80-120，**实际数写进证据文件**）+ `git log --oneline | wc -l` 记录批次数
- [ ] **Step 4: commit** `docs(health-kb): 批3 叙事 + 词表收口`

### Task 5: law KB 全量（3 模块 ~10 leaf）

**Files:**
- Create: `note-kb-test/law/{README.md,SPEC.md,scripts/,01.legal-basics/,02.civil-topics/,03.case-notes/}` + ~10 leaf

**Interfaces:**
- Consumes: STARTUP-NEW-KB 契约；设计 §4.2
- Produces: L1-L8 场景载体（**02.civil-topics 含 3+ 篇编号系列**（L4 加篇）+ **03.case-notes 含 3+ 篇同类先例**（L7 先例））

- [ ] **Step 1: 建 KB（同 Task 1 模式）**：SPEC §1.5 **不设任何角色**；§1.6 谓词全默认；README 含免责声明
- [ ] **Step 2: 生成 ~10 leaf**：法理深度原理 / 民法主题编号系列 / 案例笔记；含「某条文历次修订」时效表述（L2）与可核实数字（L7 时限/数额）
- [ ] **Step 3: 抽查 + 链接自检 + find 校对 + commit** `docs(law-kb): 全量（无角色 + 强编号系列）`

### Task 6: music KB 全量（3 模块 ~10 leaf）

**Files:**
- Create: `note-kb-test/music/{README.md,SPEC.md,scripts/,01.music-theory/,02.practice-methods/,03.repertoire-notes/}` + ~10 leaf

**Interfaces:**
- Consumes: 同 Task 5
- Produces: M1-M6 场景载体（**03.repertoire-notes 含作曲家/风格叙事素材**（M5 降级探针））

- [ ] **Step 1: 建 KB**：SPEC 无任何角色（同 law）
- [ ] **Step 2: 生成 ~10 leaf**：乐理听觉机制 / 练习方法 / 曲目笔记——**不写任何数字断言类内容**（M6 软域纯粹性）
- [ ] **Step 3: 抽查 + 链接自检 + find 校对 + commit** `docs(music-kb): 全量（无判定软域）`

### Task 7: A.0 规则溯源表预注册 → **GATE 用户签认**

**Files:**
- Modify: `.claude/skills/cross-domain-rule-trace.md`（追加 `## R2 追溯表（2026-11-20）`）

**Interfaces:**
- Consumes: Task 1-6 的 3 个 KB SPEC（§1.5/§1.6 谓词）+ `rule-catalog.md` R1-R25 + 设计 §6.1（F0 裁定 + 冲突探针框架）
- Produces: 26 行非 IT 溯源表 + 10 行 R0 对照行（指向 `cross-domain-r0-baseline.md` 冻结期望，不重写）——Task 8-11 逐行比对的唯一标尺

- [ ] **Step 1: 逐场景推导 26 行**：每行 = 场景 ID + 输入属性假设（1-3 个，谓词翻译如「生产 Bug 案例 = 临床案例」显式写）+ 命中 R# 清单 + 推导预案（位置/形态/commit 数）+ 最终方案预期。**机械推导非人工发挥**；H3/H7/L2/M5 标「冲突探针」并写双推导 + 设计者裁定预期（角色比例降级）
- [ ] **Step 2: F0 登记**：表头注记 F0 预注册发现（rule-catalog 三处语义不一致，P1）
- [ ] **Step 3: 呈现给用户签认（GATE）**——表中假设列可被否决；签认后**表冻结不再改**，记录 `Status: 已签认冻结(YYYY-MM-DD)`

### Task 8: health 场景 H1-H12 执行 + 证据

**Files:**
- Create: `.claude/skills/cross-domain-evidence-r2.md`（`## H 场景证据` 节）

**Interfaces:**
- Consumes: Task 7 冻结表 H1-H12 行 + health KB 完整态
- Produces: 12 行证据（每行含三段式输出**逐字** + 判定 + git tag）

- [ ] **Step 1: 按 H1→H12 固定序执行**：真实 skill 调用（`Skill(note-precipitation-planning / note-health / note-knowledge-qa)` + args 声明 `KB_DIR=D:/developer/IdeaProjects/note-kb-test/health`）；改变 KB 状态的场景（H1-H8）执行前 `git tag scenario-H<id>`；实施类走推荐项
- [ ] **Step 2: 逐场景记录证据**：沉淀类（H1-H8）三段式输出逐字 + 溯源链 + 最终方案；问答/体检类（H9-H12）回答类型/称谓/模板词汇 + **H12 出题称谓零「面试」原词回验**（grep 证据输出）
- [ ] **Step 3: 对照冻结表逐行判定**（PASS/DEGRADE/FAIL + 规则出处）；H12 若复现 V1 类词汇 = 修复不彻底，记新发现
- [ ] **Step 4: 校验**：note 仓库 `git status --short` 必须 clean（Review Focus 2）；三段式缺段行清零（Review Focus 3）；health KB `python scripts/check-broken-links.py` 0 断链

### Task 9: law 场景 L1-L8 执行 + 证据

**Files:**
- Create: `cross-domain-evidence-r2.md` `## L 场景证据` 节

**Interfaces:**
- Consumes: Task 7 L1-L8 行 + law KB
- Produces: 8 行证据（含 L2 冲突探针、L7 数字断言触发记录）

- [ ] **Step 1: L1→L8 固定序执行**（同 Task 8 协议；L2/L4/L7 执行前打 tag）
- [ ] **Step 2: 记录 + 判定**：L2 双推导对照；L7 记录 R22 触发与否及 Phase 5.5 行为（V4 域模板位缺口预期复现 = 已知-已排期）
- [ ] **Step 3: 校验**（同 Task 8 Step 4）

### Task 10: music 场景 M1-M6 执行 + 证据

**Files:**
- Create: `cross-domain-evidence-r2.md` `## M 场景证据` 节

**Interfaces:**
- Consumes: Task 7 M1-M6 行 + music KB
- Produces: 6 行证据（含 M5 冲突探针、M3 V3 跨域复验行）

- [ ] **Step 1: M1→M6 固定序执行**（M4/M5 执行前打 tag）
- [ ] **Step 2: 记录 + 判定**：M3 期望 PASS（V3 已修）；若输出仍预设「基础/进阶/源码」类目录 = **新发现**（不入已知项）；M5 双推导对照
- [ ] **Step 3: 校验**（同 Task 8 Step 4）

### Task 11: R0 十例重放 + 判定汇总 + 报告草稿

**Files:**
- Create: `.claude/skills/cross-domain-round2-report.md`（草稿：§结论 / §场景矩阵 / §发现归账）
- Modify: `cross-domain-evidence-r2.md`（`## R0 证据` 节）

**Interfaces:**
- Consumes: Task 8-10 全部证据 + `cross-domain-r0-baseline.md` 冻结期望 + 设计 §6/§6.1
- Produces: 判定汇总（26 非 IT + 10 R0）+ 发现清单（三分类 + F0 实证状态）——Task 12/13 的修复输入

- [ ] **Step 1: R0 P1-P10 重放**（note 仓库 read-only，沉淀类止于 Phase 5）：P1-P5 记三段式 + 溯源链，对照冻结表**逐列**比对（格式差异允许，最终方案必须一致）；P6-P10 记分流/维度结论
- [ ] **Step 2: 冲突探针专项核查（Review Focus 4）**：H3/H7/L2/M5 四行并排——同构输入处置不一致且无谓词差异说明 = FAIL；汇总 F0 哪条分支被引擎实际命中
- [ ] **Step 3: 汇总判定 + 发现归账**：逐行三分类（skill 缺陷细分引擎层/语义层/既有机制层 · 契约缺口 · 领域失配）+ 内容问题单列 + 「已知-已排期」桶；**数字 `find` 实时校对后才写报告**（Review Focus 5）
- [ ] **Step 4: 写报告草稿 + commit** `docs(skill): R2 跨域测试报告草稿（26 场景 + R0 重放）`

### Task 12: Phase B-GATE → F0 语义对齐修复

**Files:**
- Modify: `.claude/skills/note-precipitation-planning/references/rule-catalog.md`（R23 谓词 + R9 预案 + R10 落位）
- Modify: `.claude/skills/note-precipitation-planning/SKILL.md`（同步三段式排除逻辑表述，与 catalog 单源一致）

**Interfaces:**
- Consumes: Task 11 发现清单 + 设计 §6.1 裁定语义
- Produces: F0 闭环——规则语义单源一致（角色比例降级）；Task 14/15 回归依据

- [ ] **Step 1: 修复清单呈现给用户批准（GATE）**——含 F0 + P2 六项 + 新发现逐条（级别 P0/P1/P2 + 修复方案一句话）；**用户批准后才动 skill**
- [ ] **Step 2: 修 F0**：R23 谓词「任一缺失即命中」→「按缺失角色门控：仅降级缺失角色所承载的形态」；R9 预案标注 interview 层可缺省（单角色 KB = `<depth>/<story>`，commit=2）；R10 落位 `<interview>/...` →「先例系列所在栏目」（域中立）。SKILL 侧表述同步，**规则语义正文只留 catalog 单源**（SKILL 只引 R#）
- [ ] **Step 3: Safeguards 三查**（YAML / 锚点 / 派发 smoke 3 原话）+ 单文件链接校验。Expected: 全过
- [ ] **Step 4: commit** `fix(skill): F0 规则语义单源对齐（角色比例降级）`

### Task 13: P2 背包六项 + 新发现修复

**Files:**
- Modify: `.claude/skills/note-health/SKILL.md`（S3 Phase 1.6 口径分层 · K5 tags↔§8 口径说明）
- Modify: `.claude/skills/note-precipitation-planning/SKILL.md`（S2 回链 checklist 强化 · V4 Phase 5.5 域模板位 · V5 13.story 残留清理）
- Modify: 其余按 Task 11 新发现清单定

**Interfaces:**
- Consumes: Task 11 发现清单（经 Task 12 Step 1 GATE 批准）
- Produces: P2 六项 + 新发现闭环；M3 复验前置条件

- [ ] **Step 1: 逐项修复**（一项一步一验证）：S3 单向链接口径分层（README→leaf 索引行 vs 正文链分开报）· S2 回链 checklist 与产出纪律对齐 · K5 tags↔§8 桥接口径说明 · V4 Phase 5.5 加「域模板位」（非 IT 宽查询 + 人工转译提示）· V5 grep 清 13.story 字面残留（合法上下文除外）
- [ ] **Step 2: note-temp 链接脚本同步（P2-6）**：`cp .github/workflows/scripts/check-broken-links.py D:/developer/IdeaProjects/note-temp/scripts/`（目录不存在先建）
- [ ] **Step 3: 新发现中 P0/P1 修复**（按 GATE 批准清单；无则跳过并记录「无」）
- [ ] **Step 4: Safeguards 三查 + 全部改动文件链接校验**。Expected: 全过
- [ ] **Step 5: commit** `fix(skill): R2 Phase B - P2 背包六项 + 新发现修复`

### Task 14: Phase C IT 回归

**Files:**
- Modify: `cross-domain-round2-report.md`（§回归记录）

**Interfaces:**
- Consumes: Task 12/13 修改后的 skill + `cross-domain-r0-baseline.md` 冻结基线
- Produces: 回归结论——回退即回滚对应修改

- [ ] **Step 1: R0 十例重放**（对照 Task 11 Step 1 的修改前记录 + 冻结期望双比对）：决策语义不得回退；三段式格式允许演进。Expected: 10/10 最终方案一致
- [ ] **Step 2: Safeguards 三查**。Expected: 全过
- [ ] **Step 3: note-temp 冒烟（S2）**：沉淀 1 主题 + 体检 1 篇 + 问答 1 题（全实施，NOTE_DIR=note-temp）+ 链接脚本可用性验证（P2-6 修复后）。Expected: 全流程走通
- [ ] **Step 4: 回归结果记录**；任一项失败 → `git revert` 对应 commit 后重跑该项

### Task 15: Phase D 复测 + 终版报告 + 归档

**Files:**
- Modify: `cross-domain-round2-report.md`（终版）· `cross-domain-evidence-r2.md`（复测行）
- Modify: `cross-domain-generality-report.md`（P2 待办节标注 R2 已闭环）

**Interfaces:**
- Consumes: Task 12/13 修复 + Task 8-11 原始判定 + KB git 快照
- Produces: 终版交付物（设计 §7）+ 仓库归档 commits

- [ ] **Step 1: 复测**：全部原 FAIL/DEGRADE 行（含冲突探针 DEGRADE）`git checkout scenario-<id>` 回快照重跑（Task 8-10 同协议）；**M3 必测**（V3 修复跨域复验闭环）。Expected: 全部转 PASS 或给出未修复理由
- [ ] **Step 2: 终版报告**：结论直接回答设计 G1-G6（通用/稳定/可用逐条达成状态）+ 发现终表（修复状态列）+ **数字 `find`/逐列实时校对**（Review Focus 5）
- [ ] **Step 3: 归档**：R1 报告 P2 待办节标注闭环；commit `docs(skill): R2 跨域测试终版报告 + P2 闭环标注`
- [ ] **Step 4: 终检**：note 全库 `python .github/workflows/scripts/check-broken-links.py` Expected 0 断链；`git status` clean；向用户汇报 G1-G6 达成状态
