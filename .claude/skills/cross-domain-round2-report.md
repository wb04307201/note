# 跨域通用性测试 R2 报告（终版）

> **Status**: 终版（Task 15，2026-11-24）——**Phase A（发现，26 场景全 PASS）/ B（修复，GATE 批准清单 P1×6 + P2×10 全落地）/ C（IT 回归，R0 双比对 10/10 · Safeguards 4/4 · 零 revert）/ D（复测，探针 5/5 PASS + F0 文本级静态断言 9/9 位一致）全部完结**。本报告的「达成」结论覆盖修复闭环全程；Phase C 记录见文末「回归结果」节，Phase D 复测与终版验收见文末「Phase D 复测与终版收口」节及 §7。
> **标尺链**: 设计 `cross-domain-round2-test-design.md` → 溯源表 `cross-domain-rule-trace.md` R2 节（已签认冻结 2026-11-23）→ 证据 `cross-domain-evidence-r2.md`（H/L/M/R0 四节）→ R0 基线 `cross-domain-r0-baseline.md`（冻结 2026-11-19）
> **执行方式**: 测试执行者读 3 个 SKILL.md + rule-catalog.md 后按文档化 Phase 亲自执行（inline，非黑盒）；沉淀类场景在测试 KB 全实施（含 commit），note 仓库全程 read-only。

## §1 结论（G1-G6 达成状态）

| Goal | 判定 | 依据 |
|------|------|------|
| **G1 通用**：26 非 IT 场景 0 FAIL + 跨域复现 DEGRADE 复测转 PASS | ✅ **达成** | 26 PASS / 0 DEGRADE / 0 FAIL（health 12 + law 8 + music 6，逐行对冻结表判定在证据文件）；Phase D 探针复测 5/5 PASS（H3/H7/L2/M5/M3 按快照重跑，post-fix 引擎决策与注册期望恒等，明细见证据文件 `## Phase D 复测证据` 节与本文 §4.3）；「DEGRADE 修复后复测转 PASS」本轮无原 DEGRADE 行需复测（V4 为已知-已排期口径，F0 分岔以 §4.4 静态断言代证） |
| **G2 稳定**：R0 十例 10/10 + Safeguards | ✅ **达成** | Phase A 重放 10/10 与冻结基线一致 + **Phase C post-fix 双比对 10/10 一致、0 revert**（文末「回归结果」节）；Safeguards 修改前/后各一轮全过（YAML 3/3 · 锚点审计 · 派发 smoke 3/3 · 全库链接 0/0），N8 修复复验通过 |
| **G3 可用**：降级全显式、三段式全完整 | ✅ **达成** | R23/R16 类降级路径 26 场景均显式声明零卡死；沉淀类三段式逐字落证据；Phase D 复测中双缺行显式声明义务维持（声明三处仍要求）、单缺行存活/排除组两侧仍写明——修复后全部降级仍显式 |
| **G4 引擎溯源质量**：断链/编造 R# = FAIL 可追溯 | ✅ **达成** | 全 26+10 例溯源链 R# 均可解析回 rule-catalog，无编造 R#、无缺段（三轮 reviewer 独立审计确认）；Phase D 复测溯源链同样逐段可解析 |
| **G5 单角色中 KB 规模启发式** | ✅ **达成** | health（有 story 无 interview，终态 **106** leaf 实测）：采样/系列（H6 N=11 运行时）/先例（H1 排除、H7 先例 3≥3）/分批均按冻结口径正确运转；Phase D 在快照上运行时先例复算（find=3）口径不变 |
| **G6 P2 背包闭环 + F0 修复** | ✅ **达成**（含诚实限定 ×2，见下） | GATE 批准清单 **P1×6 + P2×10 全落地**（commits `aee536c`/`24e7843`/`645e756`/`4b038ff`/`233f561` + music KB `630d906`，明细 §5）；Phase C 回归零 revert；Phase D 探针复测 5/5 PASS + **F0 文本级静态断言 9/9 位一致**（§4.4，D2 推荐口径）。限定 1：F0 分支 2 的 live 复现以静态断言替代（结构性不可达，非回避）；限定 2：R22 真核实支仅正例 ×1（D1，§3.4） |

**一句话总判**：规则引擎（三段式 + R# 溯源链 + §1.5/§1.6 谓词层）跨域首考**通过**且**修复闭环完成**——Phase A 26+10 全 PASS、Phase B 17 项修复全落地（16 批准项 + 1 顺手 polish）、Phase C 零回退、Phase D 探针决策恒等且裁定语义升级为**文本唯一机械读法**（F0 矛盾在活文档层已消失）。遗留可见限定：**D1**（R22 真核实支仅 1 正例）与 **D2**（F0 分支 2 以静态断言替代 live 复现），见 §3.4。

## §2 场景矩阵终版

### 2.1 非 IT 26 场景（全部 PASS，判定明细在证据文件）

