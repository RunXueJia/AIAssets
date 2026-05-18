# 接口规范

后端使用 Python + FastAPI。接口前缀统一为 `/api/v1`，查询使用 `GET`，变更使用 `POST`。后台接口默认需要登录和权限校验，公开站接口单独标记为公开。

## 1. 通用约定

### 1.1 响应格式

```json
{
  "code": 200,
  "message": "成功",
  "data": {}
}
```

列表响应：

```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```

错误响应：

```json
{
  "code": 400,
  "message": "参数错误",
  "data": null
}
```

### 1.2 认证

后台接口 Header：

```http
Authorization: Bearer <access_token>
```

### 1.3 分页参数

| 参数 | 类型 | 必填 | 默认 | 说明 |
| --- | --- | --- | --- | --- |
| page | int | 否 | 1 | 页码 |
| page_size | int | 否 | 20 | 每页数量，最大 100 |
| keyword | string | 否 |  | 搜索词 |

### 1.4 通用字段

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| id | string | 资源 ID，建议 UUID |
| status | string | 状态 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |

### 1.5 主要枚举

内容方向状态：`enabled`、`disabled`

LLM 调用状态：`queued`、`streaming`、`success`、`failed`、`repaired`、`interrupted`

内容审核状态：`draft`、`pending_review`、`approved`、`rejected`、`regenerating`

视频状态：`waiting`、`rendering`、`success`、`failed`

发布状态：`draft`、`pending_review`、`approved`、`rendering`、`render_failed`、`pending_publish`、`published`、`offline`

任务状态：`queued`、`running`、`success`、`failed`、`cancelled`、`retrying`

## 2. 认证与用户

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| POST | `/auth/login` | 公开 | 登录 |
| POST | `/auth/logout` | 登录 | 退出 |
| GET | `/auth/get_current_user` | 登录 | 获取当前用户 |
| POST | `/auth/refresh_token` | 登录 | 刷新 Token |
| GET | `/users/get_user_list` | `system:user:read` | 用户列表 |
| GET | `/users/get_user_detail/{id}` | `system:user:read` | 用户详情 |
| POST | `/users/create_user` | `system:user:create` | 创建用户 |
| POST | `/users/update_user` | `system:user:update` | 更新用户 |
| POST | `/users/change_user_status` | `system:user:update` | 启用或禁用用户 |
| POST | `/users/reset_user_password` | `system:user:update` | 重置密码 |
| GET | `/roles/get_role_list` | `system:role:read` | 角色列表 |
| POST | `/roles/create_role` | `system:role:create` | 创建角色 |
| POST | `/roles/update_role_permissions` | `system:role:update` | 分配权限 |

登录请求：

```json
{
  "username": "admin",
  "password": "password"
}
```

登录响应 `data`：

```json
{
  "access_token": "jwt",
  "refresh_token": "jwt",
  "expires_in": 7200,
  "user": {
    "id": "u_1",
    "username": "admin",
    "display_name": "管理员",
    "roles": ["admin"],
    "permissions": ["system:user:read"]
  }
}
```

## 3. 内容配置

### 3.1 内容方向

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/content_channels/get_content_channel_list` | `content:channel:read` | 内容方向列表 |
| GET | `/content_channels/get_content_channel_detail/{id}` | `content:channel:read` | 内容方向详情 |
| POST | `/content_channels/create_content_channel` | `content:channel:create` | 创建内容方向 |
| POST | `/content_channels/update_content_channel` | `content:channel:update` | 更新内容方向 |
| POST | `/content_channels/change_content_channel_status` | `content:channel:update` | 启用或停用 |

创建内容方向请求：

```json
{
  "name": "AI 工具 + 职场效率",
  "description": "AI 办公效率科普",
  "target_audience": "职场人、学生、小微企业主",
  "tone": "清晰、务实、可执行",
  "forbidden_topics": ["医疗诊断", "金融收益承诺"],
  "daily_topic_quota": 50,
  "reviewer_ids": ["u_2"],
  "default_video_template_id": "tpl_video_1",
  "default_article_template_id": "tpl_article_1"
}
```

### 3.2 栏目

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/columns/get_column_list` | `content:column:read` | 栏目列表 |
| GET | `/columns/get_column_detail/{id}` | `content:column:read` | 栏目详情 |
| POST | `/columns/create_column` | `content:column:create` | 创建栏目 |
| POST | `/columns/update_column` | `content:column:update` | 更新栏目 |
| POST | `/columns/change_column_status` | `content:column:update` | 启用或停用 |

