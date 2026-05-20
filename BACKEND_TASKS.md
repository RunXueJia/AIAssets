# 24小时AI增长资产引擎后端任务清单

版本：v1.0  
日期：2026-05-19  
技术栈：Python + FastAPI + MySQL  
项目目录：backend  

## 实时进度同步

更新时间：2026-05-20 09:34

- 当前状态：已完成本轮后端 MVP 落地，待接入真实 MySQL/Redis/LLM/抓取/FFmpeg 环境后做联调。
- 已确认：`backend/` 目录为空，本轮从后端项目初始化开始搭建。
- 已确认：按用户要求，MySQL 数据库名固定为 `AIdrivenGrowthAssetEngine`。
- 已确认：后端接口前缀使用 `/api/v1`，响应格式遵循 `{code, message, data}`。
- 执行计划：先完成 FastAPI 项目骨架、配置、SQLAlchemy 模型、Alembic 迁移和初始化 SQL，再补齐主链路 API、SSE、审核、监控、合成、发布包、日报和系统设置接口。

更新时间：2026-05-20 10:25

- 已完成 B1：FastAPI 项目骨架、环境变量、CORS、统一异常、统一响应、基础日志表、README 和依赖清单。
- 已完成 B2：用户、角色、权限、角色权限关联、登录、退出、当前用户、JWT 兼容 Token、接口权限依赖和默认管理员初始化。
- 已完成 B3：按 `DATABASE_SCHEMA.md` 落地 P0/P1 数据表 SQLAlchemy 模型与 Alembic 初始迁移；初始化 SQL 创建数据库 `AIdrivenGrowthAssetEngine`。
- 已完成 B4-B10：生成任务、素材汇总、来源、选题、脚本、分镜、字幕、内容版本、任务日志和 SSE 接口；MVP 使用本地服务桩生成 5 条来源、10 个选题、脚本、6 段分镜和字幕。
- 已完成 B11-B15：审核、话题监控、合成任务、视频资产、发布包、发布记录接口；视频合成和发布包当前生成本地占位文件，保留可替换边界。
- 已完成 B16-B19：数据看板、每日报告、文件下载、系统设置接口。
- 验证通过：`python -m compileall backend\app backend\alembic`。
- 验证通过：`python -m ruff check backend\app backend\alembic`。
- 验证通过：FastAPI TestClient 调用 `/health` 返回 `database=AIdrivenGrowthAssetEngine`。
- 验证通过：`python -m alembic upgrade head --sql` 可离线渲染建表 SQL。
- 编码检查：本轮新增/修改的源码、配置、SQL、Markdown 未发现 UTF-8 BOM，未发现 U+FFFD。
- 待联调：真实 MySQL 执行 `scripts/create_database.sql` 和 `alembic upgrade head`，真实 Redis/Celery、网络抓取、OpenAI 兼容 LLM、FFmpeg 合成需接入生产配置后验证。

更新时间：2026-05-20 10:40

- 已补充 LLM 默认文件配置：`backend/.env.example` 新增 `LLM_MODEL_PROVIDER`、`LLM_MODEL_BASE_URL`、`LLM_MODEL_API_KEY`、`LLM_MODEL_NAME`、`LLM_REQUEST_TIMEOUT_SECONDS`。
- 已调整启动初始化：后端启动时会把 `.env` 中非空的 LLM 配置同步到 `system_setting` 表；`.env` 优先于数据库旧值。
- 已调整系统设置接口：`GET /api/v1/setting/get_setting` 返回 `model_base_url`、`model_name`、`model_timeout_seconds` 和脱敏后的 `model_key_masked`。

更新时间：2026-05-20 10:55

- 已在本机 MySQL 执行建库：`AIdrivenGrowthAssetEngine`。
- 已执行 Alembic 迁移：当前版本 `0001_initial_schema`。
- 已验证表数量：当前数据库包含 26 张表。
- 已验证核心表：`generation_task`、`system_setting` 存在。
- 已执行默认数据初始化：默认管理员 1 条，系统设置 9 条。
- 已验证接口健康检查：`/health` 返回 `database=AIdrivenGrowthAssetEngine`。
- 安全说明：本次未把本机 MySQL 密码写入仓库文件。

