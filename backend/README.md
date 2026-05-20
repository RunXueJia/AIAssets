# 24小时AI增长资产引擎后端

FastAPI + MySQL 后端 MVP，接口前缀 `/api/v1`。

## 初始化

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

先创建用户指定的数据库：

```bash
mysql -uroot -p < scripts/create_database.sql
```

复制配置并修改 MySQL 密码：

```bash
copy .env.example .env
```

LLM 默认配置也在 `.env` 中维护：

```env
LLM_MODEL_PROVIDER=openai_compatible
LLM_MODEL_BASE_URL=https://api.example.com/v1
LLM_MODEL_API_KEY=
LLM_MODEL_NAME=
LLM_REQUEST_TIMEOUT_SECONDS=60
```

后端启动时会把这些值同步到 `system_setting` 表；`.env` 中非空的 LLM 配置优先于数据库旧值。

执行迁移：

```bash
alembic upgrade head
```

启动：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 3007

.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 3007
```

## Redis / Celery

`.env` 中配置：

```env
REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2
ENABLE_CELERY_TASKS=false
```

`ENABLE_CELERY_TASKS=false` 时接口同步执行生成和合成，便于本地调试。开启异步任务后启动 worker：

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info --pool=solo
```

## 抓取 / LLM / FFmpeg

抓取种子页面：

```env
FETCH_SEED_URLS=https://www.technologyreview.com/topic/artificial-intelligence/,https://openai.com/news/
```

LLM 使用 OpenAI 兼容接口：

```env
LLM_MODEL_BASE_URL=https://api.example.com/v1
LLM_MODEL_API_KEY=
LLM_MODEL_NAME=
LLM_ENABLE_REAL_CALLS=false
```

`LLM_ENABLE_REAL_CALLS=false` 时使用本地结构化回退，避免开发环境误消耗额度。

FFmpeg：

```env
FFMPEG_BIN=ffmpeg
ENABLE_REAL_FFMPEG=false
```

`ENABLE_REAL_FFMPEG=false` 时生成占位视频文件；设为 `true` 后使用 FFmpeg 生成竖屏 MP4。

默认管理员：

- 用户名：`admin`
- 密码：`Admin123456`

## 已覆盖接口

- 登录、退出、当前用户
- 生成任务、SSE、素材来源、选题、脚本、分镜、字幕
- 审核、话题监控、视频合成、发布包、发布记录
- 数据看板、每日报告、系统设置、文件下载

网络抓取、LLM 和视频合成均已接入真实服务边界，并保留本地回退配置便于调试。
