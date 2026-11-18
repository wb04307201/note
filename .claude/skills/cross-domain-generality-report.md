# 跨领域通用性测试报告（3 skill × 4 域）

> **Status**: Phase A-D 全部完成（2026-11-16）· 设计：`cross-domain-generality-test-design.md` · 规则溯源：`cross-domain-rule-trace.md` · 逐场景证据：`cross-domain-evidence.md`
> **范围**：26 个非 IT 场景（coffee 12 + invest 8 + fitness 6）+ R0 IT 决策基线 10 例 + Safeguards

## 1. 结论

**机制层域中立性：强证据成立。** 26 场景 **24 PASS + 2 DEGRADE（均为签署预期命中）+ 0 FAIL**。所有结构/流程机制（决策树 R1-R25、批量三整理、系列义务、词表协同、体检扫描、QA 检索）在咖啡/投资/健身三个非 IT 域全部正确运转；发现集中在**概念层**（词汇、契约、模板），无一破坏机制。

**IT 安全性：R0 基线 10/10 与 2026-09-03 期望一致**——改进空间存在，但当前 IT 行为完好（回归前提成立）。

## 2. 场景矩阵终版

| 组 | 结果 | 核心数据点 |
|----|------|-----------|
| C1-C12（coffee 中 KB 102 leaf） | 11 PASS + 1 DEGRADE | R8 双层 / R11 合并×2 / R9 三层 / R1 拆分 / R11 批量三整理（合并 2·拆 1·移 2 分毫不差）/ R24 系列 / R10 先例覆盖 / R12 词表双向 / R13-C11 QA / R19-C9·R21-C10 health / C12 B 型词汇 DEGRADE |
| I1-I8（invest 无角色 KB） | 7 PASS + 1 DEGRADE | **R23 降级三重**（深度/问答/叙事形态）+ R16 E 型优雅降级 + R22 口径 + I5 B 型词汇 DEGRADE |
| F1-F6（fitness 无角色 KB） | 6 PASS | R23 三角复现 / R15 / R17 / R1 拆分三角 / **R3 拒绝** / R20+N/A 声明 |
| R0（IT 对照） | 10/10 一致 | 双层/拆分/拒绝/13.story/QA 三型/E 维度/Phase 0.1 询问——全命中 |

**三角归因验证**：R23 降级（I1+F1）、R1 拆分（C4+F4）、词汇 DEGRADE（C12+I5）、R11 合并（C2+C5）四组跨域复现 → 真耦合/真机制双向确证。

## 3. 发现归账（三分类）

### ① skill 缺陷（机制层，无 P0；1 P1 + 2 P2）

| # | 发现 | 级别 | 证据 |
|---|------|:---:|------|
| S1 | **QA Phase 0 顺序错位**：E/G 触发词下教育背景检测无条件先行，在无招聘语境 KB 上先判专业再发现无题库——降级判断应前置 | P1 | I6 |
| S2 | skill 产出的「相关章节」回链纪律弱于 checklist 承诺（3/6 采样篇有单向链） | P2 | C10 |
| S3 | Phase 1.6 单向链接口径未分层（README→leaf 索引行与正文链混报，与 1.13 三分类打架） | P2 | C10 |

### ② 契约-文档缺口（3 P1 + 2 P2）

| # | 发现 | 级别 | 证据 |
|---|------|:---:|------|
| K1 | **契约缺口孪生**：skill 文本引用 `<story>/SPEC.md §3.5`、`<interview>/SPEC.md §5`，但 STARTUP-NEW-KB 未要求 L1 配这两节 → 借 KB 时准入判定/Bug 特化无规则来源（先例格式兜底） | P1 | C3、C7 |
| K2 | **new-file-baseline 模板冲突**：7 必选段（🎯学习目标/📚章节清单含时长）是 note 课程式模板，与借 KB 自有 SPEC 结构要求不一致，无裁决规则 | P1 | C9 |
| K3 | **模块 dispatch 硬编码**：leaf-quality A~G 规则集逐字绑定 note 13 模块路径——跨 KB 时专属维度整体失效（note 主库上正常命中 E 类 = 特化非 bug） | P1 | C9、F6、R9 |
| K4 | STARTUP-NEW-KB.md 内容过时（§5 仍称 v3.x 未实施、推荐 12.interview 命名 workaround） | P2 | C3 对照 |
| K5 | tags↔§8 桥接口径错配（自由标签 vs 路由词表，185/202 天然差异） | P2 | C10 |

### ③ 领域失配（词汇/模板，2 P1 + 3 P2）

