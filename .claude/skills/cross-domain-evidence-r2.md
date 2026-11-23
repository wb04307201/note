# cross-domain evidence R2(场景执行证据)

> 配套:`cross-domain-rule-trace.md` R2 追溯表(已签认冻结 2026-11-23)。本文件为 Task 8 health 场景 H1-H12 的执行证据。KB_DIR=`D:/developer/IdeaProjects/note-kb-test/health`。执行方式:读三个 SKILL.md + rule-catalog.md 后按 skill 文档化 Phase 亲自执行(沉淀类走完整实施,问答/体检类只读)。

## H 场景证据(2026-11-23)

### H1 沉淀「睡眠的生理机制」(输入按冻结行 = 双进程交互整合总览)

- 问法(模拟用户):「睡眠的生理机制(睡眠压力 × 昼夜节律双进程交互)应该沉淀到 health KB 什么位置?」
- git tag:`scenario-H1`(= d51a182,执行前基线)

**Phase 1 现状盘点(实测)**:01.body-basics 睡眠单机制篇 7 篇(78-88 行);`grep -rn "双进程|两进程|two-process"` = **0**;运行时补测 `grep "双过程"` = adenosine-sleep-pressure.md + 01 README 共 2 处——均为**概念提及**(过程 S/C 分述),**无整合总览篇** → 缺口真实成立。同栏目(01)临床案例先例 `find` = 0(clinical-case 系列在 04,跨栏目不计)。§1.5:无 interview、有 story;§1.6:has_exam=false、is_series(01)=false。

**Phase 2**:3 信号过(高频问答向 / 机制 ≥4 层面 / 缺口真实),无反信号。

**Phase 3/4 三段式输出(逐字)**:

```
Stage 1 规则命中表(输入属性:预估行数 78-95<100 · 主题数 1 · 同栏目先例 0 · §1.5 interview 缺/story 在 · §1.6 has_exam=false)
| 规则 | 判定 | 判据→属性 |
|------|------|-----------|
| R5 | 命中 | 深度原理(机制整合)→ depth 主模块 01.body-basics |
| R7 | 命中 | 预估 <100 行(78-95)→ 单文件,commit=1 |
| R23 | 命中(选项级) | §1.6 has_interview_role=false → 排除 R4/R8(无 interview 角色 → 排除 R8/R4,SKILL 示例口径);story 门控(R6/R9)不受 R23 影响(裁定读法) |
| R4 | 排除 | has_exam=false 且无 interview 角色(§1.5) |
| R6 | 不命中 | 输入为机制推导,非叙事素材(无人物弧请求) |
| R9 | 排除 | 行数 <300;且 R23 已按选项级处理 interview 层 |
| R10 | 评估后不命中(双重排除) | ① precedent_count 口径=同栏目临床案例计数:01.body-basics 实测 0(<3);② 输入非临床案例体。二者独立各足以排除,均声明 |
| R22 | 不触发 | 纯概念/机制推导;不引入新的可核实数字断言(咖啡因半衰期等沿用本库腺苷篇既有口径) |
| R24 | 不命中 | 目标栏目 01 无编号系列(is_series=false 实测);互链义务按核心原则 ≥2 互链+回链执行 |
| R12 | 伴随义务评估 | 主题词「睡眠」已被 §8 现有词条覆盖(词条指向 01.body-basics/)→ 按「主题已被现有 §8 词覆盖」跳过加行;tags:[睡眠] 已同步(约定 3) |

Stage 2 预案集
- P1(R5):形态=depth 深度版 · 位置=01.body-basics/sleep-dual-process-model.md
- P2(R7):形态=单文件 · commit=1
- (R23:无独立预案,作用=排除 R4/R8 并强制显式降级声明)
- (R10:无预案——排除声明见 Stage 1)

Stage 3 综合裁决(Part 2 覆盖序:R23⊃R8/R9 已消化;无残余冲突)
最终方案 = 单文件 depth @ 01.body-basics/sleep-dual-process-model.md,commit=1
R23 显式降级声明:本 KB 无 interview 角色模块,双层/三层选项跳过,按 R23 降级为 depth 单文件呈现。
溯源链:R5(判据:机制深度→depth 01)+ R7(判据:78-95 行 <100)+ R23(判据:§1.6 has_interview_role=false→排除 R4/R8)+ R10(判据:同栏目先例 0 + 输入非临床案例→不命中)→ 综合 = 单文件 01 depth,1 commit。
```

**Phase 5 选项呈现(全部选项+推荐项,逐字;脚本化协议:按推荐项实施)**:

```
A. 单文件 depth @ 01.body-basics(推荐)——对应预案组合 R5+R7(+R23 声明);改动 1 文件 + 2 兄弟回链 + 目录登记,1 commit
B. 双层沉淀(interview 版 + depth 版)——对应预案组合 R8+R4:本 KB 无 interview 角色,违反 R23,不可用
C. 暂不沉淀——缺口保留
```

实施 = A(推荐项)。

**实际终态**:新文件 `01.body-basics/sleep-dual-process-model.md`(78 行,R7 成立);README 目录登记 1 行;adenosine / circadian 两兄弟各回链 1 行;commit `0e6070c` `feat(health): ...`(**1 commit**);links 复扫 0 断链;层数=1(depth)。

**对照冻结表判定**:**PASS**。依据:A.1-H1 期望列 =「单文件 depth `01.body-basics/<slug>.md`,1 commit + 显式降级声明 + §8/tags 同步;溯源链须含 R10 排除理由(同栏目口径);凭全库案例数=3 误命中 R10 = FAIL」——终态一致(单文件/1 commit/降级声明在 Stage 3),溯源链完整(R10 双重排除理由显式给出,且以同栏目口径而非全库数评估);R12 按「已被 §8 覆盖」跳过合规(约定 3 允许,tags 同步实测在)。

**意外发现(表外)**:① 快照 grep 词「双进程/两进程/two-process」与 KB 实际用词「双过程」不同形,运行时若只按快照 grep 会漏检提及位置(不影响缺口判定,但「grep=0 实测」这一输入属性在运行时的严格复测值应为:双进程=0,双过程=2 处概念提及)——建议 Phase B 在输入属性口径中固定用词变体清单。② health KB 无 git hooks、CRLF warning,链接校验以 scripts/check-broken-links.py 手动兜底(环境注记,非 skill 问题)。

### H2 沉淀「维生素 D 每日该补多少」(输入按冻结行 = 剂量个体化选择实践新篇)

- 问法(模拟用户):「维生素 D 每日该补多少(怎么选怎么补的决策工作流)沉淀到 health KB 什么位置?」
- git tag:`scenario-H2`(= 0e6070c,执行前基线)

