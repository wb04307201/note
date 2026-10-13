<!--question:
  id: 11.ai-token
  topic: 11.ai
  difficulty: ⭐⭐⭐
  frequency: 高频
  scenario_type: 反直觉代码
  tags: [11.ai, LLM, token]
  status: active
-->

# Token 与计费 — LLM 经济学面试深挖

> 一句话定位：Token 是 LLM 的最小处理单位，直接决定费用、速度和上下文窗口 —— 是所有 LLM 应用的底层经济学基础。完整概念见 [主模块 Token 与计费](../../../09.ai-applications/llm-inference/token-billing/README.md)。

---

## 引子：5 个 token 收 0.001 元，PM 怒了

```text
产品经理："我们就让 AI 写个会议纪要，为什么一次跑了 0.5 元？"
你："用户输入 8000 字上下文、会议录音转写 4000 字、再加上历史对话 5000 字……17000 字按 1 字 ≈ 1.5 token 算，就是 25500 token。"
PM："我们写个会议纪要才 800 字，输入怎么会是输出的 30 倍？"
你："因为输出的 token 比输入贵 2-3 倍。"
PM："……"
```

**真相**：LLM 不按字数收费，按 **Token** 收费。

- 1 个英文单词 ≈ 1-1.5 token
- **1 个中文字 ≈ 1-2 token（中文效率天生低于英文）**
- 输入便宜，输出贵（GPT-4 输入 $0.03/1k vs 输出 $0.06/1k）
- 图片、音频转 embedding 后**也按 token 算**

不懂 Token，AI 项目成本一定爆炸。

## 一、Token 是什么（一句话）

**Token ≠ 字符 ≠ 单词**：是分词算法（Tokenizer）处理后的最小单元。

```text
"Hello, world!" → ["Hello", ",", " world", "!"] → 4 token
"我爱中国"      → ["我", "爱", "中国"]          → 3 token
```

**✅ tiktoken 实测**（把"中文效率低于英文"从断言变实证）：

```python
import tiktoken

zh = "人工智能正在改变软件开发的方式"
en = "Artificial intelligence is changing the way software is developed"

for name in ["cl100k_base", "o200k_base"]:        # GPT-3.5/4 vs GPT-4o 两代词表
    enc = tiktoken.get_encoding(name)
    zh_tokens, en_tokens = enc.encode(zh), enc.encode(en)
    print(f"[{name}] 中文 {len(zh)} 字 → {len(zh_tokens)} token"
          f"（≈{len(zh_tokens)/len(zh):.1f} token/字）")
    print(f"[{name}] 英文 {len(en.split())} 词 → {len(en_tokens)} token"
          f"（≈{len(en_tokens)/len(en.split()):.1f} token/词）")
    print(f"[{name}] 同语义句中文/英文 token 比 ≈ {len(zh_tokens)/len(en_tokens):.1f}x")
# 典型输出：cl100k_base 下 1 中文字 ≈ 1-2 token，同语义句中文 token 数明显多于英文；
# o200k_base（GPT-4o）对中文词表做了扩充，比值收窄——结论随词表变化，务必用目标模型的
# encoding 实测，而不是背一个固定比例。
```

**关键比例**：
- 1 个英文单词 ≈ 1-1.5 个 token
- **1 个中文字 ≈ 1-2 个 token（中文效率低于英文）**
- 标点、空格、数字也占 token

---

## 二、面试陷阱

### 陷阱 1：以为 1 字 = 1 token
- **真相**：中文 1 字 ≈ 1-2 token；英文 1 词 ≈ 1-1.5 token；代码比自然语言更占 token。

### 陷阱 2：以为上下文窗口越大越好
- **真相**：上下文窗口越大，**注意力 O(n²) 复杂度**导致推理变慢 + 成本飙升；Lost in the Middle 现象让中间信息被忽略。

### 陷阱 3：以为输出 token 不重要
- **真相**：输出 token 通常**比输入贵 2-3 倍**（GPT-4 输入 $0.03/1k vs 输出 $0.06/1k）；模型倾向于"凑长度"，必须明确长度要求。

### 陷阱 4：不考虑图片/音频的 token 消耗
- **真相**：图片、音频嵌入后**也变成 token**，一张 1024×1024 图 ≈ 1024 个 token（按 patch 算），不可忽视。

### 陷阱 5：忽视 Prompt Cache
- **真相**：Anthropic / OpenAI 提供 Prompt Cache（相同前缀复用），cache 命中部分价格降 80%+。

---

## 三、3 大分词算法

| 算法 | 原理 | 使用者 |
|------|------|--------|
| **BPE** | 合并最频繁字符对 | GPT / LLaMA / Claude |
| **WordPiece** | 用似然度合并 | BERT / DistilBERT |
| **SentencePiece** | 无语言依赖、Unicode 上操作 | T5 / 多语言模型 |

---

## 四、Token 优化 3 大手段

> 以下量化实例均为**示例口径**（假设单价 + 构造场景），用于说明数量级，落地时以自家账单实测为准。

