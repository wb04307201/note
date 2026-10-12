#!/usr/bin/env python3
"""
keyword-mapping-audit.py — 双 bridge 体检脚本（候选 3 · Phase 1.17）

功能:
- 扫 KB 所有 frontmatter `tags:` 字段
- 扫 SPEC.md §8 词表
- 比对差异:
  - tags 中有但 §8 没有 → 新词未登记 (P3)
  - §8 中有但 tags 没有 → 词条未回流 (P2)
  - 完全一致 → PASS

用法:
  python scripts/keyword-mapping-audit.py            # 全 KB 自动检测
  python scripts/keyword-mapping-audit.py --spec SPEC.md    # 自定义 spec
  python scripts/keyword-mapping-audit.py --tags-dir .     # 自定义 tags 目录

退出码: 0 无 P2 警告 / 1 有 P2 警告(可选); 0 仅报告
"""
import os
import sys
import re
import glob
import argparse
import yaml

KB_DIR = os.environ.get('KB_DIR', '.')

# HTML-comment frontmatter
FRONTMATTER_RE = re.compile(r'<!--\s*(module|question|story)\s*:\s*(.*?)\s*-->', re.DOTALL)
# tags: 列表形式
TAGS_RE = re.compile(r'^\s*tags\s*:\s*(.+?)\s*$', re.MULTILINE)

EXCLUDE_DIRS = ['.claude', '.health-tmp', '.git', 'scripts']


def parse_frontmatter_yaml(block: str) -> dict:
    """Parse YAML inside HTML-comment block (tolerates indentation quirks)"""
    try:
        return yaml.safe_load(block) or {}
    except yaml.YAMLError:
        return {}


def find_md_files(root: str):
    matches = []
    for path in glob.glob(os.path.join(root, '**', '*.md'), recursive=True):
        rel = os.path.relpath(path, root)
        first = rel.split(os.sep)[0]
        if first in EXCLUDE_DIRS:
            continue
        matches.append(path)
    return matches


def collect_tags(root: str) -> dict:
    """收集 KB 内所有 .md 的 tags 字段（key=tag 字符串, val=[文件列表]）"""
    tags_map = {}
    for path in find_md_files(root):
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        m = FRONTMATTER_RE.search(content)
        if not m:
            continue
        data = parse_frontmatter_yaml(m.group(2))
        tags = data.get('tags', [])
        if isinstance(tags, str):
            tags = [t.strip() for t in re.split(r'[,;|]', tags) if t.strip()]
        elif not isinstance(tags, list):
            continue
        for tag in tags:
            tag = str(tag).strip()
            if tag:
                tags_map.setdefault(tag, []).append(path)
    return tags_map


def collect_spec_keywords(spec_path: str) -> set:
    """收集 SPEC.md §8 词条（解析 markdown 表格）"""
    if not os.path.isfile(spec_path):
        return set()
    with open(spec_path, encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # 找 §8 段
    m = re.search(r'^### 8\..*?(?=^### 9\.|\Z)', content, re.MULTILINE | re.DOTALL)
    if not m:
        return set()
    s8 = m.group()
    keywords = set()
    # 解析 markdown 表格行 (| word | path | ... | )
    for row_match in re.finditer(r'^\|\s*([^|]*?)\s*\|\s*([^|]+?)\s*\|', s8, re.MULTILINE):
        col1 = row_match.group(1).strip()
        # 跳过表头、空行、占位符
        if not col1 or col1 == '主题词' or col1.startswith('---') or col1.startswith('**LLM'):
            continue
        if col1.startswith('`') or col1.startswith('<'):
            continue
        keywords.add(col1)
    return keywords


def main():
    p = argparse.ArgumentParser(description='tags vs §8 双向 bridge 体检')
    p.add_argument('--spec', default=os.path.join(KB_DIR, 'SPEC.md'),
                   help='SPEC.md 路径（默认 $KB_DIR/SPEC.md）')
    p.add_argument('--root', default=KB_DIR, help='KB 根目录')
    args = p.parse_args()

    tags_map = collect_tags(args.root)
    spec_kw = collect_spec_keywords(args.spec)

    tags_set = set(tags_map.keys())

    # 差异分析
    new_in_tags = tags_set - spec_kw  # tags 中有但 §8 没有 (P3)
    new_in_spec = spec_kw - tags_set  # §8 中有但 tags 没有 (P2)
    matched = tags_set & spec_kw

    print('=== keyword_mapping_coverage（Phase 1.17）===')
    print(f'  KB root       : {args.root}')
    print(f'  SPEC.md       : {args.spec}')
    print(f'  tags 共        : {len(tags_set)} 个')
    print(f'  §8 词条共     : {len(spec_kw)} 个')
    print(f'  matched        : {len(matched)} 个')
    print(f'  新词未登记(P3) : {len(new_in_tags)} 个')
    print(f'  词条未回流(P2) : {len(new_in_spec)} 个')
    print('')

    if new_in_tags:
        print('### P3 新词未登记到 §8:')
        for tag in sorted(new_in_tags):
            files = tags_map[tag]
            print(f'  - {tag} (in {len(files)} file(s))')
            for f in files[:3]:
                print(f'      {os.path.relpath(f, args.root)}')
            if len(files) > 3:
                print(f'      ... and {len(files) - 3} more')
        print('')

    if new_in_spec:
        print('### P2 §8 词条未回流到 frontmatter tags:')
        for kw in sorted(new_in_spec):
            print(f'  - {kw}')
        print('')

    # 退出码: 有 P2 警告返回 1（可选）
    # 当前实现: 仅报告, 不阻断
    return 0


if __name__ == '__main__':
    sys.exit(main())
