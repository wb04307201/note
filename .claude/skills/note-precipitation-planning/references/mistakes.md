<!--type: reference · 2026-09-23 P2-1 拆分自 SKILL.md L905-L1339(435 行) -->
# Common Mistakes(Mistake 1-20)

> 本文档从 `SKILL.md` 的 `## Common Mistakes` 段落拆分而来(2026-09-23,P2-1 改进)。  
> SKILL.md 主文档 1431 → 预计 ~996 行。
>
> **索引**(20 项 + 主题速查):

| # | Mistake | 主题 | 教训年份 |
|---|---------|------|---------|
| 1 | 跳过现状盘点 | 流程 | — |
| 2 | 单一深度评估 | 流程 | — |
| 3 | 位置错位 | 分类 | — |
| 4 | 缺互链 | 互链 | — |
| 5 | subagent 调 AskUserQuestion 失败 | subagent | — |
| 6 | 缺 commit 策略 | commit | — |
| 7 | 数字虚报 | commit | — |
| 8 | 路径深度错误 | 路径 | 2026-07-25 |
| 9 | 单向链接(child 链 parent,parent 不回链) | 互链 | — |
| 10 | 系列内兄弟不互链 | 互链 | — |
| 11 | subagent silent failure(自报 PASS 但文件不存在) | subagent | — |
| 12 | git reset --soft + git commit --amend 错位 | commit | — |
| 13 | 过度宣称 PASS("所有项 PASS" 但用户规格未对齐) | subagent | — |
| 14 | 新内容引入新 broken links | 断链 | 2026-07-25 |
| 15 | 同 README 内重复维护多个等价表格 | 文档 | 2026-07-25 |
| 16 | 多主题错误合并成一个文件 | 拆分 | 2026-07-26 |
| 17 | 多主题沉淀导致上下文溢出 | 上下文 | 2026-07-26 |
| 18 | 并行 subagent 共享父 README 导致题数漂移 | 并发 | 2026-07-30 |
| 19 | 父 README 历史遗留问题 | 并发 | 2026-07-30 |
| 20 | 双层沉淀的"弱关联"互链 | 互链 | 2026-08-20 |

---

## Common Mistakes

### ❌ Mistake 1: 跳过现状盘点

**症状**：直接在某个位置创建新文件，没注意已有类似内容 → 重复沉淀

**修复**：Phase 1 不可跳过；用 grep + find 扫描 ≥ 5 个相关文件

### ❌ Mistake 2: 单一深度评估

**症状**：默认"是" → 沉淀任何主题 → note 膨胀

**修复**：Phase 2 用 3 信号判断（高频 + 内容深 + 缺口真实）；不满足就不沉淀

### ❌ Mistake 3: 位置错位

**症状**：把技术原理放 `13.story`（叙事）/ 把面试题放 `08.ai-foundations/01-fundamentals`（原理）/ 把算法放 `04-architecture`（架构）

**修复**：Phase 3 决策树 + 检查主模块子目录的命名约定（`01-fundamentals` / `02-technology-stack` / `03-engineering` / `04-architecture`）

### ❌ Mistake 4: 缺互链

**症状**：新文件是孤岛，没有反向链到已有内容 → 知识碎片化

**修复**：Phase 4 决策时**强制要求**双层/三层沉淀带互链；Phase 7 自检"至少 2 个旧章节互链"

### ❌ Mistake 5: subagent 调 AskUserQuestion 失败

**症状**：subagent 试图调 AskUserQuestion 但工具不可用 → 退化为写实施

**修复**：subagent **返回结构化选项**（不是直接调工具），让 orchestrator 转交用户

### ❌ Mistake 6: 缺 commit 策略

**症状**：模糊 commit message（"update docs"） / 多个 commit 描述重叠 / 混 refactor + feat

**修复**：Phase 6 严格按 `<type>(<slug>): <动作>` 格式；每个 commit 只做一类变更

### ❌ Mistake 7: 数字虚报

**症状**：commit message 说"删除 6 个孤儿目录"但实际只改 README

**修复**：Phase 6 数字声明必须由 implementer 用 `find` / `wc -l` 重新数；不允许估算

### ❌ Mistake 8: 路径深度错误（2026-07-25 强化）

**症状**：13.story 链接 `../../08.ai-foundations/12.interview/11.ai/...`（多一层）→ broken link

