<!--module:
  parent: spring/mybatis/02-extension
  slug: spring/mybatis/02-extension/01-type-handler
  type: article
  category: MyBatis 内部原理
  summary: TypeHandler 是 MyBatis 在 Java 类型与 JDBC 类型之间的双向转换桥——注册查找顺序、枚举处理选型、JSON 字段实战
  depth: ⭐⭐⭐
  status: active
  tags: [MyBatis, TypeHandler, 类型转换, 枚举]
-->

# 01 自定义类型处理器(TypeHandler)

> 来源:整合自原 08.mybatis/README.md § 七.7.1
>
> 🎯 一句话定位：TypeHandler 是 MyBatis 在 Java 类型与 JDBC 类型之间的双向转换桥。

## §1 内置与自定义

> ❌ **不注册直接用 `java.util.Date`**：MyBatis 默认把 `Date` 当 `TIMESTAMP` 处理，但若数据库列类型为 `DATE`/`TIME`，取值时精度丢失（时分秒截断）甚至报 `TypeException`。
> ✅ **注册自定义 `DateTypeHandler`**：明确指定 `javaType` + `jdbcType` 映射，保证双向转换精度。

```java
// BaseTypeHandler 4 个核心方法职责：
// 1. setNonNullParameter  — 写参数到 PreparedStatement（Java → JDBC）
// 2. getNullableResult(rs, columnName) — 按列名读结果（JDBC → Java）
// 3. getNullableResult(rs, columnIndex) — 按列索引读结果（JDBC → Java）
// 4. getNullableResult(cs, columnIndex) — 从 CallableStatement 读 OUT 参数（存储过程场景）
public class DateTypeHandler extends BaseTypeHandler<Date> {
    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, Date parameter, JdbcType jdbcType) throws SQLException {
        ps.setTimestamp(i, new Timestamp(parameter.getTime()));
    }

    @Override
    public Date getNullableResult(ResultSet rs, String columnName) throws SQLException {
        Timestamp timestamp = rs.getTimestamp(columnName);
        return timestamp != null ? new Date(timestamp.getTime()) : null;
    }

    @Override
    public Date getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        Timestamp timestamp = rs.getTimestamp(columnIndex);
        return timestamp != null ? new Date(timestamp.getTime()) : null;
    }

    @Override
    public Date getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        // 存储过程 OUT 参数入口——本目录 04-stored-procedure 依赖此重载，不可省略
        Timestamp timestamp = cs.getTimestamp(columnIndex);
        return timestamp != null ? new Date(timestamp.getTime()) : null;
    }
}
```

> ⚠️ 三个 `getNullableResult` 重载都要实现：列名映射、列索引映射、存储过程 `CallableStatement`（OUT 参数）走不同入口，缺任何一个都会在对应场景抛 `UnsupportedOperationException` 或返回错误值。完整的对称扩展示例（`EmailTypeHandler`）见 [08-class-diagram §实战源码片段 4](../01-architecture/08-class-diagram.md)。

**配置方式**:

```xml
<typeHandlers>
    <typeHandler handler="com.example.DateTypeHandler" javaType="java.util.Date"/>
</typeHandlers>
```

**Spring Boot 注册方式**（替代 XML 手工配置）：

```yaml
mybatis:
  type-handlers-package: com.example.handler
```

> 通过 `@Configuration` + `mybatis.type-handlers-package` 可扫描整个包自动注册，无需逐条声明。

---

## §2 TypeHandlerRegistry 查找顺序

所有 TypeHandler 都注册在 `Configuration.typeHandlerRegistry` 中——一个**两级 Map**：`Map<Class<?> javaType, Map<JdbcType, TypeHandler>>`。运行期查找（`getTypeHandler`）按以下优先级**逐级降级**：

```java
// 查找优先级（TypeHandlerRegistry.getTypeHandler 简化逻辑）：
// 1. javaType + jdbcType 精确匹配 —— 注册时显式声明了两者的 handler
// 2. javaType + null jdbcType     —— 只按 Java 类型注册（@MappedJdbcTypes 未声明或 includeNullJdbcType=true）
// 3. jdbcType 兜底                —— Java 类型没注册过时，尝试按 JdbcType 找（ObjectTypeHandler 等）
// 4. 仍找不到                     —— 返回 null，抛 "Type handler was not found" 类异常
```