| 域 | # | 场景（简） | 规则面 | 判定 | 核心数据点 |
|----|---|-----------|--------|:----:|-----------|
| health（12） | H1 | 睡眠双进程整合篇沉淀 | R5/R7/R23/R10 排除 | PASS | 单文件 depth 78 行，1 commit |
| | H2 | 维 D 补充决策篇沉淀 | R5/R7/R22/R23 | PASS | 95 行；R22 转引+未核实标注（通道受阻 fallback） |
| | H3 | 罕见病诊疗叙事【**探针**】 | R5/R6/R7/R9 排除/R23 | PASS(分支 1) | depth 82 行 + story 63 行（第 13 章；N=13 运行时），2 commit；准入 6 信号过检 |
| | H4 | 补钙 5 误区拆分 | R1(+R22/R24 条件) | PASS | 5 篇（56/56/67/67/56 行），5 commit，兄弟互链+五谈导航 |
| | H5 | 批量导入 15 篇 | R11/R5/R22/R23 | PASS | 合并 2 组/拆 1→2/移 2/正常 8=14 产出，14 commit；弃用 2 节（controller 裁定成立） |
| | H6 | 常见病系列第 11 篇 | R24/R22(+R5/R7) | PASS | N=11 运行时，10 兄弟互链+导航全更，1 commit；**实测 101 行 >R7 预估带 →N1** |
| | H7 | 新临床案例【**探针**】 | R10/R23/F0-e | PASS(分支 1) | clinical-case-04（非 -troubleshooting），1 commit（O2 口径），零「面试」，§8 跳过；落地后先例=4 |
| | H8 | 词表维护 | R12 | PASS | §8 痛风行+tags 同 commit；对照跳过+理由；O4 频次 `-` |
| | H9 | 新篇评分（11-gout） | R19/R20/R21 | PASS | 基线 7+3（health 语境转译声明）+12/12+专属维 N/A |
| | H10 | 全库扫描 | R21/R20 | PASS | leaf=106 实测 →采样不询问；1.14 空转=预期；workflow 不可用→SKILL 明文手工降级 |
| | H11 | 「什么是免疫」 | R13/R18 | PASS | A 型，3 深读+2 追踪，isfile 6/6 |
| | H12 | 出题 | R14/R23(V1) | PASS | 练习题/三层/陷阱/要点/📚；grep「面试」=0 |
| law（8） | L1 | 违约赔偿范围机制篇 | R5/R7/R22/R23 | PASS | 85 行 1 commit；双缺声明；R10 跨栏目不命中 |
| | L2 | 条文修订+「讲成故事」【**探针**】 | R6 死/R23/R24/R22 | PASS(收敛) | 02/05 单文件 80 行，1 commit；声明三处；谓词值引用；两读法收敛=B.3 预注册 |
| | L3 | 租房 3 陷阱拆分 | R1/R24/R12 | PASS | 06/07/08（83/73/86 行），3 commit；§8 租赁行同 1/3 commit；commit 切分自纠在案 |
| | L4 | 民法系列第 09 篇 | R24/R22 | PASS | N=09 运行时，8 兄弟互链，1 commit 严格终态；87 行无漂移 |
| | L5 | 出题 | R14/R23(V1) | PASS | 零角色域降级；grep「面试」=0，isfile 12/12 |
| | L6 | 租房清单设计（C 型） | R15/R18 | PASS | 3 方案对比+5 设计点；**冻结前置③运行时翻转 →N4** |
| | L7 | 项链欺诈数额断言 | R22/R13 | PASS | 三断言逐一核实（②纠错→保底 500）；V4 复现=已知桶 |
| | L8 | 「什么是物权」沉淀 | R3 | PASS | 拒绝+理由+边界转介（只验结果） |
| music（6） | M1 | 和声节奏机制篇 | R5/R7/R22 不命中 | PASS | 77 行（M5 后 78）1 commit；软域纯度双零 |
| | M2 | 练习计划设计（C 型） | R15/R18 | PASS | 权衡式对比；**延伸行前视引用=hygiene →N5** |
| | M3 | 学即兴伴奏（F 型） | R17(V3 复验) | PASS | **V3 跨域复验闭环**；IT 目录名零落位；**F 模板层目录占位 →N3** |
| | M4 | 练琴 3 误区拆分 | R1/R11 不触发 | PASS | 3 篇（61/59/65）；commit 4≠3（controller 裁定 PASS 维持）；**→N6/N7** |
| | M5 | 拉赫二协「创作故事」【**探针**】 | R6 死/R23/R25 护栏 | PASS(收敛) | 技艺笔记体 57 行 1 commit；声明三处+§1.6 口径注记+护栏；与 L2 同构同处置 |
| | M6 | 单篇评分（chopin） | R20/R21 | PASS | 软域 G1-G6 12/12；专属维**显式 N/A**；未开 workflow |

### 2.2 R0 IT 对照 10 例（详见证据文件 `## R0 证据` 节）

| P1 | P2 | P3 | P4 | P5 | P6 | P7 | P8 | P9 | P10 | 汇总 |
|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:---:|:----:|
| ✅ | ✅ | ✅(可接受域 09) | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **10/10 一致** |

Safeguards：YAML 3/3 ✅ · 锚点审计 ✅（1 处轻漂移：R24「Phase 1.7」指针→现为步骤 1.5/1.8，记 Phase B 顺手项）· 派发 smoke 3/3 ✅ · 全库链接 0/0 ✅。

### 2.3 核心数据点（全部 2026-11-23 find/git 实测，非快照引用）

| 指标 | health | law | music | 备注 |
|------|--------|-----|-------|------|
| 场景数 | 12 | 8 | 6 | 合计 26 |
| 判定 | 12 PASS | 8 PASS | 6 PASS | **26 PASS / 0 DEGRADE / 0 FAIL** |
| leaf（终态，排除 README/SPEC） | **106**（01:24/02:34/03:17/04:18/05:13；全 .md=113） | **16**（基线 10+6 新） | **15**（基线 10+5 新） | 基线：81/10/10（trace 0.3） |
| KB commits（场景期） | **26**（d51a182..HEAD） | **6**（95284d2..cffb9ec） | **6**（eb3dc6e..1dc0cda）；终态 HEAD 再 +1（**7**，eb3dc6e..630d906=630d906 为 Phase B N7 修复 commit） | scope 合规（fix round 后无残留违例）；health/law/music 终态 HEAD 见 §4.3 |
| 快照 tags | 8（H1-H8） | 5（L1/L2/L3/L4/L7） | 3（M1/M4/M5） | 16 个，Phase D 复测锚点 |
| 断链 | 0/0 | 0/0 | 0/0 | 每状态变更 commit 后均跑 |
| 工作树 | clean | clean | clean | note 仓库执行期仅证据文件变化 |

note 仓库：R0 10/10 一致；全库链接扫描 1148 .md · 断链 0/0/0。

## §3 发现归账（三分类 + 内容问题 + 已知桶 + controller 裁定）

### 3.1 ① skill 缺陷

