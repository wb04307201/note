<!--question:
  id: 01.java-sort-map
  topic: 01.java
  difficulty: ⭐⭐
  frequency: 中频
  scenario_type: 生产 Bug
  tags: [01.java, sort, map]
  status: active
-->

# 快速给Map排序

> **一句话定位**：超大数据量排序必须外排 —— 分块写入 + 块内排序 + 多路归并，避免 OOM 与全量加载。

## 引子：1 亿条数据怎么排序？

```java
Map<String, Integer> map = new HashMap<>();
// 里面有 1 亿条数据...

// 方式 1：直接 TreeMap（OOM！）
Map<String, Integer> sorted = new TreeMap<>(map);  // 内存不够

// 方式 2：Stream sorted（慢！）
map.entrySet().stream()
    .sorted(Map.Entry.comparingByValue())
    .collect(...);  // 全量加载到内存
```

数据量小时随便排，1 亿条数据时必须考虑：**内存会不会爆？单线程够不够快？排序后怎么用？**

---

> 📚 **前置知识**：[HashMap](../../../01.java-and-jvm/collection/hashmap.md) | [TreeMap](../../../01.java-and-jvm/collection/TreeMap/README.md)

## 一、核心问题分析
- **Map特性**：Java的`HashMap`无序，`TreeMap`基于红黑树实现自动排序（插入时排序），但插入1亿数据的时间复杂度为`O(n log n)`，且内存占用高（每个节点存储键值+指针，约48-64字节/节点，1亿节点需4.8-6.4GB内存）。
- **内存风险**：直接在内存中排序1亿数据可能导致`OutOfMemoryError`，需避免全量加载。
- **性能瓶颈**：单线程排序/插入效率低，需利用多核并行处理。

## 二、推荐方案：分块排序 + 归并排序（外部排序）
适用于超大数据量，避免内存溢出，步骤如下：
### 步骤1：将Map分块为多个小文件
- 遍历Map，将键值对按固定大小（如100万条/块）写入临时文件，每个文件存储序列化后的键值对（如使用`ObjectOutputStream`）。
- 示例代码：
  ```java
  Map<KeyType, ValueType> map = ...; // 原始1亿数据的Map
  int chunkSize = 1_000_000;
  List<File> chunks = new ArrayList<>();
  Iterator<Map.Entry<KeyType, ValueType>> iterator = map.entrySet().iterator();
  
  while (iterator.hasNext()) {
      File chunkFile = new File("chunk_" + chunks.size() + ".dat");
      try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(chunkFile))) {
          int count = 0;
          while (count < chunkSize && iterator.hasNext()) {
              oos.writeObject(iterator.next());
              count++;
          }
      }
      chunks.add(chunkFile);
  }
  ```

### 步骤2：对每个块进行内存排序
- 读取每个块到内存，使用`TreeMap`或流排序（`sorted()`），排序后写回临时文件。
- 示例代码：
  ```java
  for (File chunk : chunks) {
      List<Map.Entry<KeyType, ValueType>> entries = new ArrayList<>(chunkSize);
      try (ObjectInputStream ois = new ObjectInputStream(new FileInputStream(chunk))) {
          while (true) {
              entries.add((Map.Entry<KeyType, ValueType>) ois.readObject());
          }
      } catch (EOFException e) { /* 文件结束 */ }
      
      // 内存排序
      entries.sort(Map.Entry.comparingByKey());
      
      // 写回排序后的块
      File sortedChunk = new File("sorted_chunk_" + chunks.indexOf(chunk) + ".dat");
      try (ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream(sortedChunk))) {
          for (Map.Entry<KeyType, ValueType> entry : entries) {
              oos.writeObject(entry);
          }
      }
  }
  ```

### 步骤3：归并排序后的块
- 使用多线程并行归并：从每个排序后的块中读取数据，通过优先队列（堆）选择最小键值对，合并到最终输出。
- 示例代码（简化版）：
  ```java
  PriorityQueue<Map.Entry<KeyType, ValueType>> heap = new PriorityQueue<>(Comparator.comparing(Map.Entry::getKey));
  List<ObjectInputStream> streams = chunks.stream().map(file -> {
      try { return new ObjectInputStream(new FileInputStream(file)); } 
      catch (IOException e) { throw new RuntimeException(e); }
  }).collect(Collectors.toList());
  
  // 初始化堆
  for (ObjectInputStream is : streams) {
      try {
          heap.add((Map.Entry<KeyType, ValueType>) is.readObject());
      } catch (IOException | ClassNotFoundException e) {
          e.printStackTrace();
      }
  }
  
  // 归并
  while (!heap.isEmpty()) {
      Map.Entry<KeyType, ValueType> entry = heap.poll();
      // 输出到最终Map或文件
      // 尝试从对应流中读取下一个元素
      try {
          ObjectInputStream source = streams.get(streams.size() - 1); // 简化，实际需跟踪来源
          Map.Entry<KeyType, ValueType> next = (Map.Entry<KeyType, ValueType>) source.readObject();
          heap.add(next);
      } catch (EOFException e) { /* 该流已读完 */ }
  }
  ```

## 三、优化策略
- **并行处理**：使用`ParallelStream`或`ForkJoinPool`加速分块和归并。
- **内存控制**：通过`-Xmx`设置JVM最大堆内存（如`-Xmx16g`），确保分块大小适配内存。
- **序列化优化**：使用更高效的序列化库（如Kryo、FST）减少I/O开销。
- **键类型优化**：若键为基本类型（如`Long`），可改用`long[]`数组+快速排序，避免对象开销。
- **避免全量Map加载**：若数据源支持（如数据库），直接在查询时排序（`ORDER BY key`），减少Java层处理。