**排障要点**：

| 现象 | 常见原因 |
|------|---------|
| 自定义 handler 不生效 | `@MappedJdbcTypes(JdbcType.VARCHAR)` 缩小了作用域——ResultMap 解析时 JDBC 类型未知，按 `javaType + null` 查找会错过它；加 `includeNullJdbcType = true` 或去掉该注解 |
| 同一 Java 类型多个 handler 互相覆盖 | 后注册者胜出；用 `jdbcType` 区分（如 `Date` → `TIMESTAMP`/`DATE`/`TIME` 分别对应内置 3 个 handler） |
| 包扫描没生效 | `mybatis.type-handlers-package` 只扫描实现类；泛型 handler 需 `@MappedTypes` 标注（自动扫描无法内省实际类型参数） |

> 注：自 MyBatis 3.4.0 起，如果一个 Java 类型**只注册了一个** TypeHandler，即使未设 `includeNullJdbcType=true`，ResultMap 中也会默认使用它。

---

## §3 枚举处理：EnumTypeHandler vs EnumOrdinalTypeHandler

MyBatis 内置两个枚举 handler，选型是**数据兼容性**问题而非风格问题：

| 维度 | `EnumTypeHandler`（默认） | `EnumOrdinalTypeHandler` |
|------|--------------------------|--------------------------|
| 存储内容 | 枚举 `name()` 字符串（VARCHAR） | 枚举 `ordinal()` 序号（INTEGER） |
| 可读性 | ✅ 数据库里直接可读、可 SQL 过滤 | ❌ 只有数字，需查代码对照 |
| **枚举重命名** | ❌ 旧数据字符串对不上，反序列化抛异常 | ✅ 不受影响 |
| **枚举顺序变更/中间插入** | ✅ 不受影响 | ❌ **序号整体错位——静默脏数据** |
| 存储体积 | 略大 | 小 |

```xml
<!-- 全局默认即 EnumTypeHandler；切换为按序号存储需显式注册 -->
<typeHandlers>
    <typeHandler handler="org.apache.ibatis.type.EnumOrdinalTypeHandler"
                 javaType="java.math.RoundingMode"/>
</typeHandlers>

<!-- 也可在 3.4.5+ 用 settings 全局改默认 -->
<settings>
    <setting name="defaultEnumTypeHandler"
             value="com.example.handler.MyEnumTypeHandler"/>
</settings>
```

**各自的陷阱**：

- `EnumTypeHandler`：**重命名枚举常量 = 破坏历史数据**。若必须改名，要么写数据迁移脚本 `UPDATE` 旧值，要么自定义 handler 维护"别名 → 枚举"映射。
- `EnumOrdinalTypeHandler`：**绝对禁止在枚举中间插入/删除/重排常量**——`ordinal()` 全部后移，已入库的数字含义静默改变，且无任何报错。这是生产事故高发点。
- 两难时的第三条路：**自定义 handler 存业务码**（如 `code` 字段），枚举顺序和名称都可自由重构：

```java
// 存业务码而非 name/ordinal——重构安全的枚举存储方案
public class CodeEnumTypeHandler<E extends Enum<E> & HasCode> extends BaseTypeHandler<E> {
    private final Class<E> type;
    private final Map<Integer, E> codeMap; // 启动时构建 code → 枚举 索引

    public CodeEnumTypeHandler(Class<E> type) {
        this.type = type;
        this.codeMap = Arrays.stream(type.getEnumConstants())
                .collect(Collectors.toMap(HasCode::getCode, e -> e));
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, E parameter, JdbcType jdbcType) throws SQLException {
        ps.setInt(i, parameter.getCode()); // Java → JDBC：写业务码
    }

    @Override
    public E getNullableResult(ResultSet rs, String columnName) throws SQLException {
        int code = rs.getInt(columnName);
        return rs.wasNull() ? null : codeMap.get(code); // JDBC → Java：按码查表
    }
    // 其余两个重载同理...
}
```

