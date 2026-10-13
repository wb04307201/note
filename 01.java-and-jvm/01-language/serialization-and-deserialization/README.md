<!--module:
  parent: java
  slug: java/concepts/serialization
  type: article
  category: 主模块子文章
  summary: Java 序列化：Serializable、Externalizable、serialVersionUID。
  depth: ⭐⭐⭐⭐
  status: active
-->

# 序列化和反序列化

---

> **一句话定位**：序列化把对象转字节流以便存储或传输，反序列化再还原；`serialVersionUID` 与协议选型决定兼容性。

- **序列化**：将数据结构或对象转换成二进制字节流的过程
- **反序列化**：将序列化过程中生成的二进制字节流还原成数据结构或对象的过程

## 为什么需要序列化和反序列化

```mermaid
graph LR
    Obj[Object] --> Bytes[Bytes]
    Bytes --> DB[(DB)]
    Bytes --> File[📄 File]
    Bytes --> Mem[💾 Memory]
    Bytes --> Cloud[☁️ Cloud]

    DB --> Bytes2[Bytes]
    File --> Bytes2
    Mem --> Bytes2
    Cloud --> Bytes2
    Bytes2 --> Obj2[Object]

    classDef obj fill:#e3d2ff
    classDef bytes fill:#2c3e50,color:#fff
    classDef storage fill:#d4edda

    class Obj,Obj2 obj
    class Bytes,Bytes2 bytes
    class DB,File,Mem,Cloud storage
```

1. **数据持久化**：将内存中的对象状态保存到文件、数据库等存储介质
2. **远程通信**：在分布式系统中通过网络传输对象（如 RPC 调用）
3. **对象状态保存与恢复**：实现撤销/重做功能、会话恢复等
4. **数据交换**：不同系统之间交换数据（如 JSON、XML 格式）
5. **内存管理优化**：将不常用数据序列化到磁盘，释放内存空间

## 序列化的基本概念

Java 提供了内置的序列化机制，核心要素：

- **`Serializable`接口**：标记接口，标识一个类可以被序列化
- **`Externalizable`接口**：继承自 `Serializable`，提供 `writeExternal()` 和 `readExternal()` 方法，允许完全自定义序列化逻辑，性能通常优于默认序列化机制
- **`serialVersionUID`**：用于版本兼容性校验，防止序列化/反序列化版本不一致
- **`transient`关键字**：标记不需要序列化的字段

## 序列化的实现

```java
// User.java
import java.io.Serializable;

public class User implements Serializable {
    private static final long serialVersionUID = 1L;
    private String name;
    private int age;
    private transient String password;  // 不参与序列化

    public User(String name, int age, String password) {
        this.name = name;
        this.age = age;
        this.password = password;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public int getAge() { return age; }
    public void setAge(int age) { this.age = age; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }

    @Override
    public String toString() {
        return "User{name='" + name + "', age=" + age + ", password='" + password + "'}";
    }
}
```

