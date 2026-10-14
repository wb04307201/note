<!--module:
  parent: java
  slug: java/version/var-handle
  type: article
  category: 主模块子文章
  summary: Java 9 VarHandle：替代反射的轻量级字段/数组访问。
  depth: ⭐⭐⭐⭐
  status: active
-->

# VarHandle

> **定位**：Java 9 VarHandle（JEP 193）：`sun.misc.Unsafe` 的标准化替代，提供字段/数组的安全原子访问与四种内存序控制。

## 引言：变更说明

VarHandle 是 Java 9 引入的轻量级字段/数组访问机制，替代反射。

本篇按主题归类，给出每个条目的一句话定位 + 适用版本/场景，**先扫一遍再决定读哪节**。

---

## 功能描述

VarHandle 是 Java 9 引入的变量句柄 API，提供了一种安全、高效的方式来访问变量、数组元素和对象字段。它是 `sun.misc.Unsafe` 的标准化替代方案，支持原子操作、内存屏障和 volatile 语义，为底层编程和并发工具开发提供了官方支持。

## 基本用法（最新，Java 21+）

```java
import java.lang.invoke.*;
import java.util.concurrent.atomic.*;

// 1. 字段 VarHandle - 替代反射和 Unsafe
public class Counter {
    private volatile int count;
    private static final VarHandle COUNT_HANDLE;

    static {
        try {
            MethodHandles.Lookup lookup = MethodHandles.lookup();
            COUNT_HANDLE = lookup.findVarHandle(Counter.class, "count", int.class);
        } catch (NoSuchFieldException | IllegalAccessException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    // 原子递增
    public void increment() {
        COUNT_HANDLE.getAndAdd(this, 1);
    }

    // volatile 读取
    public int getCount() {
        return (int) COUNT_HANDLE.getVolatile(this);
    }
}

// 2. 数组 VarHandle - 高性能数组元素访问
public class ArrayOperations {
    private static final VarHandle ARRAY_HANDLE;

    static {
        try {
            ARRAY_HANDLE = MethodHandles.arrayElementVarHandle(int[].class);
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    // 原子更新数组元素
    public static void atomicUpdate(int[] array, int index, int newValue) {
        ARRAY_HANDLE.setRelease(array, index, newValue);
    }

    // 原子比较并交换（CAS）
    public static boolean compareAndSet(int[] array, int index, int expected, int update) {
        return (boolean) ARRAY_HANDLE.compareAndSet(array, index, expected, update);
    }
}

// 3. 内存序操作
public class MemoryOrderExample {
    private static final VarHandle VALUE_HANDLE;
    private int value;

    static {
        try {
            VALUE_HANDLE = MethodHandles.lookup()
                .findVarHandle(MemoryOrderExample.class, "value", int.class);
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    // Plain 操作（无内存屏障，最快）
    public void plainWrite(int v) { VALUE_HANDLE.set(this, v); }

    // Opaque 操作（保证原子性和单变量顺序）
    public void opaqueWrite(int v) { VALUE_HANDLE.setOpaque(this, v); }

    // Release 操作（release 语义，用于发布共享数据）
    public void releaseWrite(int v) { VALUE_HANDLE.setRelease(this, v); }

    // Volatile 操作（最强保证）
    public void volatileWrite(int v) { VALUE_HANDLE.setVolatile(this, v); }
}

// 4. 原子操作替代 AtomicInteger
public class VarHandleCounter {
    private int count;
    private static final VarHandle HANDLE;

    static {
        try {
            HANDLE = MethodHandles.lookup()
                .findVarHandle(VarHandleCounter.class, "count", int.class);
        } catch (Exception e) { throw new ExceptionInInitializerError(e); }
    }

    // 等价于 AtomicInteger.getAndIncrement()
    public int getAndIncrement() {
        return (int) HANDLE.getAndIncrement(this);
    }

    // 等价于 AtomicInteger.compareAndSet()
    public boolean compareAndSet(int expect, int update) {
        return (boolean) HANDLE.compareAndSet(this, expect, update);
    }
}
```

## 变更历史表

