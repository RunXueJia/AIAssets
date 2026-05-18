# LLM 调用设计

LLM 是内容生产链路的核心依赖，应作为独立基础设施模块建设，而不是散落在选题、脚本、分镜等业务 Service 中直接调用。所有 LLM 生成、调试、修复和重试调用统一采用 OpenAI Chat Completions 兼容的 SSE 流式输出格式。

## 1. 设计目标

- 支持 OpenAI Chat Completions 兼容接口和本地模型接口。
- 所有 LLM 调用必须使用 SSE 流式输出，后端和前端均按 OpenAI 标准 chunk 解析。
- 支持按场景选择模型：选题、脚本、分镜、质检、图文页、知识卡片、资料包、日报建议。
- 支持 Prompt 模板版本化，便于优化和回滚。
- 支持结构化输出，流式聚合完成后所有正式生成结果必须通过 JSON Schema 校验。
- 支持调用日志、成本估算、失败重试、限流和降级。
- 后台可配置模型和 Prompt，但 API Key 不允许明文返回前端。

## 2. 后端分层

推荐目录：

```text
services/api/app/
  api/v1/endpoints/
    llm_providers.py
    llm_models.py
    prompt_templates.py
    llm_call_logs.py
  models/
    llm_provider.py
    llm_model.py
    prompt_template.py
    llm_call_log.py
  repositories/
    llm_provider.py
    llm_model.py
    prompt_template.py
    llm_call_log.py
  services/
    llm_gateway.py
    prompt_render.py
    llm_output_parser.py
  integrations/
    llm/
      base.py
      openai_compatible.py
      local_model.py
```

业务 Service 只能调用 `LLMGatewayService`，不能直接调用供应商 SDK。`LLMGatewayService` 只暴露流式调用能力，不提供非流式生成方法。

## 3. SSE 标准

### 3.1 上游请求

供应商 `base_url` 按 OpenAI 兼容 `/v1` 根地址配置，实际调用固定走 `{base_url}/chat/completions`。供应商请求体必须使用 OpenAI Chat Completions 兼容格式，并强制包含：

```json
{
  "model": "model-name",
  "messages": [
    {
      "role": "system",
      "content": "system prompt"
    },
    {
      "role": "user",
      "content": "user prompt"
    }
  ],
  "stream": true,
  "stream_options": {
    "include_usage": true
  }
}
```

结构化输出场景可在模型支持时增加 `response_format`，但仍必须使用 `stream: true`。

### 3.2 下游响应

业务流式接口统一返回：

```http
Content-Type: text/event-stream; charset=utf-8
Cache-Control: no-cache
Connection: keep-alive
```

每个事件保持 OpenAI Chat Completions chunk 结构：

```text
data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"model-name","choices":[{"index":0,"delta":{"role":"assistant","content":"{"},"finish_reason":null}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"model-name","choices":[{"index":0,"delta":{"content":"\"topics\""},"finish_reason":null}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"model-name","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":800,"completion_tokens":1200,"total_tokens":2000}}

data: [DONE]
```

`usage` chunk 只有在上游供应商支持并返回时才保存。开启 `stream_options.include_usage=true` 后，`[DONE]` 前可能出现一个 `choices: []` 的 usage chunk，前端和后端聚合器不得将其当作内容增量；如果 SSE 中断，可能拿不到最终 usage，调用日志需要允许 token 字段为空或使用估算值。

后端不得把业务自定义事件混入同一个 SSE 流。如果需要展示任务 ID、解析结果或错误详情，使用 OpenAI chunk 兼容字段之外的独立查询接口读取调用日志。

### 3.3 前端解析

Vue 前端使用 `fetch` 读取 `ReadableStream`，按空行切分 SSE 事件：

- 遇到 `data: [DONE]` 表示流完成。
- 遇到 JSON chunk 时读取 `choices[0].delta.content` 并追加显示。
- 如果连接关闭但未收到 `[DONE]`，标记为中断。
- 完成后调用详情接口读取解析结果、token、成本和错误信息。

## 4. 核心数据模型

### 4.1 ModelProvider

| 字段 | 说明 |
| --- | --- |
| id | 供应商 ID |
| name | 供应商名称 |
| provider_type | `openai_compatible`、`local_model` |
| base_url | 接口地址 |
| api_key_encrypted | 加密后的密钥 |
| timeout_seconds | 超时时间 |
| status | `enabled`、`disabled` |

### 4.2 ModelConfig

| 字段 | 说明 |
| --- | --- |
| id | 模型配置 ID |
| provider_id | 供应商 ID |
| model_name | 实际模型名 |
| display_name | 后台展示名 |
| usage_type | `topic`、`script`、`storyboard`、`quality_check`、`article`、`card`、`download_asset`、`report` |
| context_window | 上下文长度 |
| max_output_tokens | 最大输出 token |
| temperature | 默认温度 |
| input_token_price | 输入 token 单价 |
| output_token_price | 输出 token 单价 |
| status | `enabled`、`disabled` |