**历史案例**（2026-07-25 ACP 沉淀）：
- ❌ `mcp.md` —— 以为是独立文件，实际 MCP 在 `context-engineering/README.md` 内联
- ❌ `multi-agent-system-design` 在 `../../../03-engineering/...` —— 实际在 `12.interview/11.ai/`
- 根因：**没实际验证目标路径就写**

**修复（4 步强制）**：
1. **目标路径必须实际验证**：用 `find "$KB_DIR" -name "<target>" -type f` 或 `ls -la <path>` 确认目标存在
2. **手动数层级**：从源文件向上数 `../` 数量 = 目标深度差（注意 `$KB_DIR/` 跨模块跳数）
3. **每文件 commit 后立即跑 broken links 扫描**（见 Phase 6.5）
4. **不依赖"记忆"**：每次都 grep/find 验证，不要凭印象写路径

**🆕 强化（2026-07-25 经验）**：
- subagent 写完每个 `[...](./xxx/README.md)` 链接后**必须**用 `find "$KB_DIR" -name "xxx" -type d` 验证目标目录存在
- 如目标目录不存在，使用**替代方案三选一**：① 删除链接 ② 改为指向父系统（如 CMDB → ITSM with 注释）③ 新建对应 README（如确有需求）
- subagent prompt 模板**强制要求**：每个深读链接必须在最终报告里列出 `find` 命令的实际输出
- 历史案例（2026-07-25 业务系统补深）：QMS 引用 `../06-specialized/lims/README.md`（少一层 `../`，正确应是 `../../06-specialized/lims/README.md`），独立 `find` 验证 + 修复为正确路径

**🆕 强化（2026-07-27 经验 — 父 README 目录表更新）**：
- 当 subagent 更新**父 README 目录表**（如 `12.interview/11.ai/README.md` 添加新面试题条目）时，目录表中的深读链接路径最易出错
- 历史案例（2026-07-27 Batch 1）：`12.interview/11.ai/README.md` 目录表新增 agent-reliability 条目，subagent 写 `../../../08.ai-foundations/03-engineering/agent-reliability/README.md`（3 层 `../`），但 `12.interview/11.ai/` 到 `08.ai-foundations/` 只需 2 层 `../../`
- **防御规则**：更新父 README 目录表时，用 Python 验证路径：
  ```python
  import os
  src_dir = '$KB_DIR/12.interview/11.ai'  # 父 README 所在目录
  tgt = '$KB_DIR/08.ai-foundations/03-engineering/agent-reliability/README.md'
  rel = os.path.relpath(tgt, src_dir)  # 自动计算正确相对路径
  print(rel)  # 输出: ../../08.ai-foundations/03-engineering/agent-reliability/README.md
  ```
- 不要手动数 `../` 层数，用 `os.path.relpath` 自动计算

### ❌ Mistake 9: 单向链接（child 链 parent，parent 不回链）

**症状**：新文件链接到 parent / 同级兄弟，但**parent / 同级兄弟没有反向链**到新文件。例如：

- 沉淀"05-agent-evaluation"，链到 `07-llmops/README.md` —— 但 `07-llmops/README.md` 没反向链到新文件
- 沉淀"production-agent 实战"，链到 `09.ai-applications/README.md` —— 但 `09.ai-applications/README.md` 没反向链到新文件

**修复**：
- **强制规则**：每个新文件 commit 时，**主动给被链接的 parent / 同级兄弟加反向链**（单独 refactor commit）
- 双向互链是**新内容责任**，不是"以后再说"
- Phase 7 自检加「互链双向性扫描」项，**不达标则 commit 不合格**

**反直觉点**：很多人以为"我加了 2 条反向链就完事" —— 实际上被链接的 parent / 兄弟文件**也要回链**，否则会出现"两个 leaf 互相知道，但 parent 完全不知道新成员"的孤岛现象。

### ❌ Mistake 10: 系列内兄弟不互链

**症状**（两种场景）：
- **场景 A**：向已有系列添加新文章后，新文件只链回 README，已有兄弟也不知道新成员的存在。
  - 例：agent-execution-patterns 系列有 01-react / 02-plan-execute，新增 05-dag / 06-multi-agent
  - 但 01 和 02 的文件末尾**没有链向** 05 和 06 —— 同系列 6 篇文章各自孤立
