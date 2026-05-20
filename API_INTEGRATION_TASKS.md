# 24小时AI增长资产引擎前端接口对接文档

版本：v1.1  
日期：2026-05-20  
适用范围：Vue 后台、FastAPI 后端、SSE、文件下载、联调验收  
接口前缀：`/api/v1`

## 1. 对接边界

- 前端只调用后端 HTTP API、SSE 和文件下载接口。
- 后端只提供接口、鉴权、任务状态、业务数据和文件流，不渲染 Vue 页面。
- 前端页面必须使用中文业务文案，不直接展示 `prompt`、`model`、`temperature`、`task_id` 等技术字段。
- 接口字段可以使用技术名，前端在 API 层或页面层转换为业务语义。
- 所有登录后接口默认需要 `Authorization: Bearer <token>`。
- Swagger/Postman 可独立调试，不依赖前端项目。

## 2. 通用协议

### 2.1 请求

| 类型 | 约定 |
| --- | --- |
| Base URL | 开发环境由前端代理 `/api` 到后端，例如 `http://127.0.0.1:8000` |
| Content-Type | JSON 请求统一 `application/json` |
| 鉴权 | `Authorization: Bearer <access_token>` |
| 时间格式 | `YYYY-MM-DD HH:mm:ss`，后端统一按服务器时区返回 |
| 分页参数 | `page` 从 1 开始，`page_size` 默认 20 |
| 文件下载 | 使用 GET 下载接口，返回文件流 |
| SSE | `Content-Type: text/event-stream` |

### 2.2 普通响应

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