**Phase 1 现状盘点(实测)**:`02.nutrition/vitamin-d-requirement-sunlight.md` 83 行,含数字口径表(RNI/UL/IOM)、血清判定争议、补充剂证据边界;grep「怎么补/决策/选购」→ 母篇无「怎么选怎么补」决策工作流(「补充剂证据边界」节仅 ~4 行且是 RCT 证据解读体)→ 深化缺口真实(与冻结行假设①一致)。web 核实通道:沙箱无 WebSearch/WebFetch 可用渠道(fetch MCP 连接超时)→ 按 SKILL Phase 5.5「噪音判定退出/fallback」:**退回仓库内既有证据(母篇口径表)+ 显式标注未核实**。

**Phase 3/4 三段式输出(逐字)**:

```
Stage 1 规则命中表(输入属性:预估行数 80-95<100 · 素材含 IU/µg 数字断言(转引自母篇) · §1.5 interview 缺 · 营养深度主题)
| 规则 | 判定 | 判据→属性 |
| R5 | 命中 | 营养深度原理 → depth 02.nutrition |
| R7 | 命中 | <100 行 → 单文件 commit=1 |
| R22 | 命中(强) | 断言含 IU 剂量数字 + 指南版本差异(中国 DRIs 2023 vs IOM vs Endocrine Society)→ 触发核实;联网通道受阻 → 按 fallback:转引母篇口径 + 正文显式「未联网核实」标注 + 「指南版本与口径」小节 |
| R23 | 命中(选项级) | has_interview_role=false → 排除 R4/R8 + 显式降级声明 |
| R4/R8/R9 | 排除 | 同 H1(无 interview / 行数 / 非叙事) |
| R10 | 不命中 | 输入非临床案例 + 02 栏目先例 0 |
| R24 | 不命中 | 02 无编号系列 |
| R12 | 跳过加行 | 「营养素」「膳食指南」均已在 §8(实测 SPEC.md 行 158/159)→ 主题已被现有词覆盖;tags:[营养素, 膳食指南] 同步 |

Stage 2 预案集
- P1(R5):depth 版 @ 02.nutrition/vitamin-d-supplement-decision.md
- P2(R7):单文件 commit=1
- P3(R22):数字断言转引 + 显式未核实标注 + 指南版本小节

Stage 3 综合裁决
最终方案 = 单文件 depth @ 02.nutrition,commit=1,R22 走「转引+标注未核实」形态
溯源链:R5(营养深度→02)+ R7(<100 行)+ R22(IU/指南版本断言→核实义务,通道受阻降级标注)+ R23(§1.6 has_interview_role=false→排除 R4/R8)→ 综合 = 单文件 02 depth,1 commit。
```

**Phase 5 选项呈现(逐字)**:

```
A. 单文件 depth @ 02.nutrition,数字转引母篇+显式标注未核实(推荐)——对应 R5+R7+R22(降级标注形态);1 commit
B. 对 IU/UL 做联网核实后写入——沙箱无可用检索通道,不可执行
C. 并入母篇做增量更新——R2 分流外(用户意图=新增独立决策篇,且母篇是参考体,合并破坏单点定位)
D. 暂不沉淀——缺口保留
```

实施 = A。**实际终态**:`02.nutrition/vitamin-d-supplement-decision.md` 95 行(<100,R7 成立;含「指南版本与口径」节 + 两处显式「未联网核实」标注);母篇回链 1 行 + README 登记;commit `226de59`(**1 commit**);0 断链。

**判定**:**PASS**。依据:A.1-H2 期望 =「单文件 depth 02,1 commit + 数字断言核实或标注 + 指南版本小节 + 降级声明 + §8/tags 同步;数字当既定事实直接用(未核实未标注)= DEGRADE」——实际走「标注」支(通道受阻 fallback,Phase 5.5 合法路径),未裸用数字;降级声明在 Stage 3。

### H3 沉淀「某罕见病例的诊疗叙事」【冲突探针 → B.1】

- 问法(模拟用户):「一个罕见病(AIP 卟啉病)反复误诊的诊疗故事,机制和叙事都值得沉淀,放 health KB 哪里?」
- git tag:`scenario-H3`(= 226de59,执行前基线)

**引擎实际分支 = B.0 分支 1(裁定语义)**。三段式输出(逐字):

```
Stage 1 规则命中表(输入属性:素材总量 ~115 行(机制部分 60-80 + 叙事 50-70 可拆分) · 人物弧/事故戏剧化叙事请求 · §1.5 story 在/interview 缺 · §1.6 has_narrative=true)
| 规则 | 判定 | 判据→属性 |
| R6 | 命中 | has_narrative=true + has_story_role=true → story 门控存活(角色比例降级裁定:R23 只降级缺失角色所门控的规则,story 在 → R6/R9 不受 R23 影响) |
| R5 | 命中 | 机制部分可独立成 depth 篇 → 01.body-basics(病例主题为代谢机制) |
| R7 | 命中×2 | 两部分各 <100 行 → 各单文件 commit=1 |
| R9 | 评估后排除 | 总量 115 <300 → 行数判据不满足(冻结行口径);注:终态与 R9 缺省 interview 层的 <depth>/<story> 同构 |
| R23 | 命中(选项级) | has_interview_role=false → 排除 R4/R8;story 门控不降级(裁定读法;catalog 字面读法见 B.1(a) 对照——引擎此处显式走 SKILL Phase 3 选项级排除示例口径) |
| R10 | 不命中 | 输入=story 叙事章节,非临床案例观察笔记体(约定 7 翻译);01 栏目先例 0 |
| 准入 6 信号 | 显式过检(O3 口径:note 13.story/SPEC.md §3.5 通用 6 信号 + 05 模块 12 篇惯例——health 05 无模块 SPEC.md,按 O3 采用通用口径,不判流程失效) | ①人物弧✅(四次急诊→确诊→重写生活)②类比落地✅(流水线堵车/马桶纸条)③❌/✅事故✅(「检查正常」误治 vs 尿 PBG 线索)④✅受众(理解症状-检查错位)⑤⚠️体量(短章联动形态,63 行,符合 05 既有病例叙事段体量惯例 55-70)⑥✅系列定位(09-13 病例叙事段,与 09 对照线)→ ①②③全过+④⑤⑥≥2 → 准入通过 |

Stage 2 预案集
- P1(R6):story 章节 · 位置=05.medical-stories/13-<slug>.md(N=运行时 find max(12)+1)· commit 随 R7
- P2(R5):depth 机制篇 · 位置=01.body-basics/porphyria-heme-pathway-mechanism.md
- P3(R7×2):各单文件 1 commit
- (R23 声明:interview 层缺失,不产出问答版)

Stage 3 综合裁决
最终方案 = 机制 depth 篇(01)+ 故事篇(05/13)双向互链,commit=2
R23 降级声明:本 KB 无 interview 角色 → 跳过「interview 版」一层,按裁定仅缺省 interview 层,story 层保留;若按 catalog 字面宽读法则全降级为 depth 单文件(B.1(a))——两读法在 health 的分叉即 F0 探针点,本执行记录=分支 1。
溯源链:R6(判据:§1.6 has_narrative=true + §1.5 story 在) + R5(判据:机制部分可独立) + R7(判据:各部分 <100 行) + R9 评估排除(判据:115<300) + R23(判据:has_interview_role=false→选项级排除 R4/R8)→ 综合 = depth+story 双篇互链,2 commit。
```

