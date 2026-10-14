<!--question:
  id: 01.java-replace-linkedlist-with-hashset
  topic: 01.java
  difficulty: ⭐⭐⭐
  frequency: 中频
  scenario_type: 性能对比
  tags: [01.java, replace, linkedlist]
  status: active
-->

# 用 HashSet 替代 LinkedList 提升查找效率

> **一句话定位**：从 O(n) 到 O(1) 的查找跃迁 —— 含黑名单、权限校验、去重等场景，速度提升数千到数万倍。

## 引子：从 5 秒到 0.1 毫秒

```java
// 场景：在 10 万条数据中，对 1 万个目标值逐一判断是否存在
LinkedList<String> list = new LinkedList<>();
// ... 添加 10 万条数据

// 单次 contains 平均遍历 5 万个节点，约 500 us（见 §一 表格）
// 1 万次查询总耗时 ≈ 10000 × 500us ≈ 5 秒
for (String target : targets) {
    boolean exists = list.contains(target);
}

// 换成 HashSet
HashSet<String> set = new HashSet<>(list);
// 单次 contains 直接哈希定位，约 0.01 us
// 1 万次查询总耗时 ≈ 0.1 毫秒（不含构建 set 的一次性 O(n)）
for (String target : targets) {
    boolean exists = set.contains(target);
}
```

同样的批量"是否存在"查询，LinkedList 要 5 秒，HashSet 只要 0.1 毫秒——**约 5 万倍的差距**（与 §一 表格 100,000 规模 50000x 一致；单次查询也是 500 us vs 0.01 us 的量级差）。

这就是 O(n) 和 O(1) 的区别。

---

> 📚 **前置知识**：[HashMap](../../../01.java-and-jvm/collection/hashmap.md) | [LinkedList](../../../01.java-and-jvm/collection/LinkedList/README.md)

## 一、核心原理

在数据结构选择中，**用 `HashSet` 替代 `LinkedList` 优化查找操作**是从 O(n) 到 O(1) 的质的飞跃。

### 1. LinkedList 的查找机制
- **线性遍历：** `LinkedList.contains()` 需要从头部逐个节点比对，平均需要遍历 n/2 个节点，时间复杂度为 **O(n)**。
- **缓存不友好：** 链表节点在堆中分散分配，遍历时频繁跳跃访问不同内存地址，导致 CPU 缓存命中率低。
- **适用场景：** 仅在头部/尾部插入删除（O(1)）、有序遍历、或按索引顺序访问时表现良好。

### 2. HashSet 的查找机制
- **哈希寻址：** `HashSet.contains()` 通过 `hashCode()` 计算桶索引，再通过 `equals()` 确认元素，平均时间复杂度为 **O(1)**。
- **退化风险：** 当哈希函数设计不佳导致大量冲突时，同一桶内的元素形成链表/红黑树（Java 8+），最坏情况退化为 O(log n) 或 O(n)。但优质哈希算法下概率极低。
- **空间换时间：** HashSet 内部维护一个数组（默认容量 16，负载因子 0.75），额外占用约 30%-50% 的内存，换取常数级查找速度。

### 3. 性能差距量化

| 数据规模 | LinkedList 查找耗时 | HashSet 查找耗时 | 倍数差异 |
|----------|---------------------|------------------|----------|
| 1,000    | ~5 us               | ~0.01 us         | 500x     |
| 10,000   | ~50 us              | ~0.01 us         | 5000x    |
| 100,000  | ~500 us             | ~0.01 us         | 50000x   |
| 1,000,000| ~5 ms               | ~0.01 us         | 500000x  |

---

## 二、代码示例

以下展示从 LinkedList 迁移到 HashSet 的完整过程及性能对比：