- **场景 B（2026-07-25 新增）**：**历史遗留**——已有编号系列，但所有文件**历史都没加过"系列导航表"**。
  - 例：`01.java-and-jvm/kotlin/` 有 01-basics.md / 02-oop.md / 03-functional.md / 04-advanced.md / 05-coroutines.md 共 5 篇，**全部缺链**（没有任何一篇末尾有"系列导航表"）
  - 这类问题体检时通过 `Phase 1.9 系列完整性` 扫描可发现

**修复**：
- **强制规则**：向已有系列新增文章时，**每篇文件末尾必须有"系列导航表"**
- 系列导航表 = 一个表格，列出系列内所有文件 + 一句话核心问题
- 新文件加导航表 + 所有已有兄弟加/更新导航表
- Phase 7 自检加「系列导航表完整性」项

**批量修复脚本**（场景 B 适用）：
```bash
# 找所有有编号系列的目录，补齐每个系列所有文件的"系列导航表"
for dir in $(find "$KB_DIR" -type d -exec sh -c 'ls "$1"/[0-9]*.md 2>/dev/null | wc -l | grep -q "^[2-9]" && echo "$1"' _ {} \;); do
  files=$(ls "$dir"/[0-9]*.md 2>/dev/null)
  # 检查哪些文件没有"系列导航表"
  for f in $files; do
    if ! grep -q "## 系列导航" "$f"; then
      echo "缺系列导航表: $f"
    fi
  done
done
```

**检测方法**：
```bash
# 找系列目录（有编号文件的目录）
for dir in $(find "$KB_DIR" -type d -exec sh -c 'ls "$1"/[0-9]*.md 2>/dev/null | head -1 | grep -q . && echo "$1"' _ {} \;); do
  echo "系列: $dir"
  for file in $(ls "$dir"/[0-9]*.md 2>/dev/null); do
    for other in $(ls "$dir"/[0-9]*.md 2>/dev/null); do
      [ "$file" = "$other" ] && continue
      other_base=$(basename "$other")
      if ! grep -q "$other_base" "$file" 2>/dev/null; then
        echo "  ⚠ $(basename $file) 未链向 $other_base"
      fi
    done
  done
done
```

### ❌ Mistake 11：subagent silent failure（自报 PASS 但文件不存在）

**症状**：subagent 报告 "X/Y self-check PASS" / "11/11 PASS" / "全部完成"，但 `git status --short` 为空、`git log` 无新 commit、目标文件不存在

**修复**：
- orchestrator 不能相信 subagent 自我报告，必须独立验证：`ls -la FILE` + `git status --short` + `git log --oneline -3`
- subagent 报告缺失 commit hash → 视为 commit 失败，立即 abort + 重派
- 注意 commit 1 章节的 subagent 失败概率最高（首次创建文件复杂操作）

**🆕 红旗识别（2026-07-25 经验）**：
- subagent 最终报告出现 **"如果需要...我可以..."** / **"可以..."** / **"建议你..."** / **"等你下一步指令"** 等委婉语 → **silent failure 红旗**，**立即 abort + 重派**，不需要等 `ls -la` 验证（红旗本身已足够判定）
- 真实 commit 完成的报告必含**实际 commit hash + `ls -la` / `wc -l` 命令输出**（不是"已完成"等模糊表述）
- 历史案例（2026-07-25 客服系统首次 subagent）：报告结尾"如果需要，我可以接着..."，但 `git log` 显示无新 commit、`ls -la call-center/README.md` 显示文件不存在 → 1 次重派即成功

### ❌ Mistake 12：git reset --soft + git commit --amend 错位

**症状**：`git reset --soft BASE` 撤销 3 个 commit 后重新 commit 1/2/3，HEAD 此时在 commit 3。后续 `git commit --amend` **修改的 HEAD（commit 3）**，而非你以为的 commit 1。结果 3 个 commit hash 全变

**修复**：
- reset 后**不要使用 `git commit --amend`**——直接 `git commit -m "..."` 创建新 commit
- 如必须 amend 早 commit，先 `git reset --soft TARGET_COMMIT^` + 重新 stage → commit（不复用 amend）
- 每次 reset 后**用 `git log --oneline` 确认 HEAD 位置**再决定 amend / commit

### ❌ Mistake 13：过度宣称 PASS（"所有项 PASS" 但用户规格未对齐）

**症状**：final report 宣告"11 项 PASS"、"全部完成"，但 peer 严格审计后发现用户原规格中的具体细节（特定链接 / 特定工具 / 特定代码示例）缺失