### 3.3 模板与平台

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/video_templates/get_video_template_list` | `template:video:read` | 视频模板列表 |
| POST | `/video_templates/create_video_template` | `template:video:create` | 创建视频模板 |
| POST | `/video_templates/update_video_template` | `template:video:update` | 更新视频模板 |
| GET | `/article_templates/get_article_template_list` | `template:article:read` | 图文模板列表 |
| POST | `/article_templates/create_article_template` | `template:article:create` | 创建图文模板 |
| GET | `/platforms/get_platform_list` | `publish:platform:read` | 平台配置列表 |
| POST | `/platforms/update_platform` | `publish:platform:update` | 更新平台限制 |

## 4. LLM 调用与提示词

LLM 接口只允许后台访问。API Key 必须加密保存，列表和详情接口只能返回脱敏值，例如 `sk-***abcd`。

所有 LLM 生成、调试、修复和重试接口必须返回 OpenAI Chat Completions 兼容 SSE：

```http
Content-Type: text/event-stream; charset=utf-8
```

SSE 事件格式：

```text
data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"model-name","choices":[{"index":0,"delta":{"content":"增量文本"},"finish_reason":null}]}

data: [DONE]
```

供应商 `base_url` 按 OpenAI 兼容 `/v1` 根地址配置，后端向上游请求固定调用 `{base_url}/chat/completions`，请求体必须使用 `messages`、`model`、`stream: true`，建议同时使用 `stream_options.include_usage=true`。开启 usage 后，`[DONE]` 前可能出现一个 `choices: []` 的 usage chunk，前端不得将其当作内容增量；如果流中断，可能收不到最终 usage。前端通过 `fetch` 读取 POST 流式响应；不要用普通 JSON 响应承载 LLM 生成结果。完成后通过调用日志或业务详情接口读取解析后的结构化结果。

### 4.1 模型供应商

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/llm_providers/get_llm_provider_list` | `llm:provider:read` | LLM 供应商列表 |
| GET | `/llm_providers/get_llm_provider_detail/{id}` | `llm:provider:read` | LLM 供应商详情 |
| POST | `/llm_providers/create_llm_provider` | `llm:provider:create` | 创建供应商 |
| POST | `/llm_providers/update_llm_provider` | `llm:provider:update` | 更新供应商 |
| POST | `/llm_providers/change_llm_provider_status` | `llm:provider:update` | 启用或停用供应商 |
| POST | `/llm_providers/test_llm_provider` | `llm:provider:test` | 测试供应商连通性 |

创建供应商请求：

```json
{
  "name": "OpenAI Compatible",
  "provider_type": "openai_compatible",
  "base_url": "https://api.example.com/v1",
  "api_key": "sk-xxxx",
  "timeout_seconds": 60,
  "status": "enabled"
}
```

### 4.2 模型配置

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/llm_models/get_llm_model_list` | `llm:model:read` | 模型列表 |
| GET | `/llm_models/get_llm_model_detail/{id}` | `llm:model:read` | 模型详情 |
| POST | `/llm_models/create_llm_model` | `llm:model:create` | 创建模型配置 |
| POST | `/llm_models/update_llm_model` | `llm:model:update` | 更新模型配置 |
| POST | `/llm_models/change_llm_model_status` | `llm:model:update` | 启用或停用模型 |

模型配置对象：

```json
{
  "id": "model_1",
  "provider_id": "provider_1",
  "model_name": "gpt-4.1-mini",
  "display_name": "内容生成模型",
  "usage_type": "content_generation",
  "context_window": 128000,
  "max_output_tokens": 4096,
  "temperature": 0.7,
  "input_token_price": 0.0,
  "output_token_price": 0.0,
  "status": "enabled"
}
```

### 4.3 Prompt 模板

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/prompt_templates/get_prompt_template_list` | `llm:prompt:read` | Prompt 模板列表 |
| GET | `/prompt_templates/get_prompt_template_detail/{id}` | `llm:prompt:read` | Prompt 模板详情 |
| POST | `/prompt_templates/create_prompt_template` | `llm:prompt:create` | 创建 Prompt 模板 |
| POST | `/prompt_templates/update_prompt_template` | `llm:prompt:update` | 更新 Prompt 模板 |
| POST | `/prompt_templates/publish_prompt_template` | `llm:prompt:publish` | 发布模板版本 |
| POST | `/prompt_templates/change_prompt_template_status` | `llm:prompt:update` | 启用或停用 |
| POST | `/prompt_templates/stream_test_prompt_template` | `llm:prompt:test` | SSE 调试 Prompt 模板 |