**Phase 5 选项呈现(逐字)**:

```
A. 双篇双层联动:01 机制 depth 篇 + 05/13 story 叙事篇,双向互链(推荐)——对应 R5+R6+R7,2 commit
B. 混合体裁单篇(05-marshall 体例,机制内嵌 story)——第三结局读法,1 commit;素材本就分两半,放弃独立 depth 检索入口
C. 纯 story 单篇(机制全部 defer 链接)——体量省,但机制知识丢失结构
D. 全降级 depth 单文件(机制+叙事合并 115 行,无 story 层)——catalog 字面读法,叙事入已声明的 story 模块旁,语义不成立
```

实施 = A(推荐)。

**实际终态**:`01.body-basics/porphyria-heme-pathway-mechanism.md`(82 行,commit `846302e`)+ `05.medical-stories/13-acute-porphyria-misdiagnosis.md`(63 行,commit `37a8b6f`);story 篇 8 字段 frontmatter(number/type/position/title/status/tags/audience/depth)+ 系列定位块 + 「叙事回顾(6 信号自证)」节 + 05 README 系列定位段登记(共 12→13 篇数字同步);双向互链实测各 1 处;全文 grep「面试」=0;0 断链;commit=2。

**判定**:**PASS**(B.0 分支 1:裁定语义 + 完整溯源链)。依据:B.1 注册期望=(b)「story 篇 05/13-<slug> + 机制 depth 篇,双向互链,commit=2;准入显式过检;N=运行时 find max+1(快照 12+1=13,实际=13 ✅)」;溯源链完整且显式引用 R23 谓词值与选项级排除口径,R6 存活判定引用 §1.6。

**意外发现(表外)**:① R22 在 H3 素材上「未触发核实通道」——机制篇含「千分位量级」流行病学直觉断言,处理为显式「未联网核实」标注(通道受阻 fallback 一致口径),行为正确但 catalog R22 语义位置在 Phase 5.5 而非 Phase 3/4 Stage 1——三段式命中表登记 R22 属 skill 扩展用法(良性)。② story 篇相对路径深度:`05/13-x.md` 引 SPEC 应为 `../SPEC.md` 而非 `../../SPEC.md`(第一版写错被 check-broken-links 拦截后修正)——链接防护网工作正常(这正是 L2 防线的价值,正面记录)。

### H4 「补钙的 5 个常见误区」(R1 拆分决策;子题级三段式按约定 6)

- 问法(模拟用户):「补钙的 5 个常见误区,沉淀到 health KB。」
- git tag:`scenario-H4`(= 37a8b6f,执行前基线)

**Phase 0.2(R1,只验决策结果)**:编号「5 个」+ 5 个互不相关子主题 → **判定多主题,拆 5 个 single-topic**。拆分决策记录:❌ 合并成 1 篇(违反 R1);✅ 5 篇独立 frontmatter + 兄弟双向互链(核心原则 4;slug 并列非编号系列 → R24 编号导航表义务不强制,母篇仍建「系列导航:补钙误区五谈」表作总入口)。

**Phase 1 盘点(实测)**:`calcium-bone-health.md` 83 行机制总览体(数字口径表 800/1000/2000/2500、单次 ≤500 mg、牛奶 100-120 mg/100 mL);无误区分述 → 总览↔分述关系,缺口真实(不触发 R11 合并,与 M4 同构)。

**子题级三段式(5 篇共用,逐字)**:

```
Stage 1:R5(营养深度→02.nutrition)· R7(每篇 <100 行→单文件各 1 commit,共 5)· R22(误区含 mg/UL 数字断言→全部转引母篇口径表并显式「未联网核实」标注;精确流行病学值不断言)· R23(interview 缺→排除 R4/R8+降级声明)· R24 条件不激活(slug 并列;兄弟互链义务仍执行)· R12 跳过加行(主题词「营养素」已在 §8,tags:[营养素] 全篇同步)
Stage 2:P1×5 = 各单文件 @ 02.nutrition/<slug>.md(5 个独立 slug)
Stage 3:拆 5 篇,每篇 1 commit;溯源链:R1(判据:编号 5 个)→ 子题×5[R5+R7+R22(标注支)+R23(声明)]→ 综合 = 5 篇 single-topic,5 commit,兄弟双向互链+母篇系列导航+README 登记。
```

**Phase 5 选项呈现(逐字)**:

```
A. 拆 5 个 single-topic,slug 并列 + 母篇建五谈导航表(推荐)——R1+R5+R7,5 commit
B. 拆 5 篇并入编号系列 11-15——02.nutrition 无编号系列先例,硬造系列改变栏目形态(不建议)
C. 合并成 1 篇「5 大误区」——违反 R1(FAIL 口径,列出仅为对照)
D. 暂不沉淀
```

实施 = A。

**实际终态**:5 文件 56/56/67/67/56 行(假设 60-90,两篇 56 略低于下沿——**行数偏差记录**,不影响 R7 与硬判据);commits `16ce7c2/72cf32c/dd5f028/b85dda0/96ba264`(**5 commit**);README 登记 5 行;母篇「系列导航:补钙误区五谈」5 兄弟双向互链实测(grep 各篇延伸互链含全部兄弟);0 断链;零「面试」grep 通过。

**判定**:**PASS**。依据:A.1-H4 期望 =「拆 5 个 single-topic(02.nutrition;硬判据=5 篇独立 frontmatter+兄弟双向互链+父 README 登记),共 5 commit+降级声明+§8/tags 同步;合并成 1 篇=FAIL」——拆分决策结果一致,硬判据全中;子题级三段式含 R# 标注(约定 6)。

**意外发现**:母篇新增的「系列导航表」是 R24 编号系列载体在**非编号**场景的自然借用(为五谈提供总入口)——合规且增强可达性,记正向观察。

### H5 批量导入 15 篇营养素材(R11)

- 问法(模拟用户):「这里有 15 份外部营养课程素材,批量导入 health KB。」(素材落 `note-kb-test/inbox-h5/`,KB 外;git tag:`scenario-H5`= 96ba264 执行前基线)

**输入构成实测**:15 文件 = 铁讲义 2 篇(同主题重复)+ 维 C 笔记 2 篇(同主题重复)+ 微量元素大讲义 1 篇(**530 行、`grep -c '^## '`=40、≥2 独立主题**,含睡眠/体温 2 处错位内容节)+ 运动恢复/体温素材 2 篇(内容主题=睡眠机制,与 02 营养定位不符)+ 8 篇正常新主题 = 4+1+2+8=15 ✓(冻结构成表吻合)。

**Phase 3/4 三段式(汇总形态,冻结行允许「汇总或逐篇」)**:

```
Stage 1 规则命中表(输入属性:15 篇批量 · 2 组同主题重复 · 1 篇 ≥500 行+H2≥8+≥2 主题 · 2 篇错位 · 素材含营养数字断言 · interview 缺)
| R11 | 命中 | 批量三整理:合并(≥2 同主题×2 组)/ 拆分(≥500+H2≥8+≥2 主题×1)/ 错位修正×2 |
| R5 | 命中(R11+R5 组合) | 合并式深读→depth 02.nutrition;错位篇→depth 01.body-basics |
| R7 | 命中(产出逐篇) | 各产出 <100 行→单文件 |
| R22 | 命中 | 素材含 IU/µg 等数字断言,外源不可核实→全部转引或降为定性+显式「未核实」标注 |
| R23 | 命中 | interview 缺→全部单文件 depth+显式降级声明;R11+R8 组合不可用 |
| R12 | 伴随 | 主题词均落 §8 现有「营养素」覆盖→加行跳过,tags 同步 |
| R24 | 条件 | 落点 02/01 无编号系列→兄弟互链按核心原则 4 |

Stage 2 预案集(逐动作)
- 合并组A:铁 A/B→1 篇(以内容最全为基准,保留两原始来源标注;两份吸收率区间数值不一致→降为方向性表述并标注)
- 合并组B:维C 1/2→1 篇(同法)
- 拆分:530 行大讲义按 H2 切→锌篇+硒篇(single-topic 独立 frontmatter);碘节并入碘篇;「咖啡因药代」「钙镁锌营销拆解」两节判已有覆盖→弃用(逐节处置记录)
- 错位×2:运动恢复→01 睡眠机制;体温节律→01 昼夜节律(带错位修正说明节)
- 正常×8:B12/碘/叶酸/维A/镁/维K/生物素/运动饮料→02 各 1 篇
- 每动作 1 commit + 链接自检

Stage 3 综合裁决
最终方案 = 合并 2 组 / 拆 1 篇(→2 产出)/ 移 2 篇 / 正常 8 篇 = 14 产出文件,全部 depth 单文件;降级声明:本 KB 无 interview 角色,批量沉淀不走双层(R23)。
溯源链:R11(判据:三整理输入构成)+ R5(判据:合并式深读→depth)+ R7(判据:产出<100)+ R22(判据:数字断言→转引/标注)+ R23(判据:§1.5 无 interview→全单文件+声明)→ 综合 = 逐动作 commit 的 depth 批量沉淀。
```

**Phase 5 选项呈现(逐字)**:

```
A. 逐动作 commit:合并×2 + 拆分×1 + 移动×2 + 正常×8 + README 登记收口 = 14 commit(推荐)——R11「逐动作 1+链接自检」口径
B. 单一大 commit——违反 R11,数字校对与回滚粒度差
C. cp -r 式搬运——Phase 6.1 明文禁止(列出仅对照)
```

实施 = A。**实际终态**:14 新文件(`02.nutrition/`:iron-diet-absorption / vitamin-c-food-sources / zinc-diet-immune-role / selenium-thyroid-antioxidant / vitamin-b12-vegetarian-risk / iodine-salt-seaweed-balance / folic-acid-pregnancy-evidence / vitamin-a-two-routes / magnesium-foods-supplements / vitamin-k1-k2-bones-anticoagulant / biotin-hair-nails-lab-interference / sports-drinks-when-needed;`01.body-basics/`:sleep-muscle-recovery-mechanism / core-temperature-alertness-rhythm);commits `48c44e7 c851583 fef5f21 fad818f 9572362 d3fd85c 7506dd9 c871b64 69d90a3 4bf921d 08ad0d8 ca3f10b 2b0ef3f ee84b69`(**14 commit**,含收口登记);**报告计数:合并 2 组 / 拆分 1 篇→2 产出 / 移动 2 篇 / 正常 8 篇 / 素材弃用 2 节**(非 cp -r:全部重写为 KB 体例+R22 标注);每 commit 后 links 扫描 0 断链(收口复扫 ✅)。

**判定**:**PASS**。依据:H5 期望「三整理落地(合并 2/拆 1/移 2)+8 正常,全部单文件 depth+显式降级声明;报告给计数;cp -r=FAIL;三段式+溯源链」——全部命中;**观察**:15 素材→14 产出(拆分 1→2 与合并 2→1×2 对冲+弃用 2 节),按「素材 15/产出 14/弃用节 2」三口径诚实记账(约定 8)。

### H6 常见病编号系列加第 N 篇(痛风/高尿酸)

- 问法(模拟用户):「向常见病编号系列加一篇痛风/高尿酸血症。」;git tag:`scenario-H6`(= ee84b69 执行前基线)
- **运行时 N 实测**:`find 04.common-conditions/[0-9]*.md` = 10 篇 → N=**11**(快照 11 吻合)

**三段式输出(逐字)**:

```
Stage 1(输入属性:新篇 ~80-95 预估,同体例下沿 · 尿酸阈值数字断言 · is_series=true(04 编号 10 篇实测)· interview 缺 · 非临床案例体)
R5 命中(常见病知识→depth 04)· R7 命中(预估<100→单文件)· R24 命中(is_series→链所有 10 兄弟+兄弟回链+导航表全更)· R22 命中(420 µmol/L 类阈值→「指南版本与口径」节:2019 中国指南口径+旧男女分线历史口径+饱和线机制,标「未联网复核」)· R23 命中(interview 缺→排除 R4/R8+降级声明)· R10 不命中(输入为系列知识篇,非临床案例观察笔记体——先例 3 在但体裁不符)· R12 伴随(tags:[常见病,代谢] §8 在位,加行跳过)
Stage 2:P1(R5+R7)=单文件 @04/11-gout-hyperuricemia-basics.md;P2(R24)=互链+导航表义务随主预案
Stage 3:最终方案 = 新篇 + 10 兄弟导航表各加 11 行 + 新篇全列 1-11 + README 登记,并入同一 commit(冻结行「严格终态并入主 commit」口径)
R23 降级声明:无 interview 角色→不出问答版,单文件 depth 呈现。
溯源链:R5(常见病→04)+ R7(预估<100)+ R24(is_series=true 实测 10 篇)+ R22(阈值数字→口径节+标注)+ R23(§1.5→排除 R4/R8)→ 综合 = 单文件 11 篇 + 双向互链网,1 commit。
```

**Phase 5 选项(逐字)**:`A. 严格终态 1 commit(推荐)` / `B. 兄弟回链拆独立 refactor commit(总 2,亦合规不判违)` / `C. 只加新篇不回链(单向链,FAIL 对照项)`。实施 = A。

**实际终态**:`04.common-conditions/11-gout-hyperuricemia-basics.md`(**101 行**);10 篇兄弟各导航表+1 行(互链 grep:兄弟→新篇 10/10 命中;新篇→兄弟导航表 10 行全列+延伸互链);README 登记;commit `b5caa0f`(**1 commit**);0 断链。