**修复**：
- orchestrator 的 final report **必须**逐项对照用户原始 question，把用户提到的每个具体名词 grep 验证
- 例：用户问"高可用高并发图片视频" → final report 必须 grep `WebP`、`AVIF`、`HLS`、`DRM`、`高可用`、`4 层防线` 全部存在
- 反例：final 报告"10 节齐全 PASS" 实际未 grep "4 层防线" "AES-128 "代码示例"" 实际是否落地

### ❌ Mistake 14：新内容引入新 broken links（2026-07-25 历史教训）

**症状**：沉淀 6 个新文件到 $KB_DIR/ 后，新文件中的 markdown 链接路径写错（相对路径多/少一层 ../），引入新的 broken links。**即使新内容质量满分（20/20），broken links 增量仍然是结构性硬伤**。

**历史案例**（2026-07-25 coding-agents 沉淀）：
- 6 个新文件 + 8 commit 后，**新引入 0 broken links**（验证通过 ✅）
- 但反例风险：在 $KB_DIR/03.java/01-foo/02-bar/README.md 写 `../baz/README.md` 而不是 `../../baz/README.md`，会让 note 出现真错

**🆕 强化（2026-07-25 经验）**：
- subagent 写新 README 引用任何系统前**必须**先 `grep -r "<system>" 10.business-systems/` 确认该系统是否独立存在
- 如果**不是独立系统**（如 CMDB 是 ITSM 子模块、APR/MRP 是 ERP 子模块），应使用替代方案：① 删除链接 ② 改为指向父系统 with 注释（如 `[ITSM 深读](../../06-specialized/itsm/README.md)`（含 CMDB））
- 历史案例（2026-07-25 业务系统补深）：EAM 引用 `../../06-specialized/cmdb/README.md`（CMDB 不是独立系统，是 ITSM 子模块），独立验证 `ls -la 10.business-systems/06-specialized/` 发现 cmdb 目录不存在 → 修复为 ITSM with 注释

**修复（沉淀完成后的简单兜底）**：

```bash
# 沉淀完成后立即跑 broken links 扫描（严格 regex 版）
# 期望输出：broken links: 0
python -c "
import os, re, glob
LINK_RE = re.compile(r'(?<![|\[])\[([^\]]*)\]\((?!https?://)(?!mailto:)(?!#)([^)#\s]+?\.md)(?:#[^)]*)?\)')
PLACEHOLDERS = ['x/README', 'xxx', 'xx/yy', '../09.ai-applications/...']
real_broken = 0
new_files = [f for f in glob.glob('$KB_DIR/**/*.md', recursive=True)
             if os.path.exists(f) and int(os.stat(f).st_mtime) > <沉淀开始时间戳>]
for readme in new_files:  # 优先扫本会话新文件
    content = open(readme, encoding='utf-8', errors='ignore').read()
    for m in LINK_RE.finditer(content):
        target_rel = m.group(2).strip()
        if any(p in target_rel for p in PLACEHOLDERS): continue
        target_abs = os.path.normpath(os.path.join(os.path.dirname(readme), target_rel))
        if not os.path.isfile(target_abs):
            real_broken += 1
            print(f'  ⚠ {readme} -> {target_rel}')
print(f'新文件 broken links: {real_broken}')
"
```

**最终报告**：final report 必须包含"broken links: 0"作为硬指标。

### ❌ Mistake 15：同 README 内重复维护多个等价表格（2026-07-25 历史教训）

**症状**：沉淀新章节时，作者**独立维护了 2+ 张等价信息源**（如"目录表" + "明细表"）。下游体检只扫**跨文件** / **文件级**重复，发现不了**同文件内冗余**。

**历史案例**（2026-07-25 13.story/README.md）：
- line 26-36：8 集群目录表（含"一句话"列）—— 完整 + 信息密度高
- line 336-353（已删除）：49 篇明细表（按类型分组）—— 100% 重叠 + 编号混乱（line 353 注释显式承认"11 = 续集二 / 14 = 番外二"）
- 两张表 49 篇文章编号需同时维护 → 维护成本翻倍 + 易漂移

**修复（沉淀时主动避免）**：
- **强制规则**：沉淀新 README 时，**每张表格只承载一个职责**，不要做"明细表"补完
- 多视角需要时，**用 section 标题区分**（"## 目录导航" + "## 速查表"），而不是重复表格
- Phase 7 自检加项：grep `\|---` 表格分隔行数 ≥ 2 的 README，人工检查表格列是否重叠 ≥ 50%

