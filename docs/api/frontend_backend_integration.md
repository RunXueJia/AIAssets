# 前后端联调接口文档
python -m uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
## 1. 联调基础约定

### 1.1 本地服务地址

| 服务 | 默认地址 | 说明 |
|---|---:|---|
| 后端 API | `http://localhost:3002` | FastAPI 服务 |
| Web 用户端 | `http://localhost:3003` | Vue 用户端 |
| 管理后台 | `http://localhost:3004` | Vue 管理后台 |

前端通过环境变量配置 API 地址：

```env
VITE_API_BASE_URL=http://localhost:3002
```

### 1.2 请求格式

- 普通接口：`Content-Type: application/json`
- 认证方式：`Authorization: Bearer <access_token>`
- SSE 接口：使用 `POST` 创建流式响应，请求头同普通接口，响应为 `text/event-stream`
- 时间格式：统一使用 ISO 8601 字符串，例如 `2026-05-21T10:30:00+08:00`

### 1.3 统一响应结构

```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

错误响应：

```json
{
  "code": 400,
  "message": "起点不能为空",
  "data": null
}
```

分页响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 120,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```

### 1.4 通用错误码

| code | 说明 |
|---:|---|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | 未登录或 Token 失效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 409 | 状态冲突，例如记录已完成不能取消 |
| 429 | 请求过于频繁 |
| 500 | 服务内部错误 |
| 502 | 外部服务调用失败 |

### 1.5 业务枚举

生成状态 `status`：

| 值 | 说明 |
|---|---|
| `pending` | 等待生成 |
| `streaming` | 生成中 |
| `completed` | 已完成 |
| `failed` | 失败 |
| `canceled` | 已取消 |

交通方式 `transport_mode`：

| 值 | 说明 |
|---|---|
| `driving` | 自驾 |
| `transit` | 公共交通 |
| `walking` | 步行 |
| `cycling` | 骑行 |
| `motorcycle` | 摩托车 |
| `mixed` | 混合出行 |

流式阶段 `stage`：

| 值 | 说明 |
|---|---|
| `understanding` | 需求理解 |
| `weather` | 天气预警 |
| `route` | 路线规划 |
| `transport` | 公共交通/路径规划 |
| `map_export` | 高德路线链接和路径图 |
| `attractions` | 途径景点 |
| `realtime` | 实时信息检索 |
| `summary` | 汇总 |

## 2. 认证接口

### 2.1 用户注册

`POST /api/v1/auth/register`

请求：

```json
{
  "username": "route_user",
  "password": "password123",
  "nickname": "路书用户",
  "email": "user@example.com"
}
```

响应：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "user": {
      "id": 1,
      "username": "route_user",
      "nickname": "路书用户",
      "role": "user",
      "status": "active"
    },
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 7200
  }
}
```

### 2.2 登录

`POST /api/v1/auth/login`

用户端和管理后台共用该接口。管理后台登录成功后前端需要校验 `user.role === "admin"`。

本地初始化默认管理员账号：`admin` / `admin123456`。生产环境首次部署后必须修改默认密码。

请求：

```json
{
  "account": "admin",
  "password": "admin123456",
  "client_type": "admin"
}
```

响应：

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "user": {
      "id": 1,
      "username": "admin",
      "nickname": "管理员",
      "role": "admin",
      "status": "active"
    },
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 7200
  }
}
```

### 2.3 游客会话

`POST /api/v1/auth/guest_session`

请求：

```json
{
  "client_id": "browser-generated-client-id"
}
```

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "user": {
      "id": 12,
      "nickname": "游客",
      "role": "guest",
      "status": "active"
    },
    "access_token": "jwt_access_token",
    "refresh_token": "jwt_refresh_token",
    "expires_in": 7200
  }
}
```

### 2.4 刷新 Token

`POST /api/v1/auth/refresh_token`

请求：

```json
{
  "refresh_token": "jwt_refresh_token"
}
```

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "access_token": "new_jwt_access_token",
    "refresh_token": "new_jwt_refresh_token",
    "expires_in": 7200
  }
}
```

### 2.5 获取当前用户信息

`GET /api/v1/auth/me`