更新时间：2026-05-20 11:10

- 已补充 Redis/Celery 配置：`REDIS_URL`、`CELERY_BROKER_URL`、`CELERY_RESULT_BACKEND`、`ENABLE_CELERY_TASKS`。
- 已新增 Celery 应用入口：`app.core.celery_app.celery_app`，生成任务和合成任务各有 worker task。
- 已新增真实抓取服务：基于 `httpx + BeautifulSoup` 抓取 `FETCH_SEED_URLS`，抓取失败会落库为 `uncertain` 来源并记录错误。
- 已新增 OpenAI 兼容 LLM 服务：读取 `system_setting` 与 `.env` 的模型配置；`LLM_ENABLE_REAL_CALLS=false` 时使用本地结构化回退。
- 已新增 FFmpeg 服务：`FFMPEG_BIN` 指定可执行文件，`ENABLE_REAL_FFMPEG=true` 时生成竖屏 MP4；默认关闭时仍生成占位文件便于本地调试。
- 已更新 README，补充 Redis/Celery、抓取、LLM、FFmpeg 启动和配置说明。

更新时间：2026-05-20 11:25

- 已修复 `FETCH_SEED_URLS` 配置解析：`.env` 支持逗号分隔 URL，也兼容 JSON 数组格式，避免 Pydantic 对列表字段预解析失败。
- 已调整 Celery 投递时序：生成任务先提交数据库再投递到 Redis broker；重试任务在 `ENABLE_CELERY_TASKS=true` 时也走 Celery worker。
- 已增强 Redis 探测：`ping_redis()` 在连接失败时返回 `False`，不会向调用方抛出 Redis 连接堆栈。
- 已验证配置加载：本机 `backend\.env` 可读取 `DATABASE_URL`、Redis/Celery、抓取源、LLM、`FFMPEG_BIN=E:\APP\bin\ffmpeg.cmd`。
- 验证通过：`backend\.venv\Scripts\python.exe -m ruff check backend\app backend\alembic`。
- 验证通过：`backend\.venv\Scripts\python.exe -m compileall -q backend\app backend\alembic`。
- 验证通过：FastAPI TestClient 调用 `/health` 返回 `database=AIdrivenGrowthAssetEngine`。
- 验证通过：FFmpeg 探测返回 `ffmpeg version n7.1.4-20260513`，默认占位视频写入验证通过。
- 当前环境状态：Redis 连接 `127.0.0.1:6379` 返回不可用，需先启动本机 Redis 后再把 `ENABLE_CELERY_TASKS=true` 并启动 Celery worker。
- 安全检查：`backend\.env` 已被忽略；可跟踪文件未发现本机 MySQL 密码或 `sk-` 形式模型密钥。

更新时间：2026-05-20 11:35

- 已尝试启动本机 Redis：未发现原生 `redis-server`、`redis-cli`、Valkey、Memurai 或 KeyDB。
- 已尝试通过 Docker Desktop 启动 Redis：Docker Desktop 程序已启动，但 `com.docker.service` 当前为 `Stopped`，当前终端无权限启动该 Windows 服务。
- 当前阻塞：`docker info` 返回 `Access is denied`，需管理员权限启动 Docker Desktop 服务后才能拉起 Redis 容器。

更新时间：2026-05-20 11:45

- 已新增部署方案文档：`DEPLOYMENT_PLAN.md`，汇总后端、前端、MySQL、Redis/Celery、抓取源、LLM、FFmpeg、启动顺序和验证命令。
- 已新增本机凭据清单：`DEPLOYMENT_LOCAL_SECRETS.md`，用于本机查看 SQL 库账号密码、默认管理员、Redis、LLM 脱敏信息和 FFmpeg 路径。
- 已更新 `.gitignore`：忽略 `DEPLOYMENT_LOCAL_SECRETS.md`，避免误提交本机账号密码。

## 1. 后端边界

后端只负责 API、SSE、数据库、任务队列、网络抓取、LLM、视频合成、文件服务和权限校验。

