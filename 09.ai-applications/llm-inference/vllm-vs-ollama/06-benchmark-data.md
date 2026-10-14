<!--module:
  parent: ai-platforms/vllm-vs-ollama
  slug: ai-platforms/vllm-vs-ollama/06-benchmark-data
  type: topic
  category: 性能基准
  summary: vLLM / Ollama / TGI / LMDeploy 在吞吐量 / 首 token 延迟 / 显存占用 3 个维度上的对比（量级估算，非严格实测）
  depth: ⭐⭐
  status: active
-->

# Benchmark 数据 · 4 引擎对比（量级估算）

> **一句话**：数据说话，但要看「**什么负载下**」——空载单卡 7B 时 4 个引擎差距不大，高并发多卡 70B 时 vLLM 领先 Ollama 可达**一个数量级**（本文表格为量级估算，见下方口径声明）。

← [返回: vLLM vs Ollama](../README.md)

---

## 测试条件与基准

> ⚠️ **全文数据口径声明**：本文所有表格为**基于公开资料的量级估算/示意**（综合 vLLM 论文的相对倍数与各引擎官方 benchmark 的趋势），**非同一环境下的严格实测**——本文未附完整可复现的硬件、软件版本与压测脚本说明。表中数字用于建立"什么负载下谁领先"的直觉，绝对数值请勿直接引用；生产选型请以下方官方 benchmark 页在目标硬件上复测为准。

### 1.1 硬件

| 设备 | 显存 | NVLink | 典型场景 |
|------|------|--------|---------|
| NVIDIA H100 80GB | 80 GB | ✅ NVLink 4 | 数据中心 |
| NVIDIA A100 80GB | 80 GB | ✅ NVLink 3 | 数据中心 |
| RTX 4090 24GB | 24 GB | ❌ PCIe 4 | 单机 / 工作站 |
| RTX 3090 24GB | 24 GB | ❌ PCIe 4 | 边缘 |

### 1.2 模型

| 模型 | 参数量 | 上下文 | 量化 |
|------|--------|--------|------|
| LLaMA-2-7B | 7B | 4096 | FP16 |
| Qwen2.5-72B | 72B | 32768 | AWQ-INT4 |
| Mixtral-8x7B | 47B (MoE) | 32768 | FP16 |

### 1.3 数据集

- **ShareGPT**：多轮对话（5k 请求，平均输出 200 token）
- **LongBench**：长上下文（128k，平均输出 50 token）
- **Random Pool**：模拟 RAG prefix sharing（20% 共享）

---

## 吞吐量（req/s，越大越好）
### 2.1 LLaMA-2-7B @ A10G / 4090

| 引擎 | 单并发 | 10 并发 | 100 并发 | 500 并发 |
|------|--------|---------|---------|---------|
| HuggingFace generate | 12 | 25 (OOM 高并发) | - | - |
| Ollama | 14 | 38 | 52 | 65 (极限) |
| TGI | 15 | 60 | 180 | 240 |
| **vLLM** | **16** | **85** | **320** | **510** |
| LMDeploy | 17 | 92 | 350 | 480 |

> 100 并发下 vLLM 是 Ollama 的 **6 倍**，500 并发是 **8 倍**。
>
> ⚠️ **口径说明**：表中 Ollama 的 100/500 并发数据为**短输入输出 + 小上下文**（类 LongBench：输出 ~50 token，KV cache 压力小）条件下的结果；一旦换成 ShareGPT 式长输出（平均 200 token）或大 ctx，Ollama 单进程在 100 并发即 OOM（见 §4.2）。

### 2.2 Qwen-72B @ 4×H100

| 引擎 | 单并发 | 32 并发 | 128 并发 |
|------|--------|---------|-----------|
| Ollama（朴素多卡）| 4 | 12 | 18 |
| TGI | 5 | 35 | 60 |
| **vLLM (TP=4)** | **6** | **88** | **190** |
| LMDeploy | 6 | 92 | 200 |

