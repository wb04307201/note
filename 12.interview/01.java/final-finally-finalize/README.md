<!--question:
  id: 01.java-final-finally-finalize
  topic: 01.java
  difficulty: ⭐⭐
  frequency: 中频
  scenario_type: 反直觉代码
  tags: [01.java, final, finally]
  status: active
-->

# final / finally / finalize 深度剖析

> **一句话定位**：三胞胎关键字名似而神异 —— final 锁不变、finally 兜底清理、finalize 已废弃，混用必栽。

## 引子：三胞胎兄弟，你能分清吗？

Java 里有三个名字长得像三胞胎的关键字：

| 关键字 | 你可能以为 | 实际上是 |
|--------|-----------|---------|
| `final` | "最终的"？ | 修饰符：让类/方法/变量**不可改变** |
| `finally` | "最后"？ | 异常处理：`try-catch` 后**必定执行**的代码块 |
| `finalize` | "终结"？ | 已废弃的 GC 钩子方法，**千万别用** |

名字只差一两个字母，但职责天差地别。面试中经常把它们混在一起考，你能分清楚吗？

---

## 一、final

> 📚 **前置知识**：[Java 语法基础](../../../01.java-and-jvm/01-language/syntax/README.md)

`final` 是 Java 中最常用的修饰符之一，核心语义是"不可改变"，根据修饰对象不同有三种表现。

### 1.1 修饰类：不可继承

被 `final` 修饰的类不能有子类，编译器会直接阻止继承行为。

```java
public final class String { }  // String 不可被继承
public final class Integer { } // Integer 不可被继承
// public class MyString extends String { } // 编译错误
```

**设计意图**：保证类的不可变性和安全性。像 `String`、`Integer` 这样的核心类，如果允许继承，子类可能破坏其不可变契约，导致哈希表、安全校验等依赖不可变性的机制失效。

### 1.2 修饰方法：不可重写 + 编译期绑定

`final` 方法可以被子类继承和调用，但不能被重写（override）。

```java
class Parent {
    public final void greet() {
        System.out.println("Hello");
    }
}
class Child extends Parent {
    // @Override public void greet() { } // 编译错误
}
```

**关键点**：`final` 方法在编译期就确定了调用目标（静态绑定），不会走虚方法表（vtable）查找，因此无法实现多态。这也是为什么 `private` 方法隐式等价于 `final`——私有方法本身就不能被重写。

**历史背景**：早期 JVM 中，`final` 方法可能被内联优化以提升性能。现代 JIT 编译器足够智能，能自行判断是否内联，因此出于性能考虑使用 `final` 的意义已不大。

### 1.3 修饰变量：不可重新赋值

这是 `final` 最核心的用法，但需要区分基本类型和引用类型。

```java
// 基本类型：值不可变
final int x = 10;
// x = 20; // 编译错误

// 引用类型：引用不可变，但对象内容可变
final List<String> list = new ArrayList<>();
list.add("hello");   // 合法：修改对象内部状态
// list = new LinkedList<>(); // 编译错误：不能重新赋值引用
```

**常见误区**：很多人认为 `final` 能让对象"不可变"，这是错误的。`final` 只保证引用本身不指向其他对象，不保证对象内部状态不变。真正的不可变对象需要类自身设计保证（如 `String` 内部 `char[]` 也是 `final` 且不提供修改方法）。

### 1.4 空白 final（Blank Final）

`final` 变量可以不立即初始化，但必须在使用前完成赋值，且只能赋值一次。

```java
class Example {
    private final int value;          // 空白 final

    {
        value = 42;                   // 实例代码块中初始化
    }

    private static final int STATIC_VALUE;

    static {
        STATIC_VALUE = 100;           // 静态代码块中初始化
    }
}
```

**初始化时机三选一**：
- 声明时直接赋值
- 实例代码块或构造器中赋值（实例变量）
- 静态代码块中赋值（静态变量）

构造器中赋值时要特别注意：如果有多个构造器，每个路径都必须给 `final` 变量赋值。

### 1.5 深挖：final 字段的 JMM 冻结语义（加分项）

`final` 不只是编译期检查，在 Java 内存模型（JMM）层面还有**重排序规则 + 冻结（freeze）语义**：