- 不渲染 Vue 页面。
- 不写 Jinja/HTML 后台模板。
- 不保存前端页面状态。
- 不依赖前端才能调试接口。
- 后端接口必须可通过 Swagger/Postman 独立验证。

## 2. 技术栈

- Python
- FastAPI
- MySQL
- SQLAlchemy 2
- Alembic
- Redis
- Celery 或 Dramatiq
- APScheduler 或 Celery Beat
- httpx / requests
- BeautifulSoup / readability-lxml
- FFmpeg
- 本地文件存储或 MinIO

## 3. 后端模块

1. 用户认证与权限
2. 生成任务管理
3. 网络抓取服务
4. 素材汇总服务
5. LLM 生成服务
6. SSE 流式输出
7. 选题服务
8. 脚本与分镜服务
9. 审核服务
10. 话题监控服务
11. 定时任务服务
12. 视频合成服务
13. 发布包服务
14. 发布记录服务
15. 数据看板服务
16. 日报服务
17. 文件存储服务
18. 任务日志服务
19. 系统设置服务

## 4. 任务清单

### B1. 后端项目初始化

- 初始化 FastAPI 项目。
- 配置 MySQL 连接。
- 配置 SQLAlchemy 2。
- 配置 Alembic。
- 配置 Redis。
- 配置 Celery 或 Dramatiq。
- 配置统一日志。
- 配置环境变量。
- 配置 CORS。

验收：

- 后端服务可独立启动。
- MySQL 连接正常。
- Redis 连接正常。
- Alembic 可生成迁移。

### B2. 用户认证与权限

- 用户表。
- 角色表。
- 权限表。
- 登录接口。
- 当前用户接口。
- JWT 鉴权。
- 角色权限校验。
- 操作审计日志。

验收：

- 后台接口必须登录后访问。
- 不同角色接口权限隔离。

### B3. 数据库模型设计

核心表：

- user：后台用户
- role：角色
- generation_task：生成任务
- monitor_task：话题监控任务
- source_item：抓取来源
- source_summary：素材汇总
- topic：选题
- script：脚本
- storyboard：分镜
- subtitle：字幕
- review_record：审核记录
- video_asset：视频资产
- cover_asset：封面资产
- card_asset：知识卡片资产
- download_asset：资料包草稿
- publish_package：发布包
- publish_record：发布记录
- task_log：任务日志
- daily_report：每日报告
- system_setting：系统设置

详细字段、索引和关系设计见 `DATABASE_SCHEMA.md`。

验收：

- 表结构支持核心业务流程。
- 重要字段有索引。
- 状态字段使用枚举或稳定常量。
- 所有表包含创建时间和更新时间。

### B4. 生成任务管理

- 创建生成任务。
- 查询生成任务列表。
- 查询生成任务详情。
- 取消生成任务。
- 重试生成任务。
- 记录任务阶段。
- 记录失败原因。

验收：

- 任务创建后进入队列。
- 任务状态可追踪。
- 失败原因可查询。

### B5. 网络抓取服务

- 根据内容方向和主题生成抓取关键词。
- 抓取公开网页内容。
- 解析标题、正文、发布时间、来源链接。
- 去重。
- 过滤无效内容。
- 保存 source_item。
- 记录抓取日志。

验收：

- 每次任务可抓取并保存来源列表。
- 抓取失败时记录原因，不静默失败。
- 每条来源保留 URL。

### B6. 素材汇总服务

- 对抓取内容做清洗。
- 调用 LLM 或规则生成素材摘要。
- 生成相关性说明。
- 提取可用于脚本的重点信息。
- 保存 source_summary。

验收：

- 每次生成任务先形成素材汇总。
- 素材汇总可被后续 LLM 生成使用。

### B7. LLM 生成服务

- 封装 OpenAI 兼容接口。
- 支持流式输出。
- 基于素材汇总生成候选选题。
- 基于选题生成 60 秒脚本。
- 基于脚本生成分镜。
- 基于分镜生成字幕。
- 生成封面文案、标题、简介、标签。
- 记录原始输出和结构化结果。

验收：

- 生成结果可结构化保存。
- LLM 异常可捕获并写入 task_log。
- 不向前端暴露模型密钥。

### B8. SSE 服务