### 4.3 PromptTemplate

| 字段 | 说明 |
| --- | --- |
| id | 模板 ID |
| scene | 场景 |
| name | 模板名称 |
| version | 版本号 |
| system_prompt | 系统提示词 |
| user_prompt | 用户提示词模板 |
| variables | 变量清单 |
| output_schema | JSON Schema |
| status | `draft`、`enabled`、`disabled` |

### 4.4 LLMCallLog

| 字段 | 说明 |
| --- | --- |
| id | 调用日志 ID |
| task_id | 任务 ID |
| target_type | 业务对象类型 |
| target_id | 业务对象 ID |
| scene | 场景 |
| provider_id | 供应商 ID |
| model_id | 模型 ID |
| prompt_template_id | Prompt 模板 ID |
| prompt_version | Prompt 版本 |
| request_payload | 脱敏后的请求 |
| stream_completed | 是否收到 `[DONE]` |
| first_token_ms | 首 token 耗时 |
| raw_output | 流式聚合后的完整输出 |
| parsed_output | 解析后的 JSON |
| input_tokens | 输入 token |
| output_tokens | 输出 token |
| estimated_cost | 估算成本 |
| duration_ms | 总调用耗时 |
| status | `queued`、`streaming`、`success`、`failed`、`repaired`、`interrupted` |
| error_message | 错误信息 |

### 4.5 LLMStreamChunk

| 字段 | 说明 |
| --- | --- |
| id | 分片 ID |
| call_log_id | 调用日志 ID |
| sequence | 分片序号 |
| chunk_json | OpenAI chunk 原文 |
| delta_content | 增量文本 |
| finish_reason | 结束原因 |
| received_at | 接收时间 |

## 5. 调用流程

1. 业务 Service 根据场景选择默认模型和 Prompt 模板。
2. Prompt 渲染服务注入内容方向、栏目、平台限制、历史内容、禁止话题和安全规则。
3. LLM 网关创建调用日志，状态为 `streaming`。
4. LLM 网关以 `stream: true` 调用供应商接口。
5. LLM 网关逐个读取 OpenAI chunk，实时转发给前端，同时保存 chunk 并累积 `delta.content`。
6. 收到 `data: [DONE]` 后标记 `stream_completed=true`。
7. 输出解析器对累积文本提取 JSON 并执行 JSON Schema 校验。
8. 校验失败时通过 SSE 发起一次自动修复调用。
9. 修复仍失败则任务失败，保留原始 chunk、聚合文本和错误信息。
10. 校验成功后写入对应业务表，并关联 Prompt 版本和调用日志。

## 6. 生成场景

| 场景 | 输入 | 输出 |
| --- | --- | --- |
| 选题生成 | 内容方向、栏目、历史选题、关键词种子 | 选题数组 |
| 脚本生成 | 选题、栏目、平台限制、时长 | 脚本结构化 JSON |
| 分镜生成 | 脚本、视频模板、时长 | 分镜数组 |
| 质量检查 | 选题、脚本、分镜 | 风险标记和修改建议 |
| 图文页生成 | 脚本、分镜、视频信息 | 图文页结构 |
| 知识卡片生成 | 脚本、核心知识点 | 卡片内容数组 |
| 资料包生成 | 主题、脚本、目标用户 | 下载资料结构 |
| 日报建议 | 当日指标、失败任务、待审核内容 | 明日建议和风险提示 |

## 7. 失败处理

- 网络失败：按指数退避重试。
- 供应商限流：切换备用模型或延迟重试。
- SSE 中断：未收到 `[DONE]` 时标记 `interrupted`，不解析为正式结果。
- 客户端断开：继续完成后台任务或按任务配置取消，并在调用日志中记录断开时间。
- JSON 解析失败：执行自动修复 Prompt。
- Schema 校验失败：记录字段错误，自动修复一次。
- 内容安全失败：生成内容进入待修改状态，不能自动通过审核。
- 超预算：停止自动任务，仅允许管理员手动触发。

## 8. 安全要求

- API Key 加密保存，前端只显示脱敏值。
- 调用日志中敏感字段必须脱敏。
- 不把用户线索、手机号、邮箱等隐私数据拼进无关 Prompt。
- 对外公开内容必须经过人工审核。
- 生产环境禁用无权限 Prompt 调试。

## 9. MVP 建议

MVP 至少实现：

- 一个 OpenAI 兼容供应商。
- 所有 LLM 调用均采用 OpenAI 标准 SSE 流式输出。
- 每个生成场景一个默认 Prompt 模板。
- JSON Schema 校验和一次自动修复。
- LLM 调用日志、chunk 保存和基础 token 统计。
- 后台模型配置、Prompt 模板查看、调用日志查看。
- 选题、脚本、分镜、图文页四个场景接入 LLM 网关。