| Java版本  | 新特性/增强内容                                              |
|---------|-------------------------------------------------------|
| Java 21 | 无 VarHandle 独立 JEP；随虚拟线程（JEP 444）落地，VarHandle 原子操作在虚拟线程环境下可直接使用（详见下文） |
| Java 16-17 | 无 VarHandle 独立 JEP；随 JDK 例行演进（Valhalla 值类型预览版尚未在正式版 JDK 落地，VarHandle 相关支持仍属孵化阶段） |
| Java 9  | [JEP 193](https://openjdk.org/jeps/193): 引入 VarHandle API |

## 功能详细介绍

### 1. Java 9 - VarHandle 初始引入 (JEP 193)

作为 `java.lang.invoke` 包的一部分引入，核心概念：

- **替代 `sun.misc.Unsafe`**：提供标准化的底层变量访问 API
- **四种内存序**：
  - `set/get`：plain 操作，无内存屏障
  - `setOpaque/getOpaque`：保证原子性，不保证全局顺序
  - `setRelease/getAcquire`：release/acquire 语义，适用于生产者-消费者模式
  - `setVolatile/getVolatile`：volatile 语义，最强保证
- **原子操作**：`compareAndSet`、`getAndSet`、`getAndAdd` 等

### 2. Java 16-21 - 随 JDK 演进

- 无独立 JEP；API 表面基本稳定，性能随 JIT 与 `MethodHandles.Lookup` 实现改进
- Project Valhalla 值类型对 VarHandle 的扩展仍处于预览/孵化阶段，未进入正式版 JDK

### 3. Java 21+ - 虚拟线程协同

VarHandle 的原子操作在虚拟线程环境中自动适配，无需修改代码。

## VarHandle vs 其他原子操作方案

| 方案              | 安全性 | 性能   | 灵活性  | 适用场景        |
|-----------------|-----|------|------|-------------|
| `synchronized`  | 最高  | 最低   | 中    | 复杂同步逻辑      |
| `AtomicInteger` | 高   | 高    | 低    | 简单计数器       |
| `VarHandle`     | 高   | 最高*  | 最高   | 框架开发、高性能场景  |
| `Unsafe`        | 最低  | 最高   | 最高   | 遗留代码，不推荐使用   |

*性能为定性排序：VarHandle 与 `AtomicInteger` 底层同为 CAS 指令，低竞争下吞吐量级相当；VarHandle 的优势在于可显式选择更弱的内存序（opaque / acquire-release）以省去 volatile 级屏障，竞争密集场景收益更明显。精确差异依赖硬件、JDK 版本与竞争强度，需以 JMH 实测为准（本文不引用无出处的具体倍数）。

**AtomicInteger → VarHandle 迁移对比**：

```java
// ❌ 迁移前：AtomicInteger（只能 volatile 语义，字段必须 public/包可见或加 getter）
public class Counter {
    private final AtomicInteger count = new AtomicInteger();
    public void incr() { count.incrementAndGet(); }
}

// ✅ 迁移后：VarHandle（可选内存序 + 直接操作字段，适合框架/高性能库）
public class Counter {
    private volatile int count;
    private static final VarHandle COUNT;
    static {
        try {
            COUNT = MethodHandles.lookup()
                    .findVarHandle(Counter.class, "count", int.class);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }
    // 与 incrementAndGet 等价的 volatile 语义
    public void incr() { COUNT.getAndAdd(this, 1); }
    // 或降级为 release/acquire，减少屏障开销（AtomicInteger 做不到）
    public void incrRelaxed() {
        int cur = (int) COUNT.getAcquire(this);
        while (!COUNT.compareAndSet(this, cur, cur + 1)) {
            cur = (int) COUNT.getAcquire(this);
        }
    }
}
```

## 适用场景

1. **并发框架开发**：构建自定义锁、信号量等
2. **高性能数据结构**：无锁队列、跳表等
3. **序列化框架**：直接操作对象字段
4. **替代 Unsafe**：迁移遗留的 Unsafe 代码

## 总结

VarHandle 从 Java 9 引入以来，为 Java 提供了安全的高性能变量访问能力。它是 Unsafe 的标准化替代方案，支持多种内存序和原子操作，是并发工具开发和底层编程的核心 API。

---


## 相关章节

- [原子类 AtomicInteger/LongAdder](../../03-concurrency/atomic/README.md) — VarHandle 常替代的上层原子工具
- [Java 内存模型 JMM](../../03-concurrency/jmm/README.md) — 四种内存序（plain/opaque/acquire-release/volatile）的理论基础
- [Java 线程基础](../../03-concurrency/thread-basics/README.md)
- [Java 版本特性](../README.md)

← [返回 功能版本变更历史](../README.md)