认证：需要 `Authorization: Bearer <access_token>`。

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": 1,
    "username": "admin",
    "nickname": "管理员",
    "role": "admin",
    "status": "active"
  }
}
```

管理后台登录成功、页面刷新和刷新 Token 成功后，都应调用该接口同步最新管理员信息。

### 2.6 退出登录

`POST /api/v1/auth/logout`

响应：

```json
{
  "code": 200,
  "message": "已退出",
  "data": null
}
```

## 3. 用户端规划接口

### 3.1 流式生成规划

`POST /api/v1/planning/generate_stream`

认证：需要登录或游客会话。

请求：

```json
{
  "origin": "杭州东站",
  "destination": "西湖景区",
  "range": "一天，步行少一点",
  "transport_mode": "mixed",
  "travel_date": "2026-06-01",
  "people_count": 2,
  "preferences": ["自然风光", "低强度", "美食"],
  "avoidances": ["少换乘", "避开热门景点"]
}
```

SSE 响应事件：

```text
event: record_created
data: {"record_id":101,"record_no":"PL202605210001","status":"pending"}

event: stage
data: {"record_id":101,"stage":"weather","stage_name":"天气预警","status":"streaming"}

event: token
data: {"record_id":101,"stage":"weather","content":"预计当天杭州多云，午后可能有阵雨。"}

event: snapshot
data: {"record_id":101,"type":"weather","data":{"alert_level":"none","source_updated_at":"2026-05-21T10:00:00+08:00"}}

event: done
data: {"record_id":101,"status":"completed","duration_ms":18500}
```

SSE 错误事件：

```text
event: error
data: {"record_id":101,"stage":"route","error_code":"AMAP_FAILED","message":"地图服务暂时不可用"}
```

前端处理要求：

- 收到 `record_created` 后保存 `record_id`，用于取消、详情和重新生成。
- `token` 事件追加到流式输出区域。
- `snapshot` 事件用于更新天气、地图、实时信息等结构化模块。
- `done` 后调用详情接口或直接使用最终事件数据刷新页面。
- 连接中断时，前端可调用详情接口恢复已保存内容，也可使用 `GET /api/v1/planning/records/{record_id}/stream` 续接已保存 SSE 事件。

### 3.2 取消生成

`POST /api/v1/planning/cancel/{record_id}`

响应：

```json
{
  "code": 200,
  "message": "已取消",
  "data": {
    "record_id": 101,
    "status": "canceled"
  }
}
```

### 3.3 我的生成记录

`GET /api/v1/planning/records?page=1&page_size=20&status=completed&keyword=西湖`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 101,
        "record_no": "PL202605210001",
        "origin_text": "杭州东站",
        "destination_text": "西湖景区",
        "range_text": "一天，步行少一点",
        "transport_mode": "mixed",
        "status": "completed",
        "summary_title": "杭州东站到西湖一日轻松路线",
        "summary_text": "建议上午抵达西湖东线，下午安排湖滨和美食。",
        "created_at": "2026-05-21T10:00:00+08:00",
        "completed_at": "2026-05-21T10:00:18+08:00"
      }
    ]
  }
}
```

### 3.4 生成记录详情