- **写规则**：构造器内对 `final` 域的写入，与随后把被构造对象的引用赋值给其他引用变量这两个操作之间**不能重排序**——保证别的线程拿到引用时，final 字段已初始化完成。
- **读规则**：首次读包含 final 域的对象引用，与随后读该 final 域之间不能重排序。
- 因此**正确构造**（`this` 未在构造器中逸出）的对象，其他线程**无需同步**就能看到 final 字段的正确值——这是 `String` 等不可变类线程安全的根基。

**反例：构造函数逸出导致 final 失效**

```java
public class EscapeExample {
    private final int value;

    public EscapeExample() {
        this.value = 42;
        // ❌ this 在构造器中逸出：注册监听器把未构造完的对象暴露出去
        ListenerRegistry.register(this);
    }

    public int getValue() { return value; }
}
```

其他线程可能在构造器结束前通过注册表读到该对象，此时 final 字段的冻结语义被破坏，**可能读到默认值 0 而非 42**。修法：把注册动作移出构造器（工厂方法中完成），或用内部类事件源延迟逸出（《Java Concurrency in Practice》§3.2.1）。

> 细节：JMM 中 final 字段写入后有 freeze 动作（`freeze(f, v)`），逸出场景下 freeze 的"正常路径"假设失效——这属于 JLS 17.5 final field semantics 的规范盲区，实践中一律按"构造器不逸出 this"处理。

### 1.6 追问必考：那怎样才能做到「真正不可变」？

面试官问完「final 修饰的对象真的不可变吗」，**下一句几乎一定是这个**。光答"不是"只拿到及格分，能给出设计清单才是加分。

**不可变类的五个必要条件**（Effective Java Item 17 口径）：

| # | 条件 | 漏掉的后果 |
|---|------|-----------|
| 1 | 类声明为 `final`（或用私有构造器 + 静态工厂） | 子类可以重写 getter 返回被篡改的值，或新增 setter |
| 2 | 所有字段 `private final` | 字段可被同包/子类直接改写；失去 JMM 冻结保证 |
| 3 | **不提供任何修改状态的方法** | 有 setter / `add` / `clear` 就等于可变 |
| 4 | **防御性拷贝**：构造器入参 + getter 出参都拷贝可变对象 | 调用方持有原始引用，绕过所有 final 直接改内部状态 |
| 5 | 字段类型本身也不可变 | 只是**浅不可变**——见下方陷阱 |

**❌ 浅不可变 vs ✅ 深不可变**（条件 4 + 5 是最容易漏的两条）：

```java
// ❌ 看着不可变，实际可被外部篡改
record Point(List<Integer> xs) {}

Point p = new Point(new ArrayList<>(List.of(1)));
p.xs().add(99);
System.out.println(p.xs());   // [1, 99]  ← record 组件是 final 引用，不是 final 内容！

// ✅ 构造器防御性拷贝（紧凑构造器写法）
record SafePoint(List<Integer> xs) {
    SafePoint { xs = List.copyOf(xs); }   // 入参拷贝 → 字段本身已不可变
}

List<Integer> src = new ArrayList<>(List.of(1));
SafePoint s = new SafePoint(src);
src.add(2);                               // 事后改源 list
System.out.println(s.xs());               // [1] ← 不受影响
s.xs().add(7);                            // UnsupportedOperationException
```

> 若字段在构造后**已经是不可变类型**（如上例 `List.copyOf` 的结果），accessor 直接返回即可，无需二次拷贝；只有当 getter 需要返回可变类型的拷贝时才写出参拷贝。

> 🔬 以上两段行为在本机 **JDK 25 实测验证**：`record Point(List<Integer> xs)` 的 `p.xs().add(99)` 确实生效，输出 `[1, 99]`。

**❌ unmodifiableList ≠ 不可变**（高频追问点）：

```java
List<String> src = new ArrayList<>(List.of("x"));
List<String> view = Collections.unmodifiableList(src);  // 只是「视图」
List<String> copy = List.copyOf(src);                   // 才是「拷贝」(Java 10+)

src.add("y");                    // 改原始 list
System.out.println(view);        // [x, y]  ← 视图跟着变！持有 src 的人仍能改
System.out.println(copy);        // [x]     ← 拷贝不受影响
copy.add("z");                   // UnsupportedOperationException
```

> 🔬 JDK 25 实测输出如上：`view = [x, y]`、`copy = [x]`、`copy.add` 抛 `UnsupportedOperationException`。
> **一句话记忆**：`unmodifiableXxx` 是「**只读视图**」（read-only view），`List.copyOf` / `Map.copyOf` 是「**不可变副本**」（immutable copy）。前者防的是"拿到返回值的人改"，后者连"原始引用持有者"一起防住。