> 32 并发下 vLLM 是 Ollama 的 **7.3 倍**。

### 2.3 Mixtral-8x7B @ 2×H100

| 引擎 | 单并发 | 50 并发 |
|------|--------|---------|
| vLLM | 9 | 145 |
| TGI | 8 | 110 |
| LMDeploy | 9 | 150 |

> MoE 模型 vLLM 与 LMDeploy 接近，Ollama 不支持 MoE。

---

## 首 token 延迟（TTFT，越小越好）
### 3.1 测试场景

- prompt = 1024 token
- 并发 = 32
- 测量首 token 返回时间

### 3.2 结果

| 引擎 | P50 (ms) | P95 (ms) | P99 (ms) |
|------|----------|----------|----------|
| Ollama | 250 | 480 | 720 |
| TGI | 180 | 320 | 480 |
| **vLLM** | **80** | **150** | **240** |
| LMDeploy | 75 | 145 | 220 |

> vLLM 在 P99 上比 Ollama 快 **3 倍**，得益于连续批处理 + prefix sharing。

---

## 显存占用（GB）
### 4.1 LLaMA-2-7B 单并发（4090 24GB）

| 引擎 | 模型权重 | KV cache | 总占用 |
|------|---------|---------|---------|
| HuggingFace | 13 GB | 1.3 GB | 14.3 GB |
| Ollama (Q4_K_M) | 4 GB | 0.4 GB | **4.4 GB** |
| vLLM (FP16) | 13 GB | 0.4 GB（更高效）| **13.4 GB** |
| vLLM (AWQ-INT4) | 4 GB | 0.4 GB | **4.4 GB** |

> 量化后 Ollama 与 vLLM 显存占用一致，但 vLLM **更多用于服务化**而非"省显存"。

### 4.2 100 并发下总占用

| 引擎 | 显存占用 | 备注 |
|------|---------|------|
| Ollama | OOM（无法 100 并发）| 单进程限制 |
| **vLLM** | **22 GB** | PagedAttention 充分复用 |
| TGI | 21 GB | FlashAttention 2 + custom kernel |

> ⚠️ **口径说明**：本节为 **ShareGPT 式负载**（平均输出 200 token，KV cache 随并发线性膨胀），24GB 单卡上 Ollama 单进程 KV 管理粗放直接 OOM；与 §2.1 吞吐表中 Ollama「100/500 并发可跑 52/65 req/s」**不矛盾**——那是短输出/小 ctx 条件（KV 压力小，见 §2.1 口径说明）。

---

## 长上下文（128k）性能
### 5.1 单卡 A100 80GB

| 引擎 | Qwen-7B-128K 吞吐量 | 备注 |
|------|---------------------|------|
| Ollama | 1.2 req/s | 难以支持 128k |
| **vLLM** | **3.5 req/s** | PagedAttention 显著优势 |
| TGI | 2.8 req/s | 接近 vLLM |

### 5.2 vLLM 长上下文关键技术

- **PagedAttention**：KV 分页避免长序列独占
- **Chunked Prefill**：把超长 prompt 分块处理
- **Sparse Attention**（实验）：LongLoRA / Landmark Attention

---

## Prefix Sharing 命中率
### 6.1 场景：RAG 检索 + 长 prompt

| 引擎 | prefix 命中率 | 显存节省 |
|------|--------------|---------|
| Ollama | 0%（无此功能）| 0% |
| TGI | 30% | 25% |
| **vLLM** | **70%** | **45%** |
| LMDeploy | 60% | 40% |

> vLLM 在 RAG / 多轮对话 / Few-shot 场景有显著优势。

---

## 反模式 · 不要轻信单一 benchmark
### ⚠️ 反模式 1：只看峰值吞吐

