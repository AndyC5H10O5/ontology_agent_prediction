# Personal Health Assistant

面向个人的**命令行健康助理**：通过多轮对话收集信息，在健康教育/自我管理取向（**非诊断、非处方**）下整理说明，并写入本地 Markdown。项目采用 OpenAI 兼容的 **Chat Completions + Tools** 接口（默认 **DeepSeek**），代码集中在 `src/`。

---

## 核心流程（可概括为三步）

1. **收集信息**：主模型按系统提示引导问诊；可结合本地 **问诊 skill**（`load_consult_skill`）减少重复提问。
2. **结构化与异步下游**：信息足够即将成稿时，模型先调用 **`submit_consult_content`**，提交 `symptom_course` + 多轮 `question`/`answer` 快照；工具写审计日志并 **发布事件**，由后台消费者并行更新 **长期记忆** 与 **skills**（均调用独立配置的模型，不阻塞对话）。
3. **输出方案**：在工具成功回执后，模型再调用 **`write_file`**，将完整方案写入 `treatment_plan/`。

---

## 主要关注

### 长期记忆（`harness/memory/personal_health.md`）

- 每次请求会在 **system** 末尾拼接 `harness/memory/personal_health.md` 内容（若文件存在），使主对话与历史健康摘要保持一致。
- 更新由 **`memory_consumer`** 在后台完成：读取旧文件 + 本轮结构化问诊，经模型合并/去重，超长时再 **全篇压缩**（阈值见环境变量），最后通过专用 IO 写回（**不**走 `write_file` 工具）。

### 结构化入队与事件总线（`src/post_manager_layer/`）

- **`submit_consult_content`** 校验后追加 **`logs/consult_content.jsonl`**，并对 **`ConsultContentEvent`** 执行 **`EventBus.publish`**。
- **扇出**：每个已注册消费者在 **独立 daemon 线程** 中收到同一事件；当前默认注册 **记忆消费者** 与 **skills 消费者**。
- 实现为进程内广播，**不是** RabbitMQ/Kafka；进程退出时未跑完的后台任务不保证完成，jsonl 可用于人工审计或后续重放。

### 问诊 Skills 进化（`harness/skills/`）

- **语义**：仅维护「**下次建议问哪些问题**」的正向列表（Markdown）；用户对某问在自然语言上等同于「无/跳过」时，由 **skills 专用模型** 推理后不再写入该问；旧 skill 中已有则删除。
- **触发**：与记忆相同，在 **`submit_consult_content`** 之后由 **`skills_consumer`** 异步写 **`harness/skills/by_id/<slug>.md`** 并维护 **`harness/skills/index.json`**。
- **加载**：新问诊开始时由主模型调用 **`load_consult_skill(symptom_query)`**，按索引子串匹配 0/1/多条并返回内容或候选列表。

### 提示词统一管理（`src/config/system_prompt.py`）

- **`HEALTH_AGENT_SYSTEM_PROMPT`**：主对话。
- **`MEMORY_CONSUMER_MERGE_SYSTEM_PROMPT`** / **`MEMORY_CONSUMER_COMPRESS_SYSTEM_PROMPT`**：记忆沉淀模型。
- **`SKILLS_CONSUMER_SYSTEM_PROMPT`**：skills 沉淀模型。

修改消费者行为时只需编辑该文件对应常量。

### RAG 检索增强（Ollama + Chroma）

- 成稿前可调用 `search_knowledge`：从本地知识库召回相关片段，辅助主模型做更稳健的健康教育分析。
- Embedding 使用本机 Ollama；向量索引使用 Chroma 嵌入式（持久化目录默认 `harness/chroma_db/`）。
- 知识源目录默认 `harness/knowledge_base/`，首版支持 `md/txt/pdf/epub`。

---

## 目录结构（概要）

| 路径 | 说明 |
|------|------|
| `src/main.py` | 入口：加载配置、启动 `agent_loop` |
| `src/agent_core/loop_core.py` | REPL、HTTP 调主模型、工具循环、system 注入记忆块 |
| `src/config/` | `api_key.py`（`ModelConfig`）、`system_prompt.py`（全部 system 文案） |
| `src/tools/` | `read_file`、`load_consult_skill`、`submit_consult_content`、`search_knowledge`、`write_file` |
| `src/post_manager_layer/` | 事件总线、bootstrap、memory/skills 消费者、路径与专用 IO；详见包内 [`README.md`](src/post_manager_layer/README.md) |
| `src/RAG/` | RAG 组件：文档读取、切块、Ollama embedding、Chroma 检索 |
| `src/build_index.py` | RAG 索引构建入口脚本（与 `main.py` 同级） |
| `src/session_store/` | 本地会话：`harness/session/index.json` 与各会话 JSON |
| `src/cli/display.py` | 终端颜色与输出 |
| `harness/memory/personal_health.md` | 长期健康记忆正文（可选，由消费者维护） |
| `harness/skills/index.json` + `harness/skills/by_id/*.md` | 问诊 skill 索引与按症状主题落盘 |
| `logs/` | `consult_content.jsonl`、`memory_worker.log`、`skills_worker.log` 等 |
| `harness/knowledge_base/` | 本地知识库源文件（`md/txt/pdf/epub`） |
| `harness/chroma_db/` | Chroma 向量索引持久化目录（建议忽略版本管理） |
| `treatment_plan/` | 主模型生成的治疗方案等（默认被 `.gitignore` 忽略时需自行纳入版本策略） |

