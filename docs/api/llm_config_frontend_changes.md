# 前端配合修改清单

本文记录后端接口变更后，前端需要配合调整的内容。完整接口定义以 `docs/api/frontend_backend_integration.md` 为准。

## 1. 管理后台 LLM 配置

### 1.1 新增 `api_format` 字段

LLM 配置列表、详情、创建、更新接口均增加 `api_format` 字段。前端表单需要把它作为必填项提交。

可选值：

| 值 | 前端展示 |
|---|---|
| `openai_chat_completions` | OpenAI Chat Completions |
| `openai_responses` | OpenAI Responses API |
| `anthropic_messages` | Anthropic Messages |
| `gemini_generate_content` | Gemini Native generateContent |

默认值建议使用 `openai_chat_completions`。旧数据如果没有返回 `api_format`，前端也按 `openai_chat_completions` 展示。

创建请求示例：

```json
{
  "name": "默认模型",
  "provider": "openai-compatible",
  "api_format": "openai_chat_completions",
  "base_url": "https://api.example.com/v1",
  "model_name": "gpt-4.1-mini",
  "api_key": "sk-xxxx",
  "timeout_s": 60,
  "max_tokens": 8000,
  "temperature": 0.7,
  "is_default": true
}
```

更新请求可以只提交改动字段。编辑时 `api_key` 留空表示不修改密钥，不要提交空字符串覆盖已有密钥。

### 1.2 流式测试接口

新增 LLM 配置流式测试接口：

```http
POST /api/v1/admin/llm_configs/{config_id}/test_stream
```

请求：

```json
{
  "test_prompt": "请用一句话介绍你自己"
}
```

响应类型：`text/event-stream`

事件：

```text
event: start
data: {"type":"start","status":"streaming","config_id":1,"api_format":"openai_chat_completions","model_name":"gpt-4.1-mini"}

event: token
data: {"type":"token","content":"OK"}

event: done
data: {"type":"done","status":"success","message":"OK","duration_ms":1200,"tested_at":"2026-05-22T10:00:00"}

event: error
data: {"type":"error","status":"failed","message":"LLM 调用失败","duration_ms":300,"tested_at":"2026-05-22T10:00:00"}
```

前端处理要求：

1. 管理后台测试按钮优先调用 `test_stream`，把 `token` 事件实时追加到调试消息区。
2. 收到 `done` 后展示成功状态和耗时，并刷新列表中的 `last_test_status` / `last_test_at`。
3. 收到 `error` 后展示失败原因，并刷新列表中的测试状态。
4. 测试弹窗关闭或点击停止时，需要通过 `AbortController` 断开 fetch。
5. 保留原 `POST /api/v1/admin/llm_configs/{config_id}/test` 作为非流式兜底也可以。

## 2. 出行方式新增摩托车

用户端规划表单、历史记录、详情页、管理端记录列表和详情页都需要识别 `motorcycle`。

交通方式完整枚举：

| 值 | 展示文案 |
|---|---|
| `driving` | 自驾 |
| `transit` | 公共交通 |
| `walking` | 步行 |
| `cycling` | 骑行 |
| `motorcycle` | 摩托车 |
| `mixed` | 混合出行 |

前端改造点：

1. 用户端创建规划时，交通方式选择器增加“摩托车”，提交字段为 `"transport_mode": "motorcycle"`。
2. 历史列表、历史详情、生成结果页、管理端记录列表和详情页都要能把 `motorcycle` 显示为“摩托车”。
3. 管理端记录筛选下拉框需要增加 `motorcycle`，查询参数仍为 `transport_mode=motorcycle`。
4. 重新生成、失败重试、详情恢复时不要把 `motorcycle` 转成其他值，直接沿用后端返回字段。

## 3. 高德路线链接展示

后端已调整高德导航 URI 的生成方式，`amap_route_url` 会尽量带入起点、终点和途径点。前端不需要自行拼接高德链接，应直接使用接口返回值。

链接来源：

- 生成过程 `snapshot.type === "map_export"` 中的 `data.amap_route_url`。
- 记录详情 `output.amap_route_url`。
- 路径图接口 `GET /api/v1/planning/records/{record_id}/route_map` 返回的 `amap_route_url`。
- 内部辅助接口 `POST /api/v1/amap/create_route_link` 返回的 `amap_route_url`。

展示要求：

1. “打开高德路线”按钮优先使用 `output.amap_route_url`，没有时再使用 `route_map.amap_route_url` 或最新 `map_export` 快照。
2. 只把链接作为外链打开，使用 `target="_blank"`；不要在前端解析或重组 query。
3. `motorcycle` 的高德 URI 模式后端会映射为骑行导航模式，前端仍展示为“摩托车”。
4. 途径点目前只保证驾车类链接带入高德 `via`；步行、公交、骑行、摩托车以高德 URI 支持能力为准。
5. 如果只需要图片预览，继续展示 `image_url`；如果用户要导航，使用 `amap_route_url`。

## 4. 历史详情页续接生成过程

### 目标

用户从历史记录点开一条 `streaming` 状态的记录时，详情页需要继续显示已生成内容，并续接后续 SSE 事件。