| # | 发现 | 级别 | 证据 |
|---|------|:---:|------|
| V1 | **响应模板层词汇耦合**（三角确认）：A/B/C 回答模板与出题模板携带「面试题/面试话术/科班」——文章层有 KB SPEC §4 覆盖机制（C1 输出干净），响应模板层**无覆盖机制**（C12/I5 原词输出） | P1 | C12、I5、C1 |
| V2 | 5-dim rubric 锚点 IT 化（D1「源码级+JVM/字节码」、D3「面试频次」） | P1 | 规则溯源预判、C9 对照 |
| V3 | F 学习路径模板假设「基础/进阶/源码/深度/实战」目录约定（IT 学科结构） | P2 | C12、F3 |
| V4 | Phase 5.5 窄查询模板 `<产品> <特性> version release` 型，非 IT 域需人工转译（降级链本身运转良好） | P2 | C1 起 |
| V5 | 13.story 路径残留（Phase 4 树一处字面引用） | P2 | C3 |

## 4. Phase B 改进清单（✅ 已批准并实施 · 2026-11-16）

**P1 六项全部落地**（6 文件手术式修改 +32/-16）：V1 响应模板词参数化（qa + precipitation 双文件）· S1 降级判断前置（Phase 0.0 招聘语境检查）· K3 dispatch KB 自定义化（note 13 模块降为示例）· K2 基线裁决规则（KB SPEC 优先）· V2 5-dim 锚点域中立化 · K4+K1 STARTUP-NEW-KB 更新（v3.x 状态修正 + §1.5/§1.6/L1 契约声明 + workaround 废弃）。

**Phase C 回归：通过**。Safeguards 三查全过（YAML/锚点/派发）；R0 十例决策语义不变（模板默认词「面试」在 note KB 原样保留 = 变宽不变差；双层模板/Phase 0.1 行为未动）；S2 精简冒烟（note-temp 结构在，缺链接脚本 = P2 备注）。

**Phase D 复测：通过**。C12′/I5′ 双域 B 型出题零「面试」原词（coffee→「认证题/话术要点」、invest→「练习题/要点」，称谓取自 §1.5 角色语义）——2 DEGRADE → **PASS 转化**。

**P2 待办**（下轮）：1.6 口径分层 · 回链 checklist 强化 · tags↔§8 口径说明 · F 模板目录参数化 · Phase 5.5 域模板位 · 13.story 残留清理 · note-temp 链接脚本同步。

**P1（六项，建议本轮做）**
1. **响应模板词汇参数化**（V1）：A/B/C/D/E/F/G 模板的「面试」系列词改为按 `SPEC.md §1.5` 角色名动态取词（如 interview 角色名 = 「认证问答」时模板自动替换）——沿 v3.x 参数化老路
2. **STARTUP-NEW-KB.md 更新**（K4+K1）：v3.x 状态修正 + §1.5/§1.6 契约要求补齐（story §3.5 / interview §5 可选项声明）
3. **leaf-quality dispatch 参数化**（K3）：A~G 表改为「KB 自定义模块维度（`<module>/SPEC.md`）+ N/A 声明指引」，note 13 模块作为示例保留
4. **new-file-baseline 裁决规则**（K2）：声明「KB 自有 SPEC 优先，基线为缺省模板」+ 必选段名参数化
5. **QA Phase 0 顺序调整**（S1）：E/G 流程先做「KB 是否有招聘语境」降级判断，再进教育背景检测
6. **5-dim rubric 锚点改写**（V2）：D1/D3/D4 锚点域中立化（「源码级」→「机制底层」等）

**P2（五项，可下轮）**：1.6 口径分层（S3）、回链 checklist 强化（S2）、tags↔§8 口径说明（K5）、F 模板目录参数化（V3）、Phase 5.5 域模板位（V4）、13.story 残留清理（V5）。

**反目标守则**（改进时必须遵守）：不许全局替换稀释 IT 特化价值——所有改动走 §1.5/§8/`<module>/SPEC.md` 参数化，note 主库行为只能变宽不能变差；改完跑 Phase C 回归（R0 十例 + Safeguards）。

## 5. 附录

- 逐场景证据（决策链/选项原文/回验 grep）：`cross-domain-evidence.md`
- 规则库 R1-R25 / K1-K5 + 26 行溯源表：`cross-domain-rule-trace.md`
- 测试 KB：`D:/developer/IdeaProjects/note-kb-test/{coffee,invest,fitness}`（git 留档，含场景快照 tag）；源素材 `_source/coffee-c5/`
- fixture 债（非 skill 发现，已单列）：生成期回链不对称若干 + 语义弱链候选——留 C10 式体检二分归账