Prompt 模板对象：

```json
{
  "id": "prompt_1",
  "scene": "topic_generation",
  "version": 1,
  "name": "选题生成模板",
  "system_prompt": "你是短视频内容策划专家。",
  "user_prompt": "请基于栏目 {{column_name}} 生成 {{count}} 个选题。",
  "variables": ["column_name", "count", "target_audience", "forbidden_topics"],
  "output_schema": {
    "type": "object",
    "properties": {
      "topics": {
        "type": "array"
      }
    },
    "required": ["topics"]
  },
  "status": "enabled"
}
```

Prompt 调试请求：

```json
{
  "prompt_template_id": "prompt_1",
  "model_id": "model_1",
  "variables": {
    "column_name": "一分钟 AI 办公",
    "count": 5,
    "target_audience": "普通职场人",
    "forbidden_topics": ["医疗诊断", "金融收益承诺"]
  }
}
```

Prompt 调试响应：`text/event-stream`

```text
data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"gpt-compatible","choices":[{"index":0,"delta":{"role":"assistant","content":"{"},"finish_reason":null}]}

data: {"id":"chatcmpl_xxx","object":"chat.completion.chunk","created":1770000000,"model":"gpt-compatible","choices":[{"index":0,"delta":{"content":"\"topics\":[]}"},"finish_reason":null}]}

data: [DONE]
```

### 4.4 LLM 调用日志与成本

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/llm_call_logs/get_llm_call_log_list` | `llm:log:read` | LLM 调用日志列表 |
| GET | `/llm_call_logs/get_llm_call_log_detail/{id}` | `llm:log:read` | LLM 调用日志详情 |
| GET | `/llm_call_logs/get_llm_cost_summary` | `llm:log:read` | LLM 成本汇总 |
| GET | `/llm_call_logs/get_llm_stream_chunks/{id}` | `llm:log:read` | 查询 SSE 原始分片 |
| POST | `/llm_call_logs/stream_retry_llm_call` | `llm:call:retry` | SSE 重试失败调用 |

调用日志对象：

```json
{
  "id": "llm_log_1",
  "task_id": "task_1",
  "target_type": "topic",
  "target_id": "topic_1",
  "scene": "topic_generation",
  "provider_id": "provider_1",
  "model_id": "model_1",
  "prompt_template_id": "prompt_1",
  "prompt_version": 1,
  "stream_completed": true,
  "first_token_ms": 600,
  "input_tokens": 800,
  "output_tokens": 1200,
  "estimated_cost": 0.0,
  "duration_ms": 3200,
  "status": "success",
  "error_message": null,
  "created_at": "2026-05-18T18:00:00+08:00"
}
```

## 5. 内容生产

### 5.1 选题

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/topics/get_topic_list` | `content:topic:read` | 选题列表 |
| GET | `/topics/get_topic_detail/{id}` | `content:topic:read` | 选题详情 |
| POST | `/topics/create_topic` | `content:topic:create` | 手动创建选题 |
| POST | `/topics/update_topic` | `content:topic:update` | 更新选题 |
| POST | `/topics/stream_generate_topics` | `content:topic:generate` | SSE 生成选题 |
| POST | `/topics/lock_topic` | `content:topic:update` | 锁定选题 |
| POST | `/topics/reject_topic` | `content:topic:review` | 驳回选题 |
| POST | `/topics/stream_generate_script` | `content:script:generate` | SSE 为选题生成脚本 |

SSE 生成选题请求：

```json
{
  "channel_id": "ch_1",
  "column_id": "col_1",
  "count": 50,
  "keyword_seeds": ["AI 写周报", "AI 做会议纪要"],
  "model_id": "model_1",
  "prompt_template_id": "prompt_topic_1"
}
```

