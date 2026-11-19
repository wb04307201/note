# R0 回归基线(IT 决策对照 · P1-P10 探针)

> **Status**: 已签认冻结(2026-11-19)· 回归比对不再改
> **Created**: 2026-11-18 · 重建自 `test-scenarios.md`(66 场景母集,问法采样)+ `cross-domain-generality-report.md` R0 结论行(决策类对齐)· 规则编号见 `cross-domain-rule-trace.md` Part 1A
> **用途**: rule-engine-plan Task 6 IT 回归对照的**唯一基线**;回归记录以 `## 回归结果(YYYY-MM-DD)` 表追加本文件尾部,基线表本体冻结不改
> **签认**: 2026-11-19 用户签认冻结,3 项裁定:P3 期望修正为 `08.ai-foundations` + 可接受域口径(落 09.ai-applications 亦 PASS)· P10 决策类定名「Phase 0.1 询问」· 依据规则 R1/R3 口径维持

## 冻结说明

- **探针编号 P1-P10,与规则库编号 R1-R25 命名隔离**(P# = 回归探针 / R# = 规则)。R0 结论行原文的 R1-R10 是当日探针旧编号,本表按序一一对齐后统一改用 P#,避免与规则库碰撞。
- **决策类对齐目标**(报告 §2 原文):`R1 双层 / R2 拆分 / R3 08 主模块 / R4 拒绝 / R5 13.story / R6-R8 QA 三型 / R9 G1-G6+E 类 / R10 Phase 0.1 询问` → 按序 = P1-P10,决策类逐一对齐。
- **方案级冻结**:期望最终方案冻结到"位置 / 层数 / commit 数"粒度;回归比对时过程输出格式差异允许,**最终方案必须一致**;P2/P4 只验决策结果。
- **P3 可接受域口径**(签认裁定 2026-11-19):主期望 = `08.ai-foundations` 主模块(修正简报笔误「08.ai-applications」);回归时落 09.ai-applications 亦 PASS(母集 F18 可接受域:09.ai-applications 或 08.ai-foundations),落其他模块 FAIL。
- **溯源链口径**(`rule-engine-design.md` §5.2 裁决):三段式只管 Phase 3/4 的"几层"决策;R1 拆分 / R3 拒绝留原 Phase 0.2 / 2,只加 R# 标注 → P2/P4 **只验决策结果,不验溯源链**;P6-P10 为非 Phase 3/4 决策,**无溯源链要求**(依据规则列仅 P1-P5 必填)。
- 依据规则列口径:方式规则(几层)= R7-R10;位置规则 = R4/R5/R6;R23(简化 KB 降级)/ R25(建新模块选项)在 note KB(全角色齐备)不触发,故未列。
- **重建声明**:原 R0 十例表未入库(`cross-domain-evidence.md` Part D 仅存结论行 + "表格见对话记录"),本表从 66 场景母集**重建**;问法为母集采样改写,非原话复刻。采样来源:P1←precip-A2 分布式锁 · P2←precip-B6 大模型 5 问 · P3←precip-F18 Agent 实战框架 · P4←precip-G23 什么是变量 · P5←precip-H25 阿明餐厅的 RAG 故事 · P6←qa-A1 HashMap 线程不安全 · P7←qa-A2 出 JVM 面试题 · P8←qa-A3 如何设计 SSO · P9←health-A3 12.interview 单篇评分 · P10←precip-H24 修复 Redis 缓存穿透。

## P1-P10 基线表(签认对象)

| 探针 | 问法(母集采样) | 决策类 | 期望最终方案(方案级冻结) | 依据规则 / 注记 |
|------|---------------|--------|--------------------------|----------------|
| P1 | 「分布式锁」沉淀到 note(高频面试主题) | 双层 | 双层;位置 = interview + depth 两版互链;2 commit | R8(方式)+ R4/R5(位置) |
| P2 | 「大模型思维工程 5 个灵魂拷问」沉淀到 note(5 个并列子主题) | 拆分(多主题输入) | 拆为 single-topic 多文件(**只验决策结果**) | R1(Phase 0.2 标注) |
| P3 | 「Agent 实战框架」应该沉淀到 note 什么位置 | 位置决策 | 落 08.ai-foundations 主模块 | R5(位置);回归时落 09.ai-applications 亦 PASS(母集 F18 可接受域:09.ai-applications 或 08.ai-foundations),落其他模块 FAIL |
| P4 | 「什么是变量」沉淀到 note | 拒绝(一句话讲清类) | 不沉淀(**只验决策结果**) | R3(Phase 2 标注) |
| P5 | 「阿明餐厅的 RAG 故事」沉淀到 note(13.story 联动) | 叙事 | 13.story 三层联动(过 §3.5 准入) | R9(方式)+ R6(位置) |
| P6 | 「HashMap 为什么线程不安全?」(查 note) | QA A 型 | A 型:检索 ≥3 篇 + 📚 知识来源表 | 非 Phase 3/4 决策,无溯源链要求 |
| P7 | 出一道 JVM 面试题 | QA B 型 | B 型:题目 + 三层答案 + 陷阱表 + 话术模板 | 非 Phase 3/4 决策,无溯源链要求 |
| P8 | 如何设计 SSO | QA C 型 | C 型:方案对比表 + 推荐 + 设计点 | 非 Phase 3/4 决策,无溯源链要求 |
| P9 | 评价 `12.interview/01.java/hashmap-thread-unsafe` 这篇质量 | health 评分 | G1-G6 通用维 + 模块专属 E 类维生效 | 非 Phase 3/4 决策,无溯源链要求 |
| P10 | 如何在 note 里修复 Redis 缓存穿透 | Phase 0.1 询问 | 修复类意图 → 直接修复,不走沉淀规划 | 非 Phase 3/4 决策,无溯源链要求 |

## 回归结果(2026-11-19)

> **执行**: rule-engine-plan Task 6(IT 回归 + V3 顺手项 + 结果落库)· 对照 Task 4 后 SKILL(Phase 3/4 三段式)+ `rule-catalog.md` 逐探针重放;**基线表本体未改**,本节仅追加。
> **口径**: P1-P5 记 命中表/预案/裁决(溯源链;P2/P4 只验决策结果,依冻结说明)· P6-P10 记 回答类型/维度/分流(无溯源链要求)· 过程输出格式差异(三段式可见)允许,最终方案按「位置/层数/commit 数」比对。

### P1-P10 重放结果

| 探针 | 期望(冻结) | 实际(重放) | 结论 |
|------|------------|-----------|:----:|
| P1 | 双层;interview + depth 两版互链;2 commit | 双层;12.interview + 深度主模块两版互链;2 commit。溯源链:`R8(判据:预估 100-300 行 + 考试价值) + R4(判据:has_exam) + R5(判据:深度原理) → 综合 = 双层`;R10 排除(同栏目 troubleshooting 先例 <3) | ✅ PASS |
| P2 | 拆为 single-topic 多文件(只验决策结果) | R1 命中(Phase 0.2:编号「5 个」+ 并列子主题)→ 拆分为 single-topic 多文件,每子题独立 frontmatter | ✅ PASS |
| P3 | 08.ai-foundations 主模块(09.ai-applications 亦 PASS) | 09.ai-applications 主模块(工程子目录)。R5 位置判定:Agent 属 §1.5「09.ai-applications = RAG + Agent + Prompt + LLM 推理」,实战框架 → 工程子目录 | ✅ PASS(可接受域) |
| P4 | 不沉淀(只验决策结果) | R3 反信号命中(一句话讲清)→ 拒绝沉淀 | ✅ PASS |
| P5 | 13.story 三层联动(过 §3.5 准入) | 三层;12.interview + depth + 13.story 联动;3 commit。溯源链:`R9(判据:预估 300+ 行 + 叙事价值过准入) + R6(判据:has_narrative + has_story_role) → 综合 = 三层`;§3.5 准入 ①②③ 核心信号全过 + ④⑤⑥ ≥2 过 | ✅ PASS |
| P6 | A 型:检索 ≥3 篇 + 📚 知识来源表 | A 型(R13):检索 ≥3 篇深度 + 追踪 1-2 篇 → 解释 → 📚 知识来源表(必填) | ✅ PASS |
| P7 | B 型:题目 + 三层答案 + 陷阱表 + 话术模板 | B 型(R14):题目 + 三层答案 + 陷阱表 + 话术模板 | ✅ PASS |
| P8 | C 型:方案对比表 + 推荐 + 设计点 | C 型(R15):多模块检索 → 方案对比表 + 推荐 + 设计点 | ✅ PASS |
| P9 | G1-G6 通用维 + 模块专属 E 类维生效 | G1-G6 通用维(SPEC §5)+ 12.interview E 类面试题规则(leaf-quality 路由 `12.interview/** → E 类`) | ✅ PASS |
| P10 | Phase 0.1 询问:修复类 → 直接修复,不走沉淀规划 | R2 分流命中(关键词「修复」/「如何在 note 里 X」)→ 直接 Edit 修复,不走 Phase 1-7 沉淀规划 | ✅ PASS |

**结论:P1-P10 最终方案 10/10 与冻结基线一致,IT 回归零回退。**

### 降级探针抽测(note-kb-test 只读)

| 探针 | 期望 | 实际(重放) | 结论 |
|------|------|-----------|:----:|
| I2(invest KB,「定投 vs 一次性买入」沉淀需求) | 单文件 + 显式降级声明(硬造双层 = FAIL) | R23 命中(§1.5 无 interview/story 角色,任一缺失即命中)→ 显式排除 R4/R6/R8/R9;R7 单文件 → 03.planning depth 单文件 + 1 commit + 显式降级声明「无 interview/story 角色,跳过双层/三层」;R25 建新模块仅作附加选项、不作默认 | ✅ PASS |
| C12′(coffee KB,B 型出题) | 称谓「认证题 / 话术要点」,零「面试」原词 | qa SKILL 用词参数化(V1 修复)生效:按 §1.5「05.cert-qa = SCA 认证题 + 高频问答」替换 → 输出「认证题 + 三层答案 + 陷阱表 + 话术要点」,零「面试」字面 | ✅ PASS |

### Safeguards 三查 + 全库链接校验

| 项 | 范围 | 结果 |
|----|------|:----:|
| YAML 解析 | precipitation + qa + health 三个 SKILL.md | ✅ 3/3 OK |
| Phase 锚点审计 | CLAUDE.md + 本计划改过的 2 个 SKILL.md | ✅ 引用锚点(Phase 0.1/0.2/2/3.5/5.5/6.x/7 等)均存在,无改名断链 |
| 派发 smoke(3 类原话读检) | 3 个 skill description | ✅ "X 应该沉淀到 note 什么位置"→precipitation · "扫一遍 note"→note-health · "查 note"→note-knowledge-qa |
| 全库链接校验 | `check-broken-links.py` | ✅ .md 断链 0 / 目录断链 0 / 总计 0 |

> **同批顺手项**:V3 修复——`note-knowledge-qa/SKILL.md` F 型学习路径模板 IT 目录假设(「基础/进阶/源码/深度/实战」)域中立化为「按 `$KB_DIR/SPEC.md §1` 模块结构生成学习顺序」。
