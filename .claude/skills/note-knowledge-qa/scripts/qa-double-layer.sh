#!/usr/bin/env bash
# qa-double-layer.sh — note 知识库双层检索(外置自 note-knowledge-qa §3.3)
#
# 用法:
#   bash scripts/qa-double-layer.sh "RAG"                       # 全库
#   bash scripts/qa-double-layer.sh "RAG" 09.ai-applications    # 指定模块
#
# 输出段: 主模块 / 面试版 / 叙事版 / 面试方法论(如该 KB 存在) / 建议阅读顺序
#   面试版与叙事版的栏目名运行时解析自 $KB_DIR/SPEC.md §1.5 角色表(类型列
#   interview / story)——R2 Phase D 顺手项②: 段头不再 IT 硬编码;无对应角色模块
#   时整段跳过(不再打印空段头)。无 §1.5 的旧式 KB 回退探测 note 默认目录。
#   「面试方法论」段仍按 11.product-and-pm 目录存在性探测(note 式实例);角色词
#   表泛化(§1.5 增 methodology 类型或等价谓词)属 R3 backlog,本轮不过度设计。
# 退出码: 0=命中 / 1=无命中 / 2=参数错误
#
# 健壮性修正(同顺手项②批次): 角色段零命中时 grep 在 pipefail 下曾使脚本中途
#   退出并丢失后续段输出(Phase C 旧版实证)——各命中管道尾部 `|| true` 兜底,
#   最终退出码统一由全库命中数决定。
#
# 风格基线: scripts/sync-skills.sh(2026-09-23 外置)

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'

KEYWORD="${1:?需要 1 个参数:关键词}"
MODULE="${2:-}"

export KB_DIR="${KB_DIR:-${NOTE_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo '.')}}"

# 非 git 仓库 + 未设 KB_DIR/NOTE_DIR → fallback 到 '.' (CWD),stderr 警告
if [ "$KB_DIR" = "." ] && [ -z "$KB_DIR_OVERRIDE" ] && [ -z "$NOTE_DIR" ]; then
  if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo -e "${YELLOW}警告: 不在 git 仓库,且未设 KB_DIR/NOTE_DIR,使用 CWD 作为 KB 根${NC}" >&2
    echo -e "${YELLOW}        如需指向其他 KB,请 export KB_DIR=/path/to/kb${NC}" >&2
  fi
fi

if [ ! -d "$KB_DIR" ]; then
  echo -e "${RED}错误: KB_DIR=$KB_DIR 不存在${NC}"
  exit 2
fi

SCOPE="$KB_DIR"
if [ -n "$MODULE" ]; then
  SCOPE="$KB_DIR/$MODULE"
  [ -d "$SCOPE" ] || { echo -e "${RED}错误: 模块 $MODULE 不在 $KB_DIR 下${NC}"; exit 2; }
fi

# === §1.5 角色模块运行时解析(顺手项②;落实 SKILL §3.3「模块列表从 §1 自动解析」既有口径) ===
# parse_role <类型>: 在 SPEC.md §1.5 区域内找「模块名 | 类型」行,输出候选模块目录名
parse_role() {
  [ -f "$KB_DIR/SPEC.md" ] || return 0
  awk -F'|' -v want="$1" '
    /^[ \t]*#+[ \t]*1\.5/ { in15 = 1; next }
    /^[ \t]*#+[ \t]*(1\.6|[2-9][0-9]*\.)/ { if (in15) exit }
    in15 && /^[ \t]*\|/ {
      m = $2; t = $3
      gsub(/[ \t*`]/, "", m); gsub(/[ \t*`]/, "", t)
      if (t == want && m ~ /^[0-9][0-9]*\./) print m
    }
  ' "$KB_DIR/SPEC.md"
}

HAS_ROLE_TABLE=0
if [ -f "$KB_DIR/SPEC.md" ] && grep -qE "^[ \t]*#+[ \t]*1\.5" "$KB_DIR/SPEC.md"; then
  HAS_ROLE_TABLE=1
fi