---

## §4 JSON 字段 TypeHandler 实战（MySQL JSON 列 ↔ Java 对象）

半结构化字段（如商品扩展属性、订单快照）存 MySQL `JSON` 列时，用自定义 handler 在**列值字符串**与 **Java 对象**之间做序列化。以 Jackson 为例：

```java
// 泛型基类：任意 POJO ↔ JSON 字符串列
// 注册时需配合 @MappedTypes 或 XML javaType 指定具体类型（泛型擦除无法内省）
public class JacksonTypeHandler<T> extends BaseTypeHandler<T> {
    private static final ObjectMapper MAPPER = new ObjectMapper();
    private final Class<T> type;

    public JacksonTypeHandler(Class<T> type) {           // MyBatis 构造泛型 handler 时会传入实际 Class
        this.type = Objects.requireNonNull(type);
    }

    @Override
    public void setNonNullParameter(PreparedStatement ps, int i, T parameter, JdbcType jdbcType) throws SQLException {
        try {
            ps.setString(i, MAPPER.writeValueAsString(parameter)); // Java 对象 → JSON 字符串写入 JSON 列
        } catch (JsonProcessingException e) {
            throw new SQLException("序列化 " + type.getSimpleName() + " 失败", e);
        }
    }

    @Override
    public T getNullableResult(ResultSet rs, String columnName) throws SQLException {
        return parse(rs.getString(columnName));          // JSON 字符串 → Java 对象
    }

    @Override
    public T getNullableResult(ResultSet rs, int columnIndex) throws SQLException {
        return parse(rs.getString(columnIndex));
    }

    @Override
    public T getNullableResult(CallableStatement cs, int columnIndex) throws SQLException {
        return parse(cs.getString(columnIndex));
    }

    private T parse(String json) throws SQLException {
        if (json == null) {
            return null;
        }
        try {
            return MAPPER.readValue(json, type);
        } catch (JsonProcessingException e) {
            // 显式抛异常而非静默返回 null——脏 JSON 应尽早暴露
            throw new SQLException("反序列化 " + type.getSimpleName() + " 失败: " + json, e);
        }
    }
}
```

**ResultMap 中绑定具体类型**（泛型 handler 必须显式指定，不能靠自动映射）：

```xml
<resultMap id="productMap" type="Product">
    <id property="id" column="id"/>
    <!-- attrs 是 MySQL JSON 列，映射到 Map<String,Object> / 自定义 POJO 均可 -->
    <result property="attrs" column="attrs"
            typeHandler="com.example.handler.ProductAttrsTypeHandler"/>
</resultMap>

<!-- 具体化泛型的子类：把 Class 固定传给基类构造器 -->
<!-- public class ProductAttrsTypeHandler extends JacksonTypeHandler<ProductAttrs> {
         public ProductAttrsTypeHandler() { super(ProductAttrs.class); }
     } -->
```

> 💡 **现成轮子**：MyBatis-Plus 的 `com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler` 已实现同样机制（实体字段加 `@TableField(typeHandler = JacksonTypeHandler.class)` + `@TableName(autoResultMap = true)`），使用 MyBatis-Plus 的项目无需自写；纯 MyBatis 项目则按上面模板自建。参见 [04-mybatis-plus](../04-mybatis-plus/README.md)。

**JSON 列的边界**：JSON 字段**不能被 WHERE 高效过滤**（MySQL 需虚拟列 + 索引才可用）；需要按属性查询的字段应拆列存储，JSON 列只放真正的"整存整取"扩展数据。

---

## 系列导航

- 深入阅读：[`08 核心类图与职责链路`](../01-architecture/08-class-diagram.md) — §1.7 ParameterHandler 与「实战源码片段 4：参数与结果 TypeHandler 的对称扩展」展示入参/出参两条路径如何汇合到本类
- 下一篇：[`02 拦截器`](02-interceptor.md) — 插件机制与四大拦截点

← [返回: 02-extension](README.md)
