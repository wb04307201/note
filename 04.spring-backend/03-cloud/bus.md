<!--module:
  parent: 04.spring-backend
  slug: 04.spring-backend/03-cloud/bus
  type: article
  category: 主模块子文章
  summary: Spring Cloud Bus 集群事件总线
  depth: ⭐⭐⭐
  status: active
-->

# Spring Cloud Bus 集群事件总线

> ⬅️ [返回 05 Spring Cloud](README.md) | [Stream](stream.md) | [Config 中心](config-center.md)

**Spring Cloud Bus** 用**轻量级消息代理**（Kafka / RabbitMQ）连接分布式系统的**所有节点**，通过单一指令触发**全集群广播**。最经典用途：**Spring Cloud Config 配置实时刷新**。

---

## 一、用途

| 场景 | 说明 |
|------|------|
| **Config 实时推送** | Git 仓库配置变更后，触发一次 `/actuator/busrefresh`，全集群节点收到通知并刷新 `@RefreshScope` Bean |
| **集群广播** | 自定义事件投递到所有实例（如缓存清理、灰度指令） |
| **运维指令** | 批量重启、热加载证书、动态日志级别 |

---

## 二、传输依赖

```xml
<!-- Kafka transport -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-bus-kafka</artifactId>
</dependency>

<!-- 或 RabbitMQ transport -->
<dependency>
    <groupId>org.springframework.cloud</groupId>
    <artifactId>spring-cloud-bus-amqp</artifactId>
</dependency>
```

二者**二选一**，不可同时引入。

---

## 三、配置

```yaml
spring:
  cloud:
    bus:
      enabled: true
      destination: spring-cloud-bus   # 默认 topic / exchange 名
      ack:
        enabled: true                # 开启 ack 确认
  kafka:
    bootstrap-servers: localhost:9092

management:
  endpoints:
    web:
      exposure:
        include: busrefresh,busenv   # 暴露 actuator 端点
```

---

## 四、关键端点

| 端点 | 方法 | 作用 |
|------|------|------|
| `/actuator/busrefresh` (POST) | 全集群刷新配置 | 所有节点重新拉取 Config |
| `/actuator/busrefresh/{destination}` | 指定服务刷新 | 仅 `service-id:**` 节点刷新 |
| `/actuator/busevent/{event}` (POST) | 自定义事件广播 | 投递任意 JSON 到所有节点 |

### 示例：触发刷新

```bash
# 触发全集群配置刷新
curl -X POST http://config-server:8080/actuator/busrefresh

# 仅刷新 order-service 实例
curl -X POST http://config-server:8080/actuator/busrefresh/order-service:**
```

---

## 五、与 Nacos Config 长轮询对比

| 维度 | Spring Cloud Bus | Nacos Config |
|------|------------------|--------------|
| **传输** | Kafka / RabbitMQ | Nacos Server（HTTP 长轮询） |
| **触发方式** | 调用 `/actuator/busrefresh` 主动推送 | 客户端长轮询自动感知变更 |
| **运维依赖** | 需额外部署 Kafka / RabbitMQ | 仅需 Nacos（注册+配置二合一） |
| **延迟** | 100ms ~ 数秒 | 取决于轮询间隔（默认 30s 长轮询） |
| **适合场景** | Spring Cloud Config 配套、已有 Kafka | 国内主流、追求一站式 |

**结论**：2026 年新项目**首选 Nacos Config**（详见 [config-center.md](config-center.md)），Bus 仅在已有 Kafka 基础设施 + 使用 Spring Cloud Config 时推荐。

---

## 六、自定义事件广播

```java
// 1. 自定义事件（继承 RemoteApplicationEvent）
public class CacheClearEvent extends RemoteApplicationEvent {
    private String cacheName;

    // Jackson 反序列化需要无参构造器（跨服务传输时必需）
    public CacheClearEvent() {
    }

    public CacheClearEvent(Object source, String originService, String cacheName) {
        super(source, originService);
        this.cacheName = cacheName;
    }

    public String getCacheName() {
        return cacheName;
    }

    public void setCacheName(String cacheName) {
        this.cacheName = cacheName;
    }
}

// 2. 发布事件（applicationEventPublisher 必须显式声明并注入）
@Service
public class CacheClearPublisher {
    private final ApplicationEventPublisher applicationEventPublisher;

    public CacheClearPublisher(ApplicationEventPublisher applicationEventPublisher) {
        this.applicationEventPublisher = applicationEventPublisher;
    }

    public void clearCache(String name) {
        CacheClearEvent event = new CacheClearEvent(this, null, name);
        applicationEventPublisher.publishEvent(event);
    }
}

// 3. 监听事件（本地发布 + Bus 跨服务广播都会触发）
@Slf4j
@Component
public class CacheClearListener {
    private final CacheManager cacheManager;

    public CacheClearListener(CacheManager cacheManager) {
        this.cacheManager = cacheManager;
    }

    @EventListener
    public void onEvent(CacheClearEvent event) {
        log.info("收到集群广播: 清空缓存 {}", event.getCacheName());
        Cache cache = cacheManager.getCache(event.getCacheName());
        if (cache != null) {
            cache.clear();
        }
    }
}
```

> 📌 自定义事件默认不在 Bus 的扫描范围内，需在发布方启动类（或配置类）加 `@RemoteApplicationEventScan("com.example.bus.event")` 声明事件所在包，Bus 才会把它序列化后经 Kafka/RabbitMQ 广播到其他服务。

---

## 相关章节

- ⬅️ [返回 05 Spring Cloud](README.md)
- [Config 中心](config-center.md) — Spring Cloud Config + Bus 经典组合
- [Spring Cloud Stream](stream.md) — 业务消息驱动
- [Spring Cloud 与 Alibaba 关系](README.md#spring-cloud-与-spring-cloud-alibaba-关系)

- [config-encryption](config-encryption.md)

← [返回: Spring Cloud](README.md)
