#!/usr/bin/env python3
"""
weak-link-scan.py — 弱关联扫描(外置自 note-health Phase 1.13 v2 · 2026-08-25 正文内链版)

四步降噪:
  ① 切掉代码块
  ② 排除表格行(导航表)
  ③ 页脚截断(← 返回 / 相关章节 / 交叉引用 / 系列导航 / 反向链 标题之后)
  ④ 排除祖先回链(返回父级 ../)

用法:
  python scripts/weak-link-scan.py                              # 全库扫描
  python scripts/weak-link-scan.py --dir 09.ai-applications    # 指定模块
  python scripts/weak-link-scan.py --ext .md --exclude-dir .health-tmp .git
  python scripts/weak-link-scan.py --output .health-tmp/weak.txt
"""
import os, re, glob, sys, argparse

# Windows UTF-8 输出兼容
if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except: pass

KB_DIR = os.environ.get('KB_DIR') or os.environ.get('NOTE_DIR') or os.getcwd()

LINK_RE = re.compile(
    r'(?<![|\[])\[([^\]]*)\]\((?!https?://)(?!mailto:)(?!#)([^)#\s]+?\.md)(?:#[^)]*)?\)'
)


def body_only(content: str) -> str:
    """①②③ 页脚/代码块/表格降噪"""
    content = re.sub(r'```.*?```', '', content, flags=re.S)
    lines = [l for l in content.split('\n') if not l.strip().startswith('|')]
    cut = len(lines)
    for i, l in enumerate(lines):
        if re.search(r'[←⬅]\s*\[?返回', l) or re.match(
            r'^#{1,3}\s*(🔗\s*)?(相关章节|交叉引用|系列导航|反向链|相关链接)\s*$', l
        ):
            cut = i
            break
    return '\n'.join(lines[:cut])


def scan(target_dir: str, exclude_dirs: list, output: str = None) -> int:
    """扫描 target_dir 下所有 .md,返回弱关联数"""
    weak = 0
    out = open(output, 'w', encoding='utf-8') if output else None
    if out:
        out.write(f"# 弱关联扫描报告 · {target_dir}\n\n")

    for f in glob.glob(os.path.join(target_dir, '**', '*.md'), recursive=True):
        rel_path = f.replace(os.sep, '/')
        if any(d in rel_path.split('/') for d in exclude_dirs):
            continue

        try:
            content = open(f, encoding='utf-8', errors='ignore').read()
        except Exception:
            continue

        body = body_only(content)
        f_dir = os.path.dirname(os.path.abspath(f))

        for m in LINK_RE.finditer(body):
            try:
                t_abs = os.path.normpath(os.path.join(os.path.dirname(f), m.group(2)))
            except Exception:
                continue
            if not os.path.isfile(t_abs):
                continue  # broken 由 check-broken-links.py 处理
            t_dir = os.path.dirname(os.path.abspath(t_abs))
            try:
                if os.path.commonpath([t_dir, f_dir]) == t_dir:
                    continue  # ④ 祖先回链
            except ValueError:
                pass

            try:
                tc = open(t_abs, encoding='utf-8', errors='ignore').read(2000)
            except Exception:
                continue
            h1 = re.search(r'^#\s+(.+)$', tc, re.M)
            kws = re.findall(
                r'[A-Za-z][A-Za-z0-9\-]{3,}|[一-鿿]{2,6}',
                (h1.group(1) if h1 else '')
            )
            if not kws:
                continue
            if all(k not in body for k in kws[:6]):  # 正文 0 提及
                weak += 1
                line = f"  ⚠ 弱关联: {f} -> {m.group(2)}"
                print(line)
                if out:
                    out.write(line + '\n')

    summary = f"弱关联(正文内链口径): {weak} 处"
    print(summary)
    if out:
        out.write(f"\n{summary}\n")
        out.close()
    return weak


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='弱关联扫描(外置自 note-health Phase 1.13 v2)')
    p.add_argument('--dir', default=KB_DIR, help='扫描根目录(默认 KB_DIR 或 NOTE_DIR)')
    p.add_argument('--ext', default='.md', help='文件扩展名(默认 .md)')
    p.add_argument('--exclude-dir', nargs='+',
                   default=['.health-tmp', '.git', 'scripts', '.claude', 'skills'],
                   help='排除目录列表')
    p.add_argument('--output', default=None, help='报告输出路径(可选)')
    args = p.parse_args()

    weak_count = scan(args.dir, args.exclude_dir, args.output)
    sys.exit(0 if weak_count == 0 else 1)
