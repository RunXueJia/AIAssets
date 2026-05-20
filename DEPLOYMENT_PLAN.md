# 24小时AI增长资产引擎部署方案

本文档记录后端、前端、数据库、Redis/Celery、LLM、FFmpeg 的本机与服务器部署方式。敏感账号密码不写入本文档，查看本机凭据请使用未提交文件 `DEPLOYMENT_LOCAL_SECRETS.md`。

## 1. 服务端口

- 前端管理端：`http://127.0.0.1:3006`
- 后端 API：`http://127.0.0.1:3007`
- 后端接口前缀：`/api/v1`
- MySQL：`127.0.0.1:3306`
- Redis：`127.0.0.1:6379`

## 2. 依赖组件

- Python 3.11+
- MySQL 8.x
- Redis 7.x 或兼容服务
- Node.js 18+
- FFmpeg
- 可选：Docker Desktop，用于本机启动 Redis

## 3. 后端部署

```powershell
cd E:\code\hours24\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

创建数据库并执行迁移：

```powershell
mysql -uroot -p < scripts\create_database.sql
alembic upgrade head
```

启动后端：

```powershell
cd E:\code\hours24\backend
.\.venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 3007
```

健康检查：

```powershell
curl http://127.0.0.1:3007/health
```

预期返回包含：

```json
{"code":0,"message":"success","data":{"status":"ok","database":"AIdrivenGrowthAssetEngine"}}
```

## 4. 数据库配置

数据库名固定为：

```text
AIdrivenGrowthAssetEngine
```

后端从 `backend/.env` 读取连接串：

```env
DATABASE_NAME=AIdrivenGrowthAssetEngine
DATABASE_URL=mysql+pymysql://<user>:<password>@127.0.0.1:3306/AIdrivenGrowthAssetEngine?charset=utf8mb4
```

本机账号密码见 `DEPLOYMENT_LOCAL_SECRETS.md`。

## 5. Redis / Celery

本机如果已安装 Docker，可使用 Redis 容器：

```powershell
docker run -d --name hours24-redis -p 127.0.0.1:6379:6379 redis:7-alpine
```

如果容器已存在：

```powershell
docker start hours24-redis
```

后端配置：

```env
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
ENABLE_CELERY_TASKS=true
```

启动 Celery worker：

```powershell
cd E:\code\hours24\backend
.\.venv\Scripts\activate
celery -A app.core.celery_app.celery_app worker --loglevel=info --pool=solo
```

验证 Redis：

```powershell
cd E:\code\hours24
backend\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'backend'); from app.services.redis_service import ping_redis; print(ping_redis())"
```

输出 `True` 代表可用。

## 6. 抓取源配置

```env
FETCH_TIMEOUT_SECONDS=20
FETCH_MAX_CONTENT_CHARS=12000
FETCH_SEED_URLS=https://www.technologyreview.com/topic/artificial-intelligence/,https://openai.com/news/
```

说明：

- 当前抓取是固定种子 URL 抓取，不是搜索引擎抓取。
- `FETCH_SEED_URLS` 支持逗号分隔 URL，也兼容 JSON 数组。
- 抓取失败会保存为 `uncertain` 来源并记录错误。

## 7. LLM 配置

配置位置：`backend/.env`

```env
LLM_MODEL_PROVIDER=openai_compatible
LLM_MODEL_BASE_URL=https://your-provider.example/v1
LLM_MODEL_API_KEY=
LLM_MODEL_NAME=
LLM_REQUEST_TIMEOUT_SECONDS=60
LLM_ENABLE_REAL_CALLS=true
```

说明：

- `LLM_ENABLE_REAL_CALLS=false` 时使用本地结构化回退，不调用真实模型。
- `LLM_ENABLE_REAL_CALLS=true` 时必须配置 `LLM_MODEL_API_KEY`、`LLM_MODEL_BASE_URL`、`LLM_MODEL_NAME`。
- 后端启动后会把 `.env` 中非空的 LLM 配置同步到 `system_setting` 表。
- 密钥不通过前端接口明文返回。

## 8. FFmpeg 配置

```env
FFMPEG_BIN=ffmpeg
ENABLE_REAL_FFMPEG=false
```

Windows 本机可配置为绝对路径：

```env
FFMPEG_BIN=E:\APP\bin\ffmpeg.cmd
```

说明：

- `ENABLE_REAL_FFMPEG=false` 时生成占位视频文件，适合本地调试。
- `ENABLE_REAL_FFMPEG=true` 时调用 FFmpeg 生成竖屏 MP4。

验证：

```powershell
cd E:\code\hours24
backend\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'backend'); from app.services.ffmpeg_service import check_ffmpeg; print(check_ffmpeg())"
```

## 9. 前端部署

```powershell
cd E:\code\hours24\frontend\admin
npm install
npm run dev
```

本机开发配置：

```env
VITE_API_BASE=/api/v1
VITE_USE_MOCK=false
```

Vite 开发服务监听 `3006`，并把 `/api` 代理到 `http://127.0.0.1:3007`。

构建：

```powershell
cd E:\code\hours24\frontend\admin
npm run build
```

部署到 Nginx 时，需要把前端 `dist` 配置为静态目录，并把 `/api/` 反向代理到后端 API 服务。

## 10. 推荐启动顺序

1. 启动 MySQL。
2. 启动 Redis。
3. 启动后端 API。
4. 启动 Celery worker。
5. 启动前端管理端。
6. 打开 `http://127.0.0.1:3006`。

## 11. 常用验证命令

后端健康检查：

```powershell
curl http://127.0.0.1:3007/health
```

数据库迁移版本：

```powershell
cd E:\code\hours24\backend
.\.venv\Scripts\activate
alembic current
```

代码检查：

```powershell
cd E:\code\hours24
backend\.venv\Scripts\python.exe -m ruff check backend\app backend\alembic
backend\.venv\Scripts\python.exe -m compileall -q backend\app backend\alembic
```

## 12. 当前注意事项

- 本机 Docker Desktop 服务需要管理员权限启动，否则无法用 Docker 拉起 Redis。
- 开启 `ENABLE_CELERY_TASKS=true` 前，必须确认 Redis 可用。
- 修改 `backend/.env` 后需要重启后端；如果修改 Celery/Redis/LLM/FFmpeg 配置，也需要重启 Celery worker。
- 真实 LLM 调用会消耗额度，开发联调前确认 Key 和模型名正确。
- `backend/.env`、`DEPLOYMENT_LOCAL_SECRETS.md` 不应提交到仓库。
