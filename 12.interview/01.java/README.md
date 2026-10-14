<!--module:
  parent: 12.interview
  slug: 12.interview/01.java
  type: index-only
  category: 面试题索引
  summary: Java 高频面试题与细节深挖（集合 / 并发 / JVM / 类型 / 设计模式）
  status: active
-->

# Java 咬文嚼字

> **定位**：Java 高频面试题与细节深挖（集合 / 并发 / JVM / 类型 / 设计模式）。

> Java 高频面试题与细节深挖，对齐主模块 [`01.java`](../../01.java-and-jvm/README.md)。40 篇分集合 / 并发 / JVM / 语言基础 / 对象类型 / 设计模式 / 综合 7 组（find 校对 2026-10-13；2026-08-10 迁出 6 篇灰色地带面试题到主模块 [01.java](../../01.java-and-jvm/README.md)：`object` → `concepts/data-types`，`create-object` → `concepts/object`，`singleton-pattern` → `design-patterns/creation/singleton.md`，`large-data-into-hashmap` → `collection/hashmap-performance.md`，`record-t` → `concepts/record`，`arrayList-distinct` → `collection/arraylist-distinct.md`），覆盖 90% 后端面试 Java 高频题。

---

## 文章清单（共 40 篇，find 校对 2026-10-13）

### 集合与数据结构
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [HashSet 替代 LinkedList 查找](replace-linkedlist-with-hashset/) | ⭐⭐⭐ | 中频 | 什么时候该换数据结构？ |
| [HashMap 扩容](hashmap-resizing/) | ⭐⭐⭐⭐ | 中频 | 1GB 的 HashMap 扩容会发生什么？ |
| [HashMap 线程不安全](hashmap-thread-unsafe/) | ⭐⭐⭐⭐ | 高频 | 3 大不安全表现 + 源码分析 + 4 大解决方案 |
| [快速给 Map 排序](sort-map/) | ⭐⭐ | 中频 | TreeMap vs LinkedHashMap 选型 |

### 并发与线程
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [ConcurrentHashMap 原理](concurrent-hashmap/) | ⭐⭐⭐⭐ | 高频 | ConcurrentHashMap 原理（JDK 7 vs 8） |
| [ThreadLocal 原理](threadlocal/) | ⭐⭐⭐⭐ | 中频 | ThreadLocal 原理与内存泄漏 |
| [父子线程数据传递](parent-child-thread/) | ⭐⭐⭐⭐ | 高频 | InheritableThreadLocal + TransmittableThreadLocal + CompletableFuture |
| [synchronized 锁升级](synchronized-lock-upgrade/) | ⭐⭐⭐⭐ | 高频 | synchronized 锁升级过程 |
| [volatile 内存语义](volatile/) | ⭐⭐⭐⭐ | 中频 | volatile 可见性、有序性、原子性 |
| [AQS 框架原理](aqs/) | ⭐⭐⭐ | 中频 | AbstractQueuedSynchronizer 实现机制 |
| [线程池 7 大参数](thread-pool/) | ⭐⭐⭐⭐ | 中频 | ThreadPoolExecutor 核心参数详解 |
| [并发 vs 并行](concurrency-vs-parallelism/) | ⭐⭐⭐ | 高频 | Rob Pike 定义 + 6 大误区 + CPU/IO 选型矩阵（延伸见主模块 [Java 并发编程导航 §1.3](../../01.java-and-jvm/03-concurrency/README.md)） |
| [Atomic 替代 synchronized](replace-synchronized-with-atomic/) | ⭐⭐⭐⭐ | 中频 | CAS 无锁编程 |
| [3 线程按顺序执行](thread-sequential-execution/) | ⭐⭐⭐ | 高频 | T1→T2→T3 的 3 语义 + 8 方案对比 + Top 3 推荐 |
| [虚拟线程](virtual-threads/) | ⭐⭐⭐⭐ | 高频 | carrier thread / mount-unmount / pinning / ScopedValue |
| [Excel 导出 OOM](excel-export-oom/) | ⭐⭐⭐ | 高频 | 3 大根因 + 流式写入 + 分批查询 + 多线程分片 + 内存改善原理 |
| [异步 vs 多线程](async-vs-multithread/) | ⭐⭐⭐ | 高频 | 执行顺序 vs 执行主体 + 4 种组合模式 + 4 大误区 + 30 秒话术 |

