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
