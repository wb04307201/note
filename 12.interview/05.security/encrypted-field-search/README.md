<!--question:
  id: 05.security-encrypted-field-search
  topic: 05.security
  difficulty: ⭐⭐⭐⭐
  frequency: 高频
  scenario_type: 反直觉代码
  tags: [05.security, encryption, PII, searchable encryption, HMAC, 保序加密, 同态加密]
  status: active
-->

# 加密字段还能模糊搜索吗？—— PII 数据可搜索加密方案

> 一句话定位：手机号 / 身份证加密后**不是不能搜**，而是需要**为「不同查询类型」选「不同方案」**：等值用 HMAC 截断索引、模糊匹配用末 N 位索引、范围用 OPE、任意查询用 FHE。完整深度见 [主模块加密 §可搜索加密](../../../06.distributed-systems/05-security/encryption/README.md#模式-4可搜索加密searchable-encryption)。

> **系列定位**：经典安全 / 后端架构面试题（字节 / 阿里 / 美团 / 滴滴 出题率 70%+）。考察的不是「要不要加密」，而是 **「加密后还能不能搜」+「怎么搜」+「不同方案怎么选」**。

---

## 引子：以为加密后就不能搜的初学者误区

面试官：「你们项目用户手机号怎么存的？」

候选人 A：**「加密存。」**

面试官：「那用户输入后四位怎么查询？」

候选人 A 卡壳：「呃…把全部手机号解开再比？」

面试官继续追问：「真要全表解密？那 100 万用户每次查询都要解密 100 万次？」

候选人 A 哑口无言。

**反直觉**：加密后**不是不能搜**，而是**要按查询类型选方案**。以为「加密 = 不可搜」是初学者误区——也是面试必追问点。

---

## 一、核心原理

### 1.1 加密 vs 搜索的根本矛盾

| 维度 | 加密（Ciphertext） | 明文搜索 |
|------|-------------------|---------|
| **可逆性** | 可逆（有密钥） | — |
| **可搜索性** | 不可直接搜索 | 直接 `LIKE` / `REGEXP` |
| **目的** | 机密性 | 业务查询 |

**矛盾本质**：加密追求「不可读」，搜索追求「可查」——两者目标天然对立。

### 1.2 6 大方案 × 5 大查询类型矩阵

| 查询类型 | 业务场景 | 推荐方案 | 方案原理 |
|---------|---------|---------|---------|
| **等值** | `WHERE phone = ?` | **HMAC-SHA256 完整索引** | 同一明文 → 同一 HMAC |
| **模糊匹配** | `WHERE phone LIKE '%1234'` | **HMAC 末 N 位索引** | 截取 HMAC 末 4 字节 |
| **前缀** | `WHERE phone LIKE '138%'` | **HMAC + Trie 索引** | 分段索引 |
| **范围** | `WHERE age BETWEEN 20 AND 30` | **OPE 保序加密** OR **全表解密** | 保留明文顺序 |
| **聚合** | `GROUP BY city` | **HMAC 索引** OR **不加密** | 密文聚合无意义 |
| **任意查询** | 任意 SQL | **FHE 同态加密** | 密文上计算（极慢） |

### 1.3 反直觉 1：HMAC 截断索引 ≠ 真加密

- HMAC 是**单向哈希**，不是加密（**不可逆**）
- 同一明文 → 同一 HMAC → **可被字典攻击**（常见手机号如 `13800138000` 命中率极高）
- **缓解**：HMAC + 长盐（per-user 或 per-record salt）+ 长截断（≥ 16 字节）

### 1.4 反直觉 2：保序加密 OPE 牺牲安全性

- OPE 保留明文顺序 → **频率分析可破解**（如「1980-01-01」对应密文在某范围）
- **适用**：低敏感数据（年龄、地区、入职日期）
- **禁用**：高敏感数据（身份证、手机号、银行卡）

### 1.5 反直觉 3：同态加密 FHE 是银弹但慢 10⁵-10⁶ 倍

- FHE 可在密文上计算 → 任意查询都能做
- 性能：**加法慢 1000 倍、乘法慢 10⁵-10⁶ 倍**（vs 明文）
- 实战：**99% 业务用不到**，仅极小数据 + 极端合规才用

---

## 二、代码示例

### 2.1 HMAC 末 N 位索引（手机号后四位模糊搜索）

```java
// 1. AES 加密存储（AES-256-GCM）
public String encryptPhone(String phone, SecretKey dek) {
    byte[] iv = SecureRandom.getInstanceStrong().generateSeed(12);
    Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
    cipher.init(Cipher.ENCRYPT_MODE, dek, new GCMParameterSpec(128, iv));
    byte[] ct = cipher.doFinal(phone.getBytes(StandardCharsets.UTF_8));
    return Base64.getEncoder().encodeToString(iv) + ":" +
           Base64.getEncoder().encodeToString(ct);
}

// 2. HMAC 末 4 位索引（模糊搜索用）
public String phoneLast4Index(String phone, byte[] hmacKey) {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(hmacKey, "HmacSHA256"));
    byte[] hash = mac.doFinal(phone.getBytes(StandardCharsets.UTF_8));
    // 取末 4 字节 = 8 个 hex 字符 ≈ 4 位数字搜索空间（65536 种可能）
    String hex = HexFormat.of().formatHex(hash);
    return hex.substring(hex.length() - 8);
}

// 3. 搜索流程（用户输入手机号后 4 位）
public List<User> searchByLast4(String userInputLast4, byte[] hmacKey) {
    // 关键：用户只知道后 4 位，必须「补全成完整手机号 → HMAC → 取末 4 位」
    String fullPhone = "138****" + userInputLast4;
    String hashed = phoneLast4Index(fullPhone, hmacKey);
    return userRepo.findByPhoneLast4Index(hashed);  // SELECT * WHERE phone_last4_idx = ?
}

// 4. SQL 表设计
// CREATE TABLE users (
//   id BIGINT PRIMARY KEY,
//   phone_enc TEXT,           -- AES 加密的手机号密文（防 DBA）
//   phone_last4_idx CHAR(8),  -- HMAC 末 4 位索引（建 B+ 树索引，防字典攻击）
//   phone_full_idx CHAR(32)   -- HMAC 完整手机号索引（等值查询用，加 per-user 盐）
// );
```

### 2.2 保序加密 OPE（年龄范围查询）

```java
// OPE 库：mCrypt / AWS Cryptography / Google Cloud DPE
public BigInteger opeEncrypt(int plaintext, byte[] key) {
    Ope ope = new Ope(key);
    return ope.encrypt(BigInteger.valueOf(plaintext));
}

// 范围查询（OPE 密文范围 = 明文范围）
// SELECT * FROM users WHERE age_ope BETWEEN opeEncrypt(20) AND opeEncrypt(30)

// 注意：OPE 暴露了顺序 → 不能用 SELECT DISTINCT 看分布（暴露频率）
// 不能用 SELECT MIN/MAX 看极值（暴露明文范围）
```

### 2.3 同态加密 FHE（银弹方案，极慢）

```java
// FHE 库：Microsoft SEAL / Google FHE Transpiler / Lattigo
public EncryptedNumber fheEncrypt(int value, PublicKey pk) {
    return FHE.encrypt(value, pk);
}

// 密文计算（不解密！）
public EncryptedNumber fheAdd(EncryptedNumber a, EncryptedNumber b) {
    return FHE.add(a, b);
}

// 性能对比（vs 明文）：
// 加法：FHE ~1ms vs 明文 ~1μs（慢 1000 倍）
// 乘法：FHE ~100ms vs 明文 ~1μs（慢 10 万倍）
// 实测：100 万行范围查询，FHE 方案需要 CPU 烧数小时 → 生产不可用
```

---

## 三、常见陷阱（5 大反模式）

### 陷阱 1：直接对密文做 LIKE 查询

- 错：`SELECT * WHERE phone_enc LIKE '%1234'` —— 密文是随机二进制，LIKE 无意义
- 对：HMAC 截断索引 / OPE / 全表解密 + 应用层过滤

### 陷阱 2：用 MD5 / SHA-256 当「加密」（不可逆 = 不能解）

- 错：`MD5(phone)` 存库 —— **真的搜不出来**（哈希不可逆，连自己都解不开）
- 对：**AES-GCM（可逆加密）+ HMAC 索引（可搜）**，两者并存

### 陷阱 3：HMAC 索引不加盐（字典攻击）

- 错：`HMAC(masterKey, phone)` —— 所有用户同一盐，可批量爆破常见手机号
- 对：`HMAC(perUserKey, phone)` 或 `HMAC(masterKey, phone + userId)`（per-record salt）

### 陷阱 4：保序加密 OPE 用在高敏感数据

- 错：身份证号用 OPE —— 顺序暴露，频率分析可猜出地区 / 出生年份
- 对：OPE 仅用于年龄 / 日期等低敏感聚合；身份证用 HMAC + 全表解密

### 陷阱 5：以为「同态加密 = 完美方案」就上 FHE

- 错：业务量小 + 简单查询，直接上 FHE —— 慢 10⁵ 倍 / CPU 烧穿
- 对：99% 业务用「HMAC + 全表解密 + 应用层过滤」即可；FHE 仅极端合规场景

---

## 四、最佳实践（5 大决策树）

### 决策 1：查询类型是什么？

```text
业务查询类型？
├─ 等值（phone = ?）→ HMAC 完整索引
├─ 模糊匹配（LIKE '%1234'）→ HMAC 末 N 位索引
├─ 前缀搜索（LIKE '138%'）→ HMAC + Trie 索引
├─ 范围查询（BETWEEN）→ OPE 或全表解密
├─ 聚合（GROUP BY）→ HMAC 索引（密文聚合无意义）
└─ 任意查询 → FHE（极慢）或不解密
```

### 决策 2：数据敏感度？

```text
敏感度？
├─ 极高（身份证 / 银行卡）→ AES 加密 + HMAC + KMS（最小索引）
├─ 中（手机号 / 邮箱）→ AES 加密 + HMAC 末位索引
└─ 低（年龄 / 城市）→ OPE 或不解密
```

### 决策 3：性能预算？

```text
查询 QPS？
├─ > 10万 QPS → HMAC 索引 + B+ 树
├─ 1万-10万 QPS → HMAC 索引
├─ < 1万 QPS → 全表解密 + 内存过滤
└─ < 100 QPS → FHE 可接受
```

### 决策 4：合规要求？

```text
合规等级？
├─ GDPR / 个保法 → 必须加密 + 最小索引 + 审计日志
├─ 等保 2.0 三级 → 加密 + 权限分离
└─ 内部系统 → HMAC 索引够用
```

### 决策 5：成本预算？

```text
预算？
├─ KMS 调用费 ≤ ¥1万/月 → 云 KMS + HMAC
├─ ≤ ¥10万/月 → 自建 Vault + HMAC
└─ ≥ ¥100万/月 → FHE + 硬件加速（HSM）
```

---

## 五、面试话术（90 秒版本）

> 「**加密字段能不能模糊搜索？** 答案：**能，但要按查询类型选方案**——
>
> **6 大方案 × 5 大查询类型矩阵**：
>
> | 查询类型 | 推荐方案 | 原理 |
> |---------|---------|------|
> | 等值 | HMAC 完整索引 | 同一明文 → 同一密文 |
> | 模糊匹配（后 4 位） | HMAC 末 N 位索引 | 截断 + 建 B+ 树索引 |
> | 前缀（138%） | HMAC + Trie | 分段索引 |
> | 范围（BETWEEN） | OPE 保序加密 | 保留明文顺序 |
> | 聚合（GROUP BY） | HMAC 索引 | 同上 |
> | 任意查询 | FHE 同态加密 | 密文上计算（极慢） |
>
> **3 大反直觉**：
> 1️⃣ **HMAC 不是真加密**：是单向哈希，**可字典攻击**（常见手机号）—— 必须加盐
> 2️⃣ **OPE 牺牲安全性**：保留顺序 → 频率分析可破解——**仅用于低敏感数据**
> 3️⃣ **FHE 是银弹但慢 10⁶ 倍**：性能不可接受——**99% 业务用不到**
>
> **实战决策树**：
> 1. 先看查询类型（等值 / 模糊 / 范围 / 聚合）
> 2. 再看敏感度（高 / 中 / 低）
> 3. 再看性能预算（QPS 阈值）
> 4. 再看合规（GDPR / 等保）
>
> **典型方案**：
> - 手机号末 4 位搜索 → HMAC 末 4 位 + B+ 树索引
> - 年龄范围 → OPE
> - 身份证等值 → AES + HMAC + 全表解密（接受慢）
> - 金融聚合 → FHE + HSM
>
> 本质：**加密 vs 搜索的目标对立** —— 选方案就是**找平衡点**，不是「要安全还是要搜索」。」

---

## 六、交叉引用

- [传输加密 vs 存储加密](../encryption-at-rest-transit/README.md) —— 加密算法 + KMS / HSM 选型
- [OWASP Top 10](../owasp-top10/README.md) —— A02 加密失败 / A04 不安全设计 防御
- 主模块深度：[`06.distributed-systems/05-security/encryption`](../../../06.distributed-systems/05-security/encryption/README.md#模式-4可搜索加密searchable-encryption) —— 5 大方案 Java 代码 + 实战选型

---

## 相关章节

- 同栏目：[`encryption-at-rest-transit`](../encryption-at-rest-transit/README.md) —— 加密算法 / KMS 选型
- 主模块：[`06.distributed-systems/05-security/encryption`](../../../06.distributed-systems/05-security/encryption/README.md) —— 加密全体系（含本主题「可搜索加密」深度章节）

---

> 📅 2026-10-16 · 咬文嚼字 · 05.security · ⭐⭐⭐⭐ · 含 90 秒话术 + 5 大反模式 + 5 大决策树

← [返回: 安全咬文嚼字](../README.md)
