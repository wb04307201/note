<!--module:
  parent: 04.spring-backend
  slug: 04.spring-backend/04-data/mybatis/02-extension/03-database-vendor
  type: article
  category: 主模块子文章
  summary: DatabaseIdProvider 让同一 Mapper 按数据库厂商切换 SQL——DB_VENDOR 的 contains 匹配机制、databaseId 加载优先级与覆盖陷阱
  depth: ⭐⭐⭐
  status: active
  tags: [MyBatis, DatabaseIdProvider, 多数据库, SQL 方言]
-->

# 03 数据库厂商扩展(DatabaseIdProvider)

> 来源:整合自原 08.mybatis/README.md § 七.7.3

## 核心机制
`DatabaseIdProvider` 允许 MyBatis 根据当前数据库类型执行不同的 SQL 语句，实现**一套代码适配多种数据库**。

工作原理：
1. MyBatis 启动时通过 `DatabaseIdProvider` 检测当前数据库的 `DatabaseProductName`
2. 将产品名映射为简短的 `databaseId`（如 `MySQL` → `mysql`）
3. 加载 Mapper XML 时，优先匹配 `databaseId` 一致的语句；无匹配则加载无 `databaseId` 的通用语句

## 配置方式
### 2.1 mybatis-config.xml 配置

```xml
<databaseIdProvider type="DB_VENDOR">
    <property name="MySQL" value="mysql"/>
    <property name="Oracle" value="oracle"/>
    <property name="PostgreSQL" value="pg"/>
    <property name="SQL Server" value="mssql"/>
</databaseIdProvider>
```

### 2.2 Spring Boot 配置

原生 MyBatis（`mybatis-spring-boot-starter`）注册的是一个 `DatabaseIdProvider` **Bean**，而不是 yaml 属性：

```java
@Configuration
public class MyBatisConfig {
    @Bean
    public DatabaseIdProvider databaseIdProvider() {
        VendorDatabaseIdProvider provider = new VendorDatabaseIdProvider();
        Properties properties = new Properties();
        properties.setProperty("MySQL", "mysql");
        properties.setProperty("Oracle", "oracle");
        properties.setProperty("PostgreSQL", "pg");
        properties.setProperty("SQL Server", "mssql");
        provider.setProperties(properties);
        return provider;
    }
}
```

> 自动配置的 `MybatisAutoConfiguration` 检测到容器中存在 `DatabaseIdProvider` Bean 时会注入 `SqlSessionFactoryBean`。

**若项目用的是 MyBatis-Plus**（`mybatis-plus-boot-starter`，本篇主题是原生 MyBatis，注意区分）：starter 的配置前缀为 `mybatis-plus:` 而非 `mybatis:`，但两个 starter 都**没有**通过 yaml 直接声明 `database-id-provider` 的属性绑定入口——`DatabaseIdProvider` 一律按上面的 Java Bean 方式注册，由自动配置类（`MybatisAutoConfiguration` / `MybatisPlusAutoConfiguration`）自动注入。

## 源码机制：VendorDatabaseIdProvider.getDatabaseId()

`type="DB_VENDOR"` 对应的内置实现是 `VendorDatabaseIdProvider`，其匹配逻辑解释了后文「精确匹配 vs contains」注意事项的由来：

```java
// org.apache.ibatis.mapping.VendorDatabaseIdProvider（MyBatis 3.5.x 节选）
public class VendorDatabaseIdProvider implements DatabaseIdProvider {

    private Properties properties;

    @Override
    public String getDatabaseId(DataSource dataSource) {
        if (dataSource == null) {
            throw new NullPointerException("dataSource cannot be null");
        }
        try {
            return getDatabaseName(dataSource);
        } catch (Exception e) {
            LogFactory.getLog(getClass()).error("Could not get a databaseId from dataSource", e);
        }
        return null;
    }

    private String getDatabaseName(DataSource dataSource) throws SQLException {
        // 第一步：通过 JDBC 元数据拿数据库产品名，如 "MySQL" / "Oracle" / "PostgreSQL"
        String productName = getDatabaseProductName(dataSource);
        if (this.properties != null) {
            // 第二步：遍历配置的 key，只要 productName.contains(key) 就命中，返回对应 value
            for (Map.Entry<Object, Object> property : properties.entrySet()) {
                if (productName.contains((String) property.getKey())) {
                    return (String) property.getValue();
                }
            }
            // 配置了 properties 但一个都没命中 → 返回 null（全部走无 databaseId 的通用语句）
            return null;
        }
        // 未配置 properties → 直接返回产品名本身作为 databaseId
        return productName;
    }

    private String getDatabaseProductName(DataSource dataSource) throws SQLException {
        try (Connection con = dataSource.getConnection();
             DatabaseMetaData metaData = con.getMetaData()) {
            return metaData.getDatabaseProductName();
        }
    }
}
```