**历史兜底**：体检时如果发现同 README 内 2+ 张表格列字段重叠 ≥ 50%，标记为 P2 应修（合并 / 删除）。

### ❌ Mistake 16：多主题错误合并成一个文件（2026-07-26 历史教训）

**症状**：用户输入包含多个独立子主题（如"大模型思维工程 5 个灵魂拷问"），skill 未识别 → 把 N 个独立主题合成一个 419 行文件。后续不得不全部拆散 + 重新定位。

**历史案例**（2026-07-26 llm-production-thinking）：
- 用户说"沉淀大模型思维工程 5 个灵魂拷问"
- Phase 0 缺失 → 5 个独立主题（思维范式 / 成本控制 / 一致性 / 超时熔断 / 监控定位）被合成一个 `production-thinking-5q/README.md`
- 后续发现：每个主题都应该独立成文 + 独立面试题 → 全部拆散 + 目录重定位

**修复（Phase 0 强制）**：
- **Phase 0 主题识别**：在盘点前先判断用户输入是单主题还是多主题
- **多主题判断信号**：有编号（"5 个"、"3 大"）、有并列（"A + B + C"）、有"N 种"/"几种"
- **多主题处理**：每个子主题独立走 Phase 1-7 流程，不要合并
- **强关联主题**：创建系列目录（如 `llm-production-thinking/`），但每个子主题独立成文（01-thinking-paradigm.md / 02-cost-control.md ...）
- **面试题处理**：每个子主题各自独立一篇面试题（`llm-thinking-paradigm/` / `llm-cost-control/` ...），不要合成"5q"文件

**检测命令**：
```bash
# 检测"多主题合并"文件（单文件 > 300 行 + 包含多个独立 H2 章节）
for f in $(find "$KB_DIR" -name "README.md" -size +10k); do
  h2_count=$(grep -c "^## " "$f" 2>/dev/null)
  if [ "$h2_count" -ge 5 ]; then
    echo "  ⚠ 可能多主题合并: $f ($h2_count 个 H2 章节)"
  fi
done
```

### ❌ Mistake 17：多主题沉淀导致上下文溢出（2026-07-26 历史教训）

**症状**：一次沉淀 3+ 个主题（每个双层 = 2 文件 + 2-3 commit + 路径验证 + 反向链），上下文被占满 → compact → 后续工作（父 README 更新、broken links 验证、commit）需手动恢复。

**历史案例**（2026-07-26 Agent 三主题沉淀）：
- 用户问 3 个问题：Skill 命中率 / Structured Output / Planning-Acting-Monitoring
- 选择沉淀后 2 个主题（第 3 个 skip）
- 每个主题：Write 文件 + 路径验证 + 反向链 + commit = ~800 行上下文
- 3 个主题 = ~2400 行 → compact 触发 → 后续父 README 更新需手动恢复

**修复（Phase 0.5 强制）**：
- **Phase 0.5 上下文预算评估**：多主题时先评估每个主题的复杂度 + 预估上下文消耗
- **单次沉淀上限**：简单主题 ≤ 3 个 / 中等主题 ≤ 2 个 / 含复杂主题分批
- **分批执行协议**：Batch 1 完成 → 主动提示用户 compact → Batch 2
- **不要硬撑**：上下文 > 1500 行时主动建议分批，不要等 compact 被动触发

**检测信号**（何时该分批）：
- 已沉淀 2 个双层主题 + 还有第 3 个待处理 → 建议分批
- 每个主题涉及跨模块链接（路径验证成本高）→ 建议分批
- 需要更新多个父 README（每个 +0.5 复杂度）→ 建议分批

### ❌ Mistake 18：并行 subagent 共享父 README 导致题数漂移（2026-07-30 历史教训）

**症状**：多个 subagent 并行工作时，各自更新**同一个父 README** 的题数计数器。后完成的 subagent 看不到先完成的 subagent 的修改，导致题数不一致（如两个新文件已添加，但题数只 +1）。

**历史案例**（2026-07-30 Batch 3）：
- 3 个 subagent 并行：#5 debounce-streaming / #6 async-vs-multithread / #7 webpack-vite-migration
- #5 和 #7 都更新 `12.interview/09.front-end/README.md`
- #5 subagent 更新题数 26→27 ✅
- #7 subagent 添加了条目但**题数仍是 27**（应为 28）
- Orchestrator 收尾时发现并修正 27→28