| # | 层 | 发现 | 证据 | 严重度 |
|---|----|------|------|:------:|
| F0（预注册） | **语义层** | 语义单源完整性破坏：R23 正文（双缺才降级）vs 谓词（任一缺即命中）vs SKILL 选项级排除三处不一致（F0-a/b/c）+ R9 预案 `<interview>` 硬编码（F0-d）+ R10×R23 优先级未定义（F0-e） | trace 0.1/B 节；本轮实证：单缺域引擎走裁定读法（H3/H7 溯源显式对照字面读法后弃用），双缺域两读法收敛——**文本矛盾客观存在，P1 维持；Phase B 必改** | **P1** |
| N1 | **引擎层** | R7 判据用「预估行数」，落地超界无复判步骤（H6 实测 101>100；Phase 7 数字校对不覆盖规则边界复判） | 证据 H6 判定块/意外发现；H 轮 reviewer 复核 PASS 成立（预估≠落地，101∈系列带 94-106） | P2（轻） |
| N2 | **既有机制层** | R11 对「已覆盖碎片」的处置权限无边界定义——H5 大讲义拆分中 2 节判已覆盖直接弃用，未单独 surface 为 Phase 5 选项 | 证据 H5；controller 裁定：冻结行只冻输入组成不冻产出节数，弃用=防重复语义，**PASS 成立**；边界定义属 Phase B 候选 | P2（轻） |
| N3 | **语义层** | qa F 模板 `{模块A}/{入门层目录}` 结构占位隐含「子目录存在」假设，平铺 KB 依赖 §2.1 降级条款兜底——V3 修了目录名词汇、未修目录层级结构假设 | 证据 M3 意外发现（归因①轻）；M3 四项硬判据全中仍 PASS | P2（轻） |

### 3.2 ② 契约-文档缺口

| # | 发现 | 证据 | 处置口径 |
|---|------|------|---------|
| O1（预注册） | R7 阈值 catalog **100** vs SKILL「3 大沉淀模式」表 **<150 行** 双源不一致 | trace 0.2；SKILL L79 本轮复测在文 | 本表采 100；Phase B 对齐措辞（P1 文本级） |
| O2（预注册） | R10 commit catalog=**1** vs SKILL Quick Reference=**2-3** | trace 0.2；SKILL L630 本轮复测在文 | 采 catalog（H7 已按 1 执行）；Quick Reference 残留 Phase B 对齐（P1 文本级） |
| O3（预注册→本轮确认） | health `05.medical-stories/SPEC.md` 缺位（叙事准入 6 信号本地读取处） | H3 按 O3 冻结口径用 note `13.story/SPEC.md §3.5` 通用 6 信号+05 惯例**成功执行，流程未失效** → 两步策略不触发，单步记账；H9 模块专属维 N/A 同族事实 | 缺口本体=补配置议题（KB 侧/Phase B），与 skill 修复分开 |
| N4 | 约定 8「运行时 find 为准」只覆盖 N 值/兄弟数/先例数，**未覆盖「缺口真实/无专篇」类输入谓词的动态翻转**（L6 冻结前置③被 L3 执行时序推翻） | 证据 L6 运行时修正记录；L 轮 reviewer 判「合法缺口发现非擅改」 | Phase B：约定 8 扩写「缺口/覆盖类前置以执行时点复测」 |
| N5 | QA 输出「capture-before-next-scenario」执行协议缺位——M2 逐字块延伸行前视引用了 M4 才创建的 3 文件（违反当时点 §3.5 校验义务；📚 主表 7 路径不受影响，PASS 维持） | 证据 M2 块头出处注记+偏差记账；Task 10 review FIX 1 已闭环 | Phase B：测试执行协议补 capture 时点条款 |
| N6 | 拆分行（M4 型）缺 H6/L4 式「commit 数非硬判据」免责声明——M4「共 3 commit」字面 vs 终态逻辑冲突（README 补登记致 4） | trace A.3-M4；controller ruling：PASS 维持（终态硬判据完整），措辞缺口成立 | Phase B：拆分行 commit 硬/辅判定口径统一 |
| N7 | 软域纯度扫描口径两处：① music SPEC §6 类 6 判词 grep 字面口径命中被审视信条**引号内原文**（基线既有文件同态命中），需「作者陈述句 vs 引语/元讨论」二级口径；② 「数字+单位」联合模式 `[0-9]+` 对中文数字（八小节/十几秒）**盲区** | 证据 M4 意外发现①+M 节纯度扫描；Task 10 review carry-forward | Phase B：检测方式列补二级口径 + 中文数字形 |
| N8 | 锚点元数据漂移：rule-catalog R24「来源: Mistake 10 / Phase 1.7」+ SKILL L263 同引，现 SKILL Phase 1 步骤号无 1.7（1.6→1.8 跳号，载体为步骤 1.5/1.8；Mistake 10 本体在位） | 本轮 Safeguards 锚点审计新见 | Phase B 顺手项：改注现存步骤号，非回退 |

### 3.3 ③ 领域失配

| 发现 | 状态 | 说明 |
|------|------|------|
| `<interview>` 落位 / `<现象>-troubleshooting` 命名 /「面试话术」节名 /「源码」层占位 | **预注册内（F0-d/O 桶），零新增** | H7 溯源中显式裁定弃用，未硬造不存在路径；H12/L5「源码」残留=未触发；M3 IT 目录名零落位 |
| V4 Phase 5.5 领域 query 模板无法律行 | **已知-已排期**（背包 4），L7 复现=是 | 行为正确全落 fallback；不重复计新发现 |

### 3.4 测试设计/环境侧注记（不计 skill 缺陷）

| # | 注记 | 影响 |
|---|------|------|
| D1 | **R22「真核实」支零覆盖**：沙箱 WebSearch 空/WebFetch 拦截/fetch MCP 超时，H+L 两域 5+ 场景全部只走「转引+显式未核实标注」fallback 支 | 跨域结论对「核实成功路径」仍无证据；music 无断言故无压力；Phase C 若在可用网络环境跑 note-temp 冒烟可部分补 |
| D2 | **F0 分支 2（catalog 字面全降级）本轮零触发且当前协议下不可复现**：引擎阅读面恒为 SKILL+catalog 同读，F0-c 选项级排除示例承载裁定意图（详见 §4） | G6「DEGRADE 探针 Phase B 修后复测转 PASS」计数=0；复现需 catalog-only 对照执行或 Phase B 文本对齐后静态断言 |

### 3.5 内容问题单列（KB fixture 问题，非 skill 发现）