**判定**:**PASS**。依据:H6 期望「`11-<slug>.md` N 运行时 ✅+10 兄弟双向互链+导航表全更新+指南版本小节+降级声明+§8/tags;硬判据=双向互链+导航表完整而非 commit 数;单向链=FAIL」——硬判据全中。**偏差观察**:实测 101 行 >R7「<100」阈值 1 行——预估-落地漂移;形态判定不受影响(R8 本就被 R23 杀死),但暴露「R7 用预估行数、落地后无复判步骤」的机制空白 → 新发现候选(skill 缺陷/引擎层轻量)。

### H7 同栏先例 ≥3 后再沉淀新临床案例【冲突探针 → B.2】

- 问法(模拟用户):「再沉淀一个临床案例:老人吃二甲双胍五年,乏力和记性差被当成衰老,最后查出来是贫血。」;git tag:`scenario-H7`(= b5caa0f 执行前基线)
- **运行时先例复测**:`find 04.common-conditions -name 'clinical-case-*.md'` = **3**(01/02/03,与快照一致;H5 沉淀未新增案例体,先例数不变)→ R10 判据 `precedent_count=3≥3` 满足;输入=临床案例(约定 7 谓词翻译:生产 Bug 案例→临床案例观察笔记体)✅

**引擎实际分支 = B.0 分支 1(裁定语义)**。三段式输出(逐字):

```
Stage 1 规则命中表(输入属性:新案例 ~85-95 行同体例预估(实测 82) · 现象不与 01-03 重复 · 含指南阈值引用 · 同命名族先例=3 · interview 缺)
| R10 | 命中(覆盖 R8) | precedent_count=3≥3 + 输入=临床案例;落位=先例系列所在栏目 04.common-conditions(R10「先例覆盖」语义角色无关;<interview>/<现象>-troubleshooting 落位是 IT 残留,按裁定弃用;catalog 字面读法=R23 全降级或引用不存在路径,见 B.2(a),本执行走裁定分支并显式记录 R10×R23 优先级未定义=F0-e 规则缺口,按设计者裁定裁决) |
| R7 | 命中(与 R10 一致) | <100 行→单文件 |
| R24 | 命中 | clinical-case 同命名族=系列口径(自带「栏目导航(临床观察笔记)」节实测)→ 3 兄弟双向互链+导航更新 |
| R22 | 命中 | 二甲双胍/B12 发生率类引用 → 降为方向性表述+「指南版本与口径」节标注未联网核实 |
| R23 | 命中(选项级) | has_interview_role=false → 排除 R4/R8(R10 覆盖对象 R8 本已死,R10 独立价值=形态单篇+先例命名惯例+落位,按裁定存活) |
| R12 | **跳过(命中跳过条款)** | troubleshooting 类=clinical-case 类(约定 7 翻译)→ §8 不收录,显式跳过声明 |

Stage 2 预案集
- P1(R10+R7):形态=单篇 · 位置=04.common-conditions/clinical-case-04-<slug>.md(命名随先例系列实测惯例) · commit=1(O2 口径:catalog R10 预案片段 commit=1;SKILL Quick Reference 2-3 不采)
- P2(R24):3 兄弟栏目导航各+1 行、新篇导航全列,随主预案
- P3(R12):跳过声明

Stage 3 综合裁决(Part 2:R10⊃R8 生效;R23×R10 冲突=已注册规则缺口 F0-e,按签认裁定=角色比例降级裁决)
最终方案 = clinical-case-04-metformin-b12-anemia.md 单篇 1 commit,骨架随先例体例(现象/机制/转归/常见误读速查/指南版本与口径/一图流/栏目导航/延伸互链/快问快答),零「面试」原词
溯源链:R10(判据:先例 3≥3+临床案例体裁;落位裁定=先例栏目)+ R7(判据:<100 行)+ R24(判据:同命名族系列)+ R22(判据:引用数字→口径节)+ R23(判据:interview 缺→排除 R4/R8;F0-e 缺口声明)+ R12(判据:troubleshooting 类→跳过 §8)→ 综合 = 单篇 04/clinical-case-04,1 commit。
```

**Phase 5 选项呈现(逐字)**:

```
A. 单篇落 04 先例栏目,命名随 clinical-case-NN 惯例,1 commit(推荐)——R10 裁定读法
B. 建 interview 模块落 <现象>-troubleshooting——违反 R23 默认+R25 非默认+SPEC §1.5 反补齐护栏(B.2(a2) 两 FAIL 路径之一,列出仅对照)
C. 双层(interview+depth)——R23 下不可用
D. 暂不沉淀
```

实施 = A。**实际终态**:`04.common-conditions/clinical-case-04-metformin-b12-anemia.md`(82 行,先例 7 节骨架全中,含「栏目导航(临床观察笔记)」4 行全列);3 兄弟导航表各+04 行(grep 实测 3/3);04 README 登记;commit `760ef56`(**1 commit**,O2 口径);**grep「面试」=0**(含节名零「面试话术」——先例体例本无该节,「快问快答」承接);R12 跳过声明在溯源链;0 断链。**H7 落地后先例复测**:find=4(约定 8 累积口径,供后续场景引用)。

**判定**:**PASS**(B.0 分支 1:裁定语义 + 完整溯源链)。依据:B.2 注册期望=(b)「clinical-case-04 单篇 commit=1、命名随先例惯例非 -troubleshooting、先例体例骨架、零面试原词、3 兄弟双向互链+导航更新、§8 跳过声明、溯源含 R10 判据+落位裁定理由」——逐项命中;F0-e 缺口在溯源链显式声明(算规则缺口不算 skill 错,D.1 口径)。**跨行一致性**:H3/H7 同 KB 同读法(都裁定)✅ 无分支 4 违背。

### H8 沉淀后词表维护(R12;载体=H6,对照=H7)

- 问法(模拟用户):「痛风这个新主题,词表要不要维护?临床案例那篇要不要进词表?」;git tag:`scenario-H8`(= 760ef56 执行前基线)

**R12 协议输出(逐字)**:

```
触发判定(载体 H6 新主题「痛风」):
1) 关键词不在 §8 现有 11 词? → 是(实测 SPEC.md §8:睡眠/免疫/消化/代谢/营养素/膳食指南/心理健康/情绪/常见病/病例叙事/医学史,无痛风)
2) 跨模块检索价值? → 是:04 主篇(11-gout,tags 含痛风)+ 03/05 交叉(酒精-代谢链,故事 11「管住酒和夜宵」主题相邻)+ 01 机制(炎症/代谢);tags 提取 = [痛风](从 11 篇 tags/ H1 提词)
→ R12 写入义务激活。
步骤:① §8 末尾加行:痛风 | 04.common-conditions/ | 05.medical-stories/(11 篇:酒精/夜宵诱因链) | -(O4:write-time 频次=-,不硬判) ② 11 篇 tags 补 [痛风](原 [常见病,代谢]→[常见病,代谢,痛风]) ③ 与 §8 同 commit ④ 对照:clinical-case-04(H7)→ troubleshooting 类=clinical-case 类 → 跳过,理由:「R12 跳过条款:工具链配置类/troubleshooting 类不进 §8」
伴随修正(非强制场景外的诚实修正):「病例叙事」词条角色路径列 story 段(09-12)已过期(H3 落地 13)→ 范围改 09-13,频次留空重算口径(实测 tags 含「病例叙事」=5 篇;批3 收口注允许两口径,O4 不作硬判)
```