两个关键结论：

1. **key 匹配是 `contains`（子串匹配），不是相等**——所以 `"SQL Server"` 能命中产品名 `"Microsoft SQL Server"`；反过来配置 key 过短（如 `"S"`）会误命中多个产品，且 `Properties` 遍历顺序不保证，**多 key 命中时结果不确定**。
2. **XML 里 `databaseId="mysql"` 与语句的比对才是精确匹配**（`Configuration.databaseId.equals(statementDatabaseId)`）——`contains` 只发生在「产品名 → databaseId」这一步。

## 使用方式
```xml
<!-- MySQL 专用：使用 LIMIT -->
<select id="selectTopUsers" resultType="User" databaseId="mysql">
    SELECT * FROM user ORDER BY score DESC LIMIT #{limit}
</select>

<!-- Oracle 专用：使用 ROWNUM -->
<select id="selectTopUsers" resultType="User" databaseId="oracle">
    SELECT * FROM (
        SELECT u.*, ROWNUM rn FROM user u ORDER BY score DESC
    ) WHERE rn &lt;= #{limit}
</select>

<!-- 通用：无 databaseId，作为兜底 -->
<select id="selectUserById" resultType="User">
    SELECT * FROM user WHERE id = #{id}
</select>
```

## 匹配优先级
| 优先级 | 条件 | 说明 |
|--------|------|------|
| 1（最高） | `databaseId` 匹配当前数据库 | 专用 SQL |
| 2 | 无 `databaseId` 属性 | 通用 SQL 兜底 |
| 3（不会加载） | `databaseId` 不匹配 | 被忽略 |

> ❌ **反例：以为"带 databaseId 的版本只是补充，无 databaseId 的版本还在兜底"**——同 id 语句两种版本并存时，只要带 `databaseId` 的版本匹配成功，**无 `databaseId` 的版本就会被丢弃**（`XMLStatementBuilder` 加载阶段决定，不是运行期选择）。真实案例：团队为 MySQL 写了分页专用版 `selectTopUsers`（带 `databaseId="mysql"`），保留了原来的通用版（无 `databaseId`）当"默认实现"；后来迁移到 PostgreSQL，以为会自动落回通用版，结果启动直接报 `Invalid bound statement (not found)`——因为通用版在 MySQL 环境加载时就已被专用版覆盖丢弃，Configuration 里根本不存在无 databaseId 的版本。
>
> ✅ 正确心智模型：同 id 语句是"**加载期二选一**"——当前 databaseId 有匹配则**只保留**匹配版本，无 databaseId 版本被静默丢弃；仅当没有任何匹配版本时，无 databaseId 版本才会被加载。所以通用兜底版只在"目标厂商没有专用版"时才存在，别指望它在有专用版的数据库上还能兜底。

## 适用场景与注意事项
| 场景 | 建议 |
|------|------|
| 单数据库项目 | 不需要 `DatabaseIdProvider`，增加复杂度 |
| 多数据库兼容产品 | 必备：为不同数据库的 SQL 方言提供差异化实现 |
| 分页差异 | MySQL `LIMIT` vs Oracle `ROWNUM` vs SQL Server `TOP` |
| 函数差异 | MySQL `IFNULL` vs Oracle `NVL` vs PG `COALESCE` |
| 日期函数 | MySQL `DATE_FORMAT` vs Oracle `TO_CHAR` |

**注意**：`databaseId` 匹配是**精确匹配**，`DB_VENDOR` 使用 `DatabaseProductName.contains(key)` 判断（源码见上文 §VendorDatabaseIdProvider.getDatabaseId()）。

---

## 相关章节

- 前置：[`01 框架本质`](../01-architecture/01-framework-essence.md)
- 关联：[`02 初始化流程`](../01-architecture/02-initialization-flow.md) — Configuration 加载过程
- 对比：[`MyBatis 动态 SQL`](../01-architecture/05-dynamic-sql.md) — 另一种 SQL 差异化方案
---

- 系列导航：上一篇 [`02 拦截器`](02-interceptor.md) · 下一篇 [`04 存储过程`](04-stored-procedure.md)

← [返回: 02-extension](README.md)
