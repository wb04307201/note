<!--module:
  parent: system-design
  slug: system-design/cloud-design-patterns
  type: article
  category: 主模块子文章
  summary: 云设计模式全景——可用性弹性/数据管理/通信集成/计算部署/安全治理五大类模式 + Resilience4j 重试与熔断配置 + 关键 trade-off 决策
  depth: ⭐⭐⭐
  status: active
-->

# 云设计模式

> ⚠️ **说明**：本文档虽以 Azure 为示例进行说明，但所列云设计模式为通用模式，可应用于 AWS、GCP、阿里云等。

**Microsoft Azure 云设计模式（Cloud Design Patterns）** 旨在解决云原生应用开发中的典型挑战，如**弹性、可伸缩性、可用性、数据管理**等。
---

## 核心原则
Azure 设计模式遵循 **12-Factor App** 原则，并强调：
- **分布式系统思维**（容忍故障、网络分区）
- **基础设施即代码**（IaC）
- **可观测性**（日志/指标/追踪一体化）
- **安全左移**（Security by Design）

---
## 关键 trade-off：模式选择的决策轴

云设计模式没有银弹，每个模式都在用一种成本换另一种收益。落地前先想清楚这 5 组取舍：

| 模式 | 换到什么 | 付出什么 | 决策要点 |
|------|---------|---------|---------|
| **Retry** | 临时故障下的成功率 | 重试风暴风险：故障期间流量放大 2-3 倍，可能压垮本已过载的下游 | 只对幂等操作 + 可恢复错误码重试；必须带指数退避与抖动；与熔断联动（熔断打开时不重试） |
| **CQRS** | 读写各自优化、读侧可水平扩展 | 引入最终一致性：写模型与读模型之间有同步延迟，"刚下单查不到订单"类问题 | 只有读写负载/模型差异足够大才值得拆分；能容忍读延迟的业务才用 |
| **Serverless** | 按调用计费、免运维、自动伸缩 | 冷启动延迟（百 ms 到秒级）+ 供应商锁定 + 长任务受限 | 突发低频流量首选；稳定高频或有状态负载反而更贵 |
| **Bulkhead** | 故障隔离——一个依赖拖垮不了整个进程 | 资源利用率下降：每个舱壁都要预留独立线程池/连接池 | 按"故障域 × 重要性"切分舱壁，核心链路给大配额，非核心给小配额 |
| **Cache-Aside** | 读性能数量级提升 | 缓存与数据库双写不一致窗口（先更库后删缓存也有并发缝隙） | 业务能容忍多大不一致窗口，决定用 TTL 兜底还是延迟双删/binlog 订阅 |

## 关键设计模式分类与详解
### 1. 可用性与弹性模式
| **模式**                                  | **核心作用**               | **Azure 服务示例**                      | **典型场景**           |
|-----------------------------------------|------------------------|-------------------------------------|--------------------|
| **重试模式 (Retry)**                        | 临时性故障（网络抖动、限流）自动重试     | `Polly`（.NET 库）、Azure SDK 内置重试策略    | 调用外部 API/数据库时      |
| **断路器模式 (Circuit Breaker)**             | 防止级联故障，快速失败（Fail Fast） | `Polly`、Dapr Resilience 组件          | 依赖服务持续失败时（如支付网关宕机） |
| **健康端点监控 (Health Endpoint Monitoring)** | 主动探测服务状态，触发自动恢复        | Azure Monitor + Application Gateway | 微服务集群自愈            |
| **领导者选举 (Leader Election)**             | 分布式系统中协调单一实例执行关键任务     | Azure Functions（单例触发器）、Dapr Actors  | 定时任务/资源协调（避免重复执行）  |

> **2025 趋势**：与 **Azure Chaos Studio** 集成，通过主动注入故障验证模式有效性。

#### 深入：Retry + Circuit Breaker 组合（Resilience4j 配置示例）

Java 生态中 Azure 文档推荐的 Polly 对应物是 **Resilience4j**（Spring Boot 官方 resilience 方案）。重试与熔断几乎总是成对出现——顺序很重要：**Retry 在外层包裹 Circuit Breaker**，这样熔断打开后重试会立即收到 `CallNotPermittedException` 快速失败，而不是继续打下游：