```java
import java.util.*;
import java.util.concurrent.ThreadLocalRandom;

public class LookupBenchmark {
    private static final int SIZE = 100_000;
    private static final int QUERIES = 10_000;

    private static List<String> prepareList() {
        List<String> list = new LinkedList<>();
        for (int i = 0; i < SIZE; i++) list.add("item_" + i);
        return list;
    }

    private static Set<String> prepareSet() {
        Set<String> set = new HashSet<>();
        for (int i = 0; i < SIZE; i++) set.add("item_" + i);
        return set;
    }

    public static void main(String[] args) {
        List<String> list = prepareList();
        Set<String> set = prepareSet();
        List<String> queries = generateQueries();

        long start = System.nanoTime();
        int listHits = 0;
        for (String q : queries) {
            if (list.contains(q)) listHits++;  // O(n)
        }
        long listTime = System.nanoTime() - start;
        System.out.printf("LinkedList: %d hits, %.2f ms%n", listHits, listTime / 1e6);

        start = System.nanoTime();
        int setHits = 0;
        for (String q : queries) {
            if (set.contains(q)) setHits++;   // O(1)
        }
        long setTime = System.nanoTime() - start;
        System.out.printf("HashSet:    %d hits, %.4f ms%n", setHits, setTime / 1e6);
        System.out.printf("加速比: %.0fx%n", (double) listTime / setTime);
    }

    private static List<String> generateQueries() {
        ThreadLocalRandom random = ThreadLocalRandom.current();
        List<String> queries = new ArrayList<>(QUERIES);
        for (int i = 0; i < QUERIES; i++) {
            if (random.nextBoolean()) {
                queries.add("item_" + random.nextInt(SIZE));
            } else {
                queries.add("missing_" + random.nextInt(SIZE));
            }
        }
        return queries;
    }
}

// 典型输出：
// LinkedList: 5012 hits, 2847.35 ms
// HashSet:    5012 hits, 0.8234 ms
// 加速比: 3458x
```

### 实际业务场景示例

```java
// 反模式：使用 LinkedList
public class BlacklistServiceBad {
    private List<String> blacklist = new LinkedList<>();
    public void loadBlacklist(List<String> users) { blacklist.addAll(users); }
    public boolean isBlocked(String userId) {
        return blacklist.contains(userId); // O(n)，每次调用遍历全表
    }
}

// 推荐：使用 HashSet
public class BlacklistServiceGood {
    private Set<String> blacklist = new HashSet<>();
    public void loadBlacklist(List<String> users) { blacklist.addAll(users); }
    public boolean isBlocked(String userId) {
        return blacklist.contains(userId); // O(1)，瞬时返回
    }
    public void addToBlacklist(String userId) { blacklist.add(userId); }
    public void removeFromBlacklist(String userId) { blacklist.remove(userId); }
}
```

---

## 三、常见陷阱

### 1. 忽视 hashCode() 和 equals() 的正确实现

```java
// 错误：只覆写 equals，未覆写 hashCode
public class User {
    private String email;
    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof User)) return false;
        return Objects.equals(email, ((User) o).email);
    }
    // 缺少 hashCode -> HashSet 无法正确定位桶位置
}

// 正确：同时覆写
public class User {
    private String email;
    @Override
    public boolean equals(Object o) { /* 同上 */ }
    @Override
    public int hashCode() { return Objects.hash(email); }
}
```

**原则：** 若 `a.equals(b)` 为 true，则 `a.hashCode()` 必须等于 `b.hashCode()`。

### 2. 可变对象作为 HashSet 元素

```java
// 危险：修改对象的 hashCode 依赖字段
Set<User> set = new HashSet<>();
User user = new User("alice@example.com");
set.add(user);
user.setEmail("bob@example.com");  // 修改后 hashCode 改变
System.out.println(set.contains(user)); // false！无法找到

// 推荐：使用不可变对象或不可变字段
public final class User {
    private final String email; // final 保证不可变
    public User(String email) { this.email = email; }
    @Override public int hashCode() { return Objects.hash(email); }
}
```

### 3. 内存溢出 / 4. 线程安全 / 5. 顺序问题

**内存：** HashSet 内存占用约为 LinkedList 的 1.5-2 倍。大数据量场景下可能触发 OOM，需使用有界缓存。

**线程安全：** 多线程并发需用 `Collections.synchronizedSet(new HashSet<>())` 或 `ConcurrentHashMap.newKeySet()`（Java 8+）。

**顺序：** HashSet 不保证顺序。需要插入顺序时用 `LinkedHashSet`；需要排序用 `TreeSet`。

```java
// 有界缓存（LRU 淘汰）
Set<String> cache = Collections.newSetFromMap(
    new LinkedHashMap<String, Boolean>(1000, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, Boolean> eldest) {
            return size() > 10000;
        }
    }
);

// 线程安全
Set<String> concurrentSet = ConcurrentHashMap.newKeySet();

// 保持插入顺序
Set<String> orderedSet = new LinkedHashSet<>();
```

---

## 四、最佳实践

### 1. 初始化容量预估

避免频繁扩容带来的性能损耗：

```java
// 预估需要存储 10,000 个元素，负载因子 0.75
// 初始容量 = 10000 / 0.75 + 1 ≈ 13334
Set<String> set = new HashSet<>(13334);
```

