<!--module:
  parent: 06.distributed-systems
  slug: 06.distributed-systems/05-security/encryption
  type: article
  category: 主模块子文章
  summary: 加密选型与正确使用——对称/非对称/哈希/TLS/字段级加密/KMS 六大主题，覆盖算法选择、密钥管理与工程实践。
  depth: ⭐⭐⭐
  status: active
-->

# 加密与密钥管理（Encryption）

> 现代应用很少需要"自己实现加密算法"，但必须**正确选型与使用**。本文按对称 / 非对称 / 哈希 / TLS / 字段级加密 / KMS 六大主题展开，附 Java 代码示例。

## 目录

- [对称加密](#对称加密)
- [非对称加密](#非对称加密)
- [哈希与 MAC](#哈希与-mac)
- [TLS / HTTPS](#tls--https)
- [字段级加密（Field-Level Encryption）](#字段级加密field-level-encryption)
- [密钥管理 KMS / HSM](#密钥管理-kms--hsm)
- [常见误区](#常见误区)
- [参考资料](#参考资料)

## 对称加密

**适用场景**：加密大量数据（数据库字段、文件、消息体）。加解密使用**同一把密钥**。

### 推荐算法

| 算法 | 密钥长度 | 模式 | 备注 |
|------|----------|------|------|
| **AES-GCM** | 128/256 bit | AEAD（认证加密） | **首选** |
| **AES-CBC + HMAC** | 256 bit | Encrypt-then-MAC | 老系统常用 |
| **ChaCha20-Poly1305** | 256 bit | AEAD | 移动端 / 无 AES-NI 时更快 |
| ~~DES / 3DES / AES-ECB~~ | — | — | **已淘汰** |

### 为什么 GCM 是首选

GCM（Galois/Counter Mode）同时提供**机密性 + 完整性**（AEAD = Authenticated Encryption with Associated Data），避免 CBC 模式常见的 padding oracle 攻击。

### Java 示例：AES-256-GCM

```java
public class AesGcmUtil {

    private static final int GCM_IV_LEN = 12;     // 96 bit 推荐长度
    private static final int GCM_TAG_LEN = 128;   // 128 bit 认证标签

    public static byte[] encrypt(byte[] plaintext, SecretKey key) throws Exception {
        // 1. 随机 IV（绝不重用！）
        byte[] iv = new byte[GCM_IV_LEN];
        SecureRandom random = new SecureRandom();
        random.nextBytes(iv);

        // 2. 加密
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        GCMParameterSpec spec = new GCMParameterSpec(GCM_TAG_LEN, iv);
        cipher.init(Cipher.ENCRYPT_MODE, key, spec);
        byte[] ct = cipher.doFinal(plaintext);

        // 3. 返回 iv + ciphertext (iv 不需保密但必须随密文存储)
        ByteBuffer buf = ByteBuffer.allocate(iv.length + ct.length);
        buf.put(iv).put(ct);
        return buf.array();
    }

    public static byte[] decrypt(byte[] cipherBlob, SecretKey key) throws Exception {
        ByteBuffer buf = ByteBuffer.wrap(cipherBlob);
        byte[] iv = new byte[GCM_IV_LEN];
        buf.get(iv);
        byte[] ct = new byte[buf.remaining()];
        buf.get(ct);

        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, key, new GCMParameterSpec(GCM_TAG_LEN, iv));
        return cipher.doFinal(ct);   // 验证 GCM tag 失败时抛 AEADBadTagException
    }
}
```

> **关键约束**：AES-GCM 的 IV 绝不能在**同一密钥**下重用。重用 → 灾难性机密性 / 完整性破坏（攻击者可恢复明文异或）。

---

## 非对称加密

**适用场景**：密钥交换（TLS）、数字签名、加密小数据（密钥封装）。加解密使用**不同密钥**（公钥 + 私钥）。

### 主流算法

| 算法 | 用途 | 密钥长度 | 备注 |
|------|------|----------|------|
| **RSA** | 签名、加密 | ≥ 2048 bit（推荐 3072/4096） | 老牌，签名验签慢 |
| **ECDSA** (P-256) | 签名 | 256 bit | TLS 主流 |
| **Ed25519** | 签名 | 256 bit | **推荐**：快、安全、易用 |
| **ECDH** (X25519) | 密钥交换 | 256 bit | TLS 1.3 / Signal |
| **RSA-OAEP** | 加密 | ≥ 2048 bit | 用于加密小数据 / 封装密钥 |

### 数字签名示例（Ed25519，Java 15+）

```java
import java.security.*;
import java.security.spec.*;

public class Ed25519Example {

    public static void main(String[] args) throws Exception {
        // 1. 生成密钥对
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("Ed25519");
        KeyPair kp = kpg.generateKeyPair();

        // 2. 签名
        Signature signer = Signature.getInstance("Ed25519");
        signer.initSign(kp.getPrivate());
        signer.update("hello world".getBytes());
        byte[] sig = signer.sign();

        // 3. 验签
        Signature verifier = Signature.getInstance("Ed25519");
        verifier.initVerify(kp.getPublic());
        verifier.update("hello world".getBytes());
        boolean ok = verifier.verify(sig);   // true
    }
}
```

### TLS 中的实际用法

- **签名**：服务器用 Ed25519 私钥签证书，客户端用 CA 公钥验签
- **密钥交换**：客户端用 ECDH 算出共享密钥 → 用 HKDF 派生对称密钥 → 用于 AES-GCM

---

## 哈希与 MAC

### 加密哈希函数

| 算法 | 输出 | 状态 | 用途 |
|------|------|------|------|
| **SHA-256** | 256 bit | 安全 | 通用哈希 |
| **SHA-3 / BLAKE3** | 可变 | 安全 | 替代 SHA-2 |
| **SHA-1** | 160 bit | **已破解** | 仅用于非安全场景 |
| **MD5** | 128 bit | **已破解** | 仅用于文件指纹校验 |

### 密码哈希（特殊场景）

密码哈希需**慢 + 加盐**，防止字典攻击：

| 算法 | 推荐度 | 备注 |
|------|--------|------|
| **Argon2id** | ⭐⭐⭐ | 内存硬，可调参 |
| **bcrypt** | ⭐⭐ | 老牌稳定 |
| **scrypt** | ⭐⭐ | 内存硬 |
| PBKDF2 | ⭐ | NIST 标准化，但快 |
| SHA-256 + salt | ❌ | 太快，不安全 |

### MAC（Message Authentication Code）

确保消息**未被篡改 + 来源可信**。HMAC 是最常用的方案：

```java
public byte[] hmacSha256(byte[] message, byte[] key) throws Exception {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    return mac.doFinal(message);
}

// 验证：compare in constant time (防时序攻击)
public boolean constantTimeEquals(byte[] a, byte[] b) {
    return MessageDigest.isEqual(a, b);
}
```

> 现代 AEAD 加密（AES-GCM / ChaCha20-Poly1305）已经自带 MAC，无需额外 HMAC。

---

## TLS / HTTPS

### TLS 握手流程（简化）

```text
Client                                  Server
  │                                       │
  │── ClientHello (支持的版本/密码套件) ──▶│
  │                                       │
  │◀── ServerHello + Certificate ────────│
  │◀── (ServerKeyExchange if needed) ────│
  │◀── ServerHelloDone ──────────────────│
  │                                       │
  │── ClientKeyExchange ────────────────▶│
  │── (CertificateVerify if mTLS) ──────▶│
  │── ChangeCipherSpec + Finished ──────▶│
  │                                       │
  │◀── ChangeCipherSpec + Finished ──────│
  │                                       │
  │◀══════ 加密通道 (AES-GCM) ══════════▶│
```

### 关键配置

```nginx
# Nginx TLS 1.3 推荐配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_prefer_server_ciphers on;
ssl_ciphers ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305;
ssl_ecdh_curve X25519:secp384r1;
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 1d;
ssl_session_tickets off;
```

### mTLS（双向 TLS）

在微服务 / 服务网格中，**双方都验证对方证书**：

- Service Mesh（Istio / Linkerd）自动注入 mTLS
- Spring Cloud Gateway + X.509 证书

### 证书锁定（Certificate Pinning）

参考 [API 安全](../api-security/README.md#https-与证书锁定)。

---

## 字段级加密（Field-Level Encryption）

数据库中的**敏感字段**（身份证、银行卡、密码）需要单独加密，与行级 / 全盘加密不同。

### 模式 1：信封加密（推荐）

```text
应用                   KMS / HSM              数据库
 │                       │                     │
 │ 1. 请求生成 DEK        │                     │
 │ ─────────────────▶   │                     │
 │ ◀── 返回 DEK ────────│                     │
 │                       │                     │
 │ 2. 用 DEK 加密数据                            │
 │ 3. 把 DEK 用 KMS 加密（加密后存入 DB）        │
 │                       │                     │
 │ 4. 写入：                                ──▶│
 │    id_card_enc, dek_enc                  ──▶│
```

详见 [secrets-management](../secrets-management/README.md#2-加密信封envelope-encryption) 章节的代码示例。

### 模式 2：确定性加密（Deterministic Encryption）

为支持**等值查询**（`WHERE id_card_hash = ?`），使用确定性加密：

- 同一明文 + 同一密钥 → 同一密文
- 但泄露后**可被频率分析**（如每年出生人数对应密文频率）

**实现方式**：

1. **HMAC 截断**：`id_card_hash = HMAC-SHA256(key, id_card)[:16]` 作为盲化索引列
2. **AES-SIV 模式**：在标准之上提供确定性 + 防滥用
3. **保序加密（OPE）**：保留顺序，但安全性弱，慎用

```java
// 模式 1 示例：HMAC 盲化索引
public String blindIndex(String plain, byte[] key) {
    Mac mac = Mac.getInstance("HmacSHA256");
    mac.init(new SecretKeySpec(key, "HmacSHA256"));
    byte[] hash = mac.doFinal(plain.getBytes(StandardCharsets.UTF_8));
    return Base64.getUrlEncoder().withoutPadding()
            .encodeToString(Arrays.copyOf(hash, 16));
}

// SQL 查询
// SELECT * FROM users WHERE id_card_bi = ?  // 传入 blindIndex(用户输入, key)
```

### 模式 3：透明加密（Transparent Data Encryption, TDE）

数据库自身提供的磁盘加密：

- **MySQL** InnoDB 表空间加密
- **PostgreSQL** pgcrypto
- **AWS RDS** 启用存储加密

- **优点**：零应用改造成本
- **缺点**：DBA / 备份仍可读明文；不防应用层 SQL 注入

### 模式 4：可搜索加密（Searchable Encryption）

应用层加密后，**直接对密文做 `LIKE` 查询是无效的**（密文是随机二进制）。需要按查询类型选方案：

| 查询类型 | 推荐方案 | 原理 |
|---------|---------|------|
| **等值**（`phone = ?`） | HMAC 完整索引 | 同一明文 → 同一 HMAC，建 B+ 树索引 |
| **模糊匹配**（`phone LIKE '%1234'`） | HMAC 末 N 位索引 | 截取 HMAC 末 4 字节，建 B+ 树索引 |
| **前缀**（`phone LIKE '138%'`） | HMAC + Trie 索引 | 分段索引 |
| **范围**（`age BETWEEN 20 AND 30`） | OPE 保序加密 / 全表解密 | 保留明文顺序 |
| **聚合**（`GROUP BY city`） | HMAC 索引 / 不加密 | 密文聚合无意义 |
| **任意查询** | FHE 同态加密 | 密文上计算（极慢 10⁵-10⁶ 倍） |

#### 4.1 HMAC 末 N 位索引（手机号后四位）

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

#### 4.2 保序加密 OPE（年龄范围查询）

```java
// OPE 库：mCrypt / AWS Cryptography / Google Cloud DPE
public BigInteger opeEncrypt(int plaintext, byte[] key) {
    Ope ope = new Ope(key);
    return ope.encrypt(BigInteger.valueOf(plaintext));
}

// 范围查询（OPE 密文范围 = 明文范围）
// SELECT * FROM users WHERE age_ope BETWEEN opeEncrypt(20) AND opeEncrypt(30)

// 注意：OPE 暴露顺序 → 不能用 SELECT DISTINCT 看分布（暴露频率）
// 不能用 SELECT MIN/MAX 看极值（暴露明文范围）
```

#### 4.3 同态加密 FHE（任意查询，极慢）

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

#### 4.4 实战选型决策树

```text
业务查询类型？
├─ 等值 → HMAC 完整索引
├─ 模糊匹配（后 N 位）→ HMAC 末 N 位索引
├─ 前缀 → HMAC + Trie
├─ 范围 → OPE（低敏感）或 全表解密（高敏感）
├─ 聚合 → HMAC 索引 / 不加密
└─ 任意 → FHE（极慢，仅极端合规）

数据敏感度？
├─ 极高（身份证 / 银行卡）→ AES + HMAC + KMS（最小索引）
├─ 中（手机号 / 邮箱）→ AES + HMAC 末位索引
└─ 低（年龄 / 城市）→ OPE 或不解密

性能预算？
├─ > 10万 QPS → HMAC + B+ 树
├─ < 1万 QPS → 全表解密 + 内存过滤
└─ < 100 QPS → FHE 可接受
```

#### 4.5 5 大反模式

| ❌ 反模式 | 错在哪 | 正确做法 |
|----------|--------|---------|
| **对密文做 LIKE 查询** | 密文是二进制乱码，LIKE 无意义 | HMAC 截断索引 / OPE / 全表解密 |
| **用 MD5 当「加密」** | 哈希不可逆，连自己都解不开 | AES-GCM + HMAC 索引 |
| **HMAC 索引不加盐** | 同一 master key → 字典攻击常见值 | per-user salt 或 per-record salt |
| **OPE 用在高敏感数据** | 保留顺序 → 频率分析可破解 | OPE 仅用于低敏感聚合 |
| **盲目上 FHE** | 慢 10⁵ 倍 / CPU 烧穿 | 99% 业务用「HMAC + 全表解密」 |

#### 4.6 一句话总结

> **应用层加密不是「不可搜索」，而是「按查询类型选方案」** —— 等值用 HMAC 完整索引、模糊匹配用 HMAC 末 N 位、范围用 OPE、任意查询用 FHE（极慢）。

#### 4.7 反直觉点

- ❓ 有人问：「加密字段 LIKE 查询会不会泄露明文？」 → LIKE 查询本身只查索引（HMAC 末 N 位），不接触密文，**无泄露**。
- ❓ 有人问：「HMAC 索引被脱库怎么办？」 → 加 per-user 盐 + 长截断（≥ 16 字节），字典攻击代价 = 2¹²⁸，**不可破解**。

---

## 密钥管理 KMS / HSM

### KMS（Key Management Service）

- **托管式**：密钥由云厂商保管，用户通过 API 使用
- 永远不暴露明文密钥，硬件（HSM）保护
- 主流：AWS KMS、Azure Key Vault、GCP Cloud KMS、阿里云 KMS

```java
// AWS KMS Java SDK 加密示例
public class KmsExample {

    private final KmsClient kms = KmsClient.builder().region(Region.US_EAST_1).build();

    public byte[] encrypt(byte[] plaintext, String keyId) {
        EncryptRequest req = EncryptRequest.builder()
                .keyId(keyId)            // arn:aws:kms:...
                .plaintext(SdkBytes.fromByteArray(plaintext))
                .build();
        EncryptResponse resp = kms.encrypt(req);
        return resp.ciphertextBlob().asByteArray();
    }

    public byte[] decrypt(byte[] cipherBlob) {
        DecryptResponse resp = kms.decrypt(DecryptRequest.builder()
                .ciphertextBlob(SdkBytes.fromByteArray(cipherBlob))
                .build());
        return resp.plaintext().asByteArray();
    }
}
```

### HSM（Hardware Security Module）

- 物理硬件保护密钥（防内存抓取、防侧信道）
- 比 KMS 更强，但贵且慢
- 适用：金融根证书、PKI 根 CA

### 自建 vs 云托管

| 维度 | 自建（HashiCorp Vault） | 云托管（AWS KMS 等） |
|------|-------------------------|----------------------|
| 成本 | 自建免费（运维成本高） | 按调用计费 |
| 合规 | 需自己过 SOC2 / PCI DSS | 已合规 |
| 多云 | 一致体验 | 锁定云厂商 |
| 物理保护 | 自购 HSM 接入 | 厂商 HSM 内置 |

> **建议**：上云就优先用云 KMS；多云 / 混合云考虑 Vault + 各云 KMS 适配。

---

## 常见误区

| 误区 | 为什么错 | 正确做法 |
|------|----------|----------|
| 密码加 MD5 / SHA-1 后存库 | GPU 秒破 | bcrypt / Argon2id |
| 自定义加密算法 | 99% 错 | 用标准库（AES-GCM） |
| 同一密钥 + 同一 IV 加密多个文件 | AES-GCM 灾难 | 每次随机 IV |
| 私钥放代码仓库 | 提交即泄露 | 放 Vault / KMS |
| 加密字段做 `LIKE` 查询 | 密文不可模糊匹配 | 等值用 HMAC 盲化索引 |
| 用 base64 当"加密" | 完全可逆 | AES-GCM 才是加密 |
| 自己实现 TLS | 必有漏洞 | 用 OpenSSL / BoringSSL / mbedTLS |

---

## 参考资料

- [NIST SP 800-57 - Recommendation for Key Management](https://csrc.nist.gov/publications/detail/sp/800-57-part-1/rev-5/final)
- [NIST SP 800-38D - GCM 模式规范](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
- [RFC 7748 - Elliptic Curves for Security (X25519, Ed25519)](https://tools.ietf.org/html/rfc7748)
- [OWASP Cryptographic Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Cryptographic_Storage_Cheat_Sheet.html)
- [AWS KMS 文档](https://docs.aws.amazon.com/kms/)
- [HashiCorp Vault Transit Engine](https://developer.hashicorp.com/vault/docs/secrets/transit)

---


- [mac](../access-control/01-traditional/mac.md)
← [返回 安全篇](../README.md)