## 四、替代方案评估
- **TreeMap直接插入**：仅适用于小数据量，1亿数据插入时间约`1e8 * log2(1e8) ≈ 1e8 * 27 ≈ 2.7e9`次操作，耗时过高（假设1e6次操作/秒，需约30分钟），且内存占用大。
- **流排序+LinkedHashMap**：
  ```java
  Map<KeyType, ValueType> sortedMap = map.entrySet().stream()
      .sorted(Map.Entry.comparingByKey())
      .collect(Collectors.toMap(
          Map.Entry::getKey,
          Map.Entry::getValue,
          (v1, v2) -> v1, // 合并重复键（Map不允许重复）
          LinkedHashMap::new // 保持顺序
      ));
  ```
  但1亿数据在内存中排序可能导致`OutOfMemoryError`，不推荐。

## 五、关键注意事项
- **内存管理**：监控堆内存使用，避免全量加载数据。
- **I/O效率**：使用缓冲流（如`BufferedOutputStream`）减少磁盘I/O次数。
- **线程安全**：归并时确保线程安全（如使用`ConcurrentLinkedQueue`或`Phaser`同步）。
- **错误处理**：添加异常处理（如`IOException`），确保临时文件可清理。

通过分块+外部排序，可在有限内存下高效处理1亿数据，同时利用多核并行加速。实际执行时需根据硬件资源（内存、CPU核心数）调整分块大小和并行度。

## 六、常见陷阱

### 陷阱 1：归并时丢失元素来源流
- **真相**：步骤 3 的简化代码里 `streams.get(streams.size() - 1)` 永远从最后一个流补数据——归并的前提是"堆顶元素弹出后，从**它来自的那个流**读下一条"。正确做法是把 `(entry, sourceStream)` 包装成对象入堆，或用下标数组跟踪每个堆顶的来源，否则归并结果直接错乱。

### 陷阱 2：临时文件未清理
- **真相**：分块 + 排序会产生 `chunk_*.dat` 和 `sorted_chunk_*.dat` 两批临时文件，1 亿数据可能占几十 GB 磁盘。归并中途抛 `IOException` 退出时，如果没在 `finally` 里删除（或没用 `File.deleteOnExit()` / `Files.createTempFile`），磁盘会被悄悄占满——这正是第五节"错误处理：确保临时文件可清理"强调的原因。

### 陷阱 3：ObjectOutputStream 未 flush/close 导致数据截断
- **真相**：`ObjectOutputStream` 内部有 1KB 缓冲块，只 `writeObject` 不 `flush()`/`close()`，最后一个块可能没落盘，读回时数据悄悄丢失。示例代码用 try-with-resources 就是为此；另外 `ObjectInputStream` 读到底抛的是 `EOFException`，必须捕获它作为正常结束信号，而不是当错误吞掉。

### 陷阱 4：数据量不大也硬上外排 / TreeMap 全量加载 OOM
- **真相**：两个极端都会翻车。百万级以下直接 `TreeMap` 或 Stream 排序即可，上外排纯属浪费磁盘 I/O；反过来，1 亿条数据硬塞 `new TreeMap<>(map)`，每节点 48-64 字节，需要 4.8-6.4GB 内存，大概率 `OutOfMemoryError`——方案选型先看数据量级。

## 七、面试话术

### 30 秒版

> "Map 排序按数据量分档：百万级以内直接 `TreeMap` 或 Stream `sorted()` + `LinkedHashMap` 收集就够了。1 亿级必须外部排序，三步走：**分块**——按固定大小（如 100 万条/块）写入临时文件；**块内排序**——每块读进内存用 `TreeMap`/`sort()` 排好写回；**多路归并**——用优先队列（堆）从各有序块取最小元素合并输出，配合多线程并行加速。核心是任何时刻内存里只有一个块 + 一个堆，避免 OOM。"

### 90 秒版

> "先反问数据量级，这决定方案。小数据（<100 万）用 `TreeMap` 或 Stream 一行搞定，别过度设计。
>
> 1 亿条数据直接内存排序会 OOM——`TreeMap` 每个节点 48-64 字节，全量加载要 5GB 左右堆。所以走**外部排序**：
>
> **第一步分块**：遍历 Map，每 100 万条序列化写一个临时文件（`ObjectOutputStream` + 缓冲流）。
>
> **第二步块内排序**：逐块读入内存，`entries.sort(Map.Entry.comparingByKey())` 排好写回。块大小按 `-Xmx` 反推，保证峰值内存在堆的一半以内。
>
> **第三步多路归并**：为每个有序块开一个输入流，堆里放 `(元素, 来源流)` 对，每次弹出最小元素输出，再从**它的来源流**补一条——注意不能丢来源，否则归并错乱。
>
> 优化点：并行分块/归并用 ForkJoinPool；键是基本类型时改 `long[]` + 快排省对象开销；数据源是数据库时直接 `ORDER BY` 让 DB 排。
>
> 工程上三个坑必提：临时文件要在 `finally` 清理、流要 try-with-resources 保证 flush/close、`EOFException` 是正常结束信号。"

## 相关章节

- 深度阅读：[`01.java/集合框架`](../../../01.java-and-jvm/collection/README.md) — TreeMap、LinkedHashMap 源码
- 相关：[`12.interview/hashmap-resizing`](../hashmap-resizing/README.md) — HashMap 扩容

> 📅 2026-09-01 · 咬文嚼字 · Map 排序 · ⭐⭐（中频面试 + 实战必会）

← [返回: 咬文嚼字 · sort-map](../README.md)
