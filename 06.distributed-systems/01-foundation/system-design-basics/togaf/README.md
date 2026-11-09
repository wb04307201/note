<!--module:
  parent: system-design
  slug: system-design/togaf
  type: article
  category: 主模块子文章
  summary: 企业架构（Enterprise Architecture，EA）是从全局视角规划和治理组织 IT 结构的系统性方法。
  depth: ⭐⭐⭐⭐
  status: active
-->

# 企业架构（TOGAF 10）

> 企业架构（Enterprise Architecture，EA）是从全局视角规划和治理组织 IT 结构的系统性方法。  
> **TOGAF**（The Open Group Architecture Framework）是目前最主流的企业架构框架，由 The Open Group 维护。最新版本是 **TOGAF 10**（2022 年 4 月发布）。

---

## 🎯 一句话定位

**TOGAF 10 是一套用于"将业务战略转化为可执行 IT 蓝图"的标准化治理框架**——它不教你如何设计一个类，而是教你如何让数百个系统、数十个团队在统一的方向下协同工作。TOGAF 10 在 9.x 的基础上做了**模块化重构**，并整合进 The Open Group 的"数字开放标准组合"。

---

## 🆕 TOGAF 10 速览（vs 9.x）

| 维度 | TOGAF 9.x | **TOGAF 10** |
|------|-----------|--------------|
| **发布** | 2009（9.0）/ 2018（9.2） | 2022 年 4 月 |
| **结构** | 单体文档 | **模块化**：Fundamental Content（核心内容）+ Series Guides（系列指南） |
| **敏捷适配** | 偏瀑布 | 内置敏捷/数字化转型支持 |
| **文档源** | Word + DocBook | **AsciiDoc + Git**（版本可控、协作友好） |
| **标准组合** | 独立标准 | 纳入 The Open Group **数字开放标准组合**（含 IT4IT、ArchiMate 3.2、Open Agile Architecture） |
| **认证** | TOGAF 9 Certified | **TOGAF Enterprise Architecture Foundation / Practitioner**（TOGAF 10 认证已超 16,000+） |
| **总认证数** | 150,000+（171 个国家） | 持续增长（2025） |

### TOGAF 10 模块化结构

```mermaid
graph TB
    T10["🏛️ TOGAF Standard v10"]
    T10 --> Fund["📘 TOGAF Fundamental Content<br/>(核心内容 - 稳定不变)"]
    T10 --> Series["📚 TOGAF Series Guides<br/>(系列指南 - 持续扩展)"]

    Fund --> F1["概念与核心原则"]
    Fund --> F2["ADM 架构开发方法"]
    Fund --> F3["架构内容"]
    Fund --> F4["ADM 指南与技术"]
    Fund --> F5["企业架构能力与治理"]

    Series --> S1["Business Capability Planning (2023)"]
    Series --> S2["Value Stream"]
    Series --> S3["Information Architecture: BI & Analytics (2023)"]
    Series --> S4["Information Architecture: Metadata Mgmt (2023)"]
    Series --> S5["Environmentally Sustainable Info Systems (2024)"]
    Series --> S6["Architecture Roles and Skills (2024)"]
    Series --> S7["Selecting Building Blocks (2024)"]
    Series --> S8["Open Agile Architecture"]

    classDef base fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    classDef ext fill:#fff3e0,stroke:#f57c00
    class T10,Fund base
    class Series,S1,S2,S3,S4,S5,S6,S7,S8 ext
```

---

## 📚 章节导航

| 章节 | 文件 | 核心问题 | 建议时长 |
|:----:|:-----|:---------|:--------:|
| **第一章** | [核心思想 + ADM 详解](adm.md) | ADM 的 9 阶段如何系统化把战略变成 IT？ | 50 min |
| **第二章** | [BCAT + 业务能力 + 价值流](business-capability.md) | 如何用"业务能力"和"价值流"连接业务与 IT？ | 45 min |
| **第三章** | [康威定律 + 团队拓扑](conway-and-team-topology.md) | 组织结构如何决定系统架构？ | 35 min |
| **第四章** | [架构治理 + 落地实践](architecture-governance.md) | 架构设计完如何保证执行不走样？ | 40 min |
| **第五章** | [TOGAF 10 情景题答题方法（OGEA-102）](scenario-exam-method.md) | 考场上如何从四个"都合理"的选项里选出 5 分的那个？（三步答题法 + 反模式清单 + 阶段定位速查表） | 40 min |
| **第六章** | [架构原则模板（Name/Statement/Rationale/Implications）](architecture-principles.md) | 一条能裁决争议的架构原则怎么写？（4 大目的 + 4 字段模板 + 坏词清单 + 示例原则集） | 30 min |

### 推荐阅读顺序

```text
README（你在这里）  →  第一章（ADM 全貌）
        ↓
        第二章（业务能力建模 + 价值流）→ 第三章（组织对齐）
        ↓
        第四章（治理 + 落地实践）
```

- **时间紧张**（30 分钟）：先读本章"核心概念速查"+ 第一章前 3 节
- **架构师视角**：四章通读 + 第四章的"按规模裁剪"
- **工程实践者**：重点看第二章（业务能力→DDD 映射）+ 第三章（康威定律→微服务）