**⚠️ 反射是 final 的后门**：`final` 是**编译期约束**，不是运行时铁墙。`Field.setAccessible(true)` 仍可改 final 字段（Java 12+ 通过 `Field.modifiers` 移除 final 修饰符会抛 `NoSuchFieldException`，但配合 `--add-opens` 或 `Unsafe` 仍能绕过）。详见 [反射专题](../../../01.java-and-jvm/01-language/reflection/README.md) 的「final 字段修改注意事项」。所以**不可变性是"约定 + 编译期检查"，不是安全边界**——安全敏感场景不能靠 final 防篡改。

**为什么还要用 final**（把「不保证不可变」和「有真实价值」说清楚，是这题的高分落点）：

- ✅ **编译期防重新赋值**：捕获"手滑改引用"这类 bug
- ✅ **JMM 安全发布**：正确构造（this 不逸出）的 final 字段无需同步即对其他线程可见（§1.5）
- ✅ **可读性契约**：声明"这个字段的设计意图是不变"
- ❌ 但**不等于**对象不可变 —— 需要上面五个条件配合

---

## 二、finally

`finally` 是 `try-catch-finally` 异常处理结构的一部分，核心保证是：**无论是否发生异常，finally 块都会执行**（除非 JVM 退出或线程被杀死）。

### 2.1 执行顺序

```java
public static int test() {
    try {
        System.out.println("try");
        return 1;
    } catch (Exception e) {
        System.out.println("catch");
        return 2;
    } finally {
        System.out.println("finally");  // 在 return 之前执行
    }
}
// 输出：try → finally → 返回 1
```

**关键规则**：`finally` 在 `return` 语句之后、实际返回值传递给调用者之前执行。如果 `finally` 中没有 `return`，则原来的返回值保持不变。

### 2.2 finally 中的 return 覆盖问题

```java
public static int dangerousReturn() {
    try {
        return 1;
    } finally {
        return 2;  // ⚠️ 覆盖了 try 中的返回值
    }
}
// 返回值是 2，不是 1
```

**陷阱分析**：当 `finally` 中包含 `return` 时，它会无条件覆盖 `try` 或 `catch` 中的返回值。这会导致：
1. 原始返回值丢失，调用方拿到意外结果
2. 如果 `try` 中抛出了异常但 `finally` 中有 `return`，异常会被吞掉

```java
public static int swallowException() {
    try {
        throw new RuntimeException("oops");
    } finally {
        return 1;  // ⚠️ 异常被吞掉，正常返回 1
    }
}
```

**最佳实践**：**永远不要在 `finally` 中使用 `return`**。IDE（如 IntelliJ IDEA）会将此标记为警告。

---

## 三、finalize

`Object.finalize()` 方法设计初衷是让对象在被垃圾回收前执行清理工作，类似析构函数。但它在 Java 9 中被标记为 `@Deprecated`，Java 18+ 中已移除。

### 3.1 为什么废弃？

| 问题 | 说明 |
|------|------|
| **不保证执行时机** | GC 何时触发不确定，`finalize` 可能很久后才执行，甚至 JVM 退出时都不执行 |
| **性能极差** | 带 `finalize` 的对象需要经过两次 GC 才能被回收（第一次执行 finalize，第二次才真正回收），严重拖慢 GC |
| **可能导致对象复活** | 在 `finalize` 中将 `this` 引用赋值给其他变量，可以让对象"起死回生"，造成内存泄漏 |
| **异常被静默吞掉** | `finalize` 中抛出的未捕获异常会被忽略，难以调试 |
| **没有执行保证** | 即使调用了 `System.gc()`，也不保证 `finalize` 一定会被执行 |

### 3.2 替代方案

#### 方案一：try-with-resources（推荐用于资源关闭）

```java
// 传统方式（容易遗漏）
BufferedReader br = null;
try {
    br = new BufferedReader(new FileReader("test.txt"));
    // 读取文件
} catch (IOException e) {
    e.printStackTrace();
} finally {
    if (br != null) {
        try { br.close(); } catch (IOException e) { e.printStackTrace(); }
    }
}

// 现代方式（Java 7+）
try (BufferedReader br = new BufferedReader(new FileReader("test.txt"))) {
    // 读取文件，自动关闭
}
```

