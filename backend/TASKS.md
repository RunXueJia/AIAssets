# 后端任务清单

## 0. 任务分配与进度看板

更新日期：2026-05-21

当前状态：基础 FastAPI 工程、数据库模型基线、认证接口、真实 JWT 鉴权、生成记录接口、流式生成落库、管理端接口、地图/天气/实时检索真实 API 适配、AI 规划编排服务已落地并通过后端自测；前端显式调用的 P0/P1 首版路由已注册，`ruff check app tests`、`pytest -q` 60 个用例、`compileall app alembic` 通过。剩余主要风险集中在存量 LLM Key 仍是旧哈希不可解密、mypy 和前端联调收口。MySQL 库 `lushujiang` 已创建，Alembic 初始迁移已执行到 `20260521_0001`。

| 角色 | 负责人 | 负责范围 | 当前进度 | 下一步 |
|---|---|---|---|---|
| 后端组长 | BE-Lead | 拆分任务、接口边界、进度同步、质量把关 | 进行中 | 每日更新本文件，协调前端联调接口优先级 |
| 基础设施后端 | BE-Infra | FastAPI 工程、配置、数据库、迁移、响应结构、日志、CORS、质量工具 | 待联调 | 处理本机 MySQL `information_schema` definer 异常，补充 DB 集成测试 |
| 账号权限后端 | BE-Auth | 用户注册登录、游客会话、JWT、管理员登录、默认管理员、用户禁用启用 | 待联调 | 继续处理前端带 Token 联调反馈 |
| 生成记录后端 | BE-Record | 生成记录、输入输出快照、状态流转、管理端记录查询和重试 | 待联调 | 前端验证 `/planning/generate_stream` 后拉详情、历史、route_map 的闭环 |
| 流式生成后端 | BE-Stream | Trip Schema、SSE/WebSocket、真实 LLM 客户端、中断、失败落库、完整输出保存、AI 规划编排 | 待联调 | 等后台重新保存 LLM API Key 后做真实生成端到端联调 |
| 外部集成后端 | BE-Integration | 高德、腾讯天气、Tavily 实时检索、外部数据来源和缓存 | 待联调 | 真实 API 已接入并纳入测试，下一步补截图兜底和更细错误码 |
| 后端测试 | BE-QA | 单元测试、API 集成测试、真实 API 合同测试、权限测试、流式接口测试 | 进行中 | `ruff check app tests`、`pytest -q` 60 个用例已通过，下一步补 mypy |

### 本迭代优先级

1. BE-Infra 先交付可启动的 FastAPI 基础工程，默认端口 `3002`。
2. BE-Infra 落地 MySQL、SQLAlchemy 2 异步会话、Alembic 和统一响应结构。
3. BE-Auth 交付认证接口，包含默认管理员 `admin` / `admin123456` 的哈希入库。
4. BE-Record 与 BE-Stream 按 `docs/api/frontend_backend_integration.md` 交付用户端可联调的创建记录、流式生成、取消生成、历史列表、详情接口。
5. BE-Integration 第一阶段接入真实高德、腾讯天气、Tavily 检索；Mock 仅保留在单元测试显式注入场景。

### 进度状态约定

- 未开始：尚未创建代码或配置。
- 进行中：已有代码落地但未完成验证。
- 待联调：后端自测通过，等待前端对接。
- 已完成：功能实现、测试和联调均完成。
- 阻塞：需要外部信息、账号、密钥或跨端决策。

### 本轮未完成项审计

检查日期：2026-05-21

前端当前显式调用的用户端和管理端接口均已在后端路由表注册；`/api/v1/admin/users?page=1&page_size=20`、`/api/v1/admin/llm_configs`、`/api/v1/admin/generation_records` 已验证可返回 200。仍未完成项如下：