```java
// SerializationDemo.java
import java.io.ObjectOutputStream;
import java.io.ObjectInputStream;
import java.io.FileOutputStream;
import java.io.FileInputStream;

public class SerializationDemo {
    public static void main(String[] args) {
        // 序列化
        User user = new User("Tom", 18, "secret123");
        try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream("user.ser"))) {
            oos.writeObject(user);
        } catch (Exception e) {
            e.printStackTrace();
        }

        // 反序列化
        try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream("user.ser"))) {
            User deserializedUser = (User) ois.readObject();
            System.out.println(deserializedUser);
            // 验证 transient 字段：输出 "secret123" 说明序列化前有值，输出 "null" 说明 transient 生效
            System.out.println("password (transient): " + deserializedUser.getPassword()); // 输出 null
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### 流协议头与默认实现要点（源码级）

**1. 流协议头（Stream Header）**：`ObjectOutputStream` 构造时立即向流写入 4 字节魔数——这是"打开流就写头，而不是第一次 writeObject 才写"的细节：

```text
AC ED 00 05
│   │  └──── streamVersion = 5（STREAM_VERSION，协议版本号）
│   └─────── magic 低字节
└─────────── magic 高字节（STREAM_MAGIC = 0xACED）
```

对应 `ObjectOutputStream` 源码（`writeStreamHeader()`，`protected` 可被子类覆盖）：

```java
protected void writeStreamHeader() throws IOException {
    bout.writeShort(STREAM_MAGIC);     // 0xACED
    bout.writeShort(STREAM_VERSION);   // 5
}
```

`ObjectInputStream` 构造时对称地 `readStreamHeader()` 校验：魔数不符抛 `StreamCorruptedException`，版本号不符抛 `InvalidClassException("local class incompatible: stream version, ...")`。因此用十六进制查看器打开 `user.ser`，**前 4 个字节必然是 `AC ED 00 05`**——这也是识别 Java 原生序列化流量（安全审计/gadget 攻击排查）的第一指纹。

**2. `writeObject`/`readObject` 的默认行为**：

- `Serializable` 未提供 `writeObject` 时走 `defaultWriteObject()` 路径：按 `ObjectStreamClass` 中登记的**非 static、非 transient 字段**逐个写入（字段元数据先于字段值写进流，含类名 + `serialVersionUID` + 字段描述）
- 类可以声明 `private void writeObject(ObjectOutputStream out)` / `readObject(ObjectInputStream in)` 接管——`ObjectStreamClass` 通过**反射查找该精确签名**（名字 + 修饰符 + 参数类型全部匹配，否则静默忽略，这是常见踩坑点）
- 惯例是先调 `out.defaultWriteObject()` / `in.defaultReadObject()` 处理常规字段，再手工写附加数据（如集合防御性拷贝）
- 反序列化**不调用任何构造方法**（除 `Externalizable` 要求公共无参构造器外）：对象内存直接分配，字段由流数据填充；`readResolve()` 在字段填充完成后执行，可整体替换返回对象

## 应用场景

- **对象持久化**：文件存储、Redis 缓存、数据库存储
- **网络传输**：RPC 调用、消息队列、HTTP API
- **分布式计算**：不同节点之间传递对象

### 序列化协议在 TCP/IP 模型中的位置

```text
┌─────────────────────────────────────────────────────────┐
│                OSI 七层协议          TCP/IP 四层协议      │
├─────────────────────────────────────────────────────────┤
│   7 应用层         ┐              应用层  ┌──────────────
│   6 表示层（序列化）│ ◄── 对应 ─│（Telnet/FTP/SMTP/HTTP）│
│   5 会话层         ┘                     └──────────────┘
│   4 运输层                       运输层（TCP/UDP）        │
│   3 网络层                       网际层（IP）             │
│   2 数据链路层                    网络接口层              │
│   1 物理层                       网络接口层              │
└─────────────────────────────────────────────────────────┘
```

序列化协议属于 TCP/IP 协议**应用层**的一部分，对应 OSI 七层模型中的**表示层**（负责数据的编码/解码）。

## 注意事项

1. **版本兼容性**：类结构变更后，旧的序列化数据可能无法正确反序列化。务必维护好`serialVersionUID`

   **❌/✅ 演进示例——缺失 `serialVersionUID` 导致 `InvalidClassException`**：

   ```java
   // ❌ 反例：未显式声明 serialVersionUID（v1 版本，已上线并写入缓存/文件）
   public class Order implements Serializable {
       private long orderId;
       private String status;
   }
   // JVM 按类名+接口+字段+方法签名自动计算 UID，假设为 8821104821955035702L

   // ❌ v2 仅新增一个无关字段——自动 UID 随之改变
   public class Order implements Serializable {
       private long orderId;
       private String status;
       private String remark;   // 新增字段
   }
   // 自动计算 UID 变成 -3460125747287946791L

   // 用 v2 类反序列化 v1 数据 → 直接炸：
   // java.io.InvalidClassException: Order;
   //   local class incompatible: stream classdesc serialVersionUID = 8821104821955035702,
   //   local class serialVersionUID = -3460125747287946791
   ```

   ```java
   // ✅ 正例：显式固定 serialVersionUID
   public class Order implements Serializable {
       private static final long serialVersionUID = 1L;  // 永不随手改
       private long orderId;
       private String status;
       private String remark;   // v2 新增字段：反序列化旧数据时取类型默认值（null/0），兼容
   }
   ```

   兼容性规则（UID 一致前提下）：**新增字段** ✅ 兼容（旧数据读出为默认值）；**删除字段** ✅ 兼容（多余数据被忽略）；**修改字段类型**（`int`→`String`）❌ 不兼容（`ClassCastException`/`InvalidClassException`）；**`serialVersionUID` 本身变更** ❌ 必炸。语义上不兼容的大改（字段含义变化）应主动升级 UID 拒绝旧数据。IDEA 开启 `Settings → Inspections → Serializable class without 'serialVersionUID'` 可自动提醒；用 `serialver com.example.Order` 命令可查自动计算值。

2. **性能影响**：序列化和反序列化可能消耗大量资源，大数据场景需谨慎
3. **安全风险**：反序列化可能执行恶意代码，需验证数据来源和完整性。Java 9 引入了 **ObjectInputFilter**（JEP 290）作为防御反序列化攻击的核心机制，可设置白名单/黑名单限制可反序列化的类：
   ```java
   // 方式一：代码中设置 ObjectInputFilter
   ObjectInputFilter filter = ObjectInputFilter.Config.createFilter(
       "com.example.*;java.base/*;!*"); // 白名单 + 黑名单
   try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream("data.ser"))) {
       ois.setObjectInputFilter(filter);
       Object obj = ois.readObject(); // 只允许指定包下的类被反序列化
   }

   // 方式二：JVM 启动参数全局配置
   // java -Djdk.serialFilter="com.example.*;java.base/*;!*" MyApp
   ```
4. **字段过滤**：使用`transient`标记敏感或无需持久化的字段
5. **循环引用**：对象之间的循环引用可能导致序列化失败或数据膨胀
6. **readResolve() 与 writeReplace()**：
   - `readResolve()`：在反序列化完成后被调用，可替换反序列化得到的对象。常用于**单例模式**，确保反序列化后仍返回同一实例：
     ```java
     public class Singleton implements Serializable {
         private static final Singleton INSTANCE = new Singleton();
         private Singleton() {}
         // 保证反序列化后仍为同一实例
         private Object readResolve() { return INSTANCE; }
     }
     ```
   - `writeReplace()`：在序列化前被调用，可替换待序列化的对象。常用于**序列化代理模式**（Effective Java 推荐），通过一个内部代理类来安全地完成序列化，避免真实对象直接暴露序列化细节

### 现代 Java 与序列化

Java 16 正式引入的 **Record 类型**（Java 14/15 为预览特性，JEP 359/384/395）天然支持序列化，但其行为与普通类有所不同（Record 本身的语法与约束见 [record/README.md](../record/README.md)）：

- Record 和普通类一样**必须实现 `Serializable` 接口**才能被序列化。实现 `Serializable` 后，所有组件（components）会被自动序列化，无需手动编写序列化逻辑
- Record 的序列化/反序列化由 **JVM 运行时**自动处理。如果在 Record 中定义 `writeObject`/`readObject` 等方法会被**忽略**，序列化行为仅基于组件和规范构造方法（canonical constructor）
- 反序列化时通过**规范构造方法**重建对象，确保不可变性得到保持
- 这一设计避免了传统 Java 序列化中常见的安全风险和自定义逻辑带来的复杂性

## 序列化框架对比

### 主流框架速查表

| 框架 | 格式 | 跨语言 | 性能 | 数据大小 | Schema | 主要场景 |
|------|------|--------|------|---------|--------|---------|
| **Jackson** | JSON | ✅ | 中 | 大 | 不需要 | Web API、RESTful 服务 |
| **Fastjson2** | JSON | ❌ | 高 | 大 | 不需要 | 国内 Web 开发 |
| **Gson** | JSON | ✅ | 中 | 大 | 不需要 | 简单 JSON 处理 |
| **Protobuf** | 二进制 | ✅ | 极高 | 极小 | 需要 | 微服务、gRPC |
| **Kryo** | 二进制 | ❌ | 极高 | 小 | 不需要 | 高性能 Java 内部通信 |
| **Hessian** | 二进制 | ✅ | 高 | 小 | 不需要 | Dubbo RPC、跨语言 |
| **Thrift** | 二进制 | ✅ | 极高 | 小 | 需要 | 跨语言 RPC |
| **Avro** | 二进制 | ✅ | 高 | 小 | 可选 | 大数据（Kafka/Hadoop） |
| **Java 原生** | 二进制 | ❌ | 低 | 大 | 不需要 | 简单 Java 内部使用 |

### 主流 JSON 框架详解

#### Jackson

最流行的 Java JSON 库，Spring Boot 默认使用：

```java
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import java.text.SimpleDateFormat;

