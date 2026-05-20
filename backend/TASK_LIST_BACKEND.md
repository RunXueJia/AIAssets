# 路书匠 (RouteCraft) — 后端任务列表

> 基于 PROJECT_BRIEF.md 生成，按里程碑 (M0–M5) 组织。

---

## M0：简化原型（设计确认）

| # | 任务 | 说明 |
|---|------|------|
| 0.1 | 确认用户输入字段 | 起点、目的地、范围、交通方式 + 选填项 |
| 0.2 | 确认流式输出结构 | 8 个阶段的输出格式定义 |
| 0.3 | 确认后台管理范围 | 用户管理、生成记录、LLM 配置三大模块 |

---

## M1：后端基础

### 1.1 工程初始化

| # | 任务 | 说明 |
|---|------|------|
| 1.1.1 | 初始化 FastAPI 项目结构 | 按 `backend/app/api/v1/endpoints/` 等目录结构创建 |
| 1.1.2 | 配置 pyproject.toml | Python 3.12+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, httpx 等依赖 |
| 1.1.3 | 配置环境变量和 settings | Pydantic Settings，支持 .env 文件 |
| 1.1.4 | 接入 MySQL | 异步驱动 aiomysql 或 asyncmy |
| 1.1.5 | 接入 SQLAlchemy 2 异步会话 | AsyncSession + async_engine |
| 1.1.6 | 配置 Alembic 迁移 | 初始化 alembic，配置异步迁移 |
| 1.1.7 | 配置统一异常处理 | 全局 exception handlers |
| 1.1.8 | 配置统一响应结构 | 标准 JSON response schema |
| 1.1.9 | 配置请求日志和链路 ID | 中间件注入 request_id |
| 1.1.10 | 配置 CORS | 允许前端跨域 |
| 1.1.11 | 配置 ruff、mypy、pytest | 代码检查、类型检查、测试框架 |

### 1.2 用户与认证

| # | 任务 | 说明 |
|---|------|------|
| 1.2.1 | 用户数据模型 (users) | SQLAlchemy model |
| 1.2.2 | 用户注册 API | POST /api/v1/auth/register |
| 1.2.3 | 用户登录 API | POST /api/v1/auth/login，返回 JWT |
| 1.2.4 | 游客临时会话 API | POST /api/v1/auth/guest_session |
| 1.2.5 | Token 刷新 API | POST /api/v1/auth/refresh_token |
| 1.2.6 | 登出 API | POST /api/v1/auth/logout |
| 1.2.7 | JWT 鉴权中间件 | 依赖注入，保护需要登录的接口 |
| 1.2.8 | 管理员登录 | 通过 users.role 区分 |
| 1.2.9 | 管理员用户列表 API | GET /api/v1/admin/users |
| 1.2.10 | 管理员查看用户详情 API | GET /api/v1/admin/users/{user_id} |
| 1.2.11 | 管理员禁用/启用用户 API | POST /api/v1/admin/users/{user_id}/disable, /enable |

### 1.3 生成记录模块

| # | 任务 | 说明 |
|---|------|------|
| 1.3.1 | 生成记录数据模型 | generation_records 主表 + inputs/outputs 子表 |
| 1.3.2 | 创建生成记录 API | 保存用户输入快照，状态=pending |
| 1.3.3 | 查询用户自己的生成记录 API | GET /api/v1/planning/records |
| 1.3.4 | 查询生成记录详情 API | GET /api/v1/planning/records/{record_id} |
| 1.3.5 | 保存最终生成结果 | 生成完成后写入 outputs 表 |
| 1.3.6 | 生成状态管理 | pending → streaming → completed / failed |
| 1.3.7 | 管理端查询全部生成记录 API | GET /api/v1/admin/generation_records，支持筛选 |
| 1.3.8 | 管理端查看记录详情 API | GET /api/v1/admin/generation_records/{record_id} |
| 1.3.9 | 管理端查看错误详情 | 返回 generation_errors 内容 |
| 1.3.10 | 管理端重试失败记录 API | POST /api/v1/admin/generation_records/{record_id}/retry |
| 1.3.11 | 管理端删除记录 API | DELETE /api/v1/admin/generation_records/{record_id} |

---

## M2：流式规划

### 2.1 LLM 集成

| # | 任务 | 说明 |
|---|------|------|
| 2.1.1 | LLM 流式调用客户端封装 | httpx + SSE，支持 OpenAI 兼容格式 |
| 2.1.2 | TripPlanningRequest Schema | Pydantic v2 model |
| 2.1.3 | TripPlanningResult Schema | 包含各阶段输出字段 |
| 2.1.4 | 流式事件格式设计 | phase / type / content / metadata |
| 2.1.5 | SSE 接口实现 | POST /api/v1/planning/generate_stream |
| 2.1.6 | 用户中断生成 API | POST /api/v1/planning/cancel/{record_id} |
| 2.1.7 | 失败兜底文本 | LLM 异常时返回部分结果 |
| 2.1.8 | 重新生成 API | POST /api/v1/planning/records/{record_id}/regenerate |
| 2.1.9 | Prompt 模板管理 | 先使用配置文件/YAML 方式 |
| 2.1.10 | 上下文拼装 | 地图 + 天气 + 新闻数据组装到 prompt |
| 2.1.11 | 8 阶段流式输出控制 | 需求理解→天气→路线→交通→高德图→景点→新闻→汇总 |