- 提供生成任务 SSE 接口。
- 推送 `start` 事件。
- 推送 `stage` 事件。
- 推送 `source` 事件。
- 推送 `delta` 事件。
- 推送 `result` 事件。
- 推送 `error` 事件。
- 推送 `done` 事件。
- 支持断线后查询任务结果。

验收：

- 前端可实时接收抓取、汇总、生成进度。
- 页面刷新后可恢复任务结果。

### B9. 选题服务

- 保存候选选题。
- 查询选题列表。
- 查询选题详情。
- 通过选题。
- 驳回选题。
- 锁定选题。
- 基于选题继续生成脚本。

验收：

- 选题状态可变更。
- 选题与素材汇总、生成任务关联。

### B10. 脚本、分镜与字幕服务

- 保存脚本。
- 保存脚本版本。
- 保存分镜。
- 保存字幕。
- 更新脚本内容。
- 更新分镜内容。
- 更新字幕内容。
- 查询完整内容详情。

验收：

- 编辑后保留版本记录。
- 脚本、分镜、字幕可用于审核和视频合成。

### B11. 审核服务

- 查询待审核列表。
- 通过。
- 修改后通过。
- 驳回。
- 重新生成。
- 保存审核记录。
- 保存驳回原因。

验收：

- 未审核内容不能进入合成队列。
- 所有审核动作有记录。

### B12. 话题监控与自动任务

- 创建监控任务。
- 编辑监控任务。
- 暂停监控任务。
- 恢复监控任务。
- 删除监控任务。
- 每天定时触发抓取。
- 保存每日素材汇总。
- 可选自动生成候选选题。

验收：

- 监控任务按设定时间执行。
- 自动任务默认不直接合成视频。
- 每日抓取结果可查询。

### B13. 视频合成服务

- 创建合成任务。
- 基于脚本、分镜和字幕生成视频。
- 生成封面。
- 生成知识卡片。
- 保存视频资产。
- 记录合成失败原因。
- 支持重试。

验收：

- 审核通过内容可进入合成队列。
- 已合成视频可下载。

### B14. 发布包服务

- 创建发布包。
- 打包视频、封面、标题、简介、标签、口播稿、分镜表。
- 保存发布包文件。
- 查询发布包列表。
- 下载发布包。

验收：

- 发布包内容完整。
- 下载链接可用。

### B15. 发布记录服务

- 创建发布记录。
- 更新发布状态。
- 记录平台链接。
- 查询发布记录。

验收：

- 发布记录关联发布包和原始内容。
- 可按平台筛选。

### B16. 数据看板服务

- 今日产出统计。
- 近 7 天统计。
- 近 30 天统计。
- 抓取成功率统计。
- LLM 生成成功率统计。
- 任务成功率统计。
- 合成耗时统计。
- 发布包导出统计。

验收：

- 前端图表接口返回稳定结构。
- 统计结果与任务数据一致。

### B17. 每日报告服务

- 定时生成日报。
- 汇总今日素材抓取。
- 汇总生成任务。
- 汇总审核状态。
- 汇总合成状态。
- 汇总发布包。
- 汇总失败任务。
- 导出 Markdown。
- 导出 PDF。

验收：

- 每天自动生成日报。
- 日报可查询和导出。

### B18. 文件存储服务

- 保存视频。
- 保存封面。
- 保存知识卡片。
- 保存资料包草稿。
- 保存发布包。
- 提供下载接口。
- 控制文件访问权限。

验收：

- 登录后才能下载后台文件。
- 文件路径不直接暴露服务器内部目录。

### B19. 系统设置服务

- 保存模型 API Key。
- 保存模型接口地址。
- 保存默认生成数量。
- 保存默认抓取数量。
- 保存文件存储配置。
- 管理默认栏目启停。

验收：

- 敏感配置加密或脱敏展示。
- 普通运营无权查看密钥。

## 5. 后端交付检查

- API 可独立调用。
- 数据表迁移可执行。
- 抓取任务可运行。
- LLM 生成可运行。
- SSE 可订阅。
- 视频合成可运行。
- 发布包可下载。
- 定时任务可执行。
- 后端可独立部署。