### 2.3 分页响应

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [],
    "total": 0,
    "page": 1,
    "page_size": 20
  }
}
```

### 2.4 错误响应

```json
{
  "code": 40001,
  "message": "参数不完整，请检查后重试",
  "data": {
    "field": "direction"
  }
}
```

前端处理要求：

- `code === 0` 表示成功。
- `401` 或业务码 `40100` 跳转登录页。
- `403` 或业务码 `40300` 展示“当前账号无权限操作”。
- 不展示堆栈、SQL、模型原始错误、密钥、内部文件路径。
- 失败文案要给运营可执行建议，例如“请缩短主题描述后重试”。

### 2.5 建议错误码

| code | 含义 |
| --- | --- |
| 0 | 成功 |
| 40001 | 参数错误 |
| 40100 | 未登录或 Token 过期 |
| 40300 | 无权限 |
| 40400 | 数据不存在 |
| 40900 | 当前状态不允许操作 |
| 42900 | 请求过于频繁 |
| 50000 | 服务异常 |
| 50200 | 外部服务异常，例如 LLM、抓取、视频合成 |

## 3. 枚举字典

前端展示中文，接口传输建议使用稳定英文值。

### 3.1 角色

| value | 展示名 |
| --- | --- |
| `admin` | 管理员 |
| `operation_manager` | 运营负责人 |
| `content_editor` | 内容编辑 |
| `video_operator` | 视频运营 |
| `viewer` | 只读查看者 |

### 3.2 生成任务状态

| value | 展示名 |
| --- | --- |
| `pending` | 等待中 |
| `running` | 运行中 |
| `success` | 成功 |
| `failed` | 失败 |
| `cancelled` | 已取消 |
| `retrying` | 重试中 |

### 3.3 内容状态

| value | 展示名 |
| --- | --- |
| `generating` | 生成中 |
| `pending_review` | 待审核 |
| `approved` | 审核通过 |
| `approved_with_edit` | 修改后通过 |
| `rejected` | 驳回 |
| `regenerating` | 重新生成中 |
| `pending_render` | 待合成 |
| `rendering` | 合成中 |
| `render_failed` | 合成失败 |
| `rendered` | 已合成 |
| `exported` | 已导出 |
| `published` | 已发布 |
| `offline` | 已下线 |

### 3.4 生成类型

| value | 展示名 |
| --- | --- |
| `topics_only` | 只生成选题 |
| `topics_and_script` | 生成选题和脚本 |
| `full_script_storyboard` | 完整生成脚本和分镜 |

### 3.5 任务阶段

| value | 展示名 |
| --- | --- |
| `create_task` | 正在创建任务 |
| `fetch_sources` | 正在抓取相关内容 |
| `summarize_sources` | 正在整理素材汇总 |
| `generate_topics` | 正在生成选题 |
| `generate_script` | 正在生成脚本 |
| `generate_storyboard` | 正在生成分镜 |
| `generate_subtitle` | 正在生成字幕 |
| `completed` | 生成完成 |

### 3.6 选题状态

| value | 展示名 |
| --- | --- |
| `draft` | 待确认 |
| `approved` | 已通过 |
| `rejected` | 已驳回 |
| `locked` | 已锁定 |

### 3.7 监控任务状态

| value | 展示名 |
| --- | --- |
| `enabled` | 运行中 |
| `paused` | 已暂停 |
| `deleted` | 已删除 |

### 3.8 发布平台

| value | 展示名 |
| --- | --- |
| `douyin` | 抖音 |
| `xiaohongshu` | 小红书 |
| `bilibili` | B 站 |
| `wechat_channels` | 视频号 |
| `youtube_shorts` | YouTube Shorts |
| `tiktok` | TikTok |

## 4. 通用数据结构

### 4.1 用户

```json
{
  "id": "u_001",
  "username": "editor01",
  "display_name": "内容编辑01",
  "role": "content_editor",
  "permissions": ["generation:view", "review:approve"],
  "created_at": "2026-05-20 09:00:00"
}
```

### 4.2 来源素材

```json
{
  "id": "src_001",
  "task_id": "task_001",
  "title": "AI 写周报的 5 个技巧",
  "site_name": "示例网站",
  "url": "https://example.com/article",
  "published_at": "2026-05-19 12:00:00",
  "summary": "文章介绍了用 AI 整理工作记录并生成周报的方法。",
  "relevance_reason": "与 AI 写周报主题高度相关",
  "key_points": ["整理本周事项", "生成结构化周报", "人工校对事实"],
  "status": "usable",
  "need_human_confirm": false,
  "created_at": "2026-05-20 09:10:00"
}
```

### 4.3 选题

```json
{
  "id": "topic_001",
  "task_id": "task_001",
  "title": "用 AI 10 分钟写完一份周报",
  "audience": "普通职场人",
  "angle": "把零散工作记录整理成可提交周报",
  "column": "一分钟 AI 办公",
  "duration_seconds": 60,
  "keywords": ["AI 写周报", "职场效率", "办公自动化"],
  "reason": "主题具体，适合 60 秒短视频演示。",
  "status": "draft",
  "need_human_confirm": false,
  "created_at": "2026-05-20 09:20:00"
}
```

### 4.4 脚本详情

```json
{
  "id": "script_001",
  "topic_id": "topic_001",
  "title": "用 AI 10 分钟写完一份周报",
  "hook": "周五最痛苦的事，是发现周报还没写。",
  "pain_point": "很多人一周做了不少事，但写周报时想不起来重点。",
  "method": "先让 AI 整理工作记录，再生成周报结构。",
  "steps": ["粘贴本周事项", "要求 AI 按成果、问题、下周计划整理", "人工补充关键数字"],
  "example": "把会议纪要、待办记录和完成事项放到一起，让 AI 输出三段式周报。",
  "summary": "AI 负责整理，人负责判断，周报效率会高很多。",
  "cta": "下次写周报前，先把本周记录丢给 AI 整理。",
  "platform_title": "用 AI 10 分钟写完周报",
  "description": "一个适合普通职场人的 AI 周报写作方法。",
  "tags": ["AI办公", "职场效率", "周报"],
  "cover_text": "AI 写周报",
  "pinned_comment": "试试先整理工作记录，再让 AI 生成周报结构。",
  "status": "pending_review",
  "version": 1,
  "created_at": "2026-05-20 09:30:00",
  "updated_at": "2026-05-20 09:30:00"
}
```

### 4.5 分镜

```json
{
  "id": "shot_001",
  "script_id": "script_001",
  "shot_no": 1,
  "duration_seconds": 6,
  "voiceover": "周五最痛苦的事，是发现周报还没写。",
  "subtitle": "周报还没写？",
  "visual_type": "screen_recording",
  "material_suggestion": "展示空白周报文档和零散待办记录",
  "motion_suggestion": "标题从上方滑入"
}
```

### 4.6 字幕

```json
{
  "id": "sub_001",
  "script_id": "script_001",
  "start_time": "00:00:00.000",
  "end_time": "00:00:03.000",
  "text": "周五最痛苦的事，是发现周报还没写。"
}
```

## 5. 认证接口

### 5.1 登录

`POST /api/v1/auth/login`

请求：

```json
{
  "username": "admin",
  "password": "123456"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "access_token": "jwt-token",
    "token_type": "Bearer",
    "expires_in": 7200,
    "user": {
      "id": "u_001",
      "username": "admin",
      "display_name": "管理员",
      "role": "admin",
      "permissions": ["*"]
    }
  }
}
```

### 5.2 退出登录

`POST /api/v1/auth/logout`

请求：

```json
{}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

### 5.3 当前用户

