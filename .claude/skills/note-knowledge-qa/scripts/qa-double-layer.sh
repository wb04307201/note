#!/usr/bin/env bash
# qa-double-layer.sh — note 知识库双层检索(外置自 note-knowledge-qa §3.3)
#
# 用法:
#   bash scripts/qa-double-layer.sh "RAG"                       # 全库
#   bash scripts/qa-double-layer.sh "RAG" 09.ai-applications    # 指定模块
#
# 4 段输出: 主模块 / 12.interview / 13.story / 11.product-and-pm
# 退出码: 0=命中 / 1=无命中 / 2=参数错误
#
# 风格基线: scripts/sync-skills.sh(2026-09-23 外置)

set -euo pipefail
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; CYAN='\033[0;36m'; NC='\033[0m'

KEYWORD="${1:?需要 1 个参数:关键词}"
MODULE="${2:-}"

export KB_DIR="${NOTE_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || echo '.')}"

if [ ! -d "$KB_DIR" ]; then
  echo -e "${RED}错误: KB_DIR=$KB_DIR 不存在${NC}"
  exit 2
fi

SCOPE="$KB_DIR"
if [ -n "$MODULE" ]; then
  SCOPE="$KB_DIR/$MODULE"
  [ -d "$SCOPE" ] || { echo -e "${RED}错误: 模块 $MODULE 不在 $KB_DIR 下${NC}"; exit 2; }
fi

# === 主模块命中(按命中数倒序,最多 10 个)===
echo -e "${CYAN}═══ 主模块命中(按命中数倒序,最多 10 个)═══${NC}"
HITS=$(grep -rl "$KEYWORD" "$SCOPE/" --include="*.md" 2>/dev/null \
  | grep -v "/12.interview/" \
  | xargs -I {} sh -c 'count=$(grep -c "$0" "{}" 2>/dev/null); echo "$count {}"' "$KEYWORD" 2>/dev/null \
  | sort -rn | head -10)
if [ -z "$HITS" ]; then
  echo -e "  ${YELLOW}无命中${NC}"
else
  echo "$HITS" | awk '{print "  " $1 " 处命中  →  " $2}'
fi

# === 12.interview 命中(被面试者视角,最多 5 个)===
echo ""
echo -e "${CYAN}═══ 12.interview 命中(面试陷阱版,最多 5 个)═══${NC}"
if [ -d "$KB_DIR/12.interview" ]; then
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/12.interview/" 2>/dev/null \
    | xargs -I {} sh -c 'count=$(grep -c "$0" "{}" 2>/dev/null); echo "$count {}"' "$KEYWORD" 2>/dev/null \
    | sort -rn | head -5)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  " $1 " 处命中  →  " $2}'
  fi
fi

# === 13.story 命中(叙事类比版,最多 3 个)===
echo ""
echo -e "${CYAN}═══ 13.story 命中(阿明餐厅版,最多 3 个)═══${NC}"
if [ -d "$KB_DIR/13.story" ]; then
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/13.story/" 2>/dev/null | head -3)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  →  " $1}'
  fi
fi

# === 11.product-and-pm 命中(仅面试方法论问题,最多 3 个)===
echo ""
echo -e "${CYAN}═══ 11.product-and-pm 命中(面试官视角,最多 3 个)═══${NC}"
if [ -d "$KB_DIR/11.product-and-pm" ]; then
  HITS=$(grep -rl "$KEYWORD" "$KB_DIR/11.product-and-pm/" 2>/dev/null | head -3)
  if [ -z "$HITS" ]; then
    echo -e "  ${YELLOW}无命中${NC}"
  else
    echo "$HITS" | awk '{print "  →  " $1}'
  fi
fi

echo ""
echo -e "${GREEN}═══ 建议阅读顺序: 主模块 → 12.interview → 13.story(叙事辅助)═══${NC}"

TOTAL=$(grep -rl "$KEYWORD" "$SCOPE/" --include="*.md" 2>/dev/null | wc -l)
[ "$TOTAL" -gt 0 ] && exit 0 || exit 1