`GET /api/v1/planning/records/{record_id}`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "record": {
      "id": 101,
      "record_no": "PL202605210001",
      "status": "completed",
      "current_stage": "summary",
      "origin_text": "杭州东站",
      "destination_text": "西湖景区",
      "transport_mode": "mixed",
      "duration_ms": 18500,
      "created_at": "2026-05-21T10:00:00+08:00"
    },
    "input": {
      "origin_text": "杭州东站",
      "destination_text": "西湖景区",
      "range_text": "一天，步行少一点",
      "travel_date": "2026-06-01",
      "people_count": 2,
      "preferences": ["自然风光", "低强度", "美食"],
      "avoidances": ["少换乘", "避开热门景点"]
    },
    "output": {
      "final_markdown": "## 行程建议\n...",
      "result_json": {},
      "weather_summary": "多云，午后可能有阵雨。",
      "route_summary": "地铁加步行更稳妥。",
      "attractions_summary": "推荐湖滨、断桥、平湖秋月。",
      "realtime_info_summary": "近期无重大交通管制，攻略参考建议避开周末午后高峰。",
      "risk_summary": "雨天注意防滑。",
      "amap_route_url": "https://uri.amap.com/navigation?..."
    },
    "snapshots": {
      "routes": [],
      "map_exports": [],
      "weather": [],
      "realtime_info": {
        "news_traffic": [],
        "guide_pitfall": []
      }
    },
    "errors": []
  }
}
```

### 3.5 重新生成

`POST /api/v1/planning/records/{record_id}/regenerate`

请求：

```json
{
  "override_input": {
    "range": "一天，尽量少走路",
    "preferences": ["自然风光", "咖啡"]
  }
}
```

响应：

```json
{
  "code": 200,
  "message": "已创建重新生成任务",
  "data": {
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
}
```

说明：

- `regenerate` 只创建新记录，不直接启动生成。
- 前端如需立即生成，可继续用 `request_payload` 调用 `POST /api/v1/planning/generate_stream`。
- 若后端内部已启动或用户端失败重试接口创建了新任务，则可用 `stream_url` 续接该记录事件流。

### 3.6 续接生成过程

`GET /api/v1/planning/records/{record_id}/stream?after_sequence=0`

认证：需要登录或游客会话，且只能访问自己的记录。

响应为 `text/event-stream`，事件格式与 `POST /api/v1/planning/generate_stream` 相同：

```text
event: record_created
data: {"record_id":101,"record_no":"PL202605210001","status":"pending"}

event: stage
data: {"record_id":101,"stage":"route","stage_name":"路线规划","status":"streaming"}

event: token
data: {"record_id":101,"stage":"route","content":"建议先..."}

event: snapshot
data: {"record_id":101,"type":"route","data":{"route_summary":"约12.8公里，预计40分钟"}}

event: done
data: {"record_id":101,"status":"completed","duration_ms":18500}
```

续接规则：

- `after_sequence` 表示只返回序号大于该值的已保存事件，默认 `0`。
- 前端应按接收到事件的顺序更新页面，并在本地记录最新事件序号。
- 对 `streaming` 记录，接口会短轮询等待新事件，直到收到 `done` / `error` 或空闲超时。
- 对 `completed` / `failed` / `canceled` 记录，接口会快速返回历史事件并在终态事件后结束。
- 若前端只需要最终结构化数据，仍可调用详情接口 `GET /api/v1/planning/records/{record_id}`。

### 3.7 失败记录重试并流式返回

`POST /api/v1/planning/records/{record_id}/retry`

认证：需要登录或游客会话，且只能重试自己的失败记录。

请求体：无。

响应为 `text/event-stream`。接口会复制失败记录的原始输入，创建一条新的生成记录，并直接开始流式生成。事件格式与 `POST /api/v1/planning/generate_stream` 相同，但不会返回旧记录事件。

示例：

```text
event: stage
data: {"record_id":102,"stage":"understanding","stage_name":"需求理解","status":"streaming"}

event: token
data: {"record_id":102,"stage":"understanding","content":"本次重试将沿用原始输入..."}

event: done
data: {"record_id":102,"status":"completed","duration_ms":19000}
```

错误：

```json
{
  "code": 409,
  "message": "只有失败记录可以重试",
  "data": null
}
```

前端处理要求：

- 失败详情页点击重试时调用该接口，并按 SSE 事件刷新过程区域。
- 第一个事件中的 `record_id` 是新创建的记录 ID，前端应切换到新记录或保存新 ID。
- 如果连接中断，可使用 `GET /api/v1/planning/records/{new_record_id}/stream` 续接。

### 3.8 路径图信息

`GET /api/v1/planning/records/{record_id}/route_map`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "record_id": 101,
    "amap_route_url": "https://uri.amap.com/navigation?...",
    "image_url": "http://localhost:3002/static/route-maps/101.png",
    "export_type": "screenshot",
    "status": "completed",
    "width": 1200,
    "height": 800
  }
}
```

## 4. 管理端接口

管理端接口均要求 `Authorization`，且用户角色为 `admin`。

### 4.1 用户列表

`GET /api/v1/admin/users?page=1&page_size=20&keyword=route&status=active&role=user`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 12,
        "username": "route_user",
        "nickname": "路书用户",
        "email": "user@example.com",
        "role": "user",
        "status": "active",
        "last_login_at": "2026-05-21T09:30:00+08:00",
        "created_at": "2026-05-21T09:00:00+08:00"
      }
    ]
  }
}
```

### 4.2 用户详情

`GET /api/v1/admin/users/{user_id}`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": 12,
    "username": "route_user",
    "nickname": "路书用户",
    "email": "user@example.com",
    "role": "user",
    "status": "active",
    "generation_count": 18,
    "last_login_at": "2026-05-21T09:30:00+08:00",
    "created_at": "2026-05-21T09:00:00+08:00"
  }
}
```

### 4.3 禁用/启用用户

`POST /api/v1/admin/users/{user_id}/disable`

`POST /api/v1/admin/users/{user_id}/enable`