`GET /api/v1/auth/me`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "u_001",
    "username": "admin",
    "display_name": "管理员",
    "role": "admin",
    "permissions": ["*"]
  }
}
```

## 6. 后台首页与看板

### 6.1 首页概览

`GET /api/v1/dashboard/get_overview`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `date` | 否 | 统计日期，默认今天，格式 `YYYY-MM-DD` |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "generation_task_count": 12,
    "fetch_task_count": 10,
    "source_item_count": 86,
    "topic_count": 30,
    "script_count": 8,
    "video_count": 3,
    "pending_review_count": 6,
    "render_failed_count": 1,
    "package_count": 2
  }
}
```

### 6.2 趋势统计

`GET /api/v1/dashboard/get_trend`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `range` | 否 | `today`、`7d`、`30d`，默认 `7d` |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "dates": ["2026-05-14", "2026-05-15"],
    "generation_task_counts": [10, 12],
    "source_item_counts": [60, 86],
    "script_counts": [5, 8],
    "video_counts": [2, 3],
    "task_success_rate": 0.92,
    "task_failed_rate": 0.08,
    "fetch_success_rate": 0.9,
    "llm_success_rate": 0.95,
    "sse_disconnect_rate": 0.03,
    "avg_generation_seconds": 180,
    "avg_render_seconds": 420,
    "package_export_count": 9
  }
}
```

## 7. 生成任务接口

### 7.1 创建生成任务

`POST /api/v1/generation/create_task`

前端页面字段映射：

| 页面字段 | 接口字段 | 说明 |
| --- | --- | --- |
| 你想做什么内容 | `direction` | 必填 |
| 这次想讲什么主题 | `topic` | 可选 |
| 主要给谁看 | `audience` | 可选 |
| 一次生成几条 | `count` | 默认 5 |
| 内容更适合哪个栏目 | `column` | 可选，`auto` 表示系统自动判断 |
| 这次要生成到哪一步 | `generation_type` | 默认 `full_script_storyboard` |
| 是否现在开始 | `start_mode` | `now` 或 `draft` |

请求：

```json
{
  "direction": "AI 工具 + 职场效率",
  "topic": "AI 写周报",
  "audience": "普通职场人",
  "count": 5,
  "column": "auto",
  "generation_type": "full_script_storyboard",
  "start_mode": "now"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_001",
    "status": "pending",
    "stream_url": "/api/v1/generation/stream/task_001"
  }
}
```

### 7.2 生成任务列表

`GET /api/v1/generation/get_task_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |
| `status` | 否 | 生成任务状态 |
| `created_by` | 否 | 创建人 ID |
| `start_date` | 否 | 创建开始日期 |
| `end_date` | 否 | 创建结束日期 |
| `keyword` | 否 | 搜索方向、主题 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "task_001",
        "direction": "AI 工具 + 职场效率",
        "topic": "AI 写周报",
        "audience": "普通职场人",
        "count": 5,
        "column": "一分钟 AI 办公",
        "generation_type": "full_script_storyboard",
        "status": "running",
        "current_stage": "generate_script",
        "progress": 60,
        "created_by_name": "运营负责人",
        "created_at": "2026-05-20 09:00:00",
        "updated_at": "2026-05-20 09:10:00",
        "error_message": ""
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 7.3 生成任务详情

`GET /api/v1/generation/get_task_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "task_001",
    "direction": "AI 工具 + 职场效率",
    "topic": "AI 写周报",
    "audience": "普通职场人",
    "count": 5,
    "column": "一分钟 AI 办公",
    "generation_type": "full_script_storyboard",
    "status": "success",
    "current_stage": "completed",
    "progress": 100,
    "source_summary_id": "sum_001",
    "source_count": 20,
    "topic_count": 10,
    "script_count": 5,
    "logs": [
      {
        "stage": "fetch_sources",
        "message": "已抓取 20 条相关素材",
        "level": "info",
        "created_at": "2026-05-20 09:05:00"
      }
    ],
    "created_at": "2026-05-20 09:00:00",
    "updated_at": "2026-05-20 09:30:00",
    "error_message": ""
  }
}
```

### 7.4 取消任务

`POST /api/v1/generation/cancel_task`

请求：

```json
{
  "task_id": "task_001"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_001",
    "status": "cancelled"
  }
}
```

### 7.5 重新生成

`POST /api/v1/generation/retry_task`

请求：

```json
{
  "task_id": "task_001",
  "retry_from_stage": "generate_script"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_001",
    "status": "retrying",
    "stream_url": "/api/v1/generation/stream/task_001"
  }
}
```

## 8. SSE 生成过程

### 8.1 订阅生成任务

`GET /api/v1/generation/stream/{id}`

请求头：

```text
Accept: text/event-stream
Authorization: Bearer <token>
```

响应头：

