<!--module:
  parent: 01.java
  slug: 01.java/kotlin/05-coroutines
  type: article
  category: 主模块子文章
  summary: Kotlin 协程的挂起恢复机制、调度器实现、结构化并发、Flow 与 Channel。
  depth: ⭐⭐
  status: active
-->

# Kotlin 协程与异步

> **一句话定位**：Kotlin 协程通过挂起函数与调度器实现轻量级并发，并以结构化并发约束任务生命周期。

## 一、协程基础

协程是轻量级的"用户态线程"，可在单个线程上运行百万级协程，而 Java 线程通常只能支持几千个。

```java
// Java — 每个线程占用 ~1MB 栈内存
new Thread(() -> {
    System.out.println("Running");
}).start();
```

```kotlin
// Kotlin — 协程对象通常远小于平台线程，但实际占用取决于捕获状态
coroutineScope {
    launch {
        delay(1000)              // 非阻塞挂起，不占用线程
        println("Hello after 1s")
    }
}
```

### 核心构建块

| 函数 | 作用 | 返回值 |
|------|------|--------|
| `launch` | 启动协程，不返回结果 | `Job` |
| `async` | 启动协程，返回结果 | `Deferred<T>` |
| `runBlocking` | 阻塞当前线程等待协程完成 | 仅用于桥接阻塞代码与协程 |
| `delay` | 挂起协程（非阻塞睡眠） | — |

```kotlin
val deferred = async { computeResult() }
// 做其他事...
val result = deferred.await()    // 等待结果
```

### 挂起原理：Continuation 与状态机

`suspend` 函数在编译期被转换为 **CPS（Continuation-Passing Style）**形式：编译器为函数追加一个 `Continuation<T>` 参数，并把函数体改写为**标签驱动的状态机**——每个挂起点（`delay`、`await` 等）对应一个 `label` 分支。

```kotlin
// 源码
suspend fun loadUser(): User {
    val token = fetchToken()     // 挂起点 1
    val user = fetchUser(token)  // 挂起点 2
    return user
}

// 编译后的等价形态（简化示意）
fun loadUser(continuation: Continuation<User>): Any? {
    when (continuation.label) {
        0 -> {
            continuation.label = 1
            val r = fetchToken(continuation)      // 传入自身作为回调
            if (r == COROUTINE_SUSPENDED) return COROUTINE_SUSPENDED
            // 未真正挂起则继续落入下一分支
        }
        1 -> {
            continuation.label = 2
            val r = fetchUser(continuation.token, continuation)
            if (r == COROUTINE_SUSPENDED) return COROUTINE_SUSPENDED
        }
        2 -> return continuation.result
    }
}
```

关键机制：

- **挂起 = 返回 `COROUTINE_SUSPENDED` 并释放线程**：局部变量被提升为 Continuation 对象的字段保存在堆上，因此挂起不阻塞线程——这就是单线程可跑百万协程的原因。
- **恢复 = `continuation.resumeWith(result)`**：异步回调完成后调用，状态机按 `label` 跳回对应分支继续执行。
- **恢复线程由 Dispatcher 决定**：`Continuation` 被包装为 `DispatchedContinuation`，`resume` 时按拦截器链（`ContinuationInterceptor`，即 `CoroutineDispatcher`）把后续计算投递到目标线程池——`Dispatchers.IO` 共享 `Default` 的线程池但上限更宽（默认 64），`Unconfined` 则在调用者线程直接执行。

## 二、结构化并发

协程通过 `CoroutineScope` 形成父子层级树，父协程取消时自动取消所有子协程，防止泄漏。

```kotlin
suspend fun fetchData(): String = coroutineScope {
    val user = async { api.getUser() }
    val posts = async { api.getPosts() }
    "${user.await()} has ${posts.await().size} posts"
}
// 任一 async 失败，整个 coroutineScope 取消
```

### 异常处理

```kotlin
supervisorScope {
    launch {
        // 此协程失败不影响其他兄弟
        throw RuntimeException("failed")
    }
    launch {
        // 正常执行
        println("I'm still running")
    }
}
```

- 普通 `coroutineScope`：子协程失败 → 全部取消（失败传播）
- `supervisorScope`：子协程独立运行，一个失败不影响其他

## 三、调度器 `Dispatcher`

| 调度器 | 适用场景 |
|--------|---------|
| `Dispatchers.Default` | CPU 密集型计算（并行度 = CPU 核心数） |
| `Dispatchers.IO` | I/O 密集型（网络、文件、数据库） |
| `Dispatchers.Main` | Android UI 线程 |
| `Dispatchers.Unconfined` | 不限制线程（测试用） |

```kotlin
launch(Dispatchers.IO) {
    val data = readFile()        // 在 I/O 线程池执行
    withContext(Dispatchers.Main) {
        updateUI(data)           // 切回主线程
    }
}
```

## 四、Flow 流式处理

`Flow` 是协程版的响应式流，冷流（只在被收集时才发射数据）。

```kotlin
// 构建
fun numbersFlow() = flow {
    for (i in 1..3) {
        delay(100)
        emit(i)
    }
}

// 收集
numbersFlow()
    .map { it * 2 }
    .filter { it > 2 }
    .collect { println(it) }    // 4, 6
```

### `flowOn` 切换上下文

```kotlin
flow { emit(dataFromDb()) }
    .flowOn(Dispatchers.IO)     // 上游在 I/O 线程
    .collect { updateUI(it) }   // 下游在收集者线程
```

### 异常处理

```kotlin
flow { emit(parseData()) }
    .catch { e -> emit(defaultValue) }    // 捕获上游异常
    .onCompletion { cause -> if (cause != null) println("Failed") }
    .collect { process(it) }
```

## 五、StateFlow / SharedFlow 热流

热流始终活跃，多个收集者共享同一数据源。

```kotlin
class ViewModel {
    private val _state = MutableStateFlow(0)
    val state: StateFlow<Int> = _state.asStateFlow()    // 只读暴露

    fun increment() { _state.value++ }
}

// 收集 — StateFlow 始终有当前值
lifecycleScope.launch {
    viewModel.state.collect { println("State: $it") }
}
```

- `StateFlow`：持有最新值，新收集者立即收到当前值（类似 LiveData）
- `SharedFlow`：事件广播，可配置回放数量和缓冲区

## 六、Channel 通道

Channel 是协程间的通信管道，对比 Java `BlockingQueue`。

```kotlin
val channel = Channel<Int>()

launch {
    for (i in 1..5) {
        channel.send(i * 2)    // 生产者
    }
    channel.close()
}

launch {
    for (value in channel) {   // 消费者
        println(value)
    }
}
```

> **对比**：`BlockingQueue` 阻塞线程，`Channel` 挂起协程。Channel 更适合协程间的细粒度数据传递，Flow 更适合数据流的变换与收集。

---

## 系列导航

| 序号 | 主题 | 核心问题 |
|------|------|---------|
| 01 | [基础语法](01-basics.md) | 基础语法、类型系统、空安全、控制流、异常 |
| 02 | [面向对象](02-oop.md) | 类与对象、泛型、继承、可见性 |
| 03 | [函数式](03-functional.md) | 函数、集合、函数式、作用域函数 |
| 04 | [高级特性](04-advanced.md) | 扩展、委托、操作符、内联、值类、DSL |
| 05 | [协程](05-coroutines.md) | 协程、Flow、Channel、结构化并发 |
| 06 | [工程实践](06-engineering.md) | Java 互操作、KMP、构建工具、迁移策略 |

← [返回: Kotlin](../README.md)