响应：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 12,
    "status": "disabled"
  }
}
```

### 4.4 生成记录列表

`GET /api/v1/admin/generation_records?page=1&page_size=20&status=failed&transport_mode=mixed&user_keyword=route`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 101,
        "record_no": "PL202605210001",
        "user_id": 12,
        "user_nickname": "路书用户",
        "origin_text": "杭州东站",
        "destination_text": "西湖景区",
        "transport_mode": "mixed",
        "status": "failed",
        "duration_ms": 8500,
        "error_message": "地图服务暂时不可用",
        "created_at": "2026-05-21T10:00:00+08:00"
      }
    ]
  }
}
```

### 4.5 生成记录详情

`GET /api/v1/admin/generation_records/{record_id}`

响应结构同用户端详情接口，额外返回调用日志：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "record": {},
    "input": {},
    "output": {},
    "snapshots": {},
    "errors": [],
    "llm_call_logs": [
      {
        "id": 1,
        "provider": "openai-compatible",
        "model_name": "gpt-4.1-mini",
        "call_type": "stream",
        "status": "success",
        "prompt_tokens": 1800,
        "completion_tokens": 2600,
        "total_tokens": 4400,
        "duration_ms": 18500,
        "created_at": "2026-05-21T10:00:00+08:00"
      }
    ]
  }
}
```

### 4.6 重试失败记录

`POST /api/v1/admin/generation_records/{record_id}/retry`

响应：

```json
{
  "code": 200,
  "message": "已创建重试任务",
  "data": {
    "record_id": 103,
    "parent_record_id": 101,
    "status": "pending"
  }
}
```

### 4.7 删除生成记录

`DELETE /api/v1/admin/generation_records/{record_id}`

响应：

```json
{
  "code": 200,
  "message": "已删除",
  "data": null
}
```

### 4.8 LLM 配置列表

`GET /api/v1/admin/llm_configs?page=1&page_size=20&status=enabled`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 1,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "name": "默认模型",
        "provider": "openai-compatible",
        "api_format": "openai_chat_completions",
        "base_url": "https://api.example.com/v1",
        "model_name": "gpt-4.1-mini",
        "api_key_masked": "sk-****abcd",
        "status": "enabled",
        "is_default": true,
        "last_test_status": "success",
        "last_test_at": "2026-05-21T09:00:00+08:00"
      }
    ]
  }
}
```

### 4.9 创建 LLM 配置

`POST /api/v1/admin/llm_configs`

请求：

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

响应：

```json
{
  "code": 200,
  "message": "创建成功",
  "data": {
    "id": 1,
    "api_key_masked": "sk-****xxxx",
    "status": "disabled"
  }
}
```

### 4.10 LLM 配置详情

`GET /api/v1/admin/llm_configs/{config_id}`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "id": 1,
    "name": "默认模型",
    "provider": "openai-compatible",
    "api_format": "openai_chat_completions",
    "base_url": "https://api.example.com/v1",
    "model_name": "gpt-4.1-mini",
    "api_key_masked": "sk-****xxxx",
    "status": "disabled",
    "is_default": true,
    "timeout_s": 60,
    "max_tokens": 8000,
    "temperature": 0.7,
    "last_test_status": null,
    "last_test_message": null
  }
}
```

### 4.11 更新 LLM 配置

`PUT /api/v1/admin/llm_configs/{config_id}`

请求：

```json
{
  "name": "默认模型",
  "api_format": "openai_responses",
  "base_url": "https://api.example.com/v1",
  "model_name": "gpt-4.1-mini",
  "api_key": "sk-new-key-or-empty",
  "timeout_s": 60,
  "max_tokens": 8000,
  "temperature": 0.7,
  "is_default": true
}
```

响应：

```json
{
  "code": 200,
  "message": "更新成功",
  "data": {
    "id": 1,
    "api_key_masked": "sk-****xxxx"
  }
}
```

### 4.12 测试 LLM 连接

`POST /api/v1/admin/llm_configs/{config_id}/test`

请求：

```json
{
  "test_prompt": "请回复 OK"
}
```

响应：

```json
{
  "code": 200,
  "message": "连接测试成功",
  "data": {
    "status": "success",
    "message": "OK",
    "duration_ms": 1200,
    "tested_at": "2026-05-21T10:00:00+08:00"
  }
}
```

### 4.12.1 流式调试 LLM 连接

`POST /api/v1/admin/llm_configs/{config_id}/test_stream`

请求：

```json
{
  "test_prompt": "请用一句话介绍你自己"
}
```

响应为 `text/event-stream`。事件：

```text
event: start
data: {"type":"start","status":"streaming","config_id":1,"api_format":"openai_chat_completions","model_name":"gpt-4.1-mini"}

event: token
data: {"type":"token","content":"OK"}

