<!--module:
  parent: java
  slug: java/concepts/annotation
  type: article
  category: 主模块子文章
  summary: Java 注解（Annotation）：元注解、自定义注解、运行时解析。
  depth: ⭐⭐⭐
  status: active
-->

# 注解（Annotation）

---

> **一句话定位**：Java 注解是贴在代码上的元数据标签，让编译器、框架、运行时按需读取并触发校验、切面或注入逻辑。

注解（Annotation）是 Java 5 引入的特性，是一种元数据（metadata）机制，用于修饰类、方法、变量、参数等，为程序提供额外的描述信息，供编译器、框架或运行时环境读取和处理。

## 注解的基本概念

注解本身不会直接影响程序的运行逻辑，但可以被编译器、框架或运行时环境读取并做出相应处理。

```java
// 使用内置注解
@Override                    // 让编译器验证此方法是否正确重写了父类方法，若未正确重写则报错
@Deprecated                  // 标记已过时的 API
@SuppressWarnings("unchecked") // 抑制编译器警告
```

## 元注解

元注解是用来注解其他注解的注解，Java 提供了以下元注解：

### `@Retention` - 注解的保留策略

决定注解在哪个阶段可用：

| 保留策略 | 说明 |
|---------|------|
| `RetentionPolicy.SOURCE` | 仅存在于源代码中，编译后被丢弃 |
| `RetentionPolicy.CLASS` | 保留到字节码文件中，运行时无法获取（**默认值**） |
| `RetentionPolicy.RUNTIME` | 保留到运行时，可通过反射获取 |

```java
@Retention(RetentionPolicy.RUNTIME)  // 运行时可用
public @interface MyAnnotation { }
```

### `@Target` - 注解可以修饰的程序元素

| 目标类型 | 说明 |
|---------|------|
| `ElementType.TYPE` | 类、接口、枚举 |
| `ElementType.FIELD` | 字段（成员变量） |
| `ElementType.METHOD` | 方法 |
| `ElementType.PARAMETER` | 方法参数 |
| `ElementType.CONSTRUCTOR` | 构造方法 |
| `ElementType.LOCAL_VARIABLE` | 局部变量 |
| `ElementType.ANNOTATION_TYPE` | 注解类型 |
| `ElementType.PACKAGE` | 包 |
| `ElementType.TYPE_PARAMETER` | 类型参数（Java 8+） |
| `ElementType.TYPE_USE` | 类型使用（Java 8+） |
| `ElementType.MODULE` | 模块（Java 9+） |
| `ElementType.RECORD_COMPONENT` | Record 组件（Java 14 预览，Java 16 正式发布） |

```java
@Target({ElementType.METHOD, ElementType.TYPE})  // 可修饰方法和类
public @interface MyAnnotation { }
```

### `@Inherited` - 注解的继承性

标记了`@Inherited`的注解，在子类中会自动继承父类的注解。

```java
@Inherited
@Retention(RetentionPolicy.RUNTIME)
public @interface MyAnnotation { }

@MyAnnotation
public class Parent { }

public class Child extends Parent { }
// Child 也自动具有 @MyAnnotation
```

> **注意**：`@Inherited` 仅影响类上的注解继承——即子类会自动继承父类声明上的注解。它对接口、方法、字段等其他元素上的注解无效。

### `@Repeatable`（Java 8+）- 可重复注解

允许在同一个程序元素上多次使用同一个注解：

```java
@Retention(RetentionPolicy.RUNTIME)
@Repeatable(Roles.class)
public @interface Role {
    String value();
}

@Retention(RetentionPolicy.RUNTIME)
public @interface Roles {
    Role[] value();
}

// 使用
@Role("admin")
@Role("user")
public class User { }
```

### `@Documented` - 文档注解

标记了`@Documented`的注解会包含在 Javadoc 生成的文档中。

## 自定义注解

### 定义注解

```java
@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.METHOD, ElementType.TYPE})
public @interface ApiEndpoint {
    String value();                           // 必填属性
    String method() default "GET";            // 带默认值的属性
    boolean requireAuth() default true;
}
```

### 注解的属性类型

注解的属性（也称为成员或元素）支持以下类型：
- 基本类型（`int`、`double`、`boolean`等）
- `String`
- `Class`
- 枚举
- 注解
- 以上类型的数组

