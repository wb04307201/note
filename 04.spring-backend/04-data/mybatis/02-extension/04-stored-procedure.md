<!--module:
  parent: 04.spring-backend
  slug: 04.spring-backend\04-data\mybatis\02-extension\04-stored-procedure
  type: article
  category: 主模块子文章
  summary: statementType=CALLABLE 让 MyBatis 透明调用数据库存储过程，支持 IN/OUT/INOUT 三种参数模式与游标映射
  depth: ⭐⭐⭐
  status: active
-->

# 04 存储过程调用

> 来源:整合自原 08.mybatis/README.md § 八
>
> 🎯 一句话定位：statementType=CALLABLE 让 MyBatis 透明调用数据库存储过程，支持 IN/OUT/INOUT 三种参数模式与游标映射。

## 适用场景
- **遗留系统集成**：老项目大量业务逻辑封装在存储过程中，Java 层只需透明调用
- **复杂报表统计**：多表关联 + 聚合计算在数据库端完成，减少网络传输
- **批量数据操作**：利用数据库游标和批处理提升性能

## 基本调用方式
```xml
<!-- 调用无返回值的存储过程 -->
<select id="callProcedure" statementType="CALLABLE">
    {call update_user_status(#{userId,mode=IN,jdbcType=INTEGER},
                           #{status,mode=IN,jdbcType=VARCHAR})}
</select>

<!-- 调用有返回结果的存储过程 -->
<select id="callFunction" statementType="CALLABLE" resultType="int">
    {#{result,mode=OUT,jdbcType=INTEGER} = call get_user_count()}
</select>
```

## 参数模式说明
| 模式 | 说明 | 示例 |
|------|------|------|
| IN | 输入参数 | `#{param,mode=IN}` |
| OUT | 输出参数 | `#{param,mode=OUT}` |
| INOUT | 输入输出参数 | `#{param,mode=INOUT}` |

**常用 jdbcType 枚举**：

| jdbcType | 对应 javaType | 典型场景 |
|----------|--------------|----------|
| `INTEGER` | `Integer` / `Long` | 主键、数量 |
| `VARCHAR` | `String` | 名称、描述 |
| `TIMESTAMP` | `Date` / `LocalDateTime` | 时间字段 |
| `CURSOR` | `ResultSet`（需 javaType=ResultSet） | Oracle 游标返回结果集 |
| `STRUCT` | 自定义对象 | 复杂类型参数 |

> OUT 参数常配合自定义 TypeHandler 处理类型转换，详见 [01-type-handler](01-type-handler.md)。

## 复杂存储过程处理
```xml
<!-- 调用带游标的存储过程 -->
<select id="callCursorProcedure" statementType="CALLABLE" resultMap="userResultMap">
    {call get_users_by_role(
        #{roleId,mode=IN,jdbcType=INTEGER},
        #{userCursor,mode=OUT,jdbcType=CURSOR,javaType=ResultSet,resultMap=userResultMap}
    )}
</select>

<resultMap id="userResultMap" type="User">
    <id property="id" column="id"/>
    <result property="name" column="name"/>
</resultMap>

<!-- 复杂示例：单游标返回主从嵌套结构（嵌套 resultMap，不发二次 SQL） -->
<!-- 前提：存储过程用单条 SQL（或多游标各自映射）把主从行拍平到一个结果集，
     由 MyBatis 按 <id> 聚合——切勿在 collection 里写 select=，那会退化为 N+1 嵌套查询，
     与游标/CALLABLE 无关 -->
<resultMap id="orderWithItemsResultMap" type="Order">
    <id property="id" column="order_id"/>
    <result property="userId" column="user_id"/>
    <collection property="items" ofType="OrderItem">
        <id property="id" column="item_id"/>
        <result property="skuId" column="sku_id"/>
        <result property="quantity" column="quantity"/>
    </collection>
</resultMap>
```

## 原理：CallableStatementHandler 如何处理 OUT 参数

`statementType="CALLABLE"` 时，`Configuration.newStatementHandler()` 创建的是 `CallableStatementHandler`（而非 `PreparedStatementHandler`），IN/OUT 参数在它的三个生命周期方法中流转：