---

## ⚡ 核心概念速查

| 概念 | 一句话定义 | 章节 |
|------|----------|:----:|
| **TOGAF** | The Open Group Architecture Framework，企业架构框架 | 全部 |
| **ADM** | Architecture Development Method，9 阶段循环迭代方法 | [第一章](adm.md) |
| **4 大核心交付物** | Request / Statement of Architecture Work + Principles + Requirements Specification 辨析 | [第一章](adm.md) |
| **内容元模型** | 定义架构信息结构和关系的 schema（框架管过程/存储库管存放/元模型管结构）| [第一章](adm.md) |
| **架构路线图** | 工作包 + 时间安排的可视化跟踪视图（E 草案 → F 定稿）| [第一章](adm.md) |
| **BCAT** | Business / Information Systems(数据+应用) / Technology 四层 | [第二章](business-capability.md) |
| **业务能力** | 组织"做什么"（而非"怎么做"）的能力单元 | [第二章](business-capability.md) |
| **价值流** | 端到端为客户创造价值的活动序列 | [第二章](business-capability.md) |
| **康威定律** | 系统结构 = 组织的沟通结构 | [第三章](conway-and-team-topology.md) |
| **团队拓扑** | 4 种团队类型（流式/赋能/复杂子系统/平台） | [第三章](conway-and-team-topology.md) |
| **架构治理** | 6 维度（合规/合同/决策/沟通/能力/控制） | [第四章](architecture-governance.md) |
| **实施治理模型** | 阶段 F 输出：实施阶段角色/责任/流程/标准框架（F 立法、G 执法）| [第四章](architecture-governance.md) |
| **合规性评估** | 阶段 G 定期审核：进度/设计概述 + 8 类架构检查单 + 五级评级 | [第四章](architecture-governance.md) |
| **ADR** | Architecture Decision Record，轻量级架构决策记录 | [第四章](architecture-governance.md) |
| **架构原则** | 4 字段模板（Name/Statement/Rationale/Implications）定义的长期裁决标尺 | [第六章](architecture-principles.md) |

---

## 🧭 TOGAF 在系统设计中的位置

```text
战略层：TOGAF（企业架构） → 决定"做什么系统、由谁做、怎么治理"
        ↓
中观层：DDD（领域驱动设计）→ 决定"系统边界在哪、业务是什么"
        ↓
战术层：OOD（面向对象设计） → 决定"类如何组织、方法如何分配"
        ↓
编码层：设计模式 + 编码规范  → 决定"常见问题如何优雅解决"
```

> TOGAF + DDD + OOD 不是竞争关系，而是**从战略到战术到编码的三层递进**，分别解决"做什么 → 怎么拆 → 怎么写"的问题。

---

## 📂 相关章节

- [第一章：核心思想 + ADM 详解](adm.md) — 从业务战略到 IT 实现的系统化方法
- [第二章：BCAT + 业务能力 + 价值流](business-capability.md) — 连接业务与 IT 的核心建模
- [第三章：康威定律 + 团队拓扑](conway-and-team-topology.md) — 组织结构与系统架构的对齐
- [第四章：架构治理 + 落地实践](architecture-governance.md) — 6 维治理 + 不同规模裁剪
- [第五章：TOGAF 10 情景题答题方法（OGEA-102）](scenario-exam-method.md) — 梯度评分数学 + 答问题不答场景 + 三步答题法
- [第六章：架构原则模板（Name/Statement/Rationale/Implications）](architecture-principles.md) — EA 原则 4 大目的 + 预备阶段核心交付物的写作标尺 + 坏词清单 + 示例原则集
- [架构认知的演进](../architecture-evolution/README.md) — OOD → DDD → TOGAF 的认知升级之路
- [架构描述语言 ArchiMate 3.2](../archimate/README.md) — TOGAF 的"标准搭档"，30+ 视点给不同人看不同的图
- [IT 价值流参考架构 IT4IT 3.0](../it4it/README.md) — Open Group 标准组合第三件套，4 价值流 + 9 功能组件
- [领域驱动设计 DDD](../ddd/README.md) — 以业务领域为核心的建模方法
- [面向对象设计 OOD](../ood/README.md) — SOLID 原则、GRASP 职责分配
- [微服务架构](../microservices/README.md) — 康威定律与团队拓扑

---

## 📖 外部参考

- [The Open Group TOGAF 官方页](https://www.opengroup.org/togaf)
- [The Open Group 中国：TOGAF 10 更新与洞察](https://www.opengroup.org.cn/node/12411)
- [TOGAF Standard v10 在线文档](https://pubs.opengroup.org/togaf-standard/)
- [Visual Paradigm：TOGAF 10 概览](https://guides.visual-paradigm.com/cn/overview-of-the-togaf-standard-10th-edition/)

---

> 🚀 从 [第一章：核心思想 + ADM 详解](adm.md) 开始

## 反向链

- [functional-components](../it4it/functional-components.md)
- [in-practice](../it4it/in-practice.md)
- [scenario-exam-method](scenario-exam-method.md)
- [architecture-principles](architecture-principles.md)
- [02-system-architecture-evolution](../../../../13.story/02-system-architecture-evolution.md)

← [返回系统设计基础](../README.md)