| # | 问题 | 记账 |
|---|------|------|
| C1 | health 根 README「81 篇 leaf」vs 实测 106、04 README summary「首批 10 项」vs 11 篇 | H10 报告 P1 Batch 1 → **终审改判：「收口批修」未执行，属外部 health KB fixture 侧 open backlog**（R3 批处理或 closed-as-fixture；体检只读不越界，本轮不动 health KB；HEAD 实测 README「81 篇」仍在） |
| C2 | 行数落带偏差：H4 三篇 56 行、M1 77 行、M4 二篇 59 行低于假设带下沿；H6 101 行超上沿（同 N1 边界带） | 记录口径；R7 硬判据均不受影响 |
| C3 | §8 频次字段随场景累积漂移（health 4 词、law 新增 2 行 `-`、music 练习方法 4→7） | O4 允许；KB SPEC 测试期只读 → **终审改判：「收口批统一重算」未执行，属外部 KB fixture 侧 open backlog**（R3 批处理或 closed-as-fixture） |
| C4 | 输入口径用词形差：H1 快照 grep「双进程」vs KB 实际「双过程」 | 缺口判定不受影响；Phase B 输入属性口径可固定用词变体清单 |
| C5 | law KB 内容瑕疵（终审补记，恢复 ledger Task 5「内容问题单列」口径）：`01.legal-basics/sources-of-law-effect-hierarchy.md:31`「第 1260 款」应为「条」+ :77 链文「逾期办证」vs 目标案例实为「逾期交房」+ 02 系列冷静期口径注记 | KB fixture backlog（外部 law KB，非 skill 发现；R3 fixture 批处理或标 closed-as-fixture） |

### 3.6 已知-已排期桶（不重复计数）

R1 P2 背包 6 项中：**V4 复现=是**（L7，见 3.3）；**V1 已修复验通过**（H12/L5/健康 grep 全 0，非新发现）；**V3 已修复验闭环**（M3 PASS）；S3/S2/K5/V5/note-temp 同步本轮无新复现。M2 hygiene（N5）为 R2 新增执行协议项，与 R1 背包不重叠。

### 3.7 controller 裁定 carry（裁定项，非新发现）

1. **M4 PASS 维持**（Important#2 frozen-row conflict ruling：终态逻辑 benign，第 4 commit 仅完成父 README 登记硬判据）。
2. **H5 弃用 2 节 PASS 成立**（冻结行只冻输入组成+三整理动作，不冻产出节数；弃用=R11 防重复语义+三层披露）。
3. **H6 101 行 PASS 成立**（R7 谓词是预估非落地；101∈系列带 94-106）。
4. **law SPEC §8 加行（租赁/保证）= R12 强制伴随产物**（Phase 6.10 write-time 同步协议），不构成「SPEC 只读边界」违背。

## §4 冲突探针专项核查（H3 / H7 / L2 / M5 四行并排）

### 4.1 同构输入处置一致性（B.0 谓词差异表复核）

| 行 | KB | has_story / has_interview | 预期处置 | 实际引擎分支 | 溯源完整性 |
|----|----|---------------------------|---------|-------------|-----------|
| H3 | health | **true** / false | 门控存活：R6 落地 story | **分支 1（裁定）** | ✅ R23 选项级排除引用 §1.6 谓词值+两读法显式对照；准入 6 信号自证节；N=13 运行时；commit=2 |
| H7 | health | true / false | R10 存活，落先例栏目 | **分支 1（裁定）** | ✅ R10 判据（先例 3≥3+谓词翻译）+落位裁定理由+**F0-e 缺口显式声明**+O2 commit=1；零「面试」 |
| L2 | law | **false** / false | 双缺收敛：叙事降级 | **两读法收敛**（裁定口径记录） | ✅ B.3 三判据全中：终态+**显式声明三处**+溯源含谓词值（双 false 对）；硬造=否、静默=否 |
| M5 | music | false / false | 双缺收敛：技艺笔记体 | **两读法收敛** | ✅ 同 L2 构型+§1.6 口径注记+§1.5 反补齐护栏引用；story schema 零出现 |

**一致性判定**：
- H3↔H7（同 KB）同走裁定读法 ✅；L2↔M5（双缺同构）处置一致（单文件 depth+显式声明+谓词值溯源）✅。
- H3/H7 vs L2/M5 的存活/死亡差异**全部由 `has_story_role` 谓词值解释并在溯源链显式引用**（B.0 锚点要求）——**分支 4 违背 = 0**。
- 分支 3（溯源断/编造 R#）= 0。

### 4.2 F0 分支统计与含义

- **实际分支计数：分支 1 ×4 / 分支 2 ×0 / 分支 3 ×0 / 分支 4 ×0**（单缺域两探针走裁定；双缺域两探针两读法机械收敛、结构性无分叉可走分支 2）。
- **F0 作为发现的状态**：分支 2 零触发意味着「catalog 字面全降级路径」在本轮执行中未被 live 复现——但 F0 的定性依据是**文本矛盾本身**（F0-a/b/c 三处语义不一致 + F0-d 硬编码 + F0-e 未定义序，均为 rule-catalog/SKILL 原文客观属性，静态可复核），故 **F0 维持已确认 P1，Phase B 修复不因实证零触发而豁免**。
- **为什么复现不出来**：引擎消费侧文本恒为 SKILL Phase 3/4（其选项级排除示例 F0-c 承载裁定意图）+ catalog 同读；H3/H7 溯源显示引擎是**显式对照 catalog 字面宽读法后弃用**（非未察觉），说明当前 skill 消费面在单缺域稳定产出裁定语义。
- **测试设计含义**（D2）：若要实证分支 2 的可达性，需「只给 catalog、不给 SKILL 排除示例」的对照执行（脱离 skill 消费协议，非常规场景）；更务实的路径是 **Phase B 修 F0 后以文本级回归断言（三处语义对齐检查）替代 live 分支复现**，Phase D 复测 H3/H7 按快照转 PASS 计入 G6。

### 4.3 Phase D 复测结果（2026-11-24，post-fix 引擎 · 决策只读）