```text
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

### 8.2 事件类型

| event | 说明 |
| --- | --- |
| `start` | 任务开始 |
| `stage` | 阶段变化 |
| `source` | 新抓取到的来源 |
| `delta` | LLM 文本增量 |
| `result` | 阶段结构化结果 |
| `error` | 任务错误 |
| `done` | 任务完成 |
| `heartbeat` | 心跳 |

### 8.3 事件示例

```text
event: start
data: {"task_id":"task_001","status":"running","message":"生成任务已开始"}

event: stage
data: {"task_id":"task_001","stage":"fetch_sources","stage_name":"正在抓取相关内容","progress":20}

event: source
data: {"id":"src_001","title":"AI 写周报的 5 个技巧","site_name":"示例网站","url":"https://example.com/article","published_at":"2026-05-19 12:00:00","summary":"文章介绍了用 AI 整理工作记录并生成周报的方法。","relevance_reason":"与 AI 写周报主题高度相关"}

event: delta
data: {"task_id":"task_001","stage":"generate_script","text":"今天教你用 AI 快速生成周报..."}

event: result
data: {"task_id":"task_001","type":"script","content_id":"script_001","message":"脚本已生成"}

event: done
data: {"task_id":"task_001","status":"success","message":"生成完成"}
```

前端要求：

- SSE 断开后可以重新连接。
- 页面刷新后先调用任务详情恢复状态，再继续订阅 SSE。
- `delta` 可以追加展示，`result` 到达后以结构化接口数据为准。
- `error` 事件要展示运营可理解文案，并保留“查看任务详情”入口。

后端要求：

- 阶段结果必须落库。
- SSE 断开不影响后台任务继续执行。
- 错误写入任务日志和任务失败原因。

## 9. 素材汇总与来源接口

### 9.1 来源列表

`GET /api/v1/source/get_source_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `task_id` | 否 | 生成任务 ID |
| `summary_id` | 否 | 素材汇总 ID |
| `status` | 否 | `usable`、`not_suitable`、`uncertain` |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "src_001",
        "task_id": "task_001",
        "title": "AI 写周报的 5 个技巧",
        "site_name": "示例网站",
        "url": "https://example.com/article",
        "published_at": "2026-05-19 12:00:00",
        "summary": "文章介绍了用 AI 整理工作记录并生成周报的方法。",
        "relevance_reason": "与 AI 写周报主题高度相关",
        "key_points": ["整理本周事项", "生成结构化周报"],
        "status": "usable",
        "need_human_confirm": false
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 9.2 素材汇总详情

`GET /api/v1/source/get_summary_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "sum_001",
    "task_id": "task_001",
    "title": "AI 写周报素材汇总",
    "summary": "本次素材集中在周报结构化、工作记录整理和人工校对三个方向。",
    "key_points": ["AI 适合整理素材", "关键事实仍需人工确认", "输出后要补充具体数据"],
    "risk_notes": ["不要夸大为完全自动完成工作汇报"],
    "source_count": 20,
    "usable_source_count": 16,
    "need_human_confirm": true,
    "created_at": "2026-05-20 09:15:00"
  }
}
```

### 9.3 标记来源状态

`POST /api/v1/source/mark_source_status`

请求：

```json
{
  "source_id": "src_001",
  "status": "not_suitable",
  "reason": "内容与当前主题不相关"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "source_id": "src_001",
    "status": "not_suitable"
  }
}
```

## 10. 选题接口

### 10.1 选题列表

`GET /api/v1/topic/get_topic_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `task_id` | 否 | 生成任务 ID |
| `status` | 否 | 选题状态 |
| `keyword` | 否 | 标题关键词 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "topic_001",
        "task_id": "task_001",
        "title": "用 AI 10 分钟写完一份周报",
        "audience": "普通职场人",
        "angle": "把零散工作记录整理成可提交周报",
        "column": "一分钟 AI 办公",
        "duration_seconds": 60,
        "keywords": ["AI 写周报", "职场效率"],
        "reason": "主题具体，适合演示。",
        "status": "draft",
        "need_human_confirm": false,
        "created_at": "2026-05-20 09:20:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 10.2 选题详情

`GET /api/v1/topic/get_topic_detail/{id}`

响应 `data` 使用 4.3 选题结构，并额外包含关联素材：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "topic_001",
    "task_id": "task_001",
    "title": "用 AI 10 分钟写完一份周报",
    "audience": "普通职场人",
    "angle": "把零散工作记录整理成可提交周报",
    "column": "一分钟 AI 办公",
    "duration_seconds": 60,
    "keywords": ["AI 写周报", "职场效率"],
    "reason": "主题具体，适合 60 秒短视频演示。",
    "status": "draft",
    "source_summary_id": "sum_001",
    "source_items": []
  }
}
```

### 10.3 修改选题状态

`POST /api/v1/topic/change_topic_status`