### 2. 选择合适的数据结构组合

| 需求场景 | 推荐数据结构 | 理由 |
|----------|--------------|------|
| 快速查找 + 无序 | `HashSet` | O(1) 查找 |
| 快速查找 + 插入顺序 | `LinkedHashSet` | O(1) 查找 + 顺序保证 |
| 快速查找 + 排序 | `TreeSet` | O(log n) 查找 + 自然排序 |
| 键值映射 | `HashMap` | O(1) 查找 + 关联值 |

### 3. 利用 Stream API 简化集合转换

```java
// List -> Set（去重 + 快速查找）
List<String> list = Arrays.asList("a", "b", "a", "c");
Set<String> set = list.stream().collect(Collectors.toSet());

// 批量过滤
List<String> filtered = list.stream()
    .filter(set::contains)  // O(1) 判断
    .collect(Collectors.toList());
```

### 4. 大数据量场景的替代方案

当元素数量超过百万级时，考虑：
- **Roaring Bitmap：** 适用于整数集合，压缩率高且支持位运算。
- **Bloom Filter：** probabilistic 数据结构，极小内存判断"可能存在"或"一定不存在"。

```java
// Bloom Filter 示例（Guava）
BloomFilter<String> bloom = BloomFilter.create(
    Funnels.stringFunnel(Charset.UTF_8), 1_000_000, 0.01);
bloom.put("user_123");
boolean mightExist = bloom.mightContain("user_123"); // true（可能误判）
```

---

## 五、面试话术（30 秒版 + 90 秒版）

**面试官：** "为什么用 HashSet 替代 LinkedList 做查找？"

**30 秒版**：

> "核心是查找复杂度差异：LinkedList.contains 线性遍历 O(n)，HashSet 哈希定位平均 O(1)。10 万条规模单次查询约 500 us vs 0.01 us，批量查询差距可达数万倍。适用场景是黑名单过滤、权限校验、去重——超过几千条就该换。代价是内存多占 30%-50% + 必须正确实现 hashCode/equals；要保持插入顺序或排序则用 LinkedHashSet / TreeSet。"

**90 秒版**：

> "核心原因是**查找复杂度的本质差异**。LinkedList 的 contains 操作需要线性遍历，时间复杂度是 O(n)；而 HashSet 基于哈希表，平均时间复杂度是 O(1)。
>
> 底层机制上：LinkedList 节点在堆中分散分配，遍历是跳跃式访存，CPU 缓存命中率低，还有每节点两个指针的额外开销；HashSet 通过 hashCode 算桶索引 + equals 确认，Java 8 起桶内冲突链表超过 8（TREEIFY_THRESHOLD=8）转红黑树，最坏也是 O(log n) 而非 O(n)。
>
> 在实际项目中，如黑名单过滤、权限校验、去重判断等场景，一旦超过几千条，HashSet 的优势就体现出来了。我之前做过一个用户标签系统，原来用 ArrayList 存几万条用户 ID，每次校验都要 5-10 毫秒，改成 HashSet 后降到 0.01 毫秒，提升了三个数量级。
>
> 当然，HashSet 也有代价：一是内存占用更高（约多 30%-50%）；二是需要正确实现 hashCode 和 equals——equals 相等的对象 hashCode 必须一致，否则 contains 会漏判。如果业务需要保持插入顺序或排序，我会选择 LinkedHashSet 或 TreeSet；海量整数集合还可以考虑 Roaring Bitmap，允许误判的预过滤场景用 Bloom Filter。"

**加分项：** 提及 Java 8 中 HashMap 链表转红黑树的阈值（TREEIFY_THRESHOLD=8）。

---

## 六、交叉引用

- HashMap/HashSet 源码分析见 [集合框架](../../../01.java-and-jvm/collection/hashmap.md)
- hashCode 和 equals 契约见 [Java 对象方法](../../../01.java-and-jvm/01-language/object/README.md)
- 并发安全的 Set 实现见 [并发容器](../../../01.java-and-jvm/03-concurrency/concurrent-collections/README.md)

## 相关章节

- 深度阅读：[`01.java-and-jvm`](../../../01.java-and-jvm/README.md) — 主模块详细内容

> 📅 2026-09-01 · 咬文嚼字 · HashSet 替代 LinkedList · ⭐⭐⭐（中频面试 + 实战必会）

← [返回: 咬文嚼字 · replace-linkedlist-with-hashset](../README.md)