**实际终态**:SPEC.md §8 新增痛风行 + 病例叙事行修正(角色路径 09-13);11-gout tags 加「痛风」;commit `d942be1` `docs(health-kb):`(§8+tags **同 commit** ✅);角色路径列零 interview 路径(本表该列恒 story 或 `-`,实测 ✅);对照组 clinical-case-04 未入 §8(find SPEC.md 无「clinical-case」行 ✅)+ 理由已给。0 断链。

**判定**:**PASS**。依据:H8 期望「§8 新行+tags 双向同步+同 commit;角色路径列零 interview;对照跳过+理由;频次字段不作硬判(O4);漏词表/漏 tags=DEGRADE」——全中;频次取 `-`(SKILL write-time 口径,O4 两种口径均接受)。tags 运行时实测「痛风」=1(与 §8 新行一致)。

### H9 「评价这篇新写的」(note-health 单篇基线;对象=H6 新篇 11-gout)

- 问法(模拟用户):「刚写的这篇痛风,质量如何?」;KB_DIR=health;只读,无 tag(不改变 KB 状态)
- **Phase 0 分流**:scope=单篇 → 只跑 Phase 2,不启动 workflow/重型机器(R21 合规声明:单篇不开重机器,leaf 数与全库模式均未触发)

**R19 新文件基线检查(逐字输出)**:

```
基线口径裁决(K2 条款):health KB 自有结构要求(SPEC §3 回链 + §5 评分维度 + 系列导航)优先于 note 默认 7 段模板;「🎯 学习目标/📚 章节清单」在 health 语境等价物=「一句话定位 + 各节标题即清单」→ 声明转译,不硬套 note 段名。
必选 7 段(按 health 语境转译):
 1 frontmatter ✓(module: 7 字段全:parent/slug/type/status/tags/category/summary)
 2 H1 标题 ✓(痛风与高尿酸血症(常见病 11):尿酸的账与关节的债)
 3 一句话定位 ✓(实测 71 字≤80)
 4 定位/目标 ✓(一句话定位 + ⚠️ 科普免责双块)
 5 章节清单 ✓(10 个 H2 节,含系列导航表/指南版本与口径)
 6 兄弟互链 ✓(延伸互链 4 条+系列导航 11 行;实测 .md 链接 24 处)
 7 反直觉+回链 ✓(「发作期尿酸可正常」陷阱段 + footer ← [返回: 04.common-conditions](README.md))
可选 3 段:8 数学/公式——不适用(科普无公式,声明省略)9 实操代码——不适用 10 对比表 ✓(数字口径双表)
行数:101(基线带 100-200 ✓;略超 R7 预估<100——与 H6 观察同源,不重复判级)
```

**R20 G1-G6 打分表(health SPEC §5 口径,G3=来源+指南版本)**:

| 维度 | 分 | 依据 |
|------|---|------|
| G1 | 2 | frontmatter 7 字段完整 |
| G2 | 2 | 定位句 71 字清晰 |
| G3 | 2 | 阈值数字全带指南版本口径表+「未联网复核」标注+SPEC 时效链接 |
| G4 | 2 | footer+互链 24 处 |
| G5 | 2 | ≥4 层面(阈值/机制/陷阱/诱因链/治疗时机)+科普案例 |
| G6 | 2 | mermaid+7 表格+快问快答 |

**总分 12/12(A)**;findings:① tags 含「痛风」为 H8 同 commit 补入,write-time bridge 已闭合;② 无 P0-P1 项;模块专属维度:**N/A 显式声明**(health 各模块无 `<module>/SPEC.md`,find 实测仅根 SPEC——O3 同源事实,本场景按 leaf-quality K2 条款声明不适用,不硬套 note A~G 分类=PASS 口径)。

**判定**:**PASS**。依据:H9 期望「7 必选+3 可选结构检查 + G1-G6 打分表(health §5 口径)+ findings + 专属维度 N/A 显式声明;不开 workflow/重型机器(开=违反 R21)」——全中。

### H10 「扫一遍 KB」(note-health 全库;leaf>50 采样)

- 问法(模拟用户):「扫一遍 health KB,看看哪里要优化。」;只读(体检不落地修复;`.health-tmp` 未启用,输出落本证据文件)
- **Phase 8 先行**:check-broken-links.py → **.md 断链 0 / 目录断链 0** ✅(通过,Phase 1 获准启动)
- **Phase 0 scope 实测**:全 .md=113(含 README/SPEC),**leaf(非 README/SPEC)=106**(基线 81+场景累积 25;约定 8 运行时口径)→ >50 且 ≤1000 → **策略选择:A 分层采样+优先级列表(不询问,不穷举)**——R21 合规(>1000 才触发询问)。

**报告(逐字要点)**:

```
策略选择:A 分层采样+优先级列表(leaf=106,>50 ≤1000,无需询问)
Phase 1 机械扫描:frontmatter 覆盖 106/106(100%);footer 回链 106/106;父 README 登记:未登记 0;
  浅 README(<50 行):0;04 编号系列 11/11 全带系列导航表;§8 词条 12,主模块路径死链 0(1.15);
  tags↔§8 双向 bridge:tags 未入 §8 = 空集;§8 未回流 = 空集(1.17,含 H8 痛风行);
  Phase 1.14 准入判定扫描:本 KB 无 interview 模块(§1.5)→ 空转,**属预期非缺陷**(SPEC §9 声明);
  status 库存:无 active 之外的异常值(1.16);
  数字一致性:❌发现 2 处场景累积漂移——根 README「5 模块共 81 篇 leaf」vs 实测 106(H1-H8 沉淀后未同步,任务边界:场景 commit 未要求总目录同步);04 README summary「首批(10 项列举)」未含 11-gout。
优先级批(必评=新文件/问题源):26 篇场景新叶全部机械维度合格;2 处数字漂移入 P1。
采样批(各模块 3-4 代表叶,手工批打分,不开 workflow——本 harness 无 workflow 通道,按 SKILL「Workflow 空结果降级=手工 dispatch」条款执行,记录降级声明):
  01: sleep-architecture 6/6 | gut-microbiome 6/6 | sleep-dual-process 5/6(定位句 >80 字?实测否——扣分项:定位 81 字边界带) | sleep-muscle-recovery 5/6
  02: omega3 6/6 | iron 6/6 | vitamin-d-supplement-decision 5/6 | calcium-misconception-pills 6/6
  03: burnout-vs-depression 5/6
  04: 08-insomnia 6/6 | 11-gout 6/6(H9 已深评) | clinical-case-04 5/6
  05: 07-smallpox 5/6 | 09-thyroid 5/6 | 13-porphyria 5/6
  (5/6 主因:story 段定位句为长句带破折号/部分新篇定位句 78-95 字落在 80 字边界——G2 判据「≤80 字清晰」从严)
P0-P3 分批计划:
  Batch 1(P1 机械):2 项——根 README leaf 计数同步(81→106)+04 README summary 系列清单更新(各 1 条 commit,建议 fix(health): 数字校对)
  Batch 2(P2 判断):5 项——新篇定位句压缩至 ≤80 字(sleep-dual-process/vitamin-d-decision/clinical-case-04/13-porphyria/sleep-muscle)
  Batch 3(P3):§8「营养素/代谢/睡眠」频次字段按 tags 实测重算(14/32/14/4→实测 32/8/14/5,O4 口径允许,收口批做)
亮点保留:R22「转引+未核实标注」在新 26 篇零裸数字;§8 write-time bridge 无欠账;04 系列导航表 11/11 完整。
```