### 新增接口

```http
GET /api/v1/planning/records/{record_id}/stream?after_sequence=0
```

响应类型：`text/event-stream`

事件格式与现有 `POST /api/v1/planning/generate_stream` 一致：

```text
event: token
data: {"record_id":101,"stage":"route","content":"建议先..."}
```

### 前端改造点

1. 在用户端历史详情页判断记录状态：
   - `streaming`：调用续接接口。
   - `completed` / `failed` / `canceled`：继续用详情接口展示最终状态。

2. 前端需要保存当前已消费的事件序号：
   - 首次进入详情页可传 `after_sequence=0`。
   - 当前后端事件体不返回 `sequence_no`，前端可按已处理事件数维护本地序号。
   - 网络中断后用最新本地序号重新连接。

3. 续接接口返回的是历史事件 + 新事件：
   - 前端应复用现有 SSE 事件处理逻辑。
   - `token` 追加到过程文本。
   - `stage` 更新当前阶段。
   - `snapshot` 刷新天气、路线、地图、景点、实时信息模块。
   - `done` / `error` 后关闭流并刷新详情接口。

4. 当前前端 `createStreamClient` 只支持 `POST` 请求体，需要扩展：
   - 支持 `GET` SSE。
   - 支持无请求体连接。
   - 支持维护本地事件序号；如果后端后续返回 `sequence_no`，再优先使用服务端序号。

建议新增方法：

```js
resumeRecordStream(recordId, afterSequence = 0) {
  return fetch(`${baseUrl}/api/v1/planning/records/${recordId}/stream?after_sequence=${afterSequence}`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${token}` },
  })
}
```

注意：当前后端 SSE `data` 中不额外包一层 `sequence_no`，续接接口按服务端保存顺序输出事件。前端如需精确断点续接，建议优先以本地已处理事件数作为 `after_sequence`；如果后续后端在事件 `data` 中补充 `sequence_no`，再切换为使用服务端序号。

## 5. 失败记录重试

### 目标

用户打开失败记录详情时，可以直接点击“重试”，前端展示新的生成过程。

### 新增接口

```http
POST /api/v1/planning/records/{record_id}/retry
```

响应类型：`text/event-stream`

说明：

- 只能重试当前用户自己的 `failed` 记录。
- 后端会复制原失败记录的输入，创建一条新记录。
- SSE 事件里的 `record_id` 是新记录 ID。

### 前端改造点

1. 历史详情页在 `record.status === 'failed'` 时显示“重试”按钮。

2. 点击重试后调用：

```js
retryRecord(recordId) {
  return fetch(`${baseUrl}/api/v1/planning/records/${recordId}/retry`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
  })
}
```

3. 收到第一个 SSE 事件后：
   - 保存新 `record_id`。
   - 建议路由切换到新记录详情，或在当前页标记“重试生成中”。
   - 后续断线用 `GET /api/v1/planning/records/{new_record_id}/stream` 续接。

4. 错误处理：

```json
{
  "code": 409,
  "message": "只有失败记录可以重试",
  "data": null
}
```

前端应提示该错误，并刷新详情确认记录状态。

## 6. 重新生成接口返回值调整

`POST /api/v1/planning/records/{record_id}/regenerate` 现在会返回更多字段：

```json
{
  "record_id": 102,
  "parent_record_id": 101,
  "status": "pending",
  "stream_url": "/api/v1/planning/records/102/stream",
  "request_payload": {
    "origin": "杭州东站",
    "destination": "西湖景区",
    "range": "一天，尽量少走路",
    "transport_mode": "mixed",
    "travel_date": "2026-06-01",
    "people_count": 2,
    "preferences": ["自然风光", "咖啡"],
    "avoidances": ["少换乘"]
  }
}
```

前端处理建议：

- 如果只是创建重新生成任务，跳转到新记录详情即可。
- 如果要立即开始生成，可继续用 `request_payload` 调用现有 `POST /api/v1/planning/generate_stream`。
- 如果该新记录已经由其他入口启动，可使用 `stream_url` 续接事件。

## 7. SSE 客户端建议

建议把现有流式客户端抽成通用能力：

```js
createStreamClient({
  method: 'POST' | 'GET',
  url,
  body,
  headers,
  onRecordCreated,
  onStage,
  onToken,
  onSnapshot,
  onDone,
  onError,
})
```

需要兼容：

- `POST /api/v1/planning/generate_stream`
- `GET /api/v1/planning/records/{record_id}/stream`
- `POST /api/v1/planning/records/{record_id}/retry`
- `POST /api/v1/admin/llm_configs/{config_id}/test_stream`

## 8. 页面状态建议

历史详情页建议增加这些状态：

- `streaming`: 展示过程区，并自动续接 SSE。
- `failed`: 展示错误信息和“重试”按钮。
- `completed`: 展示最终 Markdown、结构化模块和地图链接。
- `canceled`: 展示已取消状态，不自动续接。

过程区应避免重复追加历史内容。进入详情页时，如果已经用详情接口恢复了输出，再接入 SSE 时需要按本地事件序号或已渲染内容去重。