#### 方案二：Cleaner（Java 9+，用于原生资源清理）

```java
import java.lang.ref.Cleaner;

public class NativeResource implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();
    private final Cleaner.Cleanable cleanable;
    private boolean closed = false;

    public NativeResource() {
        this.cleanable = CLEANER.register(this, () -> {
            // 清理原生资源（如 JNI 分配的内存）
            System.out.println("Cleaning up native resource");
        });
    }

    @Override
    public void close() {
        if (!closed) {
            cleanable.clean();  // 显式清理
            closed = true;
        }
    }
}
```

**Cleaner 的核心优势**：
- 清理逻辑与对象生命周期解耦
- 通过 `AutoCloseable` 提供确定性清理
- `Cleaner` 作为最后防线，防止忘记调用 `close()` 时的资源泄漏

---

## 四、代码示例 + 陷阱

### 陷阱 1：finally 中 return 覆盖

```java
public static int trap1() {
    try {
        return 100;
    } finally {
        return 200;  // 实际返回 200
    }
}
```

- **真相**：`finally` 中的 `return` 会**丢弃** try 块的返回值和正在传播的异常（编译器给 WARN，但不是错误）。资源清理交给 try-with-resources，`finally` 里永远不要写 `return` / `throw`。

### 陷阱 2：final 变量未在构造器中初始化

```java
class BadExample {
    private final int value;  // 编译错误：blank final 未初始化

    public BadExample() {
        // 忘记给 value 赋值
    }
}
```

- **真相**：空白 final 必须在**声明处 / 实例代码块 / 构造器**三者之一完成赋值，且所有构造器路径都要覆盖。多个构造器时容易漏——把初始化收敛到一个私有构造器 + 委托调用（`this(...)`）最安全。

### 陷阱 3：误以为 final 引用指向的对象不可变

```java
final StringBuilder sb = new StringBuilder("hello");
sb.append(" world");  // 合法！对象内容可以修改
System.out.println(sb);  // "hello world"
```

