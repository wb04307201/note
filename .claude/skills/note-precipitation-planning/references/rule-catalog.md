# rule-catalog: 规则目录(R1-R25)

> **Status**: v1(规则引擎单源)· **Created**: 2026-11-19 · 配套设计:`rule-engine-design.md` §5.1
> **来源**: 规则原文迁自 [`cross-domain-rule-trace.md`](../../cross-domain-rule-trace.md) Part 1A;Part 2 / Part 3 迁自 [`rule-engine-design.md`](../../rule-engine-design.md) §5.1
> **消费方**: [`SKILL.md`](../SKILL.md) Phase 3/4 三段式决策(Stage 1 规则命中表按 R# 判定 → Stage 2 预案集 → Stage 3 按 Part 2 裁决);谓词输入读 [`SPEC.md`](../../../../SPEC.md) §1.5 / §1.6
> **域中立**: 测试域实例(coffee / invest / fitness)不进本目录(留测试文件);规则文本保持域中立表述
> **语义单源纪律**: Phase 3/4 规则(R4-R10 / R23 / R25)语义在本表,SKILL 只引 R# 编号;其余规则语义留各自 SKILL phase 原地,本表只登记——两处不重复维护

---

## Part 1. 规则登记

R1-R25 全量登记。每条 schema:`规则一句话 / 来源 phase / 适用性谓词(如适用) / 预案片段(仅 11 条) / 语义位置`。

**分级(计划钉死)**:
- **完整预案片段**(形态 / 位置 / commit 数 / 理由)11 条:R4、R5、R6、R7、R8、R9、R10、R11、R23、R24、R25
- **仅登记**(一行摘要 + 语义位置指向)14 条:R1、R2、R3、R12、R13-R22(其中 R13-R21 标注「QA/health,流程暂不改」)

### R1 多主题拆分
- **规则**:多主题拆分:编号("N 个")/ 并列 / ≥3 互不相关子主题 → 拆多个 single-topic
- **来源**:precipitation Phase 0.2
- **语义位置**:语义见 SKILL precipitation Phase 0.2,流程暂不改

### R2 修复/新增分流
- **规则**:修复/更新 vs 新增分流(修复类不走沉淀规划)
- **来源**:precipitation Phase 0.1
- **语义位置**:语义见 SKILL precipitation Phase 0.1,流程暂不改

### R3 深度评估与拒绝
- **规则**:深度评估 3 信号(高频 / 够深 / 缺口真实);反信号(一句话讲清 / 已有 5+ 重复)→ 拒绝
- **来源**:precipitation Phase 2
- **语义位置**:语义见 SKILL precipitation Phase 2,流程暂不改

### R4 考试/问答价值定位
- **规则**:考试/问答价值高 → interview 角色模块
- **来源**:precipitation Phase 3 决策树
- **适用性谓词**:has_exam(读 SPEC §1.6);has_interview_role(读 SPEC §1.5)
- **预案片段**:形态=interview 问答版 · 位置=`<interview>/<topic>` · commit=随方式规则裁定(R7-R10) · 理由=考试/问答价值高由面试层承接
- **语义位置**:本表(Phase 3/4 语义单源)

### R5 深度原理定位
- **规则**:深度原理 → depth 主模块
- **来源**:precipitation Phase 3 决策树
- **预案片段**:形态=depth 深度版 · 位置=`<depth>/<topic>` · commit=随方式规则裁定(R7-R10) · 理由=深度原理由主模块承接
- **语义位置**:本表(Phase 3/4 语义单源)

### R6 叙事定位
- **规则**:叙事 → story 角色模块(三层需过叙事准入)
- **来源**:precipitation Phase 3 决策树
- **适用性谓词**:has_narrative(读 SPEC §1.6);has_story_role(读 SPEC §1.5)
- **预案片段**:形态=story 章节 · 位置=`<story>/<NN-xxx>` · commit=随方式规则裁定(R7-R10) · 理由=叙事价值高且过叙事准入,叙事层承接
- **语义位置**:本表(Phase 3/4 语义单源)

### R7 单文件
- **规则**:预估 < 100 行 → 单文件(1 commit)
- **来源**:precipitation Phase 4 决策树
- **落地复判边界带（N1 登记，2026-11-24 Phase C 收口批）**:95-105 行(系列带语境按该系列实测行数带,如 94-106);实施后 `wc -l` 复判流程见 SKILL Phase 7 自检条目
- **预案片段**:形态=单文件 · 位置=`<depth>/<topic>` · commit=1 · 理由=体量小(<100 行)无需分层
- **语义位置**:本表(Phase 3/4 语义单源)

### R8 双层沉淀
- **规则**:预估 100-300 行 + 考试/问答价值 → 双层(interview 版 + depth 版互链,2 commit)
- **来源**:precipitation Phase 4 决策树
- **适用性谓词**:has_exam(读 SPEC §1.6);has_interview_role(读 SPEC §1.5)——**谓词任一不满足 → R8 不命中**(缺 interview 角色时另被 R23 排除组收录,见 R23 与 Part 2)
- **预案片段**:形态=双层 · 位置=`<interview>/<depth>` · commit=2 · 理由=问答价值与深度需求并存 · **层门控注**:R8 整体由 interview 角色门控,缺 interview 角色时 R8 **整条被 R23 排除**(不投影、不缺省——双层无问答版即不成立;角色投影缺省只适用于 R9,见 R9)
- **语义位置**:本表(Phase 3/4 语义单源)

### R9 三层沉淀
- **规则**:预估 300+ 行 + 叙事价值(过叙事准入 6 信号)→ 三层(双层 + story 联动)
- **来源**:precipitation Phase 4 决策树
- **适用性谓词**:has_narrative(读 SPEC §1.6);has_story_role(读 SPEC §1.5)——**谓词任一不满足 → R9 不命中;其中 has_story_role=false 时另被 R23 排除**(R9 属 **story 门控组**:缺 interview 而 story 在 → R9 存活,按下方层位投影缺省 interview 层,见 R23 与 Part 2)
- **预案片段**:形态=三层 · 位置=**按角色投影** `<interview?>/<depth>/<story?>`(缺失角色层自动缺省并在溯源链显式声明:interview 缺 → `<depth>/<story>`,commit=2,即单角色 KB 终态;story 缺 → R9 谓词已不满足(R23 亦排除),不适用投影;双缺(interview+story 全缺) → R9 同样不适用,终态走 R23 双缺全降级(depth 单文件)) · commit=随存活层数(全三层=3 / 缺层=2) · 理由=体量大 + 叙事价值过准入,三层联动;缺角色层投影而非硬造路径
- **语义位置**:本表(Phase 3/4 语义单源)

### R10 先例覆盖
- **规则**:同类先例 ≥3(先例口径)且用户输入是生产 Bug 案例(同域实况案例类;其他域按 KB 谓词翻译表对译,如案例笔记/临床观察类)→ **覆盖 R8**,默认单篇版(落位=先例系列所在栏目,命名随先例系列惯例)
- **来源**:precipitation Phase 4 §1.8 先例对照
- **适用性谓词**:precedent_count ≥3(读 SPEC §1.6)
- **预案片段**:形态=单篇 troubleshooting 型(随先例体例) · 位置=**先例系列所在栏目**/`<现象>-troubleshooting`(角色投影,不硬编码 `<interview>` 层:先例系列在 interview 栏目则落 interview 栏目——note 双角色示例即如此;先例在 depth/其他栏目则落该栏目,不建 interview 层) · commit=1 · 理由=同类先例 ≥3,先例口径覆盖 R8 双层;落位/命名跟随先例=覆盖语义本身(角色无关,见 Part 2 R10×R23)
- **语义位置**:本表(Phase 3/4 语义单源)

### R11 批量三整理
- **规则**:批量沉淀三整理:合并(≥2 篇同主题)/ 拆分(≥500 行 + H2≥8 + ≥2 主题)/ 错位修正
- **来源**:precipitation Phase 6.1
- **预案片段**:形态=合并 / 拆分 / 错位修正 · 位置=原栏目合并、按主题拆分或迁移 · commit=逐动作 1 commit + 链接自检 · 理由=批量素材防重复与错位
- **语义位置**:语义见 SKILL precipitation Phase 6.1(原地保留;预案片段供 Stage 3 组合裁决)

### R12 词表写入
- **规则**:§8 词表写入(主题词有跨模块检索价值);工具链配置类 / troubleshooting 类跳过
- **来源**:precipitation Phase 6.10
- **语义位置**:语义见 SKILL precipitation Phase 6.10,流程暂不改

### R13 QA A 型
- **规则**:A 型:检索(≥3 篇深度 + 追踪 1-2)→ 解释 → 📚 知识来源表(必填)
- **来源**:qa Phase 3/4 A
- **语义位置**:语义见 SKILL qa Phase 3/4 A,QA/health,流程暂不改

### R14 QA B 型
- **规则**:B 型:题目 + 三层答案 + 陷阱表 + 话术模板
- **来源**:qa Phase 4 B
- **语义位置**:语义见 SKILL qa Phase 4 B,QA/health,流程暂不改

### R15 QA C 型
- **规则**:C 型:多模块检索 → 方案对比表 + 推荐 + 设计点
- **来源**:qa Phase 4 C
- **语义位置**:语义见 SKILL qa Phase 4 C,QA/health,流程暂不改

### R16 QA E/G 型降级
- **规则**:E/G 型:教育背景 / 招聘场景检测;无对应结构 → 降级预案(显式声明 + 给替代)
- **来源**:qa Phase 0/4(降级为通用化预期)
- **语义位置**:语义见 SKILL qa Phase 0/4,QA/health,流程暂不改

### R17 QA F 型
- **规则**:F 型:Level 1-4 知识地图 + 学习顺序 + 自测题
- **来源**:qa Phase 4 F
- **语义位置**:语义见 SKILL qa Phase 4 F,QA/health,流程暂不改

### R18 检索终止与引用校验
- **规则**:检索终止(≥3 篇深度 / ≤8 篇)+ 引用路径校验(os.path.isfile)
- **来源**:qa Phase 3.4/3.5
- **语义位置**:语义见 SKILL qa Phase 3.4/3.5,QA/health,流程暂不改

### R19 新文件基线
- **规则**:新文件基线:7 必选 + 3 可选结构
- **来源**:health new-file-baseline
- **语义位置**:语义见 SKILL health new-file-baseline,QA/health,流程暂不改

### R20 leaf 打分
- **规则**:leaf 打分:G1-G6 通用维度(+ 模块专属维度)
- **来源**:health leaf-quality
- **语义位置**:语义见 SKILL health leaf-quality,QA/health,流程暂不改

### R21 scope 分级
- **规则**:scope 分级:单篇不开重机器;leaf>50 全库走采样;报告含「策略选择」行
- **来源**:health Phase 0
- **语义位置**:语义见 SKILL health Phase 0,QA/health,流程暂不改

### R22 数字断言核实
- **规则**:数字断言(版本 / 费率 / 日期 / 量化)→ 触发核实或显式标注未核实
- **来源**:precipitation Phase 5.5
- **语义位置**:语义见 SKILL precipitation Phase 5.5,流程暂不改

### R23 简化 KB 降级(角色比例降级)
- **规则**:**简化 KB 降级 = 角色比例降级**:interview/story 角色模块**任一缺失即命中**,但降级范围**恒只限缺失角色所门控的形态选项**——缺 interview → 跳过 interview 门控形态(R4/R8 不可用);缺 story → 跳过 story 门控形态(R6/R9 不可用);**双缺**才整体降级(= depth 单文件 + 显式声明)。已声明角色的门控形态**存活**,不把该角色内容降级扔进另一角色单文件(如把叙事从已声明的 story 模块并入 depth 单文件,语义不成立)
- **来源**:precipitation Phase 3「简化笔记库」
- **适用性谓词**:has_interview_role / has_story_role(读 SPEC §1.5)——任一缺失即命中;**作用范围与缺失角色成比例**:缺 interview → 排除 R4/R8;缺 story → 排除 R6/R9(R25 story 联动仅作非默认附加选项、不作默认预案——排除组不禁 R25 建模块建议选项本身出现,见 R25 行 + trace 约定 5「选项出现≠FAIL」);双缺 → 排除 R4/R6/R8/R9
- **预案片段**:双缺:形态=depth 单文件(降级) · 位置=`<depth>/<topic>` · commit=1 · 显式声明。单缺:仅排除缺失角色门控的规则;存活角色侧终态取其门控规则预案——缺 story(有 interview):双层仍可用 `<interview>/<depth>` commit=2;缺 interview(有 story):story 门控形态存活,R9 缺省 interview 层 = `<depth>/<story>` commit=2(见 R9 层位投影) · 理由=降级杀的是「缺失角色承载的形态」,不是全库形态;声明时写明排除组与存活组两侧
- **单角色 KB 示例**:KB 声明 story 角色、无 interview 角色,沉淀「机制 + 叙事」组合素材 → R23 命中(缺 interview):排除 R4/R8(interview 门控组)并声明;**R6/R9(story 门控组)存活** → 终态 = depth 机制篇 + story 章节篇双向互链,commit=2 —— story 内容**不**降级进 depth 单文件
- **语义位置**:本表(Phase 3/4 语义单源)

### R24 系列互链
- **规则**:系列互链:新篇链所有兄弟 + 兄弟回链 + 系列导航表
- **来源**:precipitation Mistake 10 / Phase 1 步骤 1.5(系列结构检查→系列内互链义务;N8 修正 2026-11-24:旧注「Phase 1.7」为已跳号步骤,Mistake 10 本体在位不动)
- **适用性谓词**:is_series(读 SPEC §1.6;目标目录存在编号系列,运行时 find 判定)
- **预案片段**:形态=随主预案 + 互链义务 · 位置=原系列目录 · commit=随主预案 · 理由=系列双向互链 + 导航表更新
- **语义位置**:语义见 SKILL precipitation Mistake 10 / Phase 1 步骤 1.5(原地保留;预案片段供 Stage 3 组合裁决)

### R25 建新模块选项
- **规则**:建新模块 / 新角色模块是合法**附加选项**(走 MODULE-CREATION SOP),但不得作为默认方案违反 R23
- **来源**:precipitation Phase 3.5
- **预案片段**:形态=新模块(附加选项,非默认) · 位置=新建 `<NN.xxx>/` · commit=按 MODULE-CREATION SOP · 理由=缺角色模块时可建议建模块,默认方案仍走 R23 降级
- **语义位置**:本表(Phase 3/4 语义单源)

---

## Part 2. 覆盖与组合序

综合裁决的裁决规则(从设计 §5.1 原样迁入):

- **覆盖**:R23 ⊃ R4/R6/R8/R9(简化 KB 降级——**角色比例**:覆盖对象恒为缺失角色所门控的那组规则:缺 interview → R23 ⊃ R4/R8;缺 story → R23 ⊃ R6/R9;双缺 → 四者全 ⊃;**已声明角色门控的规则不被 R23 覆盖**,即单缺时 R6 仅 story 缺才 ⊃、R9 仅 story 缺才 ⊃)· R10 ⊃ R8(先例覆盖)· R2 修复类不走沉淀
- **R10 × R23 优先级(补定义)**:R10 的「先例覆盖」语义**角色无关**——缺 interview 角色**不排除** R10;其覆盖对象 R8 虽已被 R23 排除,R10 的独立价值(单篇形态 + 先例命名惯例 + 落位)仍存活并优先于「R23 命中即全降级」的字面读法。**R10 落位 = 先例系列所在栏目**(按 R10 预案片段的角色投影,不硬编码 `<interview>` 层)。
- **组合**:R11+R8(合并式统一深读 + 新问答版)· R11+R5(合并式深读)· R25 为合法附加选项但不得违反 R23
- **冲突未定义** → 记「规则缺口」不算 skill 错(沿用测试判定基准)

---

## Part 3. 适用性谓词与默认值

适用性谓词(Tier 1,不写 git/载体条款)。**默认值列**:无 §1.6 的 KB 按默认语义——默认值 = 按角色推导(§1.5 是必填、§1.6 是精化层):

| 类 | 谓词 | 读取处 | 默认值(无 §1.6 时) |
|----|------|--------|---------------------|
| 角色 | has_interview_role / has_story_role | SPEC §1.5 | (§1.5 必填,无默认) |
| 场景 | has_exam(考试/问答价值) | SPEC §1.6 | **= has_interview_role**(有面试角色即视为可出问答版) |
| 场景 | has_recruiting(招聘语境) | SPEC §1.6 | **= has_interview_role** 且模块含方法论类内容 |
| 叙事 | has_narrative(叙事价值) | SPEC §1.6 | **= has_story_role** |
| 口径 | precedent_count(先例计数) | SPEC §1.6 | 同类先例 ≥3(口径:同栏目「-troubleshooting / 案例」类) |
| 口径 | is_series(系列) | SPEC §1.6 | 目标目录存在编号系列(运行时 find 判定) |

> 默认语义保证两头:有角色 KB(→ 双层可用)行为不变;无角色 KB 走 R23 降级(测试验证路径),不硬造语义。