```java
// org.apache.ibatis.executor.statement.CallableStatementHandler（MyBatis 3.5.x 节选）
public class CallableStatementHandler extends BaseStatementHandler {

    @Override
    protected Statement instantiateStatement(Connection connection) throws SQLException {
        // 用 prepareCall 而非 prepareStatement——这是 CALLABLE 的本质区别
        String sql = boundSql.getSql();
        if (mappedStatement.getResultSets() != null) {
            return connection.prepareCall(sql, ResultSet.TYPE_FORWARD_ONLY,
                                          ResultSet.CONCUR_READ_ONLY,
                                          ResultSet.HOLD_CURSORS_OVER_COMMIT);
        }
        return connection.prepareCall(sql);
    }

    @Override
    public void parameterize(Statement statement) throws SQLException {
        registerOutputParameters((CallableStatement) statement); // ① 先注册 OUT 参数
        parameterHandler.setParameters((CallableStatement) statement); // ② 再绑定 IN 参数
    }

    private void registerOutputParameters(CallableStatement cs) throws SQLException {
        List<ParameterMapping> parameterMappings = boundSql.getParameterMappings();
        for (int i = 0, j = 1; i < parameterMappings.size(); i++) {
            ParameterMapping parameterMapping = parameterMappings.get(i);
            // 只有 mode=OUT / INOUT 的参数才 registerOutParameter；IN 参数被跳过
            if (parameterMapping.getMode() != ParameterMode.IN) {
                TypeHandler<?> typeHandler = parameterMapping.getTypeHandler();
                JdbcType jdbcType = parameterMapping.getJdbcType();
                if (jdbcType == JdbcType.CURSOR) {
                    // Oracle 游标：注册 REF_CURSOR，执行后由 ResultSetHandler 走 resultMap 映射
                    cs.registerOutParameter(j++, jdbcType.VALUE);
                } else if (jdbcType == JdbcType.OTHER || typeHandler instanceof Jdbc3ArrayTypeHandler) {
                    cs.registerOutParameter(j++, jdbcType.VALUE, parameterMapping.getNumericScale());
                } else {
                    cs.registerOutParameter(j++, jdbcType.VALUE);
                }
                if (parameterMapping.getMode() == ParameterMode.INOUT) {
                    cs.setInt(j, i + 1); // INOUT 既要注册也要设值
                }
                if (j != i + 1) { j++; }
            }
        }
    }

    @Override
    public <E> List<E> query(Statement statement, ResultHandler resultHandler) throws SQLException {
        CallableStatement cs = (CallableStatement) statement;
        cs.execute();
        // ③ 执行后回写 OUT 参数：ResultSetHandler 内部完成
        List<E> resultList = resultSetHandler.handleResultSets(cs);
        resultSetHandler.handleOutputParameters(cs);
        return resultList;
    }
}
```

**关键链路**（对应 [08 核心类图](../01-architecture/08-class-diagram.md) §6.5 的 `localOutputParameterCache` 与 §6.6 StatementHandler）：

1. **IN 参数照常设置，OUT 参数在设参阶段被跳过**：`DefaultParameterHandler.setParameters()` 遍历 `ParameterMapping` 时，`mode=OUT` 的映射不执行 `typeHandler.setParameter()`——OUT 槽位只 `registerOutParameter`，没有值可设。
2. **执行后写回**：`DefaultResultSetHandler.handleOutputParameters()` 对每个 OUT 映射调 `typeHandler.getResult(cs, i)`，再通过 `MetaObject` 写回参数对象——参数是 `Map` 时写入对应 key（这就是 Java 示例里 `params.get("result")` 能取到值的原因），是 POJO 时写入对应属性。
3. **`localOutputParameterCache` 的角色**：当同一个 `MappedStatement` 用嵌套查询（`select=`）被多次执行时，`CachingExecutor`/`BaseExecutor` 用该缓存记住每个 `CacheKey` 对应的 OUT 参数 `ParameterMapping` 列表，保证延迟加载完成后再把 OUT 值写回正确的调用行，避免嵌套场景下输出参数错位。

> ⚠️ 游标（`jdbcType=CURSOR`）映射必须给 `resultMap`（如上文 `userCursor` 的写法），MyBatis 拿到 OUT 位置上的 `ResultSet` 后按该 resultMap 走正常的 `ResultSetHandler` 映射，等于把"嵌套 resultMap 映射结果集"复用在游标上。

## Java代码调用示例
```java
// ❌ 不推荐：finally 块手动关闭（JDK 7+ 已不推荐）
SqlSession sqlSession = sqlSessionFactory.openSession();
try {
    sqlSession.selectOne("com.example.UserMapper.callProcedure",
        Map.of("userId", 1, "status", "ACTIVE"));
} finally {
    sqlSession.close();
}

// ✅ 推荐：try-with-resources 自动关闭
try (SqlSession sqlSession = sqlSessionFactory.openSession()) {
    sqlSession.selectOne("com.example.UserMapper.callProcedure",
        Map.of("userId", 1, "status", "ACTIVE"));
}

// 带输出参数调用
try (SqlSession sqlSession = sqlSessionFactory.openSession()) {
    Map<String, Object> params = new HashMap<>();
    params.put("result", null); // 初始化OUT参数
    sqlSession.selectOne("com.example.UserMapper.callFunction", params);
    Integer count = (Integer) params.get("result");
}
```
---

## 系列导航

- 上一篇：[`03 数据库厂商扩展`](03-database-vendor.md) — 多数据库适配
- 相关主题：[`01 自定义类型处理器`](01-type-handler.md) — OUT 参数常配合自定义 TypeHandler 处理类型转换

← [返回: 02-extension](README.md)