请求：

```json
{
  "topic_id": "topic_001",
  "status": "approved",
  "reason": ""
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "topic_id": "topic_001",
    "status": "approved"
  }
}
```

### 10.4 基于选题生成脚本

`POST /api/v1/topic/generate_script`

请求：

```json
{
  "topic_id": "topic_001",
  "start_mode": "now"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_002",
    "topic_id": "topic_001",
    "status": "pending",
    "stream_url": "/api/v1/generation/stream/task_002"
  }
}
```

## 11. 脚本、分镜、字幕接口

### 11.1 脚本详情

`GET /api/v1/script/get_script_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "script": {
      "id": "script_001",
      "topic_id": "topic_001",
      "title": "用 AI 10 分钟写完一份周报",
      "hook": "周五最痛苦的事，是发现周报还没写。",
      "pain_point": "很多人一周做了不少事，但写周报时想不起来重点。",
      "method": "先让 AI 整理工作记录，再生成周报结构。",
      "steps": ["粘贴本周事项", "要求 AI 按成果、问题、下周计划整理"],
      "example": "把会议纪要、待办记录和完成事项放到一起。",
      "summary": "AI 负责整理，人负责判断。",
      "cta": "下次写周报前，先把本周记录丢给 AI 整理。",
      "platform_title": "用 AI 10 分钟写完周报",
      "description": "一个适合普通职场人的 AI 周报写作方法。",
      "tags": ["AI办公", "职场效率", "周报"],
      "cover_text": "AI 写周报",
      "pinned_comment": "试试先整理工作记录，再让 AI 生成周报结构。",
      "status": "pending_review",
      "version": 1
    },
    "storyboards": [],
    "subtitles": [],
    "versions": [
      {
        "version": 1,
        "operator_name": "系统生成",
        "created_at": "2026-05-20 09:30:00"
      }
    ]
  }
}
```

### 11.2 更新脚本

`POST /api/v1/script/update_script`

请求：

```json
{
  "script_id": "script_001",
  "title": "用 AI 10 分钟写完一份周报",
  "hook": "周报写不出来？先让 AI 帮你整理记录。",
  "pain_point": "很多人有记录，但不会整理成周报。",
  "method": "用 AI 把零散事项整理成结构化内容。",
  "steps": ["整理本周事项", "生成周报结构", "人工补充数字"],
  "example": "输入会议纪要和完成事项，让 AI 输出三段式周报。",
  "summary": "AI 提效，人工把关。",
  "cta": "下次写周报前先整理记录。",
  "platform_title": "AI 周报写作方法",
  "description": "适合职场人的 AI 周报写法。",
  "tags": ["AI办公", "周报"],
  "cover_text": "AI 写周报",
  "pinned_comment": "先整理记录，再生成周报结构。"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "script_id": "script_001",
    "version": 2,
    "updated_at": "2026-05-20 10:00:00"
  }
}
```

### 11.3 更新分镜

`POST /api/v1/storyboard/update_storyboard`

请求：

```json
{
  "script_id": "script_001",
  "items": [
    {
      "id": "shot_001",
      "shot_no": 1,
      "duration_seconds": 6,
      "voiceover": "周报写不出来？先让 AI 帮你整理记录。",
      "subtitle": "周报写不出来？",
      "visual_type": "screen_recording",
      "material_suggestion": "展示周报文档",
      "motion_suggestion": "标题滑入"
    }
  ]
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "script_id": "script_001",
    "storyboard_count": 1,
    "version": 2
  }
}
```

### 11.4 更新字幕

`POST /api/v1/subtitle/update_subtitle`

请求：

```json
{
  "script_id": "script_001",
  "items": [
    {
      "id": "sub_001",
      "start_time": "00:00:00.000",
      "end_time": "00:00:03.000",
      "text": "周报写不出来？"
    }
  ]
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "script_id": "script_001",
    "subtitle_count": 1,
    "version": 2
  }
}
```

## 12. 审核接口

### 12.1 审核列表

