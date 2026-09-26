# 项目级 ORCHESTRATION 规范

> **Inherits from**: [`SPEC.md`](SPEC.md) §7 SPEC 分层元规范
> **Updated**: 2026-09-26
> **Scope**: 3 个 meta-skill 的子 agent / git 协议,与具体沉淀流程解耦

本文件是 subagent 并行 / git 提交 / peer session 协调的**操作层规范**。
所有 3 个 skill（`note-precipitation-planning` / `note-health` / `note-knowledge-qa`）都需要遵守本文件。

---

## 1. Git author 一致性（subagent 必须用主账号）

### 背景

历史教训（2026-07-25 Phase 4 体检 + Batch 1-5 修复经验）：~6 个 subagent **修改了文件但没 commit**（"完成"报告但 `git log` 无 commit），需 orchestrator 收尾 commit。本条防御至关重要。

### 规则

- **subagent final report 必含 4 项命令输出**（避免"修改但未 commit" silent failure）：
  1. `git log --oneline -1` 的**完整输出**（不是只贴 hash）
  2. `git status --short` 的**完整输出**（working tree 状态）
  3. 实际修改文件的 `wc -l FILE` 输出
  4. 修改文件列表（`git diff --name-only HEAD~1 HEAD`）
- **subagent final report 必含 author 验证**：
  ```bash
  git log -1 --format="%an <%ae>" -- FILE
  ```
  输出必含 `吴博 <wubo_aaa@163.com>`，否则视为 author 错误
- **orchestrator 收尾协议**：subagent 报告"完成"但 `git log` 无新 commit → **立即 abort + 收尾 commit**（不信任 subagent 自我报告）
- **commit 1 必含文件创建**：commit 1 必须新增 1+ 个文件（不能用 pure README 修改代替），`find "$KB_DIR" -name "<topic>.md" -newer <commit-base>` 验证
- **失败检测规则**：如果 subagent 报告完成但 `git log` 没新 commit → 立即 abort + 重派，不要信任 subagent 自我报告

### Author 错误修复方法

```bash
# 修正最近 N 个 commit 的 author
GIT_AUTHOR_NAME="吴博" GIT_AUTHOR_EMAIL="wubo_aaa@163.com" \
  git rebase -i HEAD~N --exec 'git commit --amend --no-edit --reset-author'
```
⚠️ 注意 rebase 会改 commit hash，原预期 hash 会失效

---

## 2. 并发 peer session 协调（共享 worktree）

### 背景

历史教训：多 session 在同一 worktree 并发工作时，peer 可能修改 subagent 写过的文件而不 commit，或写文件后不 commit，需要协调。

### 规则

- **commit hash 必须可验证**：每次 session 派发后保留 agentId 列表 + 期望 commit hash，便于后续核对
- **peer 报告需独立验证**：
  - peer 报告"commit X 已落地" → `git log --grep="<topic>" --oneline` 独立验证
  - peer 报告"working tree 干净" → `git status -s` 独立验证
- **冲突协调**：当 commit 已被 peer 部分覆盖 + working tree 还有 modifications：
  - 检查 peer 修改是否被 commit（`git log` + `git diff`）
  - 如 peer 已 commit + working tree 还有未提交修改 → 询问用户偏好（reset 重写 vs polish commit）
- **不接受 floating peer 报告**：peer 报告后用 `git log --oneline` 独立核对才声明 final pass

---

## 3. 并行 subagent 共享文件协调（2026-07-30 教训）

### 背景

3 个 subagent 并行时，#5 和 #7 共享同一个父 README（`12.interview/05.frontend/README.md`）。#7 subagent 完成了 feat commit 但**反向链变更未 commit**（留在 working tree），且题数没有更新到正确值（27→28）。

### 规则

1. **识别共享文件**：派发前检查哪些父 README 会被多个 subagent 修改
2. **共享文件由 orchestrator 统一更新**：subagent prompt 中明确要求"**不要修改 `<父 README 路径>`**"，该文件由 orchestrator 统一更新
3. **Orchestrator 收尾 commit**：所有 subagent 完成后，orchestrator 检查 `git status --short`，将未提交的变更（反向链 + 题数修正）统一 commit

### Subagent prompt 模板（并行派发时）

```
**重要**：以下文件由 orchestrator 统一更新，你**不要修改**：
- `12.interview/<module>/README.md`（父 README 目录表）
- 任何其他 subagent 可能修改的文件

你只需负责：
1. 创建新 README 文件
2. 给**非共享**的兄弟 README 添加反向链
3. Commit 上述变更
```

### Orchestrator 收尾检查清单

- [ ] `git status --short` 检查是否有未提交变更
- [ ] 父 README 题数是否与实际目录数一致
- [ ] 所有反向链是否已 commit（不是只留在 working tree）

---

## 4. Subagent 父 README 更新职责（2026-07-30 教训）

### 背景

subagent 创建了新文件但没有更新父 README 的题数和条目。父 README 显示"共 20 题"，实际应该是 23 题（包含历史遗留的 media-upload、砍一刀算法等）。

### 规则

1. **单个 subagent 也必须更新父 README**：创建新文件后，必须同时更新父 README 的题数计数器和条目列表
2. **更新前验证准确性**：先统计实际目录数，再更新题数（避免"旧账新账一起算"）
3. **Orchestrator 最终验证**：所有 subagent 完成后，orchestrator 必须验证父 README 的准确性

### Subagent prompt 模板（单个任务）

```
**父 README 更新职责**：
1. 创建新 README 文件后，更新父 README：
   - 题数计数器：`## 文章清单（共 N 题，find 校对 YYYY-MM-DD）`
2. 添加新条目：
   - 找到合适的分类（如"业务系统设计"）
   - 添加一行：`| [新文件标题](新目录名/) | ⭐⭐⭐⭐ | 核心问题描述 |`
```

### Orchestrator 最终验证清单

- [ ] 父 README 题数 = 实际目录数
- [ ] 父 README 条目列表完整（无遗漏）
- [ ] 所有新文件都已添加到父 README