**根因**：并行 subagent 基于"旧版本"的父 README 工作，后完成的 subagent 的 `git diff` 看不到先完成的 subagent 已 commit 的修改。

**修复（orchestrator 必做）**：
1. **父 README 题数更新由 orchestrator 统一收尾**，不在 subagent prompt 中要求
2. **subagent 只负责**：创建新文件 + 添加反向链到**非共享文件**（兄弟 README、主模块子文章）
3. **Orchestrator 收尾步骤**：
   ```bash
   # 1. 统计实际目录数
   ACTUAL_COUNT=$(ls $KB_DIR/12.interview/<module>/ | grep -v README | wc -l)
   # 2. 对比父 README 中的题数
   DECLARED_COUNT=$(grep -oP '共 \K\d+' $KB_DIR/12.interview/<module>/README.md)
   # 3. 如不一致，orchestrator 修正 + commit
   if [ "$ACTUAL_COUNT" != "$DECLARED_COUNT" ]; then
     # sed 替换题数
     git commit -m "fix(note): <module> - 修正题数 ${DECLARED_COUNT}→${ACTUAL_COUNT}"
   fi
   ```
4. **或者**：如果并行 subagent 涉及共享父 README，**改为串行执行**（#5 完成 → #7 开始）

**检测信号**：
- `ls <module>/ | grep -v README | wc -l` ≠ 父 README 中"共 N 题"
- `grep -c "^| \[" <module>/README.md` ≠ 父 README 中"共 N 题"

### ❌ Mistake 19：父 README 历史遗留问题（2026-07-30 新增）

**症状**：执行沉淀任务时，发现父 README 的题数计数器和实际目录数不一致，且缺少历史条目。执行后"旧账新账一起算"，导致最终状态混乱。

**历史案例**（2026-07-30 消息已读未读面试题）：
- 父 README 显示"共 20 题"
- 实际目录数：23 个（包含 media-upload、砍一刀算法等历史遗留）
- 缺少 3 个条目：media-upload、砍一刀算法、message-read-status
- Subagent 只添加了 message-read-status，没有发现历史遗留问题
- Orchestrator 收尾时发现并统一修正

**根因**：subagent 没有在执行前验证父 README 的准确性，只关注"新增"而忽略"存量"。

**修复（执行前必做）**：
1. **Phase 1 现状盘点必须包含父 README 验证**：
   ```bash
   # 1. 统计实际目录数
   ACTUAL_COUNT=$(ls $KB_DIR/12.interview/<module>/ | grep -v README | wc -l)
   
   # 2. 读取父 README 声明的题数
   DECLARED_COUNT=$(grep -oP '共 \K\d+' $KB_DIR/12.interview/<module>/README.md)
   
   # 3. 对比并记录差异
   if [ "$ACTUAL_COUNT" != "$DECLARED_COUNT" ]; then
     echo "⚠️  父 README 题数不一致：声明 $DECLARED_COUNT，实际 $ACTUAL_COUNT"
     echo "   历史遗留问题：$(($ACTUAL_COUNT - $DECLARED_COUNT)) 个条目缺失"
   fi
   
   # 4. 列出实际目录 vs 父 README 条目，找出缺失项
   ls $KB_DIR/12.interview/<module>/ | grep -v README | sort > /tmp/actual.txt
   grep -oP '\[.*?\]\(([^)]+)/\)' $KB_DIR/12.interview/<module>/README.md | \
     grep -oP '(?<=\()[^)]+(?=/)' | sort > /tmp/declared.txt
   comm -23 /tmp/actual.txt /tmp/declared.txt  # 实际有但父 README 没有的
   ```

2. **Orchestrator 必须在 Phase 6 前明确告知 subagent**：
   - 如果发现历史遗留问题，subagent 应该一并修正（不仅是新增）
   - 或者 orchestrator 在收尾时统一处理

3. **Subagent prompt 模板**：
   ```
   **执行前验证**：
   1. 统计实际目录数：ACTUAL_COUNT
   2. 读取父 README 题数：DECLARED_COUNT
   3. 如果不一致，列出缺失条目并一并添加
   
   **示例输出**：
   - 实际目录数：23
   - 父 README 题数：20
   - 缺失条目：media-upload、砍一刀算法
   - 本次新增：message-read-status
   - 最终题数：23
   ```