```java
enum LogLevel { DEBUG, INFO, WARN, ERROR }

public @interface Config {
    int timeout() default 30;
    String[] tags() default {};
    Class<?> handler() default Void.class;
    LogLevel level() default LogLevel.INFO;
}
```

### 使用自定义注解

```java
@ApiEndpoint(value = "/api/users", method = "POST")
public void createUser() { }

// 只有 value 属性时可以省略属性名
@ApiEndpoint("/api/users")
public void getUsers() { }
```

### 常见反例：注解"贴了但读不到"

**反例 1：漏加 `@Retention(RUNTIME)`，运行时反射读不到注解**

```java
// ❌ 反例：未显式声明 @Retention —— 默认是 RetentionPolicy.CLASS
// 注解只保留到字节码，运行时 JVM 直接丢弃，反射永远拿不到
public @interface Audit {
    String value();
}

public class OrderService {
    @Audit("createOrder")
    public void createOrder() { }

    public static void main(String[] args) throws Exception {
        Method m = OrderService.class.getMethod("createOrder");
        // ❌ 恒为 false！CLASS 保留策略下运行时不可见，切面/框架静默失效
        System.out.println(m.isAnnotationPresent(Audit.class));
    }
}

// ✅ 正例：需要反射读取的注解必须显式声明 RUNTIME
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface Audit {
    String value();
}
```

> 排查口诀：`isAnnotationPresent()` 恒返回 `false` 时，先看注解定义的 `@Retention` 是不是漏写（默认 `CLASS`），而不是怀疑反射代码。

**反例 2：误以为 `@Inherited` 对接口生效**

```java
// ❌ 反例：@Inherited 只作用于「类继承类」，对「类实现接口」无效
@Inherited
@Retention(RetentionPolicy.RUNTIME)
public @interface Tenant {
    String value();
}

@Tenant("acme")
public interface TenantAware { }          // 注解贴在接口上

public class OrderRepo implements TenantAware { }

// ❌ null！实现类不会继承接口上的注解，多租户框架按类扫描时直接漏配
System.out.println(OrderRepo.class.getAnnotation(Tenant.class));

// ✅ 正例 1：注解贴在父类上，子类才能继承
@Tenant("acme")
public abstract class BaseRepo { }
public class OrderRepo extends BaseRepo { }   // ✅ 能读到 @Tenant("acme")

// ✅ 正例 2：确实需要读接口注解时，用 AnnotatedElementUtils（Spring）递归查找
// AnnotatedElementUtils.findMergedAnnotation(OrderRepo.class, Tenant.class)
```

> 记忆点：`@Inherited` 的语义是"子类继承**父类声明**上的注解"，JDK 原生反射从不沿 `implements` 链路查找——框架（如 Spring 的 `AnnotatedElementUtils`）是自己实现了接口遍历。

## 注解的解析方法

### 编译期直接扫描

编译器在编译时扫描注解并处理。例如`@Override`，编译器会检查方法是否真的重写了父类方法。

#### 注解处理器（Annotation Processor / JSR 269）

Java 提供了 `javax.annotation.processing` 包下的注解处理器 API，允许在编译期自动扫描和处理自定义注解，甚至生成新的源代码文件。其工作流程如下：

1. 编译器启动时加载已注册的注解处理器（通过 `META-INF/services/javax.annotation.processing.Processor` 或编译参数 `-processor` 指定）
2. 每轮编译中，处理器接收被注解标注的元素，可以读取注解属性值、生成新代码或报告编译错误
3. 处理器可以多轮运行，直到没有新的源文件需要生成

**典型应用场景：**
- **Lombok**：编译期自动生成 getter/setter/builder 等样板代码
- **MapStruct**：编译期生成对象映射代码，避免手写属性拷贝
- **Dagger / Hilt**：编译期生成依赖注入代码
- **AutoValue（Google）**：编译期生成不可变值类的实现代码

#### 注解特性版本演进时间线

上文 `@Target` 表中散落的版本标注，按时间线收拢如下：