`GET /api/v1/review/get_review_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `status` | 否 | 内容状态 |
| `keyword` | 否 | 标题关键词 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "content_id": "script_001",
        "content_type": "script",
        "title": "用 AI 10 分钟写完一份周报",
        "status": "pending_review",
        "need_human_confirm": true,
        "risk_notes": ["涉及效率提升，需避免夸张承诺"],
        "created_by_name": "系统生成",
        "created_at": "2026-05-20 09:30:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 12.2 通过

`POST /api/v1/review/approve`

请求：

```json
{
  "content_id": "script_001",
  "content_type": "script",
  "comment": "内容可用"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "content_id": "script_001",
    "status": "approved",
    "next_status": "pending_render"
  }
}
```

### 12.3 修改后通过

`POST /api/v1/review/approve_with_edit`

请求：

```json
{
  "content_id": "script_001",
  "content_type": "script",
  "edited_payload": {
    "hook": "周报写不出来？先让 AI 帮你整理记录。"
  },
  "comment": "已修改开头表达"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "content_id": "script_001",
    "status": "approved_with_edit",
    "version": 2,
    "next_status": "pending_render"
  }
}
```

### 12.4 驳回

`POST /api/v1/review/reject`

请求：

```json
{
  "content_id": "script_001",
  "content_type": "script",
  "reason": "事实依据不足，需要重新生成"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "content_id": "script_001",
    "status": "rejected"
  }
}
```

### 12.5 重新生成

`POST /api/v1/review/regenerate`

请求：

```json
{
  "content_id": "script_001",
  "content_type": "script",
  "reason": "换一个更具体的脚本角度"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "task_003",
    "status": "pending",
    "stream_url": "/api/v1/generation/stream/task_003"
  }
}
```

## 13. 话题监控接口

### 13.1 创建监控任务

`POST /api/v1/monitor/create_monitor`

前端页面字段映射：

| 页面字段 | 接口字段 |
| --- | --- |
| 监控的话题 | `topic` |
| 主要关注的人群 | `audience` |
| 每天什么时候更新 | `schedule_time` |
| 每次最多抓取多少条 | `fetch_limit` |
| 是否自动生成选题 | `auto_generate_topics` |

请求：

```json
{
  "topic": "AI 办公工具更新",
  "audience": "普通职场人",
  "schedule_time": "09:00",
  "fetch_limit": 20,
  "auto_generate_topics": true
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "monitor_id": "mon_001",
    "status": "enabled"
  }
}
```

### 13.2 监控任务列表

`GET /api/v1/monitor/get_monitor_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `status` | 否 | `enabled`、`paused`、`deleted` |
| `keyword` | 否 | 话题关键词 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "mon_001",
        "topic": "AI 办公工具更新",
        "audience": "普通职场人",
        "schedule_time": "09:00",
        "fetch_limit": 20,
        "auto_generate_topics": true,
        "status": "enabled",
        "last_run_at": "2026-05-20 09:00:00",
        "last_summary_id": "sum_002",
        "created_at": "2026-05-19 18:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 13.3 监控任务详情

`GET /api/v1/monitor/get_monitor_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "mon_001",
    "topic": "AI 办公工具更新",
    "audience": "普通职场人",
    "schedule_time": "09:00",
    "fetch_limit": 20,
    "auto_generate_topics": true,
    "status": "enabled",
    "created_at": "2026-05-19 18:00:00",
    "updated_at": "2026-05-20 09:00:00"
  }
}
```

### 13.4 更新监控任务

`POST /api/v1/monitor/update_monitor`

请求：

```json
{
  "monitor_id": "mon_001",
  "topic": "AI 办公工具更新",
  "audience": "普通职场人",
  "schedule_time": "10:00",
  "fetch_limit": 30,
  "auto_generate_topics": true
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "monitor_id": "mon_001",
    "status": "enabled"
  }
}
```

### 13.5 修改监控状态

`POST /api/v1/monitor/change_monitor_status`

请求：

```json
{
  "monitor_id": "mon_001",
  "status": "paused"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "monitor_id": "mon_001",
    "status": "paused"
  }
}
```

### 13.6 每日汇总列表

`GET /api/v1/monitor/get_daily_summary_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `monitor_id` | 否 | 监控任务 ID |
| `start_date` | 否 | 开始日期 |
| `end_date` | 否 | 结束日期 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "summary_id": "sum_002",
        "monitor_id": "mon_001",
        "topic": "AI 办公工具更新",
        "date": "2026-05-20",
        "source_count": 20,
        "topic_count": 10,
        "status": "success",
        "created_at": "2026-05-20 09:10:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

## 14. 视频合成接口

### 14.1 创建合成任务

`POST /api/v1/render/create_render_task`

请求：

```json
{
  "script_id": "script_001",
  "template_id": "default_vertical",
  "start_mode": "now"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "render_task_id": "render_001",
    "status": "pending"
  }
}
```

### 14.2 合成列表

`GET /api/v1/render/get_render_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `status` | 否 | `pending`、`rendering`、`failed`、`success` |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "render_001",
        "script_id": "script_001",
        "title": "用 AI 10 分钟写完一份周报",
        "status": "success",
        "progress": 100,
        "video_id": "video_001",
        "duration_seconds": 60,
        "error_message": "",
        "created_at": "2026-05-20 10:30:00",
        "updated_at": "2026-05-20 10:40:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 14.3 重试合成

`POST /api/v1/render/retry_render`