| 优先级 | 未完成项 | 影响范围 | 下一步分派 |
|---|---|---|---|
| P0 | 规划端和管理端接口仍使用 TODO actor，未从 Authorization 解析真实用户，也未校验 admin 角色 | 已修复：`get_current_actor`、`require_admin_actor` 已接入规划记录和管理接口 | BE-QA 已补 401/403/用户隔离/operator_id 测试，待前端联调 |
| P0 | `/api/v1/planning/generate_stream` 曾使用内存记录，不写 `generation_records`、`generation_inputs`、`generation_stream_events` | 已修复：真实接口使用数据库 RecordStore 创建记录、输入快照、stream events | MySQL 烟测通过，待前端生成后拉详情验证 |
| P0 | 最终 Markdown、JSON 摘要、天气/路线/实时信息快照未随流式生成完成落库 | 已修复：生成完成会保存 `generation_outputs`、天气/路线/地图/实时快照 | 后续真实 LLM Key 修复后做端到端联调 |
| P0 | SSE `snapshot.type` 与用户端监听值不一致，后端发 `routes/realtime_info/summary`，前端监听 `route/realtime/attractions` | 已修复：后端发 `weather/route/map_export/attractions/realtime/summary`，前端已对齐该契约 | 待联调验证 |
| P0 | 失败状态、错误表 `generation_errors` 写入未实现 | 已部分修复：生成异常会写 failed 状态、error 事件和 `generation_errors` | BE-Stream 后续接真实 LLM 时补更细的 provider 错误码 |
| P1 | 管理端 LLM 编辑字段合同不一致：前端发送 `provider`，后端更新 Schema 不接收；前端编辑未先拉详情，可能用默认值覆盖详情字段 | 已修复：前端编辑时不发送 `provider`，编辑前先拉详情填充 `timeout_s/max_tokens/temperature` | 待联调验证 |
| P1 | 高德、天气、实时检索内部辅助接口未注册：`/api/v1/amap/*`、`/api/v1/weather/query`、`/api/v1/realtime/search` | 已修复：真实 API 路由已注册且要求管理员权限 | 前端按权限联调 |
| P1 | 真实 AI 规划链路未实现：Prompt 模板、上下文拼装、路径点/公交/景点/风险生成、输出校验 | 已部分修复：`AiPlanningService` 已接真实高德/腾讯天气/Tavily 上下文和 Markdown/JSON 编排 | 等 LLM Key 可解密后做真实生成闭环 |
| P1 | 存量 LLM API Key 是旧哈希，不能解密用于真实供应商调用；配置审计日志未写入 | 真实 LLM 调用、管理端审计 | 需要在后台重新保存默认 LLM 配置的 API Key；后续补审计记录 |
| P1 | mypy 未配置 | 质量门禁 | BE-QA 增加 mypy 配置或明确暂缓 |
| P2 | 路径图截图兜底、供应商错误码细分等增强项未实现 | 地图预览/下载和稳定性增强 | BE-Integration 后续分波交付 |

### 本地启动与运维命令

工作目录默认在 `backend`：

```powershell
cd E:\code\hours24\backend
```

安装后端依赖：

```powershell
python -m pip install -e .[dev]
```

本地 `.env` 示例，真实密码写入 `backend/.env`，不要提交到 Git：

```env
BACKEND_DATABASE_URL=mysql+asyncmy://root:Qb%40123@localhost:3306/lushujiang?charset=utf8mb4
```

首次建库：