| 版本 | 关键特性 | 说明 |
|------|---------|------|
| **Java 5**（JSR 175） | 注解机制 + 元注解 | 引入 `@Override` / `@Deprecated` / `@SuppressWarnings` 与 `@Retention` / `@Target` / `@Documented` / `@Inherited` 四大元注解 |
| **Java 6**（JSR 269） | 编译期注解处理器 API | `javax.annotation.processing.Processor` + `javac -processor`，Lombok/MapStruct/Dagger 的技术地基 |
| **Java 7** | `@SafeVarargs` | 抑制堆污染（heap pollution）警告，配合泛型可变参数 |
| **Java 8**（JSR 308） | `@Repeatable` + `TYPE_PARAMETER` / `TYPE_USE` | 可重复注解；注解可贴到类型参数与任意类型使用处（如 `List<@NonNull String>`），支撑 Checker Framework 等类型检查工具 |
| **Java 9**（JPMS） | `ElementType.MODULE` | 注解可贴到 `module-info.java` 的模块声明上 |
| **Java 14/16** | `ElementType.RECORD_COMPONENT` | Record 组件级注解（Java 14 预览、Java 16 正式发布），见 [record 专题](../record/README.md) |

> 记忆锚点：**5 生（注解诞生）→ 6 处理（编译期处理器）→ 8 重复 + 类型使用 → 9 模块 → 16 Record 组件**。

### 运行期通过反射处理

通过反射 API 在运行时读取和处理注解（以下示例省略了 import 语句，实际使用时需要引入 `java.lang.annotation.Annotation`、`java.lang.reflect.Method` 等类）：

```java
// 判断方法上是否有某个注解
Method method = MyClass.class.getMethod("myMethod");
if (method.isAnnotationPresent(ApiEndpoint.class)) {
    // 获取注解实例
    ApiEndpoint annotation = method.getAnnotation(ApiEndpoint.class);
    String path = annotation.value();
    String httpMethod = annotation.method();
    System.out.println(path + " [" + httpMethod + "]");
}

// 获取类上所有注解
Annotation[] annotations = MyClass.class.getAnnotations();
for (Annotation ann : annotations) {
    System.out.println(ann);
}

// 获取直接声明在此元素上的注解（不包括从父类继承的注解）
Annotation[] declared = MyClass.class.getDeclaredAnnotations();
```

### 常用反射 API

| 方法 | 说明 |
|------|------|
| `isAnnotationPresent(Class)` | 判断是否包含指定注解 |
| `getAnnotation(Class)` | 获取指定注解实例 |
| `getAnnotations()` | 获取所有注解（包括继承的） |
| `getDeclaredAnnotations()` | 仅获取直接声明的注解（不包括继承的） |

## 注解的实际应用场景

### 1. 框架配置（Spring）

```java
@Component                        // 标记为 Spring Bean
@Service                          // 标记为服务层
@Autowired                        // 自动注入依赖
@RequestMapping("/api")           // 映射 URL
@Value("${app.name}")             // 注入配置值
```

### 2. 参数校验

```java
public class UserDTO {
    @NotBlank(message = "用户名不能为空")
    private String username;

    @Email(message = "邮箱格式不正确")
    private String email;

    @Min(value = 18, message = "年龄不能小于18")
    private int age;
}
```

### 3. AOP 切面

```java
@Aspect
@Component
public class LogAspect {
    @Around("@annotation(com.example.LogExecution)")
    public Object logMethod(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long elapsed = System.currentTimeMillis() - start;
        System.out.println(joinPoint.getSignature() + " took " + elapsed + "ms");
        return result;
    }
}
```

### 4. 单元测试（JUnit 5）

```java
@Test
@DisplayName("测试加法")
@Timeout(value = 5, unit = TimeUnit.SECONDS)
void testAdd() {
    assertEquals(3, calculator.add(1, 2));
}
```

---


## 相关章节

- [反射（Reflection）](../reflection/README.md) — 运行时注解解析的底层机制（`getAnnotation` / `isAnnotationPresent` 均由反射 API 提供）
- [SPI 服务发现机制](../spi/README.md) — 与注解处理器同为"扩展点"思想：注解处理器注册在 `META-INF/services/javax.annotation.processing.Processor`
- [Spring AOP 注解](../../../04.spring-backend/08-annotations/aop.md) — 注解 + 切面在框架层的最大应用场景（`@Aspect` / `@Around`）
- [面试题：反射深度剖析](../../../12.interview/01.java/reflection/README.md) — 注解与反射联动的高频考点

← [返回 Java 核心概念](../README.md)