本轮无原 FAIL/DEGRADE 行（Phase A 26 全 PASS），设计 §7「原 FAIL/DEGRADE 场景重跑」收敛为：**4 冲突探针 + M3 按快照/终态重跑**（`git checkout scenario-*` 输入态保真 → post-fix skill 三段式重推 → 复测后切回终态 HEAD；三 KB 零内容 commit，worktree 实测 clean：health `d942be1` / law `cffb9ec` / music `630d906`）。

| 探针 | 输入态 | post-fix 引擎分支 | 判定 |
|------|--------|------------------|:---:|
| H3 | scenario-H3（story 12 篇，N=13 运行时） | **裁定语义 = 文本唯一机械读法**：R23 谓词「任一缺失即命中+作用范围成比例」直出排除 R4/R8、R6/R9 存活；R9 投影 `<depth>/<story>` commit=2 预案直供——旧「对照 catalog 字面宽读法后弃用」步骤**消失**（矛盾文本已不存在） | ✅ PASS（决策与 Phase A 恒等） |
| H7 | scenario-H7（先例 find=3 快照复算） | R10 命中→**落位=先例栏目 04 由预案文本直供**；Part 2「R10×R23 补定义」使 F0-e 缺口关闭——溯源链不再需要「规则缺口显式声明」，改为引用补定义行 | ✅ PASS |
| L2 | scenario-L2（双缺，02 系列 max=04→N=05） | 两读法收敛终态不变（depth 单文件+**显式声明三处仍要求**）；修复把「巧合收敛」升级为「文本保证收敛」 | ✅ PASS |
| M5 | scenario-M5（双缺，技艺笔记体例在位） | 同 L2 构型逐项恒等（§1.6 口径注记+§1.5 护栏引用义务不变） | ✅ PASS |
| M3 | music 终态 HEAD（只读） | N3 层目录占位口径注在文（qa SKILL Phase 4 F 模板注，find 非空判据）——**平铺 KB 落模块根由模板本体授权**，不再依赖 §2.1 兜底；V3 四项硬判据维持 | ✅ PASS（V3+N3 双闭环） |

**复测计数：5/5 PASS，0 决策漂移**——F0 修复的行为侧验收（裁定语义机械推导化）与终态稳定性（双缺收敛不变）同时成立；逐项三段式记录在证据文件 `## Phase D 复测证据（2026-11-24）` 节。

### 4.4 F0 文本级回归断言（D2 推荐口径执行，§4.2 闭环）

按 §4.2 预定方案，live 分支 2 结构不可达处以静态断言代证：四强记位（catalog R23 正文 / R23 谓词 / SKILL 排除示例 / Part 2 覆盖序）+ 辅位（R9 投影、R10 落位+commit、R23 单角色示例、O1/O2 SKILL 行）共 **9/9 位口径一致**，旧矛盾文本在活文档（rule-catalog + precipitation SKILL）grep 残留 **= 0**（9 断言位逐位命中数与旧串零残留记录在证据文件 F0 断言表）。**结论：F0-a/b/c/d/e 语义单源恢复；分支 2 不再是「不可达」而是「无旧义可读」——分歧文本已不存在**。

## §5 Phase B 修复清单（✅ 全部落地 · GATE 批准 2026-11-24 · 修复后状态列）

**P0：无**（26+10 零 FAIL，无阻塞缺陷）。§5 表 17 行 = GATE 批准 16 项（P1×6 + P2×10）+ 顺手 polish 1 项。落地批：`aee536c`（F0 五项+O1/O2）· `24e7843`（P2 主批 11 项）· `645e756`（trace 追加节=N4/N5/N6/O4 落位）· `4b038ff`（补充批：L21 幽灵路径+structural-checks 分层注）· `233f561`（收口批：N1 catalog 边界带 + K5 指针）· music KB `630d906`（N7）。

| 级别 | 项 | 一句话方案 | 落地状态 |
|:----:|----|-----------|---------|
| **P1** | F0-a/b/c 语义对齐 | rule-catalog R23 正文/谓词/SKILL 排除示例三处统一为「角色比例降级」口径（缺哪个角色杀哪组门控规则），并加「单角色 KB 示例」行 | ✅ `aee536c`；Phase D 静态断言 9/9 + 探针复测（§4.3/§4.4） |
| **P1** | F0-d R9 层位参数化 | R9/R8 预案位置改为按角色投影 `<interview?>/<depth>/<story?>`，缺角色层自动缺省并声明（health 型=commit 2 终态） | ✅ `aee536c`（R8 层门控注同批）；H3 复测 R9 投影直供终态 |
| **P1** | F0-e R10×R23 优先级 | Part 2 覆盖序补一行：R10 先例覆盖语义角色无关、落位=先例系列所在栏目（H7 已按此执行，落文即可） | ✅ `aee536c`；H7 复测缺口关闭 |
| **P1** | O1 R7 阈值双源 | SKILL「3 大沉淀模式」表 `<150 行` 改 `<100 行（单源见 rule-catalog R7）` | ✅ `aee536c`；R0 P1 判定行逐字不变（Phase C 核验 0 语义位移） |
| **P1** | O2 R10 commit 双源 | SKILL Quick Reference R10 行 `2-3` 改 `1（单源见 rule-catalog R10）` | ✅ `aee536c`；QR 其余行 reviewer 复核与 catalog 一致无双源 |
| **P1** | 背包 V4 | Phase 5.5 领域 query 模板补非 IT 域行（含法律/医学示例措辞），降低「全押 fallback」依赖 | ✅ `24e7843`（纯增行，IT 5 行原样=变宽不变差） |
| **P2** | N1 R7 落地复判 | Phase 7/实施后自检补「wc 复判 95-105 边界带」一条目（形态不翻转则仅记录） | ✅ `24e7843`（SKILL 条目）+ `233f561`（catalog R7 边界带登记，指针收口） |
| **P2** | N2 R11 碎片处置边界 | Phase 6.1 拆分处置补「已覆盖节可弃用，但须列弃用清单并计入 Phase 5 选项影响」 | ✅ `24e7843` |
| **P2** | N3 F 模板层目录占位 | 模板注补「层目录占位仅当 KB 实际存在子目录时填充，平铺 KB 落模块根」 | ✅ `24e7843`（qa SKILL）；M3 复测验证显式支持到位 |
| **P2** | N4 约定 8 扩写（测试侧文档） | 「缺口/覆盖类输入属性同样以执行时点复测；前置翻转须记账」 | ✅ `645e756`（trace 追加节，冻结本体零改动） |
| **P2** | N6 拆分行 commit 口径（溯源表侧，冻结表本体不改） | 后续表修订时拆分行统一「commit 数非硬判据、终态登记完整为硬判据」免责措辞 | ✅ `645e756` 追加节 |
| **P2** | N7 纯度扫描口径（测试 KB 规范+扫描脚本） | 判词检测加「陈述句 vs 引语」二级口径；数字模式扩中文数词形 | ✅ music KB `630d906`（外部仓库，N7 唯一落 KB 侧项） |
| **P2** | N8 锚点漂移 | rule-catalog/SKILL「Phase 1.7」注改现存步骤号（1.5/1.8 盘点） | ✅ `24e7843`；Phase C 锚点审计复验零悬挂引用 |
| **P2** | 背包其余 S3/S2/K5/V5 + note-temp 链接脚本同步（S2 冒烟=Task 14） | 按 R1 背包原方案执行 | ✅ `24e7843`/`4b038ff`（S3/S2/V5+L21 同族）/`233f561`（K5 指针）/note-temp scripts 同步（Task 13 复制；Task 14 冒烟全实施+链接脚本在位 0/0/0） |
| **P2** | QA capture 时点条款 | R2 执行协议补「问答类输出须在下一场景前完成逐字 capture」 | ✅ `645e756` 追加节 N5 行 |
| **P2** | O4 口径升格 | 「频次字段不作硬判据」由 health 注册升为跨 KB 通用措辞（表侧注记，见 N6 同批） | ✅ `645e756` 追加节 O4 行 |
| **P2** | 顺手 polish | R9/R8 谓词基句收紧 + R9 预案 L71 指代消解（三构型追踪表零行为变化确证） | ✅ `24e7843`（catalog）|