```powershell
$env:MYSQL_PWD='Qb@123'
mysql -uroot -e "CREATE DATABASE IF NOT EXISTS lushujiang CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

执行数据库迁移：

```powershell
python -m alembic upgrade head
```

启动后端服务，默认端口 `3002`：

```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 3002 --reload
```

验证命令：

```powershell
python -m ruff check .
python -m pytest -q
$env:MYSQL_PWD='Qb@123'
mysql -uroot lushujiang -e "SELECT version_num FROM alembic_version; SELECT COUNT(*) AS users_count FROM users;"
```

注意：当前本机 MySQL 缺少 `mysql.infoschema/mysql.session/mysql.sys` 系统账号，`SHOW TABLES`、`DESCRIBE`、`alembic current` 可能因 `information_schema` definer 异常失败；业务表直接查询和后端连接已验证可用。

### 并行分派计划

第一波任务在基础工程可创建时启动，写入范围必须互不覆盖：

| 波次 | 执行人 | 写入范围 | 任务 | 依赖 | 验收标准 |
|---|---|---|---|---|---|
| Wave 1 | BE-Infra | `backend/pyproject.toml`、`backend/app/core`、`backend/app/main.py`、`backend/tests` 基线 | 创建 FastAPI 可启动工程、settings、CORS、统一响应、健康检查、ruff/mypy/pytest | 无 | `uvicorn app.main:app --port 3002` 可启动，健康检查返回统一响应 |
| Wave 1 | BE-Infra | `backend/app/db`、`backend/app/models`、`backend/alembic` | 按 MySQL 文档创建 SQLAlchemy 2 模型、异步会话、Alembic 初始化迁移 | 工程骨架 | 迁移脚本覆盖核心表，模型字段与 `docs/db/mysql_schema.md` 对齐 |
| Wave 2 | BE-Auth | `backend/app/api/v1/endpoints/auth.py`、`backend/app/services/auth*`、`backend/app/schemas/auth*` | 用户注册登录、游客会话、JWT、管理员登录、默认管理员初始化 | Wave 1 | 认证接口符合联调文档，密码和 token 只存哈希 |
| Wave 2 | BE-Record | `backend/app/api/v1/endpoints/records.py`、`backend/app/services/records*`、`backend/app/schemas/records*` | 生成记录 CRUD、输入输出快照、状态流转、管理端查询 | Wave 1、认证依赖 | 用户只能访问自己的记录，管理端可筛选全部记录 |
| Wave 2 | BE-Stream | `backend/app/api/v1/endpoints/generation.py`、`backend/app/services/generation*`、`backend/app/integrations/llm` | Trip Schema、SSE 流式接口、取消生成、真实 LLM 客户端、完整输出保存 | Wave 1、记录服务接口 | 前端可收到阶段事件和最终结果，取消后状态为 `canceled` |
| Wave 3 | BE-Integration | `backend/app/integrations/amap`、`backend/app/integrations/weather`、`backend/app/integrations/realtime` | 高德、腾讯天气、Tavily 实时检索真实客户端；Mock 仅用于单元测试显式注入 | Wave 1 | 无密钥时明确失败，有密钥时真实调用供应商 |
| Wave 3 | BE-QA | `backend/tests` | API、Service、权限、SSE、真实外部 API 合同测试和显式注入 Mock 单元测试 | Wave 2 | P0 接口测试覆盖通过，失败路径有断言 |

Wave 2 已完成并由 BE-Lead 集成：James 负责认证，Pasteur 负责记录，Arendt 负责流式生成。Wave 3 后端服务适配层已完成：高德 Web 服务、腾讯天气、Tavily 实时检索均使用真实 API，运行时无 Key 或配置 Mock 会明确失败；AI 规划已有 Prompt、真实上下文、结构化结果和 Markdown/JSON 编排。当前验证结果：`ruff check app tests` 通过，`pytest -q` 60 个用例通过，`compileall app alembic` 通过。MySQL：`lushujiang` 已建库，14 张业务表和 `alembic_version` 可直接查询，`POST /api/v1/auth/login` 使用默认管理员真实库登录已验证通过；`GET /api/v1/admin/users`、`GET /api/v1/admin/llm_configs`、`GET /api/v1/admin/generation_records` 已验证返回 200。阻塞项：`llm_configs` 表内现有两条配置仍为旧哈希 Key，非 `xor-v1:` 可解密密文，需要后台重新保存 API Key 后才能真实生成。另本机 MySQL 的 `information_schema` 存在 `mysql.infoschema` definer 异常，`SHOW TABLES` / `DESCRIBE` 会失败。

## 1. 基础工程

- [x] 初始化 FastAPI 项目结构。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 配置 pyproject.toml。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 配置环境变量和 settings。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 配置后端本地默认端口为 `3002`。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 接入 MySQL。负责人：BE-Infra；状态：已完成；优先级：P0；说明：已创建并连接 `lushujiang`。
- [x] 按 `docs/db/mysql_schema.md` 落地 MySQL 表结构和 SQLAlchemy 模型。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 接入 SQLAlchemy 2 异步会话。负责人：BE-Infra；状态：已完成；优先级：P0。
- [x] 配置 Alembic 迁移。负责人：BE-Infra；状态：已完成；优先级：P0；说明：初始迁移已执行到 `20260521_0001`。
- [x] 配置统一异常处理。负责人：BE-Infra；状态：已完成；优先级：P1。
- [x] 配置统一响应结构。负责人：BE-Infra；状态：已完成；优先级：P0。
- [ ] 按 `docs/api/frontend_backend_integration.md` 实现前后端联调接口。负责人：BE-Auth、BE-Record、BE-Stream；状态：待联调；优先级：P0；说明：首版认证、规划流、记录、管理端记录接口已注册。
- [x] 配置请求日志和链路 ID。负责人：BE-Infra；状态：已完成；优先级：P1。
- [x] 配置 CORS。负责人：BE-Infra；状态：已完成；优先级：P0。
- [ ] 配置 ruff、mypy、pytest。负责人：BE-Infra、BE-QA；状态：进行中；优先级：P1；说明：ruff 和 pytest 已接入并通过，mypy 未配置。

## 2. 用户与管理员

- [x] 用户注册登录。负责人：BE-Auth；状态：待联调；优先级：P0。
- [x] 游客临时会话。负责人：BE-Auth；状态：待联调；优先级：P0。
- [x] JWT 鉴权。负责人：BE-Auth；状态：待联调；优先级：P0。
- [x] 管理员登录。负责人：BE-Auth；状态：待联调；优先级：P0。
- [x] 初始化默认管理员账号：用户名 `admin`，初始密码 `admin123456`，密码入库必须哈希存储。负责人：BE-Auth；状态：待联调；优先级：P0。
- [x] 管理员用户列表。负责人：BE-Auth；状态：待联调；优先级：P1。
- [x] 管理员禁用/启用用户。负责人：BE-Auth；状态：待联调；优先级：P1。

## 3. 生成记录模块

- [x] 创建生成记录。负责人：BE-Record；状态：待联调；优先级：P0；说明：流式生成和重新生成均可创建记录。
- [x] 保存用户输入快照。负责人：BE-Record；状态：待联调；优先级：P0；说明：流式生成和重新生成均保存输入快照。
- [x] 查询用户自己的生成记录。负责人：BE-Record；状态：待联调；优先级：P0。
- [x] 查询生成记录详情。负责人：BE-Record；状态：待联调；优先级：P0。
- [x] 保存最终生成结果。负责人：BE-Record；状态：待联调；优先级：P0；说明：最终 Markdown、JSON 摘要和摘要字段已落库。
- [x] 保存生成状态：pending、streaming、completed、failed。负责人：BE-Record、BE-Stream；状态：待联调；优先级：P0；说明：流式主流程状态已落库，异常会写 failed 和错误记录。
- [x] 管理端查询全部生成记录。负责人：BE-Record；状态：待联调；优先级：P1。
- [x] 管理端查看错误详情。负责人：BE-Record；状态：待联调；优先级：P1。
- [x] 管理端重试失败记录。负责人：BE-Record、BE-Stream；状态：待联调；优先级：P1。

## 4. 流式生成模块

- [x] 设计 TripPlanningRequest Schema。负责人：BE-Stream；状态：待联调；优先级：P0。
- [x] 设计 TripPlanningResult Schema。负责人：BE-Stream；状态：待联调；优先级：P0；说明：当前以 `generation_outputs.result_json` 和详情接口 `output` 结构承载最终结果，真实 AI 后可继续细化强类型 Schema。
- [x] 设计流式事件格式。负责人：BE-Stream；状态：待联调；优先级：P0。
- [x] 实现 SSE 或 WebSocket 接口。负责人：BE-Stream；状态：待联调；优先级：P0；说明：已使用 StreamingResponse 实现 SSE。
- [x] 封装 LLM 流式调用客户端。负责人：BE-Stream；状态：待联调；优先级：P1；说明：已封装 OpenAI-compatible 真实 LLM 客户端，优先读取后台启用配置。
- [x] 支持用户中断生成。负责人：BE-Stream；状态：待联调；优先级：P0。
- [x] 支持失败状态落库。负责人：BE-Stream；状态：待联调；优先级：P1；说明：生成异常会返回 error 事件和 failed done，真实 provider 错误码后续细化。
- [x] 保存完整输出。负责人：BE-Stream、BE-Record；状态：待联调；优先级：P0；说明：完整 Markdown 和 JSON 摘要已保存。

## 5. 地图集成

- [x] 高德 API Key 配置。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`BACKEND_AMAP_API_KEY` 已配置，运行时无 Key 会明确失败。
- [x] 地理编码服务。负责人：BE-Integration；状态：待联调；优先级：P1；说明：真实高德 POI 解析地点名到经纬度，支持生成链路自然语言地点输入。
- [x] POI 搜索服务。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/amap/search_places` 已接真实高德 Web 服务。
- [x] 驾车路径规划服务。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/amap/calculate_route` 已接真实高德驾车路径规划。
- [x] 公共交通路径规划服务。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`calculate_route` 支持 `transport_mode=transit/mixed` 并走真实高德公交接口。
- [x] 步行路径规划服务。负责人：BE-Integration；状态：待联调；优先级：P2；说明：`calculate_route` 支持 `transport_mode=walking` 并走真实高德步行接口。
- [x] 路径点摘要生成。负责人：BE-Integration、BE-Stream；状态：待联调；优先级：P1；说明：`AiPlanningService` 保存真实 route waypoints、坐标和摘要。
- [x] 高德路线分享链接或导航 URI 生成。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/amap/create_route_link` 已接 `AmapService`。
- [x] 高德路径图导出，优先生成可预览图片，示例形态类似 `https://surl.amap.com/xo9XnEf1z1XI`。负责人：BE-Integration；状态：待联调；优先级：P2；说明：`/api/v1/amap/export_route_map` 已按高德静态图 API 生成 `restapi.amap.com/v3/staticmap` URL。
- [ ] 路径图截图兜底：当短链或静态图能力不可用时，用高德 JS API 渲染后截图保存。负责人：BE-Integration；状态：未开始；优先级：P2。
- [x] 高德接口错误重试。负责人：BE-Integration；状态：待联调；优先级：P2；说明：真实客户端已内置轻量重试，后续补更细错误码。
- [x] 高德结果缓存。负责人：BE-Integration；状态：待联调；优先级：P2；说明：真实客户端已接入 TTL 缓存。