该接口响应为 `text/event-stream`。流完成后，前端通过选题列表、任务日志或 LLM 调用日志读取解析后的结构化结果。

选题对象：

```json
{
  "id": "topic_1",
  "channel_id": "ch_1",
  "column_id": "col_1",
  "title": "用 AI 10 分钟写完周报",
  "subtitle": "适合职场人的周报生成方法",
  "keywords": ["AI", "周报", "办公效率"],
  "audience": "普通职场人",
  "angle": "减少重复写作",
  "difficulty": "beginner",
  "expected_duration": 60,
  "recommended_platforms": ["douyin", "xiaohongshu"],
  "generated_reason": "高频办公场景",
  "status": "generated"
}
```

### 5.2 脚本

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/scripts/get_script_list` | `content:script:read` | 脚本列表 |
| GET | `/scripts/get_script_detail/{id}` | `content:script:read` | 脚本详情 |
| POST | `/scripts/update_script` | `content:script:update` | 更新脚本 |
| POST | `/scripts/stream_regenerate_script` | `content:script:generate` | SSE 重新生成脚本 |
| GET | `/scripts/get_script_versions/{id}` | `content:script:read` | 脚本版本 |
| POST | `/scripts/stream_generate_storyboard` | `content:storyboard:generate` | SSE 生成分镜 |

脚本对象：

```json
{
  "id": "script_1",
  "topic_id": "topic_1",
  "version": 1,
  "duration_type": "60s",
  "hook": "还在手写周报？",
  "body": [
    {
      "section": "problem",
      "content": "很多人每周都重复整理工作内容。"
    }
  ],
  "ending": "保存这个方法，下次写周报直接套用。",
  "platform_title": "AI 写周报的 3 步方法",
  "platform_description": "一个适合职场人的 AI 周报流程。",
  "tags": ["AI办公", "周报", "效率"],
  "risk_flags": ["需避免承诺一定减少加班"],
  "status": "pending_review"
}
```

### 5.3 分镜

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/storyboards/get_storyboard_list` | `content:storyboard:read` | 分镜列表 |
| GET | `/storyboards/get_storyboard_detail/{script_id}` | `content:storyboard:read` | 某脚本分镜 |
| POST | `/storyboards/update_storyboard` | `content:storyboard:update` | 更新分镜 |
| POST | `/storyboards/stream_regenerate_storyboard` | `content:storyboard:generate` | SSE 重新生成分镜 |

分镜对象：

```json
{
  "id": "scene_1",
  "script_id": "script_1",
  "scene_index": 1,
  "duration_seconds": 6,
  "voiceover": "还在手写周报？",
  "subtitle": "还在手写周报？",
  "visual_type": "title",
  "visual_prompt": "竖屏标题页，突出周报和 AI",
  "motion_hint": "标题快速进入",
  "music_hint": "轻快办公感"
}
```

## 6. 审核

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/reviews/get_review_queue` | `review:content:read` | 待审核队列 |
| GET | `/reviews/get_review_records` | `review:content:read` | 审核记录 |
| POST | `/reviews/approve_content` | `review:content:approve` | 审核通过 |
| POST | `/reviews/reject_content` | `review:content:reject` | 驳回 |
| POST | `/reviews/approve_content_with_changes` | `review:content:approve` | 修改后通过 |
| POST | `/reviews/stream_request_regeneration` | `review:content:update` | SSE 请求重新生成 |

审核请求：

```json
{
  "target_type": "script",
  "target_id": "script_1",
  "comment": "内容可发布"
}
```

驳回请求：

```json
{
  "target_type": "script",
  "target_id": "script_1",
  "reason": "标题承诺过强，需要降低绝对化表达"
}
```

## 7. 视频、卡片和资料包

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/videos/get_video_list` | `asset:video:read` | 视频列表 |
| GET | `/videos/get_video_detail/{id}` | `asset:video:read` | 视频详情 |
| POST | `/videos/create_render_task` | `asset:video:render` | 创建合成任务 |
| POST | `/videos/retry_render_task` | `asset:video:render` | 重试合成 |
| POST | `/videos/regenerate_cover` | `asset:video:update` | 重新生成封面 |
| GET | `/videos/get_video_download_url/{id}` | `asset:video:download` | 获取下载地址 |
| GET | `/knowledge_cards/get_knowledge_card_list` | `asset:card:read` | 知识卡片列表 |
| POST | `/knowledge_cards/stream_generate_knowledge_cards` | `asset:card:generate` | SSE 生成知识卡片 |
| GET | `/download_assets/get_download_asset_list` | `asset:download:read` | 资料包列表 |
| POST | `/download_assets/stream_generate_download_asset` | `asset:download:generate` | SSE 生成资料包 |