### JVM 与类加载
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [JVM 内存区域](jvm-memory/) | ⭐⭐⭐⭐ | 中频 | JVM 内存模型 + 对象创建流程 |
| [GC 算法与收集器](gc-algorithms/) | ⭐⭐⭐⭐ | 中频 | GC 算法 + 垃圾收集器对比 |
| [类加载机制](class-loading/) | ⭐⭐⭐⭐ | 中频 | 双亲委派模型 + 自定义类加载器 |
| [CPU 飙升排查](cpu-spike-troubleshooting/) | ⭐⭐⭐ | 中频 | 线上 CPU 100% 排查全流程（-Xmx 过小） |
| [生产 NoClassDefFoundError 排查全链路](no-class-def-found-troubleshooting/) | ⭐⭐⭐⭐ | 中高频 | Maven 传递依赖 4 类漏点 + 3 招修复 + 90s 话术 |
| [JVM 内存配置踩坑](jvm-memory-pitfall/) | ⭐⭐⭐⭐ | 中频 | -Xmx 超过系统可用内存导致启动失败 |
| [JVM Metaspace 调优踩坑](metaspace-tuning-troubleshooting/) | ⭐⭐⭐⭐ | 中高频 | 只设 MaxMetaspaceSize 不设 MetaspaceSize 触发频繁 GC + 容器默认 Xmx 陷阱 |

### 语言基础
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [CompletableFuture 编排](completable-future/) | ⭐⭐⭐ | 中频 | CompletableFuture 异步任务编排 |
| [== / equals / hashCode](equals-hashcode/) | ⭐⭐⭐ | 中频 | 相等性判断契约与陷阱 |
| [泛型擦除与 PECS](generics-erasure/) | ⭐⭐⭐ | 中频 | 类型擦除 + Producer Extends Consumer Super |
| [反射原理与性能](reflection/) | ⭐⭐⭐⭐ | 中频 | Reflection API 使用与性能开销 |
| [String/Builder/Buffer](string-builder-buffer/) | ⭐⭐⭐⭐ | 中频 | 字符串拼接选型指南 |
| [StringBuilder 重用](reuse-of-stringbuilder/) | ⭐⭐⭐⭐ | 中频 | 循环中字符串拼接优化 |
| [final/finally/finalize](final-finally-finalize/) | ⭐⭐ | 中频 | 三个关键字的区别与用法 |
| [Error vs Exception](error-vs-exception/) | ⭐⭐⭐ | 高频 | Error 和 Exception 的 6 维度对比 + 反模式 |
| [try-catch 性能](try-catch-performance/) | ⭐⭐⭐ | 中高频 | 正常路径零开销 / fillInStackTrace / OmitStackTraceInFastThrow |
| [SPI 机制](spi/) | ⭐⭐⭐ | 中频 | Service Provider Interface 扩展机制 |

### 对象与类型
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [接口 vs 抽象类](interface-vs-abstract/) | ⭐⭐ | 高频 | 6 维对比 + 设计哲学 + JDK 8+ 变化 + 选择原则 |
| [Integer 缓存](integer-cache/) | ⭐⭐⭐⭐ | 中频 | -128 到 127 的复用机制与陷阱 |
| [new String("123") 创建几个对象](new-string/) | ⭐⭐⭐⭐ | 中频 | 字符串常量池 vs 堆 |
| [多态深挖](polymorphism/) | ⭐⭐⭐⭐ | 高频 | 编译时 vs 运行时 / vtable / default 冲突 / @Override |

### 设计模式与技巧
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [switch 前用 if 优化](if-before-switch/) | ⭐⭐⭐⭐ | 中频 | 热点状态的快速路径优化 |

### 综合
| 主题 | 难度 | 频率 | 核心问题 |
|------|------|------|---------|
| [高频面试题合集](questions/) | ⭐⭐⭐ | 高频 | Java 综合高频问题深度解析（原理 → 演进 → 场景 → 权衡） |

---

## 学习路径

1. **入门**（1 周）：集合去重 + Integer 缓存 + String 相关 + 主模块 [`concepts/data-types`](../../01.java-and-jvm/01-language/data-types/README.md) + [`concepts/object`](../../01.java-and-jvm/01-language/object/README.md)
2. **进阶**（2 周）：HashMap 扩容 + 并发线程 + JVM 内存 + 设计模式（单例见主模块 [`design-patterns/creation/singleton`](../../01.java-and-jvm/04-patterns/creation/singleton.md)）
3. **冲刺面试**（1 周）：AQS + 锁升级 + GC 算法 + 类加载 + 高频面试题合集

## 相关章节

- 主模块：[`01.java-and-jvm`](../../01.java-and-jvm/README.md) — Java 知识体系
- 相关章节：[`03.database`](../03.database/)（SQL 相关）/ [`06.spring`](../06.spring/)（框架相关）

← [返回咬文嚼字（高频面试题）](../README.md)