## 6. 天气与实时信息检索集成

- [x] 天气 API 客户端。负责人：BE-Integration；状态：待联调；优先级：P1；说明：默认腾讯天气真实接口，`provider=amap` 可走高德天气；运行时不允许 Mock。
- [x] 目的地天气查询。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/weather/query` 已接腾讯天气真实接口。
- [x] 沿途城市天气查询，按需。负责人：BE-Integration；状态：待联调；优先级：P2；说明：新增 `/api/v1/weather/batch_summary`。
- [x] 天气预警摘要。负责人：BE-Integration、BE-Stream；状态：待联调；优先级：P1；说明：WeatherService 汇总目的地/沿途城市预警。
- [x] 实时信息检索 API 客户端。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`BACKEND_TAVILY_API_KEY` 已配置，`TavilyRealtimeClient` 真实调用；运行时不允许 Mock。
- [x] 新闻/交通管制检索。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/realtime/search` 已接 Tavily。
- [x] 攻略/避坑参考检索。负责人：BE-Integration；状态：待联调；优先级：P1；说明：`/api/v1/realtime/search` 已接 Tavily。
- [x] 实时信息结果按来源、发布时间、分类和可信度整理。负责人：BE-Integration；状态：待联调；优先级：P1；说明：RealtimeService 输出 `sources`、`published_at`、`classification`、`credibility_score`。
- [x] 外部数据来源和更新时间记录。负责人：BE-Integration、BE-Record；状态：待联调；优先级：P1；说明：天气/实时/地图输出真实 provider、source_updated_at，并随生成快照落库。