请求：

```json
{
  "render_task_id": "render_001"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "render_task_id": "render_001",
    "status": "pending"
  }
}
```

### 14.4 视频详情

`GET /api/v1/render/get_video_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "video_001",
    "script_id": "script_001",
    "title": "用 AI 10 分钟写完一份周报",
    "duration_seconds": 60,
    "width": 1080,
    "height": 1920,
    "format": "mp4",
    "preview_url": "/api/v1/file/preview_video/video_001",
    "download_url": "/api/v1/file/download_video/video_001",
    "cover_url": "/api/v1/file/preview_cover/cover_001",
    "created_at": "2026-05-20 10:40:00"
  }
}
```

## 15. 发布包接口

### 15.1 创建发布包

`POST /api/v1/package/create_package`

请求：

```json
{
  "script_id": "script_001",
  "video_id": "video_001",
  "platforms": ["douyin", "xiaohongshu", "bilibili"]
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "package_id": "pkg_001",
    "status": "exported",
    "download_url": "/api/v1/package/download_package/pkg_001"
  }
}
```

### 15.2 发布包列表

`GET /api/v1/package/get_package_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `keyword` | 否 | 标题关键词 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "pkg_001",
        "title": "用 AI 10 分钟写完一份周报",
        "video_id": "video_001",
        "script_id": "script_001",
        "platforms": ["douyin", "xiaohongshu"],
        "file_size": 104857600,
        "download_url": "/api/v1/package/download_package/pkg_001",
        "created_at": "2026-05-20 11:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 15.3 发布包详情

`GET /api/v1/package/get_package_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "pkg_001",
    "title": "用 AI 10 分钟写完一份周报",
    "video_file": {
      "name": "video.mp4",
      "download_url": "/api/v1/file/download_video/video_001"
    },
    "cover_file": {
      "name": "cover.jpg",
      "download_url": "/api/v1/file/download_cover/cover_001"
    },
    "platform_title": "用 AI 10 分钟写完周报",
    "description": "一个适合普通职场人的 AI 周报写作方法。",
    "tags": ["AI办公", "职场效率", "周报"],
    "pinned_comment": "试试先整理工作记录，再让 AI 生成周报结构。",
    "script_text": "完整口播稿文本",
    "storyboards": [],
    "knowledge_cards": [],
    "download_draft": "资料包草稿内容",
    "download_url": "/api/v1/package/download_package/pkg_001",
    "created_at": "2026-05-20 11:00:00"
  }
}
```

### 15.4 下载发布包

`GET /api/v1/package/download_package/{id}`

响应：

- 成功：返回 `application/zip` 文件流。
- 失败：返回通用错误响应。

## 16. 发布记录接口

### 16.1 创建发布记录

`POST /api/v1/publish/create_record`

请求：

```json
{
  "package_id": "pkg_001",
  "platform": "douyin",
  "platform_url": "https://www.douyin.com/video/xxx",
  "published_at": "2026-05-20 12:00:00",
  "status": "published",
  "remark": "运营手动发布"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "record_id": "pub_001",
    "status": "published"
  }
}
```

### 16.2 更新发布记录

`POST /api/v1/publish/update_record`

请求：

```json
{
  "record_id": "pub_001",
  "platform_url": "https://www.douyin.com/video/xxx",
  "published_at": "2026-05-20 12:00:00",
  "status": "published",
  "remark": "链接已确认"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "record_id": "pub_001",
    "status": "published"
  }
}
```

### 16.3 发布记录列表

`GET /api/v1/publish/get_record_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `package_id` | 否 | 发布包 ID |
| `platform` | 否 | 发布平台 |
| `status` | 否 | `draft`、`published`、`failed`、`offline` |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "pub_001",
        "package_id": "pkg_001",
        "title": "用 AI 10 分钟写完一份周报",
        "platform": "douyin",
        "platform_url": "https://www.douyin.com/video/xxx",
        "published_at": "2026-05-20 12:00:00",
        "status": "published",
        "remark": "运营手动发布",
        "created_by_name": "视频运营",
        "created_at": "2026-05-20 12:10:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

## 17. 每日报告接口

### 17.1 日报列表

