# 24小时AI增长资产引擎接口与联调任务清单

版本：v1.0  
日期：2026-05-19  
适用范围：前后端接口、SSE、联调、部署边界  

## 1. 联调边界

- 前端只调用后端 API、SSE 和文件下载接口。
- 后端只提供接口和数据，不渲染前端页面。
- 前端开发可使用 mock 数据。
- 后端开发可使用 Swagger/Postman 独立验证。
- 接口字段允许使用技术名，前端页面必须转换为业务语义文案。

## 2. 通用接口约定

### 请求

- 业务接口统一使用 `/api/v1` 前缀。
- 登录后接口统一携带 `Authorization: Bearer <token>`。
- 普通 JSON 请求使用 `application/json`。
- 文件下载使用独立下载接口。
- SSE 使用 `text/event-stream`。

### 响应

普通响应建议结构：

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

分页响应建议结构：

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

错误响应要求：

- 后端保留技术错误日志。
- 前端显示运营可理解的错误提示。
- 普通运营界面不展示堆栈、SQL、模型原始错误或密钥信息。

## 3. API 清单

### 认证

- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### 生成任务

- `POST /api/v1/generation/create_task`
- `GET /api/v1/generation/get_task_list`
- `GET /api/v1/generation/get_task_detail/{id}`
- `GET /api/v1/generation/stream/{id}`
- `POST /api/v1/generation/cancel_task`
- `POST /api/v1/generation/retry_task`

### 素材

- `GET /api/v1/source/get_source_list`
- `GET /api/v1/source/get_summary_detail/{id}`
- `POST /api/v1/source/mark_source_status`

### 选题

- `GET /api/v1/topic/get_topic_list`
- `GET /api/v1/topic/get_topic_detail/{id}`
- `POST /api/v1/topic/change_topic_status`
- `POST /api/v1/topic/generate_script`

### 脚本分镜

- `GET /api/v1/script/get_script_detail/{id}`
- `POST /api/v1/script/update_script`
- `POST /api/v1/storyboard/update_storyboard`
- `POST /api/v1/subtitle/update_subtitle`

### 审核

- `GET /api/v1/review/get_review_list`
- `POST /api/v1/review/approve`
- `POST /api/v1/review/approve_with_edit`
- `POST /api/v1/review/reject`
- `POST /api/v1/review/regenerate`

### 话题监控

- `POST /api/v1/monitor/create_monitor`
- `GET /api/v1/monitor/get_monitor_list`
- `GET /api/v1/monitor/get_monitor_detail/{id}`
- `POST /api/v1/monitor/update_monitor`
- `POST /api/v1/monitor/change_monitor_status`
- `GET /api/v1/monitor/get_daily_summary_list`

### 视频合成

- `POST /api/v1/render/create_render_task`
- `GET /api/v1/render/get_render_list`
- `POST /api/v1/render/retry_render`
- `GET /api/v1/render/get_video_detail/{id}`

### 发布包

- `POST /api/v1/package/create_package`
- `GET /api/v1/package/get_package_list`
- `GET /api/v1/package/get_package_detail/{id}`
- `GET /api/v1/package/download_package/{id}`

### 发布记录

- `POST /api/v1/publish/create_record`
- `POST /api/v1/publish/update_record`
- `GET /api/v1/publish/get_record_list`

### 看板和日报

- `GET /api/v1/dashboard/get_overview`
- `GET /api/v1/dashboard/get_trend`
- `GET /api/v1/report/get_daily_report_list`
- `GET /api/v1/report/get_daily_report_detail/{id}`
- `GET /api/v1/report/export_daily_report/{id}`

### 系统设置

- `GET /api/v1/setting/get_setting`
- `POST /api/v1/setting/update_setting`

## 4. SSE 约定

生成任务 SSE：

```text
GET /api/v1/generation/stream/{id}
```

响应头：

```text
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
```

事件类型：

- `start`：任务开始
- `stage`：阶段变化
- `source`：抓取来源
- `delta`：LLM 文本增量
- `result`：阶段结构化结果
- `error`：任务错误
- `done`：任务完成

事件示例：

```text
event: stage
data: {"stage":"抓取相关内容","task_id":"xxx"}

event: source
data: {"title":"示例来源标题","url":"https://example.com"}

event: delta
data: {"text":"今天教你用 AI 快速生成周报..."}

event: result
data: {"type":"script","content_id":"xxx"}

event: done
data: {"task_id":"xxx","status":"success"}
```

前端要求：

- 支持断线重连。
- 页面刷新后查询任务详情恢复状态。
- 错误提示转换为业务文案。

后端要求：

- 阶段结果需要落库。
- SSE 断开不影响后台任务继续执行。
- 错误写入任务日志。

## 5. 字段语义映射

内容生成表单：

- 你想做什么内容 -> `direction`
- 这次想讲什么主题 -> `topic`
- 主要给谁看 -> `audience`
- 一次生成几条 -> `count`
- 内容更适合哪个栏目 -> `column`
- 这次要生成到哪一步 -> `generation_type`
- 是否现在开始 -> `start_mode`

话题监控表单：

- 监控的话题 -> `topic`
- 主要关注的人群 -> `audience`
- 每天什么时候更新 -> `schedule_time`
- 每次最多抓取多少条 -> `fetch_limit`
- 是否自动生成选题 -> `auto_generate_topics`

前端页面不直接展示内部参数名。

## 6. 联调顺序

1. 登录和权限。
2. 创建生成任务。
3. SSE 流式输出。
4. 网络抓取和素材汇总展示。
5. LLM 生成选题。
6. LLM 生成脚本、分镜和字幕。
7. 审核流。
8. 视频合成。
9. 发布包导出。
10. 发布记录回填。
11. 话题监控自动任务。
12. 数据看板和日报。

## 7. 联调交付检查

- 从输入内容方向到导出发布包完整闭环可走通。
- 从话题监控到每日素材汇总可走通。
- SSE 可实时显示抓取、汇总和生成状态。
- 失败任务有错误提示和日志。
- 后台数据看板能看到核心指标。
- 前端和后端可以独立启动。
- 前端和后端可以独立部署。
