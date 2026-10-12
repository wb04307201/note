#!/usr/bin/env bash
# regression-test.sh — 回归测试（候选 4 · grep 路径断言）
#
# 跑最近 N 个 feat/fix commit 的主题 .md，验证:
#   1. 文件路径是否仍存在
#   2. broken links 自检通过
#
# 触发:
#   bash scripts/regression-test.sh [N=5]
#   GitHub Actions workflow_dispatch 手动调用
#
# 退出码:
#   0 全部通过
#   1 有失效 (路径丢失 / broken link)

set -e

N=${1:-5}
# 优先用 $KB_DIR, 否则 git top-level, 否则 CWD
if [ -n "$KB_DIR" ]; then
  : # use as-is
elif KB_DIR_GIT=$(git rev-parse --show-toplevel 2>/dev/null); then
  KB_DIR="$KB_DIR_GIT"
else
  KB_DIR="$(pwd)"
fi
cd "$KB_DIR"

# 非 git 仓库友好跳过
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "[regression-test] KB_DIR ($KB_DIR) 不是 git 仓库, 跳过 (该测试需 git log)"
  echo "  提示: regression-test.sh 仅对 git 仓库有效; 借 KB(非 git)请用 keyword-mapping-audit.py + frontmatter-batch-status.py"
  exit 0
fi

CHECK_SCRIPT=".github/workflows/scripts/check-broken-links.py"

echo "=========================================================="
echo "[regression-test] 跑最近 $N 个 feat/fix commit 验证"
echo "  KB_DIR = $KB_DIR"
echo "  N      = $N"
echo "=========================================================="
echo ""

PASS=0
FAIL=0
FAIL_FILES=()

# 收集最近 N 个 feat/fix commit 的主题
while IFS= read -r line; do
  hash="${line%%|*}"
  subject="${line#*|}"

  echo "─── [$hash] $subject ───"

  # 提取该 commit 修改的 .md（最多 10 个，避免太长）
  files=$(git show --name-only --format="" "$hash" 2>/dev/null | grep "\.md$" | grep -vE "^(\.claude|\.health-tmp)" | head -10)

  if [ -z "$files" ]; then
    echo "  (无 .md 变更)"
    PASS=$((PASS + 1))
    echo ""
    continue
  fi

  any_missing=false
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if [ -f "$f" ]; then
      echo "  [OK]      $f"
    else
      echo "  [MISSING] $f  ← 路径丢失"
      any_missing=true
      FAIL_FILES+=("$f")
    fi
  done <<< "$files"

  # broken links 自检（仅跑该 commit 修改的 .md 文件）
  if [ -f "$CHECK_SCRIPT" ]; then
    echo "  → 跑 broken links 自检..."
    if python "$CHECK_SCRIPT" --quiet $files > /tmp/regression-test-blink.log 2>&1; then
      echo "  [LINKS OK]"
    else
      echo "  [LINKS FAILED]"
      cat /tmp/regression-test-blink.log | sed 's/^/    /'
      any_missing=true
    fi
  fi

  if [ "$any_missing" = "true" ]; then
    FAIL=$((FAIL + 1))
  else
    PASS=$((PASS + 1))
  fi
  echo ""
done < <(git log -"$N" --grep="^feat\|^fix" --pretty=format:"%H|%s")

echo "=========================================================="
echo "[regression-test] 汇总"
echo "  通过: $PASS"
echo "  失败: $FAIL"
if [ "$FAIL" -gt 0 ]; then
  echo "  失败文件:"
  for f in "${FAIL_FILES[@]}"; do
    echo "    - $f"
  done
  exit 1
fi
echo "=========================================================="
echo "[regression-test] ✅ 全部通过"