// User user = new User("Tom", 18, "secret123"); // 从上下文获取

ObjectMapper mapper = new ObjectMapper();
try {
    // 序列化
    String json = mapper.writeValueAsString(user);

    // 反序列化
    User deserializedUser = mapper.readValue(json, User.class);

    // 高级用法
    mapper.enable(SerializationFeature.INDENT_OUTPUT);  // 格式化输出
    mapper.setDateFormat(new SimpleDateFormat("yyyy-MM-dd"));  // 日期格式
} catch (Exception e) {
    e.printStackTrace();
}
```

#### Fastjson2

阿里巴巴开源，国内使用广泛，性能优秀：

```java
import com.alibaba.fastjson2.JSON;

// User user = new User("Tom", 18, "secret123"); // 从上下文获取

// 序列化
String json = JSON.toJSONString(user);

// 反序列化
User deserializedUser = JSON.parseObject(json, User.class);
```

#### Gson

Google 开发，API 简洁：

```java
import com.google.gson.Gson;

// User user = new User("Tom", 18, "secret123"); // 从上下文获取

Gson gson = new Gson();

// 序列化
String json = gson.toJson(user);

// 反序列化
User deserializedUser = gson.fromJson(json, User.class);
```

### 主流二进制框架详解

#### Protobuf（Protocol Buffers）

Google 开发，跨语言跨平台，gRPC 底层协议：

```protobuf
// user.proto
message User {
    string name = 1;
    int32 age = 2;
    string email = 3;
}
```

```java
// 使用生成的代码
User user = User.newBuilder()
    .setName("Tom")
    .setAge(18)
    .setEmail("tom@example.com")
    .build();