event: done
data: {"type":"done","status":"success","message":"OK","duration_ms":1200,"tested_at":"2026-05-22T10:00:00+08:00"}
```

失败时返回：

```text
event: error
data: {"type":"error","status":"failed","message":"LLM 调用失败","duration_ms":300,"tested_at":"2026-05-22T10:00:00+08:00"}
```

`api_format` 可选值：

```json
[
  "openai_chat_completions",
  "openai_responses",
  "anthropic_messages",
  "gemini_generate_content"
]
```

### 4.13 启用/停用 LLM 配置

`POST /api/v1/admin/llm_configs/{config_id}/enable`

`POST /api/v1/admin/llm_configs/{config_id}/disable`

响应：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {
    "id": 1,
    "status": "enabled"
  }
}
```

## 5. 内部辅助接口

内部辅助接口主要供后端调试、管理端排障或前端地图能力联调使用。第一期可以只给管理员开放。

### 5.1 地点搜索

`GET /api/v1/amap/search_places?keyword=西湖&city=杭州`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "items": [
      {
        "name": "西湖风景名胜区",
        "address": "浙江省杭州市西湖区",
        "location": "120.143222,30.236064",
        "type": "风景名胜"
      }
    ],
    "source_updated_at": "2026-05-21T10:00:00+08:00"
  }
}
```

### 5.2 路线计算

`POST /api/v1/amap/calculate_route`

请求：

```json
{
  "origin": "120.21201,30.29191",
  "destination": "120.143222,30.236064",
  "transport_mode": "driving",
  "waypoints": []
}
```

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "distance_m": 12800,
    "duration_s": 2400,
    "route_summary": "约12.8公里，预计40分钟",
    "raw": {}
  }
}
```

### 5.3 创建高德路线链接

`POST /api/v1/amap/create_route_link`

请求：

```json
{
  "origin_name": "杭州东站",
  "origin": "120.21201,30.29191",
  "destination_name": "西湖风景名胜区",
  "destination": "120.143222,30.236064",
  "transport_mode": "driving",
  "waypoints": ["120.160000,30.250000"]
}
```

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "amap_route_url": "https://uri.amap.com/navigation?..."
  }
}
```

### 5.4 导出路径图

`POST /api/v1/amap/export_route_map`

请求：

```json
{
  "record_id": 101,
  "route_snapshot_id": 1,
  "export_type": "screenshot"
}
```

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "export_id": 1,
    "status": "completed",
    "image_url": "http://localhost:3002/static/route-maps/101.png"
  }
}
```

### 5.5 天气查询

`GET /api/v1/weather/query?city=杭州&date=2026-06-01`

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "city_name": "杭州",
    "weather_date": "2026-06-01",
    "weather_summary": "多云，午后可能有阵雨",
    "alert_level": "none",
    "alerts": [],
    "source_updated_at": "2026-05-21T10:00:00+08:00"
  }
}
```

### 5.6 实时信息检索

`GET /api/v1/realtime/search?keyword=杭州 西湖 交通管制&category=traffic`

分类 `category`：

| 值 | 说明 |
|---|---|
| `news` | 新闻资讯 |
| `traffic` | 交通管制 |
| `guide` | 攻略参考 |
| `pitfall` | 避坑参考 |

响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "category": "traffic",
    "items": [
      {
        "title": "西湖景区周末交通提醒",
        "url": "https://example.com/news/1",
        "source": "示例新闻源",
        "published_at": "2026-05-20T08:00:00+08:00",
        "summary": "周末景区周边可能限流。",
        "tags": ["交通管制", "周末"],
        "credibility_score": 82.5
      }
    ],
    "source_updated_at": "2026-05-21T10:00:00+08:00"
  }
}
```

攻略/避坑参考请求示例：

`GET /api/v1/realtime/search?keyword=杭州 西湖 避坑&category=pitfall`

## 6. 前端联调注意事项

- 用户端启动时如果没有 Token，先调用游客会话接口。
- 管理后台不允许游客访问，登录后必须校验 `role = "admin"`。
- 所有列表接口都要支持 `page`、`page_size`，前端默认 `page_size = 20`。
- 用户端生成中不要跳转页面；取消、失败、重试都围绕 `record_id` 操作。
- SSE 断开后，前端用 `GET /api/v1/planning/records/{record_id}` 恢复已保存内容。
- API Key 表单提交后，前端只展示后端返回的 `api_key_masked`。
- 后端日志、接口响应、SSE 事件都不能返回完整 Token、密码或 API Key。
