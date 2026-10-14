
# SPEC for 04.spring-backend/04-data/

> **Inherits from**: [../../SPEC.md](../../SPEC.md)
> **Mode**: append + override
> **Updated**: 2026-10-13

---

## 子目录定位

Spring 数据层 MOC：**事务管理 + 缓存抽象 + 数据访问**三大支柱 + MyBatis 整合专题（27 篇 4 主题专题库）。leaf 合计 40 篇（find 校对 2026-10-13，不含 README 索引页）。

## 从 L1 继承

- G1-G6 通用 6 维度评分
- A1 源码级深度（带 JDK / Spring 版本）
- A2 版本演进对比（Boot 2.x vs 3.x）
- A3 反例对比（❌/✅ 自动配置陷阱）
- A4 参数调优表 + A5 场景压测数据

## 本子目录规则（强特异性）

### 评估维度（追加 L1 维度后）

| # | 维度 | 2 分 | 1 分 | 0 分 |
|---|------|------|------|------|
| D1 | 事务失效场景 | ≥ 3 个失效场景（自调用 / 私有方法 / 异常类型）+ WHY | 有失效清单无原理 | 只讲传播行为 |
| D2 | 缓存模式选型 | 4 模式（Cache-Aside / Read-Through / Write-Through / Write-Behind）+ 一致性代价对比 | 有模式无代价 | 只讲注解用法 |
| D3 | MyBatis 全链路 | SqlSession → Executor → StatementHandler 源码链 + 插件拦截点 | 有流程图无源码 | 只讲 XML 配置 |
| D4 | 多数据源 / 分布式事务 | 有落地代码 + JTA/Seata 选型对比 | 提及未展开 | 无 |

### 写作要求

- 事务类文章必含「失效场景表」（场景 + 根因 + 验证方法）
- 缓存类文章必含「多级缓存层级图」+ 序列化选型（JDK / JSON / Kryo）
- MyBatis 类文章按 4 专题归位：架构原理 → `mybatis/01-architecture/`；扩展（拦截器/TypeHandler）→ `02-extension/`；Spring 整合 → `03-spring-integration/`；MP 全家桶 → `04-mybatis-plus/`
- 专题内新增文章必须同步更新本目录 README 的「本节统计」表（leaf 口径）

### 互链要求

- 必须回链 `../../README.md`（Spring 顶层）
- 事务 ↔ 缓存互链（`@Transactional` 与 `@Cacheable` 组合失效是高频考点）
- MyBatis 整合篇必链 `03-spring-integration/`（与 01-core 的 IoC/AOP 衔接）
- 分布式事务必链 `../../../06.distributed-systems/`（Seata / TCC 属分布式范畴）

### 反模式

- ❌ 只讲 `@Transactional` 用法不讲失效场景（D1 = 0 分）
- ❌ 缓存文章无序列化/一致性代价（只教 `@Cacheable` 开关）
- ❌ MyBatis-Plus 与原生 MyBatis 内容混放（应按 04-mybatis-plus / 01-architecture 分位）
- ❌ 事务传播行为表无 WHY（`REQUIRES_NEW` 挂起连接的连接池代价必须点出）

---

← [返回 04.spring-backend](../README.md)
