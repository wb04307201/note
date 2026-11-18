# 规则引擎 + SPEC 生命周期设计(方案 2 + Tier 1)

> **Status**: 设计稿 v2(builder check 4 问已裁决,待用户终批)
> **Created**: 2026-11-18
> **前置阅读**:`cross-domain-generality-report.md`(26 场景 0 FAIL,Phase A-D 完成)· `cross-domain-rule-trace.md`(R1-R25 + K 谓词——本设计的机制原型,已按此判定模型跑完全量测试)
> **批准记录**:2026-11-18 用户批准「方案 2 + Tier 1 合并版」;形式轴(载体/形态,Tier 2/3)明确不做
> **Builder check 裁决**(2026-11-18):R0 基线 = 重建 + 冻结签认(用户选 A);其余 3 问按设计者裁定落 §2/§5.1/§5.2/§5.3

## 1. 意图与背景(Why)

用户两条核心诉求(原话):

1. **"几层不是应该根据 SPEC.md 的规则判断么,符合几个规则,就有几个预案,大模型根据预案再出最终几层的方案"** —— 层级决策从"决策树直接给结果"改为"规则命中 → 逐规则预案 → 综合裁决"。
2. **"skill 里对 SPEC.md 的何时生成、何时修改、怎么生成、怎么修改都是缺失的"** —— 补齐 SPEC 生命周期。

现状:跨域测试(26 场景 24 PASS + 2 DEGRADE + 0 FAIL)的判定基准**就是**诉求 1 的模型("命中规则→预案→综合",含 R11×R8 组合、R23⊃R8 覆盖等实例),但机制只存在于测试文件 `cross-domain-rule-trace.md`,skill 决策树仍"直接给结果";SPEC 生命周期散落三处(§8.4 词表维护、§9.3 pointer 协议、MODULE-CREATION Step 2 建模块),无统一的四问(何时生成/怎么生成/何时修改/怎么修改)。

本设计把**已验证的判定模型迁进正式机制**,并补齐 SPEC 生命周期。

## 2. 目标 / 非目标 / 反目标

**Goals**
- G1 **规则单源**:R1-R25 正式化为 `rule-catalog.md`,含适用性谓词(Tier 1)、覆盖/组合序、预案片段格式
- G2 **三段式决策**:precipitation Phase 3/4 输出改为「规则命中表 → 预案集 → 综合裁决(带溯源链)」
- G3 **SPEC 谓词层**:SPEC.md 新增 §1.6(KB 自定义谓词语义/阈值/口径),换域只改 §1.6
- G4 **SPEC 生命周期**:`SPEC-LIFECYCLE.md` 统一四问,接线 STARTUP / MODULE-CREATION / SKILL
- G5 **IT 回归零回退**:R0 十例对照**重建并经签认的冻结基线**(`cross-domain-r0-baseline.md`,见 §5.6)+ Safeguards 三查
- G6 **前置清理**:Phase B 未提交产出(6 文件改动 + 4 个测试报告)先落库

**Non-goals**
- 形式轴不考虑(git/载体谓词不写;Tier 2 存储适配 / Tier 3 新 skill 家族挂起)
- 结构性 P2(S2 回链纪律 / S3 口径分层 / K5 tags↔§8)不动
- QA/health 决策流程不重写(R13-R21 只登记进 catalog,三段式暂只覆盖 precipitation Phase 3/4——"几层"所在)
- 非 IT 测试 KB 不重跑全量(coffee/invest/fitness 仅抽降级探针复测)