**检测信号**：
- `ls <module>/ | grep -v README | wc -l` ≠ 父 README 中"共 N 题"
- 缺失条目数 = 实际目录数 - 父 README 题数

**预防措施**：
- 在 Phase 1 现状盘点中加入"父 README 准确性验证"步骤
- 在 Phase 7 验证中加入"父 README 完整性检查"

### ❌ Mistake 20：双层沉淀的"弱关联"互链（2026-08-20 新增）

**症状**：新文件链接到"同栏目 / 同目录"兄弟，但**目标文件在被链接文件里 0 真实引用**——只是"凑兄弟题数量"，没有任何语义价值。

**历史案例**（2026-08-20 file-upload 双层审查）：
- A 文件 `12.interview/04.system-design/file-upload/README.md` 链向 `product-search`（同栏目兄弟）
- 但 A 全文 191 行 **0 处提及**"搜索 / 倒排 / 索引 / typeahead"
- 同样的问题：B 文件 `06.distributed-systems/04-high-performance/file-upload/README.md` 也链向 `product-search`
- B 全文 239 行 + 3 个子文件 **0 处提及**"搜索 / 倒排 / 索引"
- 结论：商品搜索与 file-upload 0 技术耦合，链接属"凑互链"

**根因**：开发者看到"同栏目"就自动加链接，没做"目标文件在被链接文件里是否有真实语义引用"的验证。

**与 Mistake 9 / 10 的关系**：
- **Mistake 9**（单向链接）= 结构层 —— child 链 parent，parent 不回链
- **Mistake 10**（系列不互链）= 结构层 —— 同系列兄弟互不知道
- **Mistake 20**（弱关联互链）= **语义层** —— 即使双向都链了，但链接本身无意义

**修复流程（用户怀疑 → 验证 → 决策）**：

1. **当用户说"感觉不相关 / 是不是不该链"** → 不要直接相信，做内部 grep 验证：
   ```bash
   # 在"被链接的文件"里 grep "目标文件主题关键词"
   grep -rn "<目标主题关键词>" <被链接文件目录>/
   ```

2. **判定表**：
   | grep 命中 | 用户直觉 | 行动 |
   |---|---|---|
   | 0 处 | 用户对 | 立即删除弱关联链接 |
   | ≥ 1 处 | 用户不准 | 保留并补"为什么相关"的语义描述 |

3. **互链价值判断公式**（适用于任何互链审查）：
   - **强关联**：目标文件在被链接文件内有 grep 命中（≥ 1 处）→ 留
   - **弱关联**：目标文件在被链接文件内 0 grep 命中 → 删
   - **保留原则**：强关联必留，弱关联删除（互链价值 < 维护成本）

4. **保留弱关联时的描述补强**（如果 grep 命中 ≥ 1 但描述不清晰）：
   ```markdown
   # ❌ 弱描述（看不出关联）
   - 同级案例：[敏感词过滤](../sensitive-word-filter/README.md) — AC 自动机 + 高并发过滤
   
   # ✅ 强描述（说明关联语义）
   - 同级案例：[敏感词过滤](../sensitive-word-filter/README.md) — AC 自动机 + 高并发过滤（上传后内容审核）
   ```

**检测脚本**（可在 Phase 7 自检时跑）：
```bash
# 对每个被链接的兄弟文件，做关联强度判定
for target in $(grep -oP '\]\(\.\./[^)]+\)' $KB_DIR/<file>/README.md | grep -oP '\.\./[^)]+'); do
  count=$(grep -c "<target的主题关键词>" <被链接的文件>)
  if [ "$count" -eq "0" ]; then
    echo "  ⚠ 弱关联: $KB_DIR/<file>/ → $target（被链接文件 0 处提及）"
  fi
done
```

**预防措施**：
- Phase 1 现状盘点：列出每个"潜在互链候选"时，**先 grep 验证关联强度**
- Phase 6 实施：写互链前问"目标文件在被链接文件里有什么真实引用"，无引用则不写
- Phase 7 自检：加「互链关联强度判定」项（见 Quick Checklist）

**反直觉点**：很多人以为"同栏目就是强关联"——实际上栏目只是分类，分类内的文件可能零耦合（如 file-upload 和 product-search 都是"系统设计"但完全不相关）。真正的强关联 = 真实语义引用，不是目录位置。

---