---

## 环境与运行

**依赖**（需在环境中安装）：

- `httpx`
- `python-dotenv`
- `chromadb`
- `pypdf`（当知识库包含 PDF 时需要）

**配置**：在**项目根目录**放置 `.env`（勿提交仓库），至少包含：

```env
DEEPSEEK_API_KEY=你的密钥
```

可选：`MODEL_ID`、`DEEPSEEK_BASE_URL`；记忆与 skills 沉淀可单独指定 `MEMORY_*`、`SKILLS_*`（见下表）。

若启用 RAG，建议额外配置：

```env
RAG_ENABLED=1
RAG_KB_DIR=harness/knowledge_base
RAG_CHROMA_DIR=harness/chroma_db
RAG_COLLECTION_NAME=health_knowledge
RAG_OLLAMA_BASE_URL=http://127.0.0.1:11434
RAG_EMBED_MODEL=bge-m3
RAG_TOP_K=4
RAG_CHUNK_SIZE=800
RAG_CHUNK_OVERLAP=120
```

**启动**（需在 `src` 为工作目录，以便包导入正确）：

```bash
cd src
python -B main.py
```

若未设置 `DEEPSEEK_API_KEY`，程序会退出（`main.py` 会检查 `config.api_key`）。

### 构建 RAG 索引（可选）

1. 启动本地 Ollama 并准备 embedding 模型（示例：`ollama pull bge-m3`）。
2. 将知识文件放入 `harness/knowledge_base/`（支持 `md/txt/pdf/epub`）。
3. 在 `src` 目录执行：

```bash
python -B build_index.py
```

成功后会在 `harness/chroma_db/` 生成向量索引。

---

## 主模型工具一览

| 工具 | 作用 |
|------|------|
| `read_file` | 读取项目根下相对路径文件（含安全路径校验） |
| `load_consult_skill` | 按 `symptom_query` 检索并加载 `harness/skills/` 中问诊建议问题 |
| `submit_consult_content` | 提交本轮结构化问诊快照，写 jsonl 并 **publish** 事件 |
| `search_knowledge` | 检索本地知识库片段（snippet/source/chunk_id/score），用于成稿前专业分析 |
| `write_file` | 写入项目内文件；方案类内容应放在 `treatment_plan/` 下 |

---

## 会话命令（REPL）

支持 `/list`、`/new [标签]`、`/switch <编号或前缀>`、`/delete <编号或前缀>`、`/help`。说明可参考仓库内会话相关文档（若存在）；会话数据在 `harness/session/`。

---

## 环境变量参考

| 变量 | 含义 |
|------|------|
| `DEEPSEEK_API_KEY` | 主对话 API Key（必填） |
| `MODEL_ID` | 主模型 ID，默认 `deepseek-chat` |
| `DEEPSEEK_BASE_URL` | API 根 URL，默认 `https://api.deepseek.com` |
| `MEMORY_MODEL_ID` / `MEMORY_API_KEY` / `MEMORY_DEEPSEEK_BASE_URL` | 记忆消费者；未设则与主对话一致 |
| `MEMORY_MAX_CHARS` / `MEMORY_MIN_CHARS` | 记忆合并后触发压缩与压缩目标下限 |
| `SKILLS_MODEL_ID` / `SKILLS_API_KEY` / `SKILLS_DEEPSEEK_BASE_URL` | skills 消费者；未设则与主对话一致 |
| `RAG_ENABLED` | 是否启用 RAG（`1/true/on` 为启用） |
| `RAG_KB_DIR` / `RAG_CHROMA_DIR` / `RAG_COLLECTION_NAME` | 知识源目录 / 向量库目录 / collection 名称 |
| `RAG_OLLAMA_BASE_URL` / `RAG_EMBED_MODEL` | Ollama 地址与 embedding 模型名 |
| `RAG_TOP_K` / `RAG_CHUNK_SIZE` / `RAG_CHUNK_OVERLAP` | 默认召回数、切块长度、切块重叠 |

---

## 隐私与合规提示

- `harness/memory/`、`harness/skills/`、`logs/`、`harness/session/` 可能含个人健康相关描述，请自行决定 **是否纳入 `.gitignore`** 与备份策略。
- 本助理输出仅为健康教育与自我管理参考，**不能替代执业医师诊疗**。

---

## 延伸阅读

- 异步层与消费者细节：[`src/post_manager_layer/README.md`](src/post_manager_layer/README.md)
