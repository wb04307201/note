#!/usr/bin/env python3
"""
weak-link-scan.py — 弱关联扫描(外置自 note-health Phase 1.13 · v4 · 2026-10-23)

判定语义:**弱关联 = 源文链接到目标文件, 但源文自身从未提及目标的主题**。

降噪(四步):
  ① 切掉代码块
  ② 排除表格行(导航表)
  ③ 页脚截断(返回 / 相关章节 / 交叉引用 / 系列导航 / 反向链 / 延伸阅读 ...)
  ④ 排除祖先回链(仅当目标是源的**严格祖先目录**时跳过; 同目录兄弟必须参与匹配)

关键词匹配(v4 修正, 对齐 "根 README §1 实质弱关联" 口径):
  - 关键词池 = 目标 H1 + H2 + frontmatter(title/summary) + 文件名 slug 词元
  - 正文比对时把链接标记 `[anchor](url)` 还原为 `anchor`:
      保留作者对目标的**显式指称**, 去掉 URL 路径的自我满足
  - anchor 若是描述性文本(非纯路径) → 视为显式指称, 直接判强关联
  - 中文: 整词 / 通用后缀剥离后的核心词 / >=3 字前缀 / 正文含关键词 >=3 字连续片段(反向)
  - 英文: 大小写不敏感整词; 2 字母全大写缩写(AI/OS/DB)保留
  - 读目标文件全文(原只读前 2000 字符, 长文 H2 会漏)

输出三分类: 实质弱关联(leaf<->leaf) / 合规模板导航(README<->README) / 混合

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

# 纯中文的关键词
CN_RE = re.compile(r'^[一-鿿]+$')

# 模板/通用标题词 —— 无语义, 不参与匹配(否则"一句话定位""为什么"等会造成假强关联)
TEMPLATE_WORDS = {
    '一句话定位', '核心原理', '代码示例', '常见陷阱', '最佳实践', '面试话术',
    '相关章节', '交叉引用', '反向链', '外部参考', '思考', '总结', '概述',
    '简介', '是什么', '为什么', '怎么选', '如何选', '核心概念', '速查',
    '适用场景', '注意事项', '常见误区', '实战案例', '案例', '前言', '背景',
    '章节', '目录', '正文', '内容', '说明', '定义', '特点', '价值',
    '引言', '绪论', '结语', '小结', '开篇', '写在前面', '本章', '全文',
    # 结构性/导航性标题 —— 出现在大量文件的目录骨架里, 参与匹配会造成假强关联
    '引子', '详解', '模块导航', '阅读路径', '关联主题', '主题清单', '知识脉络',
    '速查要点', '选型建议', '常见面试题', '本节统计', '与其他模块的关系',
    '与其他模块的缺口', '尚未迁移的', '已知', '索引', '大纲', '概览', '综述',
}

# 通用技术修饰词 —— 从中文关键词剥离以得到"核心词"(如 异常处理注解 -> 异常)
GENERIC_MODS = (
    '注解', '模式', '原理', '设计', '实战', '详解', '入门', '基础', '笔记',
    '系列', '实践', '源码', '机制', '架构', '实现', '对比', '速查', '进阶',
    '方案', '类型', '规范', '流程', '指标', '优化', '技术', '系统', '服务',
    '组件', '框架', '引擎', '平台', '工具', '管理', '开发', '使用', '配置',
    '参数', '方法', '步骤', '案例', '问题', '陷阱', '最佳', '常见', '处理',
    '治理', '评估', '规划', '演进', '生命周期', '核心', '详解', '指南',
)

# 页脚/导航类章节标题关键词 —— 这些标题之后是"模板导航", 不参与弱关联判定
FOOTER_KW = (
    '相关章节', '交叉引用', '系列导航', '反向链', '相关链接',
    '延伸阅读', '继续阅读', '下一章',
)

# 空泛的链接显示文本 —— 不算对目标主题的显式指称
GENERIC_ANCHORS = {
    '目标', '详情', '更多', '这里', '点击', '查看', '文档', '文章', '文件',
    '链接', '参考', '如下', '展开', '点击这里', '阅读更多', '更多内容',
    '上一篇', '下一篇', '本页', '正文', '来源', '出处', '附上', '见下',
}


def is_footer_heading(line: str) -> bool:
    """判断是否页脚/导航章节标题(容忍编号前缀、emoji、括号后缀)

    例: `## 六、交叉引用` / `## 📂 相关章节` / `## 延伸阅读（2026 新增）`
        / `## 系列导航表（12.interview · 11.ai 兄弟）` / `## 跨模块反向链`
    """
    m = re.match(r'^#{1,4}\s*(.+)$', line.strip())
    if not m:
        return False
    t = m.group(1)
    t = re.sub(r'^[^\w一-鿿]+', '', t)          # 去 emoji / 装饰符号
    t = re.sub(r'^第?[一二三四五六七八九十\d]+[、.．]?\s*', '', t)  # 去章节编号
    return any(k in t for k in FOOTER_KW)


def clean_content(content: str) -> str:
    """①②③ 降噪(保留链接标记, 供提链用): 去代码块 / 去表格行 / 截断页脚导航段"""
    content = re.sub(r'```.*?```', '', content, flags=re.S)
    lines = content.split('\n')
    cut = len(lines)
    for i, l in enumerate(lines):
        if is_footer_heading(l):
            cut = i
            break
    lines = lines[:cut]
    return '\n'.join(l for l in lines if not l.strip().startswith('|'))


def body_only(content: str) -> str:
    """正文比对用: 降噪后把链接标记还原成显示文本(保留作者指称, 去掉 URL 自我满足)"""
    return LINK_RE.sub(lambda m: m.group(1) or '', clean_content(content))


def frontmatter_fields(text: str) -> dict:
    """解析 HTML 注释式 frontmatter 的 title / summary 字段"""
    out = {}
    m = re.search(r'<!--(module|question|story):(.*?)-->', text, flags=re.S)
    if not m:
        return out
    for key in ('title', 'summary'):
        fm = re.search(rf'^\s*{key}:\s*(.+?)\s*$', m.group(2), flags=re.M)
        if fm:
            out[key] = fm.group(1).strip().strip('"')
    return out


def headings_of(text: str):
    """取真 H1 + 所有 H2(跳过 frontmatter 与代码块内的 # 号)"""
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    out = []
    for line in text.split('\n'):
        s = line.strip()
        if s.startswith('<!--'):
            continue
        m = re.match(r'^(#{1,2})\s+(.+)$', s)
        if m:
            out.append(m.group(2).strip())
    return out


def keywords_of(title: str):
    """标题 -> 关键词列表(中文连续段 + 英文词, 去模板词)

    中文段 >= 2 字: 2 字词(如"熔断""单例")在正文里以**独立词**形式出现时才计命中,
    见 cn_short_hit(); >= 3 字词走整词/核心词/前缀/反向片段四级匹配。
    """
    if not title:
        return []
    segs = re.findall(r'[一-鿿]{2,}|'          # 中文连续段(>=2 字)
                      r'[A-Za-z][A-Za-z0-9\-+]{2,}|'  # 英文词(>=3 字符)
                      r'[A-Z]{2}(?![A-Za-z])',          # 2 字母全大写缩写 AI/OS/DB
                      title)
    return [s for s in segs if s not in TEMPLATE_WORDS]


def stem_keywords(t_abs: str):
    """目标 slug -> 英文词元

    leaf 文件取文件名(44-tech-debt-career-trap -> tech/debt/career/trap);
    README 文件取所在目录名(access-control/README.md -> access/control)。
    """
    base = os.path.basename(t_abs)
    if base.lower() == 'readme.md':
        stem = os.path.basename(os.path.dirname(t_abs))
    else:
        stem = os.path.splitext(base)[0]
    parts = re.split(r'[-_0-9]+', stem)
    return [p.lower() for p in parts if len(p) >= 3 and p.isalpha()]


def core_variants(kw: str):
    """中文关键词 -> 核心词(剥离通用技术修饰词)"""
    core = kw
    changed = True
    while changed:
        changed = False
        for mod in GENERIC_MODS:
            if len(core) > len(mod) and core.endswith(mod):
                core = core[:-len(mod)]
                changed = True
    return [core] if 2 <= len(core) < len(kw) else []


def english_hit(kw: str, body: str) -> bool:
    """英文关键词命中: 大小写不敏感整词"""
    return re.search(r'(?<![A-Za-z0-9])' + re.escape(kw) + r'(?![A-Za-z0-9])',
                     body, flags=re.I) is not None


def cn_short_hit(kw: str, body: str) -> bool:
    """2 字中文词命中: 必须在正文中作为**独立词**出现(前后都不是汉字)

    避免 "系统架构" 里的 "系统" 被当成独立词而误判强关联。
    """
    for m in re.finditer(re.escape(kw), body):
        s, e = m.start(), m.end()
        before = body[s - 1] if s > 0 else ' '
        after = body[e] if e < len(body) else ' '
        if not re.match(r'[一-鿿]', before) and not re.match(r'[一-鿿]', after):
            return True
    return False


def chinese_hit(kw: str, body: str) -> bool:
    """中文关键词命中: 整词 / 核心词 / 头词 / >=3 字前缀 / 正文含 >=3 字连续片段"""
    if len(kw) == 2:
        return cn_short_hit(kw, body)
    if kw in body:
        return True
    for core in core_variants(kw):
        if len(core) >= 3:
            if core in body:
                return True
        elif cn_short_hit(core, body):
            return True
    # 头词: 长关键词的前 2 字(如 "熔断降级机制…" -> "熔断"), 需独立出现
    if len(kw) >= 4 and cn_short_hit(kw[:2], body):
        return True
    for n in range(len(kw), 2, -1):          # 前缀 >= 3 字
        if kw[:n] in body:
            return True
    for n in range(3, len(kw) + 1):          # 反向: 关键词的 >=3 字连续片段
        for i in range(len(kw) - n + 1):
            if kw[i:i + n] in body:
                return True
    return False


def keyword_hit(kw: str, body: str) -> bool:
    if not CN_RE.match(kw):
        return english_hit(kw, body)
    return chinese_hit(kw, body)


def anchor_is_descriptive(anchor: str) -> bool:
    """链接显示文本是否点名了目标主题(而非纯路径/文件名/空泛词)

    判定门槛: 中文 >= 3 字连续段 或 英文 >= 3 字符词, 且不在通用词黑名单。
    """
    return bool(anchor_terms(anchor))


def anchor_terms(anchor: str):
    """链接显示文本 -> 术语列表(去路径片段后的中文段 + 英文词)"""
    if not anchor:
        return []
    a = re.sub(r'[`*_\[\]]', '', anchor).strip()
    a = re.sub(r'(?m)[\w\-]+/[\w\-./]*', ' ', a)      # 去路径片段
    a = re.sub(r'[\w\-]{3,}\.(md|markdown)\b', ' ', a, flags=re.I)
    cn = [c for c in re.findall(r'[一-鿿]{3,}', a) if c not in GENERIC_ANCHORS]
    en = [c for c in re.findall(r'[A-Za-z][A-Za-z0-9\-+]{2,}', a)
          if c.lower() not in GENERIC_ANCHORS]
    return cn + en


def is_subsequence(short: str, long_: str) -> bool:
    """short 是否为 long_ 的子序列(容忍中间插入, 如 "谁负责" ⊆ "谁替系统负责")"""
    it = iter(long_)
    return all(ch in it for ch in short)


def anchor_related(anchor: str, pool) -> bool:
    """anchor 的术语是否与目标主题池相关(含/被包含/子序列)"""
    terms = anchor_terms(anchor)
    if not terms:
        return False
    cn_pool = [k for k in pool if CN_RE.match(k)]
    en_pool = [k for k in pool if not CN_RE.match(k)]
    for term in terms:
        if CN_RE.match(term):
            for kw in cn_pool:
                if term in kw or kw in term or is_subsequence(term, kw):
                    return True
        else:
            t = term.lower()
            for kw in en_pool:
                k = kw.lower()
                if t == k or k in t or is_subsequence(k, t):
                    return True
    # 目标主题池没有可比对的中文术语时, 视为相关(无法证伪)
    return not cn_pool and not en_pool


def target_pool(t_abs: str):
    """目标文件 -> 关键词池(H1/H2 + frontmatter + 文件名词元)"""
    try:
        tc = open(t_abs, encoding='utf-8', errors='ignore').read()
    except Exception:
        return []
    pool = []
    for title in headings_of(tc):
        pool += keywords_of(title)
    fm = frontmatter_fields(tc)
    for key in ('title', 'summary'):
        if fm.get(key):
            pool += keywords_of(fm[key])
    pool += stem_keywords(t_abs)
    seen, out = set(), []
    for k in pool:
        if k not in seen:
            seen.add(k)
            out.append(k)
    return out


def scan(target_dir: str, exclude_dirs: list, output: str = None) -> int:
    """扫描 target_dir 下所有 .md,返回弱关联数"""
    weak = 0
    cats = {'substantive': 0, 'template': 0, 'mixed': 0}
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
        clean = clean_content(content)
        f_dir = os.path.dirname(os.path.abspath(f))
        seen_targets = set()

        for m in LINK_RE.finditer(clean):
            anchor, rel_target = m.group(1), m.group(2)
            if re.match(r'^\s*返回', anchor or ''):
                continue  # "← 返回: xxx" 导航链接, 不参与判定
            key = os.path.normpath(rel_target)
            if key in seen_targets:
                continue  # 同一目标在源文多次出现, 只判一次
            seen_targets.add(key)
            try:
                t_abs = os.path.normpath(os.path.join(os.path.dirname(f), rel_target))
            except Exception:
                continue
            if not os.path.isfile(t_abs):
                continue  # broken 由 check-broken-links.py 处理
            t_dir = os.path.dirname(os.path.abspath(t_abs))
            try:
                # ④ 祖先回链排除 —— 仅当目标是源的**严格祖先目录**时跳过。
                #    同目录(t_dir == f_dir)是兄弟关系, 必须参与匹配, 否则整目录互链被漏检。
                if t_dir != f_dir and os.path.commonpath([t_dir, f_dir]) == t_dir:
                    continue
            except ValueError:
                pass

            pool = target_pool(t_abs)
            if not pool:
                continue

            f_readme = os.path.basename(f) == 'README.md'
            t_readme = os.path.basename(t_abs) == 'README.md'
            is_substantive = (not f_readme) and (not t_readme)

            # Tier 1 —— 正文与目标主题共享实质术语
            hit = any(keyword_hit(k, body) for k in pool[:40])
            # Tier 2 —— 显式指称: anchor 是描述性文本
            if not hit and anchor_is_descriptive(anchor):
                if is_substantive:
                    # leaf↔leaf: anchor 必须与目标主题相关, 否则是"挂错主题"的真问题
                    hit = anchor_related(anchor, pool)
                else:
                    # README 索引/目录类: 用别名指向章节属合规导航
                    hit = True
            if hit:
                continue

            weak += 1
            if f_readme and t_readme:
                cat = 'template'      # README↔README 合规模板导航
            elif is_substantive:
                cat = 'substantive'   # leaf↔leaf 实质弱关联
            else:
                cat = 'mixed'
            cats[cat] += 1
            line = f"  ⚠ 弱关联: {f} -> {rel_target}"
            print(line)
            if out:
                out.write(line + '\n')

    summary = f"弱关联(正文内链口径): {weak} 处"
    detail = (f"  ├─ 实质弱关联(leaf↔leaf): {cats['substantive']}"
              f"  ├─ 合规模板导航(README↔README): {cats['template']}"
              f"  └─ 混合(README↔leaf 等): {cats['mixed']}")
    print(summary)
    print(detail)
    if out:
        out.write(f"\n{summary}\n{detail}\n")
        out.close()
    return weak


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='弱关联扫描(外置自 note-health Phase 1.13)')
    p.add_argument('--dir', default=KB_DIR, help='扫描根目录(默认 KB_DIR 或 NOTE_DIR)')
    p.add_argument('--ext', default='.md', help='文件扩展名(默认 .md)')
    p.add_argument('--exclude-dir', nargs='+',
                   default=['.health-tmp', '.git', 'scripts', '.claude', 'skills'],
                   help='排除目录列表')
    p.add_argument('--output', default=None, help='报告输出路径(可选)')
    args = p.parse_args()

    weak_count = scan(args.dir, args.exclude_dir, args.output)
    sys.exit(0 if weak_count == 0 else 1)
