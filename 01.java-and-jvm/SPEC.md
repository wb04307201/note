
# SPEC for 01.java-and-jvm/

> **Inherits from**: [../SPEC.md](../SPEC.md)
> **Mode**: append + override
> **Updated**: 2026-10-13

---

## 模块定位

Java 语言基础 + JVM 原理 + 并发编程 + 设计模式。

## 从 L0 继承

- G1-G6 通用评分维度
- 11 类基础扫描规则
- 命名约定 + commit 格式 + 互链规则

## 本模块规则

### 评估维度（追加 G 维度后）

| # | 维度 | 2 分 | 1 分 | 0 分 |
|---|------|------|------|------|
| A1 | 源码级深度 | 有源码片段 + WHY 注释 | 有代码只解释 WHAT | 无代码 |
| A2 | 版本演进对比 | 有 JDK X vs Y 对比 | 提及差异未展开 | 无版本 |
| A3 | ❌/✅ 反例对比 | 有正反例 | 只有正确用法 | 无对比 |
| A4 | 参数调优表 | 有实际参数 + 调优建议 | 有表无建议 | 无参数 |

### 写作要求

- 必须有源码片段（带 JDK 版本）
- 反模式用 ❌ 标识
- 至少 1 个生产实践案例

### 子目录约定（2026-10-13 全量对齐，15 个，find 校对）

| 目录 | 定位 |
|------|------|
| `01-language/` | Java 核心概念（OOP / 反射 / 注解 / SPI / 泛型）—— ⚠️ 旧名 `01-fundamentals/` 已于 2026-09 平铺重构中改名，勿引用旧名 |
| `02-jvm/` | JVM 原理（类加载 / GC / 内存模型）—— 有子 SPEC |
| `03-concurrency/` | 并发编程（底层原语 → 现代并发模型） |
| `04-patterns/` | GoF 23 设计模式 —— 有子 SPEC |
| `build-tools/` | Maven 与 Gradle 全方位对比 |
| `collection/` | 集合框架底层原理 |
| `io/` | I/O 流分类（字节 / 字符 / 缓冲 / NIO） |
| `java-agent/` | JVM 字节码增强（premain / agentmain / Instrumentation） |
| `jdbc/` | JDBC 规范与连接管理 |
| `kotlin/` | Kotlin 语法与 Java 差异（空安全 / 协程） |
| `logging/` | 日志体系（JUL / Log4j 2 / Logback / SLF4J） |
| `modules/` | JPMS 模块系统 |
| `network/` | 网络编程（BIO / NIO / AIO / Reactor） |
| `testing/` | 测试技术（JUnit 5 / Mockito / JaCoCo）—— 有子 SPEC |
| `version/` | Java 版本演进编年史（java-10 → java-25 + 横切专题） |