## 7. AI 规划集成

- [x] 管理端 LLM 配置读取。负责人：BE-Stream；状态：阻塞；优先级：P1；说明：读取链路已接入，但现有数据库 Key 是旧哈希，需后台重新保存为可解密密文。
- [x] 支持配置 LLM 供应商、Base URL、模型名、API Key。负责人：BE-Stream；状态：待联调；优先级：P1。
- [x] API Key 加密存储，列表页只显示掩码。负责人：BE-Stream、BE-Infra；状态：待联调；优先级：P1；说明：新建/更新配置已使用 `xor-v1:` 可解密密文；存量旧哈希不能迁移，需重新保存 API Key。
- [x] LLM 配置连接测试。负责人：BE-Stream；状态：待联调；优先级：P2；说明：连接测试会真实调用 OpenAI-compatible `/chat/completions`。
- [x] LLM 配置启用/停用。负责人：BE-Stream；状态：待联调；优先级：P2。
- [x] Prompt 模板管理，先用配置文件实现。负责人：BE-Stream；状态：待联调；优先级：P1；说明：`AiPlanningService` 内置 Prompt 模板，后续可迁移到配置文件。
- [x] 拼装地图、天气、实时信息检索上下文。负责人：BE-Stream、BE-Integration；状态：待联调；优先级：P1；说明：`TripPlanningContext` 已包含真实 weather/route/transport/map_export/attractions/realtime/risks；天气城市会用高德 POI 解析出省/市/区后再查腾讯天气。
- [x] 生成路径点规划。负责人：BE-Stream；状态：待联调；优先级：P1；说明：AI 编排结果包含 route waypoints。
- [x] 生成公共交通规划。负责人：BE-Stream；状态：待联调；优先级：P1；说明：AI 编排结果包含 transport summary/segments。
- [x] 生成途径景点说明。负责人：BE-Stream；状态：待联调；优先级：P1；说明：AI 编排结果包含 attractions summary/items。
- [x] 生成风险提示。负责人：BE-Stream；状态：待联调；优先级：P1；说明：AI 编排结果包含 risks 和 risk_summary。
- [x] 生成最终 Markdown。负责人：BE-Stream；状态：待联调；优先级：P0；说明：`AiPlanningService` 生成 final_markdown 并由生成流落库。
- [x] 生成 JSON 摘要。负责人：BE-Stream；状态：待联调；优先级：P1；说明：`AiPlanningService` 生成 result_json 并由生成流落库。
- [x] AI 输出基础校验。负责人：BE-Stream；状态：待联调；优先级：P1；说明：TripPlanningContext/TripPlanningResult Pydantic 模型校验基础结构。

## 8. 测试与质量

- [x] Service 层单元测试。负责人：BE-QA；状态：进行中；优先级：P1；说明：认证、记录、流式服务已有基础覆盖。
- [x] API 集成测试。负责人：BE-QA；状态：进行中；优先级：P1；说明：认证、流式、健康检查已有测试。
- [x] LLM 客户端测试。负责人：BE-QA、BE-Stream；状态：进行中；优先级：P1；说明：后台配置服务覆盖密钥加密/掩码/读取，真实连接依赖可用 Key。
- [x] 高德客户端测试。负责人：BE-QA、BE-Integration；状态：已完成；优先级：P2；说明：包含真实 API 合同测试和显式注入 Mock 的单元测试。
- [x] 天气和实时信息检索客户端测试。负责人：BE-QA、BE-Integration；状态：已完成；优先级：P2；说明：包含腾讯天气/Tavily 真实 API 合同测试和显式注入 Mock 的单元测试。
- [x] SSE 或 WebSocket 流式接口测试。负责人：BE-QA、BE-Stream；状态：待联调；优先级：P0。
- [x] 管理员权限测试。负责人：BE-QA、BE-Auth；状态：已完成；优先级：P1；说明：已覆盖 401、403、规划用户隔离和管理端 operator_id。
