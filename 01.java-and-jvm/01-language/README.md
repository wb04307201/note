<!--module:
  parent: java
  slug: java/concepts
  type: article
  category: 主模块子文章
  summary: Java 核心概念（OOP / 类型 / 反射 / 注解 / SPI / 语法糖 等）全貌。
  depth: ⭐⭐
  status: active
-->

# Java 核心概念

> **定位**：Java 语言核心概念全景导览——从基本语法、OOP、类型系统到反射、注解、SPI、语法糖，19 个专题一站式掌握。

<!-- index-only -->

---

本目录涵盖 Java 语言的核心概念和基础知识，从基本语法到高级特性。

## 目录

### 语言基础

| 主题 | 说明 |
|------|------|
| [基本语法](syntax/) | 注释、关键字、运算符、流程控制 |
| [基本数据类型](data-types/) | 8种基本类型、包装类、自动装箱拆箱、精度问题 |
| [变量](variable/) | 成员变量、局部变量、静态变量、final关键字 |
| [方法](method/) | 方法类型、重载与重写、静态方法、可变参数、参数传递 |

### 面向对象

| 主题 | 说明 |
|------|------|
| [面向对象基础](oop/) | 三大特征（封装/继承/多态）、深浅拷贝、接口与抽象类、hashCode |
| [Object 类](object/) | 所有类的根类、equals/hashCode/toString、Objects工具类 |
| [内部类](inner-class/) | 成员内部类、静态内部类、局部内部类、匿名内部类 |
| [多态](polymorphism/) | 重载 vs 重写 + 编译时 vs 运行时分派 + vtable + 默认方法 + 协变返回（深度专题） |

### 类型系统

| 主题 | 说明 |
|------|------|
| [枚举](enum/) | 枚举常量、带属性/方法的枚举、EnumSet/EnumMap、枚举单例 |
| [泛型](generics/) | 类型擦除、通配符、PECS原则、多重边界 |
| [注解](annotation/) | 元注解、自定义注解、运行时注解处理 |
| [记录类 Record](record/) | 不可变数据载体、Compact Constructor、与Lombok对比 |

### 核心机制

| 主题 | 说明 |
|------|------|
| [String](string/) | 不可变性、String/StringBuffer/StringBuilder、字符串常量池 |
| [异常](exception/) | 异常层次、Checked/Unchecked、try-with-resources、最佳实践 |
| [反射](reflection/) | Class对象、动态操作类、字段和方法访问、应用场景 |
| [序列化和反序列化](serialization-and-deserialization/) | Serializable、序列化框架对比（Jackson/Protobuf/Kryo等） |
| [SPI](spi/) | Service Provider Interface、ServiceLoader、插件化扩展 |
| [语法糖](syntactic-sugar/) | Lambda、Stream、Switch表达式、文本块、Pattern Matching |

## 日期时间

| 专题 | 一句话定位 |
|------|-----------|
| [date-time](date-time/README.md) | JDK 8+ `java.time` API（LocalDateTime / Instant / Duration）、Date/Calendar 历史问题、时区与格式化 |

## 核心概念速查：接口 vs 抽象类选型

> 本页是导览页，定义级代码示例见各子 README。此处只保留最高频的选型决策——接口还是抽象类。

| 选型信号 | ❌ 常见误用 | ✅ 推荐做法 | 详见 |
|---------|-----------|-----------|------|
| 只定义"能做什么"（行为契约） | 用抽象类承载纯契约，强迫调用方继承 | 用 `interface`，多实现 + 组合灵活 | [oop/](oop/README.md#接口和抽象类的异同) |
| 需要共享状态/构造器/受保护模板方法 | 用接口 + default 方法模拟状态（接口字段只能是 `public static final`） | 用 `abstract class` 承载公共字段与骨架实现 | [oop/](oop/README.md#接口和抽象类的异同) |
| Java 8+ 想给接口加通用逻辑 | 每个实现类重复写相同代码 | `default` / `static` 方法收敛公共逻辑 | [polymorphism/](polymorphism/README.md) |
| 类型安全的多分派扩展点 | 抽象类单继承限制扩展 | 接口多实现（如 `Comparable` + `Serializable` 同时满足） | [generics/](generics/README.md) |

**30 秒口诀**：*契约用接口，骨架用抽象类；组合优于继承，default 方法补行为。*

> 面试题深挖版（含反例代码与话术）：[12.interview/01.java/interface-vs-abstract](../../12.interview/01.java/interface-vs-abstract/README.md)

其他核心概念入口：类与对象基础见 [oop/](oop/README.md)，异常体系与 try-with-resources 见 [exception/](exception/README.md)，反射见 [reflection/](reflection/README.md)。

## 概念关系总览

```text
Java 核心概念
│
├── 类型系统
│   ├── 基本数据类型 → 包装类（自动装箱拆箱）
│   ├── 引用类型 → 类 / 接口 / 枚举 / 注解 / Record
│   └── 泛型（编译期类型安全）
│
├── 面向对象
│   ├── 封装 → 访问控制（public/private/protected）
│   ├── 继承 → extends / implements
│   └── 多态 → 方法重写 + 向上转型
│
├── 核心机制
│   ├── 异常处理 → try-catch-finally / try-with-resources
│   ├── 反射 → 运行时类型信息
│   ├── 序列化 → 对象 ↔ 字节流
│   └── SPI → 插件化扩展
│
└── 语法糖
    ├── Lambda → 函数式编程
    ├── Stream → 声明式数据处理
    ├── Switch 表达式 → 增强分支逻辑
    ├── 文本块 → 多行字符串字面量
    └── Pattern Matching → 类型安全的模式匹配
```

---

## 📊 本节统计

| 统计维度 | 数值 | 口径 |
|----------|------|------|
| 分类主题数 | 5 组 | 语言基础 / 面向对象 / 类型系统 / 核心机制 / 日期时间 |
| 子 README 数 | 19 | [`date-time`](date-time/README.md) 等 `concepts/` 下 leaf README 数 |
| 含 frontmatter 的 README | 20 / 20 | 100% 覆盖（2026-07-22） |

> **统计时间戳**：2026-07-22

---

← [返回 01.java 主模块](../README.md)