不同负载下 vLLM 优势不同：
- 7B 模型 + 24GB 卡 + 50 并发：vLLM 优势 **5x**
- 70B 模型 + 8 卡 + 200 并发：vLLM 优势 **7x**
- 7B 模型 + CPU：Ollama 可能比 vLLM **更快**（vLLM 强 GPU 绑定）

### ⚠️ 反模式 2：忽略冷启动延迟

- vLLM 冷启动 30-60 秒（导入 torch / 加载 CUDA kernel）
- Ollama 冷启动 2-5 秒（模型已预加载）
- 无服务器 / Serverless 场景：Ollama 更友好

### ⚠️ 反模式 3：用 default 配置对比

- vLLM 默认 `--max-num-seqs=256`，小显存机器需要调小
- Ollama 默认 `num_ctx=2048`，需配合模型上下文

---

## 一句话总结
> **vLLM 在工业级负载（多并发 + 长上下文 + 高 QPS）几乎全面领先 Ollama（高并发下常见数倍至一个数量级，视负载而异），但单机 / 边缘场景两者差距收窄甚至反转——选型看场景。**

---

← [返回: vLLM vs Ollama](../README.md) · 上一章：[05-distributed-inference](05-distributed-inference.md) · 下一章：[07-vs-tgi-lmdeploy](07-vs-tgi-lmdeploy.md)

---

## 📚 参考来源

> 说明：以下论文支撑本文的**机制解释**（为什么 vLLM 领先），但本文表格的具体数字与论文数据**不是一一对应**（见文首口径声明）；官方 benchmark 页链接见第 6-8 条，复测时以官方页为准。

1. **Efficient Memory Management for Large Language Model Serving with PagedAttention**：Woosuk Kwon et al. *vLLM 论文：PagedAttention + 连续批处理是高并发吞吐优势的核心机制，支撑 §2 吞吐表、§4.2 显存表的趋势（论文报告的倍数基于其自测环境，与本文表格数字不等同），SOSP 2023*. https://arxiv.org/abs/2309.06180
2. **FlashAttention: Fast and Memory-Efficient Exact Attention with IO-Awareness**：Tri Dao et al. *FlashAttention 用 IO-aware tiling 把 attention 显存降为 O(N)，支撑 §3 TTFT 表与 §4 显存表的机制解释，NeurIPS 2022*. https://arxiv.org/abs/2205.14135
3. **FlashAttention-2: Faster Attention with Better Parallelism and Work Partitioning**：Tri Dao. *FlashAttention 2：进一步并行化与工作划分优化，支撑 §3 TTFT 表机制解释，2023*. https://arxiv.org/abs/2307.08691
4. **Accelerating Large Language Model Decoding with Speculative Sampling**：Yaniv Leviathan et al. *Speculative Decoding 推测式采样加速推理（本文未展开，延伸参考），Google 2023*. https://arxiv.org/abs/2211.17192
5. **SARATHI: Efficient LLM Inference by Piggybacking Decodes with Chunked Prefills**：Amey Agrawal et al. *Chunked Prefill 分块预填：解决 prefill-decode 互相阻塞，支撑 §3 TTFT 表与 §5.2 长上下文技术，OSDI 2024*. https://arxiv.org/abs/2308.16369
6. **vLLM 官方 Performance Benchmark**：*vLLM 各版本对 HF/TGI/LMDeploy 的官方吞吐与延迟复现脚本与结果，§2/§3 表格趋势的主要参照*. https://docs.vllm.ai/en/latest/performance/benchmarks.html
7. **LMDeploy 官方 Benchmark**：*TurboMind 引擎吞吐对比数据，§2.1/§2.2 中 LMDeploy 列的趋势参照*. https://lmdeploy.readthedocs.io/en/latest/benchmark/inference_benchmark.html
8. **TGI 官方 Benchmark / 文档**：*Text Generation Inference 的性能说明，§2 中 TGI 列的趋势参照*. https://huggingface.co/docs/text-generation-inference/index
