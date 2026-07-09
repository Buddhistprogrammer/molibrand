# AI品牌咨询产品 — 技术架构文档

> **项目名称**：AI品牌咨询服务产品（MVP）
> **文档版本**：v1.0
> **编写日期**：2026-07-09
> **架构师**：高见远
> **面向用户**：中小企业老板 / 创业者
> **核心交互**：Web对话式（全模态：视频/语音/图片/文字）

---

## 目录

1. [项目概述与核心流程](#1-项目概述与核心流程)
2. [技术约束清单](#2-技术约束清单)
3. [技术选型调研](#3-技术选型调研)
4. [向量检索方案对比矩阵](#4-向量检索方案对比矩阵)
5. [最终选型结论及理由](#5-最终选型结论及理由)
6. [系统架构图](#6-系统架构图)
7. [知识库RAG设计](#7-知识库rag设计)
8. [Web对话式架构设计](#8-web对话式架构设计)
9. [不可行/高风险功能警告](#9-不可行高风险功能警告)
10. [部署方案](#10-部署方案)
11. [成本预估](#11-成本预估)
12. [附录：参考资料](#12-附录参考资料)

---

## 1. 项目概述与核心流程

### 1.1 产品定位

基于茉莉总个人品牌咨询经验，通过AI赋能打造可规模化的品牌咨询服务产品。面向中小企业老板/创业者，提供专业级品牌诊断与方案推荐。

### 1.2 MVP核心流程

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ 知识库    │───▶│ AI学习   │───▶│ 生成互动 │───▶│ 输出诊断 │───▶│ 人工审核 │
│ 录入(10-  │    │ 并向量化 │    │ 问题     │    │ 报告     │    │ 下发方案 │
│ 50篇)     │    │          │    │          │    │          │    │          │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

**详细流程说明**：

1. **知识库录入**：管理员将茉莉总的品牌咨询方法论、案例、模板等10-50篇文档录入系统
2. **AI学习与向量化**：文档被拆分为小片段，通过Embedding模型向量化后存入向量数据库
3. **用户交互**：用户通过Web对话界面描述品牌现状，AI基于知识库生成针对性的互动问题
4. **诊断报告生成**：AI综合用户回答 + 知识库内容，生成结构化品牌诊断报告
5. **人工审核**：咨询师审核AI生成的诊断报告，可修改/补充
6. **方案下发**：审核通过后，将诊断报告和品牌方案下发给用户

### 1.3 全模态支持需求

| 模态 | 输入场景 | 输出场景 |
|------|----------|----------|
| **文字** | 用户对话输入、知识库文档 | AI回复、诊断报告 |
| **图片** | 用户上传品牌Logo/产品图/海报 | AI分析图片内容并反馈 |
| **语音** | 用户语音提问（便捷输入） | AI语音播报诊断要点 |
| **视频** | 用户上传品牌宣传视频/产品演示 | AI分析视频内容并提取品牌信息 |

---

## 2. 技术约束清单

### 2.1 硬件资源约束

| 资源 | 规格 | 备注 |
|------|------|------|
| 应用服务器 | 4核8G Ubuntu 24.04 LTS（阿里云ECS） | 需承载Web后端 + RAG服务 |
| 数据库 | 2核4G MySQL 8.0（阿里云RDS） | 用户数据、对话历史、知识库元数据 |
| 对象存储 | 500G OSS | 视频/语音/图片文件存储 |
| 网络 | 阿里云内网 | 与百炼平台、OSS内网互通 |

### 2.2 技术栈约束

| 约束项 | 要求 | 说明 |
|--------|------|------|
| 大模型 | 阿里云通义系列（百炼平台） | 必须使用，不可替换 |
| 全模态 | 视频/语音/图片/文字 | 四种模态均需支持 |
| 向量检索 | 需向量检索能力 | 知识库RAG检索 |
| 知识库规模 | 10-50篇文档 | 需拆分为小片段避免上下文溢出 |
| 数据安全 | 用户数据不用于模型训练 | 百炼平台默认不用于训练 |

### 2.3 性能约束（基于4核8G服务器）

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 并发用户数 | 10-20 同时在线 | MVP阶段预期 |
| API响应首字延迟 | < 3秒 | SSE流式输出 |
| 知识库检索延迟 | < 200ms | 向量检索 |
| 文件上传大小限制 | 单文件 ≤ 100MB | 视频/语音文件 |
| 内存占用 | < 6GB | 预留2GB给系统 |

---

## 3. 技术选型调研

### 3.1 阿里云通义系列大模型能力调研

#### 3.1.1 模型矩阵概览（2026年7月最新）

阿里云百炼平台（DashScope / Model Studio）提供通义千问Qwen3.7系列及多模态模型家族，覆盖全场景需求：

**文本生成模型**：

| 模型ID | 定位 | 上下文窗口 | 输入价格 | 输出价格 | 特点 |
|--------|------|-----------|----------|----------|------|
| `qwen3.7-max` | 旗舰版 | 1M Token | 2元/百万Token | 4元/百万Token | 最强推理，复杂任务 |
| `qwen3.7-plus` | 均衡版 | 1M Token | 1元/百万Token | 2元/百万Token | 性价比最优，默认选择 |
| `qwen3.6-flash` | 轻量版 | 1M Token | 约0.5元/百万Token | 约1元/百万Token | 低延迟高并发 |

> **价格说明**：以上为原价，百炼平台新用户可获7000万免费Tokens（90天有效期）。Batch调用（批量推理）输入输出Token单价均按实时推理价格的50%计费。上下文缓存可降低输入Token费用。

**视觉理解模型**（图片/视频）：

| 模型ID | 输入模态 | 上下文 | 最大图片数 | 最大视频时长 | 特点 |
|--------|----------|--------|-----------|-------------|------|
| `qwen3.7-plus` | 文本、图像、视频 | 1M | 2048张 | 2小时/2GB | 旗舰，推荐首选 |
| `qwen3.6-flash` | 文本、图像、视频 | 1M | 256张 | 2小时/2GB | 轻量低成本 |
| `qwen3.5-omni-plus` | 文本、音频、图片、视频 | 64K | 2048张 | 1小时/2GB | 全模态 |

**全模态模型**（Qwen-Omni系列）：

| 模型ID | API | 输入模态 | 输出 | 特点 |
|--------|-----|----------|------|------|
| `qwen3.5-omni-plus` | HTTP | 文本、音频、图片、视频 | 文本、语音 | 旗舰全模态，支持Function Calling和联网搜索 |
| `qwen3.5-omni-plus-realtime` | WebSocket | 文本、音频、图片、视频 | 文本、语音 | 实时全模态对话 |
| `qwen3-omni-flash` | HTTP | 文本、音频、图片、视频 | 文本 | 轻量全模态，支持思考模式 |
| `qwen3.5-livetranslate-flash` | WebSocket/HTTP | 音频、视频 | 文本、语音 | 实时语音翻译（60种语言） |

**语音识别（ASR）模型**：

| 模型ID | 特点 |
|--------|------|
| `fun-asr-realtime` | 实时语音识别，支持30种语言+16种方言，首字延迟低 |
| `fun-asr` | 非实时语音识别 |
| `qwen3.5-omni-plus` | 全模态内置ASR能力 |

**语音合成（TTS）模型**：

| 模型ID | 特点 |
|--------|------|
| `cosyvoice-v3.5-plus` | 高质量语音合成，支持音色克隆 |
| `qwen3.5-omni-plus` | 全模态内置TTS能力 |

**Embedding与Rerank模型**：

| 模型ID | 类型 | 向量维度 | 最大Token | 适用场景 |
|--------|------|----------|----------|----------|
| `text-embedding-v4` | 文本Embedding | 64~2048（默认1024） | 8,192 | 文本搜索、RAG、聚类 |
| `text-embedding-v3` | 文本Embedding | 512~1024（默认1024） | 8,192 | 已有v3索引迁移 |
| `qwen3-vl-embedding` | 多模态Embedding | 256~2560（默认2560） | 32,000 | 图文混合检索 |
| `qwen3-rerank` | 文本重排序 | - | 4,000/条 | RAG精度提升 |
| `gte-rerank-v2` | 文本重排序 | - | 4,000/条 | 文本语义检索 |

#### 3.1.2 API调用方式

百炼平台API兼容OpenAI API格式，支持以下调用方式：

```python
# 文本生成（流式）
from openai import OpenAI
client = OpenAI(
    api_key="your-dashscope-api-key",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)
response = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[{"role": "user", "content": "你好"}],
    stream=True  # 流式输出
)

# 多模态（图片+视频）
response = client.chat.completions.create(
    model="qwen3.7-plus",
    messages=[{
        "role": "user",
        "content": [
            {"type": "text", "text": "分析这张品牌Logo"},
            {"type": "image_url", "image_url": {"url": "https://oss.../logo.png"}}
        ]
    }]
)

# 全模态（Qwen-Omni，HTTP方式）
# 通过百炼SDK调用，支持音频/视频输入

# Embedding
response = client.embeddings.create(
    model="text-embedding-v4",
    input="品牌定位的核心要素包括...",
    dimensions=1024
)
```

**API认证**：通过API Key认证，支持环境变量配置。调用与操作系统无关，只要网络连通即可。

#### 3.1.3 计费标准摘要

| 计费模式 | 说明 |
|----------|------|
| 按量付费 | 按输入/输出Token分别计费，按分钟出账 |
| Batch调用 | 输入输出Token均按实时推理价格的50%计费 |
| 上下文缓存 | 仅输入Token享有折扣 |
| 节省计划 | 承诺消费金额享折扣（0.5~0.95折），抵扣所有后付费项 |
| 免费额度 | 新用户7000万Tokens，90天有效期 |

> **参考费用**：使用`qwen3.7-plus`，单次咨询对话约消耗5000输入Token + 3000输出Token，成本约 0.005 + 0.006 = 0.011元/次。每日100次咨询约1.1元。

---

### 3.2 向量检索方案调研

#### 方案一：阿里云OpenSearch向量检索版

**概述**：阿里巴巴自主研发的大规模分布式搜索引擎，支撑淘宝、天猫等集团搜索业务。

**优势**：
- 阿里云原生服务，与OSS、RDS等无缝集成
- 支持向量+标量混合检索
- 全托管，免运维
- 支持实时索引更新

**劣势**：
- **成本较高**：最低配置（实例租用 + 1个查询节点2核8G云盘 + 1个数据节点2核16G云盘）按量付费约 0.38 + 0.38 + 0.50 = 1.26元/小时 ≈ 923元/月
- 对于10-50篇文档的知识库，严重过度配置
- 实例规格起步高，无法精细控制成本

**计费明细**（按量付费，华东区域）：
- 实例租用：0.38元/小时
- 查询节点（云盘型2核8G）：0.38元/小时/个
- 数据节点（云盘型2核16G）：0.50元/小时/个
- **最低月费**：约923元（1个查询节点 + 1个数据节点）

#### 方案二：Milvus（自建）

**概述**：全球最受欢迎的开源向量数据库，专为AI原生场景设计，支持十亿级向量检索。

**优势**：
- 专业向量数据库，性能卓越（Recall@10: 0.88-0.92）
- 支持十亿级向量，扩展性强
- 支持Hybrid Search（BM25 + 向量）
- 活跃开源社区（45,000+ GitHub Stars）

**劣势**：
- **运维复杂度高**：需部署etcd + MinIO + Milvus组件，至少3个服务
- **资源占用大**：1000万768维HNSW索引约需64-128GB内存，4核8G服务器完全无法承载
- 与阿里云生态无原生集成
- 需要额外运维人力

**资源需求**：Milvus单机版Standalone最低需要8核16G，在4核8G服务器上无法稳定运行。

#### 方案三：PostgreSQL + pgvector

**概述**：PostgreSQL的向量扩展插件，使关系型数据库原生支持向量相似度搜索。

**优势**：
- **最低运维摩擦**：PostgreSQL成熟稳定，DBA生态完善
- **SQL+向量混合查询**：可JOIN元数据，业务数据与向量数据统一存储
- **资源占用极低**：< 300万向量、QPS < 30时首选
- 成本极低：可与应用服务器共部署，无需额外数据库实例
- 2026年选型报告明确指出："PGVector是中小企业最低摩擦路径"

**劣势**：
- 大规模向量（> 500万）性能下降明显
- 不支持GPU索引加速
- Hybrid Search需配合tsvector手动实现

**性能参考**（1000万向量，768维）：
- Recall@10: 0.85-0.90
- P99查询延迟: 40-80ms
- 插入吞吐: 2K-5K条/秒

> **关键判断**：本项目知识库10-50篇文档，按每篇切分20-50个chunk计算，向量总数约200-2500条。pgvector完全可轻松承载，且QPS远低于30，pgvector是最佳选择。

#### 方案四（备选）：百炼平台内置知识库

百炼平台自身提供知识库服务，内置向量化、检索能力，无需额外部署向量数据库。

**优势**：零运维，与百炼API无缝集成。
**劣势**：知识库服务费单独计费；灵活性受限；数据存储在百炼平台而非自有数据库。
**结论**：可作为快速验证阶段的过渡方案，但不适合长期生产使用（数据主权和灵活性考量）。

---

## 4. 向量检索方案对比矩阵

| 对比维度 | OpenSearch向量检索版 | Milvus（自建） | PostgreSQL + pgvector | 百炼内置知识库 |
|----------|---------------------|----------------|----------------------|---------------|
| **月成本（最低配置）** | ~923元 | ~200元（需8核16G+） | **~0元**（与MySQL共存或SQLite） | 按量计费（知识库服务费） |
| **Recall@10（1000万向量）** | 0.86-0.91 | 0.88-0.92 | 0.85-0.90 | 依赖百炼实现 |
| **P99查询延迟** | 35-70ms | 25-45ms | 40-80ms | 100-300ms（API调用） |
| **运维复杂度** | 低（全托管） | 高（etcd+MinIO+Milvus） | **极低**（PG成熟生态） | **零** |
| **4核8G服务器适用性** | 不适用（独立服务） | **不适用**（资源不足） | **完全适用** | 完全适用 |
| **阿里云生态集成** | 原生集成 | 需手动对接 | 良好（RDS PG可选） | 原生集成 |
| **Hybrid Search** | 支持 | 支持（Sparse-BM25） | 支持（pgvector+tsvector） | 内置 |
| **数据主权** | 阿里云托管 | 自建完全可控 | **自建完全可控** | 百炼平台托管 |
| **扩展性** | 强（分布式） | 极强（十亿级） | 中（千万级） | 受限 |
| **本项目适用性** | 严重过度配置 | 资源不足，不可行 | **最优选择** | 过渡方案可用 |

---

## 5. 最终选型结论及理由

### 5.1 技术选型总表

| 技术领域 | 最终选型 | 核心理由 |
|----------|----------|----------|
| **后端框架** | Python + FastAPI | 异步支持好、SSE原生支持、AI生态丰富、阿里云SDK完善 |
| **前端框架** | React + TypeScript | 组件生态丰富、SSE EventSource原生支持 |
| **大模型（文本对话/报告生成）** | `qwen3.7-plus` | 性价比最优，1M上下文，支持Function Calling、结构化输出 |
| **大模型（图片/视频分析）** | `qwen3.7-plus`（多模态） | 同一模型支持文本+图像+视频，简化架构 |
| **大模型（全模态/语音对话）** | `qwen3.5-omni-plus` | 支持文本+音频+图片+视频输入，文本+语音输出 |
| **语音识别（ASR）** | `fun-asr-realtime` | 30种语言+16种方言，低延迟，百炼原生 |
| **语音合成（TTS）** | `cosyvoice-v3.5-plus` | 高质量合成，支持音色克隆 |
| **Embedding模型** | `text-embedding-v4` | 百炼原生，1024维（默认），8192 Token上限 |
| **Rerank模型** | `qwen3-rerank` | 百炼原生，支持100+语言，提升RAG精度 |
| **向量数据库** | **PostgreSQL + pgvector** | 资源占用极低、运维最简、与MySQL生态接近、完全满足200-2500条向量需求 |
| **关系型数据库** | MySQL 8.0（已有RDS） | 用户数据、对话历史、知识库元数据、审核记录 |
| **对象存储** | 阿里云OSS（已有500G） | 视频/语音/图片文件存储 |
| **流式通信** | SSE（Server-Sent Events） | 实现简单、自动重连、HTTP友好、百炼API原生支持流式 |
| **文件上传** | STS临时签名 + 前端直传OSS | 减轻服务器带宽压力、安全可靠 |
| **部署方式** | Docker Compose 单机部署 | 4核8G资源有限，单机足够MVP |

### 5.2 关键选型理由

#### 5.2.1 为什么选 PostgreSQL + pgvector 而非 Milvus 或 OpenSearch？

1. **资源约束决定**：4核8G服务器无法运行Milvus（最低需8核16G），OpenSearch最低月费923元性价比极差
2. **数据规模决定**：10-50篇文档，切分后约200-2500条向量，pgvector在300万向量以内为首选（2026年选型报告结论）
3. **运维成本决定**：pgvector与PostgreSQL同体，运维成熟度极高；Milvus需维护etcd+MinIO+Milvus三组件
4. **SQL+向量混合查询**：品牌咨询场景需要按知识库分类、标签等元数据过滤，pgvector原生支持SQL JOIN
5. **迁移路径清晰**：未来若向量规模增长至500万+，可评估迁移至Milvus，pgvector→Milvus迁移有成熟工具链

> **实施策略**：在4核8G应用服务器上部署PostgreSQL（Docker），或使用阿里云RDS PostgreSQL（2核4G可共享）。pgvector作为扩展安装，与MySQL 8.0分工：MySQL存业务数据，PostgreSQL存向量数据。

#### 5.2.2 为什么选 SSE 而非 WebSocket？

1. **场景匹配**：品牌咨询对话是"用户提问→AI流式回复"的单向推送场景，SSE完全满足
2. **百炼API兼容**：百炼平台流式输出使用SSE格式，后端直接透传即可，无需协议转换
3. **自动重连**：浏览器EventSource原生支持断线自动重连，无需手动实现
4. **实现简单**：基于HTTP，无需协议升级、帧编解码、心跳维护
5. **代理友好**：可穿透所有支持HTTP的代理和防火墙
6. **唯一局限**：不支持客户端→服务端实时推送（如语音流式输入），但本项目语音输入通过"录制→上传→ASR→文本"流程实现，不需要双向实时通道

> **混合方案**：文字/图片/视频对话使用SSE；未来如需实时语音对话（端到端低延迟），可引入WebSocket对接`qwen3.5-omni-plus-realtime`。

#### 5.2.3 大模型使用策略

| 场景 | 模型 | 理由 |
|------|------|------|
| 用户日常对话（文字） | `qwen3.7-plus` | 性价比最优，1M上下文可容纳完整知识库片段 |
| 图片/视频分析 | `qwen3.7-plus` | 多模态能力，支持2048张图片、2小时视频 |
| 语音输入处理 | `fun-asr-realtime` → 文字 → `qwen3.7-plus` | 解耦ASR和LLM，灵活控制成本 |
| 语音输出 | `qwen3.7-plus`生成文字 → `cosyvoice-v3.5-plus`合成语音 | 解耦TTS，可按需启用 |
| 诊断报告生成 | `qwen3.7-plus` + 结构化输出 | 支持JSON结构化输出，便于报告模板化 |
| 互动问题生成 | `qwen3.6-flash` | 低成本快速生成，非核心环节 |
| 知识库Embedding | `text-embedding-v4` | 百炼原生，1024维，8192 Token |
| 检索结果重排序 | `qwen3-rerank` | 提升RAG检索精度 |

---

## 6. 系统架构图

### 6.1 整体架构图（文字描述）

```
┌─────────────────────────────────────────────────────────────────────┐
│                           用户层（Web前端）                           │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐        │
│  │ 文字对话   │  │ 图片上传   │  │ 语音录制   │  │ 视频上传   │        │
│  │ SSE接收   │  │ OSS直传   │  │ 录制+上传  │  │ OSS直传   │        │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘        │
└────────┼──────────────┼──────────────┼──────────────┼──────────────┘
         │              │              │              │
         ▼              ▼              ▼              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    阿里云OSS（500G对象存储）                          │
│              图片/语音/视频文件存储 + STS临时签名                     │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ 文件URL
         ▼                     │                     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      应用服务器（4核8G Ubuntu）                       │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────┐       │
│  │              FastAPI Web后端（Python）                   │       │
│  │                                                         │       │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐│       │
│  │  │ 对话管理  │  │ 文件管理  │  │ 报告生成  │  │审核流程 ││       │
│  │  │ SSE流式  │  │ STS签发  │  │ 模板引擎  │  │ 状态机  ││       │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘│       │
│  │       │             │             │             │      │       │
│  │  ┌────▼─────────────▼─────────────▼─────────────▼────┐│       │
│  │  │              RAG编排层（LangChain）                 ││       │
│  │  │  ┌────────┐  ┌─────────┐  ┌────────┐  ┌────────┐ ││       │
│  │  │  │ 文档分块│  │向量化   │  │向量检索│  │重排序  │ ││       │
│  │  │  │ 递归策略│  │Embedding│  │pgvector│  │ Rerank │ ││       │
│  │  │  └────────┘  └─────────┘  └────────┘  └────────┘ ││       │
│  │  └───────────────────────────────────────────────────┘│       │
│  └───────────────────────────────────────────────────────┘       │
│                                                                     │
│  ┌──────────────────┐  ┌──────────────────┐                      │
│  │ PostgreSQL+       │  │   Redis（可选）   │                      │
│  │ pgvector          │  │  会话缓存/限流    │                      │
│  │ 向量数据存储       │  │                  │                      │
│  └──────────────────┘  └──────────────────┘                      │
└────────┬─────────────────────┬────────────────────────────────────┘
         │                     │
         ▼                     ▼
┌─────────────────────┐  ┌──────────────────────────────────────────┐
│  MySQL 8.0 RDS      │  │     阿里云百炼平台（DashScope）           │
│  (2核4G)            │  │                                          │
│                     │  │  ┌────────────┐  ┌─────────────────┐    │
│  · users            │  │  │qwen3.7-plus│  │qwen3.5-omni-plus│    │
│  · consultations    │  │  │(文本/图片/  │  │(全模态：音视频)  │    │
│  · messages         │  │  │ 视频)      │  │                 │    │
│  · knowledge_docs   │  │  └────────────┘  └─────────────────┘    │
│  · reports          │  │  ┌────────────┐  ┌─────────────────┐    │
│  · reviews          │  │  │text-        │  │fun-asr-realtime │    │
│  · audit_logs       │  │  │embedding-v4│  │(语音识别)       │    │
│                     │  │  └────────────┘  └─────────────────┘    │
│                     │  │  ┌────────────┐  ┌─────────────────┐    │
│                     │  │  │qwen3-rerank│  │cosyvoice-v3.5   │    │
│                     │  │  │(重排序)    │  │(语音合成)       │    │
│                     │  │  └────────────┘  └─────────────────┘    │
└─────────────────────┘  └──────────────────────────────────────────┘
```

### 6.2 数据流架构

```
【知识库录入流程】
管理员上传文档 → FastAPI接收 → 递归字符分块(512 tokens, 64 overlap)
    → text-embedding-v4向量化 → pgvector存储 → MySQL记录元数据

【用户对话流程】
用户输入(文字/语音/图片/视频)
    │
    ├─[语音]→ OSS上传 → fun-asr-realtime转文字
    ├─[图片]→ OSS上传 → 提取URL
    ├─[视频]→ OSS上传 → 提取URL
    │
    ▼
FastAPI接收 → RAG检索（用户问题向量化 → pgvector Top-K → qwen3-rerank重排序）
    │
    ▼
组装Prompt（检索到的知识片段 + 对话历史 + 用户输入 + 多模态URL）
    │
    ▼
调用 qwen3.7-plus（流式SSE输出）→ 前端实时显示
    │
    ▼
对话结束 → 存储对话记录到MySQL

【诊断报告流程】
对话积累足够信息 → qwen3.7-plus生成结构化诊断报告（JSON）
    → 存入MySQL reports表 → 通知咨询师审核
    → 咨询师在后台审核/修改 → 下发给用户
```

### 6.3 模块划分

| 模块 | 职责 | 技术栈 |
|------|------|--------|
| **Web前端** | 用户交互界面、SSE接收、文件上传 | React + TypeScript + Ant Design |
| **API网关层** | 请求路由、认证鉴权、限流 | FastAPI middleware |
| **对话服务** | 多轮对话管理、SSE流式输出 | FastAPI + SSE |
| **RAG服务** | 文档分块、向量化、检索、重排序 | LangChain + pgvector |
| **多模态服务** | 图片/视频/语音处理编排 | FastAPI + 百炼API |
| **知识库管理** | 文档上传、分块、索引管理 | FastAPI + LangChain |
| **报告服务** | 诊断报告生成、模板渲染 | FastAPI + Jinja2 |
| **审核服务** | 人工审核流程、状态机 | FastAPI + MySQL |
| **后台管理** | 知识库管理、用户管理、数据统计 | React Admin |

---

## 7. 知识库RAG设计

### 7.1 文档分块策略

基于2026年NAACL基准测试研究结论，**分块策略对检索质量的影响与Embedding模型选择相当甚至更大**。

#### 7.1.1 推荐策略：递归字符分块（Recursive Character Splitting）

**理由**：
- 2026年Vecta基准测试中，递归512-token分块以69%端到端准确率位列第一
- 生产环境中最推荐的默认策略
- 尽可能保留文档语义结构，每块内部主题相对聚焦

**参数配置**：

| 参数 | 推荐值 | 理由 |
|------|--------|------|
| chunk_size | 512 tokens | 2026年多个基准测试最优区间256-512的甜点值 |
| overlap | 64 tokens | chunk_size的12.5%，在10%-20%推荐范围内 |
| 分隔符优先级 | `\n\n` → `\n` → `。！？` → ` ` → `""` | 从大到小递归切分，优先在段落边界切 |

**实现示例（Python + LangChain）**：

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=64,
    separators=["\n\n", "\n", "。", "！", "？", "；", "，", " ", ""],
    length_function=lambda text: len(text)  # 中文按字符数近似token
)

chunks = splitter.split_text(document_text)
```

#### 7.1.2 各策略对比

| 策略 | 实现难度 | 语义完整性 | 计算成本 | 2026基准准确率 | 推荐场景 |
|------|----------|-----------|----------|---------------|----------|
| 固定大小 | 最低 | 低 | 极低 | ~50% | 日志、数据导出 |
| **递归字符** | **低** | **高** | **低** | **69%（第一）** | **绝大多数场景（本项目首选）** |
| 文档结构 | 中 | 极高 | 低 | 因场景而异 | Markdown/HTML文档 |
| 语义分块 | 高 | 极高 | 高（需调Embedding） | 54%（碎片风险） | 主题跳跃散文 |
| 父子分块 | 中高 | 高 | 中 | 高（无直接基准） | 高精度生产场景 |

> **关键警告**：不要用字符数代替Token数。中文字符通常对应1-2个Token，用字符数设定chunkSize会导致实际Chunk大小与嵌入模型的Token限制严重不符。

### 7.2 Embedding模型选择

**选择 `text-embedding-v4`**：
- 百炼平台原生支持，与通义大模型生态一致
- 默认1024维，平衡效果与存储
- 最大输入8,192 Token，覆盖512-token分块
- 支持阶梯计费，大规模使用成本可控

**维度选择建议**：
- 本项目选择1024维（默认值），平衡效果好
- 未来如需更高精度可切换至1536或2048维（需全库重建）

### 7.3 RAG检索流程

```
用户问题 → text-embedding-v4向量化
    │
    ▼
pgvector向量检索（Top-10，余弦相似度）
    │
    ▼
qwen3-rerank重排序（对Top-10结果精排）
    │
    ▼
取Top-3~5最相关片段
    │
    ▼
拼接到Prompt：[系统指令] + [知识库片段] + [对话历史] + [用户问题]
    │
    ▼
调用qwen3.7-plus生成回复（SSE流式输出）
```

### 7.4 知识库数据模型

**MySQL表设计**：

```sql
-- 知识库文档表
CREATE TABLE knowledge_documents (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL,
    content LONGTEXT NOT NULL,
    doc_type ENUM('methodology', 'case', 'template', 'faq') NOT NULL,
    tags JSON,
    status ENUM('pending', 'chunked', 'indexed', 'error') DEFAULT 'pending',
    chunk_count INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 知识库片段表（与pgvector中的向量对应）
CREATE TABLE knowledge_chunks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    doc_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    token_count INT,
    pgvector_id VARCHAR(64),  -- pgvector中的向量ID
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (doc_id) REFERENCES knowledge_documents(id)
);
```

**PostgreSQL + pgvector表设计**：

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_embeddings (
    id BIGINT PRIMARY KEY,
    doc_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW索引（高性能近似最近邻搜索）
CREATE INDEX ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops);
```

---

## 8. Web对话式架构设计

### 8.1 流式对话：SSE实现

#### 8.1.1 后端实现（FastAPI）

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

@app.get("/api/chat/stream")
async def chat_stream(message: str, session_id: str):
    async def event_generator():
        # 1. RAG检索
        retrieved_chunks = await rag_search(message)

        # 2. 组装Prompt
        prompt = build_prompt(retrieved_chunks, message)

        # 3. 调用百炼API（流式）
        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
                json={
                    "model": "qwen3.7-plus",
                    "messages": prompt,
                    "stream": True
                },
                headers={"Authorization": f"Bearer {API_KEY}"}
            ) as response:
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        yield f"data: {line[6:]}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Nginx禁用缓冲
        }
    )
```

#### 8.1.2 前端实现（React）

```typescript
const useChatStream = () => {
  const [messages, setMessages] = useState<string[]>([]);

  const sendMessage = (message: string) => {
    const eventSource = new EventSource(
      `/api/chat/stream?message=${encodeURIComponent(message)}&session_id=xxx`
    );

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.choices?.[0]?.delta?.content) {
        setMessages(prev => [...prev, data.choices[0].delta.content]);
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
    };
  };

  return { messages, sendMessage };
};
```

#### 8.1.3 SSE vs WebSocket 选型总结

| 维度 | SSE（选用） | WebSocket |
|------|------------|-----------|
| 通信方向 | 单向（服务端→客户端） | 全双工 |
| 协议 | HTTP/HTTPS | WebSocket (ws/wss) |
| 自动重连 | 浏览器原生支持 | 需手动实�� |
| 代理穿透 | HTTP天然穿透 | 部分代理可能拦截 |
| 实现复杂度 | 低 | 中到高 |
| 百炼API兼容 | 原生SSE格式 | 需协议转换 |
| 二进制数据 | 不支持（仅UTF-8文本） | 支持 |
| 本项目适用性 | **完全满足**（对话场景） | 过度设计 |

### 8.2 文件上传方案：STS临时签名 + 前端直传OSS

#### 8.2.1 架构设计

```
┌────────┐     1.请求STS      ┌──────────┐     2.签发STS      ┌─────────┐
│ 前端   │ ──────────────────▶│ FastAPI  │ ──────────────────▶│ 阿里云   │
│        │◀──────────────────│  后端    │◀──────────────────│ STS服务  │
│        │     STS临时凭证     └──────────┘     临时凭证        └─────────┘
│        │
│        │     3.直传文件
│        │──────────────────────────────────────────────────────▶┌─────────┐
│        │                                                        │ 阿里云   │
│        │◀─────────────────────────────────────────────────────│ OSS     │
│        │     4.上传成功返回URL                                   └─────────┘
│        │
│        │     5.提交对话（携带文件URL）
│        │──────────────────────────────────────────────────────▶┌──────────┐
│        │                                                        │ FastAPI  │
│        │                                                        │ 后端     │
└────────┘                                                        └──────────┘
```

#### 8.2.2 文件类型与限制

| 文件类型 | 支持格式 | 大小限制 | OSS路径规则 | 处理方式 |
|----------|----------|----------|------------|----------|
| 图片 | JPG/PNG/GIF/WebP | ≤ 10MB | `consultation/{userId}/images/{timestamp}.{ext}` | URL直传百炼多模态API |
| 语音 | MP3/WAV/M4A | ≤ 50MB | `consultation/{userId}/audio/{timestamp}.{ext}` | OSS URL → fun-asr-realtime转文字 |
| 视频 | MP4/MOV | ≤ 100MB | `consultation/{userId}/videos/{timestamp}.{ext}` | OSS URL → qwen3.7-plus视频分析 |
| 文档 | PDF/TXT/DOCX | ≤ 20MB | `knowledge/{docId}/original.{ext}` | 文本提取 → 分块 → 向量化 |

#### 8.2.3 STS签发实现

```python
from alibabacloud_sts20150401.client import Client as StsClient
from alibabacloud_tea_openapi import models as open_api_models

@app.post("/api/upload/sts")
async def get_upload_sts(file_type: str, filename: str):
    """签发OSS临时上传凭证"""
    # 构造OSS路径
    object_key = f"consultation/{current_user.id}/{file_type}/{int(time.time())}_{filename}"

    # 调用STS签发临时凭证
    policy = {
        "Version": "1",
        "Statement": [{
            "Effect": "Allow",
            "Action": ["oss:PutObject"],
            "Resource": [f"acs:oss:*:*:{bucket_name}/{object_key}"]
        }]
    }

    sts_credentials = sts_client.assume_role(
        role_arn=OSS_ROLE_ARN,
        role_session_name="upload",
        policy=json.dumps(policy),
        duration_seconds=900  # 15分钟有效期
    )

    return {
        "access_key_id": sts_credentials.access_key_id,
        "access_key_secret": sts_credentials.access_key_secret,
        "security_token": sts_credentials.security_token,
        "endpoint": OSS_ENDPOINT,
        "bucket": OSS_BUCKET,
        "object_key": object_key
    }
```

### 8.3 对话历史存储方案

**MySQL表设计**：

```sql
-- 咨询会话表
CREATE TABLE consultations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    status ENUM('active', 'reporting', 'reviewing', 'completed', 'closed') DEFAULT 'active',
    title VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_status (user_id, status)
);

-- 对话消息表
CREATE TABLE chat_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    consultation_id BIGINT NOT NULL,
    role ENUM('user', 'assistant', 'system') NOT NULL,
    content TEXT NOT NULL,
    content_type ENUM('text', 'image', 'audio', 'video', 'mixed') DEFAULT 'text',
    attachments JSON,  -- [{type: 'image', url: 'oss://...'}, ...]
    token_count INT,
    rag_chunks JSON,   -- 检索到的知识库片段ID列表
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id),
    INDEX idx_consultation (consultation_id, created_at)
);

-- 诊断报告表
CREATE TABLE diagnostic_reports (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    consultation_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    content JSON NOT NULL,  -- 结构化报告内容
    status ENUM('draft', 'pending_review', 'approved', 'rejected', 'delivered') DEFAULT 'draft',
    reviewer_id BIGINT,
    review_comment TEXT,
    reviewed_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id)
);
```

**对话历史管理策略**：

| 策略 | 说明 |
|------|------|
| 滑动窗口 | 保留最近10轮对话作为上下文，超出部分摘要压缩 |
| Token预算 | 上下文总Token控制在8000以内（预留知识库片段空间） |
| 会话隔离 | 每个咨询会话独立，不跨会话共享历史 |
| 持久化 | 所有对话实时写入MySQL，支持回溯和审核 |
| RAG上下文 | 每轮对话检索Top-3~5知识库片段，拼接到当前上下文 |

---

## 9. 不可行/高风险功能警告

### 9.1 不可行功能

| 功能 | 不可行原因 | 替代方案 |
|------|-----------|----------|
| **在4核8G服务器上自建Milvus** | Milvus Standalone最低需8核16G，etcd+MinIO+Milvus三组件无法在4核8G上稳定运行 | 使用pgvector，未来需求增长后迁移 |
| **实时端到端语音对话（WebSocket）** | 4核8G服务器同时处理多路WebSocket连接 + 实时ASR/TTS + LLM推理，资源不足 | 采用"录制→上传→ASR→文本→LLM→TTS→播放"的异步流程 |
| **本地部署大模型** | 4核8G无法运行任何有意义的本地LLM（最小Qwen-1.8B也需4核8G+专用） | 使用百炼平台API调用，不在本地部署模型 |
| **视频实时分析（流式输入）** | 视频流式输入需要WebSocket全双工 + 大带宽，服务器资源不足 | 用户上传视频到OSS → 传URL给百炼API分析 |

### 9.2 高风险功能

| 风险项 | 风险等级 | 风险描述 | 缓解措施 |
|--------|----------|----------|----------|
| **百炼API单点依赖** | 高 | 所有AI能力依赖百炼平台，若平台故障则服务完全不可用 | 实现降级策略（规则引擎兜底）；监控API健康状态；缓存常见问题答案 |
| **大模型幻觉** | 高 | AI可能生成不符合品牌咨询专业知识的内容 | RAG检索约束 + 人工审核环节 + 系统Prompt中强调"仅基于知识库回答" |
| **API费用失控** | 中 | 用户大量上传视频/图片，Token消耗暴增 | 设置每日API调用上限；用户配额管理；非核心环节使用Flash模型 |
| **OSS存储超量** | 中 | 视频文件较大，500G可能不够长期使用 | 设置文件过期策略（如30天自动清理）；限制单用户存储量 |
| **PostgreSQL与MySQL双数据库** | 中 | 需维护两套数据库，增加运维复杂度 | 使用Docker管理PG；数据一致性通过应用层保证；未来可评估迁移至单一PG |
| **pgvector并发限制** | 低 | 高并发时pgvector查询性能可能下降 | MVP阶段并发低（10-20），完全可控；监控查询延迟 |
| **多模态内容安全** | 中 | 用户上传不当图片/视频内容 | 接入阿里云内容安全API进行审核；人工审核环节 |
| **知识库质量** | 高 | "Garbage In, Garbage Out" — 知识库文档质量直接决定AI回答质量 | 文档录入前人工审核；建立知识库质量评估标准；定期更新优化 |

### 9.3 性能风险与缓解

| 风险 | 缓解措施 |
|------|----------|
| 百炼API响应延迟（P99 > 10s） | SSE流式输出降低感知延迟；设置超时重试机制 |
| 大文件上传超时 | STS直传OSS（不经过应用服务器）；分片上传（>50MB文件） |
| RAG检索质量不稳定 | Rerank重排序提升精度；定期评估Recall@K指标；优化分块参数 |
| 内存不足（4核8G） | Docker限制各容器内存；Redis缓存可选（内存紧张时禁用）；PG配置调优 |

---

## 10. 部署方案

### 10.1 部署架构

```
┌─────────────────────────────────────────────────────┐
│           阿里云ECS（4核8G Ubuntu 24.04）             │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │              Docker Engine                   │   │
│  │                                             │   │
│  │  ┌──────────────┐  ┌──────────────────┐    │   │
│  │  │  Nginx        │  │  FastAPI App     │    │   │
│  │  │  (反向代理     │  │  (Python 3.12)   │    │   │
│  │  │  + 静态资源   │  │  Port: 8000      │    │   │
│  │  │  + SSE透传)   │  │                  │    │   │
│  │  │  Port: 80/443 │  │                  │    │   │
│  │  └──────────────┘  └──────────────────┘    │   │
│  │                                             │   │
│  │  ┌──────────────────┐  ┌────────────────┐  │   │
│  │  │ PostgreSQL 16    │  │  Redis 7       │  │   │
│  │  │ + pgvector       │  │  (可选)         │  │   │
│  │  │ Port: 5432       │  │  Port: 6379    │  │   │
│  │  └──────────────────┘  └────────────────┘  │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  系统预留：2GB（OS + Docker Engine）                  │
│  应用可用：约6GB                                     │
│    · FastAPI: ~1GB                                  │
│    · PostgreSQL: ~2GB                               │
│    · Nginx: ~0.1GB                                  │
│    · Redis: ~0.5GB（可选）                           │
│    · 缓冲: ~2.4GB                                    │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
┌─────────────────┐        ┌──────────────────┐
│ 阿里云RDS        │        │  阿里云百炼平台    │
│ MySQL 8.0       │        │  (DashScope API)  │
│ (2核4G)         │        │                  │
│ Port: 3306      │        │  内网调用          │
└─────────────────┘        └──────────────────┘
         │
         ▼
┌─────────────────┐
│ 阿里云OSS        │
│ (500G)          │
│ 文件存储          │
└─────────────────┘
```

### 10.2 Docker Compose 部署配置

```yaml
# docker-compose.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./frontend/dist:/usr/share/nginx/html
    depends_on:
      - app
    restart: always
    deploy:
      resources:
        limits:
          memory: 256M

  app:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - MYSQL_HOST=${MYSQL_HOST}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - PG_HOST=postgres
      - PG_PASSWORD=${PG_PASSWORD}
      - OSS_ACCESS_KEY_ID=${OSS_ACCESS_KEY_ID}
      - OSS_ACCESS_KEY_SECRET=${OSS_ACCESS_KEY_SECRET}
      - OSS_BUCKET=${OSS_BUCKET}
      - OSS_ENDPOINT=${OSS_ENDPOINT}
      - STS_ROLE_ARN=${STS_ROLE_ARN}
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
    deploy:
      resources:
        limits:
          memory: 1G

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_DB=brand_consult
      - POSTGRES_USER=brand_app
      - POSTGRES_PASSWORD=${PG_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./db/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U brand_app"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always
    deploy:
      resources:
        limits:
          memory: 2G

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: always
    deploy:
      resources:
        limits:
          memory: 512M

volumes:
  pgdata:
```

### 10.3 Nginx配置要点

```nginx
# SSE关键配置
location /api/chat/stream {
    proxy_pass http://app:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;           # 关键：禁用缓冲
    proxy_cache off;
    proxy_read_timeout 300s;       # SSE长连接超时
    chunked_transfer_encoding on;
}
```

### 10.4 PostgreSQL初始化

```sql
-- init.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE knowledge_embeddings (
    id BIGSERIAL PRIMARY KEY,
    doc_id BIGINT NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- HNSW索引
CREATE INDEX idx_knowledge_embeddings_vector
ON knowledge_embeddings USING hnsw (embedding vector_cosine_ops);

-- 文档ID索引
CREATE INDEX idx_knowledge_embeddings_doc
ON knowledge_embeddings (doc_id);
```

### 10.5 部署清单

| 步骤 | 操作 | 验证方式 |
|------|------|----------|
| 1 | 安装Docker + Docker Compose | `docker --version` |
| 2 | 配置环境变量（.env文件） | 检查所有变量非空 |
| 3 | 构建FastAPI镜像 | `docker-compose build` |
| 4 | 启动所有服务 | `docker-compose up -d` |
| 5 | 执行数据库迁移 | `alembic upgrade head` |
| 6 | 初始化pgvector扩展 | 检查 `\dx vector` |
| 7 | 配置Nginx SSL证书 | `curl https://domain` |
| 8 | 配置百炼API Key | 调用测试API |
| 9 | 配置OSS + STS角色 | 测试文件上传 |
| 10 | 录入初始知识库 | 验证向量化+检索 |
| 11 | 端到端功能测试 | 完整对话流程 |

### 10.6 监控与运维

| 监控项 | 工具 | 告警阈值 |
|--------|------|----------|
| CPU使用率 | 阿里云云监控 | > 80% |
| 内存使用率 | 阿里云云监控 | > 85% |
| 磁盘使用率 | 阿里云云监控 | > 80% |
| API响应时间 | 应用日志 | P99 > 15s |
| 百炼API调用量 | 百炼控制台 | 日费用 > 50元 |
| MySQL连接数 | RDS控制台 | > 80% |
| PG查询延迟 | pg_stat_statements | P99 > 200ms |
| OSS存储量 | OSS控制台 | > 400GB |

---

## 11. 成本预估

### 11.1 基础设施成本（月度）

| 项目 | 规格 | 月费用 | 备注 |
|------|------|--------|------|
| ECS应用服务器 | 4核8G | ~200元 | 已有 |
| RDS MySQL | 2核4G | ~150元 | 已有 |
| OSS对象存储 | 500G | ~75元 | 已有 |
| **基础设施小计** | | **~425元** | 已有资源 |

### 11.2 新增成本（月度）

| 项目 | 说明 | 预估月费用 |
|------|------|-----------|
| PostgreSQL（Docker自建） | 与应用服务器共存 | 0元 |
| Redis（Docker自建） | 与应用服务器共存 | 0元 |
| 域名 + SSL | 已有或新购 | ~10元 |
| **新增基础设施小计** | | **~10元** |

### 11.3 大模型API成本（月度预估）

**假设**：日均50次咨询，每次咨询10轮对话

| 调用类型 | 模型 | 日调用量 | 日Token消耗 | 日费用 | 月费用 |
|----------|------|----------|------------|--------|--------|
| 对话生成 | qwen3.7-plus | 500次 | 输入~2.5M + 输出~1.5M | ~5.5元 | ~165元 |
| 互动问题 | qwen3.6-flash | 500次 | 输入~1M + 输出~0.5M | ~1.0元 | ~30元 |
| 报告生成 | qwen3.7-plus | 50次 | 输入~0.25M + 输出~0.15M | ~0.55元 | ~16.5元 |
| Embedding | text-embedding-v4 | 500次（含缓存命中） | ~0.5M | ~0.5元 | ~15元 |
| Rerank | qwen3-rerank | 500次 | - | ~0.5元 | ~15元 |
| 语音识别 | fun-asr-realtime | 50次 | - | ~0.04元 | ~1.2元 |
| 语音合成 | cosyvoice-v3.5-plus | 50次 | - | ~0.09元 | ~2.7元 |
| **API小计** | | | | **~8.18元/天** | **~245.4元/月** |

> **注意**：以上为原价预估。新用户有7000万免费Token额度（约可支撑前2-3个月）。使用节省计划可再降10-50%。

### 11.4 总成本预估

| 项目 | 月费用 |
|------|--------|
| 基础设施（已有） | ~425元 |
| 新增基础设施 | ~10元 |
| 大模型API | ~245元 |
| **总计** | **~680元/月** |

> MVP阶段（前3个月）利用免费Token额度，API成本可降至约50-100元/月，总成本约500元/月。

---

## 12. 附录：参考资料

### 12.1 阿里云百炼平台

- 百炼模型列表与计费：https://help.aliyun.com/zh/model-studio/models
- 百炼计费规则详解：https://help.aliyun.com/zh/model-studio/product-billing
- 百炼模型价格：https://www.alibabacloud.com/help/zh/model-studio/model-pricing
- 文本生成模型：https://help.aliyun.com/zh/model-studio/text-generation-model/
- 视觉理解模型：https://help.aliyun.com/zh/model-studio/vision-model/
- 全模态模型：https://help.aliyun.com/zh/model-studio/omni/
- Embedding与重排序：https://help.aliyun.com/zh/model-studio/embedding-rerank-model/
- DashScope API参考：https://www.alibabacloud.com/help/zh/model-studio/qwen-api-via-dashscope
- 首次调用千问API：https://help.aliyun.com/zh/model-studio/first-api-call-to-qwen

### 12.2 向量检索方案

- OpenSearch向量检索版计费：https://help.aliyun.com/zh/open-search/vector-search-edition/billing-overview-of-vector-search-edition
- Milvus vs pgvector对比：https://zilliz.com.cn/comparison/milvus-vs-pgvector
- 2026向量数据库选型报告：https://www.heibaos.com/post/369563009417216/vector-database-selection-comparison-2026

### 12.3 RAG与分块策略

- RAG文档分块策略完全指南：https://www.smallyoung.cn/docs/027-RAG文档分块策略完全指南
- RAG Chunking全攻略：https://jishuzhan.net/article/2047512859953922049
- NAACL 2025 Chunking Study：https://arxiv.org/abs/2410.13070
- Late Chunking vs Contextual Retrieval：https://arxiv.org/abs/2504.19754

### 12.4 流式通信

- 大模型流式输出SSE vs WebSocket：https://jishuzhan.net/article/2055810393448747009
- AI大模型实时通信为什么选SSE：https://developer.aliyun.com/article/1737834

### 12.5 阿里云OSS

- STS临时授权访问：https://www.alibabacloud.com/help/zh/oss/developer-reference/authorized-access-2
- STS临时凭证上传文件至OSS：https://help.aliyun.com/zh/oss/developer-reference/use-temporary-access-credentials-provided-by-sts-to-access-oss

---

> **文档结束**
>
> 本架构文档基于2026年7月最新技术调研编写。所有模型名称、价格、API规格均以阿里云百炼平台官方文档为准。生产部署前建议进行POC验证，用业务真实Query测试RAG检索Recall@K指标。