Phase B 修后必跑：Safeguards 三查 + R0 十例重放（Phase C 门禁）——**已过**（文末「回归结果」节：双比对 10/10，零 revert）；Phase D 复测 H3/H7/L2/M5/M3——**5/5 PASS**（§4.3）。

## §6 附录（指针）

| 件 | 位置 |
|----|------|
| 设计（G1-G6/§6.1/§7） | `.claude/skills/cross-domain-round2-test-design.md` |
| 规则溯源表 R2 节（26+10 行，签认冻结 2026-11-23） | `.claude/skills/cross-domain-rule-trace.md` |
| 证据（H/L/M/R0 四节 + Phase D 复测证据节，三段式逐字） | `.claude/skills/cross-domain-evidence-r2.md`（当前 1325 行；H=55b0617 / L=7061e80 / M=56da03a+925cb95 / R0=6f5ecd6 / R0 回归+Phase C=60962f0 / Phase D=本文终检批） |
| R0 冻结基线 + 2026-11-19 回归 | `.claude/skills/cross-domain-r0-baseline.md` |
| 规则单源 / 谓词层 | `.claude/skills/note-precipitation-planning/references/rule-catalog.md` · `SPEC.md §1.5/§1.6` |
| 测试 KB | `D:/developer/IdeaProjects/note-kb-test/{health,law,music}`（外部留档，不入本仓库；H5 素材 `note-kb-test/inbox-h5/`） |
| 快照 tags（Phase D 复测锚点） | health `scenario-H1..H8`（8）· law `scenario-L1/L2/L3/L4/L7`（5）· music `scenario-M1/M4/M5`（3） |
| KB commit 区间 | health `d51a182..HEAD`（26）· law `95284d2..cffb9ec`（6）· music `eb3dc6e..1dc0cda`（6） |
| Task 8/9/10 执行报告 + review ledger | `.superpowers/sdd/cross-domain-round2-test-plan/task-{8,9,10}-report.md` · `progress.md` |
| R1 前案（方法论基座） | `.claude/skills/cross-domain-generality-report.md` · `cross-domain-rule-trace.md` Part 1-3 |

## 回归结果（2026-11-24 · Phase C IT 回归,Task 14）

> **执行**:Task 14 单独执行者(无 subagent)· note 仓库 R0 重放全程 read-only（执行前 `git status --short` 空,沉淀类止于 Phase 5）· 逐探针明细在 `cross-domain-evidence-r2.md` `## R0 回归证据（2026-11-24 · Phase C post-fix 重放）` 节 · 本节为收口记录,上方 §1-§6 冻结内容零改动。
> **标尺**:双比对 =（a）Task 11 修改前重放（本文件 §2.2 + 证据 R0 2026-11-23 节）+（b）`cross-domain-r0-baseline.md` 冻结期望列。口径:决策语义不得回退,三段式格式允许演进。

### R0 十例双比对总表

| 探针 | 冻结期望（指针） | vs Task 11 修改前 | vs 冻结期望 | 结论 |
|------|----------------|:---:|:---:|:---:|
| P1 分布式锁 | 双层;interview+depth 互链;2 commit | 一致（R7 阈值双源→单源,判定行「不命中(≥100)」逐字不变;R10 排除先例复测 0<3） | 一致 | ✅✅ |
| P2 5 灵魂拷问 | 拆 single-topic 多文件（只验结果） | 一致（Phase 0.2 R1 文本未改） | 一致 | ✅✅ |
| P3 Agent 实战框架 | 08 主期望/09 亦可 | 一致（09.ai-applications/agent/ 复测在位） | 一致（可接受域） | ✅✅ |
| P4 什么是变量 | 不沉淀（只验结果） | 一致（Phase 2 R3 文本未改） | 一致 | ✅✅ |
| P5 阿明餐厅 RAG | 13.story 三层联动 | 一致（**F0-d 投影在双角色 KB 退化为全三层 commit=3,逐字等值**） | 一致 | ✅✅ |
| P6 HashMap | A 型 ≥3 篇+📚 | 一致（素材复测 466/327/225+N3 注不触 A 型） | 一致 | ✅✅ |
| P7 JVM 出题 | B 型四件套 | 一致 | 一致 | ✅✅ |
| P8 SSO 设计 | C 型三件套 | 一致 | 一致 | ✅✅ |
| P9 hashmap 评分 | G1-G6+E 类 | 一致（leaf-quality L25 路由+E1-E6 复测在位;S3/K5 注不触评分维度） | 一致 | ✅✅ |
| P10 Redis 穿透修复 | Phase 0.1 直接修复 | 一致（R2 分流表文本未改） | 一致 | ✅✅ |