**Anti-goals(出现即失败)**
- 规则全文复制进每个 KB SPEC(双维护漂移,违背 SPEC §9 单一来源)
- 三段式让 IT 现行为改变(R0 十例最终方案必须一致)
- 为泛化稀释 IT 特化(继承测试反目标)
- **规则语义**在 catalog 与 SKILL 正文两处维护(builder check 裁决:登记行不算——R1-R25 在 catalog 各有"一行摘要 + 来源指向"登记行,但**语义只在一处**;Phase 3/4 规则语义迁 catalog,其余规则语义留各自 Phase 原地,摘要表保留并加 R# 标注)

## 3. 约束

- **单一来源**(SPEC §9.2 五层分解延续):规则语义 = skill references;规则实例/谓词 = KB SPEC
- **5 层防护链不破坏**(commit-msg → pre-commit → §7.2 → push/PR → 月度 cron)
- **Skill 修订 Safeguards 必跑**(改 SKILL.md 后:YAML 解析 + 章节锚点审计 + 派发 smoke,CLAUDE.md 现有约定)
- **commit 纪律**:Conventional Commits + 数字不虚报;Phase B 存量先独立落库
- **环境**:Windows git bash;测试 KB 在 `D:/developer/IdeaProjects/note-kb-test/`(外部目录,不入本仓库 git)

## 4. 方案(已选定:方案 2 + Tier 1)

| 方案 | 内容 | 取舍 |
|------|------|------|
| 1 轻改 | 决策树只标注 R 编号 + 输出格式加溯源 | 改动最小,但"按 SPEC 规则判断"无机制载体——治标 |
| **2 + Tier 1(选定)** | 规则目录单源 + 三段式决策 + SPEC §1.6 谓词 + 适用性谓词化 | 精确落地诉求;26 场景证据直接成机制;换域只改 §1.6;动 5 处文件 + 一轮回归 |
| 3 规则全形式化 | 规则全文进各 KB SPEC,skill 退化执行器 | 双维护漂移;锁死 LLM 综合裁决灵活性——过度 |

**Tier 1 并入理由**:R23(缺角色)/S1(缺招聘语境)/R16(缺考试结构)是同一"前提不满足→跳过+显式声明"机制的三个特例,均经测试验证;泛化为每条规则的 applicability 谓词是收尾而非新发明。无谓词化的规则目录会在无角色 KB 上误命中(如 R8 建议双层)。

## 5. 设计细节(已定的 how)

### 5.1 `note-precipitation-planning/references/rule-catalog.md`(新建)

单一规则源,三部分:

**Part 1 规则登记**(R1-R25,从 `cross-domain-rule-trace.md` 迁入正式化)。每条 schema:

```markdown
### R8 双层沉淀
- **规则**:预估 100-300 行 + 考试/问答价值高 → 双层(interview 版 + depth 版互链,2 commit)
- **来源**:precipitation Phase 4 决策树
- **适用性谓词**:has_exam_value(读 SPEC §1.6);has_interview_role(读 SPEC §1.5)——任一不满足 → 被 R23 覆盖
- **预案片段**:形态=双层 · 位置=<interview>/<depth> · commit=2 · 理由=问答价值与深度需求并存
```

**Part 2 覆盖/组合序**(综合裁决的裁决规则):
- **覆盖**:R23 ⊃ R8/R9(简化 KB 降级)· R10 ⊃ R8(先例覆盖)· R2 修复类不走沉淀
- **组合**:R11+R8(合并式统一深读 + 新问答版)· R11+R5(合并式深读)· R25 为合法附加选项但不得违反 R23
- **冲突未定义** → 记「规则缺口」不算 skill 错(沿用测试判定基准)

**Part 3 适用性谓词(Tier 1)**,三类(不写 git/载体条款)。**默认值列**(builder check 裁决):无 §1.6 的 KB 按默认语义——默认值 = 按角色推导(§1.5 是必填、§1.6 是精化层):

| 类 | 谓词 | 读取处 | 默认值(无 §1.6 时) |
|----|------|--------|---------------------|
| 角色 | has_interview_role / has_story_role | SPEC §1.5 | (§1.5 必填,无默认) |
| 场景 | has_exam(考试/问答价值) | SPEC §1.6 | **= has_interview_role**(有面试角色即视为可出问答版) |
| 场景 | has_recruiting(招聘语境) | SPEC §1.6 | **= has_interview_role** 且模块含方法论类内容 |
| 叙事 | has_narrative(叙事价值) | SPEC §1.6 | **= has_story_role** |
| 口径 | precedent_count(先例计数) | SPEC §1.6 | 同类先例 ≥3(口径:同栏目「-troubleshooting / 案例」类) |
| 口径 | is_series(系列) | SPEC §1.6 | 目标目录存在编号系列(运行时 find 判定) |

> 默认语义保证两头:note/咖啡(有角色 → 双层可用)行为不变;无角色 KB 走 R23 降级(测试验证路径),不硬造语义。

### 5.2 precipitation Phase 3/4 三段式重写

```text
Stage 1 规则命中表:输入属性(预估行数 / 主题数 / 先例数 / §1.5 角色 / §1.6 谓词)
        → 逐规则判定 命中 / 不命中;谓词不满足时显式排除声明
          (如"R23 命中:无 interview 角色 → 排除 R8/R4")
Stage 2 预案集:每条命中规则 → 一条预案(5.1 预案片段格式)
Stage 3 综合裁决:按 Part 2 覆盖/组合序合并预案 → 最终方案(几层 / 位置 / commit 数)+ 溯源链
```

- Phase 3(位置)与 Phase 4(方式/几层)统一走三段式:位置规则(R4/R5/R6/R23/R25)与方式规则(R7-R10)在同一命中表内;组合规则(R10/R11/R24)参与 Stage 3 裁决
- **三段式只管 Phase 3/4 的"几层"决策**(builder check 裁决):R1 拆分 / R2 分流 / R3 拒绝留原 Phase(0.2 / 0.1 / 2)原样,只加 R# 标注;R0 回归中拆分/拒绝探针**只验决策结果,不验溯源链**。"主题数"输入属性是喂 R11 合并判据的
- Phase 5 选项呈现照旧(2-4 选项),但每选项标注「对应预案组合」
- 溯源链格式:`R#(判据:输入属性) + R#(判据) → 综合 = 方案`

### 5.3 SPEC.md §1.6 新增(KB 谓词层)

**职责切分**:§1.5 管"有没有"(角色存在性);§1.6 管"怎么算"(谓词语义 + 阈值 + 口径)。

```markdown
### 1.6 KB 谓词定义(规则引擎输入)
| 谓词 | 本 KB 定义 | 影响规则 |
|------|-----------|---------|
| 考试价值高 | SCA 认证常考 / 新手高频疑问 | R4 / R8 |
| 叙事价值高 | 故事弧 + §3.5 准入 | R6 / R9 |
| 先例口径 | 同栏目「-troubleshooting / 案例」类计数 | R10 |
```

- **无 §1.6 的 KB**:谓词按默认语义 + skill 内置降级(测试验证的 R23/S1/R16 行为不变)
- **note KB 自身 SPEC.md 也补 §1.6**(按现有口径回填,如"考试价值高 = 12.interview 高频题")
- **STARTUP-NEW-KB §2.2** 必填章节表加 §1.6 行(⭕ 可选推荐);K1 契约缺口(L1 的 §3.5/§5 声明)保持 Phase B 已落的版本

### 5.4 `note-precipitation-planning/references/SPEC-LIFECYCLE.md`(新建)

四问四章;**收编**而非复制 §8.4 / §9.3 / MODULE-CREATION 现有内容(细节留原节,SPEC-LIFECYCLE 做索引 + 缺口补齐,互链):

**① 何时生成**(4 触发):

| 触发 | 产出 | 现有出处 |
|------|------|---------|
| 建新 KB | L0 SPEC(7-9 节) | STARTUP §2.2(指入) |
| 建新模块 | L1 SPEC | MODULE-CREATION Step 2(指入) |
| 建 L1x(§7 三信号任 2) | 子目录 SPEC | SPEC §7(指入) |
| **增/删角色模块** | §1.5 行 + §1.6 谓词同步 | **缺失,本设计补** |

**② 怎么生成**:生成顺序(§1 命名 → §2 commit → §3 互链 → §1.5 角色 → §1.6 谓词 → §8 词表 → §9 契约)+ 每节模板引用(STARTUP §2.2 骨架表 / MODULE-CREATION Step 2 / L1x 三件套)+ 最低内容要求沿用现有表。

**③ 何时修改**(统一清单,现散落各处):

| 事件 | 改哪些节 | 现有出处 |
|------|---------|---------|
| 角色变更(增/删角色模块) | §1.5 + §1.6 | **缺失,本设计补** |
| 结构重构(拆/合/迁移) | §1 路径 + §8 词表 | §8.4(指入) |
| rule-catalog 规则变更 | 各 KB §1.6「影响规则」列核对 | **缺失,本设计补** |
| frontmatter 类型增删 | §4 | **缺失,本设计补** |
| 体检 P1 契约类发现 | 对应节 | **缺失,本设计补** |
| L1.5 合并/拆分 | §7(现有"何时新建 L1.5",补"何时并回 L1") | 部分 |
| 评分维度校准 | §5 | auto-calibrate(指入) |

**④ 怎么修改**:
- **顺序**:先 SPEC 后 skill(§9.3 现有,收编为索引行)
- **版本日志**:L1 模板加轻量版本日志小节(一行/版本;L1.5 模式推广)
- **改后验证**:锚点审计 + 派发 smoke + check-broken-links(类比 CLAUDE.md「Skill 修订 Safeguards」三查)
- **禁忌**:同 README 维护等价表(Mistake 15)/ 数字硬编码 / 无 `find` 校对的篇数声明

### 5.5 接线表

| 文件 | 改动 |
|------|------|
| `note-precipitation-planning/SKILL.md` | Phase 3/4 → 三段式(引 rule-catalog 编号);Phase 3.5/6.9 引 SPEC-LIFECYCLE;Quick Checklist 加溯源链项 |
| `note-precipitation-planning/references/rule-catalog.md` | 新建 |
| `note-precipitation-planning/references/SPEC-LIFECYCLE.md` | 新建 |
| `SPEC.md` | §1.6 新增;§9.1 责任矩阵加行(rule-catalog / SPEC-LIFECYCLE 引用契约) |
| `.claude/STARTUP-NEW-KB.md` | §2.2 表加 §1.6 行 + 引 SPEC-LIFECYCLE |
| `references/MODULE-CREATION-SPEC.md` | Step 2 引 SPEC-LIFECYCLE |
| (顺手,措辞级 P2)V3 / V4 / V5 | 5-dim 学习路径模板 / qa 窄查询模板 / precipitation 树 13.story 残留 |

### 5.6 回归计划

1. **R0 基线重建 + 冻结签认**(builder check 裁决·用户选 A):原十例基线表未入库(`cross-domain-evidence.md` 仅存结论行 + "(表格见对话记录)")。**步骤**:从 `test-scenarios.md`(66 场景母集)重建 10 例决策探针(对齐 R0 结论行:双层 / 拆分 / 拒绝 / 13.story / QA 三型 / E 维度 / Phase 0.1),按**方案级**冻结期望(位置 / 单双三层 / commit 数),落库为 `cross-domain-r0-baseline.md`,**用户签认后冻结**(参照 rule-trace 签认流程)
2. **R0 十例重放**:对照冻结基线比对最终方案(拆分/拒绝类只验决策结果,见 §5.2);过程可见性变化允许,最终方案必须一致
3. **降级探针抽测**(用 note-kb-test 现存 KB,只读):I2(投资库必双层题 → 单文件 + 降级声明)+ C12′(称谓替换)
4. **Safeguards 三查**:SKILL.md YAML / 章节锚点 / 派发 smoke
5. **全库 check-broken-links = 0**

## 6. 留给 builder 的

- 各文件具体措辞与行数预算
- commit 拆分粒度(建议序:①Phase B 落库 ②R0 基线重建 + 签认 ③rule-catalog + §1.6 ④三段式重写 ⑤SPEC-LIFECYCLE + 接线 ⑥回归 + 顺手项;可调)
- R0 重建探针的具体问法(从 test-scenarios.md 采样,决策类严格对齐 R0 结论行)
- catalog 中 R13-R21(QA/health 规则)登记深度:仅登记(schema 同 R1-R12,标注"流程暂不改")——已定,不带谓词

## 7. 风险与对策

| 风险 | 对策 |
|------|------|
| 三段式改变 IT 现行为 | R0 十例冻结对照;允许过程可见性变化,最终方案不变 |
| catalog 与 SKILL 漂移 | catalog 单一来源,SKILL 只引 R# 编号;违规即 anti-goal |
| §1.6 与 §1.5 重叠 | 职责切分:存在性 vs 语义;无 §1.6 按默认语义降级 |
| SPEC-LIFECYCLE 与 §8.4/§9.3 重复维护 | 收编不复制:索引 + 缺口补齐,细节留原节 |