```yaml
# application.yml — Resilience4j Spring Boot 配置
resilience4j:
  retry:
    instances:
      paymentService:
        max-attempts: 3                # 总尝试 3 次（含首次）；再多会放大故障流量
        wait-duration: 200ms           # 首次重试等待，之后指数翻倍
        exponential-backoff:
          multiplier: 2                # 200ms → 400ms → 800ms
        enable-randomized-wait: true   # 加抖动，避免多实例同时重试形成波峰
        retry-exceptions:              # 白名单：只对可恢复异常重试
          - java.io.IOException
          - java.util.concurrent.TimeoutException
        ignore-exceptions:             # 业务异常（如余额不足）重试没有意义
          - com.example.InsufficientBalanceException
  circuitbreaker:
    instances:
      paymentService:
        sliding-window-size: 20            # 按最近 20 次调用统计失败率
        failure-rate-threshold: 50         # 失败率 ≥ 50% 打开熔断
        wait-duration-in-open-state: 10s   # 打开后 10s 内直接快速失败
        permitted-calls-in-half-open: 5    # 半开态放 5 个探测请求，全成功才闭合
        slow-call-duration-threshold: 2s   # 超过 2s 的调用计为慢调用
        slow-call-rate-threshold: 80       # 慢调用占比 ≥ 80% 也触发熔断（防"不报错但拖死"）
```

```java
// 装饰顺序：Retry( CircuitBreaker( 实际调用 ) )
// WHY：熔断在内层，打开后外层重试立即拿到 CallNotPermittedException，不再穿透到下游
@Retry(name = "paymentService")
@CircuitBreaker(name = "paymentService", fallbackMethod = "paymentFallback")
public PaymentResult charge(PaymentRequest req) {
    return paymentGatewayClient.charge(req);  // 要求下游接口幂等（携带幂等键）
}

// 降级路径：返回排队中状态，由对账任务异步补偿，而不是让用户看到 500
private PaymentResult paymentFallback(PaymentRequest req, Throwable t) {
    log.warn("payment degraded, enqueue for async processing, reqId={}", req.getId(), t);
    return PaymentResult.pending(req.getId());
}
```

三个高频陷阱：

1. **对非幂等操作重试**：支付/扣库存类接口重试必须携带幂等键，否则一次网络超时可能变成重复扣款。
2. **重试层级叠加**：客户端重试 3 次 × 网关重试 3 次 = 下游收到 9 倍流量。全链路只允许一层做重试，其余层快速失败。
3. **熔断阈值拍脑袋**：`failure-rate-threshold` 与窗口大小要基于线上错误率基线推导（如平时错误率 1%，阈值设 50% 意味着已经严重故障）；窗口太小会因偶发抖动误熔断。

#### 深入：Bulkhead（舱壁隔离）

- **适用场景**：一个服务依赖多个下游（如订单服务同时调用库存、支付、推荐），任一依赖变慢时不希望耗尽公共线程池。
- **机制**：为每个依赖分配独立的线程池或信号量配额（Resilience4j 提供 `ThreadPoolBulkhead` 与 `SemaphoreBulkhead`），配额用完即拒绝，故障被隔离在单个舱壁内。
- **陷阱**：线程池隔离换来的是额外的上下文切换与内存开销（每线程约 1MB 栈），低延迟路径优先用信号量隔离；配额总和远超机器承载能力等于没隔离。

#### 深入：Cache-Aside（旁路缓存）

- **适用场景**：读多写少（读:写 > 10:1）且业务能容忍短暂不一致，如商品详情、用户资料。
- **机制**：读路径"先查缓存，miss 则查库并回填"；写路径"先更新数据库，再删除缓存"（而不是更新缓存），下次读自然回填新值。
- **陷阱**：删除缓存失败会留下脏数据，需 TTL 兜底或订阅 binlog（如 Canal）异步补偿；"先删缓存后更库"在并发读写下更容易产生长期脏数据，一般不采用。

> 以上模式的深钻版（状态机、参数推导、雪崩复盘）见 [重试](../../../03-high-availability/retry/README.md) 与 [熔断](../../../03-high-availability/circuit-break/README.md)。

---

### 2. 数据管理与分区模式
| **模式**                                              | **核心作用**              | **Azure 服务示例**                                |
|-----------------------------------------------------|-----------------------|-----------------------------------------------|
| **分片 (Sharding)**                                   | 水平拆分大数据集，提升吞吐量与隔离性    | Azure SQL Database（弹性池+分片映射管理器）               |
| **CQRS (Command Query Responsibility Segregation)** | 读写分离，优化性能与扩展性         | Azure Cosmos DB（多主写入+读副本） + Event Hubs        |
| **事件溯源 (Event Sourcing)**                           | 通过事件流重建状态，实现审计与时间旅行查询 | Azure Event Hubs + Azure Storage Append Blobs |
| **物化视图 (Materialized View)**                        | 预计算复杂查询结果，加速读取        | Azure Synapse Analytics + Power BI            |

> **2025 趋势**：**AI 增强的自动分片**（Cosmos DB 智能分区键建议）、**实时 CQRS**（结合 Stream Analytics）。

---