- **真相**：`final` 只锁**引用**（不能重新赋值指向别的对象），不锁**对象内部状态**。要真正不可变需要五个条件同时成立（类 final + 字段 private final + 无修改方法 + 构造器/getter 双向防御性拷贝 + 字段类型本身不可变），详见 [§1.6](#16-追问必考那怎样才能做到真正不可变)。两个高频二阶坑：`record` 组件是**浅不可变**（`p.xs().add()` 照样生效）、`Collections.unmodifiableList` 是**只读视图**而非拷贝（原始引用持有者仍能改，用 `List.copyOf` 才是真副本）。

### 陷阱 4：finally 中抛出异常覆盖原有异常

```java
public static void trap4() throws Exception {
    try {
        throw new IOException("original");
    } finally {
        throw new SQLException("covers original");  // 原始异常丢失
    }
}
```

- **真相**：原始异常被静默吞掉，排查时只看到 `SQLException`，根因永久丢失（try-with-resources 用 Suppressed 机制专门解决了这个问题）。`finally` 里若必须处理资源异常，应 catch 后记日志而非往外抛。

---

## 五、最佳实践

### 5.1 用 try-with-resources 替代 finally 关闭资源

```java
// ✅ 推荐
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql)) {
    // 执行业务逻辑
}
// 自动按相反顺序关闭资源

// ❌ 避免
Connection conn = null;
try {
    conn = dataSource.getConnection();
} finally {
    if (conn != null) {
        try { conn.close(); } catch (SQLException e) { /* log */ }
    }
}
```

### 5.2 用 Cleaner 处理原生资源

对于涉及 JNI、直接内存等非堆资源的场景，使用 `Cleaner` 作为安全网：

```java
public class DirectMemoryBuffer implements AutoCloseable {
    private static final Cleaner CLEANER = Cleaner.create();
    private final Cleaner.Cleanable cleanable;
    private long address;  // 原生内存地址

    public DirectMemoryBuffer(long size) {
        this.address = allocateNativeMemory(size);
        this.cleanable = CLEANER.register(this, () -> {
            freeNativeMemory(address);
        });
    }

    @Override
    public void close() {
        cleanable.clean();
        address = 0;  // 防止重复释放
    }

    private static native long allocateNativeMemory(long size);
    private static native void freeNativeMemory(long address);
}
```

### 5.3 final 变量的使用建议

- 所有不会被重新赋值的字段都应加上 `final`，提升代码可读性
- 不可变类（如 DTO、Value Object）的所有字段都应是 `private final`
- 方法参数加 `final` 可防止意外修改，但团队风格一致更重要

---

## 六、面试话术（30 秒版 + 90 秒版）

**30 秒版**：

> "一句话总结：`final` 锁引用不锁对象，`finally` 管清理，`finalize` 已经淘汰。`final` 修饰类不可继承、方法不可重写、变量不可重新赋值——但**引用类型只是引用不可变，对象内容照样能改**（要真不可变还得防御性拷贝 + 字段类型本身不可变）；`finally` 保证必定执行，但千万别在里面写 return；`finalize` 因执行时机不确定 + 性能差在 Java 9 废弃，资源清理用 try-with-resources，原生资源用 Cleaner。"

**90 秒版**：

> "`final` 是修饰符，修饰类表示不可继承（如 String），修饰方法表示不可重写且编译期绑定，修饰变量表示不可重新赋值——注意引用类型只是引用不可变，对象内容仍可修改。**追问「那怎样才真不可变」时的答法**：需要五个条件同时成立——类 final、字段 private final、不提供任何修改方法、构造器入参与 getter 出参都做防御性拷贝、字段类型本身也不可变；两个高频二阶坑是 record 组件属浅不可变（`p.xs().add()` 照样生效）、`Collections.unmodifiableList` 是只读视图而非拷贝（要用 `List.copyOf`）。**高分落点**：final 不保证不可变，但保证**安全发布**——JMM 的冻结语义让正确构造的对象无需同步即对其他线程可见。深挖一层：构造器内写 final 域与 this 引用逸出之间禁止重排序，所以构造器中逸出 this 会破坏冻结语义，别的线程可能读到默认值。
>
> `finally` 是异常处理的一部分，保证无论是否异常都会执行，常用于资源清理。两个陷阱：**永远不要在 finally 中写 return**（会覆盖 try 的返回值甚至吞掉异常）；finally 中抛异常同样会覆盖原始异常。Java 7 之后资源清理直接用 try-with-resources，它自动生成 null 检查 + 按相反顺序关闭 + 抑制异常（Suppressed）。
>
> `finalize` 是 Object 类的 GC 前清理钩子，废弃原因有三个：① 执行时机不确定，JVM 退出也不保证运行；② 性能差——带 finalize 的对象要经过两次 GC 才能回收（第一次 GC 发现不可达后放入 F-Queue，由低优先级的 Finalizer 守护线程执行 finalize()，对象被重新标记，第二次 GC 才真正回收）；③ 可在 finalize 中把 this 赋给静态引用让对象"复活"（只能复活一次），造成泄漏。替代品是 Java 9+ 的 `Cleaner`：内部用 PhantomReference + 引用队列，清理逻辑跑在独立的 Cleaner 守护线程上（线程工厂由创建者控制），且注册的是 Runnable 而非对象本身，避免了 this 逃逸。
>
> 总结：`final` 管引用不变与安全发布，`finally` 管清理，`finalize` 已淘汰。"

---

## 七、交叉引用

- 主模块：[`01.java`](../../../01.java-and-jvm/) — Java 知识体系
- [JVM 调优](../../../01.java-and-jvm/02-jvm/tuning.md) — GC 算法与内存管理
- [变量与 final 关键字](../../../01.java-and-jvm/01-language/variable/README.md) — final / static final / effectively final 主模块版（含编译期内联陷阱）
- [Record 类型](../../../01.java-and-jvm/01-language/record/README.md) — 不可变数据载体：浅不可变陷阱与防御性拷贝 accessor 写法
- [反射](../../../01.java-and-jvm/01-language/reflection/README.md) — 反射修改 final 字段的边界（Java 12+ modifiers 过滤 / --add-opens）
- [String 不可变性](../../../01.java-and-jvm/01-language/string/README.md) — 真不可变类的标准样板（byte[] 私有 + 无修改方法）

## 相关章节

- 深度阅读：[`01.java-and-jvm`](../../../01.java-and-jvm/README.md) — 主模块详细内容

> 📅 2026-09-01 · 咬文嚼字 · final/finally/finalize · ⭐⭐（中频面试 + 实战必会）

← [返回: 咬文嚼字 · final-finally-finalize](../README.md)