### 2.2 高德地图集成

| # | 任务 | 说明 |
|---|------|------|
| 2.2.1 | 高德 API Key 配置 | 环境变量管理 |
| 2.2.2 | 地理编码服务 | 地址→坐标 |
| 2.2.3 | POI 搜索服务 | 周边景点/设施搜索 |
| 2.2.4 | 驾车路径规划服务 | 高德驾车路线 API |
| 2.2.5 | 公共交通路径规划服务 | 高德公交路线 API |
| 2.2.6 | 步行路径规划服务 | 高德步行路线 API |
| 2.2.7 | 路径点摘要生成 | 从路径结果提取关键点 |
| 2.2.8 | 高德路线分享链接生成 | 短链或 URI 生成 |
| 2.2.9 | 高德路径图导出 | 静态地图图片 |
| 2.2.10 | 高德接口错误重试 | 指数退避重试 |
| 2.2.11 | 高德结果缓存 | Redis 缓存 |

### 2.3 天气与新闻集成

| # | 任务 | 说明 |
|---|------|------|
| 2.3.1 | 天气 API 客户端 | 封装第三方天气 API |
| 2.3.2 | 目的地天气查询 | 当前 + 预报 |
| 2.3.3 | 沿途城市天气查询 | 按需查询沿途城市 |
| 2.3.4 | 天气预警摘要 | 恶劣天气风险提示 |
| 2.3.5 | 新闻/搜索 API 客户端 | 封装新闻或搜索 API |
| 2.3.6 | 目的地最近新闻查询 | 近 7 天资讯 |
| 2.3.7 | 交通管制和活动资讯查询 | 关键词搜索 |
| 2.3.8 | 外部数据来源和更新时间记录 | 所有数据标注来源+时间 |

### 2.4 管理端 LLM 配置

| # | 任务 | 说明 |
|---|------|------|
| 2.4.1 | LLM 配置数据模型 | llm_configs 表 |
| 2.4.2 | LLM 配置 CRUD API | 含 API Key 加密存储、列表掩码展示 |
| 2.4.3 | LLM 连接测试 API | POST /api/v1/admin/llm_configs/{id}/test |
| 2.4.4 | LLM 配置启用/停用 API | enable/disable |
| 2.4.5 | 配置变更审计日志 | config_audit_logs 表 |
| 2.4.6 | 管理端 LLM 配置读取 | 生成时读取启用的配置 |

### 2.5 内部辅助接口

| # | 任务 | 说明 |
|---|------|------|
| 2.5.1 | 地点搜索接口 | GET /api/v1/amap/search_places |
| 2.5.2 | 路线计算接口 | POST /api/v1/amap/calculate_route |
| 2.5.3 | 路线链接创建接口 | POST /api/v1/amap/create_route_link |
| 2.5.4 | 路径图导出接口 | POST /api/v1/amap/export_route_map |
| 2.5.5 | 天气查询接口 | GET /api/v1/weather/query |
| 2.5.6 | 新闻搜索接口 | GET /api/v1/news/search |

---

## M5：试用验证

| # | 任务 | 说明 |
|---|------|------|
| 5.1 | 连续生成 50 条规划记录 | 批量测试 |
| 5.2 | 统计平均生成耗时 | 性能指标 |
| 5.3 | 统计 LLM Token 成本 | 成本指标 |
| 5.4 | 统计地图/天气/新闻接口调用成本 | 成本指标 |
| 5.5 | 收集不可用的规划样例 | 质量评估 |
| 5.6 | 优化 Prompt 和外部数据上下文 | 迭代改进 |

---

## 测试任务

| # | 任务 | 说明 |
|---|------|------|
| T1 | Service 层单元测试 | 各 service 模块 |
| T2 | API 集成测试 | httpx + pytest-asyncio |
| T3 | LLM 客户端 Mock 测试 | 不依赖真实 API |
| T4 | 高德客户端 Mock 测试 | 不依赖外部 API |
| T5 | 天气和新闻客户端 Mock 测试 | 不依赖外部 API |
| T6 | SSE 流式接口测试 | 验证事件格式和中断 |
| T7 | 管理员权限测试 | 验证权限隔离 |

---

## 统计

| 里程碑 | 任务数 |
|--------|--------|
| M0 | 3 |
| M1 | 26 |
| M2 | 35 |
| M5 | 6 |
| 测试 | 7 |
| **合计** | **77** |