### 3. 通信与集成模式
| **模式**                            | **核心作用**        | **Azure 服务示例**                                      |
|-----------------------------------|-----------------|-----------------------------------------------------|
| **异步消息 (Asynchronous Messaging)** | 解耦组件，削峰填谷       | **Azure Service Bus**（事务/会话支持）、**Event Grid**（事件驱动） |
| **API 网关 (API Gateway)**          | 统一入口、认证、限流、协议转换 | **Azure API Management**（支持 GraphQL/WebSockets）     |
| **管道-过滤器 (Pipes and Filters)**    | 流式数据处理（ETL）     | **Azure Data Factory** + **Azure Functions** 链式调用   |
| **网关聚合 (Gateway Aggregation)**    | 减少客户端与微服务的频繁交互  | API Management + Azure Functions 组合                 |

> **2025 趋势**：**Serverless 消息流**（Functions + Event Hubs 触发器）、**WebAssembly 轻量级网关**（Dapr Sidecar）。

---

### 4. 计算与部署模式
| **模式**                                      | **核心作用**   | **Azure 服务示例**                                        |
|---------------------------------------------|------------|-------------------------------------------------------|
| **自动扩缩容 (Autoscaling)**                     | 按负载动态调整资源  | **Azure Autoscale**（基于指标/时间表） + KEDA（Kubernetes 事件驱动） |
| **静态内容托管 (Static Content Hosting)**         | 高性能托管前端资源  | **Azure Static Web Apps**（内置 CI/CD + API 路由）          |
| **计算资源合并 (Compute Resource Consolidation)** | 低成本托管低负载服务 | **Azure Container Apps**（多容器共享资源）                     |
| **无状态服务 (Stateless Services)**              | 简化扩缩容，状态外置 | **Azure Kubernetes Service (AKS)** + Redis Cache      |

> **2025 趋势**：**混合扩缩容**（突发性能 + 预留实例）、**边缘计算协同**（AKS + Azure Arc）。

---

### 5. 安全与治理模式
| **模式**                        | **核心作用**                                |
|-------------------------------|-----------------------------------------|
| **身份联合 (Federated Identity)** | 零信任架构，最小权限访问（Azure AD 集成）               |
| **策略即代码 (Policy as Code)**    | 通过 **Azure Policy** + **Bicep 模块** 强制合规 |
| **机密存储 (Secrets Management)** | 凭据/证书集中管理（**Azure Key Vault** + 托管标识）   |

> **2025 重点**：**AI 驱动的威胁检测**（Microsoft Defender for Cloud 集成）、**机密计算**（Confidential VMs 保护内存数据）。

---

## 如何选择与实施？
1. **问题驱动**：先明确痛点（如“数据库在高并发下响应慢” → 考虑 CQRS + 读写分离）。
2. **成本权衡**：
    - 简单应用：Serverless（Functions + Cosmos DB）
    - 企业级：AKS + 服务网格（Istio on AKS）
3. **使用参考架构**：  
   Azure 提供 **[100+ 行业解决方案模板](https://learn.microsoft.com/en-us/azure/architecture/browse/)**（如 IoT、金融风控）。
4. **工具链支持**：
    - **Bicep/Terraform**：基础设施即代码
    - **OpenTelemetry**：统一可观测性
    - **Dapr**：简化分布式能力（状态/发布订阅/绑定）

---

## 2025 年演进方向
- **AI 原生集成**：设计模式与 Azure AI Studio 深度结合（如自动重试 + AI 降级策略）。
- **可持续架构**：模式优化碳排放（如“**绿色计算**”模式：通过调度减少资源闲置）。
- **边缘-云协同**：**Azure IoT Edge + 云模式**（如边缘断路器、边缘数据分片）。
- **量子就绪**：混合经典/量子算法的安全模式（Azure Quantum 服务）。

---

## 学习资源
1. [官方文档：Azure 设计模式](https://learn.microsoft.com/en-us/azure/architecture/patterns/)（持续更新）
2. [GitHub 样例库](https://github.com/mspnp)（Microsoft Patterns & Practices）
3. [Azure Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/)（成本/运营/安全等五大支柱）
4. **动手实验**：[Microsoft Learn 沙盒](https://learn.microsoft.com/)（免费 Azure 环境实践）

> 💡 **关键建议**：**勿过度设计**！从简单模式（如重试+健康检查）开始，根据监控数据迭代演进。Azure 的 PaaS 服务（如 Functions/Managed DB）已内置部分模式能力，优先利用托管服务而非自建。

持续关注 Azure 更新，云设计模式是**动态演进**的实践体系——2025 年的核心是 **“AI-augmented Resilience”**（AI 增强的韧性）与 **“Sustainable by Design”**（可持续设计）。

---

← [返回 系统设计基础](../README.md)