**专项核验（决策者点名 3 项）**:O1（R7 `<150→<100`）note 十例无探针落 100-149 歧义带 → 0 语义位移;O2（R10 commit `2-3→1`）note 探针均不取 R10 预案 → 0 暴露;F0（R23/R9/R10 语义）note 角色齐备 → R23 两读法本就均不命中、R9 投影退化恒等 → **双角色 KB 零变化,行为侧与 Task 12/13 静态验证闭环**。

### Safeguards 三查结果（post-fix）

| 项 | 结果 |
|----|------|
| YAML 解析 | ✅ 3/3 OK |
| Phase 锚点审计 | ✅ **N8 修复复验通过**:活跃文档（SKILL/rule-catalog/CLAUDE.md）零悬挂「Phase 1.7」引用——rule-catalog R24 来源/语义位置双行 + SKILL 范围行均改「Phase 1 步骤 1.5」并带修正注;**无新漂移**（health SKILL 表「1.7 系列完整性」为 health 自有扫描编号,非悬挂引用）;跨文件 Phase 引用全集逐一解析在位（含 §7.1/§7.2、步骤 1.5/1.8、V4 新行、N1 新行） |
| 派发 smoke | ✅ 3 原话各自路由正确（description 原文命中 1/3/1） |
| 全库链接（附加） | ✅ 1148 .md · 0/0/0 |

### note-temp 冒烟（S2 全实施,KB_DIR=note-temp）

| 场景 | 结果 |
|------|------|
| 沉淀「分布式锁」双层 | ✅ 全实施:depth 59 行 + interview 30 行,双向互链+父 README 登记,**2 commit**（aca45c4 baseline / 27e0425 / 3f06def）;F0 角色比例降级正向样本（缺 story 只杀 R6/R9,双层存活）;§7.2 自检拦截 1 处真实断链（少一级 `../`）修复后才 commit;N1 复判 59<95 不翻转 |
| 体检 cdn-cache 单篇 | ✅ G1-G6 输出+真实 findings（G4:相关章节 2/3 代码格式死路径=KB fixture 遗留;R21 不开重机器遵守;模块专属维 N/A——note-temp 无 §1.5/§1.6） |
| 问答 A 型 Cookie 跨域 | ✅ §8 命中+📚 表 isfile 3/3;小 KB 深度 2 篇<3 显式声明收束（非卡死非硬凑）;qa-double-layer.sh 跑通（段头标签脚本级 IT 硬编码,记 hygiene 观察,SKILL 正文 V5 口径不受影响） |
| 链接脚本 P2-6 闭环 | ✅ note-temp `scripts/check-broken-links.py` 在位可执行、KB_DIR 解析 OK、全库终态 0/0/0 |
| 环境注记 | note-temp 原无 git（与 24e7843 提交注记一致）→ 本轮 `git init`+baseline 以满足「全实施含 commit」;其 `.claude/skills/` 副本仍为 **pre-Phase B 旧版**（diff 证实 O1/O2/F0/N/S/V 全缺）——冒烟按 note 仓库 post-fix SKILL 文本执行,副本整体同步建议列 Phase D 顺手项（见下方 Minor 表） |

### D1 覆盖注（R22 真核实支）

本轮环境 **WebSearch 可用**:沉淀断言「Brewer 2000 猜想 / Gilbert & Lynch 2002 证明」走窄查询**真核实支首次正例命中**（MIT CSAIL PDF + ACM DL,已落 📚 参考来源带 URL+日期）;WebFetch 仍被域名安全校验拦截 → fetch 通道 fallback 依旧。**D1 从「零覆盖」升为「部分覆盖（正例 ×1）」**,Phase A D1 注记的「核实成功路径无证据」状态被部分补上。

### 回归判定

**IT 行为只变宽未变差——P1-P10 双比对 10/10 一致,Safeguards 4/4,note-temp 三场景走通,0 回退,Phase B 全部修复（F0 五项+O1/O2+背包六项+N 系）无一需要 revert。Phase C 门禁通过,放行 Phase D。**

### 收口批（本 commit 落地）

| # | 项 | 处置 |
|---|----|------|
| N1 | rule-catalog R7 补「落地复判边界带 95-105（系列带语境按该系列实测行数带,如 94-106）」 | ✅ SKILL Phase 7 指针不再悬空（本文件 §5-P2 收口） |
| K5 | health SKILL Phase 1.17 编号项 3 加「K5 注口径」指针 | ✅ 同块两读法消除（长尾标签仅满足 §8 准入才计 P3,指向本节末桥接口径说明） |
| 观察项（不修） | note-temp skill 副本旧版同步 / qa-double-layer.sh 段头标签 / note-temp §8 预置死路径（cache/、cdn-design/、session/、cap-theorem/ 等） | 均记 Phase D/KB 侧议题——属 fixture/脚本卫生,非 skill 缺陷,Phase C 边界内不动 |

## Phase D 复测与终版收口（2026-11-24 · Task 15）

> **执行**:Task 15 单独执行者(无 subagent)· 复测协议见 §4.3(post-fix skill + scenario tag 快照决策重跑,KB 复测后已全部切回终态 HEAD、零内容 commit)· 逐项三段式/F0 断言/9 断言位记录在 `cross-domain-evidence-r2.md` `## Phase D 复测证据（2026-11-24）` 节 · 上方 §1-§6 与「回归结果」节内容维持,§1/§2.3/§4/§5 已按 Phase C/D 实况终版化(草稿标记移除)。

### 收口批观察项处置(Phase C 末表兑现)

