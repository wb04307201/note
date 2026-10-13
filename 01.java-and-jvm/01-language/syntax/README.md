<!--module:
  parent: java
  slug: 01.java/concepts/syntax
  type: article
  category: 主模块子文章
  summary: 基本语法 是入门必学的基础概念。
  depth: ⭐
  status: active
-->

# 基本语法

---

> **一句话定位**：基本语法定义 Java 的字面量、关键字、运算符与流程控制，是写出可编译代码的最小词汇表。

## 注释的3种方式

- **单行注释**（`//`）：通常用于解释方法内某单行代码的作用
- **多行注释**（`/* */`）：通常用于解释一段代码的作用
- **文档注释**（`/** */`）：通常用于生成 Java 开发文档（可被 `javadoc` 工具提取）

## Java语言关键字

| 分类 | 关键字 |
|------|--------|
| 访问控制 | `private`、`protected`、`public` |
| 类、方法和变量修饰符 | `abstract`、`class`、`extends`、`final`、`implements`、`interface`、`native`、`new`、`static`、`strictfp`、`synchronized`、`transient`、`volatile`、`enum`、`void` |
| 程序控制 | `break`、`continue`、`return`、`do`、`while`、`if`、`else`、`for`、`instanceof`、`switch`、`case`、`default`、`assert` |
| 错误处理 | `try`、`catch`、`throw`、`throws`、`finally` |
| 包相关 | `import`、`package` |
| 基本类型 | `boolean`、`byte`、`char`、`double`、`float`、`int`、`long`、`short` |
| 变量引用 | `super`、`this` |
| 保留字 | `goto`、`const` |

**受限关键字（Restricted Keywords）**单列一表——仅在特定上下文中具有特殊含义，其他位置仍可作普通标识符：

| 受限关键字 | 引入版本 | 生效上下文 |
|-----------|---------|-----------|
| `record` | Java 16 | 类型声明 |
| `sealed` / `permits` / `non-sealed` | Java 17 | 类/接口声明的密封修饰 |
| `yield` | Java 14 | switch 表达式 |
| `var` | Java 10 | 局部变量类型推断（严格说是受限标识符，见下文辨析） |

> 例如 `record` 仅在类型声明中是关键字，`yield` 仅在 switch 表达式中是关键字。

## 标识符和关键字的区别

标识符是程序员自定义的名字（如变量名、方法名、类名），关键字是 Java 语言保留的、具有特殊语法含义的词（如 `class`、`public` 等）。在 JLS（Java 语言规范）中，关键字和标识符是两种互斥的词法单元（token），标识符不能使用关键字命名。

## `var` 局部变量类型推断（Java 10+）

> **受限标识符 vs 受限关键字**一句辨析：按 JLS，`var` 不是关键字，而是**受限标识符（restricted identifier）**——仅在局部变量声明上下文中具有类型推断语义，其他位置（如 `int var = 1;`）仍可编译通过；`record`/`sealed`/`yield` 同理。
>
> `var` 的完整说明（类型推断规则、适用场景、使用限制、与 `final` 结合）以 [variable/README.md 的 var 专题](../variable/README.md#var-局部变量类型推断java-10) 为准，本文不再重复。

## `continue`、`break`和`return`的区别

- **`continue`**：跳出当前的这一次循环，继续下一次循环迭代
- **`break`**：跳出整个循环体，继续执行循环后面的语句
- **`return`**：结束方法执行，直接返回
- **`return value`**：结束方法执行，并返回一个特定值

```java
for (int i = 0; i < 10; i++) {
    if (i == 3) continue;     // 跳过 i=3，继续 i=4
    if (i == 7) break;        // i=7 时终止整个循环
    System.out.println(i);    // 输出: 0 1 2 4 5 6
}
```

## 运算符

### 运算符优先级（从高到低）

| 优先级 | 运算符 | 说明 |
|-------|--------|------|
| 1 | `()` `[]` `.` `expr++` `expr--` | 括号、数组访问、成员访问、后缀运算符 |
| 2 | `++expr` `--expr` `!` `~` `+` `-` `(type)` | 前缀一元运算符 |
| 3 | `*` `/` `%` | 乘除取模 |
| 4 | `+` `-` | 加减 |
| 5 | `<<` `>>` `>>>` | 移位 |
| 6 | `<` `<=` `>` `>=` `instanceof` | 比较 |
| 7 | `==` `!=` | 相等性 |
| 8 | `&` | 按位与 |
| 9 | `^` | 按位异或 |
| 10 | `\|` | 按位或 |
| 11 | `&&` | 逻辑与（短路） |
| 12 | `\|\|` | 逻辑或（短路） |
| 13 | `?:` | 三元运算符 |
| 14 | `=` `+=` `-=` `*=` `/=` 等 | 赋值 |

> **`->` 与 `::` 不参与优先级排序**：上表第 15 行原有 "`->` `::` 优先级最低" 的说法并不严谨——按 JLS，Lambda 箭头 `->` 和方法引用 `::` **不是表达式运算符**，不出现在 JLS §15.19（Operator Precedence）的优先级表里。它们出现在语法产生式（production）中：Lambda 表达式整体作为一个 `Primary` 级操作数参与运算，`->` 左侧是形参列表、右侧是 Lambda 体；`::` 是 `ReferenceType :: Identifier` 形式的独立产生式。所以 "优先级最低" 应理解为**语法结合层面**：Lambda 体尽量向右吞噬表达式（`x -> a + b` 中 `a + b` 整体是 Lambda 体），而不是像 `+`/`*` 那样存在两两可比的优先级数值。
>
> **示例**：`list.forEach(e -> System.out.println(e));` 等价于 `list.forEach(System.out::println);`
> `Runnable r = () -> doSomething();` 中赋值右侧整体是一个 Lambda 表达式——这是语法分析的结果，而非 "先赋值再构造 Lambda"。

### `&&` 与 `&`、`||` 与 `|` 的区别

- **`&&`（短路与）**：如果左操作数为`false`，不会计算右操作数
- **`&`（非短路与）**：无论左操作数结果如何，都会计算右操作数
- **`||`（短路或）**：如果左操作数为`true`，不会计算右操作数
- **`|`（非短路或）**：无论左操作数结果如何，都会计算右操作数

```java
// 短路保护 - 如果 obj 为 null，不会执行 obj.method()，避免 NPE
if (obj != null && obj.isValid()) { /* 安全调用 */ }

// 位运算 - & 和 | 也可以用于整数位运算
int a = 5 & 3;  // 0101 & 0011 = 0001 = 1
int b = 5 | 3;  // 0101 | 0011 = 0111 = 7
```

---

## 相关章节

- [variable](../variable/README.md#var-局部变量类型推断java-10) — `var` 受限标识符的完整说明（适用场景、使用限制、与 `final` 结合），与本文"`var` 局部变量类型推断"小节互为深浅两层
- [data-types](../data-types/README.md) — 8 种基本类型的取值范围、类型转换与精度陷阱（本文关键字表中"基本类型"一行的深度展开）

← [返回 Java 核心概念](../README.md)