创建视频合成任务请求：

```json
{
  "script_id": "script_1",
  "template_id": "tpl_video_1",
  "force": false
}
```

## 8. 图文页

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/article_pages/get_article_page_list` | `content:article:read` | 图文页列表 |
| GET | `/article_pages/get_article_page_detail/{id}` | `content:article:read` | 图文页详情 |
| POST | `/article_pages/stream_generate_article_page` | `content:article:generate` | SSE 生成图文页 |
| POST | `/article_pages/update_article_page` | `content:article:update` | 更新图文页 |
| POST | `/article_pages/change_article_page_status` | `content:article:publish` | 公开或下线 |

图文页对象：

```json
{
  "id": "article_1",
  "topic_id": "topic_1",
  "video_id": "video_1",
  "slug": "ai-weekly-report",
  "title": "用 AI 写周报的 3 步方法",
  "summary": "适合职场人的周报提效流程。",
  "body": "Markdown or structured JSON",
  "seo_title": "AI 写周报方法",
  "seo_description": "学习如何用 AI 快速整理周报。",
  "status": "published",
  "published_at": "2026-05-18T18:00:00+08:00"
}
```

## 9. 发布队列

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/publish_queue/get_publish_queue_list` | `publish:queue:read` | 发布队列 |
| GET | `/publish_queue/get_publish_package_detail/{id}` | `publish:queue:read` | 发布包详情 |
| POST | `/publish_queue/create_publish_package` | `publish:package:create` | 生成发布包 |
| GET | `/publish_queue/get_publish_package_download_url/{id}` | `publish:package:download` | 下载发布包 |
| POST | `/publish_queue/mark_as_published` | `publish:queue:update` | 标记已发布 |
| POST | `/publish_queue/mark_as_offline` | `publish:queue:update` | 标记已下线 |

标记已发布请求：

```json
{
  "publish_item_id": "pub_1",
  "platform": "douyin",
  "platform_url": "https://example.com/video/1",
  "published_at": "2026-05-18T20:00:00+08:00"
}
```

## 10. 任务调度

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/tasks/get_task_log_list` | `system:task:read` | 任务日志列表 |
| GET | `/tasks/get_task_log_detail/{id}` | `system:task:read` | 任务日志详情 |
| POST | `/tasks/run_task` | `system:task:run` | 手动执行任务 |
| POST | `/tasks/retry_task` | `system:task:run` | 重试任务 |
| POST | `/tasks/cancel_task` | `system:task:update` | 取消任务 |
| POST | `/tasks/pause_schedule` | `system:task:update` | 暂停定时任务 |
| POST | `/tasks/resume_schedule` | `system:task:update` | 恢复定时任务 |
| GET | `/tasks/get_schedule_config` | `system:task:read` | 查看调度配置 |
| POST | `/tasks/update_schedule_config` | `system:task:update` | 更新调度配置 |

手动执行任务请求：

```json
{
  "task_type": "generate_topics",
  "target_id": "col_1",
  "payload": {
    "count": 20
  }
}
```

## 11. 线索与下载

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/leads/get_lead_list` | `lead:lead:read` | 线索列表 |
| GET | `/leads/get_lead_detail/{id}` | `lead:lead:read` | 线索详情 |
| GET | `/leads/export_leads` | `lead:lead:export` | 导出 CSV |
| POST | `/public/leads/submit_lead` | 公开 | 提交线索 |
| POST | `/public/downloads/request_download` | 公开 | 申请资料下载 |

公开线索提交请求：

```json
{
  "name": "张三",
  "contact": "zhangsan@example.com",
  "company": "示例公司",
  "role": "运营",
  "need_type": "download_asset",
  "source_page": "/articles/ai-weekly-report",
  "source_asset_id": "asset_1",
  "consent": true
}
```