INTV_MODULE=""; STORY_MODULE=""
if [ "$HAS_ROLE_TABLE" -eq 1 ]; then
  # 有 §1.5 → 以角色表为准;候选目录不存在则忽略(容忍配置模板/过期行),首个在位者生效
  while IFS= read -r m; do
    if [ -n "$m" ] && [ -z "$INTV_MODULE" ] && [ -d "$KB_DIR/$m" ]; then INTV_MODULE="$m"; fi
  done < <(parse_role interview || true)
  while IFS= read -r m; do
    if [ -n "$m" ] && [ -z "$STORY_MODULE" ] && [ -d "$KB_DIR/$m" ]; then STORY_MODULE="$m"; fi
  done < <(parse_role story || true)
else
  # 无 §1.5 的旧式 KB → 回退探测 note 默认栏目名(行为兼容)
  [ -d "$KB_DIR/12.interview" ] && INTV_MODULE="12.interview" || INTV_MODULE=""
  [ -d "$KB_DIR/13.story" ] && STORY_MODULE="13.story" || STORY_MODULE=""
fi

# === 主模块命中(按命中数倒序,最多 10 个;排除面试版栏目——原 /12.interview/ 口径的泛化) ===
EXCLUDE_RE="__qa_double_layer_none__"
[ -n "$INTV_MODULE" ] && EXCLUDE_RE="/$INTV_MODULE/"
echo -e "${CYAN}═══ 主模块命中(按命中数倒序,最多 10 个)═══${NC}"
HITS=$(grep -rl "$KEYWORD" "$SCOPE/" --include="*.md" 2>/dev/null \
  | grep -Ev "$EXCLUDE_RE" 2>/dev/null \
  | xargs -I {} sh -c 'count=$(grep -c "$0" "{}" 2>/dev/null); echo "$count {}"' "$KEYWORD" 2>/dev/null \
  | sort -rn | head -10 || true)
if [ -z "$HITS" ]; then
  echo -e "  ${YELLOW}无命中${NC}"
else
  echo "$HITS" | awk '{print "  " $1 " 处命中  →  " $2}'
fi

# === 面试版命中(interview 角色栏目,§1.5 解析;无则整段跳过,最多 5 个) ===
if [ -n "$INTV_MODULE" ]; then
  echo ""
  echo -e "${CYAN}═══ ${INTV_MODULE} 命中(面试版,最多 5 个)═══${NC}"
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/$INTV_MODULE/" 2>/dev/null \
    | xargs -I {} sh -c 'count=$(grep -c "$0" "{}" 2>/dev/null); echo "$count {}"' "$KEYWORD" 2>/dev/null \
    | sort -rn | head -5 || true)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  " $1 " 处命中  →  " $2}'
  fi
fi

# === 叙事版命中(story 角色栏目,§1.5 解析;无则整段跳过,最多 3 个) ===
if [ -n "$STORY_MODULE" ]; then
  echo ""
  echo -e "${CYAN}═══ ${STORY_MODULE} 命中(叙事版,最多 3 个)═══${NC}"
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/$STORY_MODULE/" 2>/dev/null | head -3 || true)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  →  " $1}'
  fi
fi

# === 面试方法论命中(仅面试方法论问题,最多 3 个;note 式目录存在性探测,泛化属 R3 backlog) ===
if [ -d "$KB_DIR/11.product-and-pm" ]; then
  echo ""
  echo -e "${CYAN}═══ 11.product-and-pm 命中(面试官视角,最多 3 个)═══${NC}"
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/11.product-and-pm/" 2>/dev/null | head -3 || true)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  →  " $1}'
  fi
fi

echo ""
ORDER="主模块"
[ -n "$INTV_MODULE" ] && ORDER="$ORDER → ${INTV_MODULE}"
[ -n "$STORY_MODULE" ] && ORDER="$ORDER → ${STORY_MODULE}(叙事辅助)"
echo -e "${GREEN}═══ 建议阅读顺序: ${ORDER} ═══${NC}"

TOTAL=$(grep -rl "$KEYWORD" "$SCOPE/" --include="*.md" 2>/dev/null | wc -l || true)
[ "${TOTAL:-0}" -gt 0 ] && exit 0 || exit 1