| 观察项 | Phase D 处置 |
|--------|-------------|
| note-temp skill 副本旧版同步 | ✅ **已同步**:三 skill 全套(SKILL+references+scripts)+ ORCHESTRATION.md + STARTUP-NEW-KB.md + check-broken-links.py 按 `STARTUP-NEW-KB.md §1` 契约整体复制 post-fix 版,**契约范围(3 skill 目录 + ORCHESTRATION.md + STARTUP-NEW-KB.md + check-broken-links.py 链接脚本)`diff -rq` 零差异**(__pycache__ 清理后;campaign 过程文档如本报告/证据文件不在复制契约内,note-temp 副本无之属预期);note-temp git 提交 `a7a7c01`(scope=note-temp 按其 SPEC §2,冒烟产物基线 aca45c4 之上)**——冒烟效度不受损结论(Phase C 按 note 仓文本执行)保持不变,副本陈旧问题关闭（截至 a7a7c01 同步时点；终审 fix wave 688c42c/a76a7e8 又改契约内文件，note-temp 副本待 R3 重同步——已记 backlog） |
| qa-double-layer.sh 段头标签 IT 硬编码 | ✅ **已参数化(小改,判定属「小参数化」)**:`parse_role` 运行时解析 SPEC §1.5 角色表(type=interview/story)取栏目名、无角色模块整段跳过(旧版在 health/law/music 打 3 个空段头+假栏目建议序)、无 §1.5 旧式 KB 回退探测默认目录(note 行为恒等:SSO 双比对命中清单逐项一致,建议序 `主模块→12.interview→13.story` 恒等)。「面试方法论」段保留 11.product-and-pm 存在性探测(角色表无 methodology 类型,泛化属 R3 backlog,不过度设计)。**顺带修复既有健壮性缺陷**:旧脚本在 pipefail 下、目录存在但 0 命中的角色段 grep 空返回即中途退出、丢弃「无命中」行+建议序输出行(旧版终检基线实证:note@「SSO」在 11.product-and-pm 段死亡,exit=1、尾两行消失;note-temp@Cookie 旧版后三段空段头照打——新脚本改为角色缺失整段跳过)——新版各管道 `|| true` 兜底、终码统一由全库命中数决定。脚本改动落 note 仓(本批)+ 同步至 note-temp 副本;SKILL §3.3「模块列表从 §1 自动解析」口径由文档宣称升级为脚本实际(§1.5 角色表) |
| note-temp §8 预置死路径 | 维持不修——KB fixture 侧议题(非 skill 缺陷),留 KB 侧 |

### 数字终检(2026-11-24 find/git 实测,终态 HEAD)

| 指标 | 实测 |
|------|------|
| health leaf(排除 README/SPEC)/全 .md | **106**(01:24/02:34/03:17/04:18/05:13)/ 113 |
| law leaf / music leaf | **16** / **15** |
| KB commits(场景期)| health 26 / law 6 / music 6(终态 HEAD 再 +1=N7 批 630d906,合计 7) |
| scenario tags | 8+5+3=**16** |
| note 仓 .md(CLAUDE.md 口径)/ README | **1200** / **815** |
| R2 campaign note 仓 commits(8b4ebf2 签收件起)| **14**(含本批 2 commit:`fix(skill)` 脚本参数化 + `docs(skill)` 终版报告收口;收口前实测 12) |
| note-temp 仓 commits | **4**(aca45c4 baseline + 冒烟 2 + 本批同步 a7a7c01) |
| 全库断链 | **0/0/0**(本批终检复跑) |

## §7 终版验收表(G1-G6 × 状态 × 证据)

| Goal | 状态 | 关键证据(指针) | 诚实限定 |
|------|:---:|---------------|---------|
| **G1 通用**(26 场景 0 FAIL;DEGRADE 修复后复测转 PASS) | ✅ 达成 | §2.1 26 PASS/0 DEGRADE/0 FAIL;§4.3 Phase D 5/5 PASS(H3/H7/L2/M5/M3,决策恒等) | 无原 DEGRADE 行,live「转 PASS」计数=0,以探针复测+静态断言代证(D2) |
| **G2 稳定**(R0 10/10 + Safeguards) | ✅ 达成 | 「回归结果」节双比对 10/10 + Safeguards 4/4(post-fix,N8 复验);零 revert | 锚点审计含 1 处历史冻结节旧引(trace L37,纪律不改,已记账) |
| **G3 可用**(降级全显式 + 三段式全完整) | ✅ 达成 | §1 G3 行;证据文件 26+10 三段式逐字;§4.3 复测声明义务维持 | — |
| **G4 溯源质量**(0 编造 R#/断链) | ✅ 达成 | 三轮 reviewer 独立审计 + Phase D 复测溯源链可解析 | — |
| **G5 单角色中 KB 启发式** | ✅ 达成 | §1 G5 行 + H1/H6/H7/H10 逐项;§4.3 先例复算(快照 find=3)口径不变 | 终态 106 leaf 实测(§2.3) |
| **G6 背包+F0 闭环** | ✅ 达成(限定×2) | §5 修复全落地(5 note commits + music 630d906);§4.4 F0 静态断言 9/9 位一致、旧矛盾文本活文档零残留;§4.3 行为佐证 | **D1**:R22 真核实支仅正例×1(Phase C);**D2**:F0 分支 2 以文本级回归断言替代 live 复现(结构不可达——修复后为「无旧义可读」的更强闭合) |

**总判(R2 完结)**:规则引擎跨域首考**通过**,且 R1 遗留 P2 背包与 F0 语义冲突**全部闭环**——设计 §6 验收口径逐项核销:26 场景 0 FAIL ✅ · R0 10/10 ✅ · Safeguards 全过 ✅ · 降级全显式 ✅ · 三段式+溯源链全完整 ✅ · P2 六项+M3 复验闭环 ✅ · F0 修复后冲突探针行全 PASS ✅(5/5 复测 + 静态断言)。后续轮建议:R22 真核实支补覆盖(D1)、`11.product-and-pm`/methodology 角色表泛化、R7 预估-落地带进一步收敛(C2 行数落带偏差)均入 R3 议题池。