1. **输入端**：RAG 只检索相关片段、压缩对话历史、删减无关内容
   - 量化实例（示例口径）：客服 bot 每轮把全部 20 轮历史塞 Prompt ≈ 12k input token；改成"最近 3 轮原文 + 更早历史摘要" ≈ 3.5k token——按 $0.03/1k 计，单次输入费 $0.36 → $0.105，**降 ~70%**，且长对话不再触发窗口截断。
2. **输出端**：明确长度要求（"用一句话"比"用 300 字"省 token）
   - 量化实例（示例口径）：分类任务不加约束时模型爱输出解释，平均 120 output token；Prompt 加"只输出标签，不要解释"+ Structured Output 后平均 3 token——输出费（$0.06/1k）单次 $0.0072 → $0.00018，**降 97%**，日 10 万次调用一年省 ~$25 万。
3. **缓存**：Prompt Cache（Anthropic / OpenAI）+ KV Cache（模型内部）
   - 量化实例（示例口径）：批量文档处理，system prompt + few-shot 前缀 20k token 固定，每天 1 万次调用。无缓存输入费 20k × $0.03/1k × 10000 = $6000/天；Anthropic Prompt Cache 命中部分按 10% 计价，命中后 ≈ $600/天 + 少量写入费（1.25×），**降 ~80-90%**——这就是"前缀不动的批量场景优先上缓存"的原因。

---

## 五、反直觉点

- **生成是串行的**：自回归模型每生成 1 个 token 都要一次完整前向传播，速度 ~50-100 token/秒。
- **中文比英文"贵"**：同样语义内容，中文 token 数约是英文的 1.5-2 倍。
- **代码更占 token**：缩进、标点、关键词让代码 token 密度比自然语言高。

---

## 六、上下文窗口速查

| 模型 | 窗口 | 约等于 |
|------|------|--------|
| GPT-3.5 | 4K | ~3000 字中文 |
| GPT-4 | 8K / 32K / 128K | ~6k / 24k / 100k 字 |
| Claude 3.5 | 200K | ~150k 字 |
| Claude 4 | 1M | ~750k 字 |
| Gemini 1.5 Pro | 1M-2M | 极大 |

---

## 七、面试话术

**30 秒简版**：

> "Token 是 LLM 的最小处理单位，由分词算法生成——中文 1 字 ≈ 1-2 token，英文 1 词 ≈ 1-1.5 token。它决定三件事：**上下文窗口**、**计费**（输出比输入贵 2-3 倍）、**生成速度**（自回归串行，~50-100 token/秒）。省钱三板斧：RAG 只塞相关片段、输出端限长度、Prompt Cache 复用前缀。"

**90 秒完整版**：

> "Token 是 LLM 的最小处理单位，由分词算法（Tokenizer）生成。
>
> **分词算法原理**：主流是 **BPE**（GPT/LLaMA/Claude 用，从字符开始反复合并语料中最高频的相邻对，直到达到词表大小——所以常见词是 1 个 token，生僻词被拆成子词）；**WordPiece**（BERT 用，不按频次而按'合并后语言模型似然提升最大'来选对）；**SentencePiece**（T5/多语言模型用，直接在 Unicode 流上训练，不依赖预分词，空格也用符号表示）。用 `tiktoken` 库可以精确计算 token 数。
>
> **两层缓存机制**：**Prompt Cache** 是 API 层的商业缓存——相同前缀（system prompt、few-shot 示例）命中后，Anthropic/OpenAI 对命中部分降价 80%+，多轮对话和批量处理收益最大；**KV Cache** 是推理引擎内部的机制——自回归生成时把已算过的 Key/Value 矩阵缓存下来，避免每生成 1 个 token 重算整个前缀，代价是显存占用随 上下文长度 × 层数 × 头维度 线性增长（长上下文的显存瓶颈就在这）。
>
> **成本计算实例**：一次会议纪要请求，输入 17000 中文字 ≈ 25500 token（×1.5），输出 800 字 ≈ 1200 token。按 GPT-4 定价：输入 25.5k × $0.03/1k ≈ $0.77，输出 1.2k × $0.06/1k ≈ $0.07——单次约 $0.84。若前缀 20k token 命中 Prompt Cache（-80%），输入成本降到 ~$0.15，总成本降 3 倍以上。这就是为什么'输入是输出的 30 倍'却仍然费用可观——优化重点在输入端裁剪 + 缓存。
>
> **优化技巧**：输入端 RAG 检索关键片段、压缩对话历史；输出端明确长度要求；缓存用 Prompt Cache（API 层）+ KV Cache（推理层，选支持 PagedAttention 的引擎提高显存利用率）。"

---

## 八、深度阅读

- 主模块：[Token 与计费](../../../09.ai-applications/llm-inference/token-billing/README.md)
- 上游：[Transformer 架构](../../../08.ai-foundations/03-transformer/README.md)
- 关联：[Context Engineering](../context-engineering-interview/README.md) — Context Window 是 Token 上限
- 关联：[RAG](../rag/README.md) — 用 RAG 减少 Token 消耗

- Token 经济学：[`AI 编程 Token 经济学`](../ai-coding-token-economics/README.md) — 9.6 万 Token 中位数 + 杠杆率 + Token 悖论

---

> 📅 2026-06-30 · 咬文嚼字 · AI 经济学基础 · ⭐⭐⭐

← [返回: 咬文嚼字 · token](../README.md)