byte[] bytes = user.toByteArray();  // 序列化
User parsed = User.parseFrom(bytes); // 反序列化
```

#### Kryo

高性能 Java 专用序列化框架，Spark/Flink 等大数据框架内部使用：

```java
import com.esotericsoftware.kryo.Kryo;
import com.esotericsoftware.kryo.io.Input;
import com.esotericsoftware.kryo.io.Output;

// User user = new User("Tom", 18, "secret123"); // 从上下文获取

Kryo kryo = new Kryo();
kryo.register(User.class);

// 序列化
byte[] bytes;
try (Output output = new Output(1024)) {
    kryo.writeObject(output, user);
    bytes = output.toBytes();
}

// 反序列化
try (Input input = new Input(bytes)) {
    User deserialized = kryo.readObject(input, User.class);
}
```

#### Hessian

轻量级跨语言二进制协议，Dubbo 2.x 默认序列化协议。Dubbo 3.x 的 Triple 协议默认使用 **Protobuf** 序列化（兼容 gRPC），Hessian 仍可作为可选配置使用：

```java
import com.caucho.hessian.io.Hessian2Output;
import com.caucho.hessian.io.Hessian2Input;
import java.io.ByteArrayOutputStream;
import java.io.ByteArrayInputStream;

// User user = new User("Tom", 18, "secret123"); // 从上下文获取

try {
    // 序列化
    ByteArrayOutputStream bos = new ByteArrayOutputStream();
    Hessian2Output out = new Hessian2Output(bos);
    out.writeObject(user);
    out.close();
    byte[] bytes = bos.toByteArray();

    // 反序列化
    ByteArrayInputStream bis = new ByteArrayInputStream(bytes);
    Hessian2Input in = new Hessian2Input(bis);
    User deserialized = (User) in.readObject();
    in.close();
} catch (Exception e) {
    e.printStackTrace();
}
```

### 如何选择序列化框架

```text
需要跨语言通信？
├── 是 → 需要 Schema 定义？
│   ├── 是 → Protobuf / Thrift
│   └── 否 → Hessian / Jackson(JSON)
└── 否 → 纯 Java 高性能？
    ├── 是 → Kryo
    └── 否 → 与 Web/API 交互？
        ├── 是 → Jackson / Fastjson2
        └── 否 → Java 原生（简单场景）
```

## 性能对比

> **说明**：以下只给**定性排序**（相对快慢档位）。具体数值与柱状 benchmark 高度依赖对象大小、字段类型、JVM 版本与硬件环境，脱离出处的绝对数字没有意义；需要精确选型时用 JMH 针对真实业务对象自测。

| 档位 | 序列化方案 | 相对速度 | 数据大小 | 备注 |
|------|-----------|---------|---------|------|
| 第一档（最快） | Kryo、FST | ★★★★★ | 小 | 纯 Java 二进制，需注册类获得最佳性能 |
| 第一档（最快） | Protobuf、Thrift | ★★★★★ | 极小 | 需要 Schema，跨语言，gRPC 底层 |
| 第二档 | Hessian2、Avro | ★★★★ | 小 | Hessian 是 Dubbo 2.x 默认协议 |
| 第三档 | Fastjson2 / Jackson（JSON） | ★★★ | 大 | 文本格式可读性好，Web API 首选 |
| 第四档（最慢） | Java 原生序列化 | ★ | 大 | 流格式冗长 + 反射开销，仅限简单内部场景 |

**一般规律**：二进制格式 > JSON 格式 > XML 格式（在序列化速度和数据大小方面）

---

## 相关章节

- [record/README.md](../record/README.md) — Record 类型的完整语法与约束（上文"现代 Java 与序列化"的 Record 序列化行为在其类型体系中的定位）
- [I/O](../../io/README.md) — 序列化的字节流最终经由 I/O 通道落盘/传输，`ObjectOutputStream` 等流 API 的基础
- [反射](../reflection/README.md) — Java 原生序列化底层依赖反射遍历字段与调用构造方法

---

## 相关面试题

- [生产 NoClassDefFoundError 排查全链路](../../../12.interview/01.java/no-class-def-found-troubleshooting/README.md) — fastjson 2.0.64 的 `<clinit>` 急初始化陷阱 + `AwtRederModule`（注意上游类名拼写，少一个 a）位于 `fastjson2-extension` 独立 jar 的部署确定性治理

---

← [返回 Java 核心概念](../README.md)
