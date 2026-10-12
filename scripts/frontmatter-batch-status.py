#!/usr/bin/env python3
"""
frontmatter-batch-status.py — 批量给 .md 加 status: active 字段（候选 5）

策略：
- 找所有 .md（排除 .claude/skills · .health-tmp · .git · 已含 status 文件）
- 解析 HTML-comment frontmatter (<!-- module: ... --> / question: / story:)
- 已有 status: 字段 → skip
- 无 frontmatter 或 frontmatter 不含 status: → 在 frontmatter 末行加 `  status: active`
- 写回文件（保持 frontmatter 格式）

用法：
  python scripts/frontmatter-batch-status.py            # dry-run（默认）
  python scripts/frontmatter-batch-status.py --apply  # 实际写入

退出码：
  0 成功 / 1 报错
"""
import os
import sys
import re
import glob
import argparse

KB_DIR = os.environ.get('KB_DIR', '.')

# HTML-comment 风格 frontmatter
FRONTMATTER_RE = re.compile(r'<!--\s*(module|question|story)\s*:(.*?)-->', re.DOTALL)
STATUS_FIELD_RE = re.compile(r'^\s*status\s*:', re.MULTILINE)

# 排除目录
EXCLUDE_DIRS = ['.claude', '.health-tmp', '.git', 'scripts']


def find_md_files(root: str):
    """递归找所有 .md 文件，排除 EXCLUDE_DIRS"""
    matches = []
    for path in glob.glob(os.path.join(root, '**', '*.md'), recursive=True):
        rel = os.path.relpath(path, root)
        # 排除第一层就是 EXCLUDE_DIRS 的文件
        first = rel.split(os.sep)[0]
        if first in EXCLUDE_DIRS:
            continue
        matches.append(path)
    return matches


def needs_status(content: str) -> tuple[bool, bool]:
    """
    判断文件是否需要加 status: 字段
    返回 (需要加, 已有 frontmatter)
    """
    m = FRONTMATTER_RE.search(content)
    if not m:
        return False, False  # 无 frontmatter，不动
    block = m.group(2)
    if STATUS_FIELD_RE.search(block):
        return False, True  # 已有 status:，skip
    return True, True  # 有 frontmatter 且无 status


def add_status(content: str, value: str = 'active') -> str:
    """在 frontmatter 最后一行加 `  status: <value>`"""
    m = FRONTMATTER_RE.search(content)
    if not m:
        return content
    block = m.group(2)
    new_block = block.rstrip() + f'\n  status: {value}\n'
    new_full = f'<!--{m.group(1)}:{new_block}-->'
    return content.replace(m.group(0), new_full, 1)


def process_file(path: str, apply: bool) -> tuple[str, str]:
    """处理单个文件，返回 (状态, 原因)"""
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        return 'ERROR', f'读取失败: {e}'

    need, has_fm = needs_status(content)
    if not has_fm:
        return 'SKIP', '无 frontmatter'
    if not need:
        return 'SKIP', '已有 status: 字段'

    if apply:
        new_content = add_status(content)
        if new_content == content:
            return 'ERROR', '加 status 失败（内容未变）'
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return 'CHANGED', '已加 status: active'

    return 'WOULD-CHANGE', '会加 status: active'


def main():
    p = argparse.ArgumentParser(description='frontmatter 批量加 status: active')
    p.add_argument('--apply', action='store_true', help='实际写入（默认 dry-run）')
    p.add_argument('--root', default=KB_DIR, help='KB 根目录')
    args = p.parse_args()

    files = find_md_files(args.root)
    if not files:
        print('未找到 .md 文件')
        return 1

    # 统计
    counters = {'CHANGED': 0, 'WOULD-CHANGE': 0, 'SKIP': 0, 'ERROR': 0}
    errors = []

    for f in files:
        status, reason = process_file(f, args.apply)
        counters[status] = counters.get(status, 0) + 1
        if status == 'ERROR':
            errors.append((f, reason))
        elif status in ('CHANGED', 'WOULD-CHANGE'):
            print(f'  [{status}] {os.path.relpath(f, args.root)}')

    mode = '实际写入' if args.apply else 'dry-run'
    print('')
    print(f'=== {mode} 汇总 ===')
    print(f'  CHANGED       : {counters["CHANGED"]}')
    print(f'  WOULD-CHANGE  : {counters["WOULD-CHANGE"]}')
    print(f'  SKIP          : {counters["SKIP"]}（含无 frontmatter）')
    print(f'  ERROR         : {counters["ERROR"]}')

    if errors:
        print('\n错误:')
        for f, reason in errors:
            print(f'  {f}: {reason}')
        return 1

    if not args.apply:
        print('\n[NOTE] 当前为 dry-run，要实际写入请加 --apply')

    return 0


if __name__ == '__main__':
    sys.exit(main())