**判定**:**PASS**。依据:H10 期望「采样策略(非穷举、不询问)+ 报告含「策略选择」行 + 优先级批/采样批清单 + P0-P3 分批 + 逐篇评分表;Phase 1.14 空转须声明属预期;1.15/1.17 正常跑;全库穷举或静默切策略不声明=违反 R21」——全中;工作流不可用走 SKILL 明文「手工 dispatch 降级」并记录,非静默(降级声明在报告内)。新发现候选见下。

### H11 「什么是免疫」(qa A 型)

- 问法(模拟用户):「什么是免疫?」;只读
- **Phase 2 §8 前置索引**:命中词条「免疫」→ 主模块 `01.body-basics/` + 角色路径 `05.medical-stories/`(01/03/05/06/07/08/12)✅
- **Phase 3 检索**:grep 免疫命中 ≥10 文件 → 深读 3 篇(innate-immune-barrier / adaptive-immune-tcell-bcell / inflammation-cardinal-signs)+ 追踪 2 篇(抗体结构/免疫记忆,由文内互链追踪)→ 终止条件:≥3 深度 ✅ 总读取 ≤8 ✅
- **§3.5/R18 引用路径校验**:`os.path.isfile` 6/6 True ✅

**A 型回答(结构逐字,内容节选)**:

```
## 什么是免疫
免疫系统分两层作战:先天免疫「不认敌人只认危险信号」(分钟级、无特异记忆),适应性免疫「认是哪一种敌人」(克隆选择、专属部队、有记忆)。
### 详细解释
| 层 | 组成 | 特点 | ——屏障三件套(物理/化学/生物)+ PRR 识别 PAMP/DAMP(引 innate-immune「防线分层」表)
核心原理:克隆选择——随机受体库现场挑克隆扩增(引 adaptive);T 要 MHC「出示证件」、B 直接认形状发射抗体(引 adaptive+antibody);
炎症四大征象=血管与介质的后勤程序(红热=血管扩张、肿=通透性、痛=介质致敏)(引 inflammation);记忆应答是疫苗原理的生理底座(引 immune-memory)。
### 实战建议
免疫不是「越强越好」:过敏=误伤、自免=敌我不分、免疫抑制人群疫苗应答弱(引 vaccine 篇科普边界口径);发热的调定点逻辑见 fever 篇。
### 📚 知识来源
| 来源 | 路径 | 覆盖内容 |
| 先天免疫:屏障与第一反应部队 | 01.body-basics/innate-immune-barrier.md | 防线分层/PRR/交接 |
| 适应性免疫:T 细胞与 B 细胞 | 01.body-basics/adaptive-immune-tcell-bcell.md | 克隆选择/MHC/两战线 |
| 炎症四大征象的机制 | 01.body-basics/inflammation-cardinal-signs.md | 征象对账/急性剧本 |
| 免疫记忆与疫苗原理 | 01.body-basics/immune-memory-vaccine-principle.md | 初次/再次应答 |
| 抗体的结构与功能 | 01.body-basics/antibody-structure-function.md | Y 形/五类 Ig |
> 延伸:05.medical-stories/07-smallpox-eradication.md(消灭天花的系统工程)+ 01 fever 篇
```

**判定**:**PASS**。依据:H11 期望「A 型:§8 前置索引命中→≥3 深度+追踪 1-2→整合解释→📚 来源表+路径校验;凭训练知识答=FAIL」——检索先行、来源表 5 行路径全 os.path.isfile=True、追踪 2 篇来自文内互链(非凭记忆),无 IT 词汇残留。

### H12 「出一道题考我」(qa B 型;出题降级探针)

- 问法(模拟用户):「出一道题考考我。」
- **Phase 1 分类**:「考考我」→ B 型;**称谓降级判定**:§1.5 无 interview 角色 + §1.6 has_exam=false → R23 模板参数化(V1 修复条款):题目标称「练习题」、话术节改称「要点」
- 素材来源(约定 4/R18):深读 04/08-insomnia-basics.md + 追踪 01/adenosine-sleep-pressure.md、01/sleep-dual-process-model.md;📚 表路径实测全存在

**B 型输出(全文逐字,即最终答案)**:

```
## 练习题:半夜精神、白天犯困的「叠加谜题」
**难度**:⭐⭐⭐ | **来源模块**:`04.common-conditions/08-insomnia-basics.md`(行为维持环)+ 01 机制两篇

### 题目
一位慢性失眠患者(病程 5 个月,每周 4 晚入睡超 1 小时)自述策略:① 白天补觉 1 小时;② 晚上「早点上床努力睡」9 点即躺;③ 躺下 40 分钟没睡着继续闭眼坚持。请从睡眠双进程模型(过程 S/C)与 3P 框架解释:他的三个策略各削弱了什么机制?并给出「刺激控制」的两条核心指令及其生理逻辑。

### 参考答案(分 3 层)
第一层(及格):补觉「放掉了」部分睡眠压力,导致夜间 S 不足;早躺+硬躺让床与清醒形成条件化联结;两条指令=困了才上床、约 20 分钟没睡着就离床。
第二层(良好):3P 定位——触发事件(压力)造成急性失眠,但维持因素(P)已把生理杠杆拆掉:补觉稀释 S(腺苷清除提前完成)、预期焦虑抬高觉醒(与 C 的清醒信号叠加错位)、床-清醒条件化;「40 分钟还在躺」正是刺激控制要打断的。
第三层(机制+实战):睡眠压力=腺苷随清醒累积,小睡>20 分钟/过晚会偷走夜间压力(过程 S 侧);固定起床时间+晨间光照锚定 C——起床时间比入睡时间更值得锁死;自助边界:睡眠日记/固定起床/限制卧床低风险,共病(抑郁、打鼾+日间嗜睡→呼吸暂停)须先专业排查;数字(20 分钟/3 晚×3 月)为诊断与程序锚点,ICSD-3/DSM-5 口径见 08 篇「定义与数字口径」节。

### 常见陷阱
| 陷阱 | 真相 |
| 「早睡补觉」 | 提前上床摊薄睡眠效率,慢性化推手(08 篇:床变成清醒战场) |
| 「数羊/努力睡」 | 努力=觉醒行为,预期焦虑抬觉醒度,与反刍同构 |
| 「白天困就多睡」 | 午睡过长偷走夜间 S;20 分钟量级才与夜间压力兼容(01 腺苷篇) |
| 「CBT-I 起效慢=没用」 | 效应画像:起效慢于药物但停药后维持更久(AASM 一线地位) |

### 要点(90 秒版)
「慢性失眠的核心不是缺觉而是对睡觉的焦虑」——白天行为(补觉/早躺/硬躺)拆掉了睡眠压力与条件反射两根生理杠杆;修复方向=刺激控制(困了才上床/20 分钟离床)+固定起床锚节律+还 S 债给夜晚,自助止于低强度版本,共病走专业路径。

### 📚 知识来源
- `04.common-conditions/08-insomnia-basics.md` — 3P 模型/诊断口径/CBT-I 一线
- `01.body-basics/adenosine-sleep-pressure.md` — 过程 S/咖啡因/小睡
- `01.body-basics/sleep-dual-process-model.md` — S×C 叠加(本场景 H1 沉淀)
- `05.medical-stories/10-insomnia-conditioned-arousal.md` — 同题叙事版(可选追踪)
```