`GET /api/v1/report/get_daily_report_list`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `start_date` | 否 | 开始日期 |
| `end_date` | 否 | 结束日期 |
| `page` | 否 | 默认 1 |
| `page_size` | 否 | 默认 20 |

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [
      {
        "id": "report_001",
        "date": "2026-05-20",
        "title": "2026-05-20 每日产出报告",
        "generation_task_count": 12,
        "script_count": 8,
        "video_count": 3,
        "package_count": 2,
        "failed_task_count": 1,
        "created_at": "2026-05-20 23:00:00"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 20
  }
}
```

### 17.2 日报详情

`GET /api/v1/report/get_daily_report_detail/{id}`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "report_001",
    "date": "2026-05-20",
    "title": "2026-05-20 每日产出报告",
    "overview": {
      "generation_task_count": 12,
      "source_item_count": 86,
      "topic_count": 30,
      "script_count": 8,
      "video_count": 3,
      "package_count": 2,
      "failed_task_count": 1
    },
    "source_summaries": [],
    "generated_contents": [],
    "pending_reviews": [],
    "render_success_items": [],
    "failed_tasks": [],
    "exported_packages": [],
    "tomorrow_suggestions": ["优先审核待处理脚本", "复盘合成失败原因"],
    "markdown": "# 2026-05-20 每日产出报告\n\n..."
  }
}
```

### 17.3 导出日报

`GET /api/v1/report/export_daily_report/{id}?format=markdown`

查询参数：

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `format` | 否 | `markdown` 或 `pdf`，默认 `markdown` |

响应：

- `format=markdown`：返回 Markdown 文件流。
- `format=pdf`：返回 PDF 文件流。

## 18. 系统设置接口

### 18.1 获取设置

`GET /api/v1/setting/get_setting`

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "default_count": 5,
    "default_fetch_limit": 20,
    "enabled_columns": [
      {
        "value": "one_minute_ai_office",
        "label": "一分钟 AI 办公",
        "enabled": true
      },
      {
        "value": "less_overtime",
        "label": "今天少加班一小时",
        "enabled": true
      }
    ],
    "storage_type": "local",
    "model_provider": "openai_compatible",
    "model_key_masked": "sk-****abcd"
  }
}
```

权限要求：

- 管理员可查看敏感配置的脱敏值。
- 普通运营不可见模型密钥字段。

### 18.2 更新设置

`POST /api/v1/setting/update_setting`

请求：

```json
{
  "default_count": 5,
  "default_fetch_limit": 20,
  "enabled_columns": ["one_minute_ai_office", "less_overtime", "boss_ai"],
  "model_provider": "openai_compatible",
  "model_base_url": "https://api.example.com/v1",
  "model_api_key": "sk-xxx"
}
```

响应：

```json
{
  "code": 0,
  "message": "success",
  "data": true
}
```

## 19. 文件预览与下载接口

这些接口用于后端统一鉴权，避免前端直接暴露服务器内部文件路径。

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| GET | `/api/v1/file/preview_video/{id}` | 视频预览 |
| GET | `/api/v1/file/download_video/{id}` | 视频下载 |
| GET | `/api/v1/file/preview_cover/{id}` | 封面预览 |
| GET | `/api/v1/file/download_cover/{id}` | 封面下载 |
| GET | `/api/v1/file/download_asset/{id}` | 通用资产下载 |

响应：

- 预览接口返回可被浏览器播放或展示的文件流。
- 下载接口返回 `Content-Disposition: attachment`。
- 无权限或文件不存在时返回通用错误响应。

## 20. 前端 Mock 最小数据

前端 mock 应至少覆盖：

- 登录成功、Token 过期、无权限。
- 生成任务：等待中、运行中、成功、失败、已取消。
- SSE：`start`、`stage`、`source`、`delta`、`result`、`error`、`done`。
- 审核：待审核、通过、驳回、修改后通过。
- 视频合成：待合成、合成中、合成失败、已合成。
- 发布包：列表、详情、下载地址。
- 空列表、接口失败、分页总数为 0。

## 21. MVP 联调顺序

1. 登录、退出、当前用户、权限菜单。
2. 首页概览统计。
3. 创建生成任务。
4. SSE 生成过程展示。
5. 任务详情刷新恢复。
6. 素材汇总与来源列表。
7. 选题列表、详情、状态变更。
8. 脚本、分镜、字幕详情与编辑保存。
9. 审核通过、修改后通过、驳回、重新生成。
10. 视频合成列表、发起合成、重试、预览和下载。
11. 发布包创建、列表、详情、下载。
12. 发布记录回填。
13. 话题监控、每日汇总。
14. 数据看板、每日报告。
15. 系统设置与角色权限校验。

## 22. 联调验收检查

- 前端可用 mock 独立开发，后端可用 Swagger/Postman 独立调试。
- 所有登录后接口均需要 Token。
- 从创建生成任务到导出发布包的主链路可走通。
- SSE 可实时显示抓取、素材汇总和 LLM 生成状态。
- 页面刷新后可通过任务详情恢复进度和结果。
- 失败任务有可理解错误提示和后端日志。
- 所有列表接口支持分页。
- 所有下载接口经过后端鉴权。
- 普通运营页面不展示模型参数、提示词、任务 ID、内部路径和原始异常。