## 12. 看板与日报

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/dashboard/get_today_overview` | `dashboard:overview:read` | 今日总览 |
| GET | `/dashboard/get_channel_performance` | `dashboard:overview:read` | 栏目表现 |
| GET | `/dashboard/get_task_metrics` | `dashboard:task:read` | 任务指标 |
| GET | `/dashboard/get_asset_growth` | `dashboard:overview:read` | 资产增长 |
| GET | `/reports/get_daily_report_list` | `report:daily:read` | 日报列表 |
| GET | `/reports/get_daily_report_detail/{id}` | `report:daily:read` | 日报详情 |
| POST | `/reports/stream_generate_daily_report` | `report:daily:generate` | SSE 手动生成日报 |
| GET | `/reports/export_daily_report/{id}` | `report:daily:export` | 导出日报 |

今日总览响应 `data`：

```json
{
  "date": "2026-05-18",
  "topics_count": 50,
  "scripts_count": 20,
  "videos_count": 10,
  "article_pages_count": 10,
  "knowledge_cards_count": 30,
  "download_assets_count": 5,
  "published_count": 8,
  "visit_count": 1200,
  "download_count": 80,
  "lead_count": 12,
  "task_success_rate": 0.92,
  "task_failed_rate": 0.08
}
```

## 13. 公开站接口

| 方法 | 路径 | 权限 | 说明 |
| --- | --- | --- | --- |
| GET | `/public/home/get_home_data` | 公开 | 首页数据 |
| GET | `/public/columns/get_column_list` | 公开 | 公开栏目 |
| GET | `/public/columns/get_column_detail/{id}` | 公开 | 栏目详情 |
| GET | `/public/articles/get_article_list` | 公开 | 图文列表 |
| GET | `/public/articles/get_article_detail/{slug}` | 公开 | 图文详情 |
| GET | `/public/videos/get_video_detail/{id}` | 公开 | 视频详情 |
| GET | `/public/topics/get_topic_page/{slug}` | 公开 | 内容专题页 |
| GET | `/public/download_assets/get_download_asset_list` | 公开 | 资料包列表 |
| GET | `/public/tools/get_tool_recommendation_list` | 公开 | 工具推荐 |
| POST | `/public/analytics/track_event` | 公开 | 访问和转化事件 |

访问事件请求：

```json
{
  "event_type": "article_view",
  "source_page": "/articles/ai-weekly-report",
  "target_id": "article_1",
  "referrer": "https://www.baidu.com",
  "utm_source": "seo"
}
```

## 14. 权限点建议

| 模块 | 权限点 |
| --- | --- |
| 系统用户 | `system:user:read`、`system:user:create`、`system:user:update` |
| 角色权限 | `system:role:read`、`system:role:create`、`system:role:update` |
| LLM 供应商 | `llm:provider:read`、`llm:provider:create`、`llm:provider:update`、`llm:provider:test` |
| LLM 模型 | `llm:model:read`、`llm:model:create`、`llm:model:update` |
| Prompt 模板 | `llm:prompt:read`、`llm:prompt:create`、`llm:prompt:update`、`llm:prompt:publish`、`llm:prompt:test` |
| LLM 日志 | `llm:log:read`、`llm:call:retry` |
| 内容方向 | `content:channel:read`、`content:channel:create`、`content:channel:update` |
| 栏目 | `content:column:read`、`content:column:create`、`content:column:update` |
| 选题 | `content:topic:read`、`content:topic:create`、`content:topic:update`、`content:topic:generate` |
| 脚本 | `content:script:read`、`content:script:update`、`content:script:generate` |
| 分镜 | `content:storyboard:read`、`content:storyboard:update`、`content:storyboard:generate` |
| 审核 | `review:content:read`、`review:content:approve`、`review:content:reject` |
| 视频资产 | `asset:video:read`、`asset:video:render`、`asset:video:download` |
| 资料资产 | `asset:download:read`、`asset:download:generate` |
| 发布 | `publish:queue:read`、`publish:queue:update`、`publish:package:create`、`publish:package:download` |
| 线索 | `lead:lead:read`、`lead:lead:export` |
| 看板日报 | `dashboard:overview:read`、`dashboard:task:read`、`report:daily:read`、`report:daily:generate`、`report:daily:export` |
| 任务 | `system:task:read`、`system:task:run`、`system:task:update` |