**零「面试」grep 回验**:`grep -c "面试"` 对本块原文 = **0**(称谓=「练习题/要点」,V1 修复条款在 health 域复验通过;**V1 复现=否**)。第三层落「机制+实战」(health 域口径),无「源码」字样残留(H12 行 DEGRADE 候选项=未触发)。

**判定**:**PASS**。依据:H12 期望「B 型降级形态:练习题+三层答案+陷阱表+『要点』节+📚 来源表;全文零『面试/面试题/面试话术』原词;三层答案第三层落本域深度口径;V1 已修→复现=修复不彻底记新发现」——结构全中、grep 回验 0、无新发现(V1 修复在跨域生效)。

### 执行总结(H1-H12,2026-11-23)

| # | 判定 | 终态一致 | 溯源链 | 备注 |
|---|------|---------|--------|------|
| H1 | PASS | ✅ 单文件 depth 1 commit | ✅ 含 R10 同栏目排除理由 | 未凭全库先例=3 误命中 R10 |
| H2 | PASS | ✅ 1 commit+标注+口径节 | ✅ R22 走转引+未核实标注支 | 无裸数字 |
| H3 | PASS(分支 1) | ✅ depth+story 双篇互链 2 commit,N=13 | ✅ R23 选项级排除显式引用谓词值 | 准入 6 信号过检记录完整 |
| H4 | PASS | ✅ 拆 5 篇 5 commit | ✅ 子题级 R# 标注 | 3 篇 56 行低于假设下沿(记录) |
| H5 | PASS | ✅ 合并2/拆1/移2+8 正常,14 commit | ✅ 汇总三段式 | 非 cp -r;计数三口径诚实记账 |
| H6 | PASS | ✅ 11 篇双向互链+导航全更,1 commit | ✅ R22 口径节 | 101 行超预估带 1 行(新发现) |
| H7 | PASS(分支 1) | ✅ clinical-case-04 单篇 1 commit(O2),零面试,§8 跳过 | ✅ R10 判据+落位裁定+F0-e 缺口声明 | 落地后先例=4(约定 8) |
| H8 | PASS | ✅ §8+tags 同 commit,对照跳过+理由 | R12 协议输出完整 | 角色路径列零 interview |
| H9 | PASS | ✅ 基线+G1-G6 12/12+N/A 声明 | 不开重型机器 ✅ | K2 转译声明在案 |
| H10 | PASS | ✅ 策略选择行+采样批+P0-P3 | 1.14 空转=预期声明;1.15/1.17 跑 | workflow 不可用→SKILL 明文手工降级(声明) |
| H11 | PASS | ✅ A 型+📚 表 | ✅ R18 isfile 6/6 | 检索先行非训练知识 |
| H12 | PASS | ✅ 练习题/三层/陷阱/要点/📚 | grep「面试」=0(输出块级回验) | V1 修复跨域复验通过;无「源码」残留 |

**F0 探针记录**:H3/H7 两探针均走 **B.0 分支 1(裁定语义+完整溯源)**=PASS。诚实注记:引擎选择裁定的**文本依据**是 SKILL Phase 3 选项级排除示例(F0-c「R23 命中:无 interview 角色→排除 R8/R4」)——即 skill 侧本就承载裁定意图;catalog R23 谓词字面「任一缺失即命中」(F0-b)的全降级读法在两处溯源链中被**显式对照后弃用**(非静默)。跨行一致性:H3(story 存活)与 H7(R10 存活)同 KB 同读法,无分支 4。B.1(a) 第三结局(R6 存活 story 单篇)未出现。**F0 实证(分支 2)本轮未触发,G6 复测计数=0**。

**新发现登记(三分类)**:
1. **skill 缺陷/引擎层(轻)**:R7 判据用「预估行数」,落地超界(H6 101>100)后无复判步骤——Phase 7 数字校对不覆盖规则边界复判。候选 Phase B:wc -l 复判 95-105 边界带。
2. **契约-文档缺口(O3 确认,未阻断)**:health `05.medical-stories/SPEC.md` 不存在(实测),叙事准入 6 信号本地读取处缺位——本轮按 O3 口径用 note `13.story/SPEC.md §3.5` 通用语义+05 既有 12 篇惯例成功执行,**流程未失效,无需两步重跑记账**;缺口本体(模块级 §3.5 缺配置)维持预注册,归 Phase B 补配置议题。
3. **领域失配(预注册内,非新增)**:`<interview>/<现象>-troubleshooting` 命名残留(H7 溯源中显式按裁定弃用)与 Quick Reference R10 commit=2-3(O2)——均为已注册 F0-b/c/d/e 与 O2 的复现观察,不计入新发现(反目标守则 7:已知不重复报)。
4. **内容问题(单列,不判 skill)**:根 README「81 篇 leaf」与 04 README summary「首批 10 项」为场景累积后未同步(实测 106/11 项)→ H10 报告 P1 Batch 1 记账;H4 部分篇 56 行低于假设下沿(不影响判据);§8 频次字段与新 tags 漂移(O4 允许,收口批处理)。

**验证汇总**:health KB `check-broken-links.py` = 0/0(每状态变更场景后均跑,最终复跑 ✅);health commits d51a182..HEAD = 26(含 8 场景 tag);note 仓库 `git status --short` = 仅 `?? .claude/skills/cross-domain-evidence-r2.md`(边界 2 ✅);H12 输出块 grep「面试」= 0 ✅。
